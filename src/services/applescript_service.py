"""AppleScript-based browser control service for macOS fallback.

This service provides browser control via AppleScript when the browser extension
is unavailable. It supports Safari (preferred) and Chrome (fallback) on macOS.

Design Decision: AppleScript Fallback for macOS
------------------------------------------------
Rationale: When browser extension is unavailable (not installed, disconnected),
users on macOS can still perform basic browser control via AppleScript. This
provides graceful degradation for navigation, clicking, form filling, etc.

Trade-offs:
- Performance: AppleScript slower than extension (~100-500ms vs ~10-50ms)
- Features: Cannot read console logs (extension-only feature)
- Reliability: Requires macOS System Preferences automation permissions
- Compatibility: macOS-only (no Windows/Linux support)

Alternatives Considered:
1. CDP (Chrome DevTools Protocol): Rejected due to complex setup
2. Selenium: Rejected due to heavyweight dependency (ChromeDriver, etc.)
3. Playwright: Rejected due to large binary downloads (100MB+)

Extension Points: BrowserController interface allows future CDP/Playwright
integration if more advanced control needed (debugging, network inspection).
"""

import asyncio
import json
import logging
import platform
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AppleScriptService:
    """Browser control via AppleScript for macOS fallback.

    Features:
    - Platform detection (only activate on macOS)
    - Safari (preferred) and Chrome support
    - AppleScript permission checking
    - Clear error messages for permission issues

    Performance:
    - Time Complexity: O(1) for command execution (subprocess overhead ~100-500ms)
    - Space Complexity: O(1) auxiliary space

    Limitations:
    - Cannot read console logs (extension required)
    - Requires System Preferences automation permissions
    - macOS-only (returns clear errors on other platforms)
    """

    # AppleScript templates for different operations
    SAFARI_CHECK_SCRIPT = """
    tell application "System Events"
        return (exists process "Safari")
    end tell
    """

    CHROME_CHECK_SCRIPT = """
    tell application "System Events"
        return (exists process "Google Chrome")
    end tell
    """

    SAFARI_NAVIGATE_SCRIPT = """
    tell application "Safari"
        activate
        if (count of windows) = 0 then
            make new document
        end if
        set URL of current tab of window 1 to "{url}"
    end tell
    """

    CHROME_NAVIGATE_SCRIPT = """
    tell application "Google Chrome"
        activate
        if (count of windows) = 0 then
            make new window
        end if
        set URL of active tab of window 1 to "{url}"
    end tell
    """

    SAFARI_EXECUTE_JS_SCRIPT = """
    tell application "Safari"
        set jsResult to do JavaScript "{script}" in current tab of window 1
    end tell
    return jsResult
    """

    CHROME_EXECUTE_JS_SCRIPT = """
    tell application "Google Chrome"
        set jsResult to execute active tab of window 1 javascript "{script}"
    end tell
    return jsResult
    """

    SAFARI_GET_URL_SCRIPT = """
    tell application "Safari"
        return URL of current tab of window 1
    end tell
    """

    CHROME_GET_URL_SCRIPT = """
    tell application "Google Chrome"
        return URL of active tab of window 1
    end tell
    """

    def __init__(self):
        """Initialize AppleScript service with platform detection."""
        self.is_macos = platform.system() == "Darwin"
        self._permission_checked: Dict[str, bool] = {}

        if not self.is_macos:
            logger.info("AppleScript service disabled (not macOS)")

    async def check_browser_availability(
        self, browser: str = "Safari"
    ) -> Dict[str, Any]:
        """Check if browser is installed and has AppleScript enabled.

        Args:
            browser: Browser name ("Safari" or "Google Chrome")

        Returns:
            {
                "available": bool,
                "installed": bool,
                "applescript_enabled": bool,
                "message": str  # User-facing message if disabled
            }

        Error Cases:
        - Not macOS: Returns unavailable with platform error
        - Browser not running: Returns installed=False
        - Permission denied: Returns applescript_enabled=False with instructions
        """
        if not self.is_macos:
            return {
                "available": False,
                "installed": False,
                "applescript_enabled": False,
                "message": (
                    "AppleScript browser control is only available on macOS. "
                    "Install the browser extension for full functionality: mcp-browser quickstart"
                ),
            }

        # Check if browser is installed (process running check)
        check_script = (
            self.SAFARI_CHECK_SCRIPT
            if browser == "Safari"
            else self.CHROME_CHECK_SCRIPT
        )

        try:
            result = await self._execute_applescript(check_script)
            is_running = (
                result.get("success") and result.get("output", "").strip() == "true"
            )

            if not is_running:
                return {
                    "available": False,
                    "installed": False,
                    "applescript_enabled": False,
                    "message": f"{browser} is not running. Please launch {browser} first.",
                }

            # Try to execute a simple operation to check permissions
            url_script = (
                self.SAFARI_GET_URL_SCRIPT
                if browser == "Safari"
                else self.CHROME_GET_URL_SCRIPT
            )

            permission_result = await self._execute_applescript(url_script)

            if not permission_result.get("success"):
                error_msg = permission_result.get("error", "")

                # Check for permission errors
                if (
                    "not allowed" in error_msg.lower()
                    or "not authorized" in error_msg.lower()
                ):
                    return {
                        "available": False,
                        "installed": True,
                        "applescript_enabled": False,
                        "message": self._get_permission_instructions(browser),
                    }

            # Browser is available and has permissions
            self._permission_checked[browser] = True
            return {
                "available": True,
                "installed": True,
                "applescript_enabled": True,
                "message": f"{browser} is available for AppleScript control",
            }

        except Exception as e:
            logger.error(f"Error checking browser availability: {e}")
            return {
                "available": False,
                "installed": False,
                "applescript_enabled": False,
                "message": f"Error checking {browser} availability: {str(e)}",
            }

    def _get_permission_instructions(self, browser: str) -> str:
        """Get user-facing instructions for enabling AppleScript permissions.

        Args:
            browser: Browser name

        Returns:
            Formatted instructions for enabling automation permissions
        """
        return f"""
{browser} does not have UI scripting enabled. To enable:

1. Open System Settings > Privacy & Security > Automation
2. Enable permissions for your terminal app (Terminal, iTerm2, etc.) to control {browser}
3. If 'mcp-browser' appears in the list, enable it
4. Restart {browser}

Alternatively, install the browser extension for full functionality:
   mcp-browser quickstart

Note: Console log capture requires the browser extension.
        """.strip()

    async def navigate(self, url: str, browser: str = "Safari") -> Dict[str, Any]:
        """Navigate browser to URL.

        Args:
            url: URL to navigate to
            browser: Browser name ("Safari" or "Google Chrome")

        Returns:
            {"success": bool, "error": str, "data": dict}

        Performance:
            - Expected: 200-500ms (AppleScript execution overhead)
            - Bottleneck: Subprocess spawn and AppleScript interpreter
        """
        if not self.is_macos:
            return {
                "success": False,
                "error": "AppleScript is only available on macOS",
                "data": None,
            }

        # Check browser availability first
        availability = await self.check_browser_availability(browser)
        if not availability["available"]:
            return {
                "success": False,
                "error": availability["message"],
                "data": None,
            }

        # Select navigation script
        script = (
            self.SAFARI_NAVIGATE_SCRIPT.format(url=url)
            if browser == "Safari"
            else self.CHROME_NAVIGATE_SCRIPT.format(url=url)
        )

        result = await self._execute_applescript(script)

        if result["success"]:
            logger.info(f"Navigated {browser} to {url} via AppleScript")
            return {
                "success": True,
                "error": None,
                "data": {"url": url, "browser": browser},
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "data": None,
            }

    async def execute_javascript(
        self, script: str, browser: str = "Safari"
    ) -> Dict[str, Any]:
        """Execute JavaScript in current tab.

        Args:
            script: JavaScript code to execute
            browser: Browser name ("Safari" or "Google Chrome")

        Returns:
            {"success": bool, "error": str, "data": Any}

        Example:
            >>> result = await service.execute_javascript(
            ...     "document.querySelector('.btn').click()",
            ...     browser="Safari"
            ... )
            >>> result["success"]
            True
        """
        if not self.is_macos:
            return {
                "success": False,
                "error": "AppleScript is only available on macOS",
                "data": None,
            }

        # Check browser availability
        availability = await self.check_browser_availability(browser)
        if not availability["available"]:
            return {
                "success": False,
                "error": availability["message"],
                "data": None,
            }

        # Escape JavaScript for AppleScript string (escape quotes and backslashes)
        escaped_script = script.replace("\\", "\\\\").replace('"', '\\"')

        # Select execution script
        applescript = (
            self.SAFARI_EXECUTE_JS_SCRIPT.format(script=escaped_script)
            if browser == "Safari"
            else self.CHROME_EXECUTE_JS_SCRIPT.format(script=escaped_script)
        )

        result = await self._execute_applescript(applescript)

        if result["success"]:
            return {
                "success": True,
                "error": None,
                "data": result.get("output", ""),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "data": None,
            }

    async def get_current_url(self, browser: str = "Safari") -> str:
        """Get current tab URL.

        Args:
            browser: Browser name ("Safari" or "Google Chrome")

        Returns:
            Current URL or empty string on error
        """
        if not self.is_macos:
            return ""

        # Check browser availability
        availability = await self.check_browser_availability(browser)
        if not availability["available"]:
            return ""

        # Select URL script
        script = (
            self.SAFARI_GET_URL_SCRIPT
            if browser == "Safari"
            else self.CHROME_GET_URL_SCRIPT
        )

        result = await self._execute_applescript(script)

        if result["success"]:
            return result.get("output", "").strip()
        return ""

    async def click(self, selector: str, browser: str = "Safari") -> Dict[str, Any]:
        """Click element via JavaScript injection.

        Args:
            selector: CSS selector for element
            browser: Browser name

        Returns:
            {"success": bool, "error": str, "data": dict}
        """
        # JavaScript to click element with error handling
        js_code = f"""
        (function() {{
            try {{
                const el = document.querySelector('{selector}');
                if (!el) {{
                    return JSON.stringify({{
                        success: false,
                        error: 'Element not found: {selector}'
                    }});
                }}
                el.click();
                return JSON.stringify({{
                    success: true,
                    element: {{
                        tagName: el.tagName,
                        id: el.id,
                        className: el.className
                    }}
                }});
            }} catch(e) {{
                return JSON.stringify({{
                    success: false,
                    error: 'Error: ' + e.message
                }});
            }}
        }})();
        """

        result = await self.execute_javascript(js_code, browser)

        if not result["success"]:
            return result

        # Parse JSON response from JavaScript
        try:
            js_result = json.loads(result["data"])
            return {
                "success": js_result.get("success", False),
                "error": js_result.get("error"),
                "data": js_result.get("element"),
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse JavaScript result",
                "data": None,
            }

    async def fill_field(
        self, selector: str, value: str, browser: str = "Safari"
    ) -> Dict[str, Any]:
        """Fill form field via JavaScript.

        Args:
            selector: CSS selector for input field
            value: Value to fill
            browser: Browser name

        Returns:
            {"success": bool, "error": str, "data": dict}
        """
        # Escape value for JavaScript
        escaped_value = (
            value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
        )

        js_code = f"""
        (function() {{
            try {{
                const el = document.querySelector('{selector}');
                if (!el) {{
                    return JSON.stringify({{
                        success: false,
                        error: 'Element not found: {selector}'
                    }});
                }}
                el.value = '{escaped_value}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return JSON.stringify({{
                    success: true,
                    element: {{
                        tagName: el.tagName,
                        value: el.value
                    }}
                }});
            }} catch(e) {{
                return JSON.stringify({{
                    success: false,
                    error: 'Error: ' + e.message
                }});
            }}
        }})();
        """

        result = await self.execute_javascript(js_code, browser)

        if not result["success"]:
            return result

        # Parse JSON response
        try:
            js_result = json.loads(result["data"])
            return {
                "success": js_result.get("success", False),
                "error": js_result.get("error"),
                "data": js_result.get("element"),
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse JavaScript result",
                "data": None,
            }

    async def get_element(
        self, selector: str, browser: str = "Safari"
    ) -> Dict[str, Any]:
        """Get element information via JavaScript.

        Args:
            selector: CSS selector for element
            browser: Browser name

        Returns:
            {"success": bool, "error": str, "data": dict}
        """
        js_code = f"""
        (function() {{
            try {{
                const el = document.querySelector('{selector}');
                if (!el) {{
                    return JSON.stringify({{
                        success: false,
                        error: 'Element not found: {selector}'
                    }});
                }}
                return JSON.stringify({{
                    success: true,
                    element: {{
                        tagName: el.tagName,
                        id: el.id,
                        className: el.className,
                        text: el.textContent.substring(0, 100),
                        value: el.value || '',
                        attributes: {{
                            href: el.getAttribute('href'),
                            src: el.getAttribute('src'),
                            type: el.getAttribute('type')
                        }}
                    }}
                }});
            }} catch(e) {{
                return JSON.stringify({{
                    success: false,
                    error: 'Error: ' + e.message
                }});
            }}
        }})();
        """

        result = await self.execute_javascript(js_code, browser)

        if not result["success"]:
            return result

        # Parse JSON response
        try:
            js_result = json.loads(result["data"])
            return {
                "success": js_result.get("success", False),
                "error": js_result.get("error"),
                "data": js_result.get("element"),
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse JavaScript result",
                "data": None,
            }

    async def _execute_applescript(self, script: str) -> Dict[str, Any]:
        """Execute AppleScript and return result.

        Args:
            script: AppleScript code to execute

        Returns:
            {"success": bool, "output": str, "error": str}

        Performance:
            - Subprocess spawn: ~50-100ms
            - AppleScript execution: ~50-400ms depending on operation
            - Total: ~100-500ms per command
        """
        try:
            # Run osascript with timeout
            process = await asyncio.create_subprocess_exec(
                "osascript",
                "-e",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=10.0
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "output": "",
                    "error": "AppleScript execution timed out after 10 seconds",
                }

            # Check return code
            if process.returncode == 0:
                return {
                    "success": True,
                    "output": stdout.decode("utf-8"),
                    "error": None,
                }
            else:
                error_output = stderr.decode("utf-8")
                logger.warning(f"AppleScript error: {error_output}")
                return {
                    "success": False,
                    "output": "",
                    "error": error_output,
                }

        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "error": "osascript command not found (not macOS?)",
            }
        except Exception as e:
            logger.error(f"Error executing AppleScript: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
            }
