# MCP Browser Installation Guide

This guide covers installing the Python package, installing the browser extension files, configuring your MCP client, and starting the WebSocket daemon.

## Quick install (most users)

```bash
pip install mcp-browser

# 1) Install extension files (unpacked)
mcp-browser extension install

# 2) Install MCP configuration for your AI tool
mcp-browser install

# 3) Start the WebSocket daemon (recommended)
mcp-browser start --background
```

Load the extension in Chrome:
1. Open `chrome://extensions`
2. Enable “Developer mode”
3. Click “Load unpacked”
4. Select `~/mcp-browser-extensions/chrome/`

Verify:
```bash
mcp-browser doctor
mcp-browser status
```

## Installation methods

### PyPI (pip)
```bash
pip install mcp-browser
```

### pipx (isolated)
```bash
pipx install mcp-browser
```

### From source (contributors)
```bash
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser
make install
```

For local extension deploy:
```bash
make ext-deploy
```

## Requirements

**Supported Platforms:**
- macOS (recommended - full AppleScript integration)
- Linux (Chrome/Chromium/Firefox support)

**Not Supported:**
- Windows (due to AppleScript dependencies and extension compatibility issues)

**Software Requirements:**
- Python 3.10+
- Chrome/Chromium (for the extension)
- Optional (macOS): Automation permissions for AppleScript control

## Post-install setup

### 1) Install extension files

Recommended (global):
```bash
mcp-browser extension install
```

Project-local:
```bash
mcp-browser extension install --local
```

Legacy (creates `./mcp-browser-extension/`):
```bash
mcp-browser init --project
```

### 2) Configure your MCP client

Automated setup:
```bash
mcp-browser install
```

Manual config entry (example):
```json
{
  "mcpServers": {
    "mcp-browser": {
      "command": "mcp-browser",
      "args": ["mcp"]
    }
  }
}
```

### 3) Start the daemon

Keep the daemon running while using MCP tools:
```bash
mcp-browser start --background
```

### 4) Verify end-to-end

```bash
mcp-browser doctor
mcp-browser browser logs --limit 20
```

## Configuration

- Default config: `~/.mcp-browser/config/settings.json`
- Override config per invocation: `mcp-browser --config /path/to/settings.json …`

Minimal example:
```json
{
  "websocket": { "port_range": [8851, 8899], "host": "localhost" },
  "storage": { "max_file_size_mb": 50, "retention_days": 7 }
}
```

## Upgrading

```bash
pip install --upgrade mcp-browser
# or
pipx upgrade mcp-browser
```

## Uninstalling and troubleshooting

- Uninstall/cleanup: `docs/guides/UNINSTALL.md`
- Troubleshooting: `docs/guides/TROUBLESHOOTING.md`
