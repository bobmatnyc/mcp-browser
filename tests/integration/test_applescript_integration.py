"""Integration tests for AppleScript fallback functionality.

These tests verify the AppleScript fallback integration works correctly.
Run on macOS only.
"""

import platform

import pytest

# Skip all tests if not on macOS
pytestmark = pytest.mark.skipif(
    platform.system() != "Darwin", reason="AppleScript tests only run on macOS"
)


class TestAppleScriptServiceBasics:
    """Test AppleScript service basic functionality."""

    def test_applescript_service_import(self):
        """Test that AppleScript service can be imported."""
        from src.services.applescript_service import AppleScriptService

        service = AppleScriptService()
        assert service is not None
        assert service.is_macos is True

    @pytest.mark.asyncio
    async def test_check_browser_availability_safari(self):
        """Test Safari availability checking."""
        from src.services.applescript_service import AppleScriptService

        service = AppleScriptService()
        result = await service.check_browser_availability("Safari")

        # Should return valid structure
        assert "available" in result
        assert "installed" in result
        assert "applescript_enabled" in result
        assert "message" in result

        # If Safari is not running, should indicate that
        if not result["installed"]:
            assert "not running" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_applescript_basic(self):
        """Test basic AppleScript execution."""
        from src.services.applescript_service import AppleScriptService

        service = AppleScriptService()

        # Test simple AppleScript command
        script = 'tell application "System Events" to return "test"'
        result = await service._execute_applescript(script)

        assert result is not None
        assert "success" in result
        assert "output" in result


class TestBrowserControllerIntegration:
    """Test BrowserController integration with AppleScript."""

    def test_browser_controller_import(self):
        """Test that BrowserController can be imported."""
        from src.services.browser_controller import BrowserController

        # Create with minimal dependencies
        controller = BrowserController(
            websocket_service=None,  # Not needed for AppleScript mode
            browser_service=None,
            applescript_service=None,
            config={"browser_control": {"mode": "auto"}},
        )

        assert controller is not None
        assert controller.mode == "auto"

    def test_browser_controller_mode_validation(self):
        """Test mode validation in BrowserController."""
        from src.services.browser_controller import BrowserController

        # Invalid mode should fall back to "auto"
        controller = BrowserController(
            websocket_service=None,
            browser_service=None,
            applescript_service=None,
            config={"browser_control": {"mode": "invalid_mode"}},
        )

        assert controller.mode == "auto"

    def test_select_browser_method_applescript(self):
        """Test browser method selection logic."""
        from src.services.applescript_service import AppleScriptService
        from src.services.browser_controller import BrowserController

        applescript = AppleScriptService()

        controller = BrowserController(
            websocket_service=None,
            browser_service=None,
            applescript_service=applescript,
            config={
                "browser_control": {"mode": "applescript", "fallback_enabled": True}
            },
        )

        # In applescript mode, should return "applescript"
        method = controller._select_browser_method(port=None)
        assert method == "applescript"

    def test_select_browser_method_extension(self):
        """Test extension-only mode selection."""
        from src.services.browser_controller import BrowserController

        controller = BrowserController(
            websocket_service=None,
            browser_service=None,
            applescript_service=None,
            config={"browser_control": {"mode": "extension"}},
        )

        method = controller._select_browser_method(port=8875)
        assert method == "extension"


class TestServiceContainerIntegration:
    """Test service container properly registers services."""

    @pytest.mark.asyncio
    async def test_applescript_service_registration(self):
        """Test that AppleScript service is registered correctly."""
        from src.container.service_container import ServiceContainer
        from src.services.applescript_service import AppleScriptService

        container = ServiceContainer()

        # Register AppleScript service
        container.register("applescript_service", lambda c: AppleScriptService())

        # Should be able to retrieve it
        service = await container.get("applescript_service")
        assert service is not None
        assert isinstance(service, AppleScriptService)

    @pytest.mark.asyncio
    async def test_browser_controller_registration(self):
        """Test BrowserController registration with dependencies."""
        from src.container.service_container import ServiceContainer
        from src.services.applescript_service import AppleScriptService
        from src.services.browser_controller import BrowserController

        container = ServiceContainer()

        # Register AppleScript service
        container.register("applescript_service", lambda c: AppleScriptService())

        # Register BrowserController
        async def create_browser_controller(c):
            applescript = await c.get("applescript_service")
            return BrowserController(
                websocket_service=None,
                browser_service=None,
                applescript_service=applescript,
                config={"browser_control": {"mode": "auto"}},
            )

        container.register("browser_controller", create_browser_controller)

        # Should be able to retrieve it
        controller = await container.get("browser_controller")
        assert controller is not None
        assert isinstance(controller, BrowserController)


