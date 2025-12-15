#!/usr/bin/env python3
"""Test semantic DOM extraction via WebSocket connection."""

import asyncio
import json
import uuid

import websockets


async def test_semantic_dom_via_websocket():
    """Test semantic DOM extraction by connecting to the WebSocket server."""
    print("=" * 80)
    print("Testing browser_extract_semantic_dom via WebSocket")
    print("=" * 80)
    print()

    port = 8875
    uri = f"ws://localhost:{port}"

    print(f"1. Connecting to WebSocket server at {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("   ✓ Connected!")
            print()

            # Send server info request
            print("2. Requesting server info...")
            await websocket.send(json.dumps({"type": "server_info"}))

            response = await websocket.recv()
            server_info = json.loads(response)
            print(f"   Server: {server_info.get('project_name')} v{server_info.get('version')}")
            print(f"   Project: {server_info.get('project_id')}")
            print(f"   Capabilities: {server_info.get('capabilities')}")
            print()

            # Send semantic DOM extraction request
            print("3. Sending extract_semantic_dom request...")
            request_id = str(uuid.uuid4())

            request = {
                "type": "extract_semantic_dom",
                "requestId": request_id,
                "tabId": None,  # Active tab
                "options": {
                    "include_headings": True,
                    "include_landmarks": True,
                    "include_links": True,
                    "include_forms": True,
                    "max_text_length": 100
                }
            }

            await websocket.send(json.dumps(request))
            print(f"   Request ID: {request_id}")
            print("   Waiting for response...")
            print()

            # Wait for response (with timeout) - may receive multiple messages
            try:
                # Wait for semantic_dom_extracted response
                timeout_time = 15.0
                start_time = asyncio.get_event_loop().time()

                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    remaining = timeout_time - elapsed

                    if remaining <= 0:
                        raise asyncio.TimeoutError()

                    response_data = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                    response = json.loads(response_data)
                    msg_type = response.get("type")

                    # Skip server_info_response, we're looking for semantic_dom_extracted
                    if msg_type == "server_info_response":
                        print(f"   (Received {msg_type}, waiting for semantic_dom_extracted...)")
                        continue

                    # Found our response
                    print("4. RESPONSE RECEIVED:")
                    print("-" * 80)
                    print(f"   Type: {msg_type}")

                    # Break out of the loop to process the response
                    break

                if msg_type == "semantic_dom_extracted":
                    req_id = response.get("requestId")
                    result = response.get("response", {})

                    print(f"   Request ID match: {req_id == request_id}")
                    print()

                    if result.get("success"):
                        print("   ✓ Extraction successful!")
                        dom = result.get("dom", {})

                        print()
                        print(f"   Title: {dom.get('title', 'N/A')}")
                        print(f"   URL: {dom.get('url', 'N/A')}")
                        print()

                        headings = dom.get("headings", [])
                        print(f"   Headings: {len(headings)}")
                        for h in headings[:3]:
                            print(f"     - H{h.get('level')}: {h.get('text', '')[:60]}")
                        print()

                        landmarks = dom.get("landmarks", [])
                        print(f"   Landmarks: {len(landmarks)}")
                        for lm in landmarks[:3]:
                            print(f"     - {lm.get('role')}: {lm.get('label', '(no label)')}")
                        print()

                        links = dom.get("links", [])
                        print(f"   Links: {len(links)}")
                        print()

                        forms = dom.get("forms", [])
                        print(f"   Forms: {len(forms)}")
                        print()

                        print("=" * 80)
                        print("✓ TEST PASSED")
                        return True
                    else:
                        error = result.get("error", "Unknown error")
                        print(f"   ✗ Extraction failed: {error}")
                        print()
                        print("=" * 80)
                        print("✗ TEST FAILED")
                        return False
                elif msg_type == "error":
                    print(f"   ✗ Error: {response.get('message')}")
                    print()
                    print("=" * 80)
                    print("✗ TEST FAILED - Server returned error")
                    return False
                else:
                    print(f"   ⚠ Unexpected message type: {msg_type}")
                    print(f"   Full response: {json.dumps(response, indent=2)}")
                    print()
                    print("=" * 80)
                    print("? TEST INCONCLUSIVE")
                    return False

            except asyncio.TimeoutError:
                print("   ✗ Timeout waiting for response")
                print()
                print("=" * 80)
                print("✗ TEST FAILED - Timeout")
                print()
                print("POSSIBLE CAUSES:")
                print("  1. No browser extension connected")
                print("  2. Browser not on a page with content")
                print("  3. Extension doesn't support extract_semantic_dom")
                print()
                print("SETUP:")
                print("  1. Launch a browser with the extension:")
                print("     mcp-browser launch --port 8875")
                print("  2. Navigate to a test page:")
                print("     - https://developer.mozilla.org/")
                print("     - https://www.wikipedia.org/")
                return False

    except ConnectionRefusedError:
        print(f"   ✗ Connection refused - server not running on port {port}")
        print()
        print("SETUP REQUIRED:")
        print(f"  Start the server: mcp-browser start --port {port}")
        print()
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_semantic_dom_via_websocket())
    exit(0 if result else 1)
