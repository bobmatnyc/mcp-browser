# Release Script Documentation

Complete automation for mcp-browser release workflow.

## Overview

The `scripts/release.py` script automates the entire release process from version bumping to publishing. It handles all quality checks, builds, and deployment steps in a single command.

## Quick Start

```bash
# Dry-run (simulate without changes)
make release-script-dry-run

# Patch release (2.0.10 -> 2.0.11)
make release-script-patch

# Minor release (2.0.10 -> 2.1.0)
make release-script-minor

# Major release (2.0.10 -> 3.0.0)
make release-script-major
```

## Prerequisites

### 1. Environment Configuration

Create `.env.local` with required tokens:

```bash
PYPI_TOKEN=pypi-your-token-here
GITHUB_TOKEN=ghp_your-token-here
GITHUB_OWNER=your-github-username
```

### 2. Required Tools

- Python 3.10+
- Git
- GitHub CLI (`gh`)
- Build tools: `python -m build`, `twine`
- Quality tools: `ruff`, `mypy`, `pytest`

### 3. Clean Git State

```bash
# Verify no uncommitted changes
git status

# Commit or stash changes if needed
git stash
```

## Release Workflow

The script executes 14 steps automatically:

### Step 1: Load Environment
- Reads `.env.local`
- Validates required tokens
- Checks `PYPI_TOKEN`, `GITHUB_TOKEN`, `GITHUB_OWNER`

### Step 2: Validate Prerequisites
- Checks git working directory is clean
- Verifies on main branch (or prompts for confirmation)
- Ensures no uncommitted changes

### Step 3: Quality Gate
- **Linting**: `ruff check src/ tests/`
- **Format check**: `ruff format --check`
- **Type checking**: `mypy src/` (warnings allowed)
- **Tests**: `pytest tests/ -v --cov=src` (if not skipped)
- **Build**: `python -m build`

### Step 4: Security Scan
- Checks for hardcoded secrets:
  - API keys: `api_key = "..."`
  - Passwords: `password = "..."`
  - Tokens: `token = "..."`
- Scans all Python files in `src/`

### Step 5: Bump Version
- Runs `scripts/bump_version.py`
- Updates:
  - `VERSION`
  - `pyproject.toml`
  - `src/_version.py`
  - `CHANGELOG.md`

### Step 6: Commit Version Changes
- Stages version files
- Commits with message: `chore: bump version to X.Y.Z`

### Step 7: Build Distribution Packages
- Cleans `dist/` and `build/` directories
- Builds wheel and sdist
- Verifies artifacts created

### Step 8: Publish to PyPI
- Uploads to PyPI using `twine`
- Uses `PYPI_TOKEN` for authentication
- Handles "already exists" gracefully

### Step 9: Push to GitHub
- Pushes commits to `origin/main`
- Skipped with `--skip-push` flag

### Step 10: Create GitHub Release
- Uses `gh CLI` to create release
- Extracts changelog from `CHANGELOG.md`
- Uploads distribution artifacts
- Skipped with `--skip-push` flag

### Step 11: Homebrew Instructions
- Displays Homebrew tap update steps
- Shows command for updating formula

### Step 12: Verify Release
- Waits 5 seconds for PyPI propagation
- Checks PyPI package availability
- Verifies GitHub release created

### Step 13: Summary
- Displays release URLs
- Shows next steps
- Provides verification links

## Command-Line Options

### Version Bump Type (Required)

```bash
python scripts/release.py patch  # 2.0.10 -> 2.0.11
python scripts/release.py minor  # 2.0.10 -> 2.1.0
python scripts/release.py major  # 2.0.10 -> 3.0.0
```

### Optional Flags

#### `--dry-run`
Simulate entire workflow without making changes:

```bash
python scripts/release.py --dry-run patch
```

What it does:
- ✅ Runs all quality checks
- ✅ Simulates version bump
- ❌ Does NOT commit changes
- ❌ Does NOT build packages
- ❌ Does NOT publish to PyPI
- ❌ Does NOT push to GitHub

Use case: Test workflow before actual release.

#### `--skip-tests`
Skip test execution (faster, less safe):

```bash
python scripts/release.py --skip-tests patch
```

What it skips:
- ❌ `pytest tests/` execution

What it still does:
- ✅ Linting, formatting, type checking
- ✅ Build, publish, release

Use case: Emergency hotfix when tests are already passing.

#### `--skip-push`
Local release without GitHub operations:

```bash
python scripts/release.py --skip-push patch
```

What it skips:
- ❌ `git push origin main`
- ❌ GitHub release creation

What it still does:
- ✅ Version bump, commit
- ✅ Build packages
- ✅ Publish to PyPI

Use case: Test PyPI publishing without GitHub integration.

## Makefile Targets

Convenient shortcuts via `make`:

```bash
# Automated release (recommended)
make release-script-patch    # Patch release via script
make release-script-minor    # Minor release via script
make release-script-major    # Major release via script

# Testing and development
make release-script-dry-run  # Simulate patch release
make release-script-skip-tests    # Skip tests (faster)
make release-script-skip-push     # Local-only release

# Manual workflow (deprecated, use script instead)
make release-patch           # Manual Makefile-based release
make release-minor           # Manual minor release
make release-major           # Manual major release
```

## Error Handling

### Git Not Clean
```
ERROR: Git working directory not clean
Uncommitted changes:
M file1.py
M file2.py
```

**Solution**: Commit or stash changes:
```bash
git add .
git commit -m "chore: prepare for release"
# OR
git stash
```

### Missing Environment Variables
```
ERROR: Missing required environment variables:
  PYPI_TOKEN
  GITHUB_TOKEN
```

