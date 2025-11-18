# MCP-Browser Project Organization Standard

Version: 1.0.0
Last Updated: 2025-11-18
Project: mcp-browser (Python MCP Server)

## Overview

This document defines the official file organization standards for the mcp-browser project. All contributors should follow these guidelines when adding or moving files.

## Directory Structure

### Root Level (Minimal)
```
/
├── README.md              # Main project documentation
├── CHANGELOG.md           # Version history and release notes
├── CLAUDE.md              # AI agent instructions
├── LICENSE                # Project license
├── VERSION                # Version file
├── pyproject.toml         # Python package configuration
├── Makefile              # Build automation
├── .gitignore            # Git ignore patterns
└── .env.local            # Local environment variables (not committed)
```

**Rule**: Only essential project files in root. All other files belong in subdirectories.

### Source Code (`src/`)
```
src/
├── cli/                  # Command-line interface
│   ├── main.py          # CLI entry point
│   ├── commands/        # CLI command implementations
│   └── utils/           # CLI utilities
├── services/            # Service layer (SOA architecture)
│   ├── mcp_service.py
│   ├── browser_service.py
│   ├── applescript_service.py
│   └── ...
├── models/              # Data models
├── container/           # Dependency injection
└── _version.py          # Version information
```

**Naming**: snake_case (Python PEP 8)
**Organization**: Service-Oriented Architecture with clean separation

### Tests (`tests/`)
```
tests/
├── unit/                # Unit tests (isolated, mocked dependencies)
│   └── test_*.py
├── integration/         # Integration tests (multiple components)
│   └── test_*.py
├── services/           # Service-specific tests
│   └── test_*_service.py
└── fixtures/           # Test fixtures and HTML test pages
    ├── *.html
    ├── *.css
    └── *.js
```

**Naming**: `test_*.py` or `*_test.py`
**Organization**: By test type (unit, integration, service)

### Documentation (`docs/`)
```
docs/
├── README.md            # Documentation index and navigation
├── guides/             # User-facing guides
│   ├── APPLESCRIPT_USAGE.md
│   ├── releases/       # Release documentation
│   │   ├── RELEASE.md
│   │   └── RELEASE_QUICK_REFERENCE.md
│   └── ...
├── reference/          # Reference documentation
│   ├── PROJECT_ORGANIZATION.md  # This file
│   ├── API.md
│   └── ...
├── developer/          # Developer/maintainer documentation
│   ├── APPLESCRIPT_IMPLEMENTATION_SUMMARY.md
│   ├── RELEASE_AUTOMATION_SUMMARY.md
│   └── ...
└── testing/            # Test reports and evidence
    ├── UNINSTALL_TEST_REPORT.md
    └── ...
```

**Organization**:
- `guides/` - User-facing how-to guides
- `reference/` - Reference documentation and standards
- `developer/` - Internal implementation details
- `testing/` - Test reports and validation evidence

### Scripts (`scripts/`)
```
scripts/
├── release.py          # Release automation
├── bump_version.py     # Version management
├── extract_changelog.py
├── update_homebrew_tap.sh
└── ...
```

**Content**: Build scripts, automation, release tools
**Naming**: Descriptive names, `.py` or `.sh` extensions

### Examples (`examples/`)
```
examples/
├── demo-extension-detection.html
├── extension-installer.html
└── verify-extension.html
```

**Content**: User-facing demos and examples
**Purpose**: Help users understand how to use features

### Extension (`mcp-browser-extension/`)
```
mcp-browser-extension/
├── manifest.json
├── background.js
├── content.js
└── ...
```

**Purpose**: Chrome/Safari browser extension
**Organization**: Standard browser extension structure

### Temporary (`tmp/`)
```
tmp/
├── *.log              # Temporary logs
├── *.cache            # Build caches
└── ...                # Ephemeral files
```

**Rule**: All contents gitignored, safe to delete
**Cleanup**: Regular cleanup recommended (weekly/monthly)

## File Placement Rules

### Documentation Files (*.md)

**Root Level Only:**
- README.md - Main project documentation
- CHANGELOG.md - Version history
- CLAUDE.md - AI agent instructions
- LICENSE - Project license

**All Other Markdown Files:**

