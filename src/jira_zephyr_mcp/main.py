"""Bootstrap helpers for the eventual MCP server implementation."""

from __future__ import annotations

from typing import Any


def create_app(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a placeholder application object until MCP wiring exists."""
    return {"config": config or {}}
