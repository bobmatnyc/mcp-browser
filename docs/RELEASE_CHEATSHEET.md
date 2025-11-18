# Release Automation Cheatsheet

Quick reference for mcp-browser release automation.

## Setup (One-Time)

```bash
# 1. Copy environment template
cp .env.local.template .env.local

# 2. Get PyPI token from https://pypi.org/manage/account/token/
# 3. Get GitHub token from https://github.com/settings/tokens (scopes: repo, write:packages)

# 4. Edit .env.local
vim .env.local  # Add PYPI_TOKEN and GITHUB_TOKEN
```

## Complete Release (Recommended)

```bash
# Patch release (2.0.10 → 2.0.11)
make release-patch

# Minor release (2.0.10 → 2.1.0)
make release-minor

# Major release (2.0.10 → 3.0.0)
make release-major
```

## Pre-Release Checks

```bash
# Run quality gate + security scan
make release-prep

# Quality gate only
make pre-publish

# Security scan only
make security-scan
```

## Version Bumping

```bash
# Bump and commit (recommended)
make bump-and-commit-patch  # 2.0.10 → 2.0.11
make bump-and-commit-minor  # 2.0.10 → 2.1.0
make bump-and-commit-major  # 2.0.10 → 3.0.0

# Bump only (no commit)
make bump-patch
make bump-minor
make bump-major
```

## Publishing

```bash
# Publish to PyPI
make publish-pypi

# Create GitHub release
make github-release

# Get Homebrew SHA256
make update-homebrew
```

## Post-Release

```bash
# Verify release
make verify-release

# Check version consistency
make check-version
```

## Workflow Breakdown

| Step | Command | What It Does |
|------|---------|--------------|
| 1 | `make release-prep` | Quality gate + security scan |
| 2 | `make bump-and-commit-patch` | Bump version, update files, commit |
| 3 | `make publish-pypi` | Upload to PyPI |
| 4 | `git push origin main` | Push version bump commit |
| 5 | `make github-release` | Create GitHub release + tag |
| 6 | `make update-homebrew` | Display Homebrew update instructions |
| 7 | `make verify-release` | Verify PyPI and GitHub |

## Environment Variables

```bash
# Required in .env.local
PYPI_TOKEN=pypi-...          # From https://pypi.org/manage/account/token/
GITHUB_TOKEN=ghp_...         # From https://github.com/settings/tokens

# Optional (defaults to "browserpymcp")
GITHUB_OWNER=browserpymcp
```

## Troubleshooting Quick Fixes

```bash
# "PYPI_TOKEN not found"
echo "PYPI_TOKEN=pypi-..." >> .env.local

# "GITHUB_TOKEN not found"
echo "GITHUB_TOKEN=ghp_..." >> .env.local

# Quality gate failed - auto fix
make lint-fix
make format

# Git not clean
git add . && git commit -m "fix: message"

# PyPI not propagated yet
sleep 120 && make verify-release

# Delete failed release
gh release delete vX.Y.Z --yes
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

## Manual Step-by-Step (If Needed)

```bash
make release-prep              # 1. Quality checks
make bump-and-commit-patch     # 2. Bump version
make build                     # 3. Build package
make publish-pypi              # 4. Upload to PyPI
git push origin main           # 5. Push commits
make github-release            # 6. Create release
make update-homebrew           # 7. Get Homebrew SHA
make verify-release            # 8. Verify
```

## Scripts

```bash
# Extract changelog for version
python scripts/extract_changelog.py 2.0.10

# Bump version with dry-run
python scripts/bump_version.py patch --dry-run

# Get Homebrew SHA256
bash scripts/update_homebrew_tap.sh 2.0.10
```

## Quality Commands

```bash
make test                      # Run tests with coverage
make lint                      # Check code style
make lint-fix                  # Auto-fix linting
make format                    # Format with black
make quality                   # Lint + test
```

## All Release Targets

```bash
make pre-publish               # Quality gate
make security-scan             # Security checks
make release-prep              # Quality + security
make bump-and-commit-patch     # Bump patch + commit
make bump-and-commit-minor     # Bump minor + commit
make bump-and-commit-major     # Bump major + commit
make publish-pypi              # Publish to PyPI
make github-release            # Create GitHub release
make update-homebrew           # Homebrew instructions
make release-patch             # Complete patch release
make release-minor             # Complete minor release
make release-major             # Complete major release
make verify-release            # Verify release
```

## Typical Release Flow

```bash
# 1. Update CHANGELOG.md manually with changes
vim CHANGELOG.md

# 2. Run complete release
make release-patch

# 3. Wait 2-5 minutes for PyPI propagation

# 4. Verify
make verify-release

# 5. Test installation
pip install --upgrade mcp-browser

# 6. Celebrate! 🎉
```

## Rollback (If Something Goes Wrong)

```bash
# 1. Delete GitHub release
gh release delete vX.Y.Z --yes

# 2. Delete tag
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# 3. Revert commit
git revert HEAD
git push origin main

# 4. Fix issues and release again with new version
make release-patch
```

## Best Practices

- ✅ Always run `make release-prep` before releasing
- ✅ Update CHANGELOG.md manually before releasing
- ✅ Use complete workflows (`make release-patch`)
- ✅ Verify with `make verify-release` after publishing
- ✅ Keep `.env.local` secure (it's in .gitignore)
- ❌ Don't commit `.env.local` to git
- ❌ Don't skip quality checks
- ❌ Don't manually edit version files (use bump commands)
