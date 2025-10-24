"""Async Jira Cloud REST API client with retry and logging support."""

import logging
from typing import Any, Optional

import httpx

from jira_zephyr_mcp.utils.http import get_retry_config

logger = logging.getLogger(__name__)


class JiraClientError(Exception):
    """Base exception for Jira client errors."""

    pass


class JiraAuthError(JiraClientError):
    """Authentication error."""

    pass


class JiraNotFoundError(JiraClientError):
    """Resource not found error."""

    pass


class JiraRateLimitError(JiraClientError):
    """Rate limit exceeded error."""

    pass


class JiraClient:
    """Async HTTP client for Jira Cloud REST API."""

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize Jira client.

        Args:
            base_url: Jira instance base URL (e.g., https://your-domain.atlassian.net)
            email: Jira user email for Basic auth
            api_token: Jira API token for Basic auth
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "JiraClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Accept": "application/json"},
            auth=(self.email, self.api_token),
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create async client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                auth=(self.email, self.api_token),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_issue(
        self,
        issue_key: str,
        fields: Optional[list[str]] = None,
        expand: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Retrieve issue details.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: Optional list of specific fields to retrieve
            expand: Optional list of fields to expand

        Returns:
            Issue data as dictionary

        Raises:
            JiraAuthError: Authentication failed
            JiraNotFoundError: Issue not found
            JiraRateLimitError: Rate limit exceeded
            JiraClientError: Other API errors
        """
        url = f"/rest/api/3/issue/{issue_key}"
        params = {}

        if fields:
            params["fields"] = ",".join(fields)
        if expand:
            params["expand"] = ",".join(expand)

        response = await self._make_request("GET", url, params=params)
        data: dict[str, Any] = response.json()
        return data

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
            JiraClientError: After max retries exhausted
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
                        logger.error("Jira authentication failed")
                        raise JiraAuthError("Invalid Jira credentials")
                    elif e.response.status_code == 404:
                        logger.warning("Jira resource not found: %s", url)
                        raise JiraNotFoundError(f"Resource not found: {url}")
                    elif e.response.status_code == 429:
                        logger.warning("Jira rate limit exceeded")
                        raise
                    raise
                except (httpx.TimeoutException, httpx.HTTPError) as e:
                    logger.debug("Retrying request to %s after error: %s", url, str(e))
                    raise
        
        raise JiraClientError(f"Failed to make request to {url} after max retries")
