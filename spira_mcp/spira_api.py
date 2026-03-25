"""Authenticated Spira REST calls: retries, semaphore, and error mapping."""

from __future__ import annotations

import json
import logging

import httpx
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS
from tenacity import (
    RetryCallState,
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
)

from spira_mcp.config import settings
from spira_mcp.context import SpiraContext
from spira_mcp.logging_setup import log


def resolve_project(override: int | None) -> int:
    pid = override or settings.default_project
    if not pid:
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS,
                message=(
                    "No project_id provided and SPIRA_PROJECT_ID is not set. "
                    "Pass project_id in your prompt or set SPIRA_PROJECT_ID in mcp.json."
                ),
            )
        )
    return pid


def _transient_wait(retry_state: RetryCallState) -> float:
    """Exponential backoff between retries: 1s, 2s, 4s."""
    delays = (1.0, 2.0, 4.0)
    i = retry_state.attempt_number - 1
    return delays[i] if i < len(delays) else delays[-1]


def _is_transient_http_error(exc: BaseException) -> bool:
    """Retry only on selected status codes and transport errors."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    if isinstance(exc, httpx.RequestError):
        return not isinstance(exc, httpx.HTTPStatusError)
    return False


@retry(
    stop=stop_after_attempt(4),
    wait=_transient_wait,
    retry=retry_if_exception(_is_transient_http_error),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
async def _get_with_retry(http: httpx.AsyncClient, path: str) -> dict | list:
    r = await http.get(path)
    r.raise_for_status()
    return r.json()


@retry(
    stop=stop_after_attempt(4),
    wait=_transient_wait,
    retry=retry_if_exception(_is_transient_http_error),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
async def _put_with_retry(http: httpx.AsyncClient, path: str, payload: dict) -> None:
    r = await http.put(path, content=json.dumps(payload))
    r.raise_for_status()


async def get_json(ctx: SpiraContext, path: str) -> dict | list:
    """Authenticated GET — raises McpError on HTTP failure."""
    async with ctx.semaphore:
        try:
            return await _get_with_retry(ctx.http, path)
        except httpx.HTTPStatusError as e:
            log.warning("GET %s → HTTP %s", path, e.response.status_code)
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=(
                        f"Spira API error {e.response.status_code}: "
                        f"{e.response.text[:300]}"
                    ),
                )
            )
        except httpx.RequestError as e:
            log.error("Network error on GET %s: %s", path, e)
            raise McpError(
                ErrorData(code=INTERNAL_ERROR, message=f"Network error: {e}")
            )


async def put_json(ctx: SpiraContext, path: str, payload: dict) -> None:
    """Authenticated PUT — raises McpError on HTTP failure."""
    async with ctx.semaphore:
        try:
            await _put_with_retry(ctx.http, path, payload)
        except httpx.HTTPStatusError as e:
            log.warning("PUT %s → HTTP %s", path, e.response.status_code)
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=(
                        f"Spira API error {e.response.status_code}: "
                        f"{e.response.text[:300]}"
                    ),
                )
            )
        except httpx.RequestError as e:
            log.error("Network error on PUT %s: %s", path, e)
            raise McpError(
                ErrorData(code=INTERNAL_ERROR, message=f"Network error: {e}")
            )


async def get_comments(
    ctx: SpiraContext, artifact: str, project_id: int, artifact_id: int
) -> list:
    """Fetch comments for any artifact — non-fatal, returns [] on any failure."""
    try:
        result = await get_json(
            ctx, f"projects/{project_id}/{artifact}/{artifact_id}/comments"
        )
        return result if isinstance(result, list) else []
    except Exception:
        return []
