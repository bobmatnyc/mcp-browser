"""Tests for AppleScriptService.

Test Coverage:
- Platform detection (macOS vs other platforms)
- Safari availability and permission checking
- Chrome availability and permission checking
- Navigation commands
- JavaScript execution
- Click operations
- Fill field operations
- Get element operations
- Permission error handling
- AppleScript execution with timeout
"""

import asyncio
import platform
import sys
from unittest.mock import AsyncMock, patch

import pytest

from src.services.applescript_service import AppleScriptService


@pytest.fixture
def applescript_service():
    """Create AppleScriptService instance for testing."""
    return AppleScriptService()


class TestPlatformDetection:
    """Test platform detection and availability."""

    def test_macos_detection(self, applescript_service):
        """Should detect macOS platform correctly."""
        if platform.system() == "Darwin":
            assert applescript_service.is_macos is True
        else:
            assert applescript_service.is_macos is False

    @pytest.mark.asyncio
    async def test_non_macos_unavailable(self):
        """Should return unavailable on non-macOS platforms."""
        with patch("platform.system", return_value="Linux"):
            service = AppleScriptService()
            result = await service.check_browser_availability("Safari")

            assert result["available"] is False
            assert result["installed"] is False
            assert result["applescript_enabled"] is False
            assert "macOS" in result["message"]
            assert "extension" in result["message"]


class TestBrowserAvailability:
    """Test browser availability checking."""

    @pytest.mark.asyncio
    async def test_safari_not_running(self, applescript_service):
        """Should detect when Safari is not running."""

        # Mock AppleScript execution to return false (not running)
        async def mock_execute(script):
            return {"success": True, "output": "false", "error": None}

        with patch.object(
            applescript_service, "_execute_applescript", side_effect=mock_execute
        ):
            result = await applescript_service.check_browser_availability("Safari")

            assert result["available"] is False
            assert result["installed"] is False
            assert "not running" in result["message"]

    @pytest.mark.asyncio
    async def test_safari_permission_denied(self, applescript_service):
        """Should detect permission errors and provide instructions."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock AppleScript execution:
        # 1. First call (check running): returns true
        # 2. Second call (get URL): returns permission error
        call_count = 0

        async def mock_execute(script):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"success": True, "output": "true", "error": None}
            else:
                return {
                    "success": False,
                    "output": "",
                    "error": "Safari is not allowed assistive access",
                }

        with patch.object(
            applescript_service, "_execute_applescript", side_effect=mock_execute
        ):
            result = await applescript_service.check_browser_availability("Safari")

            assert result["available"] is False
            assert result["installed"] is True
            assert result["applescript_enabled"] is False
            assert "System Settings" in result["message"]
            assert "Automation" in result["message"]

    @pytest.mark.asyncio
    async def test_safari_available(self, applescript_service):
        """Should detect when Safari is available with permissions."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock successful AppleScript execution
        async def mock_execute(script):
            if "System Events" in script:
                return {"success": True, "output": "true", "error": None}
            else:
                return {"success": True, "output": "https://example.com", "error": None}

        with patch.object(
            applescript_service, "_execute_applescript", side_effect=mock_execute
        ):
            result = await applescript_service.check_browser_availability("Safari")

            assert result["available"] is True
            assert result["installed"] is True
            assert result["applescript_enabled"] is True
            assert applescript_service._permission_checked["Safari"] is True


