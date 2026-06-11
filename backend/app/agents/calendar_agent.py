"""
Uday AI — Calendar Agent

Google Calendar integration for event management.
Currently uses mock/placeholder - requires Google OAuth setup for real integration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from langchain_core.messages import AIMessage

from app.agents.orchestrator import AgentState

logger = logging.getLogger(__name__)


async def run_calendar_agent(state: AgentState) -> dict:
    """Run the calendar agent."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Calendar agent processing: {latest[:80]}")

    operation = _parse_calendar_intent(latest)
    result = await _handle_calendar(operation, latest)

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "calendar_agent": {"response": result, "operation": operation},
        },
        "final_response": result,
        "messages": [AIMessage(content=result)],
    }


def _parse_calendar_intent(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["create", "add", "schedule", "book"]):
        return "create"
    elif any(w in msg for w in ["today", "schedule", "agenda", "what's on"]):
        return "today"
    elif any(w in msg for w in ["tomorrow"]):
        return "tomorrow"
    elif any(w in msg for w in ["update", "change", "modify", "reschedule"]):
        return "update"
    elif any(w in msg for w in ["delete", "cancel", "remove"]):
        return "delete"
    elif any(w in msg for w in ["week", "weekly"]):
        return "week"
    return "today"


async def _handle_calendar(operation: str, message: str) -> str:
    """Handle calendar operations."""
    now = datetime.now(timezone.utc)

    if operation == "today":
        return (
            f"📅 **Today's Schedule ({now.strftime('%A, %B %d, %Y')})**\n\n"
            f"To see your real calendar, please connect Google Calendar in Settings.\n\n"
            f"📌 **Setup Instructions:**\n"
            f"1. Go to Settings → Integrations\n"
            f"2. Connect your Google account\n"
            f"3. Grant Calendar access\n\n"
            f"Once connected, I can:\n"
            f"- Show your daily/weekly schedule\n"
            f"- Create and manage events\n"
            f"- Set reminders\n"
            f"- Find free time slots"
        )
    elif operation == "create":
        return (
            "📅 I'd love to create an event for you!\n\n"
            "Please provide:\n"
            "- **Title**: What's the event?\n"
            "- **Date/Time**: When?\n"
            "- **Duration**: How long?\n"
            "- **Description** (optional)\n\n"
            "Note: Connect Google Calendar in Settings for full integration."
        )
    elif operation == "tomorrow":
        tomorrow = now + timedelta(days=1)
        return (
            f"📅 **Tomorrow's Schedule ({tomorrow.strftime('%A, %B %d, %Y')})**\n\n"
            f"Connect Google Calendar in Settings to see your real schedule."
        )
    elif operation == "week":
        return (
            f"📅 **This Week's Schedule**\n\n"
            f"Connect Google Calendar in Settings to see your weekly view."
        )
    else:
        return f"📅 Calendar `{operation}` operation noted. Connect Google Calendar for full functionality."
