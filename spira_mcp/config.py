"""Environment-backed settings loaded once at process start."""

from __future__ import annotations

import os
from dataclasses import dataclass


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"[spira-mcp] Missing required env variable: {name}\n"
            f"Add it to the 'env' section of your .cursor/mcp.json."
        )
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    base_url: str
    username: str
    api_key: str
    default_project: int
    allow_updates: bool
    api_root: str

    @classmethod
    def load(cls) -> Settings:
        base = require_env("SPIRA_BASE_URL").rstrip("/")
        default_project = int(os.environ.get("SPIRA_PROJECT_ID", "0") or "0")
        allow_updates = os.environ.get("SPIRA_ALLOW_UPDATES", "false").lower() == "true"
        return cls(
            base_url=base,
            username=require_env("SPIRA_USERNAME"),
            api_key=require_env("SPIRA_API_KEY"),
            default_project=default_project,
            allow_updates=allow_updates,
            api_root=f"{base}/Services/v7_0/RestService.svc",
        )


settings = Settings.load()
