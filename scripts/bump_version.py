#!/usr/bin/env python3
"""Version bumping automation for mcp-browser.

This script handles semantic version bumping, changelog updates,
and git tagging for releases.

Usage:
    python scripts/bump_version.py patch  # Bump patch version (1.0.1 -> 1.0.2)
    python scripts/bump_version.py minor  # Bump minor version (1.0.1 -> 1.1.0)
    python scripts/bump_version.py major  # Bump major version (1.0.1 -> 2.0.0)
    python scripts/bump_version.py --dry-run patch  # Preview changes without applying
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse semantic version string into components."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    return tuple(map(int, match.groups()))


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version components into string."""
    return f"{major}.{minor}.{patch}"


def read_current_version() -> str:
    """Read current version from VERSION file."""
    version_file = PROJECT_ROOT / "VERSION"
    if not version_file.exists():
        raise FileNotFoundError(f"VERSION file not found at {version_file}")
    return version_file.read_text().strip()


def bump_version(current: str, component: str) -> str:
    """Calculate new version based on component to bump."""
    major, minor, patch = parse_version(current)

    if component == 'major':
        return format_version(major + 1, 0, 0)
    elif component == 'minor':
        return format_version(major, minor + 1, 0)
    elif component == 'patch':
        return format_version(major, minor, patch + 1)
    else:
        raise ValueError(f"Invalid component: {component}")


def update_version_file(new_version: str, dry_run: bool = False) -> None:
    """Update VERSION file with new version."""
    version_file = PROJECT_ROOT / "VERSION"
    if not dry_run:
        version_file.write_text(new_version)
    print(f"{'Would update' if dry_run else 'Updated'} VERSION file: {new_version}")


