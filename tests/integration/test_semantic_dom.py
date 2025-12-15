#!/usr/bin/env python3
"""Test script for browser_extract_semantic_dom feature."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path to enable absolute imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Use absolute imports matching the package structure
from src.models.browser_state import BrowserState  # noqa: E402
from src.services.browser_service import BrowserService  # noqa: E402


async def test_semantic_dom():
    """Test semantic DOM extraction."""
    print("=" * 80)
    print("Testing browser_extract_semantic_dom Feature")
    print("=" * 80)
    print()

    # Initialize services
    print("1. Initializing browser service...")
    state = BrowserState()
    browser = BrowserService()
    browser.browser_state = state

    # Test port - check running server
    test_port = 8875  # Current running server is on 8875
    print(f"2. Testing on port {test_port}")
    print()

    # Check if there's an active connection
    print("3. Checking for active connection...")
    connection = await state.get_connection(test_port)
    if not connection:
        print(f"   ❌ No active browser connection on port {test_port}")
        print()
        print("SETUP REQUIRED:")
        print(f"  1. Ensure mcp-browser server is running on port {test_port}:")
        print(f"     mcp-browser serve --port {test_port}")
        print()
        print("  2. Launch browser with extension:")
        print(f"     mcp-browser launch --port {test_port}")
        print()
        print("  3. Navigate to a test page, e.g.:")
        print("     - https://developer.mozilla.org/")
        print("     - https://www.wikipedia.org/")
        print("     - https://news.ycombinator.com/")
        print()
        return False

    print(f"   ✓ Connection found: {connection}")
    print()

    # Test extraction with default options
    print("4. Testing semantic DOM extraction (default options)...")
    result = await browser.extract_semantic_dom(port=test_port)

    print()
    print("5. RESULT:")
    print("-" * 80)

    if result.get("success"):
        print("   ✓ Extraction successful!")
        print()

        dom = result.get("dom", {})
        print(f"   Page Title: {dom.get('title', 'N/A')}")
        print(f"   URL: {dom.get('url', 'N/A')}")
        print()

        headings = dom.get("headings", [])
        print(f"   Headings: {len(headings)} found")
        if headings:
            print("   First 5 headings:")
            for h in headings[:5]:
                level = h.get("level", "?")
                text = h.get("text", "")[:60]
                print(f"     - H{level}: {text}")
        print()

        landmarks = dom.get("landmarks", [])
        print(f"   Landmarks: {len(landmarks)} found")
        if landmarks:
            print("   Landmarks:")
            for lm in landmarks[:5]:
                role = lm.get("role", "?")
                label = lm.get("label", "")
                print(f"     - {role}: {label if label else '(no label)'}")
        print()

        links = dom.get("links", [])
        print(f"   Links: {len(links)} found")
        if links:
            print("   First 5 links:")
            for link in links[:5]:
                text = link.get("text", "")[:40]
                href = link.get("href", "")[:50]
                print(f"     - {text} → {href}")
        print()

        forms = dom.get("forms", [])
        print(f"   Forms: {len(forms)} found")
        if forms:
            print("   Forms:")
            for form in forms[:3]:
                action = form.get("action", "")
                method = form.get("method", "")
                fields = form.get("fields", [])
                print(
                    f"     - Action: {action}, Method: {method}, Fields: {len(fields)}"
                )
        print()

        print("-" * 80)
        print()
        print("FULL RESULT (JSON):")
        print(json.dumps(result, indent=2))
        print()
        return True
    else:
        error = result.get("error", "Unknown error")
        print(f"   ❌ Extraction failed: {error}")
        print()
        print("FULL RESULT:")
        print(json.dumps(result, indent=2))
        print()
        return False


async def test_semantic_dom_with_options():
    """Test semantic DOM extraction with custom options."""
    print("=" * 80)
    print("Testing with Custom Options")
    print("=" * 80)
    print()

    state = BrowserState()
    browser = BrowserService()
    browser.browser_state = state
    test_port = 8875  # Match the main test

    connection = await state.get_connection(test_port)
    if not connection:
        print("⚠️  Skipping (no connection)")
        return False

    # Test with limited options
    options = {
        "include_headings": True,
        "include_landmarks": True,
        "include_links": False,  # Exclude links
        "include_forms": False,  # Exclude forms
        "max_text_length": 50,  # Shorter text
    }

    print(f"Options: {json.dumps(options, indent=2)}")
    print()

    result = await browser.extract_semantic_dom(
        port=test_port, options=options, timeout=15.0
    )

    if result.get("success"):
        dom = result.get("dom", {})
        print("   ✓ Custom options test successful!")
        print(f"   Headings: {len(dom.get('headings', []))}")
        print(f"   Landmarks: {len(dom.get('landmarks', []))}")
        print(f"   Links: {len(dom.get('links', []))} (should be 0)")
        print(f"   Forms: {len(dom.get('forms', []))} (should be 0)")
        return True
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False


async def main():
    """Run all tests."""
    print("\n")

    # Test 1: Default options
    test1_passed = await test_semantic_dom()

    print("\n")

    # Test 2: Custom options (only if test 1 passed)
    test2_passed = False
    if test1_passed:
        test2_passed = await test_semantic_dom_with_options()

    print("\n")
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Default options): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(
        f"Test 2 (Custom options): {'✓ PASSED' if test2_passed else '✗ SKIPPED' if not test1_passed else '✗ FAILED'}"
    )
    print("=" * 80)
    print()

    return 0 if test1_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
