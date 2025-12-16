"""Log query tool service for MCP browser control."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LogQueryToolService:
    """MCP tool handler for console log queries."""

    def __init__(self, browser_service=None):
        self.browser_service = browser_service

    async def handle_query_logs(
        self, port: int, last_n: int = 100, level_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Query console logs from browser.

        Args:
            port: Browser daemon port
            last_n: Number of recent logs to return
            level_filter: Filter by log levels

        Returns:
            Dict with success status and formatted log messages
        """
        if not self.browser_service:
            return {
                "success": False,
                "error": "Browser service not available",
                "formatted_text": "Browser service not available",
            }

        try:
            messages = await self.browser_service.query_logs(
                port=port, last_n=last_n, level_filter=level_filter
            )

            if not messages:
                return {
                    "success": True,
                    "message_count": 0,
                    "formatted_text": f"No console logs found for port {port}",
                }

            formatted_text = self._format_log_messages(messages)

            return {
                "success": True,
                "message_count": len(messages),
                "formatted_text": formatted_text,
            }

        except Exception as e:
            logger.exception("Failed to query logs")
            return {
                "success": False,
                "error": str(e),
                "formatted_text": f"Log query failed: {str(e)}",
            }

    def _format_log_messages(self, messages: List) -> str:
        """Format log messages for output.

        Args:
            messages: List of ConsoleMessage objects

        Returns:
            Formatted string with timestamps, levels, and messages
        """
        log_lines = []
        for msg in messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S.%f")[:-3]
            level = msg.level.value.upper()
            log_lines.append(f"[{timestamp}] [{level}] {msg.message}")
            if msg.stack_trace:
                log_lines.append(f"  Stack: {msg.stack_trace[:200]}")

        return f"Console logs (last {len(messages)}):\n\n" + "\n".join(log_lines)
