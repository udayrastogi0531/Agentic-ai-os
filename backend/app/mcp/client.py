"""
Uday AI — MCP Client Manager

Handles starting enabled MCP servers as subprocesses (stdio transport),
negotiates tools list, and invokes actions over JSON-RPC.
"""

from __future__ import annotations

import json
import uuid
import logging
import asyncio
import os
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MCPServerProcess:
    """Manages a single running MCP server subprocess (stdio transport)."""

    def __init__(self, name: str, command: str, args: list[str], env: dict[str, str] | None = None):
        self.name = name
        self.command = command
        self.args = args
        self.env = env or {}
        self.proc: asyncio.subprocess.Process | None = None
        self.read_task: asyncio.Task | None = None
        self.read_stderr_task: asyncio.Task | None = None
        self.futures: dict[str, asyncio.Future] = {}

    async def start(self) -> None:
        """Start the MCP subprocess, launch workers, and execute initialization handshake."""
        # Merge system environment to inherit npx path
        merged_env = os.environ.copy()
        merged_env.update(self.env)

        logger.info(f"[MCP] Starting server subprocess '{self.name}': {self.command} {' '.join(self.args)}")
        
        self.proc = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=merged_env
        )

        # Launch background loops reading stdout and stderr
        self.read_task = asyncio.create_task(self._read_stdout_loop())
        self.read_stderr_task = asyncio.create_task(self._read_stderr_loop())
        logger.info(f"[MCP] Server subprocess '{self.name}' successfully started (PID: {self.proc.pid})")

        # Perform MCP initialization handshake
        try:
            logger.info(f"[MCP] Initializing server '{self.name}'...")
            init_result = await self.call_method(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": False},
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "uday-ai",
                        "version": "1.0.0"
                    }
                }
            )
            logger.info(f"[MCP] Server '{self.name}' initialization response received: {init_result}")
            await self.send_notification("notifications/initialized", {})
            logger.info(f"[MCP] Server '{self.name}' fully initialized and handshake completed.")
        except Exception as e:
            logger.error(f"[MCP] Handshake failed for server '{self.name}': {e}")
            await self.stop()
            raise

    async def _read_stdout_loop(self) -> None:
        """Background worker reading JSON-RPC packets line-by-line from stdout."""
        if not self.proc or not self.proc.stdout:
            return

        while True:
            try:
                line = await self.proc.stdout.readline()
                if not line:
                    logger.warning(f"[MCP] Server '{self.name}' stdout pipe closed.")
                    break

                # Parse JSON-RPC response
                try:
                    response = json.loads(line.decode().strip())
                except json.JSONDecodeError:
                    continue

                # Match with pending future using ID
                req_id = str(response.get("id"))
                if req_id in self.futures:
                    future = self.futures.pop(req_id)
                    if not future.done():
                        if "error" in response:
                            future.set_exception(Exception(response["error"].get("message", "Unknown error")))
                        else:
                            future.set_result(response.get("result"))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[MCP] Error reading server '{self.name}' stdout: {e}")
                break

    async def _read_stderr_loop(self) -> None:
        """Background worker reading logs/errors from stderr to prevent blocking."""
        if not self.proc or not self.proc.stderr:
            return

        while True:
            try:
                line = await self.proc.stderr.readline()
                if not line:
                    break
                decoded_line = line.decode().strip()
                if decoded_line:
                    logger.warning(f"[MCP {self.name} stderr] {decoded_line}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[MCP] Error reading server '{self.name}' stderr: {e}")
                break

    async def call_method(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send a JSON-RPC request packet and await response matching."""
        if not self.proc or not self.proc.stdin:
            raise RuntimeError(f"Server '{self.name}' is not running.")

        req_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }

        # Register future
        future = asyncio.get_running_loop().create_future()
        self.futures[req_id] = future

        # Send packet
        payload = json.dumps(request) + "\n"
        self.proc.stdin.write(payload.encode())
        await self.proc.stdin.drain()

        # Await future
        try:
            return await asyncio.wait_for(future, timeout=15.0)
        except asyncio.TimeoutError:
            self.futures.pop(req_id, None)
            raise TimeoutError(f"MCP tool call '{method}' timed out after 15 seconds.")

    async def send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a JSON-RPC notification packet (no id, no response expected)."""
        if not self.proc or not self.proc.stdin:
            raise RuntimeError(f"Server '{self.name}' is not running.")

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }

        # Send packet
        payload = json.dumps(request) + "\n"
        self.proc.stdin.write(payload.encode())
        await self.proc.stdin.drain()

    async def stop(self) -> None:
        """Terminate process and cancel logs reader."""
        if self.read_task:
            self.read_task.cancel()
        if self.read_stderr_task:
            self.read_stderr_task.cancel()
        if self.proc:
            try:
                self.proc.terminate()
                await self.proc.wait()
            except Exception:
                pass
        self.proc = None
        self.futures.clear()

    def is_running(self) -> bool:
        """Check if the subprocess is currently active."""
        return self.proc is not None and self.proc.returncode is None


