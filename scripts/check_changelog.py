#!/usr/bin/env python3
"""Check that CHANGELOG.md has been updated for version changes.

This script ensures that when the version is bumped,
there's a corresponding entry in the CHANGELOG.
"""

import re
import sys
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def get_current_version() -> str:
    """Get current version from VERSION file."""
    version_file = PROJECT_ROOT / "VERSION"
    if not version_file.exists():
        return None
    return version_file.read_text().strip()


def check_changelog_for_version(version: str) -> bool:
    """Check if CHANGELOG.md contains an entry for the given version."""
    changelog = PROJECT_ROOT / "CHANGELOG.md"

    if not changelog.exists():
        print("Warning: CHANGELOG.md not found", file=sys.stderr)
        # Don't fail if changelog doesn't exist yet
        return True

    content = changelog.read_text()

    # Look for version entry in changelog
    # Format: ## [1.0.1] - 2024-01-01
    pattern = rf'##\s+\[{re.escape(version)}\]'
    if re.search(pattern, content):
        return True

    # Also check for unreleased section with content
    if '## [Unreleased]' in content:
        # Check if there's content after Unreleased
        lines = content.split('\n')
        unreleased_index = -1
        for i, line in enumerate(lines):
            if '## [Unreleased]' in line:
                unreleased_index = i
                break

        if unreleased_index >= 0:
            # Check next few lines for content
            for i in range(unreleased_index + 1, min(unreleased_index + 10, len(lines))):
                line = lines[i].strip()
                if line and not line.startswith('#'):
                    # Found content in Unreleased section
                    return True

    return False


def main():
    """Main entry point."""
    version = get_current_version()

    if not version:
        print("Error: Could not determine current version", file=sys.stderr)
        sys.exit(1)

    if not check_changelog_for_version(version):
        print(f"Error: No changelog entry found for version {version}", file=sys.stderr)
        print("Please update CHANGELOG.md with release notes", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Changelog check passed for version {version}")
    sys.exit(0)


if __name__ == "__main__":
    main()