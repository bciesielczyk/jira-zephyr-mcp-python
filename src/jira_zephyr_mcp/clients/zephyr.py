"""Async Zephyr Scale REST API client with retry and logging support."""

import logging
from typing import Any, Optional

import httpx

from jira_zephyr_mcp.utils.http import get_retry_config

logger = logging.getLogger(__name__)


class ZephyrClientError(Exception):
    """Base exception for Zephyr client errors."""

    pass


class ZephyrAuthError(ZephyrClientError):
    """Authentication error."""

    pass


class ZephyrNotFoundError(ZephyrClientError):
    """Resource not found error."""

    pass


class ZephyrRateLimitError(ZephyrClientError):
    """Rate limit exceeded error."""

    pass


class ZephyrClient:
    """Async HTTP client for Zephyr Scale REST API."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize Zephyr client.

        Args:
            base_url: Zephyr Scale base URL
            api_token: Zephyr Scale API token for bearer auth
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ZephyrClient":
        """Async context manager entry."""
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create async client."""
        if self._client is None:
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_token}",
            }
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an HTTP request with retry/backoff policy.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            Response object
            
        Raises:
            ZephyrClientError: After max retries exhausted
        """
        retry_config = get_retry_config(self.max_retries)
        
        async for attempt in retry_config:
            with attempt:
                try:
                    client = self._get_client()
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        logger.error("Zephyr authentication failed")
                        raise ZephyrAuthError("Invalid Zephyr credentials")
                    elif e.response.status_code == 404:
                        logger.warning("Zephyr resource not found: %s", url)
                        raise ZephyrNotFoundError(f"Resource not found: {url}")
                    elif e.response.status_code == 429:
                        logger.warning("Zephyr rate limit exceeded")
                        raise
                    raise
                except (httpx.TimeoutException, httpx.HTTPError) as e:
                    logger.debug("Retrying request to %s after error: %s", url, str(e))
                    raise
        
        raise ZephyrClientError(f"Failed to make request to {url} after max retries")
