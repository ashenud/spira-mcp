"""FastMCP application instance and tool registration."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from spira_mcp.logging_setup import log
from spira_mcp import config
from spira_mcp.context import lifespan
from spira_mcp.tools import register_tools

log.info(
    "spira-mcp starting | base=%s | updates_enabled=%s",
    config.settings.base_url,
    config.settings.allow_updates,
)

mcp = FastMCP(
    "spira-custom",
    dependencies=["httpx>=0.27", "mcp>=1.0", "tenacity>=8.2"],
    lifespan=lifespan,
)

register_tools(mcp)
