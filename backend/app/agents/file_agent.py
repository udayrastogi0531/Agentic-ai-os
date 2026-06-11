"""
Uday AI — File Agent

File system operations: search, read, create, organize files.
Integrates with MCP Filesystem server when available.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path

from langchain_core.messages import AIMessage

from app.agents.orchestrator import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_file_agent(state: AgentState) -> dict:
    """Run the file agent for file operations."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""

    logger.info(f"File agent processing: {latest[:80]}")

    # Parse the file operation intent
    operation = _parse_file_operation(latest)
    result = await _execute_file_operation(operation, latest)

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "file_agent": {"response": result, "operation": operation},
        },
        "final_response": result,
        "messages": [AIMessage(content=result)],
    }


def _parse_file_operation(message: str) -> str:
    """Determine the file operation type."""
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["search", "find", "locate", "where"]):
        return "search"
    elif any(w in msg_lower for w in ["create", "new file", "write"]):
        return "create"
    elif any(w in msg_lower for w in ["read", "open", "show", "content"]):
        return "read"
    elif any(w in msg_lower for w in ["organize", "sort", "arrange", "move"]):
        return "organize"
    elif any(w in msg_lower for w in ["delete", "remove"]):
        return "delete"
    elif any(w in msg_lower for w in ["list", "directory", "folder"]):
        return "list"
    else:
        return "info"


async def _execute_file_operation(operation: str, message: str) -> str:
    """Execute a file operation."""
    workspace = Path(settings.mcp_filesystem_root)
    workspace.mkdir(parents=True, exist_ok=True)

    if operation == "list":
        return _list_directory(workspace)
    elif operation == "search":
        query = message.lower().replace("search", "").replace("find", "").strip()
        return _search_files(workspace, query)
    elif operation == "info":
        return (
            f"📁 **File Agent Ready**\n\n"
            f"I can help you with:\n"
            f"- **Search** files by name or content\n"
            f"- **Create** new files\n"
            f"- **Read** file contents\n"
            f"- **List** directory contents\n"
            f"- **Organize** files into folders\n\n"
            f"Workspace: `{workspace}`\n\n"
            f"What would you like to do?"
        )
    else:
        return f"I'll help with the `{operation}` operation. Please provide more details about the file path or name."


def _list_directory(path: Path) -> str:
    """List contents of a directory."""
    try:
        items = sorted(path.iterdir())
        if not items:
            return f"📂 `{path}` is empty."

        lines = [f"📂 **Contents of `{path}`:**\n"]
        for item in items[:50]:  # Limit to 50 items
            icon = "📁" if item.is_dir() else "📄"
            size = f" ({item.stat().st_size:,} bytes)" if item.is_file() else ""
            lines.append(f"  {icon} `{item.name}`{size}")

        if len(items) > 50:
            lines.append(f"\n  ... and {len(items) - 50} more items")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing directory: {e}"


def _search_files(root: Path, query: str) -> str:
    """Search for files matching a query."""
    matches = []
    try:
        for path in root.rglob("*"):
            if query in path.name.lower():
                matches.append(path)
            if len(matches) >= 20:
                break

        if not matches:
            return f"🔍 No files found matching `{query}`"

        lines = [f"🔍 **Found {len(matches)} file(s) matching `{query}`:**\n"]
        for m in matches:
            icon = "📁" if m.is_dir() else "📄"
            rel = m.relative_to(root)
            lines.append(f"  {icon} `{rel}`")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching files: {e}"
