"""
Nidhi — Coding Agent

Code generation, explanation, debugging, and project creation.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.orchestrator import AgentState
from app.llm.provider import get_llm

logger = logging.getLogger(__name__)

CODING_PROMPT = """You are an expert software engineer. Help the user with their coding request.

Guidelines:
- Write clean, production-ready code
- Include comments for complex logic
- Follow best practices for the language
- If debugging, explain the root cause
- If explaining, use clear analogies
- Always include the language/framework in code blocks
- Provide working, testable code

Be thorough but concise. Explain your approach briefly before the code."""


async def run_coding_agent(state: AgentState) -> dict:
    """Run the coding agent."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Coding agent processing: {latest[:80]}")

    llm = get_llm(temperature=0.2, max_tokens=8192)

    lc_messages = [
        SystemMessage(content=CODING_PROMPT),
        *messages,
    ]

    try:
        response = await llm.ainvoke(lc_messages)
        result = response.content
    except Exception as e:
        logger.error(f"Coding agent error: {e}")
        result = f"I encountered an error generating code: {type(e).__name__}"

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "coding_agent": {"response": result},
        },
        "final_response": result,
        "messages": [AIMessage(content=result)],
    }
