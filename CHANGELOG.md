# Changelog

All notable changes to MCP Browser will be documented in this file.

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
