# Zephyr MCP Python Rewrite Plan

## Action Plan & TODOs

- [X] **Set scope & requirements**: document security objectives, feature parity targets, supported MCP tools, performance/SLA expectations, and compliance constraints.
- [X] **Create Python scaffold**: initialize `pyproject.toml`, configure virtual environment layout, create package skeleton under `src/jira_zephyr_mcp`, wire linting/formatting (`ruff`), typing (`mypy`/`pyright`), testing (`pytest`), and a CLI entry point via `typer` or `click`.
- [ ] **Implement configuration layer**: load environment variables and secret stores with `pydantic` models, define validation rules, support multiple config sources, and write unit tests.
- [ ] **Port Jira & Zephyr clients**: recreate REST integrations using `httpx` (async), add retry/backoff policies, structured logging with redaction, timeout defaults, and response schema validation.
- [ ] **Rebuild MCP tool handlers**: translate each TypeScript tool (`test_cases`, `test_plans`, `test_cycles`, `test_execution`, `jira_issues`, `nl_command`) into Python modules, ensure consistent error handling, and add security checks for input validation.
- [ ] **Enhance security posture**: pin dependencies (`pip-tools`), enable SAST/DAST hooks (Bandit, Semgrep), redact sensitive data in logs, enforce TLS settings, and document secret rotation processes.
- [ ] **Testing & QA**: implement unit/integration tests with mocks for Jira/Zephyr APIs, create contract tests for MCP responses, configure GitHub Actions CI, and track coverage metrics.
- [ ] **Documentation & rollout**: update README for Python usage, provide migration checklist, prepare operational runbook, and plan decommissioning of the Node implementation.

## Overview
This plan covers porting the existing Node.js/TypeScript MCP server to Python while maintaining functionality, improving security, and preserving a smooth developer experience.

## Architecture

### Core Components
- **MCP Server**: Python entry point managing MCP protocol (JSON-RPC/WebSocket) communication using the MCP Python SDK or custom transport.
- **Jira Client**: Async HTTP client for Jira Cloud REST API operations.
- **Zephyr Client**: Async HTTP client targeting Zephyr Scale endpoints.
- **Tool Handlers**: Python modules implementing each MCP tool.
- **Configuration Manager**: Typed configuration loader using `pydantic`/`pydantic-settings`.
- **Logging & Observability**: Structured logging (`structlog` or `loguru`) with optional OpenTelemetry hooks.

## Project Structure
```
jira-zephyr-mcp-py/
├── pyproject.toml
├── README.md
├── .env.example
├── src/
│   └── jira_zephyr_mcp/
│       ├── __init__.py
│       ├── main.py              # MCP server bootstrap
│       ├── config.py            # Typed configuration & validation
│       ├── logging.py           # Logging setup utilities
│       ├── clients/
│       │   ├── jira.py          # Jira API client
│       │   └── zephyr.py        # Zephyr API client
│       ├── tools/
│       │   ├── test_plans.py
│       │   ├── test_cycles.py
│       │   ├── test_cases.py
│       │   ├── test_execution.py
│       │   ├── jira_issues.py
│       │   └── nl_command.py
│       ├── schemas/
│       │   ├── jira.py          # Jira response/request models
│       │   └── zephyr.py        # Zephyr response/request models
│       └── utils/
│           ├── http.py          # Shared HTTP helpers, retry logic
│           └── validation.py    # Custom validators
└── tests/
    ├── unit/
    └── integration/
```

## MCP Tools Implementation

### Primary Tools (Parity Targets)

#### 1. `create_test_plan`
- **Purpose**: Create Zephyr test plans.
- **Inputs**:
  - `name: str`
  - `description: str | None`
  - `projectKey: str`
  - `startDate: str | None`
  - `endDate: str | None`
- **Output**: `TestPlan` model serialized for MCP response.

#### 2. `create_test_cycle`
- **Purpose**: Create Zephyr execution cycles.
- **Inputs**:
  - `name: str`
  - `description: str | None`
  - `projectKey: str`
  - `versionId: str`
  - `environment: str | None`
  - `startDate: str | None`
  - `endDate: str | None`
- **Output**: `TestCycle` model.

#### 3. `read_jira_issue`
- **Purpose**: Retrieve Jira issue details.
- **Inputs**:
  - `issueKey: str`
  - `fields: list[str] | None`
- **Output**: `JiraIssue` model with selected fields.

### Additional Tools (Parity & Enhancements)

