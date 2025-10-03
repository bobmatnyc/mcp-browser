# Changelog

All notable changes to MCP Browser will be documented in this file.

## [2.0.7] - 2025-10-03

### Fixed
- Import sorting and code style improvements
- Auto-fixed isort violations in 7 files

## [2.0.6] - 2025-10-03

### Added
- New `install` CLI command for automated Claude Code/Desktop configuration
- New `extension` CLI command for managing Chrome extension files
- Extension directory moved to `src/extension/` for proper packaging

### Changed
- Extension files now properly included in pip/pipx installations
- Updated build scripts to reference new extension location
- Shell completion scripts updated with new commands

### Fixed
- Extension source detection in `init` command (packaging issue)
- Path detection for both development and production installations
- Extension manifest version synced with package version

## [2.0.5] - 2024-10-03

### Changed
- Renamed package from BrowserPyMCP to mcp-browser
- Restructured CLI into modular command system (main.py: 1,835 → 317 lines)
- Improved service container with per-service creation locks
- Enhanced async patterns in storage service (replaced blocking I/O)

### Added
- CLI commands package with dedicated modules for each command
- CLI utilities package for shared functionality
- Periodic cleanup for pending browser requests (prevents memory leak)
- Interactive quickstart wizard
- System diagnostics (doctor command)
- Tutorial command for guided learning

### Fixed
- Race condition in service container singleton creation
- Memory leak in BrowserService pending requests
- Blocking file I/O in StorageService.get_storage_stats()
- Circular dependency between BrowserService and DOMInteractionService

### Performance
- Better concurrency for service initialization
- Non-blocking async file operations
- Automatic cleanup of orphaned requests (every 30s)

## [1.0.3] - 2024-09-24

### Fixed
- Fixed WebSocket handler signature mismatch (missing 'path' parameter) that caused connection errors
- Fixed MCP tools registration to properly expose all 11 browser control tools
- Fixed MCP protocol initialization to use correct "notifications/initialized" method
- Improved MCP server initialization to use dynamic capabilities generation

### Changed
- Updated WebSocketService._handle_connection to accept both websocket and path parameters
- Enhanced MCP service to use server.create_initialization_options() for proper capability registration

## [1.0.2] - 2024-09-24

### Added
- Mozilla Readability integration for content extraction
- Comprehensive CLI help system with rich output
- Interactive quickstart wizard for first-time users
- Doctor command for diagnosing and fixing issues
- Tutorial command for step-by-step learning
- Reference command for quick command lookup

### Changed
- Improved dual deployment model (local venv + pipx)
- Enhanced version management with semantic versioning

## [1.0.1] - 2024-09-24

### Added
- Initial release with core functionality
- WebSocket server for browser communication
- Chrome extension for console log capture
- MCP tools for Claude Code integration
- Dashboard for monitoring and management
- Automatic log rotation and retention
