"""Services for mcp-browser."""

# MCP installer bridge is available for installation commands
from . import mcp_installer_bridge
from .browser_service import BrowserService
from .daemon_client import DaemonClient
from .mcp_service import MCPService
from .storage_service import StorageService
from .websocket_service import WebSocketService

# AppleScript and BrowserController are imported conditionally in server.py
# to avoid platform-specific import errors

__all__ = [
    "StorageService",
    "WebSocketService",
    "BrowserService",
    "MCPService",
    "DaemonClient",
    "mcp_installer_bridge",
]
