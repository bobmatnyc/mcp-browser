"""Screenshot tool service for MCP browser control."""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ScreenshotToolService:
    """MCP tool handler for screenshot capture.

    Handles browser_screenshot tool - captures viewport screenshots
    via browser extension, optionally navigating to URL first.
    """

    def __init__(self, browser_service=None):
        """Initialize with browser service.

        Args:
            browser_service: Service for WebSocket-based browser communication
        """
        self.browser_service = browser_service

    async def handle_screenshot(
        self, port: int, url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Capture screenshot via browser extension.

        Args:
            port: Browser daemon port
            url: Optional URL to navigate to before screenshot

        Returns:
            Dict with success status and base64 image data:
            {
                "success": True,
                "data": "base64-encoded-png-data",
                "error": None
            }

            Or on failure:
            {
                "success": False,
                "data": None,
                "error": "Error message"
            }
        """
        if not self.browser_service:
            return {
                "success": False,
                "data": None,
                "error": "Browser service not available",
            }

        try:
            # Navigate to URL if provided
            if url:
                logger.debug(f"Navigating to {url} before screenshot on port {port}")
                nav_success = await self.browser_service.navigate_browser(port, url)
                if not nav_success:
                    return {
                        "success": False,
                        "data": None,
                        "error": f"Failed to navigate to {url}",
                    }
                # Give page time to load (extension will handle readyState)
                import asyncio

                await asyncio.sleep(1.0)

            # Capture screenshot via extension
            result = await self.browser_service.capture_screenshot_via_extension(port)

            if result and result.get("success"):
                return {
                    "success": True,
                    "data": result.get("data"),
                    "error": None,
                }
            else:
                error_msg = result.get("error") if result else "Unknown error"
                return {
                    "success": False,
                    "data": None,
                    "error": f"Screenshot capture failed: {error_msg}",
                }

        except Exception as e:
            logger.error(f"Screenshot capture error on port {port}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Exception during screenshot: {str(e)}",
            }
