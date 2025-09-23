# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-09-23

### Fixed
- **Package Configuration**: Standardized package name to "mcp-browser" across all configuration files
- **Version Consistency**: Fixed version inconsistencies between pyproject.toml (0.1.0), setup.py (1.0.0), and source files
- **Python Requirements**: Updated Python version requirement to >=3.10 consistently across all files
- **Dependencies**: Consolidated and aligned dependencies between setup.py and pyproject.toml
- **Build Tools**: Updated Python version targets in black, ruff, and mypy configurations

### Added
- **Shell Script**: Added project-level management shell script for improved DevOps workflow
- **Test Suite**: Comprehensive test suite for MCP functions with async testing support
- **Documentation**: Improved project documentation and setup instructions

### Changed
- **Package Name**: Unified package name from "browserpymcp" to "mcp-browser"
- **Entry Point**: Updated console script entry point to use correct module path
- **Python Support**: Removed support for Python 3.8 and 3.9, now requires Python >=3.10

## [1.0.0] - 2025-09-14

### Added
- Initial release of MCP Browser implementation
- Service-Oriented Architecture (SOA) with Dependency Injection
- Browser console log capture and control via MCP for Claude Code integration
- Chrome extension for real-time console monitoring
- WebSocket service for browser communication
- Storage service with JSONL persistence and automatic log rotation
- Screenshot service with Playwright integration
- MCP service exposing browser tools to Claude Code
- Dashboard service for web-based monitoring
- Docker support with development containers
- Comprehensive documentation and setup guides

### Features
- **Browser Integration**: Chrome extension captures console messages from all tabs
- **Real-time Communication**: WebSocket connection between browser and server
- **Log Management**: Automatic log rotation at 50MB with 7-day retention
- **MCP Tools**: Navigate, query logs, and capture screenshots via Claude Code
- **Dashboard**: Web interface for monitoring connections and logs
- **Async Architecture**: Fully asynchronous service layer with proper error handling