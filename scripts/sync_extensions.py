#!/usr/bin/env python3
"""Sync and adapt extensions from Chrome source.

This script:
1. Syncs shared assets (icons, Readability.js) to all extension directories
2. Converts Chrome MV3 manifest to Firefox MV2 format
3. Adapts JavaScript for browser compatibility
"""

import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict


def get_project_root() -> Path:
    """Get the project root directory."""
    # Script is in scripts/, project root is parent
    return Path(__file__).parent.parent


def sync_shared_assets() -> None:
    """Copy shared assets to all extension directories."""
    project_root = get_project_root()
    shared_dir = project_root / "src" / "extensions" / "shared"

    print("📦 Syncing shared assets...")

    for ext_name in ["chrome", "firefox", "safari"]:
        ext_dir = project_root / "src" / "extensions" / ext_name
        if not ext_dir.exists():
            print(f"  ⚠️  {ext_name} directory not found, skipping")
            continue

        # Copy icons directory
        icons_src = shared_dir / "icons"
        icons_dst = ext_dir / "icons"
        if icons_src.exists():
            if icons_dst.exists():
                shutil.rmtree(icons_dst)
            shutil.copytree(icons_src, icons_dst)
            print(f"  ✅ Synced icons to {ext_name}")

        # Copy Readability.js
        readability_src = shared_dir / "Readability.js"
        readability_dst = ext_dir / "Readability.js"
        if readability_src.exists():
            shutil.copy(readability_src, readability_dst)
            print(f"  ✅ Synced Readability.js to {ext_name}")


def convert_manifest_v3_to_v2(v3_manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Chrome MV3 manifest to Firefox MV2.

    Key changes:
    - manifest_version: 3 → 2
    - background.service_worker → background.scripts
    - action → browser_action
    - host_permissions → merge into permissions
    - Add browser_specific_settings for Firefox
    """
    v2 = v3_manifest.copy()
    v2["manifest_version"] = 2

    # Convert background service_worker to scripts
    if "background" in v2:
        sw = v2["background"].get("service_worker")
        if sw:
            # For Firefox, we'll use the same background script
            # but it should be MV2-compatible
            v2["background"] = {
                "scripts": [sw],
                "persistent": True
            }

    # Convert action to browser_action (MV2 uses browser_action)
    if "action" in v2:
        v2["browser_action"] = v2.pop("action")

    # Merge host_permissions into permissions
    if "host_permissions" in v3_manifest:
        v2.setdefault("permissions", []).extend(v3_manifest["host_permissions"])
        v2.pop("host_permissions", None)

    # Add Firefox-specific settings
    v2["browser_specific_settings"] = {
        "gecko": {
            "id": "mcp-browser@anthropic.com",
            "strict_min_version": "109.0"
        }
    }

    return v2


def adapt_js_for_firefox(js_content: str) -> str:
    """Adapt JavaScript for Firefox compatibility.

    Firefox supports both chrome.* and browser.* APIs, but browser.* is preferred.
    For now, we keep chrome.* as Firefox has a polyfill.

    Future improvements:
    - Convert chrome.* to browser.* for Firefox preference
    - Handle MV2-specific patterns
    """
    # For now, return as-is since Firefox supports chrome.* via polyfill
    # In the future, we could convert to browser.* for better Firefox integration
    return js_content


def generate_firefox_from_chrome() -> None:
    """Generate Firefox extension from Chrome source.

    This converts the Chrome MV3 extension to Firefox MV2 format.
    """
    project_root = get_project_root()
    chrome_dir = project_root / "src" / "extensions" / "chrome"
    firefox_dir = project_root / "src" / "extensions" / "firefox"

    if not chrome_dir.exists():
        print("❌ Chrome extension directory not found")
        return

    print("\n🦊 Generating Firefox extension from Chrome source...")

    # Convert manifest
    chrome_manifest_path = chrome_dir / "manifest.json"
    firefox_manifest_path = firefox_dir / "manifest.json"

    if chrome_manifest_path.exists():
        with open(chrome_manifest_path, "r") as f:
            chrome_manifest = json.load(f)

        firefox_manifest = convert_manifest_v3_to_v2(chrome_manifest)

        # Firefox uses same enhanced popup as Chrome
        # No need to change popup reference - keep popup-enhanced.html

        with open(firefox_manifest_path, "w") as f:
            json.dump(firefox_manifest, f, indent=2)

        print(f"  ✅ Converted manifest.json (MV3 → MV2)")

    # Note: JavaScript files are already compatible
    # Firefox supports chrome.* API via polyfill
    print("  ℹ️  JavaScript files remain unchanged (Firefox supports chrome.* API)")


def validate_extensions() -> None:
    """Validate that all extensions have required files."""
    project_root = get_project_root()
    extensions_dir = project_root / "src" / "extensions"

    print("\n🔍 Validating extensions...")

    required_files = {
        "chrome": [
            "manifest.json",
            "background-enhanced.js",
            "content.js",
            "popup-enhanced.html",
            "popup-enhanced.js",
            "Readability.js",
            "icons"
        ],
        "firefox": [
            "manifest.json",
            "background-enhanced.js",
            "content.js",
            "popup-enhanced.html",
            "popup-enhanced.js",
            "Readability.js"
        ],
        "safari": [
            "manifest.json",
            "background.js",
            "popup.html",
            "popup.js"
        ]
    }

    for ext_name, files in required_files.items():
        ext_dir = extensions_dir / ext_name
        print(f"\n  {ext_name}:")

        if not ext_dir.exists():
            print(f"    ⚠️  Directory not found")
            continue

        for file_name in files:
            file_path = ext_dir / file_name
            if file_path.exists():
                print(f"    ✅ {file_name}")
            else:
                print(f"    ❌ {file_name} MISSING")


def main() -> None:
    """Main entry point for extension sync script."""
    print("🔄 MCP Browser Extension Sync Tool\n")
    print("=" * 60)

    # Sync shared assets to all extensions
    sync_shared_assets()

    # Generate/update Firefox extension from Chrome
    generate_firefox_from_chrome()

    # Validate all extensions
    validate_extensions()

    print("\n" + "=" * 60)
    print("✅ Extension sync complete!")
    print("\nNext steps:")
    print("  1. Test Chrome extension: Load src/extensions/chrome/ in Chrome")
    print("  2. Test Firefox extension: Load src/extensions/firefox/ in Firefox")
    print("  3. Review generated Firefox manifest for correctness")


if __name__ == "__main__":
    main()
