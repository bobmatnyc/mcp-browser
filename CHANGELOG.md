# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2025-09-23

### Added
- Comprehensive CLI help system with detailed command documentation
- Semantic versioning and build tracking implemented with single source of truth
- Project management shell script for automated operations
- Interactive quickstart command with step-by-step setup guide
- Doctor diagnostic command for system health checks
- Tutorial mode with interactive learning flows
- Shell completion support for bash, zsh, and fish
- Version bumping automation script (`scripts/bump_version.py`)
- CLI `version` command to display detailed build information with git metadata
- Build metadata tracking (git commit, branch, build date, dirty state)
- Version consistency validation across all package files
- GitHub Actions workflow for automated releases and PyPI publishing
- Docker image publishing to Docker Hub and GitHub Container Registry

### Changed
- Centralized version management in `src/_version.py`
- Updated all version references to use single source
- Enhanced build system with setuptools-scm support
- Improved CLI interface with better user experience
- Enhanced documentation with comprehensive command reference

### Fixed
- Version consistency issues across package files
- Build metadata accuracy in development environments

## [1.0.1] - 2024-01-15

### Added
- Initial stable release with core functionality
- MCP server implementation for browser console capture
- Chrome extension for WebSocket communication
- Service-Oriented Architecture with dependency injection
- Console log storage with JSONL format and rotation
- Screenshot service using Playwright
- Dashboard interface for monitoring
- DOM interaction capabilities

### Fixed
- WebSocket port auto-discovery for conflict resolution
- Message buffering to prevent I/O blocking
- Async service initialization patterns

### Changed
- Improved error handling and logging
- Enhanced service lifecycle management
- Better connection state tracking

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Basic MCP server functionality
- Chrome extension prototype
- Simple console log capture
- Basic navigation commands

[Unreleased]: https://github.com/browserpymcp/mcp-browser/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/browserpymcp/mcp-browser/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/browserpymcp/mcp-browser/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/browserpymcp/mcp-browser/releases/tag/v1.0.0