from typer.testing import CliRunner

from jira_zephyr_mcp import __version__
from jira_zephyr_mcp.cli import app


def test_version_command() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output
