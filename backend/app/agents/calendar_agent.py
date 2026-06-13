"""
Uday AI — Calendar Agent

Google Calendar integration for event management.
Currently uses mock/placeholder - requires Google OAuth setup for real integration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from langchain_core.messages import AIMessage

from app.agents.orchestrator import AgentState

logger = logging.getLogger(__name__)


async def run_calendar_agent(state: AgentState) -> dict:
    """Run the calendar agent."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Calendar agent processing: {latest[:80]}")

    operation = _parse_calendar_intent(latest)
    result = await _execute_calendar_operation(operation, latest, state.get("user_id"))

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


async def _execute_calendar_operation(operation: str, message: str, user_id: Any | None) -> str:
    """Execute Calendar operations via MCP if enabled, else fall back to instructions."""
    from app.config import get_settings
    from app.mcp.client import mcp_manager

    settings = get_settings()
    use_mcp = settings.mcp_calendar_enabled
    now = datetime.now(timezone.utc)

    if use_mcp:
        try:
            if operation == "today":
                # List events for today
                t_min = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                t_max = now.replace(hour=23, minute=59, second=59, microsecond=999).isoformat()
                res = await mcp_manager.call_tool("calendar", "list_events", {"calendar_id": "primary", "time_min": t_min, "time_max": t_max}, user_id=user_id)
                content = res.get("content", [])
                if content:
                    return f"📅 **Today's Events (Calendar MCP):**\n\n{content[0].get('text', '')}"
                return f"📅 No events scheduled for today ({now.strftime('%B %d, %Y')})."
            
            elif operation == "create":
                # Create an event summary (mock parameters parsed)
                start_t = (now + timedelta(hours=1)).isoformat()
                end_t = (now + timedelta(hours=2)).isoformat()
                res = await mcp_manager.call_tool("calendar", "create_event", {
                    "calendar_id": "primary",
                    "summary": f"Event: {message[:50]}",
                    "start_time": start_t,
                    "end_time": end_t
                }, user_id=user_id)
                content = res.get("content", [])
                if content:
                    return f"📅 **Event Scheduled (Calendar MCP):**\n\n{content[0].get('text', '')}"

            elif operation == "tomorrow":
                tomorrow = now + timedelta(days=1)
                t_min = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                t_max = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999).isoformat()
                res = await mcp_manager.call_tool("calendar", "list_events", {"calendar_id": "primary", "time_min": t_min, "time_max": t_max}, user_id=user_id)
                content = res.get("content", [])
                if content:
                    return f"📅 **Tomorrow's Events (Calendar MCP):**\n\n{content[0].get('text', '')}"
                return f"📅 No events scheduled for tomorrow ({tomorrow.strftime('%B %d, %Y')})."

            elif operation == "week":
                t_min = now.isoformat()
                t_max = (now + timedelta(days=7)).isoformat()
                res = await mcp_manager.call_tool("calendar", "list_events", {"calendar_id": "primary", "time_min": t_min, "time_max": t_max}, user_id=user_id)
                content = res.get("content", [])
                if content:
                    return f"📅 **Weekly Schedule (Calendar MCP):**\n\n{content[0].get('text', '')}"
        except Exception as e:
            logger.warning(f"Calendar MCP call failed, using fallback instructions: {e}")

    # Fallback/Mock Setup Instructions
    if operation == "today":
        return (
            f"📅 **Today's Schedule ({now.strftime('%A, %B %d, %Y')})**\n\n"
            f"To see your real calendar, please connect Google Calendar in Settings.\n\n"
            f"Status: Calendar MCP client not configured.\n\n"
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
            "- **Duration**: How long?\n\n"
            "Status: Calendar MCP client not configured."
        )
    elif operation == "tomorrow":
        tomorrow = now + timedelta(days=1)
        return (
            f"📅 **Tomorrow's Schedule ({tomorrow.strftime('%A, %B %d, %Y')})**\n\n"
            f"Status: Calendar MCP client not configured."
        )
    elif operation == "week":
        return (
            f"📅 **This Week's Schedule**\n\n"
            f"Status: Calendar MCP client not configured."
        )
    else:
        return f"📅 Calendar `{operation}` operation noted. Connect Google Calendar in Settings for full functionality."
