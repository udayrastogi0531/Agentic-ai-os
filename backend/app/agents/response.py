"""
Uday AI — Response Node
"""

from __future__ import annotations

import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.llm.provider import get_llm
from app.agents.state import AgentState

logger = logging.getLogger(__name__)

RESPONSE_SYSTEM_PROMPT = """You are **Uday AI**, a highly capable, emotionally intelligent personal AI assistant.
Answer the user's query utilizing the context gathered from the execution of plan steps and memories.

## Context Gathered:
- User Memories:
{memory_context}

- Tool Outputs:
{tool_results_formatted}

## Guidelines:
- Answer naturally in a friendly, supportive tone (switching to Hinglish where appropriate).
- Do not mention internal tools or plan numbers (e.g., do not say "The notes tool returned..."). Instead say: "I checked your notes and found..."
- Address the user by their nickname if provided.
- Be concise, clean, and directly resolve the query.
"""


async def run_response_node(state: AgentState) -> dict:
    """
    Response Node.
    Synthesizes the plan execution outcomes, context memories,
    and user messages to generate the final response.
    """
    # Check if this run is paused for a confirmation gate
    if state.get("approval_required"):
        plan = state.get("plan", [])
        current_step = state.get("current_step", 0)
        step = plan[current_step] if current_step < len(plan) else {}
        tool = step.get("tool", "unknown")
        argument = step.get("argument", "")
        
        content = (
            f"🛡️ **Confirmation Required**\n\n"
            f"Before I proceed, I need your permission to run the following action:\n"
            f"- **Action**: {tool.upper()} execution\n"
            f"- **Details**: {argument}\n\n"
            f"Please approve or deny this action to continue."
        )
        logger.info(f"[Response Node] Action '{tool}' requires approval. Requesting confirmation.")
        return {
            "final_response": content,
            "messages": [AIMessage(content=content)]
        }

    logger.info("[Response Node] Compiling final response...")

    user_msg = state.get("user_message", "")
    memory_context = state.get("memory_context", "") or "No relevant memories found."
    tool_results = state.get("tool_results", {})

    # Format tool outputs
    if tool_results:
        tool_results_formatted = "\n".join(
            f"- Tool '{k}': {v}" for k, v in tool_results.items()
        )
    else:
        tool_results_formatted = "No tools were executed."

    system_prompt = RESPONSE_SYSTEM_PROMPT.format(
        memory_context=memory_context,
        tool_results_formatted=tool_results_formatted,
    )

    llm = get_llm(temperature=0.7)

    try:
        messages = [
            SystemMessage(content=system_prompt),
            *state.get("messages", []),
            HumanMessage(content=user_msg)
        ]
        response = await llm.ainvoke(messages)
        content = response.content
    except Exception as e:
        logger.error(f"[Response Node] LLM generation failed: {e}", exc_info=True)
        content = "I ran into a slight issue generating the final answer, but the action completed successfully."

    return {
        "final_response": content,
        "messages": [AIMessage(content=content)]
    }
