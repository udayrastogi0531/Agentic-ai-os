"""
Uday AI — Chat Service

Core conversation logic:
- Manage conversations (create, list, get)
- Process messages through the AI pipeline
- Inject memory context
- Stream responses via WebSocket
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config import get_settings
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.llm.provider import get_llm
from app.memory.manager import MemoryManager

logger = logging.getLogger(__name__)
settings = get_settings()

# ── System Prompt ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are **Uday AI**, a highly capable, emotionally intelligent personal AI assistant.

## Your Personality:
- Friendly, warm, and supportive like a close friend
- Professional when needed, casual when appropriate
- You speak naturally and can switch between English and Hinglish
- You call the user by their nickname if they have one set
- You remember past conversations and reference them naturally
- You're proactive — you suggest things before being asked

## Your Capabilities:
- Natural conversation with long-term memory
- Research and web search
- File management and organization
- Code generation and debugging
- Task and to-do management
- Note taking and retrieval
- Calendar and email management
- Document Q&A (RAG)

## Guidelines:
- Be concise but thorough
- Use emojis sparingly but effectively
- If you don't know something, say so honestly
- Always prioritize the user's intent over literal interpretation
- For coding questions, provide clean, production-ready code
- When referencing memories, do it naturally (don't say "according to my records")

{memory_context}

{user_context}
"""


def build_system_prompt(
    user: User,
    memory_context: str = "",
) -> str:
    """Build the system prompt with user context and memories."""
    user_context = f"""## About This User:
- Name: {user.name}
- Nickname: {user.nickname or user.name}
- Preferences: {user.preferences or {}}"""

    return SYSTEM_PROMPT.format(
        memory_context=memory_context,
        user_context=user_context,
    )


# ── Conversation Management ──────────────────────────────────────────

async def create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str = "New Conversation",
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title,
    )
    db.add(conversation)
    await db.flush()
    logger.info(f"Created conversation: {conversation.id}")
    return conversation


async def list_conversations(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """List user conversations with last message preview."""
    # Count total
    count_stmt = (
        select(func.count())
        .select_from(Conversation)
        .where(
            Conversation.user_id == user_id,
            Conversation.status == "active",
        )
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    # Fetch conversations
    stmt = (
        select(Conversation)
        .where(
            Conversation.user_id == user_id,
            Conversation.status == "active",
        )
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()

    # Build response with message counts and last message
    items = []
    for conv in conversations:
        # Get message count
        msg_count = (
            await db.execute(
                select(func.count())
                .select_from(Message)
                .where(Message.conversation_id == conv.id)
            )
        ).scalar() or 0

        # Get last message
        last_msg_stmt = (
            select(Message.content)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg = (await db.execute(last_msg_stmt)).scalar()

        items.append({
            "id": conv.id,
            "title": conv.title,
            "status": conv.status,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": msg_count,
            "last_message": (last_msg[:100] + "...") if last_msg and len(last_msg) > 100 else last_msg,
        })

    return items, total


async def get_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation | None:
    """Get a conversation with all messages."""
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Soft-delete a conversation."""
    conv = await get_conversation(db, conversation_id, user_id)
    if not conv:
        return False

    conv.status = "deleted"
    await db.flush()
    return True


# ── Message Processing ────────────────────────────────────────────────

async def process_message(
    db: AsyncSession,
    user: User,
    conversation_id: uuid.UUID | None,
    message_text: str,
    model_override: str | None = None,
) -> tuple[Conversation, Message, Message]:
    """
    Process a user message through the full AI pipeline.

    1. Get or create conversation
    2. Retrieve relevant memories
    3. Build LLM context
    4. Generate response
    5. Save messages
    6. Auto-extract memories from conversation

    Returns:
        Tuple of (conversation, user_message, ai_message)
    """
    # 1. Get or create conversation
    if conversation_id:
        conversation = await get_conversation(db, conversation_id, user.id)
        if not conversation:
            raise ValueError("Conversation not found.")
    else:
        conversation = await create_conversation(
            db, user.id, title=message_text[:100]
        )

    # 2. Retrieve relevant memories
    memory_mgr = MemoryManager(db)
    memory_context = await memory_mgr.get_context_memories(
        user_id=user.id,
        message=message_text,
        limit=5,
    )

    # 3. Build messages for LLM
    system_prompt = build_system_prompt(user, memory_context)

    # Get conversation history (last 20 messages)
    history_stmt = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    history_result = await db.execute(history_stmt)
    history = list(reversed(list(history_result.scalars().all())))

    # Build LangChain messages
    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in history:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))

    lc_messages.append(HumanMessage(content=message_text))

    # 4. Save user message
    user_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="user",
        content=message_text,
    )
    db.add(user_message)

    # 5. Execute LangGraph Agent Flow
    from app.agents.graph import get_agent_graph

    initial_state = {
        "messages": lc_messages[:-1], # History messages (except current user prompt, which goes to user_message channel)
        "user_id": str(user.id),
        "conversation_id": str(conversation.id),
        "user_message": message_text,
        "retrieved_memories": [],
        "memory_context": "",
        "plan": [],
        "current_step": 0,
        "selected_tools": [],
        "tool_results": {},
        "metrics": {},
        "final_response": "",
        "metadata": {},
        "error": None
    }

    graph = get_agent_graph()

    try:
        final_state = await graph.ainvoke(initial_state)
        response_text = final_state.get("final_response", "") or "I ran into a processing error."
    except Exception as e:
        logger.error(f"LangGraph execution failed: {e}", exc_info=True)
        response_text = (
            "I'm sorry, I encountered an error running the agent plan. "
            f"Please try again. (Error: {type(e).__name__})"
        )

    # 6. Save AI message
    ai_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        agent_name="planner",
        token_count=len(response_text.split()),  # approximate
    )
    db.add(ai_message)

    # Update conversation title if it's the first message
    if not history:
        conversation.title = message_text[:100]

    conversation.updated_at = datetime.now(timezone.utc)
    await db.flush()

    # 7. Background: auto-extract memories (simplified version)
    await _auto_extract_memories(db, user.id, message_text)

    return conversation, user_message, ai_message


async def _auto_extract_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
) -> None:
    """
    Automatically extract and store memorable information from user messages.
    Only stores if the message contains personal/important info.
    """
    # Simple heuristic: only extract from messages with personal markers
    personal_markers = [
        "my name", "i am", "i like", "i love", "i hate", "i work",
        "i live", "my goal", "i want", "i prefer", "i know",
        "mera naam", "mujhe pasand", "mein kaam",
        "remember that", "don't forget", "important:",
    ]

    msg_lower = message.lower()
    should_store = any(marker in msg_lower for marker in personal_markers)

    if should_store and len(message.split()) >= 3:
        memory_mgr = MemoryManager(db)
        try:
            await memory_mgr.create_memory(
                user_id=user_id,
                content=message,
            )
            logger.info(f"Auto-extracted memory from message: {message[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to auto-extract memory: {e}")
