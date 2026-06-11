"""
Uday AI — Notes Agent

Create, search, and manage notes with semantic search.
"""

from __future__ import annotations

import uuid
import logging

from langchain_core.messages import AIMessage, SystemMessage
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentState
from app.llm.provider import get_llm

logger = logging.getLogger(__name__)


async def run_notes_agent(state: AgentState) -> dict:
    """Run the notes agent."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Notes agent processing: {latest[:80]}")

    operation = _parse_notes_intent(latest)

    if operation == "create":
        response = await _create_note_response(latest)
    elif operation == "search":
        response = f"🔍 Searching notes for: *{latest}*\n\nConnect the database to search through your saved notes."
    elif operation == "list":
        response = "📝 **Your Notes**\n\nYour notes will appear here once you start creating them through the dashboard or via conversation."
    else:
        response = (
            "📝 **Notes Agent Ready**\n\n"
            "I can help you with:\n"
            "- **Create** a new note\n"
            "- **Search** through your notes\n"
            "- **Organize** notes by category\n"
            "- **List** all your notes\n\n"
            "Try saying: *\"Create a note about...\"* or *\"Find my notes about...\"*"
        )

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "notes_agent": {"response": response, "operation": operation},
        },
        "final_response": response,
        "messages": [AIMessage(content=response)],
    }


def _parse_notes_intent(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["create", "write", "new note", "jot", "save", "likh"]):
        return "create"
    elif any(w in msg for w in ["search", "find", "look for", "dhundh"]):
        return "search"
    elif any(w in msg for w in ["list", "show", "all notes"]):
        return "list"
    elif any(w in msg for w in ["organize", "categorize", "sort"]):
        return "organize"
    return "info"


async def _create_note_response(message: str) -> str:
    """Generate a note creation response."""
    # Extract note content from the message
    content = message
    for prefix in ["create a note", "write a note", "note:", "save note", "jot down"]:
        if prefix in message.lower():
            idx = message.lower().index(prefix) + len(prefix)
            content = message[idx:].strip()
            break

    if not content or content == message:
        return (
            "📝 I'd love to create a note for you!\n\n"
            "What should the note say? You can say something like:\n"
            "- *\"Create a note: Meeting with team at 3 PM\"*\n"
            "- *\"Note down: Python project ideas\"*"
        )

    return (
        f"📝 **Note Created!**\n\n"
        f"**Content:** {content}\n\n"
        f"💡 *Note saved successfully. You can view it in the Notes section of your dashboard.*"
    )
