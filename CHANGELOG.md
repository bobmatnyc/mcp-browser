# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.11] - 2025-11-18


## [2.0.10] - 2025-11-17

### Added
- AppleScript fallback for browser control on macOS when extension unavailable
- Automatic fallback logic with configuration-driven mode selection
- Safari and Google Chrome support via AppleScript automation
- BrowserController service for unified browser control interface
- Configuration modes: `auto` (default), `extension`, `applescript`
- Comprehensive AppleScript fallback documentation (docs/APPLESCRIPT_FALLBACK.md)
- Quick start guide for AppleScript setup (APPLESCRIPT_QUICK_START.md)
- macOS permission setup instructions and troubleshooting

### Features
- Browser navigation without extension
- Element clicking via CSS selectors
- Form field filling with event triggering
- JavaScript execution in browser context
- Element inspection and information retrieval
- Clear error messages with actionable permission instructions

### Technical
- AppleScriptService: macOS browser control via osascript subprocess
- BrowserController: Automatic method selection (extension → AppleScript → error)
- Service container integration with dependency injection
- Platform-specific service registration (macOS only)
- Performance: 100-500ms per operation (vs 10-50ms for extension)

### Limitations
- Console log capture requires browser extension (browser security restriction)
- AppleScript 5-15x slower than extension due to subprocess overhead
- macOS only feature (Windows/Linux require extension)

### Backward Compatibility
- No breaking changes
- Existing configurations continue to work unchanged
- New services are optional dependencies
- Extension-only workflows remain unaffected

## [2.0.9] - 2025-11-12

### Added
- Uninstall command to remove mcp-browser from MCP configuration
- Support for --target option (claude-code, claude-desktop, both)
- Comprehensive test suite for uninstall functionality (unit and integration tests)
- Demo page improvements for Chrome extension
- Architecture enhancements for better service organization

### Fixed
- Version synchronization across package files (pyproject.toml and _version.py)
- Test file organization and duplicate removal

## [2.0.8] - 2025-10-30

### Added
- Initial version with semantic versioning support

### Changed
- Implemented centralized version management

### Fixed
- Version consistency across all package files
