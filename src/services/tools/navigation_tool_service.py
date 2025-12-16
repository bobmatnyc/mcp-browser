"""Navigation tool service for MCP browser control.

Handles browser navigation operations with automatic WebSocket/AppleScript fallback.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import TextContent

logger = logging.getLogger(__name__)


class NavigationToolService:
    """MCP tool handler for browser navigation operations.

    Provides navigation with automatic fallback:
    1. Try BrowserController (supports AppleScript fallback on macOS)
    2. Fallback to direct BrowserService (WebSocket only)
    """

    def __init__(
        self, browser_service: Optional[Any] = None, browser_controller: Optional[Any] = None
    ) -> None:
        """Initialize with required services.

        Args:
            browser_service: Service for WebSocket-based browser communication
            browser_controller: Controller for AppleScript fallback (optional)
        """
        self.browser_service = browser_service
        self.browser_controller = browser_controller

    async def handle_navigate(
        self, port: int, url: str
    ) -> List[TextContent]:
        """Navigate browser to URL with automatic fallback.

        Args:
            port: Browser daemon port
            url: URL to navigate to

        Returns:
            List of TextContent with navigation result
        """
        if not url:
            return [
                TextContent(
                    type="text",
                    text="Error: 'url' is required for navigate action",
                )
            ]

        # Try BrowserController first for automatic fallback support
        if self.browser_controller:
            result = await self.browser_controller.navigate(url=url, port=port)

            if result["success"]:
                method = result.get("method", "extension")
                if method == "applescript":
                    return [
                        TextContent(
                            type="text",
                            text=f"Navigated to {url} using AppleScript fallback.\n"
                            f"Note: Console log capture requires the browser extension.",
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Navigated to {url} on port {port}",
                        )
                    ]
            else:
                error_msg = result.get("error", "Unknown error")
                return [
                    TextContent(
                        type="text",
                        text=f"Navigation failed: {error_msg}",
                    )
                ]

        # Fallback to direct browser_service (WebSocket only)
        if not self.browser_service:
            return [
                TextContent(
                    type="text",
                    text="Browser service not available",
                )
            ]

        success = await self.browser_service.navigate_browser(port, url)
        if success:
            return [
                TextContent(
                    type="text",
                    text=f"Navigated to {url} on port {port}",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Navigation failed on port {port}. No active connection.",
                )
            ]
