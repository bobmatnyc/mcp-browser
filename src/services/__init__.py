"""Services for mcp-browser."""

from .browser_service import BrowserService
from .mcp_service import MCPService
from .screenshot_service import ScreenshotService
from .storage_service import StorageService
from .websocket_service import WebSocketService

# AppleScript and BrowserController are imported conditionally in server.py
# to avoid platform-specific import errors

__all__ = [
    "StorageService",
    "WebSocketService",
    "BrowserService",
    "MCPService",
    "ScreenshotService",
]
