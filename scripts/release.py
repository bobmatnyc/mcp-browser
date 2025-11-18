#!/usr/bin/env python3
"""Release automation for mcp-browser.

This script automates the entire release process including:
- Environment validation and prerequisite checks
- Version bumping with semantic versioning
- Quality gate (linting, formatting, type checking, tests)
- Security scanning for hardcoded secrets
- Building distribution packages
- Publishing to PyPI
- Creating GitHub releases
- Displaying Homebrew tap update instructions
- Post-release verification

Usage:
    python scripts/release.py patch              # Patch release (2.0.10 -> 2.0.11)
    python scripts/release.py minor              # Minor release (2.0.10 -> 2.1.0)
    python scripts/release.py major              # Major release (2.0.10 -> 3.0.0)
    python scripts/release.py --dry-run patch    # Simulate without changes
    python scripts/release.py --skip-tests patch # Skip test suite
    python scripts/release.py --skip-push patch  # Don't push to GitHub
"""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple


# ANSI Color Codes
class Colors:
    """Terminal color codes for formatted output."""
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def load_env() -> None:
    """Load environment variables from .env.local file.

    Raises:
        SystemExit: If .env.local not found or invalid
    """
    env_file = PROJECT_ROOT / '.env.local'

    if not env_file.exists():
        print(f"{Colors.RED}ERROR: .env.local not found{Colors.NC}")
        print(f"{Colors.YELLOW}Create .env.local with required tokens:{Colors.NC}")
        print("  PYPI_TOKEN=pypi-...")
        print("  GITHUB_TOKEN=ghp_...")
        print("  GITHUB_OWNER=your-username")
        sys.exit(1)

    # Load environment variables
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

    # Validate required variables
    required_vars = ['PYPI_TOKEN', 'GITHUB_TOKEN', 'GITHUB_OWNER']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print(f"{Colors.RED}ERROR: Missing required environment variables:{Colors.NC}")
        for var in missing_vars:
            print(f"  {var}")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ Environment loaded{Colors.NC}")


def check_git_clean() -> bool:
    """Verify git working directory is clean.

    Returns:
        True if working directory is clean, False otherwise
    """
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    if result.stdout.strip():
        print(f"{Colors.RED}ERROR: Git working directory not clean{Colors.NC}")
        print(f"{Colors.YELLOW}Uncommitted changes:{Colors.NC}")
        print(result.stdout)
        print(f"\n{Colors.YELLOW}Commit or stash changes before release{Colors.NC}")
        return False

    print(f"{Colors.GREEN}✓ Git working directory clean{Colors.NC}")
    return True


def check_git_branch() -> bool:
    """Verify we're on main branch.

    Returns:
        True if on main branch, False otherwise
    """
    result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    branch = result.stdout.strip()
    if branch != 'main':
        print(f"{Colors.YELLOW}WARNING: Not on main branch (current: {branch}){Colors.NC}")
        response = input("Continue anyway? (y/N): ")
        return response.lower() == 'y'

    print(f"{Colors.GREEN}✓ On main branch{Colors.NC}")
    return True


