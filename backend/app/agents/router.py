"""
Nidhi — Router Logic
"""

from __future__ import annotations

import logging
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def route_next(state: AgentState) -> str:
    """
    Decides the next execution node based on the current step in the execution plan.

    Transitions:
      - To 'tools' if there are pending tool execution steps in the plan.
      - To 'response' if the plan is complete or specifies 'direct_answer'.
    """
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    if not plan:
        logger.info("[Router] No plan found in state, routing to response node")
        return "response"

    if current_step >= len(plan):
        logger.info(f"[Router] Plan completed ({current_step}/{len(plan)} steps), routing to response node")
        return "response"

    next_step = plan[current_step]
    tool_name = next_step.get("tool", "direct_answer").lower()

    logger.info(f"[Router] Step {current_step + 1}/{len(plan)}: Routing to '{tool_name}'")

    if tool_name == "direct_answer":
        return "response"

    return "tools"
