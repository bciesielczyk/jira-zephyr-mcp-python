"""Command-line interface for the Jira Zephyr MCP server."""

from __future__ import annotations

import typer

app = typer.Typer(help="Run Jira Zephyr MCP services and developer utilities.")


@app.command()
def version() -> None:
    """Print the installed package version."""
    from . import __version__

    typer.echo(__version__)


@app.command()
def serve() -> None:
    """Start the MCP server."""
    import asyncio
    from jira_zephyr_mcp.config import load_config
    from jira_zephyr_mcp.server import JiraZephyrMCPServer
    
    settings = load_config()
    mcp_server = JiraZephyrMCPServer(settings)
    asyncio.run(mcp_server.run())


def main() -> None:
    """Entrypoint used by console_scripts and python -m execution."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
