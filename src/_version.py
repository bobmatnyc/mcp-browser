"""Single source of truth for mcp-browser versioning.

This module provides version information and build metadata for the mcp-browser package.
All version references throughout the project should import from this module.
"""

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# Semantic version - MAJOR.MINOR.PATCH
__version__ = "2.0.11"

# Version components for programmatic access
VERSION_INFO = tuple(map(int, __version__.split(".")))
MAJOR, MINOR, PATCH = VERSION_INFO

# Project metadata
__title__ = "mcp-browser"
__description__ = "Browser console log capture and control via MCP for Claude Code"
__author__ = "MCP Browser Team"
__author_email__ = "support@mcp-browser.dev"
__license__ = "MIT"
__copyright__ = f"2024 {__author__}"

# Build metadata
BUILD_DATE = datetime.now(timezone.utc).isoformat()
IS_DEVELOPMENT = os.environ.get("MCP_BROWSER_ENV", "production") == "development"


def get_git_commit() -> Optional[str]:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=1,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def get_git_branch() -> Optional[str]:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=1,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def get_git_dirty() -> bool:
    """Check if the git repository has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=1,
        )
        if result.returncode == 0:
            return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return False


def get_version_string(include_build: bool = False) -> str:
    """Get the version string with optional build metadata.

    Args:
        include_build: If True, include git commit and build info

    Returns:
        Version string like '1.0.1' or '1.0.1+abc1234.dev'
    """
    version = __version__

    if include_build:
        metadata = []

        # Add git commit if available
        commit = get_git_commit()
        if commit:
            metadata.append(commit)
            if get_git_dirty():
                metadata.append("dirty")

        # Add development flag
        if IS_DEVELOPMENT:
            metadata.append("dev")

        # Add branch if not main/master
        branch = get_git_branch()
        if branch and branch not in ("main", "master"):
            metadata.append(branch.replace("/", "-"))

        if metadata:
            version = f"{version}+{'.'.join(metadata)}"

    return version


def get_version_info() -> dict:
    """Get comprehensive version information.

    Returns:
        Dictionary containing all version and build metadata
    """
    return {
        "version": __version__,
        "version_info": VERSION_INFO,
        "major": MAJOR,
        "minor": MINOR,
        "patch": PATCH,
        "build_date": BUILD_DATE,
        "git_commit": get_git_commit(),
        "git_branch": get_git_branch(),
        "git_dirty": get_git_dirty(),
        "is_development": IS_DEVELOPMENT,
        "full_version": get_version_string(include_build=True),
        "title": __title__,
        "description": __description__,
        "author": __author__,
        "license": __license__,
    }


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse a semantic version string.

    Args:
        version_str: Version string like '1.2.3' or '1.2.3+build'

    Returns:
        Tuple of (major, minor, patch)

    Raises:
        ValueError: If version string is invalid
    """
    # Remove build metadata if present
    if "+" in version_str:
        version_str = version_str.split("+")[0]

    # Remove pre-release info if present
    if "-" in version_str:
        version_str = version_str.split("-")[0]

    parts = version_str.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version string: {version_str}")

    try:
        return tuple(map(int, parts))
    except ValueError as e:
        raise ValueError(f"Invalid version string: {version_str}") from e


def bump_version(component: str = "patch") -> str:
    """Calculate the next version number.

    Args:
        component: Which version component to bump ('major', 'minor', 'patch')

    Returns:
        The new version string

    Raises:
        ValueError: If component is invalid
    """
    major, minor, patch = VERSION_INFO

    if component == "major":
        return f"{major + 1}.0.0"
    elif component == "minor":
        return f"{major}.{minor + 1}.0"
    elif component == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(
            f"Invalid component: {component}. Must be 'major', 'minor', or 'patch'"
        )


# Convenience exports
version = __version__
version_string = get_version_string(include_build=True)
version_info = VERSION_INFO
