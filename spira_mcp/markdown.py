"""Markdown rendering for Spira requirements and incidents."""

from __future__ import annotations

import re

from spira_mcp.custom_properties import custom_property_display_value

_STATUS_REQUIREMENT = {
    1: "Requested",
    2: "Planned",
    3: "In Progress",
    4: "Developed",
    5: "Accepted",
    6: "Rejected",
    7: "Under Review",
    8: "Obsolete",
}
_STATUS_INCIDENT = {
    1: "New",
    2: "Open",
    3: "Assigned",
    4: "In Progress",
    5: "Fixed",
    6: "Closed",
    7: "Duplicate",
    8: "Not Reproducible",
    9: "Deferred",
    10: "Rejected",
}
_IMPORTANCE = {1: "1 - Critical", 2: "2 - High", 3: "3 - Medium", 4: "4 - Low"}
_SEVERITY = {1: "1 - Critical", 2: "2 - High", 3: "3 - Medium", 4: "4 - Low"}
_PRIORITY = {1: "1 - Critical", 2: "2 - High", 3: "3 - Medium", 4: "4 - Low"}


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    for entity, char in [
        ("&nbsp;", " "),
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&#39;", "'"),
    ]:
        text = text.replace(entity, char)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def field_text(data: dict, key: str, fallback: str = "_Not specified_") -> str:
    v = data.get(key)
    return str(v).strip() if v else fallback


def label(mapping: dict, id_val, fallback: str = "_Not set_") -> str:
    if id_val is None:
        return fallback
    return mapping.get(int(id_val), f"ID {id_val}")


def md_custom_properties(custom_props: list) -> list[str]:
    if not custom_props:
        return []
    lines = ["## Custom Properties", ""]
    for cp in custom_props:
        defn = cp.get("Definition") or {}
        name = defn.get("Name") or f"Property {cp.get('PropertyNumber', '?')}"
        value = custom_property_display_value(cp)
        lines.append(f"- **{name}:** {value if value is not None else '_Not set_'}")
    lines.append("")
    return lines


def md_comments(comments: list) -> list[str]:
    lines = ["## Comments", ""]
    if not comments:
        lines += ["_No comments._", ""]
        return lines
    for c in comments:
        author = c.get("CreatorName") or "Unknown"
        date_raw = c.get("CreationDate") or ""
        date_str = date_raw[:10] if len(date_raw) >= 10 else date_raw
        text = strip_html(c.get("Text") or c.get("Body") or c.get("Comment") or "")
        lines += [f"### {author} — {date_str}", "", text or "_No content_", ""]
    return lines


def build_requirement_md(req: dict, comments: list, project_id: int, base_url: str) -> str:
    rid = req.get("RequirementId") or req.get("ArtifactId") or "?"
    rq_id = f"RQ-{rid}"
    cprops = req.get("CustomProperties") or []
    lines = [
        f"# Requirement Specification: {rq_id}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| **ID** | {rq_id} |",
        f"| **Name** | {field_text(req, 'Name')} |",
        f"| **Status** | {label(_STATUS_REQUIREMENT, req.get('StatusId'))} |",
        f"| **Priority** | {label(_IMPORTANCE, req.get('ImportanceId'))} |",
        f"| **Type** | {field_text(req, 'RequirementTypeName')} |",
        f"| **Author** | {field_text(req, 'AuthorName')} |",
        f"| **Owner** | {field_text(req, 'OwnerName', '_Unassigned_')} |",
        f"| **Release** | {field_text(req, 'ReleaseVersionNumber', '_No release_')} |",
        f"| **Component** | {field_text(req, 'ComponentName', '_None_')} |",
        f"| **Last Updated** | {field_text(req, 'LastUpdateDate')} |",
        "",
        "## Description",
        "",
        strip_html(req.get("Description")) or "_No description provided._",
        "",
        "## Acceptance Criteria",
        "",
        strip_html(req.get("AcceptanceCriteria"))
        or "_No acceptance criteria defined._",
        "",
    ]
    lines += md_custom_properties(cprops)
    lines += md_comments(comments)
    lines += [
        "---",
        f"_Source: [{rq_id}]({base_url}/{project_id}/Requirement/{rid}/Overview.aspx)_",
    ]
    return "\n".join(lines)


def build_incident_md(inc: dict, comments: list, project_id: int, base_url: str) -> str:
    iid = inc.get("IncidentId") or inc.get("ArtifactId") or "?"
    in_id = f"IN-{iid}"
    cprops = inc.get("CustomProperties") or []
    lines = [
        f"# Incident Specification: {in_id}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| **ID** | {in_id} |",
        f"| **Name** | {field_text(inc, 'Name')} |",
        f"| **Status** | {label(_STATUS_INCIDENT, inc.get('IncidentStatusId'))} |",
        f"| **Severity** | {label(_SEVERITY, inc.get('SeverityId'))} |",
        f"| **Priority** | {label(_PRIORITY, inc.get('PriorityId'))} |",
        f"| **Type** | {field_text(inc, 'IncidentTypeName')} |",
        f"| **Opener** | {field_text(inc, 'OpenerName')} |",
        f"| **Owner** | {field_text(inc, 'OwnerName', '_Unassigned_')} |",
        f"| **Detected Release** | {field_text(inc, 'DetectedReleaseVersionNumber', '_Unknown_')} |",
        f"| **Resolved Release** | {field_text(inc, 'ResolvedReleaseVersionNumber', '_Not set_')} |",
        f"| **Last Updated** | {field_text(inc, 'LastUpdateDate')} |",
        "",
        "## Description",
        "",
        strip_html(inc.get("Description")) or "_No description provided._",
        "",
        "## Steps to Reproduce",
        "",
        strip_html(inc.get("StepsToReproduce")) or "_Not specified._",
        "",
    ]
    lines += md_custom_properties(cprops)
    lines += md_comments(comments)
    lines += [
        "---",
        f"_Source: [{in_id}]({base_url}/{project_id}/Incident/{iid}/Overview.aspx)_",
    ]
    return "\n".join(lines)
