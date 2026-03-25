"""Register all MCP tools on the FastMCP server instance."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import read as read_tools
from . import write as write_tools


def register_tools(mcp: FastMCP) -> None:
    read_tools.register(mcp)
    write_tools.register(mcp)
