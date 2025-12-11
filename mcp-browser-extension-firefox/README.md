# MCP Browser Extension - Firefox Version

Firefox port of the MCP Browser extension using Manifest V2 with persistent background pages.

## Features

- **Manifest V2**: Uses persistent background pages (simpler than Chrome's service worker)
- **Promise-based API**: Uses Firefox's `browser.*` namespace with native promises
- **Multi-backend support**: Connect to multiple MCP servers simultaneously
- **Console log capture**: Automatic capture of console messages, errors, and warnings
- **Content extraction**: Mozilla Readability integration for article extraction
- **Port scanning**: Auto-discovery of MCP servers on ports 8875-8895

## Key Differences from Chrome Version

### API Namespace
- **Firefox**: `browser.*` (promise-based)
- **Chrome**: `chrome.*` (callback-based)

### Background Script
- **Firefox**: Persistent background page (`background.js`)
- **Chrome**: Service worker with lifecycle management

### Manifest
- **Firefox**: Manifest V2 with `browser_action`
- **Chrome**: Manifest V3 with `action`

### Permissions
- **Firefox**: Direct permissions in manifest
- **Chrome**: `host_permissions` for network access

## Installation

### Load as Temporary Extension (Development)

1. Open Firefox
2. Navigate to `about:debugging#/runtime/this-firefox`
3. Click "Load Temporary Add-on"
4. Select the `manifest.json` file in this directory
5. Extension will load and appear in toolbar

### Packaging for Distribution

```bash
cd mcp-browser-extension-firefox
zip -r ../mcp-browser-firefox.xpi *
```

Then submit the `.xpi` file to [addons.mozilla.org](https://addons.mozilla.org)

## Browser Requirements

- **Firefox**: 109.0 or higher
- **Extension ID**: `mcp-browser@anthropic.com`

## File Structure

```
mcp-browser-extension-firefox/
├── manifest.json          # Manifest V2 configuration
├── background.js          # Persistent background page
├── content.js            # Content script (console capture)
├── popup.html            # Extension popup UI
├── popup.js              # Popup logic
├── Readability.js        # Mozilla Readability library
├── icon-16.png           # Extension icons
├── icon-48.png
├── icon-128.png
└── README.md             # This file
```

## Usage

1. **Start MCP Server**: Run your MCP Browser server on a port between 8875-8895
2. **Extension Auto-connects**: The extension will automatically scan and connect
3. **View Dashboard**: Click the extension icon to see connection status
4. **Console Capture**: All console messages are automatically captured and sent to the server

## Debugging

1. Open Firefox DevTools
2. Go to `about:debugging#/runtime/this-firefox`
3. Find "MCP Browser" extension
4. Click "Inspect" to open background script console

## Development Notes

### Persistent Background Page
Firefox Manifest V2 uses persistent background pages, which:
- Don't terminate like Chrome's service workers
- Maintain WebSocket connections without keepalive tricks
- Simplify heartbeat and reconnection logic

### Promise-based API
Firefox's `browser.*` namespace returns promises:
```javascript
// Firefox (promise-based)
const result = await browser.storage.local.get('key');

// Chrome (callback-based)
chrome.storage.local.get('key', (result) => { ... });
```

### Tab Execution
Firefox uses `browser.tabs.executeScript()` instead of Chrome's `chrome.scripting.executeScript()`:
```javascript
// Firefox
await browser.tabs.executeScript(tabId, { code: '...' });

// Chrome
await chrome.scripting.executeScript({ target: { tabId }, func: ... });
```

## Version History

- **2.1.0**: Initial Firefox port with Manifest V2
  - Persistent background page
  - Promise-based browser.* API
  - Simplified lifecycle management
  - Multi-connection support

## License

Same as parent project

## Support

For issues specific to the Firefox extension, please note in your issue report that you're using Firefox.
