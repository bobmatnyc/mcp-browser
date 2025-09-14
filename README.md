# BrowserPyMCP

A Model Context Protocol (MCP) server that captures browser console logs and provides browser control capabilities through Chrome extension integration.

## Features

- **Console Log Capture**: Capture all console messages (log, warn, error, debug, info) from any browser tab
- **WebSocket Communication**: Real-time message streaming with automatic port discovery (8875-8895)
- **Persistent Storage**: JSONL format with automatic rotation at 50MB and 7-day retention
- **Browser Control**: Navigate browsers and capture screenshots via MCP tools
- **Chrome Extension**: Visual status indicator with connection monitoring
- **Service-Oriented Architecture**: Clean separation of concerns with dependency injection

## Architecture

The project follows a Service-Oriented Architecture (SOA) with dependency injection:

- **WebSocket Service**: Handles browser connections with port auto-discovery
- **Storage Service**: Manages JSONL log files with rotation
- **Browser Service**: Processes console messages and manages browser state
- **Screenshot Service**: Playwright integration for screenshots
- **MCP Service**: Exposes tools to Claude Desktop

## Installation

### 1. Install Python Package

Using pip:
```bash
pip install browserpymcp
```

Using pipx (recommended):
```bash
pipx install browserpymcp
```

### 2. Install Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` folder from this repository
5. The extension icon should appear in your toolbar

### 3. Configure Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "browserpymcp": {
      "command": "browserpymcp",
      "args": ["mcp"]
    }
  }
}
```

## Usage

### Start the Server

```bash
# Start with WebSocket server
browserpymcp start

# Run in MCP mode for Claude Desktop
browserpymcp mcp

# Check status
browserpymcp status
```

### MCP Tools Available in Claude

1. **browser_navigate(port, url)** - Navigate browser to a URL
2. **browser_query_logs(port, last_n, level_filter)** - Query console logs
3. **browser_screenshot(port)** - Capture viewport screenshot

### Chrome Extension

The extension automatically:
- Captures all console messages from every tab
- Buffers and sends messages every 2-3 seconds
- Shows connection status in the toolbar icon
- Auto-reconnects on connection loss

## File Structure

```
~/.browserPYMCP/browser/
├── 8875/
│   ├── console.jsonl         # Current log file
│   └── console_20240101_120000.jsonl  # Rotated log file
├── 8876/
│   └── console.jsonl
└── ...
```

## Development

### Single-Path Workflows

This project follows the "ONE way to do ANYTHING" principle. Use these commands:

```bash
# ONE way to install
make install

# ONE way to develop
make dev

# ONE way to test
make test

# ONE way to build
make build

# ONE way to format code
make lint-fix

# See all available commands
make help
```

### Requirements

- Python 3.8+
- Chrome/Chromium browser
- Make (for workflow commands)

### 5-Minute Setup

```bash
# 1. Install everything
make install

# 2. Start development server
make dev

# 3. Load Chrome extension (see Installation section above)

# 4. Configure Claude Desktop (see Configuration section above)
```

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test types
make test-unit
make test-integration
make test-extension
```

## Configuration

Environment variables:
- `BROWSERPYMCP_PORT_START`: Starting port for auto-discovery (default: 8875)
- `BROWSERPYMCP_PORT_END`: Ending port for auto-discovery (default: 8895)
- `BROWSERPYMCP_LOG_LEVEL`: Logging level (default: INFO)
- `BROWSERPYMCP_STORAGE_PATH`: Base storage path (default: ~/.browserPYMCP/browser)

## Troubleshooting

### Extension Not Connecting

1. Check server is running: `browserpymcp status`
2. Verify port in extension popup (should show 8875-8895)
3. Check Chrome DevTools console for errors
4. Ensure localhost connections are allowed

### No Console Logs Captured

1. Verify extension is installed and enabled
2. Refresh the target web page
3. Check extension popup for connection status
4. Look for test message: "[BrowserPyMCP] Console capture initialized"

### Screenshot Failures

1. Ensure Playwright is installed: `playwright install chromium`
2. Check system has required dependencies
3. Verify port number matches an active browser

## License

MIT License - see LICENSE file for details

## Documentation

This project follows comprehensive documentation standards for optimal AI agent understanding:

### For AI Agents (Claude Code)
- **[CLAUDE.md](CLAUDE.md)** - Priority-based instructions for AI agents working on this codebase
- **[CODE_STRUCTURE.md](CODE_STRUCTURE.md)** - Detailed architecture analysis and patterns

### For Developers
- **[DEVELOPER.md](DEVELOPER.md)** - Technical implementation guide with service interfaces
- **[.claude-mpm/memories/](/.claude-mpm/memories/)** - Project patterns and architectural decisions

### Quick Reference
- **Installation & Usage**: This README.md (you are here)
- **Development Setup**: `make help` or [DEVELOPER.md](DEVELOPER.md)
- **Architecture Overview**: [CODE_STRUCTURE.md](CODE_STRUCTURE.md)
- **AI Agent Instructions**: [CLAUDE.md](CLAUDE.md)

## Contributing

Contributions are welcome! Please follow the single-path development workflow:

1. **Setup**: `make setup` (installs deps + pre-commit hooks)
2. **Develop**: `make dev` (start development server)
3. **Quality**: `make quality` (run all linting and tests)
4. **Submit**: Create feature branch and submit pull request

All code must pass `make quality` before submission. The pre-commit hooks will automatically format and lint your code.

## Support

For issues and questions:
- **GitHub Issues**: https://github.com/browserpymcp/mcp-browser/issues
- **Documentation**: Start with [CLAUDE.md](CLAUDE.md) for AI agents or [DEVELOPER.md](DEVELOPER.md) for humans
- **Architecture Questions**: See [CODE_STRUCTURE.md](CODE_STRUCTURE.md) for detailed analysis