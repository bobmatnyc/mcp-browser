#!/usr/bin/env python3
"""
Example of using MCP Browser programmatically.

This script demonstrates how to:
1. Start the MCP Browser server
2. Connect to it programmatically
3. Query console logs
4. Navigate the browser
5. Take screenshots
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path to import mcp_browser
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli.main import BrowserMCPServer
from src.services.browser_service import BrowserService


async def example_usage():
    """Example of using MCP Browser programmatically."""

    # 1. Create custom configuration
    config = {
        'storage': {
            'base_path': '/tmp/mcp-browser-example',
            'max_file_size_mb': 10,
            'retention_days': 1
        },
        'websocket': {
            'port_range': [8890, 8895],
            'host': 'localhost'
        },
        'logging': {
            'level': 'DEBUG'
        }
    }

    # 2. Create and start server
    print("Starting MCP Browser server...")
    server = BrowserMCPServer(config=config)

    # Start server in background
    server_task = asyncio.create_task(server.start())

    # Wait a bit for server to start
    await asyncio.sleep(2)

    print(f"Server started on port {server.websocket_port}")

    # 3. Get services from container
    browser_service = await server.container.get('browser_service')
    screenshot_service = await server.container.get('screenshot_service')

    # 4. Wait for browser connection
    print("\nWaiting for browser connection...")
    print("Please ensure the Chrome extension is installed and active.")

    # Poll for connection (in real usage, you'd have the extension already connected)
    max_wait = 30  # seconds
    for i in range(max_wait):
        stats = await browser_service.get_browser_stats()
        if stats['total_connections'] > 0:
            print("Browser connected!")
            break
        await asyncio.sleep(1)
        if i % 5 == 0:
            print(f"Still waiting... ({i}/{max_wait}s)")

    # 5. Query console logs
    print("\n--- Querying Console Logs ---")

    # Get recent logs
    logs = await browser_service.query_logs(limit=10)
    print(f"Found {len(logs)} recent log entries")

    for log in logs[:5]:  # Show first 5
        print(f"  [{log['level']}] {log['url']}: {log['message'][:50]}...")

    # Search for specific logs
    error_logs = await browser_service.query_logs(
        level='error',
        limit=5
    )
    print(f"\nFound {len(error_logs)} error messages")

    # 6. Navigate browser (if connected)
    if stats['total_connections'] > 0:
        print("\n--- Browser Navigation ---")

        # Navigate to a URL
        success = await browser_service.navigate("https://example.com")
        if success:
            print("Successfully navigated to example.com")

        # Wait for logs from the new page
        await asyncio.sleep(3)

        # Get logs from specific URL
        example_logs = await browser_service.query_logs(
            url_pattern="example.com",
            limit=10
        )
        print(f"Captured {len(example_logs)} logs from example.com")

    # 7. Take screenshot
    print("\n--- Taking Screenshot ---")

    # Initialize screenshot service
    await screenshot_service.start()

    # Take screenshot
    screenshot_path = await screenshot_service.capture_screenshot(
        url="https://example.com",
        path="/tmp/example-screenshot.png"
    )

    if screenshot_path:
        print(f"Screenshot saved to: {screenshot_path}")

    # 8. Get storage statistics
    storage_service = await server.container.get('storage_service')
    stats = await storage_service.get_storage_stats()

    print("\n--- Storage Statistics ---")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"Log files: {stats.get('file_count', 0)}")

    # 9. Clean up
    print("\n--- Cleanup ---")

    # Stop screenshot service
    await screenshot_service.stop()

    # Stop server
    await server.stop()

    print("Example completed successfully!")


async def example_mcp_integration():
    """Example of MCP integration patterns."""

    print("\n=== MCP Integration Example ===\n")

    # This shows how Claude Code would interact with MCP Browser

    # 1. The MCP service exposes tools
    print("Available MCP Tools:")
    print("  - browser_navigate: Navigate to a URL")
    print("  - browser_query_logs: Query console logs")
    print("  - browser_screenshot: Capture screenshots")

    # 2. Example tool calls (as they would be made by Claude)
    example_calls = [
        {
            "tool": "browser_navigate",
            "parameters": {
                "url": "https://example.com"
            }
        },
        {
            "tool": "browser_query_logs",
            "parameters": {
                "limit": 100,
                "level": "error",
                "url_pattern": "example.com"
            }
        },
        {
            "tool": "browser_screenshot",
            "parameters": {
                "url": "https://example.com",
                "fullpage": True
            }
        }
    ]

    print("\nExample MCP tool calls:")
    for call in example_calls:
        print(f"\n{json.dumps(call, indent=2)}")


def main():
    """Main entry point."""
    print("MCP Browser Usage Examples")
    print("=" * 50)

    # Run async example
    try:
        asyncio.run(example_usage())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Show MCP integration patterns
    asyncio.run(example_mcp_integration())

    print("\n" + "=" * 50)
    print("For more examples, see the documentation at:")
    print("https://docs.mcp-browser.dev")


if __name__ == "__main__":
    main()