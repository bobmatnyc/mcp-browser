"""Unified browser control with automatic extension/AppleScript fallback.

This service provides a unified interface for browser control that automatically
selects between browser extension (preferred) and AppleScript fallback (macOS).

Design Decision: Unified Browser Control with Automatic Fallback
-----------------------------------------------------------------
Rationale: Abstracts browser control to provide consistent interface regardless
of underlying implementation. Automatically falls back to AppleScript when
extension is unavailable, providing graceful degradation.

Trade-offs:
- Complexity: Additional abstraction layer adds ~50 LOC overhead
- Performance: Extension check adds ~10-50ms latency on first call
- Flexibility: Easy to add new control methods (CDP, Playwright, etc.)

Alternatives Considered:
1. Direct service calls: Rejected due to lack of fallback logic
2. Factory pattern: Rejected due to lack of runtime fallback switching
3. Strategy pattern with manual selection: Rejected due to poor UX

Extension Points: BrowserController interface allows adding new control
methods (CDP, Playwright) by implementing same interface pattern.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BrowserController:
    """Unified browser control with automatic fallback.

    This service coordinates between browser extension (WebSocket) and
    AppleScript fallback to provide seamless browser control.

    Features:
    - Automatic method selection (extension-first, AppleScript fallback)
    - Configuration-driven mode selection ("auto", "extension", "applescript")
    - Clear error messages when no control method available
    - Console log limitation communication (extension-only feature)

    Performance:
    - Extension: ~10-50ms per operation (WebSocket)
    - AppleScript: ~100-500ms per operation (subprocess + interpreter)
    - Fallback check: ~10-50ms (WebSocket connection check)

    Usage:
        controller = BrowserController(websocket, browser, applescript, config)
        result = await controller.navigate("https://example.com", port=8875)
        # Automatically uses extension if available, falls back to AppleScript
    """

    def __init__(
        self,
        websocket_service,
        browser_service,
        applescript_service,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize browser controller.

        Args:
            websocket_service: WebSocket service for extension communication
            browser_service: Browser service for state management
            applescript_service: AppleScript service for macOS fallback
            config: Optional configuration dictionary
        """
        self.websocket = websocket_service
        self.browser_service = browser_service
        self.applescript = applescript_service
        self.config = config or {}

        # Get browser control configuration
        browser_control = self.config.get("browser_control", {})
        self.mode = browser_control.get("mode", "auto")
        self.preferred_browser = browser_control.get("applescript_browser", "Safari")
        self.fallback_enabled = browser_control.get("fallback_enabled", True)
        self.prompt_for_permissions = browser_control.get(
            "prompt_for_permissions", True
        )

        # Validate mode
        if self.mode not in ["auto", "extension", "applescript"]:
            logger.warning(f"Invalid mode '{self.mode}', using 'auto'")
            self.mode = "auto"

        logger.info(
            f"BrowserController initialized: mode={self.mode}, "
            f"browser={self.preferred_browser}, fallback={self.fallback_enabled}"
        )

    async def navigate(self, url: str, port: Optional[int] = None) -> Dict[str, Any]:
        """Navigate browser to URL with automatic fallback.

        Args:
            url: URL to navigate to
            port: Optional port number for extension (None = use AppleScript)

        Returns:
            {"success": bool, "error": str, "method": str, "data": dict}

        Mode Selection Logic:
        1. If mode="extension": only try extension, fail if unavailable
        2. If mode="applescript": only try AppleScript, fail if unavailable
        3. If mode="auto" (default): try extension first, fall back to AppleScript

        Error Handling:
        - Extension unavailable + macOS: Falls back to AppleScript
        - Extension unavailable + Linux/Windows: Returns clear error
        - AppleScript disabled: Returns permission instructions
        """
        # Mode: extension-only
        if self.mode == "extension":
            if not port:
                return {
                    "success": False,
                    "error": "Port required for extension mode",
                    "method": "extension",
                    "data": None,
                }

            if not await self._has_extension_connection(port):
                return {
                    "success": False,
                    "error": (
                        f"No browser extension connected on port {port}. "
                        "Install extension: mcp-browser quickstart"
                    ),
                    "method": "extension",
                    "data": None,
                }

            # Use extension
            success = await self.browser_service.navigate_browser(port, url)
            return {
                "success": success,
                "error": None if success else "Navigation command failed",
                "method": "extension",
                "data": {"url": url, "port": port},
            }

        # Mode: applescript-only
        if self.mode == "applescript":
            result = await self.applescript.navigate(
                url, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        # Mode: auto (try extension, fall back to AppleScript)
        if port and await self._has_extension_connection(port):
            # Use extension
            success = await self.browser_service.navigate_browser(port, url)
            return {
                "success": success,
                "error": None if success else "Navigation command failed",
                "method": "extension",
                "data": {"url": url, "port": port},
            }

        # Extension unavailable, try AppleScript fallback
        if self.fallback_enabled and self.applescript.is_macos:
            logger.info("Extension unavailable, falling back to AppleScript")
            result = await self.applescript.navigate(
                url, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        # No control method available
        if self.applescript.is_macos:
            error_msg = (
                "Browser extension not connected. Falling back to AppleScript.\n"
                "Note: Console log capture requires the browser extension.\n"
                "Install extension: mcp-browser quickstart"
            )
        else:
            error_msg = (
                "Browser extension not connected and no fallback available on this platform.\n"
                "AppleScript fallback is only available on macOS.\n"
                "Install extension: mcp-browser quickstart"
            )

        return {
            "success": False,
            "error": error_msg,
            "method": "none",
            "data": None,
        }

    async def click(
        self,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        text: Optional[str] = None,
        index: int = 0,
        port: Optional[int] = None,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Click element with automatic fallback.

        Args:
            selector: CSS selector
            xpath: XPath expression
            text: Text content to match
            index: Element index if multiple matches
            port: Optional port number for extension
            tab_id: Optional tab ID for extension

        Returns:
            {"success": bool, "error": str, "method": str, "data": dict}
        """
        method = self._select_browser_method(port)

        if method == "extension":
            # Use extension via DOMInteractionService (circular dependency avoided)
            # Import here to avoid circular import
            from .dom_interaction_service import DOMInteractionService

            dom_service = DOMInteractionService(browser_service=self.browser_service)
            result = await dom_service.click(
                port=port,
                selector=selector,
                xpath=xpath,
                text=text,
                index=index,
                tab_id=tab_id,
            )
            return {
                "success": result.get("success", False),
                "error": result.get("error"),
                "method": "extension",
                "data": result,
            }

        elif method == "applescript":
            if not selector:
                return {
                    "success": False,
                    "error": "CSS selector required for AppleScript mode (xpath/text not supported)",
                    "method": "applescript",
                    "data": None,
                }

            logger.info("Using AppleScript fallback for click operation")
            result = await self.applescript.click(
                selector, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        else:
            return self._no_method_available_error()

    async def fill_field(
        self,
        value: str,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        index: int = 0,
        port: Optional[int] = None,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fill form field with automatic fallback.

        Args:
            value: Value to fill
            selector: CSS selector
            xpath: XPath expression
            index: Element index if multiple matches
            port: Optional port number for extension
            tab_id: Optional tab ID for extension

        Returns:
            {"success": bool, "error": str, "method": str, "data": dict}
        """
        method = self._select_browser_method(port)

        if method == "extension":
            from .dom_interaction_service import DOMInteractionService

            dom_service = DOMInteractionService(browser_service=self.browser_service)
            result = await dom_service.fill_field(
                port=port,
                value=value,
                selector=selector,
                xpath=xpath,
                index=index,
                tab_id=tab_id,
            )
            return {
                "success": result.get("success", False),
                "error": result.get("error"),
                "method": "extension",
                "data": result,
            }

        elif method == "applescript":
            if not selector:
                return {
                    "success": False,
                    "error": "CSS selector required for AppleScript mode",
                    "method": "applescript",
                    "data": None,
                }

            logger.info("Using AppleScript fallback for fill_field operation")
            result = await self.applescript.fill_field(
                selector, value, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        else:
            return self._no_method_available_error()

    async def get_element(
        self,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        text: Optional[str] = None,
        index: int = 0,
        port: Optional[int] = None,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get element information with automatic fallback.

        Args:
            selector: CSS selector
            xpath: XPath expression
            text: Text content to match
            index: Element index if multiple matches
            port: Optional port number for extension
            tab_id: Optional tab ID for extension

        Returns:
            {"success": bool, "error": str, "method": str, "data": dict}
        """
        method = self._select_browser_method(port)

        if method == "extension":
            from .dom_interaction_service import DOMInteractionService

            dom_service = DOMInteractionService(browser_service=self.browser_service)
            result = await dom_service.get_element(
                port=port,
                selector=selector,
                xpath=xpath,
                text=text,
                index=index,
                tab_id=tab_id,
            )
            return {
                "success": result.get("success", False),
                "error": result.get("error"),
                "method": "extension",
                "data": result,
            }

        elif method == "applescript":
            if not selector:
                return {
                    "success": False,
                    "error": "CSS selector required for AppleScript mode",
                    "method": "applescript",
                    "data": None,
                }

            logger.info("Using AppleScript fallback for get_element operation")
            result = await self.applescript.get_element(
                selector, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        else:
            return self._no_method_available_error()

    async def execute_javascript(
        self, script: str, port: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute JavaScript with automatic fallback.

        Args:
            script: JavaScript code to execute
            port: Optional port number for extension

        Returns:
            {"success": bool, "error": str, "method": str, "data": Any}
        """
        method = self._select_browser_method(port)

        if method == "extension":
            # Extension doesn't have direct JS execution in current API
            # Would need to add this to DOMInteractionService
            return {
                "success": False,
                "error": "JavaScript execution not yet supported via extension",
                "method": "extension",
                "data": None,
            }

        elif method == "applescript":
            logger.info("Using AppleScript fallback for JavaScript execution")
            result = await self.applescript.execute_javascript(
                script, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        else:
            return self._no_method_available_error()

    async def _has_extension_connection(self, port: int) -> bool:
        """Check if extension is connected on port.

        Args:
            port: Port number to check

        Returns:
            True if extension is connected

        Performance: O(1) dictionary lookup + await (~10-50ms)
        """
        # If no websocket service available, extension cannot be connected
        if not self.websocket:
            return False

        try:
            connection = await self.browser_service.browser_state.get_connection(port)
            return connection is not None and connection.websocket is not None
        except Exception as e:
            logger.debug(f"Error checking extension connection: {e}")
            return False

    def _select_browser_method(self, port: Optional[int] = None) -> str:
        """Select browser control method based on configuration and availability.

        Args:
            port: Optional port number for extension

        Returns:
            "extension", "applescript", or "none"

        Decision Logic:
        1. mode="extension": return "extension" (fail if unavailable)
        2. mode="applescript": return "applescript"
        3. mode="auto": check extension availability, fallback to AppleScript
        """
        if self.mode == "extension":
            return "extension"

        if self.mode == "applescript":
            return "applescript"

        # Auto mode: check extension availability
        # Note: Can't use async here, so we check synchronously
        # This is a limitation - we'll return "extension" if port is provided
        # and let the caller handle connection errors
        if port:
            return "extension"

        # No port provided, use AppleScript if available
        if self.fallback_enabled and self.applescript.is_macos:
            return "applescript"

        return "none"

    def _no_method_available_error(self) -> Dict[str, Any]:
        """Return error when no control method is available.

        Returns:
            Error response dictionary
        """
        if self.applescript and self.applescript.is_macos:
            error_msg = (
                "Browser extension not connected. Falling back to AppleScript.\n"
                "Note: Console log capture requires the browser extension.\n"
                "Install extension: mcp-browser quickstart"
            )
        else:
            error_msg = (
                "Browser extension not connected and no fallback available on this platform.\n"
                "AppleScript fallback is only available on macOS.\n"
                "Install extension: mcp-browser quickstart"
            )

        return {
            "success": False,
            "error": error_msg,
            "method": "none",
            "data": None,
        }
