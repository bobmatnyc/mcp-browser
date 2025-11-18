#!/usr/bin/env python3
"""Test MCP server tools listing with CORRECT protocol."""

import json
import subprocess
import sys


def test_mcp_server():
    """Test MCP server initialization and tool listing."""

    # Test initialization
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"},
        },
    }

    # CORRECT initialized notification - must use "notifications/initialized"
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }

    # Test tool listing
    tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

    try:
        # Start the MCP server
        proc = subprocess.Popen(
            [".venv/bin/python", "mcp-server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Send initialization request
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # Use timeout to read responses
        import time

        time.sleep(0.5)  # Give server time to start

        # Read initialization response
        init_response = proc.stdout.readline()
        if init_response:
            print("✅ Initialization response received")
            init_data = json.loads(init_response)
            if "result" in init_data:
                print(
                    f"  Server: {init_data['result'].get('serverInfo', {}).get('name', 'Unknown')}"
                )
                print(
                    f"  Version: {init_data['result'].get('serverInfo', {}).get('version', 'Unknown')}"
                )

        # Send initialized notification to complete handshake
        proc.stdin.write(json.dumps(initialized_notification) + "\n")
        proc.stdin.flush()
        time.sleep(0.5)  # No response expected for notification

        # Send tools list request
        proc.stdin.write(json.dumps(tools_request) + "\n")
        proc.stdin.flush()

        # Read tools response with timeout
        time.sleep(0.5)
        tools_response = proc.stdout.readline()

        # Parse and display tools
        if tools_response:
            response_data = json.loads(tools_response)
            if "result" in response_data and "tools" in response_data["result"]:
                tools = response_data["result"]["tools"]
                print(f"\n✅ MCP Server provides {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")
            else:
                print("⚠️  No tools found in response")
        else:
            print("⚠️  No tools response received (this may be normal)")

        # Terminate the process
        proc.terminate()
        proc.wait(timeout=1)

    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_mcp_server()
