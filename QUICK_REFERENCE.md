# MCP Browser Quick Reference

## Installation & Setup

```bash
# Install
pip install mcp-browser

# Quick setup (interactive)
mcp-browser quickstart

# Manual setup
mcp-browser init --project  # Initialize in current directory
mcp-browser start           # Start server
```

## Essential Commands

| Command | Description | Example |
|---------|-------------|---------|
| `quickstart` | Interactive setup wizard | `mcp-browser quickstart` |
| `init` | Initialize extension | `mcp-browser init --project` |
| `start` | Start server + dashboard | `mcp-browser start` |
| `status` | Check installation status | `mcp-browser status` |
| `doctor` | Diagnose & fix issues | `mcp-browser doctor --fix` |
| `dashboard` | Run dashboard only | `mcp-browser dashboard -p 3000` |
| `tutorial` | Interactive tutorial | `mcp-browser tutorial` |

## Common Options

```bash
# Global options
--help        # Show help for any command
--debug       # Enable debug logging
--config FILE # Use custom config file
--version     # Show version

# Start options
--port 8880           # Specific WebSocket port
--no-dashboard        # Skip dashboard
--dashboard-port 3000 # Custom dashboard port

# Status options
--format json  # Output as JSON
--format table # Pretty table (default)

# Doctor options
--fix     # Auto-fix issues
--verbose # Detailed output
```

## Chrome Extension Setup

1. Start server: `mcp-browser start`
2. Open dashboard: http://localhost:8080
3. Click "Install Extension" button
4. Or manually:
   - Open chrome://extensions
   - Enable "Developer mode"
   - Load unpacked: `.mcp-browser/extension`

## Claude Desktop Configuration

Add to Claude Desktop config:

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

## Directory Structure

```
~/.mcp-browser/           # Global installation
├── config/
│   └── settings.json    # Configuration
├── data/                # Console logs storage
│   └── console_*.jsonl  # Log files
└── logs/                # Server logs

./.mcp-browser/          # Project installation
├── extension/           # Chrome extension
├── data/               # Project logs
└── logs/               # Server logs
```

## Port Ranges

- **WebSocket**: 8875-8895 (auto-select)
- **Dashboard**: 8080 (default)

## Troubleshooting

```bash
# Quick diagnostics
mcp-browser doctor        # Check for issues
mcp-browser doctor --fix  # Auto-fix

# Check status
mcp-browser status

# View logs
tail -f ~/.mcp-browser/logs/mcp-browser.log

# Test MCP mode
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | mcp-browser mcp
```

## Shell Completion

```bash
# Bash
eval "$(mcp-browser completion bash)"

# Zsh
eval "$(mcp-browser completion zsh)"

# Fish
mcp-browser completion fish | source
```

## Environment Variables

- `MCP_BROWSER_CONFIG` - Path to config file
- `MCP_BROWSER_DEBUG` - Enable debug mode
- `MCP_BROWSER_PORT` - Default WebSocket port
- `MCP_BROWSER_DATA` - Data directory path

## MCP Tools Available

| Tool | Description | Parameters |
|------|-------------|------------|
| `browser_navigate` | Navigate to URL | `url` |
| `browser_query_logs` | Query console logs | `limit`, `level`, `url_pattern` |
| `browser_screenshot` | Capture screenshot | `url`, `fullpage` |

## Common Issues

| Issue | Solution |
|-------|----------|
| Extension not connecting | Check port matches (8875-8895) |
| No logs appearing | Refresh webpage, check extension |
| Port in use | Server auto-selects next available |
| Server won't start | Run `mcp-browser doctor --fix` |

## Examples

```bash
# Start with specific port
mcp-browser start --port 8880

# Run without dashboard
mcp-browser start --no-dashboard

# Check JSON status
mcp-browser status --format json

# Initialize globally
mcp-browser init --global

# Open dashboard in browser
mcp-browser dashboard --open
```

## Getting Help

- Run: `mcp-browser COMMAND --help`
- Tutorial: `mcp-browser tutorial`
- Issues: https://github.com/mcp-browser/mcp-browser
- Docs: https://docs.mcp-browser.dev