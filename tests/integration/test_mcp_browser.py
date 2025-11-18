#!/usr/bin/env python3
"""Test script for MCP Browser functionality."""

import asyncio
import json
import time

import websockets


async def test_websocket_connection(port=8875):
    """Test WebSocket connection to MCP Browser server."""
    uri = f"ws://localhost:{port}"

    print(f"Testing WebSocket connection to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to port {port}")

            # Send a test message
            test_message = {
                "type": "batch",
                "messages": [
                    {
                        "level": "log",
                        "message": "Test message from Python client",
                        "timestamp": time.time() * 1000,
                    }
                ],
                "url": "http://test.example.com",
                "timestamp": time.time() * 1000,
            }

            await websocket.send(json.dumps(test_message))
            print("✅ Sent test message")

            # Wait for any response (optional)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"📨 Received response: {response}")
            except asyncio.TimeoutError:
                print("ℹ️ No response received (normal for batch messages)")

            return True

    except Exception as e:
        print(f"❌ Connection failed on port {port}: {e}")
        return False


async def scan_ports():
    """Scan all MCP Browser ports."""
    print("\nScanning MCP Browser port range (8875-8895)...")
    print("-" * 40)

    active_ports = []
    for port in range(8875, 8896):
        try:
            # Quick connection test
            websocket = await asyncio.wait_for(
                websockets.connect(f"ws://localhost:{port}"), timeout=0.5
            )
            await websocket.close()
            active_ports.append(port)
            print(f"Port {port}: ✅ Active")
        except (asyncio.TimeoutError, OSError, Exception):
            print(f"Port {port}: ⭕ Not listening")

    return active_ports


async def main():
    """Main test function."""
    print("=" * 50)
    print("MCP Browser WebSocket Test")
    print("=" * 50)

    # Scan for active ports
    active_ports = await scan_ports()

    if active_ports:
        print(f"\n✅ Found {len(active_ports)} active WebSocket server(s)")
        print(f"Active ports: {active_ports}")

        # Test connection to first active port
        print(f"\nTesting connection to port {active_ports[0]}...")
        await test_websocket_connection(active_ports[0])
    else:
        print("\n❌ No active WebSocket servers found")
        print("\nTips:")
        print("1. Make sure MCP Browser server is running:")
        print("   mcp-browser start")
        print("2. Check if the server is listening on the expected ports")
        print("3. Verify firewall settings allow local WebSocket connections")

    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
