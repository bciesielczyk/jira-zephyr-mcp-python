"""Configuration loading and validation using pydantic models."""

from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class JiraConfig(BaseModel):
    """Jira API configuration."""

    base_url: HttpUrl = Field(..., description="Jira instance base URL")
    email: str = Field(..., description="Jira user email for authentication")
    api_token: SecretStr = Field(..., description="Jira API token")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("Invalid email format")
        return v


class ZephyrConfig(BaseModel):
    """Zephyr Scale API configuration."""

    api_token: SecretStr = Field(..., description="Zephyr Scale API token")
    base_url: HttpUrl | None = Field(
        default=None,
        description="Zephyr Scale base URL (optional, defaults to cloud)",
    )


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    host: str = Field(default="0.0.0.0", description="Server listen address")
    port: int = Field(default=8000, description="Server listen port")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    jira: JiraConfig
    zephyr: ZephyrConfig
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    debug: bool = Field(default=False, description="Enable debug logging")

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def load_config(
    jira_base_url: str | None = None,
    jira_email: str | None = None,
    jira_api_token: str | None = None,
    zephyr_api_token: str | None = None,
    zephyr_base_url: str | None = None,
    mcp_server_host: str | None = None,
    mcp_server_port: int | None = None,
    debug: bool | None = None,
) -> Settings:
    """Load configuration from environment variables and .env file.

    Args:
        jira_base_url: Jira base URL (overrides env var).
        jira_email: Jira email (overrides env var).
        jira_api_token: Jira API token (overrides env var).
        zephyr_api_token: Zephyr API token (overrides env var).
        zephyr_base_url: Zephyr base URL (overrides env var).
        mcp_server_host: MCP server host (overrides env var).
        mcp_server_port: MCP server port (overrides env var).
        debug: Debug mode (overrides env var).

    Returns:
        Settings: Validated configuration object.

    Raises:
        ValidationError: If configuration is invalid.
    """
    import os

    if jira_base_url is not None:
        os.environ["JIRA__BASE_URL"] = jira_base_url
    if jira_email is not None:
        os.environ["JIRA__EMAIL"] = jira_email
    if jira_api_token is not None:
        os.environ["JIRA__API_TOKEN"] = jira_api_token
    if zephyr_api_token is not None:
        os.environ["ZEPHYR__API_TOKEN"] = zephyr_api_token
    if zephyr_base_url is not None:
        os.environ["ZEPHYR__BASE_URL"] = zephyr_base_url
    if mcp_server_host is not None:
        os.environ["MCP_SERVER__HOST"] = mcp_server_host
    if mcp_server_port is not None:
        os.environ["MCP_SERVER__PORT"] = str(mcp_server_port)
    if debug is not None:
        os.environ["DEBUG"] = str(debug).lower()

    return Settings()  # type: ignore[call-arg]
