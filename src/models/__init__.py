"""Data models for mcp-browser."""

from .browser_state import BrowserConnection, BrowserState
from .console_message import ConsoleLevel, ConsoleMessage

__all__ = ["ConsoleMessage", "ConsoleLevel", "BrowserState", "BrowserConnection"]
