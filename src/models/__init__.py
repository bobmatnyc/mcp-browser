"""Data models for mcp-browser."""

from .console_message import ConsoleMessage, ConsoleLevel
from .browser_state import BrowserState, BrowserConnection

__all__ = [
    'ConsoleMessage',
    'ConsoleLevel',
    'BrowserState',
    'BrowserConnection'
]