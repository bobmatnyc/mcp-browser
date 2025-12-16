"""Unified browser control with automatic extension/AppleScript fallback.

This service provides a unified interface for browser control that automatically
selects between browser extension (preferred) and AppleScript fallback (macOS).

Design Decision: Unified Browser Control with Automatic Fallback
-----------------------------------------------------------------
Rationale: Abstracts browser control to provide consistent interface regardless
of underlying implementation. Automatically falls back through methods:
1. Extension (WebSocket) - best performance, full features
2. AppleScript - macOS-only, slowest but reliable

Trade-offs:
- Complexity: Additional abstraction layer adds overhead
- Performance: Extension check adds ~10-50ms latency on first call
- Flexibility: Easy to add new control methods

Alternatives Considered:
1. Direct service calls: Rejected due to lack of fallback logic
2. Factory pattern: Rejected due to lack of runtime fallback switching
3. Strategy pattern with manual selection: Rejected due to poor UX

Extension Points: BrowserController interface allows adding new control
methods by implementing same interface pattern.

NOTE: Playwright/CDP support has been removed to prevent memory leaks.
"""

import logging
from enum import Flag, auto
from typing import Any, Dict, Optional

from .fallback_executor import FallbackExecutor

logger = logging.getLogger(__name__)


# Custom Exceptions
class ExtensionNotConnectedError(Exception):
    """Raised when extension is not connected."""

    pass


class ExtensionTimeoutError(Exception):
    """Raised when extension operation times out."""

    pass


class BrowserNotAvailableError(Exception):
    """Raised when browser is not available for connection."""

    pass


class Capability(Flag):
    """Browser control capabilities using Flag for bitwise operations.

    Capabilities can be combined using bitwise OR (|) and checked using bitwise AND (&).
    Example: EXTENSION_CAPS = CONSOLE_CAPTURE | MULTI_TAB | DOM_INTERACTION
    """

    CONSOLE_CAPTURE = auto()  # Capture console logs from browser
    MULTI_TAB = auto()  # Manage multiple tabs
    DOM_INTERACTION = auto()  # Click, fill, get elements
    SCREENSHOTS = auto()  # Capture screenshots
    CRASH_RECOVERY = auto()  # Recover from browser crashes
    CROSS_BROWSER = auto()  # Support multiple browser types


# Capability sets for each control method
EXTENSION_CAPS = (
    Capability.CONSOLE_CAPTURE
    | Capability.MULTI_TAB
    | Capability.DOM_INTERACTION
    | Capability.SCREENSHOTS
)

APPLESCRIPT_CAPS = Capability.DOM_INTERACTION


class CapabilityDetector:
    """Detects available browser control capabilities.

    Checks which control methods are available and reports their capabilities.
    Capabilities update dynamically based on active connections.

    Example:
        detector = CapabilityDetector(browser_controller)
        capabilities = await detector.detect()
        if Capability.CONSOLE_CAPTURE in capabilities:
            print("Console capture available!")

        report = await detector.get_capability_report()
        # Returns human-readable capability information
    """

    def __init__(self, browser_controller: "BrowserController"):
        """Initialize capability detector.

        Args:
            browser_controller: BrowserController instance to inspect
        """
        self.controller = browser_controller

    async def detect(self) -> Capability:
        """Detect available capabilities based on active connections.

        Returns:
            Combined Capability flags representing available capabilities

        Example:
            caps = await detector.detect()
            # caps might be: CONSOLE_CAPTURE | MULTI_TAB | DOM_INTERACTION
        """
        available = Capability(0)  # Start with no capabilities

        # Check extension connection (all ports)
        has_extension = await self._has_any_extension_connection()
        if has_extension:
            available |= EXTENSION_CAPS

        # Check AppleScript availability
        has_applescript = self._has_applescript()
        if has_applescript:
            available |= APPLESCRIPT_CAPS

        return available

    async def get_capability_report(self) -> Dict[str, Any]:
        """Get human-readable capability report.

        Returns:
            Dictionary with capability details:
            {
                "capabilities": ["CONSOLE_CAPTURE", "MULTI_TAB", ...],
                "methods": {
                    "extension": {"available": bool, "capabilities": [...]},
                    "applescript": {"available": bool, "capabilities": [...]}
                },
                "summary": "human-readable summary"
            }
        """
        capabilities = await self.detect()

        # Check individual methods
        has_extension = await self._has_any_extension_connection()
        has_applescript = self._has_applescript()

        # Build capability list
        capability_names = []
        for cap in Capability:
            if cap in capabilities:
                capability_names.append(cap.name)

        # Build method details
        methods = {
            "extension": {
                "available": has_extension,
                "capabilities": [c.name for c in Capability if c in EXTENSION_CAPS],
                "description": "Browser extension (WebSocket) - best performance",
            },
            "applescript": {
                "available": has_applescript,
                "capabilities": [c.name for c in Capability if c in APPLESCRIPT_CAPS],
                "description": "AppleScript (macOS) - reliable fallback",
            },
        }

        # Build summary
        active_methods = [name for name, info in methods.items() if info["available"]]
        if not active_methods:
            summary = "No browser control methods available. Install extension."
        elif len(active_methods) == 1:
            summary = f"Using {active_methods[0]} for browser control."
        else:
            summary = f"Multiple methods available: {', '.join(active_methods)}. Using automatic fallback."

        return {
            "capabilities": capability_names,
            "methods": methods,
            "summary": summary,
            "active_methods": active_methods,
        }

    async def _has_any_extension_connection(self) -> bool:
        """Check if any browser extension is connected.

        Returns:
            True if at least one extension connection exists
        """
        if not self.controller.browser_service:
            return False

        try:
            # Check if browser_state has any active connections
            connections = self.controller.browser_service.browser_state.connections
            return len(connections) > 0
        except Exception as e:
            logger.debug(f"Error checking extension connections: {e}")
            return False

    def _has_applescript(self) -> bool:
        """Check if AppleScript is available.

        Returns:
            True if running on macOS with AppleScript service
        """
        if not self.controller.applescript:
            return False
        return self.controller.applescript.is_macos


