# Release Quick Start Guide

Fast reference for releasing mcp-browser.

## 30-Second Release

```bash
# 1. Ensure clean state
git status  # Should be clean

# 2. Test the release
make release-script-dry-run

# 3. Execute release
make release-script-patch  # or minor/major
```

## Prerequisites (One-Time Setup)

### Create `.env.local`
```bash
cat > .env.local <<EOF
PYPI_TOKEN=pypi-your-token-here
GITHUB_TOKEN=ghp_your-token-here
GITHUB_OWNER=your-github-username
EOF
```

### Install Tools
```bash
# Install Python dependencies
pip install -e ".[dev]"

# Install GitHub CLI
brew install gh  # macOS
# or: sudo apt install gh  # Ubuntu
```

## Common Release Commands

```bash
# Patch release (2.0.10 -> 2.0.11)
make release-script-patch

# Minor release (2.0.10 -> 2.1.0)
make release-script-minor

# Major release (2.0.10 -> 3.0.0)
make release-script-major

# Test without changes
make release-script-dry-run

# Skip tests (faster, use cautiously)
make release-script-skip-tests

# Local only (no GitHub)
make release-script-skip-push
```

## Pre-Release Checklist

- [ ] Tests passing: `make test`
- [ ] CHANGELOG.md updated
- [ ] Git status clean: `git status`
- [ ] On main branch: `git branch --show-current`
- [ ] `.env.local` configured

## What the Script Does

1. ✅ Validates environment and git state
2. ✅ Runs linting, formatting, type checks
3. ✅ Runs full test suite
4. ✅ Scans for security issues
5. ✅ Bumps version in all files
6. ✅ Commits version changes
7. ✅ Builds distribution packages
8. ✅ Publishes to PyPI
9. ✅ Pushes to GitHub
10. ✅ Creates GitHub release
11. ✅ Verifies deployment

## If Something Goes Wrong

### Quality Gate Fails
```bash
# Fix issues
ruff check --fix src/
ruff format src/

# Retry
make release-script-patch
```

### Reset Version Bump
```bash
# Before PyPI publish
git reset --hard HEAD~1
make clean
```

### Re-run After Partial Failure
```bash
# Script handles this gracefully
make release-script-patch  # Will skip already-published PyPI
```

## Post-Release

1. Verify PyPI: https://pypi.org/project/mcp-browser/
2. Verify GitHub: https://github.com/your-org/mcp-browser/releases
3. Test install: `pip install mcp-browser==X.Y.Z`
4. Update Homebrew (if applicable)

## Getting Help

```bash
# Show help
python scripts/release.py --help

# Test with dry-run
python scripts/release.py --dry-run patch

# Check Makefile targets
make help
```

## Full Documentation

See [RELEASE_SCRIPT.md](RELEASE_SCRIPT.md) for comprehensive documentation.
