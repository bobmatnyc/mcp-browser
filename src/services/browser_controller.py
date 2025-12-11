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

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# CDP/Playwright imports - optional dependency
try:
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.debug("Playwright not available - CDP support disabled")


class BrowserController:
    """Unified browser control with automatic fallback.

    This service coordinates between browser extension (WebSocket), CDP
    (Playwright), and AppleScript fallback to provide seamless browser control.

    Features:
    - Automatic method selection (extension → CDP → AppleScript)
    - Configuration-driven mode selection ("auto", "extension", "cdp", "applescript")
    - Clear error messages when no control method available
    - Console log limitation communication (extension-only feature)

    Performance:
    - Extension: ~10-50ms per operation (WebSocket)
    - CDP: ~50-150ms per operation (Chrome DevTools Protocol)
    - AppleScript: ~100-500ms per operation (subprocess + interpreter)
    - Fallback check: ~10-50ms (WebSocket connection check)

    Usage:
        controller = BrowserController(websocket, browser, applescript, config)
        result = await controller.navigate("https://example.com", port=8875)
        # Automatically uses extension if available, falls back to CDP, then AppleScript
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

        # CDP configuration
        self.cdp_port = browser_control.get("cdp_port", 9222)
        self.cdp_enabled = browser_control.get("cdp_enabled", True) and PLAYWRIGHT_AVAILABLE

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

    async def navigate(self, url: str, port: Optional[int] = None) -> Dict[str, Any]:
        """Navigate browser to URL with automatic fallback.

        Args:
            url: URL to navigate to
            port: Optional port number for extension (None = use fallback)

        Returns:
            {"success": bool, "error": str, "method": str, "data": dict}

        Mode Selection Logic:
        1. If mode="extension": only try extension, fail if unavailable
        2. If mode="cdp": only try CDP, fail if unavailable
        3. If mode="applescript": only try AppleScript, fail if unavailable
        4. If mode="auto" (default): try extension → CDP → AppleScript

        Error Handling:
        - Extension unavailable → Falls back to CDP
        - CDP unavailable → Falls back to AppleScript (macOS)
        - All methods unavailable → Returns clear error
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

        # Mode: auto (try extension → CDP → AppleScript)
        if port and await self._has_extension_connection(port):
            # Use extension
            success = await self.browser_service.navigate_browser(port, url)
            return {
                "success": success,
                "error": None if success else "Navigation command failed",
                "method": "extension",
                "data": {"url": url, "port": port},
            }

        # Extension unavailable, try CDP
        if self.cdp_enabled:
            try:
                if not await self._has_cdp_connection():
                    await self.init_cdp()

                if await self._has_cdp_connection():
                    logger.info("Extension unavailable, using CDP")
                    page = await self._get_cdp_page()
                    await page.goto(url, wait_until="domcontentloaded")
                    return {
                        "success": True,
                        "error": None,
                        "method": "cdp",
                        "data": {"url": url, "cdp_port": self.cdp_port},
                    }
            except Exception as e:
                logger.debug(f"CDP navigation failed, trying AppleScript: {e}")

        # CDP unavailable, try AppleScript fallback
        if self.fallback_enabled and self.applescript.is_macos:
            logger.info("Extension and CDP unavailable, falling back to AppleScript")
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
        return self._no_method_available_error()

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
