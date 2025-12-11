# Modular Build System for MCP Browser

This directory contains modular makefiles extracted from the python-project-template.

## Structure

```
.makefiles/
├── common.mk      - Core infrastructure (colors, ENV system, strict mode)
├── deps.mk        - Dependency management (pip-based for mcp-browser)
├── quality.mk     - Code quality (linting, formatting, pre-publish)
├── testing.mk     - Test execution (pytest with parallel/serial modes)
├── release.mk     - Release automation (integrates with scripts/release.py)
└── README.md      - This file
```

## Integration

These modules are loaded in the main `Makefile`:

```makefile
-include .makefiles/common.mk
-include .makefiles/deps.mk
-include .makefiles/quality.mk
-include .makefiles/testing.mk
-include .makefiles/release.mk
```

## Key Features

### ENV System (common.mk)
- Supports `development`, `staging`, `production` environments
- Override with `make ENV=production <target>`
- ENV-specific configurations for pytest, ruff, build flags

### Dependency Management (deps.mk)
- Adapted for pip-based workflow (not Poetry)
- `make install` - Install with dev dependencies + Playwright
- `make install-prod` - Production dependencies only
- `make deps-info` - Show dependency information

### Quality Checks (quality.mk)
- `make quality` - Run all quality checks (ruff + mypy)
- `make lint-fix` - Auto-fix linting issues
- `make pre-publish` - Comprehensive pre-release quality gate
- `make clean-pre-publish` - Clean artifacts before release

### Testing (testing.mk)
- `make test` - Parallel test execution (default)
- `make test-serial` - Serial execution for debugging
- `make test-coverage` - Coverage reporting
- `make test-unit/integration` - Category-specific tests

### Release Automation (release.mk)
- `make release-patch/minor/major` - Complete release using scripts/release.py
- `make bump-patch/minor/major` - Version bumping using scripts/bump_version.py
- `make release-dry-run` - Preview release without changes
- `make release-build` - Build with quality checks

## Customization

These files are adapted for mcp-browser:
- **deps.mk**: Pip-based instead of Poetry, includes Playwright installation
- **release.mk**: Integrates with scripts/release.py and scripts/bump_version.py
- **common.mk**: Uses existing VERSION file, adds mcp-browser project variables

## Migration from Legacy Makefile

The original 544-line Makefile has been:
1. Backed up as `Makefile.legacy`
2. Replaced with 286-line modular version
3. All functionality preserved and enhanced

### Comparison

**Legacy Makefile**: 544 lines (monolithic)
**New System**:
- Main Makefile: 286 lines (orchestration + mcp-browser specific)
- Modular .mk files: ~40KB total (reusable components)

## Testing

Key targets have been tested and verified:
- `make help` - Shows organized target list
- `make env-info` - Displays environment configuration
- `make deps-info` - Shows dependency information
- `make health` - Quick health check
- All modular targets load correctly

## Benefits

1. **Separation of Concerns**: Each .mk file has a single responsibility
2. **Reusability**: Modular files can be used across projects
3. **Maintainability**: Easier to update individual modules
4. **Clarity**: Main Makefile focuses on mcp-browser-specific targets
5. **Standards**: Based on production-tested patterns from claude-mpm

## Quick Reference

### Common Workflows

**Development Setup**:
```bash
make install        # Install all dependencies
make setup          # Complete dev environment setup
make dev            # Start full dev environment
```

**Quality Checks**:
```bash
make quality        # Run all quality checks
make lint-fix       # Auto-fix issues
make test           # Run tests
```

**Release**:
```bash
make release-patch  # Complete patch release (RECOMMENDED)
make release-minor  # Complete minor release
make release-dry-run # Preview release
```

**Environment-Specific**:
```bash
make ENV=production test      # Production test settings
make ENV=staging quality      # Staging quality checks
```

## Documentation

For complete usage examples, see the header comments in each .mk file:
- `common.mk` - Lines 120-138
- `deps.mk` - Lines 76-90
- `quality.mk` - Lines 168-184
- `testing.mk` - Lines 114-143
- `release.mk` - Lines 211-230