class TestNavigation:
    """Test browser navigation."""

    @pytest.mark.asyncio
    async def test_navigate_non_macos(self):
        """Should fail gracefully on non-macOS."""
        with patch("platform.system", return_value="Windows"):
            service = AppleScriptService()
            result = await service.navigate("https://example.com", "Safari")

            assert result["success"] is False
            assert "macOS" in result["error"]

    @pytest.mark.asyncio
    async def test_navigate_safari_success(self, applescript_service):
        """Should navigate Safari successfully."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock availability check and navigation
        async def mock_check(browser):
            return {
                "available": True,
                "installed": True,
                "applescript_enabled": True,
                "message": "OK",
            }

        async def mock_execute(script):
            return {"success": True, "output": "", "error": None}

        with patch.object(
            applescript_service, "check_browser_availability", side_effect=mock_check
        ):
            with patch.object(
                applescript_service, "_execute_applescript", side_effect=mock_execute
            ):
                result = await applescript_service.navigate(
                    "https://example.com", "Safari"
                )

                assert result["success"] is True
                assert result["data"]["url"] == "https://example.com"
                assert result["data"]["browser"] == "Safari"

    @pytest.mark.asyncio
    async def test_navigate_browser_unavailable(self, applescript_service):
        """Should fail when browser is unavailable."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock unavailable browser
        async def mock_check(browser):
            return {
                "available": False,
                "installed": False,
                "applescript_enabled": False,
                "message": "Browser not running",
            }

        with patch.object(
            applescript_service, "check_browser_availability", side_effect=mock_check
        ):
            result = await applescript_service.navigate("https://example.com", "Safari")

            assert result["success"] is False
            assert "not running" in result["error"]


class TestJavaScriptExecution:
    """Test JavaScript execution via AppleScript."""

    @pytest.mark.asyncio
    async def test_execute_javascript_success(self, applescript_service):
        """Should execute JavaScript and return result."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock availability and execution
        async def mock_check(browser):
            return {
                "available": True,
                "installed": True,
                "applescript_enabled": True,
                "message": "OK",
            }

        async def mock_execute(script):
            return {"success": True, "output": "test result", "error": None}

        with patch.object(
            applescript_service, "check_browser_availability", side_effect=mock_check
        ):
            with patch.object(
                applescript_service, "_execute_applescript", side_effect=mock_execute
            ):
                result = await applescript_service.execute_javascript(
                    "document.querySelector('.test').click()", "Safari"
                )

                assert result["success"] is True
                assert result["data"] == "test result"

    @pytest.mark.asyncio
    async def test_execute_javascript_escaping(self, applescript_service):
        """Should properly escape JavaScript for AppleScript."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock availability
        async def mock_check(browser):
            return {
                "available": True,
                "installed": True,
                "applescript_enabled": True,
                "message": "OK",
            }

        executed_script = None

        async def mock_execute(script):
            nonlocal executed_script
            executed_script = script
            return {"success": True, "output": "ok", "error": None}

        with patch.object(
            applescript_service, "check_browser_availability", side_effect=mock_check
        ):
            with patch.object(
                applescript_service, "_execute_applescript", side_effect=mock_execute
            ):
                # Test with quotes and backslashes
                js_code = "alert(\"Hello 'world'\");"
                await applescript_service.execute_javascript(js_code, "Safari")

                # Verify escaping occurred
                assert executed_script is not None
                assert '\\"' in executed_script  # Quotes should be escaped


class TestClickOperation:
    """Test element click operations."""

    @pytest.mark.asyncio
    async def test_click_success(self, applescript_service):
        """Should click element successfully."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock successful JavaScript execution
        async def mock_execute_js(script, browser):
            return {
                "success": True,
                "data": '{"success": true, "element": {"tagName": "BUTTON", "id": "btn1"}}',
                "error": None,
            }

        with patch.object(
            applescript_service, "execute_javascript", side_effect=mock_execute_js
        ):
            result = await applescript_service.click(".test-button", "Safari")

            assert result["success"] is True
            assert result["data"]["tagName"] == "BUTTON"

    @pytest.mark.asyncio
    async def test_click_element_not_found(self, applescript_service):
        """Should handle element not found error."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock JavaScript execution returning element not found
        async def mock_execute_js(script, browser):
            return {
                "success": True,
                "data": '{"success": false, "error": "Element not found: .missing"}',
                "error": None,
            }

        with patch.object(
            applescript_service, "execute_javascript", side_effect=mock_execute_js
        ):
            result = await applescript_service.click(".missing", "Safari")

            assert result["success"] is False
            assert "not found" in result["error"]


