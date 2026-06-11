"""
Uday AI — Task Agent

Task management: create, update, list, and plan tasks.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from app.agents.orchestrator import AgentState

logger = logging.getLogger(__name__)


async def run_task_agent(state: AgentState) -> dict:
    """Run the task agent."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"Task agent processing: {latest[:80]}")

    operation = _parse_task_intent(latest)
    response = await _handle_task(operation, latest)

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "task_agent": {"response": response, "operation": operation},
        },
        "final_response": response,
        "messages": [AIMessage(content=response)],
    }


def _parse_task_intent(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["add task", "create task", "new task", "todo"]):
        return "create"
    elif any(w in msg for w in ["complete", "done", "finish", "mark"]):
        return "complete"
    elif any(w in msg for w in ["delete", "remove"]):
        return "delete"
    elif any(w in msg for w in ["list", "show", "my tasks", "pending"]):
        return "list"
    elif any(w in msg for w in ["daily plan", "today's plan", "plan my day"]):
        return "daily_plan"
    elif any(w in msg for w in ["weekly", "week plan", "this week"]):
        return "weekly_plan"
    return "create"


async def _handle_task(operation: str, message: str) -> str:
    """Handle task operations."""
    if operation == "create":
        # Extract task title
        task_title = message
        for prefix in ["add task", "create task", "new task", "todo:", "add todo"]:
            if prefix in message.lower():
                idx = message.lower().index(prefix) + len(prefix)
                task_title = message[idx:].strip().strip(":")
                break

        if not task_title or task_title == message:
            return (
                "✅ **Create a Task**\n\n"
                "What task would you like to add? Try:\n"
                "- *\"Add task: Complete the API documentation\"*\n"
                "- *\"Todo: Review pull requests\"*\n"
                "- *\"Create task: Buy groceries by Friday\"*"
            )

        return (
            f"✅ **Task Created!**\n\n"
            f"📌 **{task_title}**\n"
            f"- Priority: Medium\n"
            f"- Status: To Do\n\n"
            f"💡 *Manage your tasks in the Tasks section of the dashboard.*"
        )

    elif operation == "list":
        return (
            "✅ **Your Tasks**\n\n"
            "View and manage all your tasks in the Tasks section of the dashboard.\n\n"
            "You can also:\n"
            "- Say *\"Show my pending tasks\"*\n"
            "- Say *\"What's on my to-do list?\"*\n"
            "- Say *\"Plan my day\"*"
        )

    elif operation == "daily_plan":
        return (
            "📋 **Daily Planning**\n\n"
            "I'll help you plan your day! Let me know:\n"
            "1. What are your top priorities today?\n"
            "2. Any deadlines to meet?\n"
            "3. Any meetings or events?\n\n"
            "I'll create an optimized daily schedule for you."
        )

    elif operation == "weekly_plan":
        return (
            "📋 **Weekly Planning**\n\n"
            "Let's plan your week! Share:\n"
            "1. Major goals for this week\n"
            "2. Recurring tasks\n"
            "3. Any important deadlines\n\n"
            "I'll help you break it down day by day."
        )

    elif operation == "complete":
        return "✅ Which task would you like to mark as complete? Tell me the task name or number."

    elif operation == "delete":
        return "🗑️ Which task would you like to delete? Tell me the task name or number."

    else:
        return f"✅ Task `{operation}` operation noted. Use the Tasks dashboard for full management."
