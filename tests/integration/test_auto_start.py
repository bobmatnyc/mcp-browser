#!/usr/bin/env python3
"""Test script to verify auto-start functionality."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cli.utils.daemon import (  # noqa: E402
    ensure_server_running,
    get_server_status,
)


def test_auto_start():
    """Test the auto-start functionality."""
    print("Testing auto-start functionality...\n")

    # 1. Check initial status
    print("1. Checking initial status:")
    is_running, pid, port = get_server_status()
    print(f"   Server running: {is_running}")
    print(f"   PID: {pid}")
    print(f"   Port: {port}\n")

    # 2. Test ensure_server_running
    print("2. Testing ensure_server_running():")
    success, port = ensure_server_running()
    print(f"   Success: {success}")
    print(f"   Port: {port}\n")

    # 3. Check status after ensure
    print("3. Checking status after ensure_server_running():")
    is_running, pid, port = get_server_status()
    print(f"   Server running: {is_running}")
    print(f"   PID: {pid}")
    print(f"   Port: {port}\n")

    # 4. Call ensure again (should return existing server)
    print("4. Testing idempotence (calling again):")
    success, port2 = ensure_server_running()
    print(f"   Success: {success}")
    print(f"   Port: {port2}")
    print(f"   Same as before: {port == port2}\n")

    print("✓ Auto-start functionality test complete!")
    print(f"\nServer is running on port {port}")
    print("You can verify by running: mcp-browser status")


if __name__ == "__main__":
    test_auto_start()