| File Type | Location | Examples |
|-----------|----------|----------|
| User guides | `docs/guides/` | APPLESCRIPT_USAGE.md |
| Release guides | `docs/guides/releases/` | RELEASE.md |
| API reference | `docs/reference/` | API.md, PROJECT_ORGANIZATION.md |
| Implementation | `docs/developer/` | *_IMPLEMENTATION_*.md, *_SUMMARY.md |
| Test reports | `docs/testing/` | *_TEST_REPORT.md |

### Python Files (*.py)

| File Type | Location | Pattern |
|-----------|----------|---------|
| Source code | `src/` | Service, model, util files |
| CLI commands | `src/cli/commands/` | Command implementations |
| Unit tests | `tests/unit/` | `test_*.py` |
| Integration tests | `tests/integration/` | `test_*.py` |
| Scripts | `scripts/` | Automation scripts |

### HTML/CSS/JS Files

| File Type | Location | Purpose |
|-----------|----------|---------|
| Test fixtures | `tests/fixtures/` | HTML for testing |
| User examples | `examples/` | Demo pages |
| Extension code | `mcp-browser-extension/` | Browser extension |

### Configuration Files

| File Type | Location | Examples |
|-----------|----------|----------|
| Root config | `/` (root) | pyproject.toml, Makefile |
| Hidden config | `/` (root) | .gitignore, .env.local |
| Tool config | `/` (root) | .mypy.ini, .ruff.toml |

## Naming Conventions

### Python Code
- **Modules/Files**: `snake_case.py` (PEP 8)
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

### Documentation
- **Root Level**: `UPPERCASE.md` (README.md, CHANGELOG.md)
- **Subdirectories**: `Title_Case.md` or `lowercase.md`
- **Multi-word**: Use underscores (`APPLESCRIPT_USAGE.md`)

### Directories
- **Lowercase**: All directory names lowercase
- **Multi-word**: Use hyphens (`mcp-browser-extension`)
- **Avoid**: Spaces, special characters, camelCase

## Git Integration

### File Moves
Always use `git mv` to preserve history:
```bash
git mv old/path/file.md new/path/file.md
```

### Commit Messages
Use conventional commits for organization:
```
refactor(docs): move release guides to docs/guides/releases/
refactor(tests): reorganize test files into unit/ and integration/
docs: create PROJECT_ORGANIZATION.md standard
```

## Import Path Management

### After Moving Python Files

Update imports in all affected files:

**Before:**
```python
from test_implementation import TestCase
```

**After:**
```python
from tests.integration.test_implementation import TestCase
```

### Update References

Check and update:
- Python imports
- Makefile targets
- README.md links
- CLAUDE.md references
- Documentation cross-references

## Validation

### After Reorganization

Run these checks:
```bash
# 1. Tests pass
make test

# 2. Build succeeds
make build

# 3. Linting passes
make lint

# 4. All links work
# Check README.md and docs/ links manually
```

## Maintenance

### Regular Tasks

**Weekly:**
- Clear `tmp/` directory
- Review root for misplaced files

**Monthly:**
- Audit for organization compliance
- Update this standard if patterns change

**Per Release:**
- Verify all new files properly placed
- Update documentation structure if needed

## Examples

### Good Organization
```
✓ docs/guides/APPLESCRIPT_USAGE.md
✓ docs/reference/API.md
✓ docs/developer/IMPLEMENTATION.md
✓ tests/unit/test_service.py
✓ tests/integration/test_workflow.py
✓ scripts/release.py
✓ examples/demo.html
```

### Bad Organization
```
✗ APPLESCRIPT_USAGE.md (should be in docs/guides/)
✗ test_service.py (should be in tests/unit/)
✗ release.py (should be in scripts/)
✗ demo.html (should be in examples/)
✗ implementation_notes.md (should be in docs/developer/)
```

## Enforcement

This standard is enforced through:
1. **Code Reviews**: Check file placement in PRs
2. **CI/CD**: Automated checks for misplaced files
3. **Documentation**: This standard as reference
4. **Tools**: `/mpm-organize` command for automated organization

## Updates

This standard is a living document. Updates require:
1. Discussion with maintainers
2. Update to this document
3. Migration plan if breaking changes
4. Communication to all contributors

---

**Last Reviewed**: 2025-11-18
**Approved By**: Project Maintainers
**Next Review**: 2026-02-18 (Quarterly)
