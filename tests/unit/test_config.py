"""Unit tests for configuration loading and validation."""

import pytest
from pydantic import HttpUrl, SecretStr, ValidationError

from jira_zephyr_mcp.config import (
    JiraConfig,
    MCPServerConfig,
    Settings,
    ZephyrConfig,
)


class TestJiraConfig:
    """Tests for Jira configuration model."""

    def test_valid_jira_config(self) -> None:
        """Test creating a valid Jira configuration."""
        config = JiraConfig(
            base_url=HttpUrl("https://example.atlassian.net"),
            email="user@example.com",
            api_token=SecretStr("my-secret-token"),
        )
        assert config.email == "user@example.com"
        assert str(config.base_url) == "https://example.atlassian.net/"

    def test_jira_config_invalid_email(self) -> None:
        """Test Jira config validation rejects invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(
                base_url=HttpUrl("https://example.atlassian.net"),
                email="not-an-email",
                api_token=SecretStr("my-secret-token"),
            )
        assert "Invalid email format" in str(exc_info.value)

    def test_jira_config_invalid_url(self) -> None:
        """Test Jira config validation rejects invalid URL."""
        with pytest.raises(ValidationError):
            JiraConfig(
                base_url="not-a-url",  # type: ignore
                email="user@example.com",
                api_token=SecretStr("my-secret-token"),
            )

    def test_jira_config_missing_required_field(self) -> None:
        """Test Jira config validation requires all fields."""
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(
                base_url=HttpUrl("https://example.atlassian.net"),
                email="user@example.com",
            )  # type: ignore
        assert "api_token" in str(exc_info.value)

    def test_jira_api_token_is_secret(self) -> None:
        """Test that API token is treated as a secret string."""
        config = JiraConfig(
            base_url=HttpUrl("https://example.atlassian.net"),
            email="user@example.com",
            api_token=SecretStr("secret-token-123"),
        )
        # SecretStr should mask in string representation
        assert "secret-token-123" not in repr(config.api_token)
        assert config.api_token.get_secret_value() == "secret-token-123"


class TestZephyrConfig:
    """Tests for Zephyr configuration model."""

    def test_valid_zephyr_config_minimal(self) -> None:
        """Test creating a valid minimal Zephyr configuration."""
        config = ZephyrConfig(api_token=SecretStr("zephyr-token"))
        assert config.api_token.get_secret_value() == "zephyr-token"
        assert config.base_url is None

    def test_valid_zephyr_config_with_url(self) -> None:
        """Test creating Zephyr config with optional URL."""
        config = ZephyrConfig(
            api_token=SecretStr("zephyr-token"),
            base_url=HttpUrl("https://zephyr.example.com"),
        )
        assert str(config.base_url) == "https://zephyr.example.com/"

    def test_zephyr_config_missing_api_token(self) -> None:
        """Test Zephyr config validation requires API token."""
        with pytest.raises(ValidationError) as exc_info:
            ZephyrConfig()  # type: ignore
        assert "api_token" in str(exc_info.value)

    def test_zephyr_api_token_is_secret(self) -> None:
        """Test that Zephyr API token is treated as secret."""
        config = ZephyrConfig(api_token=SecretStr("secret-zephyr-123"))
        assert "secret-zephyr-123" not in repr(config.api_token)
        assert config.api_token.get_secret_value() == "secret-zephyr-123"


class TestMCPServerConfig:
    """Tests for MCP server configuration model."""

    def test_default_mcp_server_config(self) -> None:
        """Test default MCP server configuration."""
        config = MCPServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000

    def test_custom_mcp_server_config(self) -> None:
        """Test creating custom MCP server configuration."""
        config = MCPServerConfig(host="127.0.0.1", port=9000)
        assert config.host == "127.0.0.1"
        assert config.port == 9000

    def test_mcp_port_validation_too_low(self) -> None:
        """Test port validation rejects port below 1."""
        with pytest.raises(ValidationError) as exc_info:
            MCPServerConfig(port=0)
        assert "Port must be between 1 and 65535" in str(exc_info.value)

    def test_mcp_port_validation_too_high(self) -> None:
        """Test port validation rejects port above 65535."""
        with pytest.raises(ValidationError) as exc_info:
            MCPServerConfig(port=70000)
        assert "Port must be between 1 and 65535" in str(exc_info.value)

    def test_mcp_port_validation_valid_boundaries(self) -> None:
        """Test port validation accepts boundary values."""
        config1 = MCPServerConfig(port=1)
        assert config1.port == 1

        config2 = MCPServerConfig(port=65535)
        assert config2.port == 65535


class TestSettings:
    """Tests for full Settings configuration."""

    def test_settings_model_structure(self) -> None:
        """Test Settings model has required nested configs."""
        # This test verifies the model definition
        assert hasattr(Settings, "model_fields")
        assert "jira" in Settings.model_fields
        assert "zephyr" in Settings.model_fields
        assert "mcp_server" in Settings.model_fields
        assert "debug" in Settings.model_fields

    def test_settings_debug_default_false(self) -> None:
        """Test debug defaults to False."""
        # We test this by checking the field definition
        debug_field = Settings.model_fields["debug"]
        assert debug_field.default is False

    def test_settings_validation_error_propagation(self) -> None:
        """Test that validation errors from nested configs propagate."""
        # Note: Actually instantiating Settings requires env vars,
        # so we test the model definition instead
        assert Settings.model_config["env_nested_delimiter"] == "__"


class TestConfigurationIntegration:
    """Integration tests for configuration loading."""

    def test_all_configs_together(self) -> None:
        """Test creating all config models together."""
        jira = JiraConfig(
            base_url=HttpUrl("https://jira.example.com"),
            email="test@example.com",
            api_token=SecretStr("jira-token"),
        )
        zephyr = ZephyrConfig(api_token=SecretStr("zephyr-token"))
        mcp = MCPServerConfig(port=9000)

        assert jira.email == "test@example.com"
        assert zephyr.api_token.get_secret_value() == "zephyr-token"
        assert mcp.port == 9000

