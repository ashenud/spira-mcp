"""
Compatibility entrypoint for Cursor / legacy `uv run spira_mcp_server.py`.

Prefer: `python -m spira_mcp` or the `spira-mcp` console script after install.
"""

from __future__ import annotations

from spira_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
