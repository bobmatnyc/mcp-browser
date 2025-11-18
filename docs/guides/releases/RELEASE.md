# Release Automation Guide

This guide explains how to use the automated release workflow for mcp-browser.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Release Workflow](#release-workflow)
- [Individual Commands](#individual-commands)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

1. **Python 3.10+** - For running the project
2. **pip** - Python package manager
3. **twine** - For uploading to PyPI (`pip install twine`)
4. **gh CLI** - GitHub CLI tool (`brew install gh` or see [GitHub CLI](https://cli.github.com/))
5. **git** - Version control

### Required Credentials

Create a `.env.local` file in the project root (copy from `.env.local.template`):

```bash
cp .env.local.template .env.local
```

Then fill in the required credentials:

```bash
# .env.local

# PyPI Token (Required for publishing)
# Get from: https://pypi.org/manage/account/token/
PYPI_TOKEN=pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# GitHub Token (Required for GitHub releases)
# Get from: https://github.com/settings/tokens
# Required scopes: repo, write:packages
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# GitHub Repository Owner (Optional, defaults to "browserpymcp")
GITHUB_OWNER=browserpymcp
```

### Get PyPI Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: "mcp-browser release automation"
4. Scope: "Entire account" or "Project: mcp-browser"
5. Copy the token (starts with `pypi-`)
6. Add to `.env.local`

### Get GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "mcp-browser release automation"
4. Scopes: Select `repo` and `write:packages`
5. Click "Generate token"
6. Copy the token (starts with `ghp_` or `github_pat_`)
7. Add to `.env.local`

## Quick Start

### Complete Release (Recommended)

For a standard patch release (e.g., 2.0.10 → 2.0.11):

```bash
make release-patch
```

This single command will:
1. ✅ Run quality gate (linting, formatting, type checking, tests)
2. ✅ Run security scan (secret detection, vulnerability scan)
3. ✅ Bump patch version
4. ✅ Update VERSION, pyproject.toml, src/_version.py, CHANGELOG.md
5. ✅ Commit changes with message "chore: bump version to X.Y.Z"
6. ✅ Build package (sdist and wheel)
7. ✅ Upload to PyPI
8. ✅ Push to GitHub
9. ✅ Create GitHub release with changelog
10. ✅ Display Homebrew tap update instructions

### Other Release Types

```bash
# Minor release (e.g., 2.0.10 → 2.1.0)
make release-minor

# Major release (e.g., 2.0.10 → 3.0.0)
make release-major
```

## Release Workflow

### Step-by-Step Breakdown

#### 1. Pre-Release Quality Gate

```bash
make release-prep
```

This runs:
- **Linting**: `ruff check src/ tests/`
- **Formatting**: `ruff format --check src/ tests/`
- **Type Checking**: `mypy src/` (warnings are non-blocking)
- **Tests**: `pytest tests/ -v --cov=src`
- **Build**: `python -m build`
- **Security Scan**: Check for hardcoded secrets and vulnerabilities

If any check fails, the release is aborted.

#### 2. Version Bump

```bash
# Patch: 2.0.10 → 2.0.11
make bump-and-commit-patch

# Minor: 2.0.10 → 2.1.0
make bump-and-commit-minor

# Major: 2.0.10 → 3.0.0
make bump-and-commit-major
```

This updates:
- `VERSION` file
- `pyproject.toml`
- `src/_version.py`
- `CHANGELOG.md` (adds new version entry)

Then commits with message: `chore: bump version to X.Y.Z`

#### 3. Publish to PyPI

```bash
make publish-pypi
```

- Checks for `PYPI_TOKEN` in `.env.local`
- Uploads dist/* to PyPI using twine
- Displays PyPI URL on success

#### 4. Create GitHub Release

```bash
make github-release
```

- Checks for `GITHUB_TOKEN` in `.env.local`
- Creates release tag `vX.Y.Z`
- Extracts changelog for this version
- Uploads dist/* as release assets
- Displays GitHub release URL

#### 5. Update Homebrew Tap

```bash
make update-homebrew
```

- Fetches package SHA256 from PyPI
- Displays instructions for updating Homebrew formula

#### 6. Verify Release

```bash
make verify-release
```

- Tests PyPI installation: `pip install --upgrade mcp-browser==X.Y.Z`
- Verifies GitHub release exists
- Reports status

## Individual Commands

### Quality Assurance

```bash
# Run only quality checks (no security scan)
make pre-publish

# Run only security scan
make security-scan
```

### Version Management

```bash
# Bump version WITHOUT committing
make bump-patch
make bump-minor
make bump-major

# Check version consistency across files
make check-version
```

### Publishing

```bash
# Publish to PyPI only (no GitHub release)
make publish-pypi

# Create GitHub release only (no PyPI publish)
make github-release
```

### Post-Release

```bash
# Verify release was successful
make verify-release

# Update Homebrew tap (displays instructions)
make update-homebrew
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PYPI_TOKEN` | PyPI API token for publishing | `pypi-AgEIcHlwaS5vcmc...` |
| `GITHUB_TOKEN` | GitHub personal access token | `ghp_1234567890...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_OWNER` | GitHub repository owner | `browserpymcp` |

### Loading Environment Variables

The Makefile automatically loads `.env.local` if it exists:

```makefile
ifneq (,$(wildcard .env.local))
    include .env.local
    export
endif
```

You can also manually export variables:

```bash
export PYPI_TOKEN=pypi-...
export GITHUB_TOKEN=ghp_...
make release-patch
```

## Troubleshooting

### "PYPI_TOKEN not found in .env.local"

**Solution**: Create `.env.local` and add your PyPI token:

```bash
cp .env.local.template .env.local
# Edit .env.local and add PYPI_TOKEN=pypi-...
```

### "GITHUB_TOKEN not found in .env.local"

**Solution**: Add GitHub token to `.env.local`:

```bash
echo "GITHUB_TOKEN=ghp_..." >> .env.local
```

### "Version already exists on PyPI"

**Solution**: Bump version again or manually fix VERSION file:

```bash
# If you already bumped but didn't publish
# Just run publish steps:
make publish-pypi
make github-release

# If you need to bump again
make bump-and-commit-patch
make publish-pypi
make github-release
```

### "Quality gate failed"

**Solution**: Fix the failing checks:

```bash
# Fix formatting
make format

# Fix linting
make lint-fix

# Run tests
make test

# Try again
make release-prep
```

### "PyPI package not found" during verification

**Solution**: PyPI may take a few minutes to propagate:

```bash
# Wait 2-5 minutes, then retry
make verify-release
```

### "GitHub release already exists"

**Solution**: Delete the release first:

```bash
gh release delete vX.Y.Z --yes
make github-release
```

### Permission Denied for PyPI

**Causes**:
1. Invalid token
2. Token doesn't have project permissions
3. Project name mismatch

**Solution**:
1. Verify token at https://pypi.org/manage/account/token/
2. Ensure token scope includes "mcp-browser" project
3. Regenerate token if needed

### Permission Denied for GitHub

**Causes**:
1. Invalid token
2. Missing `repo` or `write:packages` scopes
3. Not authenticated with `gh` CLI

**Solution**:
1. Check token scopes at https://github.com/settings/tokens
2. Regenerate with correct scopes
3. Authenticate gh CLI: `gh auth login`

### Git Working Directory Not Clean

**Solution**: Commit or stash changes before releasing:

```bash
# Commit changes
git add .
git commit -m "Your message"

# Or stash
git stash

# Then retry
make release-patch
```

## Best Practices

### Before Every Release

1. **Update CHANGELOG.md** manually with changes for this version
2. **Run quality gate**: `make release-prep`
3. **Check git status**: Ensure working directory is clean
4. **Verify tests**: `make test`

### During Release

1. **Use complete workflows**: `make release-patch` (not individual steps)
2. **Monitor output**: Check each step completes successfully
3. **Wait for PyPI**: Allow 2-5 minutes for propagation

### After Release

1. **Verify installation**: `make verify-release`
2. **Test installation**: `pip install --upgrade mcp-browser`
3. **Update Homebrew tap** (if applicable)
4. **Announce release**: Post to GitHub Discussions, Twitter, etc.

### Rollback Strategy

If a release goes wrong:

```bash
# 1. Delete PyPI release (CANNOT BE UNDONE - version is burned)
# Contact PyPI support or use different version

# 2. Delete GitHub release
gh release delete vX.Y.Z --yes

# 3. Delete git tag
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# 4. Revert version bump commit
git revert HEAD
git push origin main

# 5. Fix issues and try again with new version
make release-patch
```

## Advanced Usage

### Dry Run (Testing)

Test version bump without applying changes:

```bash
python scripts/bump_version.py patch --dry-run
```

### Manual Release Process

If you need more control:

```bash
# 1. Quality checks
make release-prep

# 2. Bump version
make bump-and-commit-patch

# 3. Build package
make build

# 4. Publish to PyPI
make publish-pypi

# 5. Push to GitHub
git push origin main

# 6. Create GitHub release
make github-release

# 7. Update Homebrew
make update-homebrew

# 8. Verify
make verify-release
```

### Extract Changelog for Specific Version

```bash
python scripts/extract_changelog.py 2.0.10
python scripts/extract_changelog.py 2.0.10 --markdown
```

### Check Homebrew SHA256 Manually

```bash
bash scripts/update_homebrew_tap.sh 2.0.10
```

## CI/CD Integration

You can integrate these commands into GitHub Actions:

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      version_type:
        description: 'Version type'
        required: true
        type: choice
        options:
          - patch
          - minor
          - major

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: make install

      - name: Create .env.local
        run: |
          echo "PYPI_TOKEN=${{ secrets.PYPI_TOKEN }}" >> .env.local
          echo "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}" >> .env.local

      - name: Release
        run: make release-${{ github.event.inputs.version_type }}
```

## Summary

The release automation provides a **one-command release process**:

```bash
# Patch release (most common)
make release-patch

# Minor release
make release-minor

# Major release
make release-major
```

Each command handles:
- ✅ Quality assurance
- ✅ Security scanning
- ✅ Version bumping
- ✅ Building
- ✅ Publishing to PyPI
- ✅ Creating GitHub release
- ✅ Generating Homebrew instructions

**Happy releasing! 🚀**
