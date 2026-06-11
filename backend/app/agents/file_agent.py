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
    elif any(w in msg_lower for w in ["create", "new file", "write", "save"]):
        return "create"
    elif any(w in msg_lower for w in ["read", "open", "show", "content"]):
        return "read"
    elif any(w in msg_lower for w in ["organize", "sort", "arrange", "move", "rename"]):
        return "organize"
    elif any(w in msg_lower for w in ["delete", "remove"]):
        return "delete"
    elif any(w in msg_lower for w in ["list", "directory", "folder"]):
        return "list"
    else:
        return "info"


async def _execute_file_operation(operation: str, message: str) -> str:
    """Execute a file operation, routing through MCP if enabled."""
    workspace = Path(settings.mcp_filesystem_root)
    workspace.mkdir(parents=True, exist_ok=True)
    
    from app.mcp.client import mcp_manager

    # Check if filesystem MCP is enabled
    use_mcp = settings.mcp_filesystem_enabled

    if operation == "list":
        if use_mcp:
            try:
                res = await mcp_manager.call_tool("filesystem", "list_directory", {"path": str(workspace)})
                content = res.get("content", [])
                if content:
                    return f"📁 **List Directory (MCP):**\n\n{content[0].get('text', '')}"
            except Exception as e:
                logger.warning(f"MCP list failed, using fallback: {e}")
        return _list_directory(workspace)

    elif operation == "search":
        query = message.lower().replace("search", "").replace("find", "").strip()
        if use_mcp:
            try:
                res = await mcp_manager.call_tool("filesystem", "find_by_name", {"path": str(workspace), "pattern": f"*{query}*"})
                content = res.get("content", [])
                if content:
                    return f"🔍 **Search Files (MCP):**\n\n{content[0].get('text', '')}"
            except Exception as e:
                logger.warning(f"MCP search failed, using fallback: {e}")
        return _search_files(workspace, query)

    elif operation == "read":
        # Extract filename/path
        parts = message.split()
        filename = parts[-1] if parts else ""
        file_path = workspace / filename
        
        if use_mcp:
            try:
                res = await mcp_manager.call_tool("filesystem", "read_file", {"path": str(file_path)})
                content = res.get("content", [])
                if content:
                    return f"📄 **Read File (MCP): `{filename}`**\n\n{content[0].get('text', '')}"
            except Exception as e:
                logger.warning(f"MCP read failed: {e}")
                
        # Native fallback
        try:
            if file_path.exists() and file_path.is_file():
                with open(file_path, "r", encoding="utf-8") as f:
                    return f"📄 **Read File: `{filename}`**\n\n{f.read(4000)}"
            return f"❌ File not found: `{filename}`"
        except Exception as e:
            return f"Error reading file: {e}"

    elif operation == "create":
        # Extract content & filename
        filename = "new_file.txt"
        file_content = message
        
        # Simple extraction logic
        if "file" in message.lower():
            match = re.search(r"file\s+(\S+)", message, re.IGNORECASE)
            if match:
                filename = match.group(1)
        
        file_path = workspace / filename
        
        if use_mcp:
            try:
                res = await mcp_manager.call_tool("filesystem", "write_file", {"path": str(file_path), "content": file_content})
                content = res.get("content", [])
                if content:
                    return f"💾 **Write File (MCP): `{filename}`**\n\n{content[0].get('text', '')}"
            except Exception as e:
                logger.warning(f"MCP write failed: {e}")

        # Native fallback
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            return f"💾 **File Created successfully:** `{filename}`"
        except Exception as e:
            return f"Error creating file: {e}"

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
