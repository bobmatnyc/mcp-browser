#!/usr/bin/env python3
"""Check version consistency across all project files.

This script ensures that version numbers are consistent in:
- VERSION file
- src/_version.py
- pyproject.toml
- setup.py
"""

import re
import sys
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def extract_version_from_file(filepath: Path, pattern: str) -> str:
    """Extract version from a file using regex pattern."""
    if not filepath.exists():
        return None

    content = filepath.read_text()
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        return match.group(1)
    return None


def check_versions():
    """Check version consistency across all files."""
    versions = {}
    errors = []

    # Check VERSION file
    version_file = PROJECT_ROOT / "VERSION"
    if version_file.exists():
        versions["VERSION"] = version_file.read_text().strip()
    else:
        errors.append("VERSION file not found")

    # Check src/_version.py
    version_py = PROJECT_ROOT / "src" / "_version.py"
    version = extract_version_from_file(
        version_py,
        r'^__version__ = ["\']([0-9]+\.[0-9]+\.[0-9]+)["\']'
    )
    if version:
        versions["src/_version.py"] = version
    else:
        errors.append("Could not extract version from src/_version.py")

    # Check pyproject.toml
    pyproject = PROJECT_ROOT / "pyproject.toml"
    version = extract_version_from_file(
        pyproject,
        r'^version = ["\']([0-9]+\.[0-9]+\.[0-9]+)["\']'
    )
    if version:
        versions["pyproject.toml"] = version
    else:
        errors.append("Could not extract version from pyproject.toml")

    # Check setup.py (it should now import from _version.py, but let's verify)
    setup_py = PROJECT_ROOT / "setup.py"
    if setup_py.exists():
        content = setup_py.read_text()
        # Check if setup.py imports from _version
        if "from _version import __version__" in content:
            # Good, it's using the centralized version
            pass
        else:
            # Try to extract hardcoded version
            version = extract_version_from_file(
                setup_py,
                r'version\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']'
            )
            if version:
                versions["setup.py"] = version

    # Check for consistency
    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        errors.append(f"Version mismatch detected!")
        for file, version in versions.items():
            print(f"  {file}: {version}", file=sys.stderr)
        return False

    if not versions:
        errors.append("No version information found in any file")
        return False

    if errors:
        print("Version check errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return False

    # All versions match
    version = list(unique_versions)[0]
    print(f"✅ Version consistency check passed: {version}")
    return True


def main():
    """Main entry point."""
    if not check_versions():
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()