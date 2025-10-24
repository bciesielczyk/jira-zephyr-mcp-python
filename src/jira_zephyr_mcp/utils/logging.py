"""Logging utilities for structured log events."""

from typing import Any

import structlog

logger = structlog.get_logger()


def log_request(method: str, url: str, **kwargs: Any) -> None:
    """
    Log HTTP request details.
    
    Args:
        method: HTTP method
        url: Request URL
        **kwargs: Additional context
    """
    logger.debug("http_request", method=method, url=url, **kwargs)


def log_response(method: str, url: str, status_code: int, **kwargs: Any) -> None:
    """
    Log HTTP response details.
    
    Args:
        method: HTTP method
        url: Request URL
        status_code: HTTP status code
        **kwargs: Additional context
    """
    logger.debug(
        "http_response",
        method=method,
        url=url,
        status_code=status_code,
        **kwargs,
    )


def log_error(event: str, error: Exception, **kwargs: Any) -> None:
    """
    Log error with exception details.
    
    Args:
        event: Event description
        error: Exception instance
        **kwargs: Additional context
    """
    logger.error(
        event,
        error_type=type(error).__name__,
        error_message=str(error),
        **kwargs,
    )


def log_retry(attempt: int, max_attempts: int, url: str, reason: str, **kwargs: Any) -> None:
    """
    Log retry attempt.
    
    Args:
        attempt: Current attempt number
        max_attempts: Maximum attempts
        url: Request URL
        reason: Reason for retry
        **kwargs: Additional context
    """
    logger.warning(
        "http_retry",
        attempt=attempt,
        max_attempts=max_attempts,
        url=url,
        reason=reason,
        **kwargs,
    )
