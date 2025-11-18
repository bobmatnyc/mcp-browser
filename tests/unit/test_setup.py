#!/usr/bin/env python3
"""Test script to verify MCP Browser setup."""

import importlib.util
import sys
from pathlib import Path


def test_imports():
    """Test if all required modules can be imported."""
    modules = [
        "src.cli.main",
        "src.container.service_container",
        "src.services.browser_service",
        "src.services.websocket_service",
        "src.services.storage_service",
        "src.services.mcp_service",
        "src.services.screenshot_service",
        "src.services.dashboard_service",
    ]

    print("Testing module imports...")
    for module_name in modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec:
                print(f"✓ {module_name}")
            else:
                print(f"✗ {module_name} - not found")
                return False
        except ImportError as e:
            print(f"✗ {module_name} - {e}")
            return False

    return True


def test_static_files():
    """Test if static files are in place."""
    base_path = Path(__file__).parent / "src" / "static"
    files = [
        "test-page.html",
        "extension-installer.html",
        "dashboard/index.html",
    ]

    print("\nTesting static files...")
    for file_path in files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - not found at {full_path}")
            return False

    return True


def test_extension():
    """Test if extension files exist."""
    ext_path = Path(__file__).parent / "extension"
    required_files = [
        "manifest.json",
        "background.js",
        "content.js",
        "popup.html",
        "popup.js",
    ]

    print("\nTesting extension files...")
    for file_name in required_files:
        full_path = ext_path / file_name
        if full_path.exists():
            print(f"✓ {file_name}")
        else:
            print(f"✗ {file_name} - not found")
            return False

    return True


def main():
    """Run all tests."""
    print("MCP Browser Setup Test")
    print("=" * 40)

    success = True

    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent))

    if not test_imports():
        success = False

    if not test_static_files():
        success = False

    if not test_extension():
        success = False

    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed!")
        print("\nYou can now run:")
        print("  ./install.sh        # Install via pipx")
        print("  mcp-browser init    # Initialize project extension")
        print("  mcp-browser start   # Start server with dashboard")
        return 0
    else:
        print("✗ Some tests failed. Please check the setup.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
