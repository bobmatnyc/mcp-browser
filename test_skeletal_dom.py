#!/usr/bin/env python3
"""Test script for skeletal DOM feature."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli.utils.browser_client import BrowserClient, find_active_port
from cli.commands.browser_refactored import display_skeletal_dom


async def test_skeletal_dom():
    """Test skeletal DOM extraction and display."""
    # Find active port
    port = await find_active_port()
    if not port:
        print("❌ No active mcp-browser server found")
        print("   Start server with: mcp-browser start")
        return

    print(f"✓ Found server on port {port}")

    # Connect client
    client = BrowserClient(port=port)
    connected = await client.connect()
    if not connected:
        print("❌ Failed to connect to server")
        return

    print("✓ Connected to server")

    try:
        # Test 1: Navigate to a page
        print("\n--- Test 1: Navigate to example.com ---")
        result = await client.navigate("https://example.com", wait=0)
        if result.get("success"):
            print("✓ Navigation initiated")
            # Wait for page to load
            await asyncio.sleep(2)

            # Fetch skeletal DOM
            skeletal = await client.get_skeletal_dom()
            print("\n--- Skeletal DOM Response ---")
            display_skeletal_dom(skeletal)
        else:
            print(f"❌ Navigation failed: {result.get('error')}")

        # Test 2: Navigate to another page
        print("\n--- Test 2: Navigate to google.com ---")
        result = await client.navigate("https://www.google.com", wait=0)
        if result.get("success"):
            print("✓ Navigation initiated")
            await asyncio.sleep(2)

            skeletal = await client.get_skeletal_dom()
            print("\n--- Skeletal DOM Response ---")
            display_skeletal_dom(skeletal)
        else:
            print(f"❌ Navigation failed: {result.get('error')}")

    finally:
        await client.disconnect()
        print("\n✓ Disconnected from server")


if __name__ == "__main__":
    asyncio.run(test_skeletal_dom())
