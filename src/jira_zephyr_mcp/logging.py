"""Structured logging setup with PII redaction."""

import logging
import re
from typing import Any

import structlog


# Sensitive patterns to redact
SENSITIVE_PATTERNS = [
    (r"(?i)api[_-]?token['\"]?\s*[:=]\s*['\"]?([^'\"}\s]+)", r"api_token=***REDACTED***"),
    (r"(?i)password['\"]?\s*[:=]\s*['\"]?([^'\"}\s]+)", r"password=***REDACTED***"),
    (r"(?i)token['\"]?\s*[:=]\s*['\"]?([^'\"}\s]+)", r"token=***REDACTED***"),
    (r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*", r"Bearer ***REDACTED***"),
    (r"(?i)Basic\s+[A-Za-z0-9\+/]+=*", r"Basic ***REDACTED***"),
    (r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", r"***EMAIL_REDACTED***"),
]


def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive information from log messages.
    
    Args:
        text: Text to redact
        
    Returns:
        Redacted text
    """
    if not isinstance(text, str):
        return text
    
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


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
    # Note: structlog.processors signature doesn't fully align with strict typing
    structlog.configure(
        processors=[
            redact_processor,  # type: ignore[list-item]
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
    )