class TestFillField:
    """Test form field filling."""

    @pytest.mark.asyncio
    async def test_fill_field_success(self, applescript_service):
        """Should fill form field successfully."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock successful JavaScript execution
        async def mock_execute_js(script, browser):
            return {
                "success": True,
                "data": '{"success": true, "element": {"tagName": "INPUT", "value": "test value"}}',
                "error": None,
            }

        with patch.object(
            applescript_service, "execute_javascript", side_effect=mock_execute_js
        ):
            result = await applescript_service.fill_field(
                "#email", "test@example.com", "Safari"
            )

            assert result["success"] is True
            assert result["data"]["tagName"] == "INPUT"

    @pytest.mark.asyncio
    async def test_fill_field_value_escaping(self, applescript_service):
        """Should properly escape special characters in values."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        executed_js = None

        async def mock_execute_js(script, browser):
            nonlocal executed_js
            executed_js = script
            return {
                "success": True,
                "data": '{"success": true, "element": {"tagName": "INPUT"}}',
                "error": None,
            }

        with patch.object(
            applescript_service, "execute_javascript", side_effect=mock_execute_js
        ):
            # Test with special characters
            await applescript_service.fill_field(
                "#input", "Value with 'quotes'", "Safari"
            )

            # Verify escaping occurred in the JavaScript
            assert executed_js is not None
            assert "\\'" in executed_js


class TestGetElement:
    """Test element information retrieval."""

    @pytest.mark.asyncio
    async def test_get_element_success(self, applescript_service):
        """Should retrieve element information successfully."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock successful JavaScript execution
        element_info = {
            "success": True,
            "element": {
                "tagName": "A",
                "id": "link1",
                "className": "nav-link",
                "text": "Home",
                "value": "",
                "attributes": {"href": "/home", "src": None, "type": None},
            },
        }

        async def mock_execute_js(script, browser):
            import json

            return {"success": True, "data": json.dumps(element_info), "error": None}

        with patch.object(
            applescript_service, "execute_javascript", side_effect=mock_execute_js
        ):
            result = await applescript_service.get_element(".nav-link", "Safari")

            assert result["success"] is True
            assert result["data"]["tagName"] == "A"
            assert result["data"]["attributes"]["href"] == "/home"


class TestAppleScriptExecution:
    """Test low-level AppleScript execution."""

    @pytest.mark.asyncio
    async def test_execute_applescript_success(self, applescript_service):
        """Should execute AppleScript successfully."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"success output", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await applescript_service._execute_applescript('return "test"')

            assert result["success"] is True
            assert result["output"] == "success output"
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_execute_applescript_error(self, applescript_service):
        """Should handle AppleScript errors."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock subprocess with error
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"", b"execution error"))
        mock_process.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await applescript_service._execute_applescript("invalid script")

            assert result["success"] is False
            assert "error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_applescript_timeout(self, applescript_service):
        """Should handle execution timeout."""
        if not applescript_service.is_macos:
            pytest.skip("macOS only test")

        # Mock subprocess that times out
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
        mock_process.kill = AsyncMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await applescript_service._execute_applescript(
                "long running script"
            )

            assert result["success"] is False
            assert "timed out" in result["error"]
            mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_applescript_not_found(self, applescript_service):
        """Should handle osascript command not found."""
        # Mock osascript not found
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("osascript not found"),
        ):
            result = await applescript_service._execute_applescript("test")

            assert result["success"] is False
            assert "osascript" in result["error"]


class TestPermissionInstructions:
    """Test permission instruction messages."""

    def test_safari_permission_instructions(self, applescript_service):
        """Should provide clear Safari permission instructions."""
        instructions = applescript_service._get_permission_instructions("Safari")

        assert "System Settings" in instructions
        assert "Automation" in instructions
        assert "Safari" in instructions
        assert "mcp-browser quickstart" in instructions

    def test_chrome_permission_instructions(self, applescript_service):
        """Should provide clear Chrome permission instructions."""
        instructions = applescript_service._get_permission_instructions("Google Chrome")

        assert "System Settings" in instructions
        assert "Automation" in instructions
        assert "Google Chrome" in instructions


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only integration test")
class TestIntegrationMacOS:
    """Integration tests on real macOS system (requires Safari/Chrome running)."""

    @pytest.mark.asyncio
    async def test_real_safari_availability(self):
        """Test real Safari availability check (requires Safari to be installed)."""
        service = AppleScriptService()
        result = await service.check_browser_availability("Safari")

        # Should at least detect if Safari is installed (it always is on macOS)
        assert isinstance(result, dict)
        assert "available" in result
        assert "installed" in result
        assert "message" in result
