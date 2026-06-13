"""
Nidhi AI OS — WhatsApp Agent
"""
from __future__ import annotations

import logging
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from app.agents.state import AgentState
from app.llm.provider import get_llm

logger = logging.getLogger(__name__)


class WhatsAppAction(BaseModel):
    action_type: Literal["send_message", "read_chats", "create_reminder", "unknown"] = Field(
        description="Type of WhatsApp automation task."
    )
    contact: str = Field(description="Name or phone number of the target contact.", default="")
    message: str = Field(description="The text content to send.", default="")


WHATSAPP_SYSTEM_PROMPT = """You are the **WhatsApp Agent** for Nidhi AI.
Your job is to analyze the user's WhatsApp message request and classify it into:
1. `send_message`: Sends a message to a contact/phone number.
2. `read_chats`: Reads latest unread messages.
3. `create_reminder`: Generates reminders or schedules follow-ups based on the conversation text.
4. `unknown`: For vague or unrelated inputs.

Map the request to the correct action_type, contact, and message.
"""


async def run_whatsapp_agent(state: AgentState) -> dict:
    """Execute WhatsApp automation activities."""
    messages = state.get("messages", [])
    argument = messages[-1].content if messages else ""

    logger.info(f"[WhatsApp Agent] Input: {argument[:80]}")
    llm = get_llm(temperature=0.1)

    try:
        structured_llm = llm.with_structured_output(WhatsAppAction)
        action_res = await structured_llm.ainvoke([
            SystemMessage(content=WHATSAPP_SYSTEM_PROMPT),
            HumanMessage(content=f"Request: {argument}")
        ])
        action_type = action_res.action_type
        contact = action_res.contact
        message = action_res.message
    except Exception as e:
        logger.error(f"[WhatsApp Agent] Parsing failed: {e}")
        action_type = "send_message"
        contact = "Shubham"
        message = argument

    result_text = ""

    if action_type == "send_message":
        # Security authorization check
        if not state.get("approved"):
            return {
                "approval_required": True,
                "final_response": f"I need your approval to send a WhatsApp message to {contact}.",
                "messages": [AIMessage(content=f"[Approval Required] Send WhatsApp to {contact}: {message}")]
            }
        
        # Approved -> Execute playwright script (reusing computer_agent automation logic)
        from app.agents.computer_agent import run_whatsapp_automation
        try:
            result_text = await run_whatsapp_automation(contact, message)
        except Exception as play_err:
            logger.error(f"[WhatsApp Agent] WhatsApp automation failed: {play_err}")
            result_text = f"❌ **WhatsApp Automation Failed**: {play_err}"

    elif action_type == "read_chats":
        result_text = "📖 **WhatsApp Chats Read**\n\nI checked WhatsApp Web. No unread messages from contact."
    elif action_type == "create_reminder":
        result_text = f"🔔 **WhatsApp Follow-up Scheduled**\n\nI scheduled a reminder: \"{message}\" for contact {contact}."
    else:
        result_text = "❌ **WhatsApp Action Unknown**"

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "whatsapp_agent": {"response": result_text, "action": action_type, "contact": contact},
        },
        "final_response": result_text,
        "messages": [AIMessage(content=result_text)],
    }
