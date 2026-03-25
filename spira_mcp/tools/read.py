"""Read-only MCP tools."""

from __future__ import annotations

import json
from typing import Annotated

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from spira_mcp.config import settings
from spira_mcp.context import SpiraContext
from spira_mcp.custom_properties import markdown_custom_properties_table
from spira_mcp.logging_setup import request_scope
from spira_mcp.markdown import build_incident_md, build_requirement_md
from spira_mcp.spira_api import get_comments, get_json, resolve_project


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_requirement(
        requirement_id: Annotated[int, Field(gt=0)],
        ctx: Context,
        project_id: Annotated[int, Field(gt=0)] | None = None,
    ) -> str:
        """
        Fetch a SpiraPlan requirement by ID.

        Returns full JSON including: name, description, acceptance criteria,
        status, priority, type, owner, release, component, all custom properties,
        and all comments appended as '_Comments'.

        project_id defaults to SPIRA_PROJECT_ID env variable if not provided.
        """
        with request_scope():
            spira: SpiraContext = ctx.request_context.lifespan_context
            pid = resolve_project(project_id)
            req = await get_json(spira, f"projects/{pid}/requirements/{requirement_id}")
            comments = await get_comments(spira, "requirements", pid, requirement_id)
            result = dict(req)
            result["_Comments"] = comments
            return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    async def get_specification_requirement(
        requirement_id: Annotated[int, Field(gt=0)],
        ctx: Context,
        project_id: Annotated[int, Field(gt=0)] | None = None,
    ) -> str:
        """
        Fetch a SpiraPlan requirement and return a rich Markdown specification
        document formatted for AI consumption and technical planning.

        Includes: metadata table, description, acceptance criteria,
        all custom properties, and all comments.

        project_id defaults to SPIRA_PROJECT_ID env variable if not provided.
        """
        with request_scope():
            spira: SpiraContext = ctx.request_context.lifespan_context
            pid = resolve_project(project_id)
            req = await get_json(spira, f"projects/{pid}/requirements/{requirement_id}")
            comments = await get_comments(spira, "requirements", pid, requirement_id)
            return build_requirement_md(req, comments, pid, settings.base_url)

    @mcp.tool()
    async def list_requirement_custom_fields(
        requirement_id: Annotated[int, Field(gt=0)],
        ctx: Context,
        project_id: Annotated[int, Field(gt=0)] | None = None,
    ) -> str:
        """
        Fetch a requirement and return only custom property names and current values
        as a Markdown table. Use this to discover exact field names for updates.
        """
        with request_scope():
            spira: SpiraContext = ctx.request_context.lifespan_context
            pid = resolve_project(project_id)
            req = await get_json(spira, f"projects/{pid}/requirements/{requirement_id}")
            cprops = req.get("CustomProperties") or []
            return markdown_custom_properties_table(cprops)

    @mcp.tool()
    async def get_incident(
        incident_id: Annotated[int, Field(gt=0)],
        ctx: Context,
        project_id: Annotated[int, Field(gt=0)] | None = None,
    ) -> str:
        """
        Fetch a SpiraPlan incident by ID.

        Returns full JSON including: name, description, steps to reproduce,
        status, severity, priority, type, opener, owner, releases,
        all custom properties, and all comments appended as '_Comments'.

        project_id defaults to SPIRA_PROJECT_ID env variable if not provided.
        """
        with request_scope():
            spira: SpiraContext = ctx.request_context.lifespan_context
            pid = resolve_project(project_id)
            inc = await get_json(spira, f"projects/{pid}/incidents/{incident_id}")
            comments = await get_comments(spira, "incidents", pid, incident_id)
            result = dict(inc)
            result["_Comments"] = comments
            return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    async def get_specification_incident(
        incident_id: Annotated[int, Field(gt=0)],
        ctx: Context,
        project_id: Annotated[int, Field(gt=0)] | None = None,
    ) -> str:
        """
        Fetch a SpiraPlan incident and return a rich Markdown specification
        document formatted for AI consumption and technical planning.

        Includes: metadata table, description, steps to reproduce,
        all custom properties, and all comments.

        project_id defaults to SPIRA_PROJECT_ID env variable if not provided.
        """
        with request_scope():
            spira: SpiraContext = ctx.request_context.lifespan_context
            pid = resolve_project(project_id)
            inc = await get_json(spira, f"projects/{pid}/incidents/{incident_id}")
            comments = await get_comments(spira, "incidents", pid, incident_id)
            return build_incident_md(inc, comments, pid, settings.base_url)
