#!/usr/bin/env python3
"""Test browser control functionality through MCP Browser server."""

import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_browser_control():
    """Test browser control commands via WebSocket."""
    uri = "ws://localhost:8875"

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as ws:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected successfully")

            # Wait for connection_ack
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for connection acknowledgment...")
            ack = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received: {ack}")

            # Test 1: Navigate command
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === TEST 1: Navigation ===")
            navigate_cmd = {
                "type": "navigate",
                "url": "https://httpbin.org/html"
            }
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending: {json.dumps(navigate_cmd, indent=2)}")
            await ws.send(json.dumps(navigate_cmd))

            # Wait for response or timeout
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for response...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Response: {response}")
            except asyncio.TimeoutError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No error response (command may have succeeded)")

            # Give navigation time to complete
            await asyncio.sleep(2)

            # Test 2: Get page title
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === TEST 2: Get Page Title ===")
            get_title_cmd = {
                "type": "execute_script",
                "script": "document.title"
            }
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending: {json.dumps(get_title_cmd, indent=2)}")
            await ws.send(json.dumps(get_title_cmd))

            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Response: {response}")
            except asyncio.TimeoutError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No response received")

            # Test 3: Click command (if page has clickable element)
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === TEST 3: Click Element ===")
            click_cmd = {
                "type": "click",
                "selector": "h1"  # httpbin.org/html has an h1 element
            }
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending: {json.dumps(click_cmd, indent=2)}")
            await ws.send(json.dumps(click_cmd))

            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Response: {response}")
            except asyncio.TimeoutError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No response received")

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === Test Complete ===")

    except websockets.exceptions.ConnectionRefused:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Connection refused. Is the server running?")
        return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    print("MCP Browser Control Test")
    print("=" * 50)
    print("Prerequisites:")
    print("1. MCP Browser server running on port 8875")
    print("2. Browser extension loaded and connected (green badge)")
    print("3. At least one browser tab open")
    print("=" * 50)
    print()

    success = asyncio.run(test_browser_control())
    sys.exit(0 if success else 1)
