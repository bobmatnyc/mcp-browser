"""MCP server implementation."""

import logging
from typing import Optional, List, Dict, Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, ImageContent

logger = logging.getLogger(__name__)


class MCPService:
    """MCP server for browser tools."""

    def __init__(
        self,
        browser_service=None,
        screenshot_service=None
    ):
        """Initialize MCP service.

        Args:
            browser_service: Browser service for navigation and logs
            screenshot_service: Screenshot service for captures
        """
        self.browser_service = browser_service
        self.screenshot_service = screenshot_service
        self.server = Server("browserpymcp")
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Set up MCP tools."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="browser_navigate",
                    description="Navigate browser to a specific URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number"
                            },
                            "url": {
                                "type": "string",
                                "description": "URL to navigate to"
                            }
                        },
                        "required": ["port", "url"]
                    }
                ),
                Tool(
                    name="browser_query_logs",
                    description="Query console logs from browser",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number"
                            },
                            "last_n": {
                                "type": "integer",
                                "description": "Number of recent logs to return",
                                "default": 100
                            },
                            "level_filter": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["debug", "info", "log", "warn", "error"]
                                },
                                "description": "Filter by log levels"
                            }
                        },
                        "required": ["port"]
                    }
                ),
                Tool(
                    name="browser_screenshot",
                    description="Capture a screenshot of browser viewport",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number"
                            },
                            "url": {
                                "type": "string",
                                "description": "Optional URL to navigate to before screenshot"
                            }
                        },
                        "required": ["port"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str,
            arguments: dict
        ) -> list[TextContent | ImageContent]:
            """Handle tool calls."""

            if name == "browser_navigate":
                return await self._handle_navigate(arguments)
            elif name == "browser_query_logs":
                return await self._handle_query_logs(arguments)
            elif name == "browser_screenshot":
                return await self._handle_screenshot(arguments)
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]

    async def _handle_navigate(
        self,
        arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle browser navigation.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        port = arguments.get("port")
        url = arguments.get("url")

        if not self.browser_service:
            return [TextContent(
                type="text",
                text="Browser service not available"
            )]

        success = await self.browser_service.navigate_browser(port, url)

        if success:
            return [TextContent(
                type="text",
                text=f"Successfully navigated browser on port {port} to {url}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to navigate browser on port {port}. "
                     f"No active connection found."
            )]

    async def _handle_query_logs(
        self,
        arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle log query.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        port = arguments.get("port")
        last_n = arguments.get("last_n", 100)
        level_filter = arguments.get("level_filter")

        if not self.browser_service:
            return [TextContent(
                type="text",
                text="Browser service not available"
            )]

        messages = await self.browser_service.query_logs(
            port=port,
            last_n=last_n,
            level_filter=level_filter
        )

        if not messages:
            return [TextContent(
                type="text",
                text=f"No console logs found for port {port}"
            )]

        # Format messages
        log_lines = []
        for msg in messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S.%f")[:-3]
            level = msg.level.value.upper()
            log_lines.append(f"[{timestamp}] [{level}] {msg.message}")

            if msg.stack_trace:
                log_lines.append(f"  Stack: {msg.stack_trace[:200]}")

        log_text = "\n".join(log_lines)

        return [TextContent(
            type="text",
            text=f"Console logs from port {port} (last {len(messages)} messages):\n\n{log_text}"
        )]

    async def _handle_screenshot(
        self,
        arguments: Dict[str, Any]
    ) -> List[ImageContent | TextContent]:
        """Handle screenshot capture.

        Args:
            arguments: Tool arguments

        Returns:
            List of image or text content responses
        """
        port = arguments.get("port")
        url = arguments.get("url")

        if not self.screenshot_service:
            return [TextContent(
                type="text",
                text="Screenshot service not available"
            )]

        screenshot_base64 = await self.screenshot_service.capture_screenshot(
            port=port,
            url=url
        )

        if screenshot_base64:
            return [ImageContent(
                type="image",
                data=screenshot_base64,
                mimeType="image/png"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to capture screenshot for port {port}"
            )]

    async def start(self) -> None:
        """Start the MCP server."""
        # Initialize server with options
        init_options = InitializationOptions(
            server_name="browserpymcp",
            server_version="1.0.0"
        )

        # The actual server start is handled by the stdio transport
        logger.info("MCP service initialized")

    async def run_stdio(self) -> None:
        """Run the MCP server with stdio transport."""
        from mcp.server.stdio import stdio

        async with stdio() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="browserpymcp",
                    server_version="1.0.0"
                )
            )