# Release Checklist

Use this checklist when releasing a new version of mcp-browser.

## Pre-Release (Day Before)

### Code Quality
- [ ] All tests passing locally: `make test`
- [ ] All tests passing in CI/CD
- [ ] No known critical bugs
- [ ] Code reviewed and merged to main
- [ ] Documentation updated (README, API docs)

### Version Planning
- [ ] Determine version bump type:
  - **Patch** (2.0.10 -> 2.0.11): Bug fixes, minor improvements
  - **Minor** (2.0.10 -> 2.1.0): New features, backward compatible
  - **Major** (2.0.10 -> 3.0.0): Breaking changes
- [ ] Update CHANGELOG.md with release notes
- [ ] Review and edit changelog for clarity

### Environment Setup
- [ ] `.env.local` exists with valid tokens:
  ```bash
  cat .env.local
  # Should show PYPI_TOKEN, GITHUB_TOKEN, GITHUB_OWNER
  ```
- [ ] GitHub CLI authenticated: `gh auth status`
- [ ] PyPI token valid (not expired)
- [ ] GitHub token has repo permissions

## Release Day

### 1. Pre-Flight Checks (5 minutes)
```bash
# Git status clean
- [ ] git status
      # Output: "nothing to commit, working tree clean"

# On main branch
- [ ] git branch --show-current
      # Output: "main"

# Pull latest
- [ ] git pull origin main

# Quality checks pass
- [ ] make release-prep
      # All checks should pass
```

### 2. Dry-Run Test (2 minutes)
```bash
# Test the release workflow
- [ ] make release-script-dry-run
      # Review output for any issues
      # Verify version number is correct
      # Check all 14 steps complete
```

### 3. Execute Release (5-10 minutes)
```bash
# Run the automated release
- [ ] make release-script-patch
      # (or minor/major as planned)

# Wait for completion
- [ ] Monitor output for errors
- [ ] Verify success message
- [ ] Note the version number
```

### 4. Verify Release (2 minutes)
```bash
# Check PyPI
- [ ] Visit https://pypi.org/project/mcp-browser/
      # New version should be listed
      # Check file sizes are reasonable

# Check GitHub
- [ ] Visit https://github.com/[owner]/mcp-browser/releases
      # New release should be visible
      # Changelog should be populated
      # Artifacts attached

# Test installation
- [ ] pip install --upgrade mcp-browser==[version]
      # Should install without errors
```

## Post-Release (30 minutes)

### 1. Homebrew Update (if applicable)
```bash
- [ ] Wait 5-10 minutes for PyPI propagation
- [ ] Run: bash scripts/update_homebrew_tap.sh [version]
- [ ] Update Homebrew formula repository
- [ ] Test Homebrew installation
```

### 2. Documentation Updates
- [ ] Update README.md installation instructions
- [ ] Update any version-specific documentation
- [ ] Check documentation links are not broken
- [ ] Update examples with new version number

### 3. Announcements
- [ ] Prepare release announcement
- [ ] Post to social media (Twitter, LinkedIn, etc.)
- [ ] Update project website (if applicable)
- [ ] Notify key users/stakeholders
- [ ] Post to relevant communities (Reddit, HN, etc.)

### 4. Monitoring
- [ ] Monitor PyPI download stats
- [ ] Check for installation issues
- [ ] Review GitHub issues for new reports
- [ ] Monitor error tracking (if configured)

## Emergency Rollback

If critical bug discovered after release:

### Option 1: Hotfix Release
```bash
# Fix the bug
- [ ] Create fix in new branch
- [ ] Test thoroughly
- [ ] Merge to main
- [ ] Release patch version immediately
      make release-script-patch
```

### Option 2: Yank PyPI Release
```bash
# Discouraged but available
- [ ] Visit PyPI project page
- [ ] Click "Manage"
- [ ] Select version
- [ ] Click "Yank release"
- [ ] Provide reason
```

### Option 3: GitHub Release Edit
```bash
# Mark as pre-release
- [ ] Visit GitHub release page
- [ ] Click "Edit release"
- [ ] Check "This is a pre-release"
- [ ] Update description with warning
```

## Common Issues

### Quality Gate Fails
**Problem**: Linting or tests fail

**Solution**:
```bash
# Fix issues
ruff check --fix src/
ruff format src/
pytest tests/

# Retry release
make release-script-patch
```

### PyPI Upload Fails
**Problem**: "ERROR: PyPI upload failed"

**Solutions**:
1. Check token is valid: `echo $PYPI_TOKEN | head -c 20`
2. Verify network connection
3. Try manual upload: `python -m twine upload dist/* --verbose`
4. Re-run script (handles already-published gracefully)

### GitHub Release Fails
**Problem**: "ERROR: GitHub release failed"

**Solutions**:
1. Check gh authentication: `gh auth status`
2. Verify token permissions (needs repo access)
3. Check if release already exists: `gh release view v[version]`
4. Re-run script (will skip PyPI, retry GitHub)

### Version Already Published
**Problem**: "Package already published to PyPI"

**Not an error**: Script continues with GitHub release.

**If unintended**:
- Double-check version number
- Review git history for previous release

## Success Criteria

Release is complete when:
- [✅] PyPI package published and installable
- [✅] GitHub release created with changelog
- [✅] Homebrew formula updated (if applicable)
- [✅] Documentation updated
- [✅] Release announced
- [✅] No critical issues reported within 24 hours

## Tips for Success

1. **Always dry-run first** - Catch issues before real release
2. **Release during business hours** - Available to handle issues
3. **Avoid Friday releases** - Weekend support burden
4. **Keep CHANGELOG updated** - Easier than retroactive documentation
5. **Test installation** - Verify in fresh virtualenv
6. **Monitor for 24 hours** - Watch for unexpected issues

## Script Reference

```bash
# Standard releases
make release-script-patch  # 2.0.10 -> 2.0.11
make release-script-minor  # 2.0.10 -> 2.1.0
make release-script-major  # 2.0.10 -> 3.0.0

# Special cases
make release-script-dry-run      # Test workflow
make release-script-skip-tests   # Emergency hotfix
make release-script-skip-push    # Local-only release

# Manual control
python scripts/release.py --help  # Full options
```

## Release Cadence Recommendations

- **Patch releases**: As needed (bug fixes)
- **Minor releases**: Monthly or bi-monthly (features)
- **Major releases**: Quarterly or annually (breaking changes)

## Post-Release Tasks

### Week After Release
- [ ] Review download statistics
- [ ] Collect user feedback
- [ ] Address any reported issues
- [ ] Plan next release features

### Month After Release
- [ ] Analyze adoption rate
- [ ] Review changelog for next version
- [ ] Identify deprecation candidates
- [ ] Update roadmap

## Documentation
- Full docs: [RELEASE_SCRIPT.md](RELEASE_SCRIPT.md)
- Quick start: [RELEASE_QUICKSTART.md](RELEASE_QUICKSTART.md)
- Summary: [RELEASE_SCRIPT_SUMMARY.md](../RELEASE_SCRIPT_SUMMARY.md)