- `list_test_plans`
- `list_test_cycles`
- `execute_test`
- `get_test_execution_status`
- `link_tests_to_issues`
- `generate_test_report`
- `get_test_case`
- `create_test_case`
- `create_multiple_test_cases`
- `nl_command`

Each tool will expose a Python coroutine registered with the MCP server, performing schema validation via `pydantic` models and returning sanitized responses.

## Technical Implementation Details

### Dependencies
- `httpx`: async HTTP client with HTTP/2 and timeout support.
- `pydantic` / `pydantic-settings`: configuration and schema validation.
- `typer` or `click`: CLI/bootstrap interface.
- `anyio`: async concurrency foundation if needed.
- `structlog` or `loguru`: structured logging.
- `python-dotenv`: local development env loading.
- `tenacity`: retry/backoff utilities.
- `ruff`, `mypy`, `pytest`, `coverage`, `bandit`, `semgrep` for quality and security gates.

### Authentication
- Jira Cloud API tokens via HTTP Basic authentication (email + API token).
- Zephyr Scale API tokens via bearer headers.
- Optional secret stores (AWS Secrets Manager, HashiCorp Vault) using abstraction in config layer.

### Error Handling
- Centralized exception hierarchy translating to MCP error responses.
- Retry policies for transient HTTP status codes and rate limits.
- Timeout and cancellation handling via `httpx` client configuration.
- Structured error logs with sensitive field redaction.

### Type Safety
- `pydantic` models for all request/response payloads.
- `typing` annotations across codebase.
- `mypy` strict mode for static checks.

## Configuration

### Environment Variables
```bash
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
ZEPHYR_API_TOKEN=your-zephyr-api-token
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
```

### MCP Server Configuration Example
```json
{
  "name": "jira-zephyr-mcp-py",
  "version": "0.1.0",
  "tools": [
    "create_test_plan",
    "create_test_cycle",
    "read_jira_issue",
    "list_test_plans",
    "list_test_cycles",
    "execute_test",
    "get_test_execution_status",
    "link_tests_to_issues",
    "generate_test_report",
    "create_test_case",
    "create_multiple_test_cases",
    "nl_command"
  ]
}
```

## Implementation Phases

### Phase 1: Core Setup
1. Initialize Python project structure and tooling.
2. Implement configuration loading and validation.
3. Build base MCP server scaffold with health-check tool.
4. Port `read_jira_issue` as first end-to-end slice.

### Phase 2: Test Management
1. Implement Zephyr client abstractions.
2. Port test plan and cycle management tools.
3. Add test case creation/listing tools.
4. Harden input validation and error conversions.

### Phase 3: Advanced Features
1. Port execution and reporting tools.
2. Implement natural language command parsing handler.
3. Add batching support for `create_multiple_test_cases` and other bulk operations.
4. Integrate audit logging and metrics collection.

### Phase 4: Security & Observability
1. Add dependency pinning, SBoM generation, and vulnerability scanning.
2. Integrate logging redaction, request tracing, and rate limit monitoring.
3. Configure CI pipelines with lint/test/security gates.
4. Conduct security review and penetration testing.

### Phase 5: Documentation & Rollout
1. Document setup, configuration, and runbooks.
2. Provide migration checklist and parity verification tasks.
3. Plan parallel run and cutover from Node implementation.
4. Capture lessons learned and backlog for future enhancements.

## Testing Strategy
- Unit tests for configuration, clients, and tool handlers using `pytest` and `pytest-httpx`.
- Integration tests hitting sandbox Jira/Zephyr endpoints with feature flags.
- Contract tests ensuring MCP JSON structures match expectations.
- Load tests for high-volume tool usage (optional stage).

## Deployment Options
- Local CLI using virtual environments or `uv`.
- Docker container built from slim Python base with non-root user.
- CI/CD pipelines targeting enterprise artifact registries.
- Integration with MCP-compatible clients (Claude Desktop, IDE plugins).

## Security Considerations
- Secure credential management (no plaintext tokens in repo, support external secret stores).
- TLS certificate verification and optional mutual TLS.
- Strict logging policies with PII/secret scrubbing.
- Rate limit compliance with Jira/Zephyr APIs.
- Immutable audit trails for test execution operations.
- Regular dependency scanning and patch management.

## Migration Checklist
- [ ] Align stakeholder expectations and sign-off on scope.
- [ ] Establish Python repo with initial scaffold.
- [ ] Verify configuration and secret handling in dev/staging environments.
- [ ] Achieve tool parity and pass automated test suite.
- [ ] Run pilot with selected teams, collect feedback, iterate.
- [ ] Decommission Node service after successful cutover and documentation handoff.
