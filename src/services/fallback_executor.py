"""Fallback executor for browser actions with extension→AppleScript fallback.

This service provides a generic pattern for executing browser actions with automatic
fallback from extension (preferred) to AppleScript (macOS fallback).

Design Decision: Centralized Fallback Logic
--------------------------------------------
Rationale: Eliminates duplicated timeout and fallback logic across BrowserController
action methods (navigate, click, fill_field, get_element, execute_javascript).

Trade-offs:
- Complexity: Adds abstraction layer but reduces overall code duplication
- Maintainability: Single source of truth for fallback behavior
- Flexibility: Easy to adjust timeout and fallback strategy globally

Pattern:
1. Try extension handler with timeout
2. On timeout/error, fall back to AppleScript handler (if provided)
3. Return standardized result format

Extension Points: Can be extended to support additional fallback methods
or custom timeout strategies per action type.
"""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class FallbackExecutor:
    """Executes browser actions with automatic timeout-based fallback strategy.

    This service encapsulates the common pattern of trying extension first with
    timeout, then falling back to AppleScript on failure.

    Example:
        executor = FallbackExecutor(extension_timeout=5.0)

        result = await executor.execute_with_fallback(
            action_name="navigate",
            extension_handler=lambda: navigate_via_extension(port, url),
            applescript_handler=lambda: navigate_via_applescript(url)
        )

        if result["success"]:
            print(f"Navigated via {result.get('method', 'unknown')}")
    """

    def __init__(
        self, extension_timeout: float = 5.0, applescript_enabled: bool = True
    ):
        """Initialize fallback executor.

        Args:
            extension_timeout: Timeout in seconds for extension operations
            applescript_enabled: Whether AppleScript fallback is available
        """
        self.extension_timeout = extension_timeout
        self.applescript_enabled = applescript_enabled

    async def execute_with_fallback(
        self,
        action_name: str,
        extension_handler: Optional[Callable[[], Awaitable[Dict[str, Any]]]] = None,
        applescript_handler: Optional[Callable[[], Awaitable[Dict[str, Any]]]] = None,
        extension_only: bool = False,
    ) -> Dict[str, Any]:
        """Execute action with automatic extension→AppleScript fallback.

        Args:
            action_name: Name of action for logging (e.g., "navigate", "click")
            extension_handler: Async function to try via extension (optional)
            applescript_handler: Async function to try via AppleScript (fallback)
            extension_only: If True, don't fall back to AppleScript

        Returns:
            Result dict with keys:
                - success (bool): Whether action succeeded
                - error (str): Error message if failed
                - method (str): Method used ("extension", "applescript", "none")
                - data (Any): Action-specific data

        Example:
            result = await executor.execute_with_fallback(
                action_name="click",
                extension_handler=lambda: dom_service.click(port, selector),
                applescript_handler=lambda: applescript.click(selector)
            )
        """
        # Try extension first with timeout (if handler provided)
        if extension_handler:
            try:
                result = await asyncio.wait_for(
                    extension_handler(), timeout=self.extension_timeout
                )
                if result and result.get("success"):
                    logger.info(f"{action_name}: Completed via extension")
                    if "method" not in result:
                        result["method"] = "extension"
                    return result
                else:
                    logger.warning(
                        f"{action_name}: Extension returned unsuccessful result"
                    )
            except asyncio.TimeoutError:
                logger.warning(
                    f"{action_name}: Extension timed out after {self.extension_timeout}s"
                )
            except Exception as e:
                logger.warning(f"{action_name}: Extension failed: {e}")

        # Fall back to AppleScript if available and allowed
        if not extension_only and applescript_handler and self.applescript_enabled:
            try:
                result = await applescript_handler()
                if result and result.get("success"):
                    logger.info(f"{action_name}: Completed via AppleScript")
                    result["method"] = "applescript"
                    return result
                else:
                    logger.warning(
                        f"{action_name}: AppleScript returned unsuccessful result"
                    )
            except Exception as e:
                logger.warning(f"{action_name}: AppleScript failed: {e}")

        # Both methods failed or unavailable
        return {
            "success": False,
            "error": f"{action_name} failed: No available method succeeded",
            "method": "none",
            "data": None,
        }

    async def execute_extension_only(
        self,
        action_name: str,
        extension_handler: Callable[[], Awaitable[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Execute action via extension only (no fallback).

        Used for actions that ONLY work with extension (e.g., console capture, screenshots).

        Args:
            action_name: Name of action for logging
            extension_handler: Async function to execute via extension

        Returns:
            Result dict with success, error, method, data keys

        Example:
            result = await executor.execute_extension_only(
                action_name="query_logs",
                extension_handler=lambda: browser_service.query_logs(port, last_n=50)
            )
        """
        try:
            result = await asyncio.wait_for(
                extension_handler(), timeout=self.extension_timeout
            )
            logger.info(f"{action_name}: Extension-only action completed")
            if "method" not in result:
                result["method"] = "extension"
            return result
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"{action_name}: Extension timeout ({self.extension_timeout}s)",
                "method": "extension",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"{action_name}: Extension error: {str(e)}",
                "method": "extension",
                "data": None,
            }
