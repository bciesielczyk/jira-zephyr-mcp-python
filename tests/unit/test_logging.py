"""Tests for structured logging and redaction."""

import pytest

from jira_zephyr_mcp import logging as logging_module
from jira_zephyr_mcp.logging import redact_sensitive_data, redact_processor


class TestRedaction:
    """Test sensitive data redaction."""

    def test_redact_api_token(self) -> None:
        """Test API token redaction."""
        text = "api_token='abc123def456'"
        result = redact_sensitive_data(text)
        assert "abc123def456" not in result
        assert "***REDACTED***" in result

    def test_redact_password(self) -> None:
        """Test password redaction."""
        text = 'password: "mySecretPassword123"'
        result = redact_sensitive_data(text)
        assert "mySecretPassword123" not in result
        assert "***REDACTED***" in result

    def test_redact_bearer_token(self) -> None:
        """Test bearer token redaction."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact_sensitive_data(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "***REDACTED***" in result

    def test_redact_basic_auth(self) -> None:
        """Test basic auth redaction."""
        text = "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ="
        result = redact_sensitive_data(text)
        assert "dXNlcm5hbWU6cGFzc3dvcmQ=" not in result
        assert "***REDACTED***" in result

    def test_redact_email(self) -> None:
        """Test email redaction."""
        text = "user: john.doe@example.com"
        result = redact_sensitive_data(text)
        assert "john.doe@example.com" not in result
        assert "***EMAIL_REDACTED***" in result

    def test_no_redaction_for_normal_text(self) -> None:
        """Test that normal text is not redacted."""
        text = "This is a normal log message"
        result = redact_sensitive_data(text)
        assert result == text

    def test_redact_processor_string_values(self) -> None:
        """Test redact processor with string values."""
        event_dict = {
            "message": "Request with Authorization: Bearer secret123token",
            "url": "https://api.example.com",
        }
        result = redact_processor(None, "info", event_dict)
        assert "secret123token" not in result["message"]
        assert "***REDACTED***" in result["message"]

    def test_redact_processor_nested_dict(self) -> None:
        """Test redact processor with nested dictionaries."""
        event_dict = {
            "message": "API call",
            "headers": {
                "Authorization": "Bearer token123abc",
                "Content-Type": "application/json",
            },
        }
        result = redact_processor(None, "info", event_dict)
        assert "token123abc" not in result["headers"]["Authorization"]
        assert "***REDACTED***" in result["headers"]["Authorization"]
        assert result["headers"]["Content-Type"] == "application/json"

    def test_redact_processor_non_string_values(self) -> None:
        """Test redact processor preserves non-string values."""
        event_dict = {
            "status_code": 200,
            "attempt": 1,
            "success": True,
        }
        result = redact_processor(None, "info", event_dict)
        assert result["status_code"] == 200
        assert result["attempt"] == 1
        assert result["success"] is True


class TestSetupLogging:
    """Tests for structured logging setup."""

    def test_setup_logging_requires_structlog(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """setup_logging should raise a helpful error when structlog is unavailable."""
        monkeypatch.setattr(logging_module, "_STRUCTLOG", None, raising=False)

        with pytest.raises(RuntimeError) as exc_info:
            logging_module.setup_logging()

        assert "structlog is required" in str(exc_info.value)
