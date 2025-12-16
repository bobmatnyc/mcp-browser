# MCP Browser

[![PyPI Version](https://img.shields.io/pypi/v/mcp-browser.svg)](https://pypi.org/project/mcp-browser/)
[![Python Support](https://img.shields.io/pypi/pyversions/mcp-browser.svg)](https://pypi.org/project/mcp-browser/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A professional Model Context Protocol (MCP) server that provides comprehensive browser automation and console log capture through Chrome extension integration. Features automated installation, DOM interaction capabilities, and seamless Claude Code integration.

## 🌟 Zero Documentation Required

**Get started without reading any documentation:**

```bash
pip install mcp-browser
mcp-browser extension install
mcp-browser install
mcp-browser start --background
```

Load the extension in Chrome (one-time):
- `chrome://extensions` → enable Developer mode → “Load unpacked” → select `~/mcp-browser-extensions/chrome/`

Prefer an interactive wizard?
```bash
mcp-browser quickstart
```

**Need help anytime?** The CLI is completely self-documenting:
```bash
mcp-browser --help          # See all commands
mcp-browser reference       # Quick reference card
mcp-browser doctor          # Diagnose and fix issues
mcp-browser tutorial        # Step-by-step feature tour
```

## 🚀 Quick Start (30 Seconds)

### Option 1: Zero-Config Installation (Recommended)
```bash
pip install mcp-browser
mcp-browser extension install
mcp-browser install
mcp-browser start --background
```

### Option 2: Development Installation
```bash
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser
make install
make ext-deploy
mcp-browser start --background
```

### Next: load the extension
- Chrome: `chrome://extensions` → “Load unpacked” → `./mcp-browser-extensions/chrome/`

## ✨ Features

### Core Capabilities
- **🎯 Advanced DOM Interaction**: Click elements, fill forms, submit data, select dropdowns, wait for elements
- **📊 Console Log Capture**: Real-time capture from all browser tabs with advanced filtering
- **📷 Screenshots**: Extension-backed viewport capture
- **🌐 Smart Navigation**: Programmatic browser navigation with URL validation
- **🔄 Auto-Discovery**: Dynamic port allocation (default 8851-8899) with collision avoidance
- **🤖 AI-Ready**: 5 consolidated MCP tools optimized for efficient prompting

### Technical Architecture
- **⚡ Service-Oriented Architecture (SOA)**: Clean separation with dependency injection
- **🔗 WebSocket Communication**: Real-time bidirectional browser communication
- **💾 JSONL Storage**: Automatic log rotation (50MB) with 7-day retention
- **🎨 Chrome Extension**: Visual connection status with real-time monitoring
- **🤖 MCP Integration**: Consolidated tool surface for AI-driven browser automation

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
- **DOM Interaction**: DOM actions, extraction, and screenshots via extension protocol
- **MCP Service**: Exposes tools to MCP clients (Claude Code/Desktop, etc.)

## 📦 Installation

### Prerequisites
- **Python 3.10+** (with pip)
- **Chrome/Chromium** browser

### Method 1: PyPI Installation (Recommended)

```bash
pip install mcp-browser
mcp-browser extension install
mcp-browser install
mcp-browser start --background
```

### Method 2: Development Installation

```bash
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser
make install
make ext-deploy
mcp-browser start --background
```

### Method 3: pipx Installation (Isolated)

```bash
# Install with pipx for complete isolation
pipx install mcp-browser
mcp-browser extension install
mcp-browser install
mcp-browser start --background
```

Prefer an interactive wizard? Run `mcp-browser quickstart`.

**Need detailed installation help?** See [INSTALLATION.md](docs/guides/INSTALLATION.md) for platform-specific instructions, troubleshooting, and alternative methods.

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
mcp-browser start --background  # Start daemon in background (recommended)
mcp-browser start               # Start in foreground (debugging)
mcp-browser stop                # Stop daemon for current project
mcp-browser status              # Status for current project

# Installation management
mcp-browser install              # Install/configure MCP integration
mcp-browser uninstall            # Remove MCP config entry

# MCP integration
mcp-browser mcp                 # Run in MCP stdio mode (invoked by MCP clients)

# Utilities
mcp-browser version        # Show version info

# Extension management
mcp-browser extension install [--local]
mcp-browser extension update [--local]
mcp-browser extension path --check

# Local testing (CLI)
mcp-browser browser logs --limit 20
mcp-browser browser extract content
```

### Uninstalling MCP Browser

MCP Browser provides flexible uninstall options from simple MCP config removal to complete cleanup.

#### Quick Uninstall (MCP Config Only)

```bash
# Remove from Claude Code (default)
mcp-browser uninstall

# Remove from Claude Desktop
mcp-browser uninstall --target claude-desktop

# Remove from both
mcp-browser uninstall --target both
```

#### Complete Cleanup

```bash
# Preview what would be removed (recommended first step)
mcp-browser uninstall --clean-all --dry-run

# Remove everything with confirmation
mcp-browser uninstall --clean-all

# Remove everything without confirmation (use with caution)
mcp-browser uninstall --clean-all --yes
```

#### Cleanup Options

| Flag | Description | What Gets Removed |
|------|-------------|-------------------|
| `--clean-local` | Clean project files | `./mcp-browser-extensions/`, `./mcp-browser-extension/` (legacy), `./.mcp-browser/` |
| `--clean-global` | Clean user data | `~/.mcp-browser/` (data, logs, config) |
| `--clean-all` | Complete removal | MCP config + local + global data (add `--playwright` for caches) |
| `--playwright` | Remove Playwright cache | `~/.cache/ms-playwright/` (or OS equivalent; optional) |
| `--backup` / `--no-backup` | Control backup creation | Creates timestamped backup (default: enabled) |
| `--dry-run` | Preview changes | Shows what would be removed without doing it |
| `-y`, `--yes` | Skip confirmations | Removes without prompting (dangerous) |

#### Safety Features

- **Automatic Backups**: By default, creates timestamped backups in `~/.mcp-browser-backups/` before removing data
- **Confirmation Prompts**: Asks for confirmation before destructive operations (unless `--yes` is used)
- **Preview Mode**: Use `--dry-run` to see exactly what would be removed
- **Selective Cleanup**: Choose specific cleanup levels based on your needs

#### Example Scenarios

```bash
# Scenario 1: Remove MCP config only (safest)
mcp-browser uninstall

# Scenario 2: Clean local project files only
mcp-browser uninstall --clean-local

# Scenario 3: Clean global data with backup
mcp-browser uninstall --clean-global

# Scenario 4: Preview complete removal
mcp-browser uninstall --clean-all --dry-run

# Scenario 5: Complete removal with backup
mcp-browser uninstall --clean-all

# Scenario 6: Nuclear option (no backup, no confirmation)
mcp-browser uninstall --clean-all --no-backup --yes
```

**For detailed uninstall instructions and recovery options, see [UNINSTALL.md](docs/guides/UNINSTALL.md)**

#### Uninstall the Package Itself

After removing configurations and data, uninstall the package:

```bash
# If installed with pip
pip uninstall mcp-browser

# If installed with pipx
pipx uninstall mcp-browser
```

### 🛠️ MCP Tools (MCP surface)

MCP Browser exposes a consolidated tool surface optimized for AI assistants:

- `browser_action` — navigate/click/fill/select/wait
- `browser_query` — logs/element/capabilities
- `browser_screenshot` — extension-backed screenshot capture
- `browser_form` — fill/submit forms
- `browser_extract` — readable content or semantic DOM extraction

Tool schemas, examples, and legacy-name mapping: `docs/reference/MCP_TOOLS.md`.

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

### Safari Extension (macOS)

Full Safari support with native macOS app wrapper:

#### Installation
```bash
# Automated conversion from Chrome extension
cd /path/to/mcp-browser
bash scripts/create-safari-extension.sh
```

#### Features
- **Safari 17+ Support**: Full Manifest V3 compatibility with service workers
- **Cross-browser API**: Uses both `chrome.*` and `browser.*` namespaces
- **Native App Wrapper**: Packaged as macOS application for App Store distribution
- **Code Signing Ready**: Configured for both development and distribution signing
- **Xcode Project**: Automatically generated with proper capabilities

#### Key Differences from Chrome
- Requires macOS app wrapper (automatically created)
- Uses Apple's `safari-web-extension-converter` tool
- Needs App Sandbox capabilities for WebSocket connections
- Distribution requires Apple Developer account for signing

📚 **Complete Guide**: See [docs/guides/SAFARI_EXTENSION.md](docs/guides/SAFARI_EXTENSION.md) for:
- Step-by-step setup instructions
- Xcode project configuration
- Code signing and notarization
- App Store and direct distribution
- Testing and debugging guides
- Common issues and solutions

## 🗂️ File Structure

### Repository structure
```
mcp-browser/
├── src/                      # Python package (mcp_browser)
│   ├── cli/                  # CLI commands and utilities
│   ├── services/             # SOA services (WebSocket, MCP, storage, DOM, etc.)
│   ├── extension/            # Packaged Chrome extension assets (used by CLI installer)
│   └── extensions/           # Unpacked extension sources (chrome/firefox/safari)
├── docs/                     # Documentation (start at docs/README.md)
├── scripts/                  # Dev + release scripts
├── tests/                    # Tests
└── mcp-browser-extensions/   # Generated unpacked extensions (gitignored)
```

### Runtime data
```
~/.mcp-browser/
├── config/settings.json      # Configuration
├── data/<port>/console.jsonl # Stored console logs (JSONL, rotated)
├── logs/mcp-browser.log      # Main log
└── server.pid                # Daemon registry (per-project entries)
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

### Local smoke test

```bash
make ext-deploy
mcp-browser start --background
mcp-browser demo
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

Default config file:
- `~/.mcp-browser/config/settings.json`

Use a custom config for a single invocation:
```bash
mcp-browser --config /path/to/settings.json start --background
```

Full details: `docs/guides/INSTALLATION.md`.

## Troubleshooting

Start with:
```bash
mcp-browser doctor
```

Maintained guide: `docs/guides/TROUBLESHOOTING.md`.

## License

MIT License - see LICENSE file for details

## Documentation

Start here:
- `docs/README.md` (doc index)
- `docs/guides/INSTALLATION.md` (install + first run)
- `docs/reference/MCP_TOOLS.md` (authoritative MCP tool surface)
- `docs/reference/CODE_STRUCTURE.md` (architecture overview)
- `docs/developer/DEVELOPER.md` (maintainer guide)

Project-wide doc standards: `docs/STANDARDS.md`.

AI agent instructions: `CLAUDE.md`.

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
- **Documentation**: Start with `docs/README.md`
- **Architecture Questions**: See `docs/reference/CODE_STRUCTURE.md`
