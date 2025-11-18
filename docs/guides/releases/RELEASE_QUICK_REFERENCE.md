# Release Automation Quick Reference Card

## One-Command Release (Most Common)

```bash
make release-patch    # Patch: 2.0.10 → 2.0.11 ⭐ RECOMMENDED
make release-minor    # Minor: 2.0.10 → 2.1.0
make release-major    # Major: 2.0.10 → 3.0.0
```

## Setup (One-Time Only)

```bash
# 1. Copy template
cp .env.local.template .env.local

# 2. Add tokens (edit .env.local):
PYPI_TOKEN=pypi-XXXXXXXX          # https://pypi.org/manage/account/token/
GITHUB_TOKEN=ghp_XXXXXXXX         # https://github.com/settings/tokens
```

## Pre-Release Checks

```bash
make release-prep     # Run quality gate + security scan
make pre-publish      # Run quality checks only
make security-scan    # Run security checks only
```

## Individual Steps (If Needed)

```bash
make bump-and-commit-patch    # 1. Bump version + commit
make publish-pypi             # 2. Upload to PyPI
git push origin main          # 3. Push to GitHub
make github-release           # 4. Create GitHub release
make verify-release           # 5. Verify release
```

## Troubleshooting

```bash
# "PYPI_TOKEN not found"
echo "PYPI_TOKEN=pypi-..." >> .env.local

# "GITHUB_TOKEN not found"
echo "GITHUB_TOKEN=ghp_..." >> .env.local

# "Quality gate failed"
make lint-fix
make format
make test

# "Git not clean"
git add . && git commit -m "fix: message"

# Delete failed release
gh release delete vX.Y.Z --yes
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

## What `make release-patch` Does

1. ✅ Clean build artifacts
2. ✅ Run linting (ruff)
3. ✅ Check formatting (ruff)
4. ✅ Type check (mypy)
5. ✅ Run tests with coverage
6. ✅ Build package
7. ✅ Scan for secrets
8. ✅ Bump version (X.Y.Z → X.Y.Z+1)
9. ✅ Update VERSION, pyproject.toml, src/_version.py, CHANGELOG.md
10. ✅ Git commit "chore: bump version to X.Y.Z"
11. ✅ Publish to PyPI
12. ✅ Push to GitHub
13. ✅ Create GitHub release with changelog
14. ✅ Display Homebrew instructions
15. ✅ Show success summary

## Get Help

```bash
make help                # Show all targets
cat RELEASE.md           # Read full guide
cat docs/RELEASE_CHEATSHEET.md  # Read cheatsheet
```

---

**Quick Start**: `make release-patch` (after setting up `.env.local`)
