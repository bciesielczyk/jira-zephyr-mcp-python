# jira-zephyr-mcp-python

Python rewrite of the Jira Zephyr MCP server. The project uses [uv](https://docs.astral.sh/uv/) to manage dependencies and tooling.

## Setup
- Install dependencies locally: `uv sync --dev`
- Activate the managed virtualenv when needed: `source .venv/bin/activate`

## Linting
- Static checks: `uv run ruff check .`
- Formatting preview (no changes): `uv run ruff format --diff`

## Typing
- MyPy strict mode: `uv run mypy src tests`
- Pyright (mirrors editor diagnostics): `uv run pyright`

## Testing
- Unit and integration tests: `uv run pytest`
- Focused test module: `uv run pytest tests/path_to_test.py -k name_fragment`

## Full Quality Gate
- Run everything before pushing: `uv run ruff check . && uv run mypy src tests && uv run pyright && uv run pytest`
