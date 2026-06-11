"""
Uday AI — Research Agent

Web search, multi-source research, summarization, and report generation.
Uses DuckDuckGo search (free) with optional Tavily for deeper research.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from app.agents.orchestrator import AgentState
from app.llm.provider import get_llm

logger = logging.getLogger(__name__)

RESEARCH_PROMPT = """You are a research assistant. The user wants information about a topic.

Based on the search results provided, synthesize a comprehensive, well-structured answer.
Include key facts, different perspectives, and cite sources where possible.

If no search results are available, provide your best knowledge while noting that 
you couldn't verify with current web sources.

Always be thorough but concise. Use bullet points and headers for readability.
"""


async def run_research_agent(state: AgentState) -> dict:
    """Run the research agent for web search and analysis."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Research agent processing: {latest[:80]}")

    # Perform web search
    search_results = await _web_search(latest)

    # Synthesize response with LLM
    response = await _synthesize_research(latest, search_results)

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "research_agent": {
                "response": response,
                "sources": search_results,
            },
        },
        "final_response": response,
        "messages": [AIMessage(content=response)],
    }


async def _web_search(query: str) -> list[dict]:
    """Perform web search using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })

        logger.info(f"Web search returned {len(results)} results for: {query[:50]}")
        return results

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


async def _synthesize_research(query: str, results: list[dict]) -> str:
    """Synthesize search results into a coherent response."""
    llm = get_llm(temperature=0.3)

    sources_text = "\n\n".join(
        f"**{r['title']}** ({r['url']})\n{r['snippet']}"
        for r in results
    ) if results else "No web search results available."

    messages = [
        SystemMessage(content=RESEARCH_PROMPT),
        HumanMessage(content=f"""Research query: {query}

Search Results:
{sources_text}

Please provide a comprehensive answer based on these results."""),
    ]

    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Research synthesis failed: {e}")
        return f"I found some results but had trouble synthesizing them. Here are the raw sources:\n\n{sources_text}"
