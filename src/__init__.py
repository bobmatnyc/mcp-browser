"""mcp-browser - MCP server for browser console log capture and control."""

# Import version from single source of truth
from ._version import __author__, __description__, __version__, version_string
from .container import ServiceContainer
from .models import BrowserConnection, BrowserState, ConsoleLevel, ConsoleMessage
from .services import (
    BrowserService,
    MCPService,
    ScreenshotService,
    StorageService,
    WebSocketService,
)

__all__ = [
    # Services
    "StorageService",
    "WebSocketService",
    "BrowserService",
    "MCPService",
    "ScreenshotService",
    # Models
    "ConsoleMessage",
    "ConsoleLevel",
    "BrowserState",
    "BrowserConnection",
    # Container
    "ServiceContainer",
    # Version
    "__version__",
    "__author__",
    "__description__",
    "version_string",
]
