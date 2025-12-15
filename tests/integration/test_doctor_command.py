#!/usr/bin/env python3
"""Test script for the doctor command.

This script verifies all doctor checks work correctly in different scenarios.
"""

import subprocess
import sys
import time

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(name: str):
    """Print test name."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")


def print_success(msg: str):
    """Print success message."""
    print(f"{GREEN}✓ {msg}{RESET}")


def print_error(msg: str):
    """Print error message."""
    print(f"{RED}✗ {msg}{RESET}")


def print_info(msg: str):
    """Print info message."""
    print(f"{YELLOW}→ {msg}{RESET}")


def run_doctor():
    """Run the doctor command and return output."""
    result = subprocess.run(
        ["mcp-browser", "browser", "doctor"],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_basic_execution():
    """Test that doctor command runs without errors."""
    print_test("Basic Execution")

    returncode, stdout, stderr = run_doctor()

    if returncode == 0:
        print_success("Doctor command executed successfully (exit code 0)")
    else:
        print_error(f"Doctor command failed with exit code {returncode}")
        if stderr:
            print_error(f"Error output: {stderr}")
        return False

    # Check for expected output sections
    if "MCP Browser Doctor" in stdout:
        print_success("Found header")
    else:
        print_error("Header missing")
        return False

    if "Summary:" in stdout:
        print_success("Found summary")
    else:
        print_error("Summary missing")
        return False

    return True


def test_all_checks_present():
    """Test that all 8 checks are present."""
    print_test("All Checks Present")

    _, stdout, _ = run_doctor()

    expected_checks = [
        "Configuration",
        "Python Dependencies",
        "MCP Installer",
        "Server Status",
        "Port Availability",
        "Extension Package",
        "MCP Configuration",
        "WebSocket Connectivity",
    ]

    all_present = True
    for check in expected_checks:
        if check in stdout:
            print_success(f"Found check: {check}")
        else:
            print_error(f"Missing check: {check}")
            all_present = False

    return all_present


def test_status_indicators():
    """Test that status indicators are present."""
    print_test("Status Indicators")

    _, stdout, _ = run_doctor()

    # Check for at least one of each status type
    has_pass = "PASS" in stdout
    has_warn = "WARN" in stdout or "warnings" in stdout
    has_fail = "FAIL" in stdout or "failed" in stdout

    if has_pass:
        print_success("Found PASS status")
    else:
        print_error("No PASS status found")

    # We should have warnings or fails (system not perfect)
    if has_warn or has_fail:
        print_success("Found WARN or FAIL status")
    else:
        print_info("No WARN or FAIL status (system is perfect!)")

    return has_pass


def test_with_server_running():
    """Test doctor with server running."""
    print_test("Server Running Scenario")

    # Start server
    print_info("Starting server...")
    subprocess.Popen(
        ["mcp-browser", "start"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for server to start
    time.sleep(3)

    # Run doctor
    _, stdout, _ = run_doctor()

    # Check server status
    if "Running on port" in stdout:
        print_success("Server detected as running")
        server_ok = True
    else:
        print_error("Server not detected as running")
        server_ok = False

    # Check WebSocket connectivity
    if "Successfully connected to ws://localhost:" in stdout:
        print_success("WebSocket connectivity check passed")
        ws_ok = True
    else:
        print_error("WebSocket connectivity check failed")
        ws_ok = False

    # Stop server
    print_info("Stopping server...")
    subprocess.run(["mcp-browser", "stop"], capture_output=True)
    time.sleep(1)

    return server_ok and ws_ok


def test_with_server_stopped():
    """Test doctor with server stopped."""
    print_test("Server Stopped Scenario")

    # Ensure server is stopped
    print_info("Ensuring server is stopped...")
    subprocess.run(["mcp-browser", "stop"], capture_output=True)
    time.sleep(1)

    # Run doctor
    _, stdout, _ = run_doctor()

    # Check server status
    if "Not running" in stdout or "will auto-start" in stdout:
        print_success("Server correctly detected as not running")
        server_ok = True
    else:
        print_error("Server status incorrect")
        server_ok = False

    # Check WebSocket connectivity skipped
    if "skipping connectivity test" in stdout or "Server not running" in stdout:
        print_success("WebSocket check correctly skipped")
        ws_ok = True
    else:
        print_error("WebSocket check should be skipped")
        ws_ok = False

    return server_ok and ws_ok


def test_dependencies_check():
    """Test that dependencies are checked."""
    print_test("Dependencies Check")

    _, stdout, _ = run_doctor()

    # Check for dependency status
    if "required packages installed" in stdout or "Python Dependencies" in stdout:
        print_success("Dependencies check working")
        return True
    else:
        print_error("Dependencies check not working")
        return False


def test_configuration_check():
    """Test configuration check."""
    print_test("Configuration Check")

    _, stdout, _ = run_doctor()

    # Check for config directory mention
    if ".mcp-browser" in stdout or "config.json" in stdout or "Configuration" in stdout:
        print_success("Configuration check working")
        return True
    else:
        print_error("Configuration check not working")
        return False


def test_port_availability_check():
    """Test port availability check."""
    print_test("Port Availability Check")

    _, stdout, _ = run_doctor()

    # Check for port range
    if "8851" in stdout or "8899" in stdout or "ports available" in stdout:
        print_success("Port availability check working")
        return True
    else:
        print_error("Port availability check not working")
        return False


def test_extension_package_check():
    """Test extension package check."""
    print_test("Extension Package Check")

    _, stdout, _ = run_doctor()

    # Check for extension package mention
    if "Extension Package" in stdout or "mcp-browser-extension.zip" in stdout:
        print_success("Extension package check working")
        return True
    else:
        print_error("Extension package check not working")
        return False


def test_no_auto_start():
    """Verify doctor does NOT auto-start the server."""
    print_test("No Auto-Start Behavior")

    # Ensure server is stopped
    print_info("Ensuring server is stopped...")
    subprocess.run(["mcp-browser", "stop"], capture_output=True)
    time.sleep(1)

    # Run doctor
    print_info("Running doctor...")
    run_doctor()

    # Check if server started
    status_result = subprocess.run(
        ["mcp-browser", "status"],
        capture_output=True,
        text=True,
    )

    if (
        "not running" in status_result.stdout.lower()
        or "stopped" in status_result.stdout.lower()
    ):
        print_success("Doctor did NOT auto-start server (correct behavior)")
        return True
    else:
        print_error("Doctor auto-started server (incorrect behavior)")
        return False


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}MCP Browser Doctor Command Test Suite{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    tests = [
        ("Basic Execution", test_basic_execution),
        ("All Checks Present", test_all_checks_present),
        ("Status Indicators", test_status_indicators),
        ("Dependencies Check", test_dependencies_check),
        ("Configuration Check", test_configuration_check),
        ("Port Availability Check", test_port_availability_check),
        ("Extension Package Check", test_extension_package_check),
        ("No Auto-Start Behavior", test_no_auto_start),
        ("Server Stopped Scenario", test_with_server_stopped),
        ("Server Running Scenario", test_with_server_running),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' raised exception: {e}")
            results.append((name, False))

    # Print summary
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        if result:
            print(f"{GREEN}✓{RESET} {name}")
        else:
            print(f"{RED}✗{RESET} {name}")

    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"{GREEN}All tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}Some tests failed.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
