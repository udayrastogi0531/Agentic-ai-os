"""
Nidhi — WebSocket Handler

Real-time streaming chat over WebSocket.
Protocol:
  Client → Server: { "type": "message", "content": "...", "metadata": {...} }
  Server → Client: { "type": "token|agent_status|message_complete|error", ... }
"""

from __future__ import annotations

import uuid
import json
import logging
import time
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config import get_settings
from app.database import async_session_factory
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.llm.provider import get_llm
from app.memory.manager import MemoryManager
from app.services.auth_service import decode_access_token, get_user_by_id
from app.services.chat_service import build_system_prompt, get_conversation, create_conversation

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory store for pending agent execution states waiting for human approval
pending_approvals: dict[str, dict] = {}


# ── Connection Manager ────────────────────────────────────────────────

class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str) -> None:
        self.active_connections.pop(user_id, None)
        logger.info(f"WebSocket disconnected: {user_id}")

    async def send_json(self, user_id: str, data: dict) -> None:
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()


# ── WebSocket Endpoint ────────────────────────────────────────────────

async def websocket_chat_handler(
    websocket: WebSocket,
    conversation_id: str | None = None,
    token: str | None = None,
) -> None:
    """
    Handle a WebSocket chat connection with streaming LLM responses.
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["sub"]

    async with async_session_factory() as db:
        user = await get_user_by_id(db, uuid.UUID(user_id))
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return

        await manager.connect(user_id, websocket)

        try:
            while True:
                # Receive message from client
                raw = await websocket.receive_text()

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await manager.send_json(user_id, {
                        "type": "error",
                        "content": "Invalid JSON",
                    })
                    continue

                msg_type = data.get("type", "message")

                if msg_type == "ping":
                    await manager.send_json(user_id, {"type": "pong"})
                    continue

                if msg_type == "approval":
                    approved = data.get("approved", False)
                    await _resume_with_approval(
                        db=db,
                        user=user,
                        user_id=user_id,
                        approved=approved,
                        conversation_id=conversation_id,
                    )
                    continue

                if msg_type != "message":
                    continue

                content = data.get("content", "").strip()
                if not content:
                    continue

                # Process the message with streaming
                await _stream_response(
                    db=db,
                    user=user,
                    user_id=user_id,
                    message=content,
                    conversation_id=conversation_id,
                )

        except WebSocketDisconnect:
            manager.disconnect(user_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            manager.disconnect(user_id)


async def _stream_response(
    db: AsyncSession,
    user: User,
    user_id: str,
    message: str,
    conversation_id: str | None,
) -> None:
    """Stream an LLM response token by token."""

    # Send agent status
    await manager.send_json(user_id, {
        "type": "agent_status",
        "agent_name": "planner",
        "content": "Thinking...",
    })

    # Get or create conversation
    conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
    if conv_uuid:
        conversation = await get_conversation(db, conv_uuid, uuid.UUID(user_id))
    else:
        conversation = await create_conversation(db, uuid.UUID(user_id), message[:100])

    if not conversation:
        await manager.send_json(user_id, {
            "type": "error",
            "content": "Conversation not found",
        })
        return

    # Retrieve memories
    memory_mgr = MemoryManager(db)
    memory_context = await memory_mgr.get_context_memories(
        user_id=uuid.UUID(user_id),
        message=message,
    )

    # Build prompt
    system_prompt = build_system_prompt(user, memory_context)

    # Build message history
    from sqlalchemy import select
    history_stmt = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    history_result = await db.execute(history_stmt)
    history = list(reversed(list(history_result.scalars().all())))

    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in history:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
    lc_messages.append(HumanMessage(content=message))

    # Save user message
    user_msg = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="user",
        content=message,
    )
    db.add(user_msg)

    # Stream LangGraph response and agent nodes execution
    from app.agents.graph import get_agent_graph

    initial_state = {
        "messages": lc_messages[:-1], # History messages (except current user prompt, which goes to user_message channel)
        "user_id": str(user.id),
        "conversation_id": str(conversation.id),
        "user_message": message,
        "retrieved_memories": [],
        "memory_context": "",
        "plan": [],
        "current_step": 0,
        "selected_tools": [],
        "tool_results": {},
        "metrics": {},
        "final_response": "",
        "metadata": {},
        "error": None,
        "approved": False,
        "approval_required": False,
        "loop_count": 0
    }

    graph = get_agent_graph()
    full_response = ""
    final_state = initial_state.copy()
    node_timers = {}

    try:
        async for event in graph.astream_events(initial_state, version="v2"):
            kind = event["event"]
            name = event["name"]

            if kind == "on_node_start":
                # Translate node execution to user status feedback
                status_messages = {
                    "memory": "Recalling user preferences...",
                    "planner": "Formulating execution plan...",
                    "tools": "Invoking helper sub-agents...",
                    "evaluate": "Evaluating step outcome...",
                    "replan": "Re-routing plan steps...",
                    "response": "Drafting final response...",
                    "files_node": "Retrieving relevant files/documents...",
                    "tasks_node": "Updating task list...",
                    "notes_node": "Reading/writing note details...",
                    "memory_node": "Recalling long term memory context...",
                    "research_node": "Researching details on the web...",
                    "browser_node": "Running Playwright browser agent...",
                    "gmail_node": "Interacting with Gmail...",
                    "calendar_node": "Updating Google Calendar events...",
                    "coding_node": "Writing/debugging source code...",
                    "computer_node": "Automating desktop and messaging tasks...",
                    "voice_node": "Invoking voice synthesis/processing...",
                }
                if name in status_messages:
                    await manager.send_json(user_id, {
                        "type": "agent_status",
                        "agent_name": name,
                        "content": status_messages[name],
                    })
                node_timers[name] = time.perf_counter()

            elif kind == "on_chat_model_stream":
                # Only stream chunks generated during the 'response' compilation node
                metadata = event.get("metadata", {})
                node_name = metadata.get("langgraph_node", "")
                if node_name == "response":
                    token = event["data"]["chunk"].content
                    if token:
                        full_response += token
                        await manager.send_json(user_id, {
                            "type": "token",
                            "content": token,
                        })

            elif kind == "on_chain_end":
                node_name = event.get("metadata", {}).get("langgraph_node")
                if node_name:
                    output_update = event["data"].get("output")
                    if isinstance(output_update, dict):
                        for k, v in output_update.items():
                            if k == "messages":
                                final_state[k] = list(final_state[k]) + list(v)
                            else:
                                final_state[k] = v

                    # Log the node execution to database
                    duration_ms = None
                    if node_name in node_timers:
                        duration_ms = int((time.perf_counter() - node_timers.pop(node_name)) * 1000)

                    status = "success"
                    error_msg = None
                    if isinstance(output_update, dict) and "error" in output_update and output_update["error"]:
                        status = "error"
                        error_msg = output_update["error"]

                    from app.models.agent_log import AgentLog
                    log = AgentLog(
                        id=uuid.uuid4(),
                        user_id=uuid.UUID(user_id),
                        conversation_id=conversation.id,
                        agent_name=node_name,
                        action="execute_node",
                        input_data={"current_step": final_state.get("current_step", 0)},
                        output_data=output_update if isinstance(output_update, dict) else {"output": str(output_update)},
                        duration_ms=duration_ms,
                        status=status,
                        error_message=error_msg
                    )
                    db.add(log)

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        full_response = f"Sorry, I encountered an error running the agent plan: {type(e).__name__}"
        await manager.send_json(user_id, {
            "type": "token",
            "content": full_response,
        })

    # Save AI message
    ai_msg = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="assistant",
        content=full_response,
        agent_name="planner",
        token_count=len(full_response.split()),
    )
    db.add(ai_msg)

    # Trigger memory consolidation if not paused for approval
    if not final_state.get("approval_required"):
        from app.memory.consolidation import consolidate_conversation_memory
        try:
            await db.flush()
            await consolidate_conversation_memory(db, user.id, conversation.id)
        except Exception as e:
            logger.warning(f"Failed to consolidate memory in WebSocket: {e}")

    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # If the run ended with a pending approval, save the state to wait for user confirmation
    if final_state.get("approval_required"):
        pending_approvals[str(conversation.id)] = final_state
        logger.info(f"[WebSocket] Graph run paused. Saved state for conversation {conversation.id} to pending approvals.")

    # Send completion signal
    await manager.send_json(user_id, {
        "type": "message_complete",
        "content": full_response,
        "metadata": {
            "conversation_id": str(conversation.id),
            "message_id": str(ai_msg.id),
            "approval_required": bool(final_state.get("approval_required")),
        },
    })


async def _resume_with_approval(
    db: AsyncSession,
    user: User,
    user_id: str,
    approved: bool,
    conversation_id: str | None,
) -> None:
    """Resume execution of a paused plan after user approval or denial."""
    if not conversation_id:
        await manager.send_json(user_id, {
            "type": "error",
            "content": "Conversation ID is missing.",
        })
        return

    # Retrieve pending state
    state = pending_approvals.pop(conversation_id, None)
    if not state:
        await manager.send_json(user_id, {
            "type": "error",
            "content": "No pending actions found for this conversation.",
        })
        return

    if not approved:
        # User denied approval
        denial_response = "❌ **Action Cancelled**\n\nYou declined the confirmation request. The action was not executed."
        await manager.send_json(user_id, {
            "type": "token",
            "content": denial_response,
        })
        
        # Save denial response to DB
        ai_msg = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            role="assistant",
            content=denial_response,
            agent_name="planner",
            token_count=len(denial_response.split()),
        )
        db.add(ai_msg)
        
        conv_uuid = uuid.UUID(conversation_id)
        conv = await get_conversation(db, conv_uuid, uuid.UUID(user_id))
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
        await db.commit()

        await manager.send_json(user_id, {
            "type": "message_complete",
            "content": denial_response,
            "metadata": {
                "conversation_id": conversation_id,
                "message_id": str(ai_msg.id),
                "approval_required": False
            },
        })
        return

    # User approved! Run graph from where it paused with approved=True
    state["approved"] = True
    state["approval_required"] = False
    
    # Send status update
    await manager.send_json(user_id, {
        "type": "agent_status",
        "agent_name": "tools",
        "content": "Resuming action with approval...",
    })

    # Execute graph with updated state
    from app.agents.graph import get_agent_graph
    graph = get_agent_graph()
    full_response = ""
    final_state = state.copy()
    node_timers = {}

    try:
        async for event in graph.astream_events(state, version="v2"):
            kind = event["event"]
            name = event["name"]

            if kind == "on_node_start":
                status_messages = {
                    "memory": "Recalling user preferences...",
                    "planner": "Formulating execution plan...",
                    "tools": "Invoking helper sub-agents...",
                    "evaluate": "Evaluating step outcome...",
                    "replan": "Re-routing plan steps...",
                    "response": "Drafting final response...",
                    "files_node": "Retrieving relevant files/documents...",
                    "tasks_node": "Updating task list...",
                    "notes_node": "Reading/writing note details...",
                    "memory_node": "Recalling long term memory context...",
                    "research_node": "Researching details on the web...",
                    "browser_node": "Running Playwright browser agent...",
                    "gmail_node": "Interacting with Gmail...",
                    "calendar_node": "Updating Google Calendar events...",
                    "coding_node": "Writing/debugging source code...",
                    "computer_node": "Automating desktop and messaging tasks...",
                    "voice_node": "Invoking voice synthesis/processing...",
                }
                if name in status_messages:
                    await manager.send_json(user_id, {
                        "type": "agent_status",
                        "agent_name": name,
                        "content": status_messages[name],
                    })
                node_timers[name] = time.perf_counter()

            elif kind == "on_chat_model_stream":
                metadata = event.get("metadata", {})
                node_name = metadata.get("langgraph_node", "")
                if node_name == "response":
                    token = event["data"]["chunk"].content
                    if token:
                        full_response += token
                        await manager.send_json(user_id, {
                            "type": "token",
                            "content": token,
                        })

            elif kind == "on_chain_end":
                node_name = event.get("metadata", {}).get("langgraph_node")
                if node_name:
                    output_update = event["data"].get("output")
                    if isinstance(output_update, dict):
                        for k, v in output_update.items():
                            if k == "messages":
                                final_state[k] = list(final_state[k]) + list(v)
                            else:
                                final_state[k] = v

                    # Log the node execution to database
                    duration_ms = None
                    if node_name in node_timers:
                        duration_ms = int((time.perf_counter() - node_timers.pop(node_name)) * 1000)

                    status = "success"
                    error_msg = None
                    if isinstance(output_update, dict) and "error" in output_update and output_update["error"]:
                        status = "error"
                        error_msg = output_update["error"]

                    from app.models.agent_log import AgentLog
                    log = AgentLog(
                        id=uuid.uuid4(),
                        user_id=uuid.UUID(user_id),
                        conversation_id=uuid.UUID(conversation_id),
                        agent_name=node_name,
                        action="execute_node",
                        input_data={"current_step": final_state.get("current_step", 0)},
                        output_data=output_update if isinstance(output_update, dict) else {"output": str(output_update)},
                        duration_ms=duration_ms,
                        status=status,
                        error_message=error_msg
                    )
                    db.add(log)

    except Exception as e:
        logger.error(f"Streaming error on resume: {e}", exc_info=True)
        full_response = f"Sorry, I encountered an error running the agent plan: {type(e).__name__}"
        await manager.send_json(user_id, {
            "type": "token",
            "content": full_response,
        })

    # Save AI message
    ai_msg = Message(
        id=uuid.uuid4(),
        conversation_id=uuid.UUID(conversation_id),
        role="assistant",
        content=full_response,
        agent_name="planner",
        token_count=len(full_response.split()),
    )
    db.add(ai_msg)

    conv_uuid = uuid.UUID(conversation_id)
    conv = await get_conversation(db, conv_uuid, uuid.UUID(user_id))

    # Trigger memory consolidation if not paused for approval
    if not final_state.get("approval_required") and conv:
        from app.memory.consolidation import consolidate_conversation_memory
        try:
            await db.flush()
            await consolidate_conversation_memory(db, user.id, conv.id)
        except Exception as e:
            logger.warning(f"Failed to consolidate memory in WebSocket resume: {e}")

    if conv:
        conv.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # If it paused again (multi-step approvals)
    if final_state.get("approval_required"):
        pending_approvals[conversation_id] = final_state
        logger.info(f"[WebSocket] Resumed graph run paused again. Saved state.")
        
    await manager.send_json(user_id, {
        "type": "message_complete",
        "content": full_response,
        "metadata": {
            "conversation_id": conversation_id,
            "message_id": str(ai_msg.id),
            "approval_required": bool(final_state.get("approval_required"))
        },
    })
