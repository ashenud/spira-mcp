# spira-mcp-server

A secure, production-grade **Model Context Protocol (MCP) server** for [SpiraPlan](https://www.inflectra.com/SpiraPlan/) — built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) and designed for use inside **Cursor**.

---

## Features

| Tool | Type | Description |
|---|---|---|
| `get_requirement` | 🔵 Read | Fetch a requirement as full JSON (with comments + custom properties) |
| `get_specification_requirement` | 🔵 Read | Fetch a requirement as a rich Markdown specification document |
| `list_requirement_custom_fields` | 🔵 Read | Fetch a requirement’s custom properties only (Markdown table of names and values) |
| `get_incident` | 🔵 Read | Fetch an incident as full JSON (with comments + custom properties) |
| `get_specification_incident` | 🔵 Read | Fetch an incident as a rich Markdown specification document |
| `update_requirement_custom_field` | 🔴 Write | Update a single custom property on a requirement (disabled by default) |
| `update_incident_custom_field` | 🔴 Write | Update a single custom property on an incident (disabled by default) |

### Security model
- **Write tools are off by default** — set `SPIRA_ALLOW_UPDATES=true` to enable
- Credentials are loaded from environment variables and **never logged or returned** in tool output
- All rich-text fields from Spira are **HTML-sanitised** before being passed to the AI
- Uses a **single shared `httpx.AsyncClient`** per server lifetime via FastMCP's typed lifespan — no credential leakage between requests
- Errors return structured `McpError` responses — no raw stack traces or API internals exposed

---

## Requirements

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`
- A SpiraPlan account with API access

---

## Installation

### Option A — uv (recommended)

```bash
git clone <repo-url> ~/spira-mcp && cd ~/spira-mcp
# or copy the whole project tree (including the `spira_mcp/` package directory)

# Install dependencies with uv (creates .venv automatically)
uv sync
```

### Option B — pip + venv

```bash
cd ~/spira-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Getting Your Spira API Key

1. Log in to your Spira instance
2. Click your **user avatar** → your name → **My Profile**
3. Scroll to **"Enable RSS Feeds"** → set to **Yes**
4. Click **Generate New** next to **RSS / API Key**
5. Copy the key — it looks like `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}`

---

## Cursor Configuration

Create `.cursor/mcp.json` at your project root (or `~/.cursor/mcp.json` for global use):

### Using uv (recommended)
```json
{
  "mcpServers": {
    "spira-custom": {
      "command": "uv",
      "args": ["--directory", "/home/YOUR_USER/spira-mcp", "run", "python", "-m", "spira_mcp"],
      "env": {
        "SPIRA_BASE_URL": "https://simitive.spiraservice.net",
        "SPIRA_USERNAME": "your_login",
        "SPIRA_API_KEY": "{YOUR-API-KEY-HERE}",
        "SPIRA_PROJECT_ID": "31"
      },
      "type": "stdio"
    }
  }
}
```

### Using the venv console script (after `pip install -e .` or `uv sync`)
```json
{
  "mcpServers": {
    "spira-custom": {
      "command": "/home/YOUR_USER/spira-mcp/.venv/bin/spira-mcp",
      "args": [],
      "env": {
        "SPIRA_BASE_URL": "https://simitive.spiraservice.net",
        "SPIRA_USERNAME": "your_login",
        "SPIRA_API_KEY": "{YOUR-API-KEY-HERE}",
        "SPIRA_PROJECT_ID": "31"
      },
      "type": "stdio"
    }
  }
}
```

### To enable write tools
Add `"SPIRA_ALLOW_UPDATES": "true"` to the `env` block above.

> ⚠️ **Security:** Add `.cursor/mcp.json` to your `.gitignore` immediately.
> ```bash
> echo ".cursor/mcp.json" >> .gitignore
> ```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SPIRA_BASE_URL` | ✅ | — | Base URL of your Spira instance, e.g. `https://simitive.spiraservice.net` |
| `SPIRA_USERNAME` | ✅ | — | Your Spira login username |
| `SPIRA_API_KEY` | ✅ | — | Your Spira RSS/API key including `{` `}` braces |
| `SPIRA_PROJECT_ID` | Optional | — | Default project ID used when not specified in prompt |
| `SPIRA_ALLOW_UPDATES` | Optional | `false` | Set to `true` to enable `update_requirement_custom_field` and `update_incident_custom_field` |

---

## Usage in Cursor Agent Mode

Switch to **Agent mode** (`Ctrl + .`) then use natural language:

### Read a requirement
```
Get requirement 22942
```
```
Get requirement 22942 from project 31
```

### Get a Markdown specification
```
Get the specification for requirement 22942
```
```
Get spec for requirement 22942 in project 31
```

### List custom field names on a requirement
```
List custom fields for requirement 22942
```
```
Show requirement 22942 custom properties in project 31
```

### Read an incident
```
Get incident 1234
```
```
Get the specification for incident 1234 in project 31
```

### Full AI workflow — read, plan, write back
```
Get the specification for requirement 22942 in project 31.

Based on the Description, Acceptance Criteria, and Comments,
generate a detailed Technical Implementation Plan covering:
  - Component / module breakdown
  - API contracts or data models needed
  - Key dependencies and risks
  - Estimated complexity / story points

Then update the 'Technical Details' custom field on
requirement 22942 in project 31 with the plan you generated.
```

### Update an incident custom field (writes enabled)
```
Update incident 1234 custom field 'Root Cause' to 'Race in cache invalidation' in project 31
```

---

## What the tools return

### `get_requirement` / `get_incident`
Raw JSON with every field Spira returns, plus `_Comments` array:
```json
{
  "RequirementId": 22942,
  "Name": "User SSO Authentication",
  "Description": "The system shall allow...",
  "AcceptanceCriteria": "- User can click Login with SSO...",
  "StatusId": 3,
  "ImportanceId": 2,
  "CustomProperties": [
    {
      "PropertyNumber": 1,
      "StringValue": null,
      "Definition": { "Name": "Technical Details" }
    }
  ],
  "_Comments": [
    {
      "CreatorName": "Jane Doe",
      "CreationDate": "2025-03-08T10:30:00",
      "Text": "We need to confirm the SAML metadata URL first."
    }
  ]
}
```

### `list_requirement_custom_fields`
Markdown table with only custom property names and values (no other requirement fields):
```markdown
| Property Name | Current Value |
|---|---|
| Technical Details | _Not set_ |
| Sprint | Sprint 14 |
```

### `get_specification_requirement` / `get_specification_incident`
Clean Markdown document ready for AI consumption:
```markdown
# Requirement Specification: RQ-22942

| Field | Value |
|---|---|
| **ID** | RQ-22942 |
| **Name** | User SSO Authentication |
| **Status** | In Progress |
| **Priority** | 2 - High |
...

## Description
The system shall allow users to authenticate using corporate SSO...

## Acceptance Criteria
- User can click "Login with SSO" on the login page
- System redirects to the IdP login page

## Custom Properties
- **Technical Details:** _Not set_
- **Sprint:** Sprint 14

## Comments

### Jane Doe — 2025-03-08
We need to confirm the SAML metadata URL with the infrastructure team.

---
_Source: [RQ-22942](https://simitive.spiraservice.net/31/Requirement/22942/Overview.aspx)_
```

---

## Cursor Prompt Template

Save this as a `.cursor/prompts/spira-technical-plan.md` prompt template:

```
You are a senior software engineer. Use the spira-custom MCP tools to:

1. Call get_specification_requirement with requirement_id={REQUIREMENT_ID}
2. Read the Description, Acceptance Criteria, Custom Properties, and Comments carefully
3. Generate a Technical Implementation Plan with these sections:
   - ## Overview
   - ## Architecture & Components
   - ## Data Models / API Contracts
   - ## Dependencies & Risks
   - ## Acceptance Verification
   - ## Estimated Complexity (S/M/L/XL)
4. Call update_requirement_custom_field to write the plan to the
   'Technical Details' field on that requirement

Do not ask for confirmation — execute all steps automatically.
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Server not appearing in Cursor | Fully quit and reopen Cursor (not just reload window) |
| `HTTP 401 / Access Denied` | Check `SPIRA_API_KEY` includes the `{` `}` braces |
| `HTTP 404` | Verify project ID and artifact ID are correct by checking the URL in your browser |
| `ModuleNotFoundError: mcp` / `spira_mcp` | Run `uv sync` or `pip install -e .` from the project root so the package is on `PYTHONPATH` |
| Comments always empty | Verify `GET /projects/{id}/requirements/{id}/comments` works in your Spira API docs at `{BASE_URL}/Services/v7_0/RestService.aspx` |
| Write tools rejected | Add `"SPIRA_ALLOW_UPDATES": "true"` to the env in mcp.json and restart Cursor |
| `RuntimeError: Missing required env variable` | Check all three required vars are in the `env` block of mcp.json |

---

## Architecture

```
Cursor Agent
    │  stdio
    ▼
spira_mcp.server  (FastMCP + register_tools)
    │
    ├── lifespan (context.py): SpiraContext
    │     └── httpx.AsyncClient + asyncio.Semaphore(5)
    │
    ├── tools/read.py                   ──► spira_api (GET + comments)
    ├── tools/write.py                  ──► spira_api (GET/PUT, gated)
    ├── spira_api.py                    ──► Spira REST (retries, McpError mapping)
    ├── markdown.py                     ──► specification Markdown
    └── custom_properties.py            ──► custom field table / updates
```

---

## Project structure

```
spira-mcp/
├── spira_mcp/                 ← Python package
│   ├── __init__.py
│   ├── __main__.py            ← `python -m spira_mcp`
│   ├── server.py              ← FastMCP app + tool registration
│   ├── config.py              ← env → Settings
│   ├── logging_setup.py       ← stderr logging, request correlation
│   ├── context.py             ← SpiraContext, lifespan
│   ├── spira_api.py           ← HTTP client helpers (retry, semaphore)
│   ├── markdown.py            ← specification Markdown builders
│   ├── custom_properties.py   ← custom property helpers
│   └── tools/
│       ├── __init__.py        ← register_tools(mcp)
│       ├── read.py
│       └── write.py
├── spira_mcp_server.py        ← thin shim → spira_mcp.server (optional)
├── pyproject.toml
├── .venv/                     ← created by uv sync (gitignored)
└── README.md
```

---

## Licence

MIT
