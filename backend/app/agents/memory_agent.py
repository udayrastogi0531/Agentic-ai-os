"""
Nidhi — Memory Agent

Handles memory-related queries:
- Recall past information
- Store new memories
- Search for relevant context
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from app.agents.orchestrator import AgentState

logger = logging.getLogger(__name__)


async def run_memory_agent(state: AgentState) -> dict:
    """Run the memory agent to handle memory queries."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Memory agent processing: {latest[:80]}")

    # The memory context is already injected by the planner
    memories = state.get("memories", [])
    memory_context = state.get("memory_context", "")

    if memories:
        response = f"Here's what I remember:\n\n{memory_context}"
    else:
        response = (
            "I don't have any specific memories about that. "
            "As we talk more, I'll remember important things about you!"
        )

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "memory_agent": {"response": response, "memories_found": len(memories)},
        },
        "final_response": response,
        "messages": [AIMessage(content=response)],
    }
