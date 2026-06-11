"""
Uday AI — LangGraph Core Graph Wiring
"""

from __future__ import annotations

import logging
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.planner import run_planner
from app.agents.memory import run_memory_node
from app.agents.tools import run_tools_node, run_evaluate_node, route_evaluation, run_replan_node
from app.agents.response import run_response_node
from app.agents.router import route_next

logger = logging.getLogger(__name__)


def build_agent_graph() -> StateGraph:
    """
    Build and compile the multi-agent graph logic.

    Flow:
      START -> memory -> planner -> [router edge] -> tools -> evaluate -> [eval edge] -> planner
                                                                                      -> replan -> planner
                                                                                      -> response -> END
                                                 -> response -> END
    """
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("memory", run_memory_node)
    workflow.add_node("planner", run_planner)
    workflow.add_node("tools", run_tools_node)
    workflow.add_node("evaluate", run_evaluate_node)
    workflow.add_node("replan", run_replan_node)
    workflow.add_node("response", run_response_node)

    # Establish entry point
    workflow.set_entry_point("memory")

    # Connect simple transitions
    workflow.add_edge("memory", "planner")
    workflow.add_edge("tools", "evaluate")
    workflow.add_edge("replan", "planner")

    # Connect conditional routing edges from planner
    workflow.add_conditional_edges(
        "planner",
        route_next,
        {
            "tools": "tools",
            "response": "response",
        }
    )

    # Connect conditional routing edges from evaluate
    workflow.add_conditional_edges(
        "evaluate",
        route_evaluation,
        {
            "planner": "planner",
            "replan": "replan",
            "response": "response",
        }
    )

    # End point
    workflow.add_edge("response", END)

    return workflow


# Compiled graph singleton cache
_compiled_graph = None


def get_agent_graph():
    """Retrieve the compiled agent graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        workflow = build_agent_graph()
        _compiled_graph = workflow.compile()
        logger.info("✅ Uday AI LangGraph agent compiled successfully.")
    return _compiled_graph
