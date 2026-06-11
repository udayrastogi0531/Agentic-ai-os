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
    result = await _execute_email_operation(operation, latest, state.get("user_id"))

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


async def _execute_email_operation(operation: str, message: str, user_id: str | None) -> str:
    """Execute Gmail operations via MCP if enabled, else fall back to instructions."""
    from app.config import get_settings
    from app.mcp.client import mcp_manager

    settings = get_settings()
    use_mcp = settings.mcp_gmail_enabled

    if use_mcp:
        try:
            if operation == "read" or operation == "summarize":
                res = await mcp_manager.call_tool("gmail", "search_messages", {"query": "is:unread", "max_results": 5})
                content = res.get("content", [])
                if content:
                    return f"📧 **Unread Emails (Gmail MCP):**\n\n{content[0].get('text', '')}"
                return "📧 No unread emails found."
            
            elif operation == "send":
                # Call Gmail Send Tool (mock parameters parsed)
                res = await mcp_manager.call_tool("gmail", "send_message", {
                    "to": "udayrastogi0531@gmail.com", 
                    "subject": "Update from Uday AI", 
                    "body": message
                })
                content = res.get("content", [])
                if content:
                    return f"📧 **Email Sent (Gmail MCP):**\n\n{content[0].get('text', '')}"

            elif operation == "draft":
                res = await mcp_manager.call_tool("gmail", "create_draft", {
                    "to": "recipient@example.com",
                    "subject": "Draft from Uday AI",
                    "body": message
                })
                content = res.get("content", [])
                if content:
                    return f"📧 **Draft Created (Gmail MCP):**\n\n{content[0].get('text', '')}"
        except Exception as e:
            logger.warning(f"Gmail MCP call failed, using fallback instructions: {e}")

    # Fallback/Mock Setup Instructions
    if operation == "read":
        return (
            "📧 **Gmail Integration**\n\n"
            "To read your emails, please connect Gmail in Settings.\n\n"
            "Status: Gmail MCP client not configured.\n\n"
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
            "Status: Gmail MCP client not configured."
        )
    elif operation == "draft":
        return (
            "📧 I'll help you draft an email.\n\n"
            "What should the email be about? Provide:\n"
            "- **To**: Who is it for?\n"
            "- **Context**: What do you want to communicate?\n"
            "Status: Gmail MCP client not configured."
        )
    elif operation == "summarize":
        return (
            "📧 To summarize your emails, connect Gmail in Settings first.\n\n"
            "Status: Gmail MCP client not configured."
        )
    else:
        return f"📧 Email `{operation}` operation noted. Connect Gmail in Settings for full functionality."
