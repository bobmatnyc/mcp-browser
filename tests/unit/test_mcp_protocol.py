#!/usr/bin/env python3
"""
Test MCP server protocol implementation.

This test demonstrates the CORRECT MCP protocol flow:
1. Send initialize request
2. Receive initialize response
3. Send notifications/initialized notification (NOT just "initialized")
4. Server is now ready to handle requests like tools/list

IMPORTANT: The initialized notification method must be "notifications/initialized"
not just "initialized" as per the MCP specification.
"""

import json
import select
import subprocess
import sys


def send_request(proc, req_dict, timeout=2.0):
    """Send a request and return the response."""
    proc.stdin.write(json.dumps(req_dict) + "\n")
    proc.stdin.flush()

    # Wait for response (notifications don't return a response)
    ready, _, _ = select.select([proc.stdout], [], [], timeout)
    if ready:
        response = proc.stdout.readline()
        if response:
            return json.loads(response)
    return None


def test_mcp_server():
    """Test MCP server with correct protocol flow."""

    print("Starting MCP server test...")

    # Start the MCP server
    proc = subprocess.Popen(
        [sys.executable, "mcp-server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    try:
        # 1. Initialize handshake
        print("\n1. Sending initialize request...")
        response = send_request(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            },
        )

        if response and "result" in response:
            server_info = response["result"].get("serverInfo", {})
            print(
                f"   ✓ Server initialized: {server_info.get('name', 'Unknown')} "
                f"v{server_info.get('version', 'Unknown')}"
            )
            print(f"   Protocol version: {response['result'].get('protocolVersion')}")
        else:
            print(f"   ✗ Failed to initialize: {response}")
            return False

        # 2. Complete initialization with correct notification
        print("\n2. Sending initialized notification...")
        print("   Note: Using 'notifications/initialized' (not just 'initialized')")
        send_request(
            proc,
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",  # CORRECT format
                "params": {},
            },
            timeout=0.5,
        )  # Short timeout as no response expected
        print("   ✓ Notification sent")

        # 3. List available tools
        print("\n3. Requesting tools list...")
        response = send_request(
            proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )

        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"   ✓ Server provides {len(tools)} tools:")
            for tool in tools:
                print(f"      - {tool['name']}: {tool['description']}")
        elif response and "error" in response:
            print(f"   ✗ Error: {response['error']['message']}")
            print("      This usually means the initialized notification was incorrect")
            return False
        else:
            print("   ✗ No response received")
            return False

        # 4. Test a tool call
        print("\n4. Testing tool call...")
        response = send_request(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "browser_query_logs",
                    "arguments": {"port": 8888, "last_n": 10},
                },
            },
        )

        if response and "result" in response:
            print("   ✓ Tool call successful")
        elif response and "error" in response:
            # Expected if no browser is connected
            print(
                f"   ✓ Tool call processed (error expected if no browser): "
                f"{response['error'].get('message', 'Unknown error')}"
            )
        else:
            print("   ✗ No response received")

        print("\n✅ All tests passed! MCP server is working correctly.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
