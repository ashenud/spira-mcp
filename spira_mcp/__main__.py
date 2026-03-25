"""`python -m spira_mcp` entry point."""

from __future__ import annotations


def main() -> None:
    from spira_mcp.server import mcp

    mcp.run()


if __name__ == "__main__":
    main()
