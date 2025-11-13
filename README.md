# MCP Browser

[![PyPI Version](https://img.shields.io/pypi/v/mcp-browser.svg)](https://pypi.org/project/mcp-browser/)
[![Python Support](https://img.shields.io/pypi/pyversions/mcp-browser.svg)](https://pypi.org/project/mcp-browser/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A professional Model Context Protocol (MCP) server that provides comprehensive browser automation and console log capture through Chrome extension integration. Features automated installation, DOM interaction capabilities, and seamless Claude Code integration.

## 🌟 Zero Documentation Required

**Get started in under 30 seconds without reading any documentation:**

```bash
pip install mcp-browser
mcp-browser quickstart
```

The interactive quickstart command will:
- ✅ Guide you through installation and setup
- ✅ Install and configure the Chrome extension
- ✅ Set up Claude Code integration automatically
- ✅ Test all features with interactive examples
- ✅ Provide troubleshooting if anything goes wrong

**Need help anytime?** The CLI is completely self-documenting:
```bash
mcp-browser --help          # See all commands
mcp-browser quickstart      # Interactive setup guide
mcp-browser doctor          # Diagnose and fix issues
mcp-browser tutorial        # Step-by-step feature tour
```

## 🚀 Quick Start (30 Seconds)

### Option 1: Zero-Config Installation (Recommended)
```bash
# Install from PyPI and run interactive setup
pip install mcp-browser
mcp-browser quickstart
```

### Option 2: Development Installation
```bash
# Clone and install with automated setup
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser
./install.sh

# Follow the interactive setup
mcp-browser quickstart
```

### That's it! The quickstart command handles:
- ✅ Chrome extension installation guide
- ✅ Claude Code integration setup
- ✅ Server configuration and startup
- ✅ Interactive feature demonstration
- ✅ Troubleshooting any issues

## ✨ Features

### Core Capabilities
- **🎯 Advanced DOM Interaction**: Click elements, fill forms, submit data, select dropdowns, wait for elements
- **📊 Console Log Capture**: Real-time capture from all browser tabs with advanced filtering
- **📷 High-Quality Screenshots**: Automated browser viewport captures via Playwright
- **🌐 Smart Navigation**: Programmatic browser navigation with URL validation
- **🔄 Auto-Discovery**: Dynamic port allocation (8875-8895) with collision avoidance
- **🤖 AI-Ready**: 11 MCP tools optimized for Claude Code browser automation

### Technical Architecture
- **⚡ Service-Oriented Architecture (SOA)**: Clean separation with dependency injection
- **🔗 WebSocket Communication**: Real-time bidirectional browser communication
- **💾 JSONL Storage**: Automatic log rotation (50MB) with 7-day retention
- **🎨 Chrome Extension**: Visual connection status with real-time monitoring
- **🤖 Claude Code Integration**: 10 MCP tools for AI-driven browser automation

### Installation & CLI
- **📦 PyPI Distribution**: `pip install mcp-browser` for instant setup
- **🎯 Interactive Setup**: `mcp-browser quickstart` for guided configuration
- **🔧 Self-Documenting CLI**: Built-in help, tutorials, and troubleshooting
- **🏥 Health Monitoring**: `mcp-browser doctor` for system diagnostics
- **⚙️ Smart Configuration**: Auto-generated settings with sensible defaults
- **🧪 Self-Verification**: Built-in installation testing and demo capabilities

## Architecture

The project follows a Service-Oriented Architecture (SOA) with dependency injection:

- **WebSocket Service**: Handles browser connections with port auto-discovery
- **Storage Service**: Manages JSONL log files with rotation
- **Browser Service**: Processes console messages and manages browser state
- **Screenshot Service**: Playwright integration for screenshots
- **MCP Service**: Exposes tools to Claude Code

## 📦 Installation

### Prerequisites
- **Python 3.10+** (with pip)
- **Chrome/Chromium** browser

### Method 1: PyPI Installation (Recommended)

```bash
# Install from PyPI
pip install mcp-browser

# Run interactive setup (handles everything)
mcp-browser quickstart
```

### Method 2: Development Installation

```bash
# Clone and install
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser
./install.sh

# Run interactive setup
mcp-browser quickstart
```

### Method 3: pipx Installation (Isolated)

```bash
# Install with pipx for complete isolation
pipx install mcp-browser
mcp-browser quickstart
```

> **📋 Note**: The project includes a smart launcher for dual deployment. When working in the project directory, it automatically uses the local development version. Outside the project, it uses the pipx-installed version. See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

### What the quickstart command does:
- ✅ Verifies system requirements and dependencies
- ✅ Guides Chrome extension installation with screenshots
- ✅ Sets up Claude Code integration automatically
- ✅ Tests all features with interactive examples
- ✅ Configures optimal settings for your system
- ✅ Provides troubleshooting for any issues

**Need detailed installation help?** See [INSTALLATION.md](INSTALLATION.md) for platform-specific instructions, troubleshooting, and alternative methods.

## 🎯 Usage

### Self-Documenting CLI

**New to MCP Browser?** The CLI guides you through everything:

```bash
# Interactive setup and feature tour
mcp-browser quickstart     # Complete setup guide
mcp-browser tutorial       # Step-by-step feature demo
mcp-browser doctor         # Diagnose and fix issues

# Get help anytime
mcp-browser --help         # See all commands
mcp-browser start --help   # Help for specific commands
```

### Professional Server Management

```bash
# Server control
mcp-browser start          # Start the server
mcp-browser stop           # Stop the server
mcp-browser restart        # Restart (stop + start)
mcp-browser status         # Check status (ports, PIDs, logs)

# Installation management
mcp-browser install        # Install/configure MCP integration
mcp-browser uninstall      # Remove from Claude Code
mcp-browser uninstall --target claude-desktop  # Remove from Claude Desktop
mcp-browser uninstall --target both           # Remove from both

# Monitoring and logs
mcp-browser logs           # Last 50 lines
mcp-browser logs 100       # Last 100 lines
mcp-browser follow         # Real-time tail

# MCP integration
mcp-browser mcp            # Run in MCP mode for Claude Code
mcp-browser test-mcp       # Test all MCP tools

# Utilities
mcp-browser version        # Show version info
mcp-browser config         # Show configuration
mcp-browser clean          # Clean old logs and data
```

### Uninstalling MCP Browser

To remove MCP Browser from your Claude configuration:

```bash
# Remove from Claude Code (default)
mcp-browser uninstall

# Remove from Claude Desktop only
mcp-browser uninstall --target claude-desktop

# Remove from both Claude Code and Claude Desktop
mcp-browser uninstall --target both
```

The uninstall command will:
- Remove the mcp-browser entry from the MCP configuration file
- Preserve all other MCP server configurations
- Handle missing or invalid configuration files gracefully
- Provide clear feedback about what was removed

**Note:** This only removes the MCP configuration. To completely uninstall the package:

```bash
# If installed with pip
pip uninstall mcp-browser

# If installed with pipx
pipx uninstall mcp-browser
```

### 🛠️ MCP Tools Available in Claude Code

MCP Browser provides **11 comprehensive tools** for advanced browser automation and interaction:

#### Core Browser Control
1. **`browser_navigate(port, url)`** - Navigate browser to a URL
   - Port auto-discovery from active connections
   - Full URL validation and error handling
   - WebSocket command transmission

2. **`browser_query_logs(port, last_n, level_filter)`** - Query console logs with advanced filtering
   - Filter by log level (error, warn, info, debug)
   - Limit number of results (default: 50)
   - Real-time and stored log retrieval
   - JSONL format with timestamps

3. **`browser_screenshot(port, url?)`** - Capture high-quality viewport screenshots
   - Optional URL navigation before capture
   - Playwright-powered rendering
   - PNG format with metadata

#### Advanced DOM Interaction & Automation
4. **`browser_click(port, selector/xpath/text)`** - Intelligent element clicking
   - CSS selectors, XPath expressions, or visible text
   - Automatic element visibility waiting
   - Click coordination and action verification

5. **`browser_fill_field(port, selector/xpath, value)`** - Precise form field filling
   - Support for text inputs, textareas, and password fields
   - Automatic field clearing before input
   - Value validation and error reporting

6. **`browser_fill_form(port, form_data, submit?)`** - Bulk form filling automation
   - Multiple fields filled in single operation
   - Optional automatic form submission
   - Field mapping by name, ID, or selector
   - Batch operation with rollback on errors

7. **`browser_submit_form(port, selector/xpath?)`** - Smart form submission
   - Auto-detect forms or use specific selectors
   - Handle both button clicks and form.submit()
   - Wait for submission completion

8. **`browser_get_element(port, selector/xpath/text)`** - Element information extraction
   - Retrieve text content, attributes, and properties
   - Element visibility and interaction state
   - Bounding box and position data

9. **`browser_wait_for_element(port, selector, timeout?)`** - Dynamic content handling
   - Wait for elements to appear in DOM
   - Configurable timeout (default: 10s)
   - Essential for SPA and AJAX-heavy sites

10. **`browser_select_option(port, selector, value/text/index)`** - Dropdown interaction
    - Select by value, visible text, or index
    - Support for both `<select>` and custom dropdowns
    - Multiple selection handling

11. **`browser_evaluate_js(port, code)`** - Execute JavaScript in browser
    - Run custom JavaScript code in the browser context
    - Return values and handle execution results
    - Advanced automation and data extraction

### Chrome Extension Features

The Chrome extension provides comprehensive browser integration:

#### Automatic Console Capture
- **Multi-tab monitoring**: Captures console logs from all active browser tabs
- **Real-time buffering**: Collects messages every 2.5 seconds for optimal performance
- **Level filtering**: Supports error, warn, info, and debug message types
- **Automatic initialization**: Self-starts on page load with verification message

#### Visual Connection Management
- **Status indicator**: Toolbar icon shows connection state (green = connected, red = disconnected)
- **Port display**: Shows active WebSocket port in extension popup
- **Auto-reconnection**: Automatically reconnects on connection loss
- **Connection diagnostics**: Real-time connection health monitoring

#### DOM Interaction Support
- **Element discovery**: Supports CSS selectors, XPath, and text-based element finding
- **Form automation**: Integrates with form filling and submission tools
- **Event handling**: Manages click, input, and selection events
- **Wait mechanics**: Handles dynamic content and AJAX loading

## 🗂️ File Structure

### Project Structure
```
mcp-browser/
├── install.sh                # Automated installation
├── setup-claude-code.sh      # Claude Code integration
├── test_installation.sh      # Installation verification
├── demo.sh                   # Feature demonstration
├── mcp-browser              # Professional CLI entry point
├── src/
│   ├── cli/main.py          # Enhanced CLI with process management
│   ├── container/           # Dependency injection container
│   ├── services/            # Service layer (SOA)
│   │   ├── browser_service.py
│   │   ├── websocket_service.py
│   │   ├── storage_service.py
│   │   ├── mcp_service.py
│   │   ├── screenshot_service.py
│   │   └── dom_interaction_service.py
│   └── models/              # Data models
├── extension/               # Chrome extension
├── tmp/
│   └── demo_dom_interaction.html  # Test page for DOM features
└── requirements.txt
```

### Runtime Structure
```
~/.mcp-browser/
├── config/
│   └── settings.json        # Configuration (auto-generated)
├── logs/
│   ├── mcp-browser.log      # Main server log
│   └── [8875-8895]/         # Port-specific browser logs
├── run/
│   └── mcp-browser.pid      # Process ID tracking
└── data/                    # JSONL storage with rotation
    └── [port]/
        ├── console.jsonl    # Current session logs
        └── console_20240921_*.jsonl  # Rotated archives
```

### Automated Installation Benefits
- **Zero-configuration setup**: `./install.sh` handles everything automatically
- **Virtual environment isolation**: No system Python pollution
- **Port auto-discovery**: Finds available ports in 8875-8895 range
- **Self-verification**: Built-in installation testing and validation
- **Professional CLI**: Complete process management with status monitoring

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

### 🧪 Testing the Installation

```bash
# Run comprehensive installation test
./test_installation.sh

# Run feature demonstration
./demo.sh

# Test DOM interaction with demo page
open tmp/demo_dom_interaction.html
# Then use Claude Code tools to interact with the demo page:
# - "Fill the username field with 'testuser'"
# - "Click the test button"
# - "Fill the entire form and submit it"
# - "Select 'Canada' from the country dropdown"
# - "Wait for the dynamic content to appear after clicking the button"
```

### ⚡ 5-Minute Complete Setup

```bash
# 1. Clone and install everything
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser
./install.sh  # Handles venv, dependencies, directories, CLI setup

# 2. Load Chrome extension (30 seconds)
# chrome://extensions/ → Developer mode → Load unpacked → select extension/

# 3. Configure Claude Code integration
./setup-claude-code.sh  # Auto-generates config, tests all tools

# 4. Start and test immediately
mcp-browser start
open tmp/demo_dom_interaction.html
# Ask Claude:
# "Fill out the demo form with test data"
# "Click the test button and wait for results"
# "Select Canada from the country dropdown"
# "Submit the form and capture the console output"
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
4. Look for test message: "[mcp-browser] Console capture initialized"

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
- **Deployment Options**: [DEPLOYMENT.md](DEPLOYMENT.md) - Dual deployment guide (local & system-wide)
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