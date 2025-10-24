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
def serve(  # pragma: no cover - placeholder until server is implemented
    host: str = typer.Option("127.0.0.1", help="Host interface for the MCP server."),
    port: int = typer.Option(8765, help="Port for the MCP server."),
) -> None:
    """Start the MCP server (placeholder)."""
    typer.echo(f"MCP server bootstrap not yet implemented. Would bind to {host}:{port} when ready.")


def main() -> None:
    """Entrypoint used by console_scripts and python -m execution."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
