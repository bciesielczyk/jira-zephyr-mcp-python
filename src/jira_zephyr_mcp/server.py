"""MCP Server implementation for Jira/Zephyr integration."""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from jira_zephyr_mcp.logging import setup_logging
from jira_zephyr_mcp.config import Settings
from jira_zephyr_mcp.clients import JiraClient, ZephyrClient

logger = logging.getLogger(__name__)


class JiraZephyrMCPServer:
    """MCP Server for Jira and Zephyr Scale integration."""

    def __init__(self, settings: Settings):
        """
        Initialize MCP server.
        
        Args:
            settings: Configuration settings
        """
        self.settings = settings
        self.server = Server("jira-zephyr-mcp")
        self.jira_client: JiraClient | None = None
        self.zephyr_client: ZephyrClient | None = None
        
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP tool handlers."""
        @self.server.list_tools()  # type: ignore[no-untyped-call, misc]
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="read_jira_issue",
                    description="Retrieve Jira issue details by key",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "issue_key": {
                                "type": "string",
                                "description": "Jira issue key (e.g., PROJ-123)",
                            },
                            "fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional list of specific fields to retrieve",
                            },
                        },
                        "required": ["issue_key"],
                    },
                ),
                Tool(
                    name="health_check",
                    description="Check server and API connectivity",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
            ]

        @self.server.call_tool()  # type: ignore[misc]
        async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            """Handle tool calls."""
            if name == "health_check":
                return await self._handle_health_check()
            elif name == "read_jira_issue":
                return await self._handle_read_jira_issue(arguments)
            else:
                return {
                    "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                    "isError": True,
                }

    async def _handle_health_check(self) -> dict[str, Any]:
        """Handle health check tool."""
        try:
            status = {
                "status": "healthy",
                "jira_configured": bool(self.settings.jira),
                "zephyr_configured": bool(self.settings.zephyr),
            }
            return {
                "content": [{"type": "text", "text": str(status)}],
                "isError": False,
            }
        except Exception as e:
            logger.exception("Health check failed")
            return {
                "content": [{"type": "text", "text": f"Health check failed: {str(e)}"}],
                "isError": True,
            }

    async def _handle_read_jira_issue(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle read_jira_issue tool."""
        try:
            issue_key = arguments.get("issue_key")
            fields = arguments.get("fields")
            
            if not issue_key:
                return {
                    "content": [{"type": "text", "text": "issue_key is required"}],
                    "isError": True,
                }
            
            if not self.settings.jira:
                return {
                    "content": [{"type": "text", "text": "Jira not configured"}],
                    "isError": True,
                }
            
            if not self.jira_client:
                self.jira_client = JiraClient(
                    base_url=str(self.settings.jira.base_url),
                    email=self.settings.jira.email,
                    api_token=self.settings.jira.api_token.get_secret_value(),
                )
            
            issue = await self.jira_client.get_issue(issue_key, fields=fields)
            return {
                "content": [{"type": "text", "text": str(issue)}],
                "isError": False,
            }
        except Exception as e:
            logger.exception("Failed to read Jira issue")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            }

    async def run(self) -> None:
        """Run the MCP server."""
        setup_logging("INFO")
        logger.info("Starting Jira/Zephyr MCP Server")
        await self.server.run_stdio()  # type: ignore[attr-defined]

    async def close(self) -> None:
        """Close server and client connections."""
        if self.jira_client:
            await self.jira_client.close()
        if self.zephyr_client:
            await self.zephyr_client.close()