class BrowserController:
    """Unified browser control with automatic fallback.

    This service coordinates between browser extension (WebSocket) and
    AppleScript fallback to provide seamless browser control.

    Features:
    - Automatic method selection (extension → AppleScript)
    - Configuration-driven mode selection ("auto", "extension", "applescript")
    - Clear error messages when no control method available
    - Console log limitation communication (extension-only feature)
    - Timeout-based fallback (extension timeout → AppleScript fallback)

    Performance:
    - Extension: ~10-50ms per operation (WebSocket)
    - AppleScript: ~100-500ms per operation (subprocess + interpreter)
    - Fallback check: ~10-50ms (WebSocket connection check)

    Timeout Configuration:
    - Extension timeout: 5.0 seconds

    Usage:
        controller = BrowserController(websocket, browser, applescript, config)
        result = await controller.navigate("https://example.com", port=8875)
        # Automatically uses extension if available, falls back to AppleScript
    """

    # Timeout configuration (seconds)
    EXTENSION_TIMEOUT = 5.0

    # Actions that require extension (no AppleScript fallback)
    EXTENSION_ONLY_ACTIONS = ["get_console_logs", "monitor_tabs", "query_logs"]

    def __init__(
        self,
        websocket_service,
        browser_service,
        applescript_service,
        config: Optional[Dict[str, Any]] = None,
        daemon_client=None,
    ):
        """Initialize browser controller.

        Args:
            websocket_service: WebSocket service for extension communication
            browser_service: Browser service for state management
            applescript_service: AppleScript service for macOS fallback
            config: Optional configuration dictionary
            daemon_client: Optional daemon client for MCP mode relay
        """
        self.websocket = websocket_service
        self.browser_service = browser_service
        self.applescript = applescript_service
        self.config = config or {}
        self.daemon_client = daemon_client

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

        # Initialize fallback executor
        self.fallback_executor = FallbackExecutor(
            extension_timeout=self.EXTENSION_TIMEOUT,
            applescript_enabled=(
                self.fallback_enabled
                and self.applescript is not None
                and self.applescript.is_macos
            ),
        )

        logger.info(
            f"BrowserController initialized: mode={self.mode}, "
            f"browser={self.preferred_browser}, fallback={self.fallback_enabled}"
        )

    # NOTE: CDP/Playwright support was removed in v2.2.29 to prevent memory leaks.
    # Navigation and all browser control now works exclusively through:
    # 1. Extension (WebSocket) - preferred, full features
    # 2. AppleScript (macOS) - fallback for basic operations
    #
    # The optional `mcp-browser connect` CLI command still references CDP for
    # documentation purposes but is not used in the normal MCP flow.

    async def execute_action(
        self, action: str, port: Optional[int] = None, **kwargs
    ) -> Dict[str, Any]:
        """Execute action with automatic timeout-based fallback.

        Tries extension first with timeout, automatically falls back to AppleScript on timeout or disconnection.

        Args:
            action: Action name ('navigate', 'click', 'fill', 'get_element', 'execute_javascript')
            port: Optional port for extension
            **kwargs: Action-specific arguments

        Returns:
            {"success": bool, "error": str, "method": str, "data": Any}

        Example:
            result = await controller.execute_action('navigate', port=8875, url='https://example.com')
            # Tries extension first (5s timeout), falls back to AppleScript automatically
        """
        # Check if action requires extension-only features
        if action in self.EXTENSION_ONLY_ACTIONS:
            return await self._extension_only(action, port, **kwargs)

        logger.info(f"execute_action: action={action}, port={port}")

        # Create extension handler if port provided and connection exists
        async def extension_handler() -> Dict[str, Any]:
            return await self._try_extension(action, port, **kwargs)

        # Create AppleScript handler if available
        async def applescript_handler() -> Dict[str, Any]:
            return await self._try_applescript(action, **kwargs)

        # Check if extension is available
        has_extension = port and await self._has_extension_connection(port)
        has_applescript = (
            self.fallback_enabled and self.applescript and self.applescript.is_macos
        )

        # Execute with fallback using FallbackExecutor
        if has_extension or has_applescript:
            return await self.fallback_executor.execute_with_fallback(
                action_name=action,
                extension_handler=extension_handler if has_extension else None,
                applescript_handler=applescript_handler if has_applescript else None,
                extension_only=False,
            )

        # No methods available
        return {
            "success": False,
            "error": f"No available method for action '{action}'",
            "method": "none",
            "data": None,
        }

    async def _extension_only(
        self, action: str, port: Optional[int], **kwargs
    ) -> Dict[str, Any]:
        """Handle actions that ONLY work with extension.

        Args:
            action: Action name (must be in EXTENSION_ONLY_ACTIONS)
            port: Port number for extension
            **kwargs: Action-specific arguments

        Returns:
            Result dictionary with error if extension not connected
        """
        if not port:
            return {
                "success": False,
                "error": f"Action '{action}' requires extension (port must be provided)",
                "method": "extension",
                "data": None,
            }

        if not await self._has_extension_connection(port):
            return {
                "success": False,
                "error": f"Action '{action}' requires extension but no connection found on port {port}",
                "method": "extension",
                "data": None,
            }

        # Create extension handler
        async def extension_handler() -> Dict[str, Any]:
            return await self._try_extension(action, port, **kwargs)

        # Use FallbackExecutor for extension-only actions
        return await self.fallback_executor.execute_extension_only(
            action_name=action,
            extension_handler=extension_handler,
        )

    async def _try_extension(self, action: str, port: int, **kwargs) -> Dict[str, Any]:
        """Execute action via extension.

        Args:
            action: Action name
            port: Port number
            **kwargs: Action-specific arguments

        Returns:
            Result dictionary

        Raises:
            ExtensionNotConnectedError: If extension disconnected during operation
        """
        # Verify connection still active
        if not await self._has_extension_connection(port):
            raise ExtensionNotConnectedError(f"Extension not connected on port {port}")

        # Map action to appropriate method
        if action == "navigate":
            url = kwargs.get("url")
            if not url:
                return {
                    "success": False,
                    "error": "Missing 'url' argument",
                    "method": "extension",
                    "data": None,
                }

            # Use daemon client if available (MCP mode), otherwise direct
            if self.daemon_client and self.daemon_client.is_connected:
                result = await self.daemon_client.navigate(url, port)
                return {
                    "success": result.get("success", False),
                    "error": result.get("error") if not result.get("success") else None,
                    "method": "extension",
                    "data": {"url": url, "port": port, "via": "daemon"},
                }
            else:
                success = await self.browser_service.navigate_browser(port, url)
                return {
                    "success": success,
                    "error": None if success else "Navigation command failed",
                    "method": "extension",
                    "data": {"url": url, "port": port},
                }

        elif action in ["click", "fill", "get_element"]:
            # Use DOMInteractionService
            from .dom_interaction_service import DOMInteractionService

            dom_service = DOMInteractionService(browser_service=self.browser_service)

            if action == "click":
                result = await dom_service.click(
                    port=port,
                    selector=kwargs.get("selector"),
                    xpath=kwargs.get("xpath"),
                    text=kwargs.get("text"),
                    index=kwargs.get("index", 0),
                    tab_id=kwargs.get("tab_id"),
                )
            elif action == "fill":
                result = await dom_service.fill_field(
                    port=port,
                    value=kwargs.get("value", ""),
                    selector=kwargs.get("selector"),
                    xpath=kwargs.get("xpath"),
                    index=kwargs.get("index", 0),
                    tab_id=kwargs.get("tab_id"),
                )
            else:  # get_element
                result = await dom_service.get_element(
                    port=port,
                    selector=kwargs.get("selector"),
                    xpath=kwargs.get("xpath"),
                    text=kwargs.get("text"),
                    index=kwargs.get("index", 0),
                    tab_id=kwargs.get("tab_id"),
                )

            return {
                "success": result.get("success", False),
                "error": result.get("error"),
                "method": "extension",
                "data": result,
            }

        elif action == "execute_javascript":
            return {
                "success": False,
                "error": "JavaScript execution not yet supported via extension",
                "method": "extension",
                "data": None,
            }

        return {
            "success": False,
            "error": f"Unknown action '{action}'",
            "method": "extension",
            "data": None,
        }

    async def _try_applescript(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute action via AppleScript.

        Args:
            action: Action name
            **kwargs: Action-specific arguments

        Returns:
            Result dictionary
        """
        # Map action to appropriate AppleScript method
        if action == "navigate":
            url = kwargs.get("url")
            if not url:
                return {
                    "success": False,
                    "error": "Missing 'url' argument",
                    "method": "applescript",
                    "data": None,
                }
            result = await self.applescript.navigate(
                url, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        elif action == "click":
            selector = kwargs.get("selector")
            if not selector:
                return {
                    "success": False,
                    "error": "CSS selector required for AppleScript mode (xpath/text not supported)",
                    "method": "applescript",
                    "data": None,
                }
            result = await self.applescript.click(
                selector, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        elif action == "fill":
            selector = kwargs.get("selector")
            value = kwargs.get("value", "")
            if not selector:
                return {
                    "success": False,
                    "error": "CSS selector required for AppleScript mode",
                    "method": "applescript",
                    "data": None,
                }
            result = await self.applescript.fill_field(
                selector, value, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        elif action == "get_element":
            selector = kwargs.get("selector")
            if not selector:
                return {
                    "success": False,
                    "error": "CSS selector required for AppleScript mode",
                    "method": "applescript",
                    "data": None,
                }
            result = await self.applescript.get_element(
                selector, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        elif action == "execute_javascript":
            script = kwargs.get("script")
            if not script:
                return {
                    "success": False,
                    "error": "Missing 'script' argument",
                    "method": "applescript",
                    "data": None,
                }
            result = await self.applescript.execute_javascript(
                script, browser=self.preferred_browser
            )
            return {
                "success": result["success"],
                "error": result.get("error"),
                "method": "applescript",
                "data": result.get("data"),
            }

        return {
            "success": False,
            "error": f"Unknown action '{action}'",
            "method": "applescript",
            "data": None,
        }

    async def navigate(self, url: str, port: Optional[int] = None) -> Dict[str, Any]:
        """Navigate browser to URL with automatic timeout-based fallback.

        Args:
            url: URL to navigate to
            port: Optional port number for extension (None = use fallback)

        Returns:
            {"success": bool, "error": str, "method": str, "data": dict}

        Mode Selection Logic:
        1. If mode="extension": only try extension, fail if unavailable
        2. If mode="applescript": only try AppleScript, fail if unavailable
        3. If mode="auto" (default): try extension (5s timeout) → AppleScript

        Error Handling:
        - Extension timeout/unavailable → Falls back to AppleScript (macOS)
        - All methods unavailable → Returns clear error
        """
        logger.info(f"navigate() called: url={url}, port={port}, mode={self.mode}")

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

            # Use extension (via daemon client if available, otherwise direct)
            if self.daemon_client and self.daemon_client.is_connected:
                # MCP mode: relay command via daemon
                result = await self.daemon_client.navigate(url, port)
                return {
                    "success": result.get("success", False),
                    "error": result.get("error") if not result.get("success") else None,
                    "method": "extension",
                    "data": {"url": url, "port": port, "via": "daemon"},
                }
            else:
                # Direct mode: use browser_service
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

        # Mode: auto (try extension → AppleScript with timeouts)
        return await self.execute_action("navigate", port=port, url=url)

    async def click(
        self,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        text: Optional[str] = None,
        index: int = 0,
        port: Optional[int] = None,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Click element with automatic timeout-based fallback.

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
        # Use execute_action for auto mode with timeouts
        if self.mode == "auto":
            return await self.execute_action(
                "click",
                port=port,
                selector=selector,
                xpath=xpath,
                text=text,
                index=index,
                tab_id=tab_id,
            )

        # For specific modes, use old logic
        method = self._select_browser_method(port)

        if method == "extension":
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
        """Fill form field with automatic timeout-based fallback.

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
        # Use execute_action for auto mode with timeouts
        if self.mode == "auto":
            return await self.execute_action(
                "fill",
                port=port,
                value=value,
                selector=selector,
                xpath=xpath,
                index=index,
                tab_id=tab_id,
            )

        # For specific modes, use old logic
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
        """Get element information with automatic timeout-based fallback.

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
        # Use execute_action for auto mode with timeouts
        if self.mode == "auto":
            return await self.execute_action(
                "get_element",
                port=port,
                selector=selector,
                xpath=xpath,
                text=text,
                index=index,
                tab_id=tab_id,
            )

        # For specific modes, use old logic
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

        return self._no_method_available_error()

    async def execute_javascript(
        self, script: str, port: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute JavaScript with automatic timeout-based fallback.

        Args:
            script: JavaScript code to execute
            port: Optional port number for extension

        Returns:
            {"success": bool, "error": str, "method": str, "data": Any}
        """
        # Use execute_action for auto mode with timeouts
        if self.mode == "auto":
            return await self.execute_action(
                "execute_javascript", port=port, script=script
            )

        # For specific modes, use old logic
        method = self._select_browser_method(port)

        if method == "extension":
            # Extension doesn't have direct JS execution in current API
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

        return self._no_method_available_error()

    async def _has_extension_connection(self, port: int) -> bool:
        """Check if extension is connected on port.

        Args:
            port: Port number to check (may be server port or client port)

        Returns:
            True if extension is connected

        Performance: O(1) dictionary lookup + await (~10-50ms)
        """
        # Check if daemon_client is available (MCP mode)
        if self.daemon_client and self.daemon_client.is_connected:
            logger.info(f"_has_extension_connection({port}): Using daemon client relay")
            return True

        # If no websocket service available, extension cannot be connected
        if not self.websocket:
            logger.info(
                f"_has_extension_connection({port}): No websocket service or daemon client"
            )
            return False

        try:
            # Try exact port match first
            connection = await self.browser_service.browser_state.get_connection(port)
            logger.info(
                f"_has_extension_connection({port}): Exact match = {connection is not None}"
            )

            # If no exact match and port is in server range, try any active connection
            if connection is None and 8851 <= port <= 8895:
                connection = (
                    await self.browser_service.browser_state.get_any_active_connection()
                )
                logger.info(
                    f"_has_extension_connection({port}): Fallback match = {connection is not None}"
                )
                if connection:
                    logger.info(
                        f"_has_extension_connection({port}): Found active connection on port {connection.port}, is_active={connection.is_active}"
                    )

            result = connection is not None and connection.websocket is not None
            logger.info(f"_has_extension_connection({port}): Final result = {result}")
            return result
        except Exception as e:
            logger.info(f"Error checking extension connection: {e}")
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
        3. mode="auto": check extension → AppleScript availability
        """
        if self.mode == "extension":
            return "extension"

        if self.mode == "applescript":
            return "applescript"

        # Auto mode: check availability in order

        # 1. Extension (if port provided)
        if port:
            return "extension"

        # 2. AppleScript (if macOS and fallback enabled)
        if self.fallback_enabled and self.applescript and self.applescript.is_macos:
            return "applescript"

        return "none"

    def _no_method_available_error(self) -> Dict[str, Any]:
        """Return error when no control method is available.

        Returns:
            Error response dictionary
        """
        error_parts = ["No browser control method available."]

        if self.applescript and self.applescript.is_macos:
            error_parts.append(
                "Browser extension not connected. "
                "Install extension: mcp-browser quickstart"
            )
        else:
            error_parts.append(
                "Browser extension not connected and AppleScript not available on this platform. "
                "Install extension: mcp-browser quickstart"
            )

        error_msg = "\n".join(error_parts)

        return {
            "success": False,
            "error": error_msg,
            "method": "none",
            "data": None,
        }