**Solution**: Create `.env.local`:
```bash
cat > .env.local <<EOF
PYPI_TOKEN=pypi-your-token-here
GITHUB_TOKEN=ghp_your-token-here
GITHUB_OWNER=your-username
EOF
```

### Quality Gate Failure
```
✗ Linting failed
src/file.py:42: E501 line too long
```

**Solution**: Fix issues and retry:
```bash
# Auto-fix what's possible
ruff check --fix src/
ruff format src/

# Re-run release
make release-script-patch
```

### PyPI Already Exists
```
⚠ Package already published to PyPI
```

**Not an error**: Script continues with GitHub release. This happens when:
- Retrying after partial failure
- Manual PyPI upload already done

### Security Scan Violation
```
✗ Found hardcoded API keys
src/config.py:10: api_key = "sk-1234"
```

**Solution**: Move secrets to environment:
```python
# WRONG
api_key = "sk-1234"

# CORRECT
import os
api_key = os.environ.get("API_KEY")
```

## Rollback Procedures

### Before PyPI Publish
If release fails before Step 8:

```bash
# Reset version bump commit
git reset --hard HEAD~1

# Clean build artifacts
make clean
```

### After PyPI Publish
**Cannot delete PyPI releases!** Instead:

```bash
# Create hotfix release
python scripts/release.py patch  # 2.0.11 -> 2.0.12

# Or yank the broken version (discouraged)
pip install twine
twine upload --skip-existing --repository pypi dist/*
```

### GitHub Release Only
```bash
# Delete GitHub release (keeps PyPI)
gh release delete v2.0.11 --repo your-org/mcp-browser

# Re-run release script (will skip PyPI)
make release-script-patch
```

## Best Practices

### Pre-Release Checklist
- [ ] All tests passing locally
- [ ] CHANGELOG.md updated with changes
- [ ] Branch is main (or feature branch for pre-release)
- [ ] No uncommitted changes
- [ ] `.env.local` configured with valid tokens

### During Release
- [ ] Use `--dry-run` first to validate
- [ ] Review quality gate output
- [ ] Verify version number is correct
- [ ] Check security scan passes

### Post-Release Verification
- [ ] Visit PyPI URL to confirm package
- [ ] Check GitHub release page
- [ ] Test installation: `pip install mcp-browser==X.Y.Z`
- [ ] Update Homebrew formula (if applicable)
- [ ] Announce release

## Comparison: Script vs Manual

### Release Script (Recommended)
```bash
# One command, 14 automated steps
make release-script-patch
```

**Pros**:
- ✅ Automated, consistent
- ✅ Built-in safety checks
- ✅ Dry-run testing
- ✅ Comprehensive error handling
- ✅ Single source of truth

**Cons**:
- ❌ Less granular control
- ❌ Requires `.env.local` setup

### Manual Makefile Workflow (Legacy)
```bash
# Multiple manual steps
make release-prep
make bump-and-commit-patch
make publish-pypi
git push origin main
make github-release
make update-homebrew
```

**Pros**:
- ✅ Step-by-step control
- ✅ Can skip/retry individual steps

**Cons**:
- ❌ Error-prone (easy to forget steps)
- ❌ No automated validation
- ❌ Inconsistent execution

## Troubleshooting

### Script Exits Immediately
**Symptom**: Script exits without running

**Causes**:
1. `.env.local` missing
2. Git working directory not clean
3. Not on main branch

**Debug**:
```bash
# Check environment
cat .env.local

# Check git status
git status

# Run with dry-run
python scripts/release.py --dry-run patch
```

### PyPI Upload Fails
**Symptom**: `ERROR: PyPI upload failed`

**Causes**:
1. Invalid `PYPI_TOKEN`
2. Network issues
3. Package name conflict

**Debug**:
```bash
# Test token manually
echo "$PYPI_TOKEN" | head -c 20

# Upload manually
python -m twine upload dist/* --verbose
```

### GitHub Release Fails
**Symptom**: `ERROR: GitHub release failed`

**Causes**:
1. Invalid `GITHUB_TOKEN`
2. Release already exists
3. `gh` CLI not installed

**Debug**:
```bash
# Test gh CLI
gh auth status

# Check if release exists
gh release view v2.0.11

# Install gh if missing
brew install gh
```

## Advanced Usage

### Custom Release Branch
```bash
# Release from feature branch
git checkout feature/my-feature
python scripts/release.py --skip-push minor
```

### Emergency Hotfix
```bash
# Skip tests for urgent fix
python scripts/release.py --skip-tests patch
```

### Local Testing
```bash
# Build and publish to PyPI, skip GitHub
python scripts/release.py --skip-push patch
```

### Re-run Failed Release
```bash
# If PyPI succeeded but GitHub failed
python scripts/release.py patch
# Script detects existing PyPI package and continues
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Release
on:
  workflow_dispatch:
    inputs:
      bump_type:
        type: choice
        options: [patch, minor, major]
        required: true

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Create .env.local
        run: |
          echo "PYPI_TOKEN=${{ secrets.PYPI_TOKEN }}" > .env.local
          echo "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}" >> .env.local
          echo "GITHUB_OWNER=${{ github.repository_owner }}" >> .env.local

      - name: Run release script
        run: python scripts/release.py ${{ inputs.bump_type }}
```

## Support

For issues with the release script:

1. Check this documentation
2. Run `python scripts/release.py --help`
3. Test with `--dry-run` first
4. Open an issue on GitHub

## See Also

- [scripts/bump_version.py](../scripts/bump_version.py) - Version bumping
- [scripts/extract_changelog.py](../scripts/extract_changelog.py) - Changelog extraction
- [Makefile](../Makefile) - Manual release targets
- [CHANGELOG.md](../CHANGELOG.md) - Version history
