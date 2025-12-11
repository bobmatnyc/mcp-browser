# Firefox Extension Installation Guide

## Quick Install (Development)

### Method 1: Temporary Extension (Recommended for Testing)

1. **Open Firefox Developer Tools**
   - Navigate to `about:debugging` in Firefox
   - Click "This Firefox" in the left sidebar

2. **Load Extension**
   - Click "Load Temporary Add-on..."
   - Navigate to `mcp-browser-extension-firefox/`
   - Select `manifest.json`

3. **Verify Installation**
   - Extension icon should appear in toolbar
   - Badge should show "..." (scanning for servers)
   - Click icon to open dashboard

### Method 2: Install from XPI (Packaged)

1. **Package Extension**
   ```bash
   cd mcp-browser-extension-firefox
   zip -r ../mcp-browser-firefox.xpi *
   ```

2. **Install XPI**
   - Open Firefox
   - Navigate to `about:addons`
   - Click gear icon → "Install Add-on From File..."
   - Select `mcp-browser-firefox.xpi`

## Verification Steps

### 1. Check Extension is Running
- Open `about:debugging#/runtime/this-firefox`
- Find "MCP Browser" in extensions list
- Status should show "Running"

### 2. Inspect Background Script
- Click "Inspect" next to the extension
- Console should show:
  ```
  [MCP Browser] Firefox extension initializing...
  [MCP Browser] Scanning ports 8875-8895...
  ```

### 3. Test Console Capture
1. Open any webpage
2. Open browser console (F12)
3. Type: `console.log('test message')`
4. Click extension icon
5. Click "Generate Test Message"
6. Verify messages appear in MCP server

## Troubleshooting

### Extension Not Loading
- **Check Firefox Version**: Requires Firefox 109.0+
- **Check Manifest**: Ensure `manifest.json` is valid JSON
- **Check Permissions**: Firefox may block some permissions

### No Server Connection
- **Start MCP Server**: Ensure server is running on port 8875-8895
- **Check WebSocket**: Open browser console, look for WebSocket errors
- **Firewall**: Ensure localhost WebSocket connections are allowed

### Console Messages Not Captured
1. Click extension icon
2. Check "Active Connections" count
3. If 0, click "Scan for Backends"
4. Verify server is responding

## Uninstall

### Temporary Extension
1. Navigate to `about:debugging#/runtime/this-firefox`
2. Find "MCP Browser"
3. Click "Remove"

### Installed Extension
1. Navigate to `about:addons`
2. Find "MCP Browser"
3. Click "Remove"

## Development Notes

### Auto-reload on Changes
- Temporary extensions must be manually reloaded
- Click "Reload" button in `about:debugging`

### Debugging
- **Background Script**: Inspect from `about:debugging`
- **Content Script**: Inspect from page console
- **Popup**: Right-click popup → "Inspect Element"

### Common Issues

#### WebSocket Connection Refused
```
Error: Connection refused to ws://localhost:8875
```
**Solution**: Start MCP server first

#### Manifest Error
```
Error: Reading manifest: Error processing browser_action
```
**Solution**: Check `manifest.json` syntax

#### Permission Denied
```
Error: Extension does not have permission
```
**Solution**: Check `permissions` array in manifest

## Differences from Chrome Version

| Feature | Firefox | Chrome |
|---------|---------|--------|
| Manifest | V2 | V3 |
| Background | Persistent page | Service worker |
| API | `browser.*` (promises) | `chrome.*` (callbacks) |
| Action | `browser_action` | `action` |
| Scripting | `tabs.executeScript()` | `scripting.executeScript()` |

## Production Deployment

### Sign Extension
1. Create account at [addons.mozilla.org](https://addons.mozilla.org)
2. Submit extension for review
3. Wait for approval (usually 24-48 hours)
4. Receive signed XPI

### Self-hosting
1. Package as XPI
2. Sign through AMO
3. Host on your server
4. Users install via "Install Add-on From File"

## Support

For Firefox-specific issues:
- Check Firefox extension console
- Review manifest.json syntax
- Verify browser.* API usage
- Test with temporary extension first
