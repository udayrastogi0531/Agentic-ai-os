"""
Uday AI — LangGraph Orchestrator

The central multi-agent orchestration graph.
Routes user messages through the Planner to specialized agents.

Graph Flow:
  START → planner → [route to agent(s)] → planner (aggregate) → END
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, TypedDict, Literal

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# Agent State Schema
# ══════════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    """Shared state across all agent nodes in the graph."""

    # Core message history
    messages: Annotated[list[BaseMessage], add_messages]

    # User context
    user_id: str
    user_name: str
    user_nickname: str
    conversation_id: str

    # Planning
    intent: str  # Classified intent from planner
    plan: list[dict]  # Execution plan steps
    current_step: int  # Current step index

    # Agent results
    agent_results: dict[str, Any]  # Results keyed by agent name
    agent_name: str  # Currently active agent

    # Memory context
    memories: list[dict]  # Retrieved memories
    memory_context: str  # Formatted memory string

    # Final output
    final_response: str
    tool_calls_log: list[dict]

    # Error handling
    error: str | None


# ══════════════════════════════════════════════════════════════════════
# Intent Classification
# ══════════════════════════════════════════════════════════════════════

INTENT_KEYWORDS = {
    "memory_query": [
        "remember", "recall", "memory", "forgot", "what did i",
        "do you know", "my preference", "yaad", "batao jo",
    ],
    "research": [
        "search", "research", "find out", "look up", "what is",
        "who is", "explain", "tell me about", "khojo", "dhundo",
    ],
    "code": [
        "code", "program", "function", "debug", "fix this code",
        "write a script", "python", "javascript", "generate code",
    ],
    "file_op": [
        "file", "open file", "create file", "find file", "organize",
        "folder", "directory", "save file",
    ],
    "calendar": [
        "calendar", "schedule", "meeting", "event", "appointment",
        "remind me", "tomorrow", "next week",
    ],
    "email": [
        "email", "mail", "gmail", "inbox", "send email", "draft",
        "compose", "reply",
    ],
    "note": [
        "note", "write down", "jot", "save this", "notebook",
        "notes", "likh lo",
    ],
    "task": [
        "todo", "task", "to-do", "add task", "create task",
        "my tasks", "pending", "done", "complete",
    ],
    "browse": [
        "browse", "website", "open url", "web page", "scrape",
        "extract from",
    ],
    "direct_answer": [],  # fallback for general conversation
}


def classify_intent(message: str) -> str:
    """
    Classify user intent using keyword matching.
    Returns the most likely intent category.
    """
    message_lower = message.lower()
    scores: dict[str, int] = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in message_lower)
        scores[intent] = score

    # Return highest scoring intent, default to direct_answer
    max_score = max(scores.values()) if scores else 0
    if max_score == 0:
        return "direct_answer"

    return max(scores, key=scores.get)  # type: ignore


# ══════════════════════════════════════════════════════════════════════
# Agent Nodes
# ══════════════════════════════════════════════════════════════════════

async def planner_node(state: AgentState) -> dict:
    """
    Planner Agent — The brain of the system.
    Analyzes intent, decides which agent to invoke, aggregates results.
    """
    from app.agents.planner import run_planner
    return await run_planner(state)


async def memory_agent_node(state: AgentState) -> dict:
    """Memory Agent — Search and store memories."""
    from app.agents.memory_agent import run_memory_agent
    return await run_memory_agent(state)


async def research_agent_node(state: AgentState) -> dict:
    """Research Agent — Web search and summarization."""
    from app.agents.research_agent import run_research_agent
    return await run_research_agent(state)


async def coding_agent_node(state: AgentState) -> dict:
    """Coding Agent — Generate, explain, debug code."""
    from app.agents.coding_agent import run_coding_agent
    return await run_coding_agent(state)


async def file_agent_node(state: AgentState) -> dict:
    """File Agent — File operations."""
    from app.agents.file_agent import run_file_agent
    return await run_file_agent(state)


async def calendar_agent_node(state: AgentState) -> dict:
    """Calendar Agent — Calendar operations."""
    from app.agents.calendar_agent import run_calendar_agent
    return await run_calendar_agent(state)


async def gmail_agent_node(state: AgentState) -> dict:
    """Gmail Agent — Email operations."""
    from app.agents.gmail_agent import run_gmail_agent
    return await run_gmail_agent(state)


async def notes_agent_node(state: AgentState) -> dict:
    """Notes Agent — Note operations."""
    from app.agents.notes_agent import run_notes_agent
    return await run_notes_agent(state)


async def task_agent_node(state: AgentState) -> dict:
    """Task Agent — Task management."""
    from app.agents.task_agent import run_task_agent
    return await run_task_agent(state)


async def browser_agent_node(state: AgentState) -> dict:
    """Browser Agent — Web browsing."""
    from app.agents.browser_agent import run_browser_agent
    return await run_browser_agent(state)


# ══════════════════════════════════════════════════════════════════════
# Router Function
# ══════════════════════════════════════════════════════════════════════

def route_to_agent(state: AgentState) -> str:
    """Route from planner to the appropriate agent based on classified intent."""
    intent = state.get("intent", "direct_answer")

    route_map = {
        "memory_query": "memory_agent",
        "research": "research_agent",
        "code": "coding_agent",
        "file_op": "file_agent",
        "calendar": "calendar_agent",
        "email": "gmail_agent",
        "note": "notes_agent",
        "task": "task_agent",
        "browse": "browser_agent",
        "direct_answer": END,
    }

    destination = route_map.get(intent, END)
    logger.info(f"Routing to: {destination} (intent: {intent})")
    return destination


# ══════════════════════════════════════════════════════════════════════
# Build the Graph
# ══════════════════════════════════════════════════════════════════════

def build_agent_graph() -> StateGraph:
    """
    Build the LangGraph multi-agent orchestration graph.

    Flow:
      START → planner → (conditional routing) → agent → planner_aggregate → END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("memory_agent", memory_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("coding_agent", coding_agent_node)
    graph.add_node("file_agent", file_agent_node)
    graph.add_node("calendar_agent", calendar_agent_node)
    graph.add_node("gmail_agent", gmail_agent_node)
    graph.add_node("notes_agent", notes_agent_node)
    graph.add_node("task_agent", task_agent_node)
    graph.add_node("browser_agent", browser_agent_node)

    # Entry point
    graph.set_entry_point("planner")

    # Conditional routing from planner
    graph.add_conditional_edges(
        "planner",
        route_to_agent,
        {
            "memory_agent": "memory_agent",
            "research_agent": "research_agent",
            "coding_agent": "coding_agent",
            "file_agent": "file_agent",
            "calendar_agent": "calendar_agent",
            "gmail_agent": "gmail_agent",
            "notes_agent": "notes_agent",
            "task_agent": "task_agent",
            "browser_agent": "browser_agent",
            END: END,
        },
    )

    # All agents return to END (planner aggregates in its node)
    for agent in [
        "memory_agent", "research_agent", "coding_agent",
        "file_agent", "calendar_agent", "gmail_agent",
        "notes_agent", "task_agent", "browser_agent",
    ]:
        graph.add_edge(agent, END)

    return graph


# Compiled graph singleton
_compiled_graph = None


def get_agent_graph():
    """Get the compiled agent graph (singleton)."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_agent_graph()
        _compiled_graph = graph.compile()
        logger.info("✅ LangGraph agent graph compiled.")
    return _compiled_graph
