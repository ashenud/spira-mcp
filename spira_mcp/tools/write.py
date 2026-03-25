"""Write MCP tools (gated by SPIRA_ALLOW_UPDATES)."""

from __future__ import annotations

from typing import Annotated

from mcp import McpError
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ErrorData, INVALID_PARAMS
from pydantic import Field

from spira_mcp.config import settings
from spira_mcp.context import SpiraContext
from spira_mcp.custom_properties import apply_custom_field_update
from spira_mcp.logging_setup import log, request_scope
from spira_mcp.spira_api import get_json, put_json, resolve_project


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def update_requirement_custom_field(
        requirement_id: Annotated[int, Field(gt=0)],
        field_name: Annotated[str, Field(min_length=1, max_length=200)],
        field_value: Annotated[str, Field(max_length=10000)],
        ctx: Context,
        project_id: Annotated[int, Field(gt=0)] | None = None,
    ) -> str:
        """
        Update a single custom property on a SpiraPlan requirement.

        ⚠ DISABLED unless SPIRA_ALLOW_UPDATES=true is set in mcp.json.

        Performs a safe read-then-write:
          1. GET the current requirement (preserves ConcurrencyDate and all fields)
          2. Locate the named custom property
          3. PUT the full requirement back with only that field changed

        Args:
            requirement_id: Numeric requirement ID (e.g. 22942)
            field_name:     Exact name of the custom property (e.g. 'Technical Details')
            field_value:    New string value to write
            project_id:     Optional. Defaults to SPIRA_PROJECT_ID env variable.
        """
        with request_scope():
            if not settings.allow_updates:
                raise McpError(
                    ErrorData(
                        code=INVALID_PARAMS,
                        message=(
                            "Write tools are disabled. "
                            "Set SPIRA_ALLOW_UPDATES=true in your mcp.json env to enable them."
                        ),
                    )
                )

            spira: SpiraContext = ctx.request_context.lifespan_context
            pid = resolve_project(project_id)

            req = await get_json(spira, f"projects/{pid}/requirements/{requirement_id}")
            custom_props: list = req.get("CustomProperties") or []

            if not apply_custom_field_update(custom_props, field_name, field_value):
                available = [
                    (cp.get("Definition") or {}).get("Name", "?") for cp in custom_props
                ]
                raise McpError(
                    ErrorData(
                        code=INVALID_PARAMS,
                        message=(
                            f"Custom property '{field_name}' not found on RQ-{requirement_id}. "
                            f"Available properties: {available}"
                        ),
                    )
                )

            payload = dict(req)
            payload["CustomProperties"] = custom_props
            await put_json(spira, f"projects/{pid}/requirements", payload)

            log.info(
                "Updated RQ-%s field '%s' in project %s",
                requirement_id,
                field_name,
                pid,
            )
            return (
                f"✅ Successfully updated '{field_name}' on "
                f"RQ-{requirement_id} in project {pid}."
            )

    @mcp.tool()
    async def update_incident_custom_field(
        incident_id: Annotated[int, Field(gt=0)],
        field_name: Annotated[str, Field(min_length=1, max_length=200)],
        field_value: Annotated[str, Field(max_length=10000)],
        ctx: Context,
        project_id: Annotated[int, Field(gt=0)] | None = None,
    ) -> str:
        """
        Update a single custom property on a SpiraPlan incident.

        ⚠ DISABLED unless SPIRA_ALLOW_UPDATES=true is set in mcp.json.

        Performs a safe read-then-write:
          1. GET the current incident (preserves ConcurrencyDate and all fields)
          2. Locate the named custom property
          3. PUT the full incident back with only that field changed

        Args:
            incident_id: Numeric incident ID (e.g. 1234)
            field_name:  Exact name of the custom property
            field_value: New string value to write
            project_id:  Optional. Defaults to SPIRA_PROJECT_ID env variable.
        """
        with request_scope():
            if not settings.allow_updates:
                raise McpError(
                    ErrorData(
                        code=INVALID_PARAMS,
                        message=(
                            "Write tools are disabled. "
                            "Set SPIRA_ALLOW_UPDATES=true in your mcp.json env to enable them."
                        ),
                    )
                )

            spira: SpiraContext = ctx.request_context.lifespan_context
            pid = resolve_project(project_id)

            inc = await get_json(spira, f"projects/{pid}/incidents/{incident_id}")
            custom_props: list = inc.get("CustomProperties") or []

            if not apply_custom_field_update(custom_props, field_name, field_value):
                available = [
                    (cp.get("Definition") or {}).get("Name", "?") for cp in custom_props
                ]
                raise McpError(
                    ErrorData(
                        code=INVALID_PARAMS,
                        message=(
                            f"Custom property '{field_name}' not found on IN-{incident_id}. "
                            f"Available properties: {available}"
                        ),
                    )
                )

            payload = dict(inc)
            payload["CustomProperties"] = custom_props
            await put_json(spira, f"projects/{pid}/incidents", payload)

            log.info(
                "Updated IN-%s field '%s' in project %s",
                incident_id,
                field_name,
                pid,
            )
            return (
                f"✅ Successfully updated '{field_name}' on "
                f"IN-{incident_id} in project {pid}."
            )
