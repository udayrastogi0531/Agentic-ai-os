"""
Uday AI — Browser Agent

Web browsing, information extraction, and research workflows.
Integrates with MCP Browser server when available.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from app.agents.orchestrator import AgentState

logger = logging.getLogger(__name__)


async def run_browser_agent(state: AgentState) -> dict:
    """Run the browser agent."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Browser agent processing: {latest[:80]}")

    # For now, delegate to research agent's web search
    from app.agents.research_agent import _web_search, _synthesize_research

    search_results = await _web_search(latest)
    response = await _synthesize_research(latest, search_results)

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "browser_agent": {"response": response, "sources": search_results},
        },
        "final_response": response,
        "messages": [AIMessage(content=response)],
    }
