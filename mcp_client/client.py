"""
MCP client for Culture Facts: launches the server over stdio, performs the
MCP handshake, and lets the rest of the code call tools.
"""

import json
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class MCPClient:
    """Starts the MCP server and talks to it; use with `async with MCPClient() as mcp`."""

    def __init__(self, server_module: str = "mcp_server.server"):
        """Configure how to launch the server (as `python -m <server_module>`)."""
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", server_module],
            cwd=str(PROJECT_ROOT),
        )
        self._stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.tool_names: list[str] = []

    async def __aenter__(self) -> "MCPClient":
        """Launch the server, do the MCP handshake, and discover its tools."""
        read, write = await self._stack.enter_async_context(stdio_client(self.server_params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()                        # 1. handshake
        tools = await self.session.list_tools()                # 2. capability discovery
        self.tool_names = [tool.name for tool in tools.tools]  # 3. registration
        return self

    async def __aexit__(self, *exc) -> None:
        """Close the session and stop the server process."""
        await self._stack.aclose()

    async def call_tool(self, name: str, **arguments: Any) -> Any:
        """Call a server tool by name and return its result as plain Python data."""
        if self.session is None:
            raise RuntimeError("Not connected; use `async with MCPClient() as mcp`")

        result = await self.session.call_tool(name, arguments=arguments)
        text = "\n".join(c.text for c in result.content if getattr(c, "type", "") == "text")

        if result.isError:
            raise RuntimeError(f"Tool '{name}' failed: {text}")

        # Prefer structured output; FastMCP wraps non-dict returns as {"result": ...}
        data = result.structuredContent
        if data is not None:
            return data["result"] if set(data) == {"result"} else data

        # Fallback: parse the text as JSON, else return it as-is
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return text