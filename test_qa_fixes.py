#!/usr/bin/env python3
"""Test script for QA fixes to auto-start functionality."""

import subprocess
import sys
import time
from pathlib import Path

def run_cmd(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run command and return success status and output."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"CMD: {' '.join(cmd)}")
    print('='*60)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        success = result.returncode == 0
        print(f"\nResult: {'✅ PASS' if success else '❌ FAIL'} (exit code: {result.returncode})")

        return success, result.stdout

    except subprocess.TimeoutExpired:
        print("❌ FAIL - Command timed out")
        return False, ""
    except Exception as e:
        print(f"❌ FAIL - Exception: {e}")
        return False, ""

def main():
    """Run test sequence."""
    print("\n" + "="*60)
    print("QA FIXES VERIFICATION TEST")
    print("="*60)

    # Test 1: Stop server (cleanup)
    success, _ = run_cmd(
        ["mcp-browser", "stop"],
        "Stop any running server"
    )
    time.sleep(1)

    # Test 2: Check status (should auto-start)
    success, output = run_cmd(
        ["mcp-browser", "browser", "status"],
        "Auto-start server via browser status command"
    )

    if not success:
        print("\n❌ CRITICAL: Auto-start failed!")
        sys.exit(1)

    # Check for correct port range in output
    if "8851" in output or "8852" in output or any(f"88{i}" in output for i in range(51, 100)):
        print("\n✅ Server using correct port range (8851-8899)")
    else:
        print("\n⚠️  WARNING: Could not verify port range in output")

    # Test 3: Verify status shows running server
    time.sleep(1)
    success, output = run_cmd(
        ["mcp-browser", "status"],
        "Verify status shows server running"
    )

    if "running" in output.lower() or "started" in output.lower():
        print("\n✅ Status correctly shows server running")
    else:
        print("\n⚠️  WARNING: Status output unclear about server state")

    # Test 4: Stop server (cleanup)
    success, _ = run_cmd(
        ["mcp-browser", "stop"],
        "Stop server (cleanup)"
    )

    print("\n" + "="*60)
    print("TEST SEQUENCE COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("1. Review output above for any failures")
    print("2. Test browser control commands")
    print("3. Test with actual browser extension")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
