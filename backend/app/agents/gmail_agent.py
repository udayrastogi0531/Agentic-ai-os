"""
Uday AI — Gmail Agent

Gmail integration for email management.
Currently uses mock/placeholder - requires Google OAuth setup for real integration.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from app.agents.orchestrator import AgentState

logger = logging.getLogger(__name__)


async def run_gmail_agent(state: AgentState) -> dict:
    """Run the Gmail agent."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Gmail agent processing: {latest[:80]}")

    operation = _parse_email_intent(latest)
    result = await _handle_email(operation, latest)

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "gmail_agent": {"response": result, "operation": operation},
        },
        "final_response": result,
        "messages": [AIMessage(content=result)],
    }


def _parse_email_intent(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["read", "check", "inbox", "unread"]):
        return "read"
    elif any(w in msg for w in ["send", "compose", "write email"]):
        return "send"
    elif any(w in msg for w in ["draft", "prepare"]):
        return "draft"
    elif any(w in msg for w in ["summarize", "summary"]):
        return "summarize"
    elif any(w in msg for w in ["reply", "respond"]):
        return "reply"
    return "read"


async def _handle_email(operation: str, message: str) -> str:
    """Handle email operations."""
    if operation == "read":
        return (
            "📧 **Gmail Integration**\n\n"
            "To read your emails, please connect Gmail in Settings.\n\n"
            "📌 **Setup Instructions:**\n"
            "1. Go to Settings → Integrations\n"
            "2. Connect your Google account\n"
            "3. Grant Gmail access\n\n"
            "Once connected, I can:\n"
            "- Read and summarize your inbox\n"
            "- Draft and send emails\n"
            "- Search for specific emails\n"
            "- Reply to messages"
        )
    elif operation == "send":
        return (
            "📧 I'd love to send an email for you!\n\n"
            "Please provide:\n"
            "- **To**: Recipient email\n"
            "- **Subject**: Email subject\n"
            "- **Body**: What should the email say?\n\n"
            "I'll draft it first for your review before sending.\n\n"
            "Note: Connect Gmail in Settings for full integration."
        )
    elif operation == "draft":
        return (
            "📧 I'll help you draft an email.\n\n"
            "What should the email be about? Provide:\n"
            "- **To**: Who is it for?\n"
            "- **Context**: What do you want to communicate?\n"
            "- **Tone**: Professional, casual, formal?"
        )
    elif operation == "summarize":
        return (
            "📧 To summarize your emails, connect Gmail in Settings first.\n\n"
            "Once connected, I can provide:\n"
            "- Daily email digest\n"
            "- Important email highlights\n"
            "- Action items from emails"
        )
    else:
        return f"📧 Email `{operation}` operation noted. Connect Gmail for full functionality."
