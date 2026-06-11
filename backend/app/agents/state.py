"""
Uday AI — LangGraph Agent State
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Centralized state definition governing LangGraph nodes and execution paths.
    """
    # Core conversation message streams
    messages: Annotated[list[BaseMessage], add_messages]

    # Context identifiers
    user_id: str
    conversation_id: str

    # User input query
    user_message: str

    # Retain retrieved memory context
    retrieved_memories: list[dict[str, Any]]
    memory_context: str

    # Planned execution steps
    plan: list[dict[str, Any]]
    current_step: int

    # Active tool selection
    selected_tools: list[str]
    tool_results: dict[str, Any]

    # Latency tracking
    metrics: dict[str, float]

    # Output details
    final_response: str
    metadata: dict[str, Any]

    # Caught exceptions
    error: Optional[str]

    # Confirmation gate
    approval_required: Optional[bool]
    approved: Optional[bool]

    # Cycle and loop tracking
    loop_count: int

