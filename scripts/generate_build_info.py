#!/usr/bin/env python3
"""Generate build information for browser extensions.

This script generates a build-info.json file with timestamp-based build numbers
for tracking extension deployments during development.

Usage:
    python scripts/generate_build_info.py [extension_dir]
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def generate_build_number() -> str:
    """Generate a timestamp-based build number.

    Format: YYYY.MM.DD.HHMM
    Example: 2025.12.15.0630
    """
    now = datetime.now(timezone.utc)
    return f"{now.year}.{now.month:02d}.{now.day:02d}.{now.hour:02d}{now.minute:02d}"


def get_version() -> str:
    """Get the current version from _version.py."""
    version_file = Path(__file__).parent.parent / "src" / "_version.py"

    try:
        with open(version_file, "r") as f:
            for line in f:
                if line.startswith("__version__"):
                    # Extract version from: __version__ = "2.2.25"
                    return line.split('"')[1]
    except Exception as e:
        print(f"Warning: Could not read version: {e}", file=sys.stderr)
        return "unknown"

    return "unknown"


def generate_build_info(extension_dir: Path) -> dict:
    """Generate build information dictionary.

    Args:
        extension_dir: Path to the extension directory

    Returns:
        Dictionary containing build information
    """
    build_number = generate_build_number()
    deployed_time = datetime.now(timezone.utc).isoformat()
    version = get_version()

    return {
        "version": version,
        "build": build_number,
        "deployed": deployed_time,
        "extension": extension_dir.name,
    }


def update_manifest_version(extension_dir: Path, build_info: dict) -> str:
    """Update manifest.json version to include build number.

    Chrome allows 4-part versions: X.Y.Z.W
    We use HHMM as the 4th component for the build number.

    Args:
        extension_dir: Path to the extension directory
        build_info: Build information dictionary

    Returns:
        The new 4-part version string
    """
    manifest_file = extension_dir / "manifest.json"
    if not manifest_file.exists():
        return build_info["version"]

    with open(manifest_file, "r") as f:
        manifest = json.load(f)

    # Extract HHMM from build number (format: YYYY.MM.DD.HHMM)
    build_parts = build_info["build"].split(".")
    hhmm = int(build_parts[3]) if len(build_parts) >= 4 else 0

    # Get base version (first 3 parts)
    base_version = manifest.get("version", "1.0.0")
    version_parts = base_version.split(".")[:3]  # Take only first 3 parts

    # Create 4-part version: X.Y.Z.HHMM
    new_version = ".".join(version_parts + [str(hhmm)])
    manifest["version"] = new_version

    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    return new_version


def write_build_info(extension_dir: Path, build_info: dict) -> None:
    """Write build-info.json and update manifest.json version.

    Args:
        extension_dir: Path to the extension directory
        build_info: Build information dictionary
    """
    # Update manifest.json with 4-part version
    manifest_version = update_manifest_version(extension_dir, build_info)

    # Write build-info.json
    build_info_file = extension_dir / "build-info.json"

    with open(build_info_file, "w") as f:
        json.dump(build_info, f, indent=2)

    print(f"✓ Generated {build_info_file}")
    print(f"  Version: {manifest_version}")
    print(f"  Build: {build_info['build']}")
    print(f"  Deployed: {build_info['deployed']}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        extension_dir = Path(sys.argv[1])
    else:
        # Default to mcp-browser-extensions/chrome
        extension_dir = Path(__file__).parent.parent / "mcp-browser-extensions" / "chrome"

    if not extension_dir.exists():
        print(f"Error: Extension directory not found: {extension_dir}", file=sys.stderr)
        sys.exit(1)

    build_info = generate_build_info(extension_dir)
    write_build_info(extension_dir, build_info)


if __name__ == "__main__":
    main()
