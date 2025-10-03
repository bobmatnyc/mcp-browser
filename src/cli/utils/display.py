"""Display utilities for CLI output."""

import sys

from rich.console import Console

from ..._version import get_version_info

# Create console for rich output
console = Console()


def show_version_info():
    """Display detailed version and build information."""
    info = get_version_info()

    print(f"MCP Browser v{info['version']}")
    print(f"{'=' * 40}")
    print(f"Version:        {info['full_version']}")
    print(f"  Major:        {info['major']}")
    print(f"  Minor:        {info['minor']}")
    print(f"  Patch:        {info['patch']}")
    print()
    print("Build Info:")
    print(f"  Date:         {info['build_date']}")
    if info["git_commit"]:
        print(f"  Git Commit:   {info['git_commit']}")
    if info["git_branch"]:
        print(f"  Git Branch:   {info['git_branch']}")
    if info["git_dirty"]:
        print("  Git Status:   Modified (uncommitted changes)")
    print(
        f"  Environment:  {'Development' if info['is_development'] else 'Production'}"
    )
    print()
    print("Project Info:")
    print(f"  Title:        {info['title']}")
    print(f"  Description:  {info['description']}")
    print(f"  Author:       {info['author']}")
    print(f"  License:      {info['license']}")
    print()
    print(f"Python:         {sys.version.split()[0]}")
    print(f"Platform:       {sys.platform}")
    print(f"{'=' * 40}")