def update_python_version(new_version: str, dry_run: bool = False) -> None:
    """Update version in Python source files."""
    # Update src/_version.py
    version_py = PROJECT_ROOT / "src" / "_version.py"
    if version_py.exists():
        content = version_py.read_text()
        updated = re.sub(
            r'^__version__ = ["\'][\d.]+["\']',
            f'__version__ = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        if not dry_run:
            version_py.write_text(updated)
        print(f"{'Would update' if dry_run else 'Updated'} src/_version.py")

    # Update src/__init__.py
    init_py = PROJECT_ROOT / "src" / "__init__.py"
    if init_py.exists():
        content = init_py.read_text()
        updated = re.sub(
            r'^__version__ = ["\'][\d.]+["\']',
            f'__version__ = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        if not dry_run:
            init_py.write_text(updated)
        print(f"{'Would update' if dry_run else 'Updated'} src/__init__.py")


def update_pyproject_toml(new_version: str, dry_run: bool = False) -> None:
    """Update version in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        updated = re.sub(
            r'^version = ["\'][\d.]+["\']',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        if not dry_run:
            pyproject.write_text(updated)
        print(f"{'Would update' if dry_run else 'Updated'} pyproject.toml")


def update_setup_py(new_version: str, dry_run: bool = False) -> None:
    """Update version in setup.py."""
    setup_py = PROJECT_ROOT / "setup.py"
    if setup_py.exists():
        content = setup_py.read_text()
        updated = re.sub(
            r'version=["\'][\d.]+["\']',
            f'version="{new_version}"',
            content
        )
        if not dry_run:
            setup_py.write_text(updated)
        print(f"{'Would update' if dry_run else 'Updated'} setup.py")


def update_changelog(new_version: str, dry_run: bool = False) -> None:
    """Add new version entry to CHANGELOG.md."""
    changelog = PROJECT_ROOT / "CHANGELOG.md"

    if not changelog.exists():
        # Create initial changelog
        content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{new_version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- Initial version with semantic versioning support

### Changed
- Implemented centralized version management

### Fixed
- Version consistency across all package files
"""
        if not dry_run:
            changelog.write_text(content)
        print(f"{'Would create' if dry_run else 'Created'} CHANGELOG.md")
    else:
        content = changelog.read_text()

        # Check if Unreleased section exists
        if '## [Unreleased]' in content:
            # Insert new version after Unreleased
            date_str = datetime.now().strftime('%Y-%m-%d')
            new_section = f"\n## [{new_version}] - {date_str}\n"
            updated = content.replace(
                '## [Unreleased]',
                f'## [Unreleased]\n{new_section}'
            )
        else:
            # Add new version at the top
            date_str = datetime.now().strftime('%Y-%m-%d')
            lines = content.split('\n')
            # Find the first version entry
            for i, line in enumerate(lines):
                if line.startswith('## ['):
                    lines.insert(i, f"## [{new_version}] - {date_str}\n")
                    break
            updated = '\n'.join(lines)

        if not dry_run:
            changelog.write_text(updated)
        print(f"{'Would update' if dry_run else 'Updated'} CHANGELOG.md")


def create_git_tag(version: str, dry_run: bool = False) -> None:
    """Create git tag for the new version."""
    tag = f"v{version}"

    if not dry_run:
        try:
            # Check if tag already exists
            result = subprocess.run(
                ['git', 'tag', '-l', tag],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )

            if result.stdout.strip():
                print(f"Warning: Tag {tag} already exists")
                return

            # Create annotated tag
            subprocess.run(
                ['git', 'tag', '-a', tag, '-m', f"Release version {version}"],
                check=True,
                cwd=PROJECT_ROOT
            )
            print(f"Created git tag: {tag}")

        except subprocess.CalledProcessError as e:
            print(f"Error creating git tag: {e}", file=sys.stderr)
            raise
    else:
        print(f"Would create git tag: {tag}")


def commit_changes(version: str, dry_run: bool = False) -> None:
    """Commit version bump changes."""
    if not dry_run:
        try:
            # Add all version-related files
            files = [
                "VERSION",
                "src/_version.py",
                "src/__init__.py",
                "pyproject.toml",
                "setup.py",
                "CHANGELOG.md"
            ]

            # Filter existing files
            existing_files = [f for f in files if (PROJECT_ROOT / f).exists()]

            # Stage files
            subprocess.run(
                ['git', 'add'] + existing_files,
                check=True,
                cwd=PROJECT_ROOT
            )

            # Commit
            commit_message = f"Bump version to {version}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                check=True,
                cwd=PROJECT_ROOT
            )
            print(f"Committed changes: {commit_message}")

        except subprocess.CalledProcessError as e:
            print(f"Error committing changes: {e}", file=sys.stderr)
            print("You may need to commit manually")
    else:
        print(f"Would commit changes: Bump version to {version}")


def validate_git_status() -> bool:
    """Check if git working directory is clean."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

        if result.stdout.strip():
            print("Warning: Git working directory has uncommitted changes")
            print("It's recommended to commit or stash changes before bumping version")
            response = input("Continue anyway? (y/N): ")
            return response.lower() == 'y'

        return True

    except subprocess.CalledProcessError:
        print("Warning: Not a git repository or git not available")
        return True


def main():
    """Main entry point for version bumping."""
    parser = argparse.ArgumentParser(
        description="Bump version for mcp-browser project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'component',
        choices=['major', 'minor', 'patch'],
        help='Version component to bump'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )

    parser.add_argument(
        '--no-git',
        action='store_true',
        help='Skip git operations (commit and tag)'
    )

    parser.add_argument(
        '--no-changelog',
        action='store_true',
        help='Skip changelog update'
    )

    args = parser.parse_args()

    try:
        # Validate git status unless skipping git operations
        if not args.no_git and not args.dry_run:
            if not validate_git_status():
                print("Aborted.")
                return 1

        # Read current version
        current_version = read_current_version()
        print(f"Current version: {current_version}")

        # Calculate new version
        new_version = bump_version(current_version, args.component)
        print(f"New version: {new_version}")

        if args.dry_run:
            print("\n--- DRY RUN MODE ---")

        # Update all version references
        print("\nUpdating version files...")
        update_version_file(new_version, args.dry_run)
        update_python_version(new_version, args.dry_run)
        update_pyproject_toml(new_version, args.dry_run)
        update_setup_py(new_version, args.dry_run)

        # Update changelog
        if not args.no_changelog:
            print("\nUpdating changelog...")
            update_changelog(new_version, args.dry_run)

        # Git operations
        if not args.no_git:
            print("\nGit operations...")
            commit_changes(new_version, args.dry_run)
            create_git_tag(new_version, args.dry_run)

            if not args.dry_run:
                print(f"\n✅ Successfully bumped version to {new_version}")
                print(f"Don't forget to push the tag: git push origin v{new_version}")
            else:
                print(f"\n✅ Dry run completed. Would bump version to {new_version}")
        else:
            print(f"\n✅ Version bumped to {new_version} (git operations skipped)")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())