class MCPClientManager:
    """Manages MCP server lifecycle and client-side tool discovery/calling."""

    def __init__(self):
        self._servers: dict[str, MCPServerProcess] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Starts enabled MCP servers (skips user-specific servers)."""
        if self._initialized:
            return

        server_configs = self._get_server_configs()

        for name, config in server_configs.items():
            if name in ["gmail", "calendar"]:
                # Skipped during global startup; initialized per-user on demand in call_tool
                continue
            if config.get("enabled", False):
                try:
                    server = MCPServerProcess(
                        name=name,
                        command=config["command"],
                        args=config["args"],
                        env=config.get("env")
                    )
                    await server.start()
                    
                    # Fetch initial tools list from server to verify health
                    result = await server.call_method("tools/list")
                    tools_list = result.get("tools", [])
                    
                    logger.info(f"✅ MCP server '{name}' registered with {len(tools_list)} tools.")
                    self._servers[name] = server
                except Exception as e:
                    logger.warning(f"⚠️ MCP server '{name}' failed to start: {e}")

        self._initialized = True

    def _get_server_configs(self) -> dict[str, dict]:
        """Fetch settings configurations."""
        return {
            "filesystem": {
                "enabled": settings.mcp_filesystem_enabled,
                "command": "npx" if os.name != "nt" else "npx.cmd",  # Support Windows shell executable
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(settings.mcp_filesystem_root),
                ],
                "description": "File system operations",
            },
            "github": {
                "enabled": settings.mcp_github_enabled and bool(settings.github_token),
                "command": "npx" if os.name != "nt" else "npx.cmd",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-github",
                ],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": settings.github_token},
                "description": "GitHub repository integration",
            },
            "browser": {
                "enabled": settings.mcp_browser_enabled,
                "command": "npx" if os.name != "nt" else "npx.cmd",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-playwright",
                ],
                "description": "Playwright browser control",
            },
            "gmail": {
                "enabled": settings.mcp_gmail_enabled,
                "command": "npx" if os.name != "nt" else "npx.cmd",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-gmail",
                ],
                "env": {
                    "GOOGLE_CLIENT_ID": settings.google_client_id,
                    "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
                },
                "description": "Gmail integration",
            },
            "calendar": {
                "enabled": settings.mcp_calendar_enabled,
                "command": "npx" if os.name != "nt" else "npx.cmd",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-google-calendar",
                ],
                "env": {
                    "GOOGLE_CLIENT_ID": settings.google_client_id,
                    "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
                },
                "description": "Google Calendar integration",
            },
        }

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: Any | None = None,
    ) -> Any:
        """Call a specific tool on an active MCP server, handling user-specific servers on demand."""
        server_key = server_name
        user_env = None
        current_access_token = None

        if server_name in ["gmail", "calendar"]:
            if not user_id:
                raise ValueError(f"user_id is required to invoke user-specific MCP server '{server_name}'")
            
            # Ensure user_id is UUID
            if isinstance(user_id, str):
                try:
                    user_id = uuid.UUID(user_id)
                except ValueError:
                    raise ValueError(f"Invalid UUID user_id format: {user_id}")

            server_key = f"{server_name}:{user_id}"

            # Fetch valid/refreshed tokens from database
            from app.database import async_session_factory
            from app.services.oauth_service import get_valid_google_token
            from app.security.encryption import decrypt_token
            from sqlalchemy import select
            from app.models.user_token import UserToken

            async with async_session_factory() as session:
                current_access_token = await get_valid_google_token(session, user_id)
                if not current_access_token:
                    raise ValueError(f"Google account is not connected or authorization is invalid for user '{user_id}'")

                # Fetch refresh token as well for the server
                stmt = select(UserToken).where(
                    UserToken.user_id == user_id,
                    UserToken.service == "google"
                )
                res = await session.execute(stmt)
                ut = res.scalar_one_or_none()
                refresh_token = decrypt_token(ut.encrypted_refresh_token) if ut else None

            # Build credentials env dict
            user_env = {
                "GOOGLE_CLIENT_ID": settings.google_client_id,
                "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
                "GOOGLE_ACCESS_TOKEN": current_access_token,
                "GOOGLE_REFRESH_TOKEN": refresh_token or "",
                "GMAIL_CLIENT_ID": settings.google_client_id,
                "GMAIL_CLIENT_SECRET": settings.google_client_secret,
                "GMAIL_ACCESS_TOKEN": current_access_token,
                "GMAIL_REFRESH_TOKEN": refresh_token or "",
                "ACCESS_TOKEN": current_access_token,
                "REFRESH_TOKEN": refresh_token or "",
            }

        server = self._servers.get(server_key)

        # Check if we need to restart/recreate due to access token rotation
        if server and server.is_running() and current_access_token:
            previous_token = getattr(server, "_access_token", None)
            if previous_token != current_access_token:
                logger.info(f"[MCP] Restarting user-specific server '{server_key}' due to token rotation.")
                await server.stop()
                self._servers.pop(server_key, None)
                server = None

        # Start server if not running
        if not server or not server.is_running():
            configs = self._get_server_configs()
            if server_name in configs and configs[server_name].get("enabled"):
                try:
                    if server:
                        await server.stop()

                    config = configs[server_name]
                    merged_env = config.get("env", {}).copy()
                    if user_env:
                        merged_env.update(user_env)

                    logger.info(f"[MCP] Initializing dynamic instance for '{server_key}'...")
                    new_server = MCPServerProcess(
                        name=server_name,
                        command=config["command"],
                        args=config["args"],
                        env=merged_env
                    )
                    await new_server.start()
                    if current_access_token:
                        setattr(new_server, "_access_token", current_access_token)
                    
                    self._servers[server_key] = new_server
                    server = new_server
                except Exception as e:
                    logger.error(f"[MCP] Failed to start dynamic instance '{server_key}': {e}")
                    raise RuntimeError(f"MCP server '{server_name}' could not start: {e}")
            else:
                raise ValueError(f"MCP server is not configured or enabled: {server_name}")

        return await server.call_method("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

    async def list_tools(self, server_name: str | None = None) -> list[dict]:
        """Enumerate tools list with validation check."""
        all_tools = []
        for name, server in self._servers.items():
            # Exclude user-specific key matches if prefix doesn't match
            clean_name = name.split(":")[0]
            if server_name and clean_name != server_name:
                continue
            if not server.is_running():
                continue
            try:
                result = await server.call_method("tools/list")
                for tool in result.get("tools", []):
                    all_tools.append({"server": clean_name, **tool})
            except Exception as e:
                logger.error(f"Failed to list tools for server '{name}': {e}")
        return all_tools

    async def shutdown(self) -> None:
        """Shutdown all sub-processes."""
        for name, server in list(self._servers.items()):
            logger.info(f"Stopping MCP server: {name}")
            await server.stop()
            self._servers.pop(name, None)
        self._initialized = False


# Singleton manager
mcp_manager = MCPClientManager()
