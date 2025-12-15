"""Unified browser control with automatic extension/CDP/AppleScript fallback.

This service provides a unified interface for browser control that automatically
selects between browser extension (preferred), CDP via Playwright, and AppleScript
fallback (macOS).

Design Decision: Unified Browser Control with Automatic Fallback
-----------------------------------------------------------------
Rationale: Abstracts browser control to provide consistent interface regardless
of underlying implementation. Automatically falls back through methods:
1. Extension (WebSocket) - best performance, full features
2. CDP (Playwright) - cross-platform, good performance
3. AppleScript - macOS-only, slowest but reliable

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
"""

import asyncio
import logging
from enum import Flag, auto
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# CDP/Playwright imports - optional dependency
try:
    from playwright.async_api import Browser, Page, Playwright, async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.debug("Playwright not available - CDP support disabled")


# Custom Exceptions
class ExtensionNotConnectedError(Exception):
    """Raised when extension is not connected."""

    pass


class ExtensionTimeoutError(Exception):
    """Raised when extension operation times out."""

    pass


class BrowserNotAvailableError(Exception):
    """Raised when browser is not available for CDP connection."""

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
    Capability.CONSOLE_CAPTURE | Capability.MULTI_TAB | Capability.DOM_INTERACTION
)

CDP_CAPS = (
    Capability.DOM_INTERACTION
    | Capability.SCREENSHOTS
    | Capability.CRASH_RECOVERY
    | Capability.CROSS_BROWSER
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

        # Check CDP connection
        has_cdp = await self.controller._has_cdp_connection()
        if has_cdp:
            available |= CDP_CAPS

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
                    "cdp": {"available": bool, "capabilities": [...]},
                    "applescript": {"available": bool, "capabilities": [...]}
                },
                "summary": "human-readable summary"
            }
        """
        capabilities = await self.detect()

        # Check individual methods
        has_extension = await self._has_any_extension_connection()
        has_cdp = await self.controller._has_cdp_connection()
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
            "cdp": {
                "available": has_cdp,
                "capabilities": [c.name for c in Capability if c in CDP_CAPS],
                "description": "Chrome DevTools Protocol - cross-platform",
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
            summary = "No browser control methods available. Install extension or start browser with CDP."
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

    This service coordinates between browser extension (WebSocket), CDP
    (Playwright), and AppleScript fallback to provide seamless browser control.

    Features:
    - Automatic method selection (extension → CDP → AppleScript)
    - Configuration-driven mode selection ("auto", "extension", "cdp", "applescript")
    - Clear error messages when no control method available
    - Console log limitation communication (extension-only feature)
    - Timeout-based fallback (extension timeout → CDP fallback)

    Performance:
    - Extension: ~10-50ms per operation (WebSocket)
    - CDP: ~50-150ms per operation (Chrome DevTools Protocol)
    - AppleScript: ~100-500ms per operation (subprocess + interpreter)
    - Fallback check: ~10-50ms (WebSocket connection check)

    Timeout Configuration:
    - Extension timeout: 5.0 seconds
    - CDP timeout: 10.0 seconds

    Usage:
        controller = BrowserController(websocket, browser, applescript, config)
        result = await controller.navigate("https://example.com", port=8875)
        # Automatically uses extension if available, falls back to CDP, then AppleScript
    """

    # Timeout configuration (seconds)
    EXTENSION_TIMEOUT = 5.0
    CDP_TIMEOUT = 10.0

    # Actions that require extension (no CDP/AppleScript fallback)
    EXTENSION_ONLY_ACTIONS = ["get_console_logs", "monitor_tabs", "query_logs"]

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

        # CDP configuration
        self.cdp_port = browser_control.get("cdp_port", 9222)
        self.cdp_enabled = (
            browser_control.get("cdp_enabled", True) and PLAYWRIGHT_AVAILABLE
        )

        # CDP state
        self.playwright: Optional[Playwright] = None
        self.cdp_browser: Optional[Browser] = None
        self.cdp_page: Optional[Page] = None

        # Validate mode
        if self.mode not in ["auto", "extension", "cdp", "applescript"]:
            logger.warning(f"Invalid mode '{self.mode}', using 'auto'")
            self.mode = "auto"

        logger.info(
            f"BrowserController initialized: mode={self.mode}, "
            f"browser={self.preferred_browser}, fallback={self.fallback_enabled}, "
            f"cdp_enabled={self.cdp_enabled}"
        )

    async def init_cdp(self, port: int = None) -> bool:
        """Initialize CDP connection to existing browser.

        Args:
            port: CDP port number (default: 9222)

        Returns:
            True if connection successful, False otherwise

        Example:
            # Start Chrome with: chrome --remote-debugging-port=9222
            await controller.init_cdp(9222)
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not installed - CDP support unavailable")
            return False

        if not self.cdp_enabled:
            logger.debug("CDP disabled in configuration")
            return False

        port = port or self.cdp_port

        try:
            # Initialize Playwright
            if not self.playwright:
                self.playwright = await async_playwright().start()

            # Connect to existing browser via CDP
            endpoint = f"http://localhost:{port}"
            logger.info(f"Connecting to browser via CDP: {endpoint}")

            self.cdp_browser = await self.playwright.chromium.connect_over_cdp(endpoint)

            # Get first page/context
            if self.cdp_browser.contexts:
                context = self.cdp_browser.contexts[0]
                if context.pages:
                    self.cdp_page = context.pages[0]
                    logger.info("CDP connection established successfully")
                    return True

            logger.warning("CDP connected but no pages available")
            return False

        except Exception as e:
            logger.error(f"Failed to initialize CDP connection: {e}")
            await self.close_cdp()
            return False

    async def close_cdp(self) -> None:
        """Close CDP connection and cleanup resources."""
        try:
            if self.cdp_browser:
                await self.cdp_browser.close()
                self.cdp_browser = None
                self.cdp_page = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("CDP connection closed")

        except Exception as e:
            logger.error(f"Error closing CDP connection: {e}")

    async def connect_to_existing_browser(self, cdp_port: int = 9222) -> Dict[str, Any]:
        """Connect to existing Chrome browser via CDP.

        Args:
            cdp_port: Port where Chrome is running with CDP (default 9222)

        Returns:
            Dict with connection status, browser version, and page count:
            {
                "success": bool,
                "browser_version": str,
                "page_count": int,
                "cdp_port": int,
                "error": Optional[str]
            }

        Raises:
            BrowserNotAvailableError: If Chrome is not running with CDP

        Example:
            # Start Chrome with: chrome --remote-debugging-port=9222
            result = await controller.connect_to_existing_browser(9222)
            if result["success"]:
                print(f"Connected to {result['browser_version']}")
        """
        import aiohttp

        # Check if Chrome is running with remote debugging using aiohttp
        cdp_url = f"http://localhost:{cdp_port}/json/version"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    cdp_url, timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        raise BrowserNotAvailableError(
                            f"CDP endpoint returned status {response.status}. "
                            f"Ensure Chrome is running with --remote-debugging-port={cdp_port}"
                        )

                    version_info = await response.json()
                    browser_version = version_info.get("Browser", "Unknown")

        except aiohttp.ClientConnectionError:
            raise BrowserNotAvailableError(
                f"Cannot connect to Chrome on port {cdp_port}. "
                f"Start Chrome with: chrome --remote-debugging-port={cdp_port}"
            )
        except asyncio.TimeoutError:
            raise BrowserNotAvailableError(
                f"Connection to Chrome on port {cdp_port} timed out. "
                f"Ensure Chrome is running with --remote-debugging-port={cdp_port}"
            )
        except Exception as e:
            raise BrowserNotAvailableError(
                f"Failed to check CDP availability: {str(e)}"
            )

        # Connect via Playwright's connect_over_cdp
        try:
            if not PLAYWRIGHT_AVAILABLE:
                return {
                    "success": False,
                    "error": "Playwright not installed. Install with: pip install playwright && playwright install",
                    "browser_version": None,
                    "page_count": 0,
                    "cdp_port": cdp_port,
                }

            # Initialize Playwright if needed
            if not self.playwright:
                self.playwright = await async_playwright().start()

            # Connect to existing browser via CDP
            endpoint = f"http://localhost:{cdp_port}"
            logger.info(f"Connecting to browser via CDP: {endpoint}")

            self.cdp_browser = await self.playwright.chromium.connect_over_cdp(endpoint)

            # Count pages across all contexts
            page_count = 0
            if self.cdp_browser.contexts:
                for context in self.cdp_browser.contexts:
                    page_count += len(context.pages)

                # Set first available page as active
                if self.cdp_browser.contexts[0].pages:
                    self.cdp_page = self.cdp_browser.contexts[0].pages[0]

            logger.info(
                f"CDP connection established: {browser_version}, "
                f"{page_count} page(s) available"
            )

            return {
                "success": True,
                "browser_version": browser_version,
                "page_count": page_count,
                "cdp_port": cdp_port,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Failed to connect to browser via CDP: {e}")
            await self.close_cdp()

            return {
                "success": False,
                "error": f"Failed to connect via CDP: {str(e)}",
                "browser_version": browser_version,
                "page_count": 0,
                "cdp_port": cdp_port,
            }

    async def _has_cdp_connection(self) -> bool:
        """Check if CDP browser is connected and has pages.

        Returns:
            True if CDP connection is active
        """
        try:
            if not self.cdp_browser:
                return False

            # Check if browser is still connected
            if not self.cdp_browser.is_connected():
                logger.debug("CDP browser disconnected")
                await self.close_cdp()
                return False

            # Ensure we have a page
            if self.cdp_browser.contexts and self.cdp_browser.contexts[0].pages:
                return True

            logger.debug("CDP connected but no pages available")
            return False

        except Exception as e:
            logger.debug(f"CDP connection check failed: {e}")
            return False

    async def _get_cdp_page(self) -> Page:
        """Get the active page from CDP browser.

        Returns:
            Active Page instance

        Raises:
            RuntimeError: If no page available
        """
        if not self.cdp_browser or not self.cdp_browser.contexts:
            raise RuntimeError("CDP browser not connected")

        context = self.cdp_browser.contexts[0]
        if not context.pages:
            raise RuntimeError("No pages available in CDP browser")

        # Update stored page reference
        self.cdp_page = context.pages[0]
        return self.cdp_page

    async def execute_action(
        self, action: str, port: Optional[int] = None, **kwargs
    ) -> Dict[str, Any]:
        """Execute action with automatic timeout-based fallback.

        Tries extension first with timeout, automatically falls back to CDP on timeout or disconnection.

        Args:
            action: Action name ('navigate', 'click', 'fill', 'get_element', 'execute_javascript')
            port: Optional port for extension
            **kwargs: Action-specific arguments

        Returns:
            {"success": bool, "error": str, "method": str, "data": Any}

        Example:
            result = await controller.execute_action('navigate', port=8875, url='https://example.com')
            # Tries extension first (5s timeout), falls back to CDP automatically
        """
        # Check if action requires extension-only features
        if action in self.EXTENSION_ONLY_ACTIONS:
            return await self._extension_only(action, port, **kwargs)

        # Try extension first with timeout (if port provided)
        logger.info(f"execute_action: action={action}, port={port}")
        if port and await self._has_extension_connection(port):
            try:
                result = await asyncio.wait_for(
                    self._try_extension(action, port, **kwargs),
                    timeout=self.EXTENSION_TIMEOUT,
                )
                if result.get("success"):
                    logger.info(f"Action '{action}' completed via extension")
                    return result
            except asyncio.TimeoutError:
                logger.warning(
                    f"Extension timeout ({self.EXTENSION_TIMEOUT}s) for '{action}', falling back to CDP"
                )
            except ExtensionNotConnectedError:
                logger.info(f"Extension disconnected, using CDP for '{action}'")
            except Exception as e:
                logger.warning(
                    f"Extension error for '{action}': {e}, falling back to CDP"
                )

        # Fallback to CDP
        if self.cdp_enabled:
            try:
                result = await asyncio.wait_for(
                    self._try_cdp(action, **kwargs), timeout=self.CDP_TIMEOUT
                )
                if result.get("success"):
                    logger.info(f"Action '{action}' completed via CDP")
                    return result
            except asyncio.TimeoutError:
                logger.error(f"CDP timeout ({self.CDP_TIMEOUT}s) for '{action}'")
            except Exception as e:
                logger.warning(f"CDP error for '{action}': {e}")

        # Last resort: AppleScript
        if self.fallback_enabled and self.applescript.is_macos:
            try:
                result = await self._try_applescript(action, **kwargs)
                if result.get("success"):
                    logger.info(f"Action '{action}' completed via AppleScript")
                    return result
            except Exception as e:
                logger.warning(f"AppleScript error for '{action}': {e}")

        return {
            "success": False,
            "error": f"All methods failed for action '{action}'",
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

        try:
            result = await asyncio.wait_for(
                self._try_extension(action, port, **kwargs),
                timeout=self.EXTENSION_TIMEOUT,
            )
            logger.info(f"Extension-only action '{action}' completed")
            return result
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Extension timeout ({self.EXTENSION_TIMEOUT}s) for '{action}'",
                "method": "extension",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Extension error for '{action}': {str(e)}",
                "method": "extension",
                "data": None,
            }

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

    async def _try_cdp(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute action via CDP.

        Args:
            action: Action name
            **kwargs: Action-specific arguments

        Returns:
            Result dictionary
        """
        # Initialize CDP if not connected
        if not await self._has_cdp_connection():
            if not await self.init_cdp():
                return {
                    "success": False,
                    "error": f"CDP connection not available for action '{action}'",
                    "method": "cdp",
                    "data": None,
                }

        page = await self._get_cdp_page()

        # Map action to appropriate Playwright method
        if action == "navigate":
            url = kwargs.get("url")
            if not url:
                return {
                    "success": False,
                    "error": "Missing 'url' argument",
                    "method": "cdp",
                    "data": None,
                }
            await page.goto(url, wait_until="domcontentloaded")
            return {
                "success": True,
                "error": None,
                "method": "cdp",
                "data": {"url": url, "cdp_port": self.cdp_port},
            }

        elif action == "click":
            selector = kwargs.get("selector")
            xpath = kwargs.get("xpath")
            text = kwargs.get("text")
            index = kwargs.get("index", 0)

            if selector:
                await page.click(selector)
            elif xpath:
                await page.click(f"xpath={xpath}")
            elif text:
                await page.get_by_text(text).nth(index).click()
            else:
                return {
                    "success": False,
                    "error": "Must provide selector, xpath, or text",
                    "method": "cdp",
                    "data": None,
                }

            return {
                "success": True,
                "error": None,
                "method": "cdp",
                "data": {"clicked": True},
            }

        elif action == "fill":
            selector = kwargs.get("selector")
            xpath = kwargs.get("xpath")
            value = kwargs.get("value", "")

            if selector:
                await page.fill(selector, value)
            elif xpath:
                await page.fill(f"xpath={xpath}", value)
            else:
                return {
                    "success": False,
                    "error": "Must provide selector or xpath",
                    "method": "cdp",
                    "data": None,
                }

            return {
                "success": True,
                "error": None,
                "method": "cdp",
                "data": {"filled": True, "value": value},
            }

        elif action == "get_element":
            selector = kwargs.get("selector")
            xpath = kwargs.get("xpath")
            text = kwargs.get("text")
            index = kwargs.get("index", 0)

            element = None
            if selector:
                element = await page.query_selector(selector)
            elif xpath:
                element = await page.query_selector(f"xpath={xpath}")
            elif text:
                element = await page.get_by_text(text).nth(index).element_handle()
            else:
                return {
                    "success": False,
                    "error": "Must provide selector, xpath, or text",
                    "method": "cdp",
                    "data": None,
                }

            if not element:
                return {
                    "success": False,
                    "error": "Element not found",
                    "method": "cdp",
                    "data": None,
                }

            text_content = await element.text_content()
            return {
                "success": True,
                "error": None,
                "method": "cdp",
                "data": {"text": text_content or ""},
            }

        elif action == "execute_javascript":
            script = kwargs.get("script")
            if not script:
                return {
                    "success": False,
                    "error": "Missing 'script' argument",
                    "method": "cdp",
                    "data": None,
                }
            result = await page.evaluate(script)
            return {"success": True, "error": None, "method": "cdp", "data": result}

        return {
            "success": False,
            "error": f"Unknown action '{action}'",
            "method": "cdp",
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
        2. If mode="cdp": only try CDP, fail if unavailable
        3. If mode="applescript": only try AppleScript, fail if unavailable
        4. If mode="auto" (default): try extension (5s timeout) → CDP (10s timeout) → AppleScript

        Error Handling:
        - Extension timeout/unavailable → Falls back to CDP
        - CDP unavailable → Falls back to AppleScript (macOS)
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

            # Use extension
            success = await self.browser_service.navigate_browser(port, url)
            return {
                "success": success,
                "error": None if success else "Navigation command failed",
                "method": "extension",
                "data": {"url": url, "port": port},
            }

        # Mode: cdp-only
        if self.mode == "cdp":
            try:
                if not await self._has_cdp_connection():
                    # Try to initialize CDP
                    if not await self.init_cdp():
                        return {
                            "success": False,
                            "error": (
                                "CDP connection not available. "
                                f"Ensure browser is running with --remote-debugging-port={self.cdp_port}"
                            ),
                            "method": "cdp",
                            "data": None,
                        }

                page = await self._get_cdp_page()
                await page.goto(url, wait_until="domcontentloaded")
                return {
                    "success": True,
                    "error": None,
                    "method": "cdp",
                    "data": {"url": url, "cdp_port": self.cdp_port},
                }

            except Exception as e:
                logger.error(f"CDP navigation failed: {e}")
                return {
                    "success": False,
                    "error": f"CDP navigation failed: {str(e)}",
                    "method": "cdp",
                    "data": None,
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

        # Mode: auto (try extension → CDP → AppleScript with timeouts)
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

        elif method == "cdp":
            try:
                if not await self._has_cdp_connection():
                    if not await self.init_cdp():
                        # Fall through to next method
                        if self.fallback_enabled and self.applescript.is_macos:
                            method = "applescript"
                        else:
                            return self._no_method_available_error()
                    else:
                        page = await self._get_cdp_page()

                        # Determine locator strategy
                        if selector:
                            await page.click(selector)
                        elif xpath:
                            await page.click(f"xpath={xpath}")
                        elif text:
                            await page.get_by_text(text).nth(index).click()
                        else:
                            return {
                                "success": False,
                                "error": "Must provide selector, xpath, or text",
                                "method": "cdp",
                                "data": None,
                            }

                        return {
                            "success": True,
                            "error": None,
                            "method": "cdp",
                            "data": {"clicked": True},
                        }
                else:
                    page = await self._get_cdp_page()

                    # Determine locator strategy
                    if selector:
                        await page.click(selector)
                    elif xpath:
                        await page.click(f"xpath={xpath}")
                    elif text:
                        await page.get_by_text(text).nth(index).click()
                    else:
                        return {
                            "success": False,
                            "error": "Must provide selector, xpath, or text",
                            "method": "cdp",
                            "data": None,
                        }

                    return {
                        "success": True,
                        "error": None,
                        "method": "cdp",
                        "data": {"clicked": True},
                    }

            except Exception as e:
                logger.error(f"CDP click failed: {e}")
                # Fall through to AppleScript
                if self.fallback_enabled and self.applescript.is_macos:
                    method = "applescript"
                else:
                    return {
                        "success": False,
                        "error": f"CDP click failed: {str(e)}",
                        "method": "cdp",
                        "data": None,
                    }

        if method == "applescript":
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

        elif method == "cdp":
            try:
                if not await self._has_cdp_connection():
                    if not await self.init_cdp():
                        # Fall through to next method
                        if self.fallback_enabled and self.applescript.is_macos:
                            method = "applescript"
                        else:
                            return self._no_method_available_error()
                    else:
                        page = await self._get_cdp_page()

                        # Determine locator strategy
                        if selector:
                            await page.fill(selector, value)
                        elif xpath:
                            await page.fill(f"xpath={xpath}", value)
                        else:
                            return {
                                "success": False,
                                "error": "Must provide selector or xpath",
                                "method": "cdp",
                                "data": None,
                            }

                        return {
                            "success": True,
                            "error": None,
                            "method": "cdp",
                            "data": {"filled": True, "value": value},
                        }
                else:
                    page = await self._get_cdp_page()

                    # Determine locator strategy
                    if selector:
                        await page.fill(selector, value)
                    elif xpath:
                        await page.fill(f"xpath={xpath}", value)
                    else:
                        return {
                            "success": False,
                            "error": "Must provide selector or xpath",
                            "method": "cdp",
                            "data": None,
                        }

                    return {
                        "success": True,
                        "error": None,
                        "method": "cdp",
                        "data": {"filled": True, "value": value},
                    }

            except Exception as e:
                logger.error(f"CDP fill_field failed: {e}")
                # Fall through to AppleScript
                if self.fallback_enabled and self.applescript.is_macos:
                    method = "applescript"
                else:
                    return {
                        "success": False,
                        "error": f"CDP fill_field failed: {str(e)}",
                        "method": "cdp",
                        "data": None,
                    }

        if method == "applescript":
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

        elif method == "cdp":
            try:
                if not await self._has_cdp_connection():
                    if not await self.init_cdp():
                        # Fall through to next method
                        if self.fallback_enabled and self.applescript.is_macos:
                            method = "applescript"
                        else:
                            return self._no_method_available_error()
                    else:
                        page = await self._get_cdp_page()

                        # Determine locator strategy and get element
                        element = None
                        if selector:
                            element = await page.query_selector(selector)
                        elif xpath:
                            element = await page.query_selector(f"xpath={xpath}")
                        elif text:
                            element = (
                                await page.get_by_text(text).nth(index).element_handle()
                            )
                        else:
                            return {
                                "success": False,
                                "error": "Must provide selector, xpath, or text",
                                "method": "cdp",
                                "data": None,
                            }

                        if not element:
                            return {
                                "success": False,
                                "error": "Element not found",
                                "method": "cdp",
                                "data": None,
                            }

                        # Extract element information
                        text_content = await element.text_content()
                        return {
                            "success": True,
                            "error": None,
                            "method": "cdp",
                            "data": {"text": text_content or ""},
                        }
                else:
                    page = await self._get_cdp_page()

                    # Determine locator strategy and get element
                    element = None
                    if selector:
                        element = await page.query_selector(selector)
                    elif xpath:
                        element = await page.query_selector(f"xpath={xpath}")
                    elif text:
                        element = (
                            await page.get_by_text(text).nth(index).element_handle()
                        )
                    else:
                        return {
                            "success": False,
                            "error": "Must provide selector, xpath, or text",
                            "method": "cdp",
                            "data": None,
                        }

                    if not element:
                        return {
                            "success": False,
                            "error": "Element not found",
                            "method": "cdp",
                            "data": None,
                        }

                    # Extract element information
                    text_content = await element.text_content()
                    return {
                        "success": True,
                        "error": None,
                        "method": "cdp",
                        "data": {"text": text_content or ""},
                    }

            except Exception as e:
                logger.error(f"CDP get_element failed: {e}")
                # Fall through to AppleScript
                if self.fallback_enabled and self.applescript.is_macos:
                    method = "applescript"
                else:
                    return {
                        "success": False,
                        "error": f"CDP get_element failed: {str(e)}",
                        "method": "cdp",
                        "data": None,
                    }

        if method == "applescript":
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
            # Would need to add this to DOMInteractionService
            return {
                "success": False,
                "error": "JavaScript execution not yet supported via extension",
                "method": "extension",
                "data": None,
            }

        elif method == "cdp":
            try:
                if not await self._has_cdp_connection():
                    if not await self.init_cdp():
                        # Fall through to next method
                        if self.fallback_enabled and self.applescript.is_macos:
                            method = "applescript"
                        else:
                            return self._no_method_available_error()
                    else:
                        page = await self._get_cdp_page()
                        result = await page.evaluate(script)
                        return {
                            "success": True,
                            "error": None,
                            "method": "cdp",
                            "data": result,
                        }
                else:
                    page = await self._get_cdp_page()
                    result = await page.evaluate(script)
                    return {
                        "success": True,
                        "error": None,
                        "method": "cdp",
                        "data": result,
                    }

            except Exception as e:
                logger.error(f"CDP execute_javascript failed: {e}")
                # Fall through to AppleScript
                if self.fallback_enabled and self.applescript.is_macos:
                    method = "applescript"
                else:
                    return {
                        "success": False,
                        "error": f"CDP execute_javascript failed: {str(e)}",
                        "method": "cdp",
                        "data": None,
                    }

        if method == "applescript":
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
        # If no websocket service available, extension cannot be connected
        if not self.websocket:
            logger.info(f"_has_extension_connection({port}): No websocket service")
            return False

        try:
            # Try exact port match first
            connection = await self.browser_service.browser_state.get_connection(port)
            logger.info(f"_has_extension_connection({port}): Exact match = {connection is not None}")

            # If no exact match and port is in server range, try any active connection
            if connection is None and 8851 <= port <= 8895:
                connection = await self.browser_service.browser_state.get_any_active_connection()
                logger.info(f"_has_extension_connection({port}): Fallback match = {connection is not None}")
                if connection:
                    logger.info(f"_has_extension_connection({port}): Found active connection on port {connection.port}, is_active={connection.is_active}")

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
            "extension", "cdp", "applescript", or "none"

        Decision Logic:
        1. mode="extension": return "extension" (fail if unavailable)
        2. mode="cdp": return "cdp" (fail if unavailable)
        3. mode="applescript": return "applescript"
        4. mode="auto": check extension → CDP → AppleScript availability
        """
        if self.mode == "extension":
            return "extension"

        if self.mode == "cdp":
            return "cdp"

        if self.mode == "applescript":
            return "applescript"

        # Auto mode: check availability in order
        # Note: Can't use async here, so we use heuristics

        # 1. Extension (if port provided)
        if port:
            return "extension"

        # 2. CDP (if enabled and likely available)
        if self.cdp_enabled and self.cdp_browser:
            return "cdp"

        # 3. AppleScript (if macOS and fallback enabled)
        if self.fallback_enabled and self.applescript.is_macos:
            return "applescript"

        return "none"

    def _no_method_available_error(self) -> Dict[str, Any]:
        """Return error when no control method is available.

        Returns:
            Error response dictionary
        """
        error_parts = ["No browser control method available."]

        if not PLAYWRIGHT_AVAILABLE:
            error_parts.append(
                "Install Playwright for CDP support: pip install playwright && playwright install"
            )

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
