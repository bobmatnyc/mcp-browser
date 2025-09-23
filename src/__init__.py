"""BrowserPyMCP - MCP server for browser console log capture and control."""

__version__ = "1.0.1"
__author__ = "BrowserPyMCP Team"

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
