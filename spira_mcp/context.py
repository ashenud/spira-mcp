"""FastMCP lifespan: shared HTTP client and API concurrency limit."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from mcp.server.fastmcp import FastMCP

from spira_mcp.config import settings
from spira_mcp.logging_setup import log


@dataclass
class SpiraContext:
    """Typed dependency container injected into every tool call."""

    http: httpx.AsyncClient
    semaphore: asyncio.Semaphore


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[SpiraContext]:
    """Open one AsyncClient on startup; close it cleanly on shutdown."""
    async with httpx.AsyncClient(
        base_url=settings.api_root,
        params={"username": settings.username, "api-key": settings.api_key},
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
    ) as client:
        log.info("HTTP client ready")
        yield SpiraContext(http=client, semaphore=asyncio.Semaphore(5))
    log.info("HTTP client closed")
