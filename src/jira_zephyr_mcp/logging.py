"""Structured logging helpers with redaction support."""

from __future__ import annotations

import logging
import re
from typing import Any

try:  # pragma: no cover - import is environment dependent
    import structlog as _STRUCTLOG
except ModuleNotFoundError:  # pragma: no cover - exercised when dependency missing
    _STRUCTLOG = None  # type: ignore[assignment]


# Sensitive patterns to redact
SENSITIVE_PATTERNS = [
    (r"(?i)api[_-]?token['\"]?\s*[:=]\s*['\"]?([^'\"}\s]+)", r"api_token=***REDACTED***"),
    (r"(?i)password['\"]?\s*[:=]\s*['\"]?([^'\"}\s]+)", r"password=***REDACTED***"),
    (r"(?i)token['\"]?\s*[:=]\s*['\"]?([^'\"}\s]+)", r"token=***REDACTED***"),
    (r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*", r"Bearer ***REDACTED***"),
    (r"(?i)Basic\s+[A-Za-z0-9\+/]+=*", r"Basic ***REDACTED***"),
    (r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", r"***EMAIL_REDACTED***"),
]


def redact_sensitive_data(value: Any) -> Any:
    """
    Redact sensitive information from log messages.
    
    Args:
        value: Text or structured data to redact
        
    Returns:
        Redacted value
    """
    if not isinstance(value, str):
        return value

    for pattern, replacement in SENSITIVE_PATTERNS:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    return value


def redact_processor(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Structlog processor to redact sensitive data in log events.
    
    Args:
        logger: Logger instance
        method_name: Logging method name
        event_dict: Event dictionary
        
    Returns:
        Processed event dictionary with redacted values
    """
    for key, value in event_dict.items():
        if isinstance(value, str):
            event_dict[key] = redact_sensitive_data(value)
        elif isinstance(value, dict):
            event_dict[key] = {
                k: redact_sensitive_data(v) if isinstance(v, str) else v
                for k, v in value.items()
            }
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with JSON output and redaction.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    structlog_module = _STRUCTLOG
    if structlog_module is None:
        msg = "structlog is required to configure structured logging. Install the 'structlog' package."
        raise RuntimeError(msg)

    # Note: structlog.processors signature doesn't fully align with strict typing
    structlog_module.configure(
        processors=[
            redact_processor,  # type: ignore[list-item]
            structlog_module.processors.TimeStamper(fmt="iso"),
            structlog_module.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog_module.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
    )