class TestConfigurationHandling:
    """Test configuration handling for browser control."""

    def test_default_configuration(self):
        """Test default browser control configuration."""
        from src.services.browser_controller import BrowserController

        controller = BrowserController(
            websocket_service=None,
            browser_service=None,
            applescript_service=None,
            config={},  # No config
        )

        # Should have defaults
        assert controller.mode == "auto"
        assert controller.fallback_enabled is True

    def test_custom_configuration(self):
        """Test custom browser control configuration."""
        from src.services.applescript_service import AppleScriptService
        from src.services.browser_controller import BrowserController

        applescript = AppleScriptService()

        config = {
            "browser_control": {
                "mode": "applescript",
                "applescript_browser": "Google Chrome",
                "fallback_enabled": True,
                "prompt_for_permissions": True,
            }
        }

        controller = BrowserController(
            websocket_service=None,
            browser_service=None,
            applescript_service=applescript,
            config=config,
        )

        assert controller.mode == "applescript"
        assert controller.preferred_browser == "Google Chrome"
        assert controller.fallback_enabled is True
        assert controller.prompt_for_permissions is True


class TestErrorHandling:
    """Test error handling and messaging."""

    @pytest.mark.asyncio
    async def test_no_browser_running_error(self):
        """Test error when browser is not running."""
        from src.services.applescript_service import AppleScriptService

        service = AppleScriptService()

        # Navigate should fail gracefully if browser not running
        result = await service.navigate("https://example.com", browser="Safari")

        # Should return error structure
        assert "success" in result
        assert "error" in result

        # If Safari not running, success should be False
        # (unless Safari happens to be running during test)

    def test_permission_instructions_generation(self):
        """Test that permission instructions are generated correctly."""
        from src.services.applescript_service import AppleScriptService

        service = AppleScriptService()
        instructions = service._get_permission_instructions("Safari")

        # Should contain key information
        assert "System Settings" in instructions
        assert "Automation" in instructions
        assert "Safari" in instructions
        assert "mcp-browser quickstart" in instructions

    @pytest.mark.asyncio
    async def test_browser_controller_fallback_error(self):
        """Test BrowserController error when no method available."""
        from src.services.browser_controller import BrowserController

        # Create controller with no websocket and no AppleScript (simulate non-macOS)
        controller = BrowserController(
            websocket_service=None,
            browser_service=None,
            applescript_service=None,  # No AppleScript
            config={"browser_control": {"mode": "auto"}},
        )

        # Should return error
        result = controller._no_method_available_error()
        assert result["success"] is False
        assert "error" in result
        assert "Install extension" in result["error"]


# Manual testing guidance for features requiring live browser
class ManualTestingGuide:
    """
    MANUAL TESTING GUIDE

    These tests require a live browser and should be run manually:

    1. Navigation Test:
       - Open Safari
       - Configure mode="applescript"
       - Run: mcp-browser start
       - Use MCP tool: browser_navigate(port=8875, url="https://example.com")
       - Expected: Safari navigates to example.com

    2. Click Test:
       - Navigate to a page with clickable elements
       - Use MCP tool: browser_click(port=8875, selector=".button")
       - Expected: Element is clicked

    3. Fill Form Test:
       - Navigate to a page with form fields
       - Use MCP tool: browser_fill_field(port=8875, selector="input", value="test")
       - Expected: Field is filled with "test"

    4. Permission Error Test:
       - Disable automation permissions in System Settings
       - Try navigation
       - Expected: Clear error message with setup instructions

    5. Fallback Test:
       - Disable/remove browser extension
       - Configure mode="auto"
       - Use browser_navigate
       - Expected: Automatic AppleScript fallback with notification
    """

    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
