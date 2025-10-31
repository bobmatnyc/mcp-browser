# MCP Browser Chrome Extension

This directory contains the Chrome extension for MCP Browser.

## Installation

1. Open Chrome and navigate to `chrome://extensions`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this directory (`mcp-browser-extension/`)

## Status Colors

The extension badge shows connection status:

- 🔴 **RED** - Error or not functional
- 🟡 **YELLOW** - Listening but not connected
- 🟢 **GREEN** - Connected to server (shows port number)

## Testing the Extension

Open the included **demo.html** test page to verify extension functionality:

```
file:///path/to/mcp-browser-extension/demo.html
```

Or from Chrome:
```
chrome-extension://<your-extension-id>/demo.html
```

The demo page includes:
- Console logging tests (log, info, warn, error, objects, arrays)
- DOM interaction examples (buttons, inputs, dropdowns)
- Active tab filtering verification
- Command examples for Claude Code integration

### Example Commands

Once the demo page is open and generating console messages:

```python
# Query recent console logs
browser_query_logs(port=8875, last_n=10)

# Filter by level
browser_query_logs(port=8875, level_filter=["error"], last_n=5)

# Take screenshot
browser_screenshot(port=8875)
```

## Version

See `manifest.json` for current version.

## Server Connection

The extension automatically scans ports 8875-8895 for MCP Browser servers.
When connected, the badge will show the port number (e.g., "8875").

## Features

- ✅ **Active tab filtering** - Only the active tab sends console messages
- ✅ **Multi-server discovery** - Automatically finds servers on ports 8875-8895
- ✅ **Three-color status** - Visual connection state indicator
- ✅ **Message batching** - Efficient WebSocket communication
- ✅ **Auto-reconnection** - Handles connection failures gracefully
