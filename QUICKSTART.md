# BrowserPyMCP Quick Start Guide

## Installation in 3 Steps

### Step 1: Install Python Package

```bash
# Using pipx (recommended)
pipx install browserpymcp

# Or using pip
pip install browserpymcp
```

### Step 2: Load Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `extension` folder from this project
5. You should see the extension icon in your toolbar

### Step 3: Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Restart Claude Desktop after saving.

## Testing the Setup

### 1. Start the Server (for testing)

```bash
browserpymcp start
```

You should see:
```
WebSocket server listening on port 8875
BrowserPyMCP server started successfully
```

### 2. Check Extension Connection

- Look at the extension icon in Chrome toolbar
- Green badge with port number = connected
- Red badge with "!" = disconnected

### 3. Test Console Capture

Open any website and run in the browser console:
```javascript
console.log("Test message from BrowserPyMCP");
console.error("Test error");
console.warn("Test warning");
```

### 4. Use in Claude Desktop

Ask Claude to:
- "Navigate my browser to https://example.com"
- "Show me the console logs from my browser"
- "Take a screenshot of my browser"

## Common Commands

```bash
# Start server manually
browserpymcp start

# Check server status
browserpymcp status

# Run in MCP mode (for Claude Desktop)
browserpymcp mcp
```

## Troubleshooting

### Extension Not Connecting?

1. Make sure server is running: `browserpymcp status`
2. Click extension icon to see connection status
3. Try clicking "Reconnect" in the popup

### No Logs Captured?

1. Refresh the web page after extension loads
2. Check for "[BrowserPyMCP] Console capture initialized" in console
3. Make sure extension is enabled in Chrome

### Claude Can't Access Tools?

1. Verify config file is saved correctly
2. Restart Claude Desktop completely
3. Check that `browserpymcp mcp` command works in terminal

## Architecture Overview

```
Browser Tab → Console Message → Chrome Extension
                                       ↓
                                WebSocket (8875)
                                       ↓
                               BrowserPyMCP Server
                                       ↓
                                  MCP Protocol
                                       ↓
                                Claude Desktop
```

## Log Storage Location

Logs are stored at:
```
~/.browserPYMCP/browser/[port]/console.jsonl
```

- Files rotate at 50MB
- 7-day retention policy
- JSONL format for easy parsing

## Need Help?

- Check the full README.md for detailed documentation
- Report issues at: https://github.com/browserpymcp/mcp-browser/issues