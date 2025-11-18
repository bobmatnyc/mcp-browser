#!/usr/bin/env python3
"""Test script to verify the implementation works."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime

from src.container import ServiceContainer
from src.models import ConsoleLevel, ConsoleMessage
from src.services import (
    BrowserService,
    MCPService,
    ScreenshotService,
    StorageService,
    WebSocketService,
)


async def test_services():
    """Test that all services can be instantiated and basic operations work."""

    print("Testing mcp-browser Implementation\n" + "=" * 40)

    # Test 1: Service Container
    print("\n1. Testing Service Container...")
    container = ServiceContainer()
    container.register("test_service", lambda c: {"name": "test"})
    test_service = await container.get("test_service")
    assert test_service["name"] == "test"
    print("✓ Service Container works")

    # Test 2: Storage Service
    print("\n2. Testing Storage Service...")
    storage = StorageService()

    # Create a test message
    test_message = ConsoleMessage(
        timestamp=datetime.now(),
        level=ConsoleLevel.INFO,
        message="Test message",
        port=8875,
        url="http://example.com",
    )

    # Test JSONL conversion
    jsonl = test_message.to_jsonl()
    parsed = json.loads(jsonl)
    assert parsed["message"] == "Test message"
    assert parsed["level"] == "info"
    print("✓ Storage Service message serialization works")

    # Test 3: WebSocket Service
    print("\n3. Testing WebSocket Service...")
    ws_service = WebSocketService()

    # Test port range configuration
    assert ws_service.start_port == 8875
    assert ws_service.end_port == 8895
    print("✓ WebSocket Service configured correctly")

    # Test 4: Browser Service
    print("\n4. Testing Browser Service...")
    browser_service = BrowserService(storage_service=storage)

    # Test message handling setup
    assert browser_service.storage_service is not None
    assert browser_service._buffer_interval == 2.5
    print("✓ Browser Service initialized correctly")

    # Test 5: Screenshot Service
    print("\n5. Testing Screenshot Service...")
    screenshot_service = ScreenshotService()

    # Check initialization
    assert screenshot_service._browser is None  # Not started yet
    print("✓ Screenshot Service initialized correctly")

    # Test 6: MCP Service
    print("\n6. Testing MCP Service...")
    mcp_service = MCPService(
        browser_service=browser_service, screenshot_service=screenshot_service
    )

    # Check tool registration
    assert mcp_service.browser_service is not None
    assert mcp_service.screenshot_service is not None
    print("✓ MCP Service initialized with dependencies")

    # Test 7: Full Integration
    print("\n7. Testing Full Service Integration...")
    full_container = ServiceContainer()

    # Register all services
    full_container.register("storage_service", lambda c: StorageService())
    full_container.register("websocket_service", lambda c: WebSocketService())

    async def create_browser_service(c):
        storage = await c.get("storage_service")
        return BrowserService(storage_service=storage)

    full_container.register("browser_service", create_browser_service)
    full_container.register("screenshot_service", lambda c: ScreenshotService())

    async def create_mcp_service(c):
        browser = await c.get("browser_service")
        screenshot = await c.get("screenshot_service")
        return MCPService(browser_service=browser, screenshot_service=screenshot)

    full_container.register("mcp_service", create_mcp_service)

    # Get all services to verify dependency injection works
    storage = await full_container.get("storage_service")
    _ = await full_container.get("websocket_service")  # Verify registration
    browser = await full_container.get("browser_service")
    screenshot = await full_container.get("screenshot_service")
    mcp = await full_container.get("mcp_service")

    # Verify dependencies are properly injected
    assert browser.storage_service is storage
    assert mcp.browser_service is browser
    assert mcp.screenshot_service is screenshot

    print("✓ Full service integration works with dependency injection")

    print("\n" + "=" * 40)
    print("All tests passed! ✓")
    print("\nFile Statistics:")

    # Count lines in each service file
    service_files = [
        "src/services/storage_service.py",
        "src/services/websocket_service.py",
        "src/services/browser_service.py",
        "src/services/screenshot_service.py",
        "src/services/mcp_service.py",
        "src/container/service_container.py",
        "src/cli/main.py",
    ]

    total_lines = 0
    for file_path in service_files:
        path = Path(file_path)
        if path.exists():
            lines = len(path.read_text().splitlines())
            print(f"  {path.name}: {lines} lines")
            total_lines += lines
            if lines > 500:
                print("    ⚠️  Warning: File exceeds 500 line limit!")

    print(f"\nTotal Python lines: {total_lines}")

    # Check extension files exist
    print("\nExtension Files:")
    extension_files = [
        "extension/manifest.json",
        "extension/background.js",
        "extension/content.js",
        "extension/popup.html",
        "extension/popup.js",
    ]

    for file_path in extension_files:
        path = Path(file_path)
        exists = "✓" if path.exists() else "✗"
        print(f"  {exists} {path.name}")

    print("\n✅ Implementation complete and verified!")


if __name__ == "__main__":
    try:
        asyncio.run(test_services())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
