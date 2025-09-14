"""BrowserPyMCP - MCP server for browser console log capture and control."""

__version__ = "1.0.0"
__author__ = "BrowserPyMCP Team"

from .services import (
    StorageService,
    WebSocketService,
    BrowserService,
    MCPService,
    ScreenshotService
)
from .models import (
    ConsoleMessage,
    ConsoleLevel,
    BrowserState,
    BrowserConnection
)
from .container import ServiceContainer

__all__ = [
    # Services
    'StorageService',
    'WebSocketService',
    'BrowserService',
    'MCPService',
    'ScreenshotService',
    # Models
    'ConsoleMessage',
    'ConsoleLevel',
    'BrowserState',
    'BrowserConnection',
    # Container
    'ServiceContainer',
    # Version
    '__version__'
]