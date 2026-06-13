"""
Nidhi — Memory Node
"""

from __future__ import annotations

import uuid
import logging

from app.database import async_session_factory
from app.memory.manager import MemoryManager
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


async def run_memory_node(state: AgentState) -> dict:
    """
    Memory Node.
    Queries the database/ChromaDB for semantic memories matching the query,
    enriching the graph state for planning and response nodes.
    """
    user_id_str = state.get("user_id")
    user_msg = state.get("user_message", "")

    if not user_id_str:
        logger.warning("[Memory Node] No user_id in state, skipping memory retrieval")
        return {"retrieved_memories": [], "memory_context": ""}

    logger.info(f"[Memory Node] Retrieving memories for query: {user_msg[:80]}")

    try:
        user_uuid = uuid.UUID(user_id_str)
        async with async_session_factory() as db:
            mgr = MemoryManager(db)
            memories = await mgr.search_memories(
                user_id=user_uuid,
                query=user_msg,
                limit=5,
            )
            context = await mgr.get_context_memories(
                user_id=user_uuid,
                message=user_msg,
                limit=5,
            )

            # Query User Knowledge Graph connections
            from app.knowledge.graph import query_graph_context
            graph_context = await query_graph_context(db, user_uuid, user_msg)
            if graph_context:
                context = f"{context}\n\n{graph_context}"

        logger.info(f"[Memory Node] Retrieved {len(memories)} relevant memories.")
    except Exception as e:
        logger.error(f"[Memory Node] Failed to retrieve memories: {e}", exc_info=True)
        memories = []
        context = ""

    return {
        "retrieved_memories": memories,
        "memory_context": context,
    }
