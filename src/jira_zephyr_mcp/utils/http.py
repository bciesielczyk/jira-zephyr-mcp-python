"""Shared HTTP utilities including retry logic and backoff policies."""

import logging
from typing import TypeVar

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_retry_config(max_retries: int = 3) -> AsyncRetrying:
    """
    Get tenacity AsyncRetrying configuration for HTTP operations.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        AsyncRetrying instance configured with exponential backoff
    """
    return AsyncRetrying(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
