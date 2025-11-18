#!/usr/bin/env python3
"""Extract changelog entry for a specific version.

This script extracts the changelog section for a given version from CHANGELOG.md.
Used during GitHub release creation to populate release notes.

Usage:
    python scripts/extract_changelog.py 2.0.10
    python scripts/extract_changelog.py 2.0.10 --markdown  # Output in markdown format
"""

import argparse
import re
import sys
from pathlib import Path


def extract_changelog(version: str, markdown: bool = False) -> str:
    """Extract changelog for specific version from CHANGELOG.md.

    Args:
        version: Version string (e.g., "2.0.10")
        markdown: If True, return markdown formatted output

    Returns:
        Changelog content for the specified version
    """
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"

    try:
        if not changelog_path.exists():
            return f"Release version {version}\n\nNo CHANGELOG.md found."

        with open(changelog_path, "r") as f:
            content = f.read()

        # Find the section for this version
        # Match: ## [2.0.10] - 2024-01-15 (with or without date)
        pattern = rf"## \[{re.escape(version)}\].*?\n(.*?)(?=\n## \[|$)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            changelog_content = match.group(1).strip()

            if markdown:
                return f"## Release Notes for v{version}\n\n{changelog_content}"
            else:
                return changelog_content
        else:
            # Version not found, provide default message
            return f"Release version {version}\n\nSee [CHANGELOG.md](CHANGELOG.md) for details."

    except Exception as e:
        print(f"Error reading changelog: {e}", file=sys.stderr)
        return f"Release version {version}\n\nSee CHANGELOG.md for details."


def main():
    """Main entry point for changelog extraction."""
    parser = argparse.ArgumentParser(
        description="Extract changelog entry for a specific version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "version",
        help="Version to extract changelog for (e.g., 2.0.10)"
    )

    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output in markdown format with header"
    )

    args = parser.parse_args()

    # Extract and print changelog
    changelog = extract_changelog(args.version, args.markdown)
    print(changelog)

    return 0


if __name__ == "__main__":
    sys.exit(main())