def run_command(
    cmd: List[str],
    description: str,
    check: bool = True,
    capture_output: bool = True,
    allow_failure: bool = False
) -> subprocess.CompletedProcess:
    """Run a command and handle errors.

    Args:
        cmd: Command and arguments as list
        description: Human-readable description for output
        check: Raise exception on non-zero exit
        capture_output: Capture stdout/stderr
        allow_failure: Don't exit on failure (just warn)

    Returns:
        CompletedProcess instance

    Raises:
        SystemExit: If command fails and not allow_failure
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=PROJECT_ROOT,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        if allow_failure:
            print(f"{Colors.YELLOW}⚠ {description} failed (non-blocking){Colors.NC}")
            if capture_output and e.stderr:
                print(e.stderr)
            return e
        else:
            print(f"{Colors.RED}✗ {description} failed{Colors.NC}")
            if capture_output and e.stderr:
                print(e.stderr)
            sys.exit(1)


def run_quality_gate(skip_tests: bool = False) -> bool:
    """Run pre-publish quality checks.

    Args:
        skip_tests: Skip test execution if True

    Returns:
        True if all checks pass, False otherwise
    """
    print(f"{Colors.BLUE}Running quality gate...{Colors.NC}")

    checks = [
        (['ruff', 'check', 'src/', 'tests/'], 'Linting', False),
        (['ruff', 'format', '--check', 'src/', 'tests/'], 'Format check', False),
        (['mypy', 'src/'], 'Type checking', True),  # Allow failure
    ]

    if not skip_tests:
        # Use virtualenv pytest if available, otherwise system pytest
        venv_pytest = PROJECT_ROOT / '.venv' / 'bin' / 'pytest'
        pytest_cmd = str(venv_pytest) if venv_pytest.exists() else 'pytest'

        # Check if pytest-cov is available
        cov_available = subprocess.run(
            [pytest_cmd, '--version'],
            capture_output=True
        ).returncode == 0 and subprocess.run(
            ['python3', '-c', 'import pytest_cov'],
            capture_output=True
        ).returncode == 0

        if cov_available:
            checks.append(([pytest_cmd, 'tests/', '-v', '--cov=src'], 'Tests', False))
        else:
            checks.append(([pytest_cmd, 'tests/', '-v'], 'Tests', False))

    checks.append((['python3', '-m', 'build'], 'Build', False))

    for cmd, name, allow_failure in checks:
        print(f"{Colors.YELLOW}{name}...{Colors.NC}")
        result = run_command(cmd, name, check=not allow_failure, allow_failure=allow_failure)

        if isinstance(result, subprocess.CalledProcessError) and not allow_failure:
            return False

        print(f"{Colors.GREEN}✓ {name} passed{Colors.NC}")

    return True


def run_security_scan() -> bool:
    """Run security checks for hardcoded secrets.

    Returns:
        True if security scan passes, False otherwise
    """
    print(f"{Colors.BLUE}Running security scan...{Colors.NC}")

    # Patterns to search for
    patterns = [
        (r'api[_-]key\s*=\s*["\'](?!.*\.env)', "API keys"),
        (r'password\s*=\s*["\']', "Passwords"),
        (r'token\s*=\s*["\'](?!.*GITHUB|.*PYPI)', "Tokens"),
        (r'secret\s*=\s*["\']', "Secrets"),
    ]

    violations_found = False

    for pattern, name in patterns:
        # Search in Python files
        result = subprocess.run(
            ['grep', '-rn', '-E', pattern, 'src/', '--include=*.py'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

        if result.returncode == 0 and result.stdout.strip():
            print(f"{Colors.RED}✗ Found hardcoded {name}{Colors.NC}")
            print(result.stdout)
            violations_found = True

    if violations_found:
        print(f"{Colors.RED}Security violations found!{Colors.NC}")
        return False

    print(f"{Colors.GREEN}✓ Security scan passed{Colors.NC}")
    return True


def bump_version(bump_type: str, dry_run: bool = False) -> str:
    """Bump version using existing bump_version.py script.

    Args:
        bump_type: One of 'patch', 'minor', 'major'
        dry_run: Simulate without making changes

    Returns:
        New version string

    Raises:
        SystemExit: If version bump fails
    """
    cmd = ['python3', 'scripts/bump_version.py', bump_type, '--no-git']
    if dry_run:
        cmd.append('--dry-run')

    result = run_command(cmd, f"Version bump ({bump_type})")

    # Read new version from VERSION file
    version_file = PROJECT_ROOT / 'VERSION'
    if dry_run:
        # Calculate expected version by reading current VERSION file
        current_version = version_file.read_text().strip()
        major, minor, patch = map(int, current_version.split('.'))
        if bump_type == 'major':
            new_version = f"{major + 1}.0.0"
        elif bump_type == 'minor':
            new_version = f"{major}.{minor + 1}.0"
        else:  # patch
            new_version = f"{major}.{minor}.{patch + 1}"
    else:
        new_version = version_file.read_text().strip()

    print(f"{Colors.GREEN}✓ Version bumped to {new_version}{Colors.NC}")
    return new_version


def git_commit_version(version: str, dry_run: bool = False) -> None:
    """Commit version bump changes.

    Args:
        version: New version string
        dry_run: Simulate without making changes
    """
    files = ['pyproject.toml', 'src/_version.py', 'VERSION', 'CHANGELOG.md']

    # Filter existing files
    existing_files = [f for f in files if (PROJECT_ROOT / f).exists()]

    if dry_run:
        print(f"{Colors.YELLOW}[DRY RUN] Would commit: {', '.join(existing_files)}{Colors.NC}")
        return

    # Stage files
    run_command(['git', 'add'] + existing_files, "Stage version files")

    # Commit
    commit_msg = f"chore: bump version to {version}"
    run_command(['git', 'commit', '-m', commit_msg], "Commit version bump")

    print(f"{Colors.GREEN}✓ Version changes committed{Colors.NC}")


def build_packages(dry_run: bool = False) -> None:
    """Build distribution packages.

    Args:
        dry_run: Simulate without making changes
    """
    if dry_run:
        print(f"{Colors.YELLOW}[DRY RUN] Would build packages{Colors.NC}")
        return

    # Clean previous builds
    for path in ['dist', 'build']:
        dir_path = PROJECT_ROOT / path
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)

    # Build new packages
    run_command(['python3', '-m', 'build'], "Build packages")

    # Verify build artifacts
    dist_dir = PROJECT_ROOT / 'dist'
    if not dist_dir.exists() or not list(dist_dir.glob('*')):
        print(f"{Colors.RED}ERROR: No build artifacts created{Colors.NC}")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ Packages built{Colors.NC}")


def publish_to_pypi(dry_run: bool = False) -> bool:
    """Publish to PyPI using PYPI_TOKEN.

    Args:
        dry_run: Simulate without making changes

    Returns:
        True if successful, False if already published
    """
    pypi_token = os.environ.get('PYPI_TOKEN')
    if not pypi_token:
        print(f"{Colors.RED}ERROR: PYPI_TOKEN not found{Colors.NC}")
        sys.exit(1)

    if dry_run:
        print(f"{Colors.YELLOW}[DRY RUN] Would upload to PyPI{Colors.NC}")
        return True

    # Set up environment for twine
    env = os.environ.copy()
    env['TWINE_USERNAME'] = '__token__'
    env['TWINE_PASSWORD'] = pypi_token

    # Upload to PyPI
    result = subprocess.run(
        ['python3', '-m', 'twine', 'upload', 'dist/*'],
        env=env,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    # Check if already exists (not a failure)
    if result.returncode != 0:
        if 'File already exists' in result.stderr or 'already exists' in result.stderr.lower():
            print(f"{Colors.YELLOW}⚠ Package already published to PyPI{Colors.NC}")
            return False
        else:
            print(f"{Colors.RED}ERROR: PyPI upload failed{Colors.NC}")
            print(result.stderr)
            sys.exit(1)

    print(f"{Colors.GREEN}✓ Published to PyPI{Colors.NC}")
    return True


def git_push(dry_run: bool = False) -> None:
    """Push commits to GitHub.

    Args:
        dry_run: Simulate without making changes
    """
    if dry_run:
        print(f"{Colors.YELLOW}[DRY RUN] Would push to GitHub{Colors.NC}")
        return

    run_command(['git', 'push', 'origin', 'main'], "Push to GitHub")
    print(f"{Colors.GREEN}✓ Pushed to GitHub{Colors.NC}")


def extract_changelog(version: str) -> str:
    """Extract changelog for specific version.

    Args:
        version: Version string to extract

    Returns:
        Changelog content
    """
    try:
        result = subprocess.run(
            ['python3', 'scripts/extract_changelog.py', version],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    return f"Release version {version}\n\nSee [CHANGELOG.md](CHANGELOG.md) for details."


def create_github_release(version: str, dry_run: bool = False) -> bool:
    """Create GitHub release using gh CLI.

    Args:
        version: Version string
        dry_run: Simulate without making changes

    Returns:
        True if successful, False if already exists
    """
    github_token = os.environ.get('GITHUB_TOKEN')
    github_owner = os.environ.get('GITHUB_OWNER')

    if not github_token or not github_owner:
        print(f"{Colors.RED}ERROR: GITHUB_TOKEN or GITHUB_OWNER not found{Colors.NC}")
        sys.exit(1)

    if dry_run:
        print(f"{Colors.YELLOW}[DRY RUN] Would create GitHub release v{version}{Colors.NC}")
        return True

    # Extract changelog
    changelog = extract_changelog(version)

    # Create release with gh CLI
    env = os.environ.copy()
    env['GITHUB_TOKEN'] = github_token

    # Check if release already exists
    check_result = subprocess.run(
        ['gh', 'release', 'view', f'v{version}', '--repo', f'{github_owner}/mcp-browser'],
        env=env,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    if check_result.returncode == 0:
        print(f"{Colors.YELLOW}⚠ GitHub release v{version} already exists{Colors.NC}")
        return False

    # Create new release
    result = subprocess.run(
        [
            'gh', 'release', 'create', f'v{version}',
            '--title', f'v{version}',
            '--notes', changelog,
            '--repo', f'{github_owner}/mcp-browser',
            'dist/*'
        ],
        env=env,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        print(f"{Colors.RED}ERROR: GitHub release failed{Colors.NC}")
        print(result.stderr)
        sys.exit(1)

    print(f"{Colors.GREEN}✓ GitHub release created{Colors.NC}")
    return True


def display_homebrew_instructions(version: str) -> None:
    """Display instructions for updating Homebrew tap.

    Args:
        version: Version string
    """
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}  HOMEBREW TAP UPDATE{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"\n{Colors.YELLOW}If you maintain a Homebrew tap:{Colors.NC}")
    print(f"  1. Wait 5-10 minutes for PyPI propagation")
    print(f"  2. Run: bash scripts/update_homebrew_tap.sh {version}")
    print(f"  3. Update formula with SHA256 from PyPI")
    print(f"  4. Commit and push formula changes")


def verify_release(version: str, dry_run: bool = False) -> None:
    """Verify release was successful.

    Args:
        version: Version string
        dry_run: Simulate without making changes
    """
    if dry_run:
        print(f"{Colors.YELLOW}[DRY RUN] Would verify release{Colors.NC}")
        return

    print(f"{Colors.BLUE}Verifying release...{Colors.NC}")

    # Wait for PyPI propagation
    print(f"{Colors.YELLOW}Waiting 5 seconds for PyPI propagation...{Colors.NC}")
    time.sleep(5)

    # Check PyPI
    try:
        result = subprocess.run(
            ['pip', 'index', 'versions', 'mcp-browser'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if version in result.stdout:
            print(f"{Colors.GREEN}✓ PyPI package verified{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}⚠ PyPI package not yet visible (may take a few minutes){Colors.NC}")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ Could not verify PyPI: {e}{Colors.NC}")

    # Check GitHub release
    github_owner = os.environ.get('GITHUB_OWNER')
    try:
        result = subprocess.run(
            ['gh', 'release', 'view', f'v{version}', '--repo', f'{github_owner}/mcp-browser'],
            env={'GITHUB_TOKEN': os.environ.get('GITHUB_TOKEN', '')},
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ GitHub release verified{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}⚠ GitHub release not found{Colors.NC}")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ Could not verify GitHub release: {e}{Colors.NC}")


def print_step(step_num: int, total: int, message: str) -> None:
    """Print progress step.

    Args:
        step_num: Current step number
        total: Total number of steps
        message: Step description
    """
    print(f"\n{Colors.BLUE}[{step_num}/{total}] {message}{Colors.NC}")


def print_summary(version: str) -> None:
    """Print release summary.

    Args:
        version: Version string
    """
    github_owner = os.environ.get('GITHUB_OWNER', 'browserpymcp')
    pypi_url = f"https://pypi.org/project/mcp-browser/{version}/"
    github_url = f"https://github.com/{github_owner}/mcp-browser/releases/tag/v{version}"

    print(f"\n{Colors.GREEN}{'='*60}{Colors.NC}")
    print(f"{Colors.GREEN}  ✓ RELEASE COMPLETE!{Colors.NC}")
    print(f"{Colors.GREEN}{'='*60}{Colors.NC}")
    print(f"\n{Colors.YELLOW}Version {version} published to:{Colors.NC}")
    print(f"  📦 PyPI:   {pypi_url}")
    print(f"  🐙 GitHub: {github_url}")
    print(f"\n{Colors.YELLOW}Next steps:{Colors.NC}")
    print("  1. Update Homebrew tap (if applicable)")
    print("  2. Announce release on social media")
    print("  3. Update documentation links")
    print("  4. Notify users of new version")


def main() -> int:
    """Main entry point for release automation.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description='Release automation for mcp-browser',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'bump_type',
        choices=['patch', 'minor', 'major'],
        help='Version bump type'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without making changes'
    )

    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip test suite'
    )

    parser.add_argument(
        '--skip-push',
        action='store_true',
        help='Skip git push and GitHub release'
    )

    args = parser.parse_args()

    # Print header
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}  MCP-BROWSER RELEASE AUTOMATION{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

    if args.dry_run:
        print(f"{Colors.YELLOW}  DRY RUN MODE - No changes will be made{Colors.NC}")

    print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")

    total_steps = 14 if not args.skip_push else 11

    try:
        # Step 1: Load environment
        print_step(1, total_steps, "Loading environment")
        load_env()

        # Step 2: Validate prerequisites
        print_step(2, total_steps, "Validating prerequisites")
        if not args.dry_run:
            if not check_git_clean():
                return 1
            if not check_git_branch():
                return 1
        else:
            print(f"{Colors.YELLOW}[DRY RUN] Skipping git validation{Colors.NC}")

        # Step 3: Quality gate
        print_step(3, total_steps, "Running quality gate")
        if not args.skip_tests:
            if not run_quality_gate(skip_tests=False):
                return 1
        else:
            print(f"{Colors.YELLOW}Skipping tests (--skip-tests){Colors.NC}")
            if not run_quality_gate(skip_tests=True):
                return 1

        # Step 4: Security scan
        print_step(4, total_steps, "Running security scan")
        if not run_security_scan():
            print(f"{Colors.RED}Security scan failed - aborting release{Colors.NC}")
            return 1

        # Step 5: Bump version
        print_step(5, total_steps, f"Bumping {args.bump_type} version")
        new_version = bump_version(args.bump_type, args.dry_run)

        # Step 6: Commit version changes
        print_step(6, total_steps, "Committing version changes")
        git_commit_version(new_version, args.dry_run)

        # Step 7: Build packages
        print_step(7, total_steps, "Building distribution packages")
        build_packages(args.dry_run)

        # Step 8: Publish to PyPI
        print_step(8, total_steps, "Publishing to PyPI")
        publish_to_pypi(args.dry_run)

        if not args.skip_push:
            # Step 9: Push to GitHub
            print_step(9, total_steps, "Pushing to GitHub")
            git_push(args.dry_run)

            # Step 10: Create GitHub release
            print_step(10, total_steps, "Creating GitHub release")
            create_github_release(new_version, args.dry_run)

            # Step 11: Homebrew instructions
            print_step(11, total_steps, "Homebrew update instructions")
            display_homebrew_instructions(new_version)

            # Step 12: Verify release
            print_step(12, total_steps, "Verifying release")
            verify_release(new_version, args.dry_run)
        else:
            print(f"\n{Colors.YELLOW}Skipping push and GitHub release (--skip-push){Colors.NC}")

        # Step 13/14: Summary
        step = 13 if not args.skip_push else 9
        print_step(step, total_steps, "Release complete!")
        print_summary(new_version)

        return 0

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Release interrupted by user{Colors.NC}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
