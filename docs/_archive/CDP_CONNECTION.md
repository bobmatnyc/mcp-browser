# CDP Connection Guide (Archived)

This document is retained for historical context. CDP support is not available in current `mcp-browser` releases; use the extension-backed daemon flow instead.

Connect to your existing Chrome browser via Chrome DevTools Protocol (CDP) to use MCP Browser while preserving your browser session, cookies, and extensions.

## Overview

The CDP connection feature allows you to:
- Connect to a **running Chrome instance** without launching a new browser
- **Preserve browser state**: cookies, sessions, logged-in accounts
- **Keep your extensions**: ad blockers, password managers, etc.
- **Maintain browsing history** and settings
- Use all MCP Browser features with your existing browser

## Prerequisites

1. **Google Chrome** (or Chromium-based browser)
2. **Playwright** installed (required for CDP mode):
   ```bash
   pip install playwright
   playwright install
   ```
3. **mcp-browser** package:
   ```bash
   pip install mcp-browser
   ```

## Quick Start

### 1. Start Chrome with Remote Debugging

You need to start Chrome with the `--remote-debugging-port` flag:

#### macOS
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

#### Linux
```bash
google-chrome --remote-debugging-port=9222
# or
chromium-browser --remote-debugging-port=9222
```

#### Windows
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**Important**: Close all Chrome instances before starting with CDP:
```bash
# macOS/Linux
pkill -f "Google Chrome"

# Windows (PowerShell)
Stop-Process -Name chrome -Force
```

### 2. Test the Connection

Use the CLI command to verify the connection:

```bash
mcp-browser connect
```

Or specify a custom port:

```bash
mcp-browser connect --cdp-port 9223
```

**Success Output:**
```
✓ Connection Successful
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status              ✓ Connected
Browser Version     Chrome/120.0.6099.109
CDP Port            9222
Active Pages        3
```

### 3. Configure MCP Browser to Use CDP

Create or update your configuration file (`~/.mcp-browser/config/settings.json`):

```json
{
  "browser_control": {
    "mode": "cdp",
    "cdp_port": 9222,
    "cdp_enabled": true,
    "fallback_enabled": false
  }
}
```

**Configuration Options:**
- `mode`: Set to `"cdp"` for CDP-only mode, or `"auto"` for automatic fallback
- `cdp_port`: Port number where Chrome is running with CDP (default: 9222)
- `cdp_enabled`: Enable CDP connection (default: true)
- `fallback_enabled`: Allow fallback to extension/AppleScript if CDP fails

## Usage with Claude Code

Once configured, all MCP Browser tools will use your existing browser:

```python
# MCP Browser exposes a consolidated tool surface (see docs/reference/MCP_TOOLS.md).
# Example: Navigate to a URL (preserves cookies/session)
await mcp.call_tool("browser_action", {"action": "navigate", "url": "https://example.com"})

# Click elements (works with logged-in state)
await mcp.call_tool("browser_action", {"action": "click", "selector": "#dashboard-link"})

# Fill a field
await mcp.call_tool(
    "browser_action",
    {"action": "fill", "selector": "#search-input", "value": "query"},
)
```

## Advanced Usage

### Multiple Chrome Profiles

Run different Chrome instances with different profiles and CDP ports:

```bash
# Profile 1 on port 9222
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-profile-1

# Profile 2 on port 9223
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir=/tmp/chrome-profile-2
```

Connect to specific profile:
```bash
mcp-browser connect --cdp-port 9223
```

### Custom User Data Directory

Preserve a specific Chrome profile:

```bash
# macOS/Linux
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-mcp-profile"

# Windows
chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-mcp-profile"
```

### Headless Mode

Run Chrome in headless mode (no visible window) with CDP:

```bash
# Headless with CDP
google-chrome --headless --remote-debugging-port=9222
```

**Note**: Some websites detect headless mode and may block automation.

## Programmatic Usage

Use CDP connection in Python scripts:

```python
import asyncio
from mcp_browser.services.browser_controller import (
    BrowserController,
    BrowserNotAvailableError
)
from mcp_browser.services import BrowserService, WebSocketService
from mcp_browser.services.applescript_service import AppleScriptService

async def connect_to_browser():
    # Create service instances
    websocket_service = WebSocketService(host="localhost", start_port=8851, end_port=8899)
    browser_service = BrowserService()
    applescript_service = AppleScriptService()

    # Configure for CDP
    config = {
        "browser_control": {
            "mode": "cdp",
            "cdp_port": 9222,
            "cdp_enabled": True
        }
    }

    # Create controller
    controller = BrowserController(
        websocket_service=websocket_service,
        browser_service=browser_service,
        applescript_service=applescript_service,
        config=config
    )

    try:
        # Connect to existing browser
        result = await controller.connect_to_existing_browser(cdp_port=9222)

        if result["success"]:
            print(f"Connected to {result['browser_version']}")
            print(f"Active pages: {result['page_count']}")

            # Use browser controller
            await controller.navigate("https://example.com")
            await controller.click(selector="button#submit")

        else:
            print(f"Connection failed: {result['error']}")

    except BrowserNotAvailableError as e:
        print(f"Browser not available: {e}")

    finally:
        await controller.close_cdp()

# Run
asyncio.run(connect_to_browser())
```

## Troubleshooting

### Connection Refused

**Problem**: `Cannot connect to Chrome on port 9222`

**Solutions**:
1. Ensure Chrome is running with `--remote-debugging-port=9222`
2. Close all Chrome instances and restart with CDP flag
3. Check if another process is using port 9222:
   ```bash
   # macOS/Linux
   lsof -i :9222

   # Windows
   netstat -ano | findstr :9222
   ```
4. Try a different port (e.g., 9223)

### Playwright Not Installed

**Problem**: `Playwright not installed`

**Solution**:
```bash
pip install playwright
playwright install
```

### CDP Endpoint Returns 404

**Problem**: `CDP endpoint returned status 404`

**Solutions**:
1. Verify Chrome is running with remote debugging
2. Check the CDP port is correct
3. Try accessing `http://localhost:9222/json/version` in a browser
   - Should return JSON with browser version info
   - If returns 404, Chrome CDP is not enabled

### Port Already in Use

**Problem**: `Address already in use: bind`

**Solutions**:
1. Find and kill the process using the port:
   ```bash
   # macOS/Linux
   lsof -ti:9222 | xargs kill -9

   # Windows
   netstat -ano | findstr :9222
   taskkill /PID <pid> /F
   ```
2. Use a different port number

### No Pages Available

**Problem**: `CDP connected but no pages available`

**Solutions**:
1. Open at least one tab in Chrome
2. Navigate to a website (not `chrome://` URLs)
3. Ensure the tab is not in incognito mode (CDP doesn't access incognito by default)

### Connection Timeout

**Problem**: `Connection to Chrome on port 9222 timed out`

**Solutions**:
1. Check firewall settings (allow local connections on CDP port)
2. Verify Chrome is running and responsive
3. Try restarting Chrome with CDP flag
4. Increase timeout in code (default: 5 seconds)

### Browser Crashes or Becomes Unresponsive

**Problem**: Browser freezes during CDP usage

**Solutions**:
1. Close and restart Chrome with CDP
2. Reduce concurrent operations
3. Check system resources (CPU, memory)
4. Update Chrome to latest version

## Security Considerations

### Local Access Only

CDP should **only** be accessible locally. Never expose CDP to external networks:

```bash
# ✓ GOOD: Localhost only (default)
chrome --remote-debugging-port=9222

# ✗ BAD: Exposed to network
chrome --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222
```

### Firewall Configuration

Ensure your firewall blocks external access to CDP ports:

```bash
# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add chrome
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --block chrome

# Linux (ufw)
sudo ufw deny 9222

# Windows Firewall
netsh advfirewall firewall add rule name="Block CDP" dir=in action=block protocol=TCP localport=9222
```

### User Data Isolation

Use separate user data directories for automation:

```bash
# Don't use your main profile for automation
chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-automation
```

## Comparison: CDP vs Extension vs AppleScript

| Feature | CDP | Extension | AppleScript |
|---------|-----|-----------|-------------|
| **Preserve Browser State** | ✅ Yes | ❌ No | ✅ Yes |
| **Keep Extensions** | ✅ Yes | ❌ No | ✅ Yes |
| **Performance** | ⚡ Fast | ⚡ Fastest | 🐌 Slow |
| **Setup Complexity** | 🔧 Medium | 🟢 Easy | 🟢 Easy |
| **Cross-Platform** | ✅ Yes | ✅ Yes | ❌ macOS only |
| **Console Logs** | ❌ No* | ✅ Yes | ❌ No |
| **Requires Chrome Restart** | ✅ Yes | ❌ No | ❌ No |

*CDP can access console logs via Chrome DevTools Protocol, but this is not yet implemented in mcp-browser.

## Best Practices

### 1. Use Dedicated Chrome Profile

Create a dedicated Chrome profile for MCP Browser automation:

```bash
mkdir -p ~/.chrome-mcp-profile
chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-mcp-profile
```

**Benefits**:
- Isolates automation from personal browsing
- Prevents accidental data exposure
- Easier to reset/clean

### 2. Automate Chrome Startup

Create a shell script or alias:

```bash
# ~/.bashrc or ~/.zshrc
alias chrome-cdp='google-chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-mcp-profile &'
```

Usage:
```bash
chrome-cdp
mcp-browser connect
```

### 3. Use Environment Variables

Store CDP configuration in environment variables:

```bash
# ~/.bashrc or ~/.zshrc
export MCP_BROWSER_CDP_PORT=9222
export MCP_BROWSER_MODE=cdp
```

Reference in config:
```json
{
  "browser_control": {
    "mode": "${MCP_BROWSER_MODE}",
    "cdp_port": "${MCP_BROWSER_CDP_PORT}"
  }
}
```

### 4. Monitor Connection Health

Periodically check CDP connection:

```bash
# Check if CDP is accessible
curl http://localhost:9222/json/version
```

### 5. Graceful Cleanup

Always close CDP connections when done:

```python
try:
    await controller.connect_to_existing_browser(9222)
    # ... use browser ...
finally:
    await controller.close_cdp()
```

## FAQ

### Can I use CDP with Firefox?

No, CDP is specific to Chromium-based browsers (Chrome, Edge, Brave, etc.). Firefox uses a different protocol (Firefox DevTools Protocol).

### Does CDP work with Brave/Edge?

Yes! Any Chromium-based browser supports CDP:

```bash
# Brave
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --remote-debugging-port=9222

# Edge
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222
```

### Remote Chrome instances

CDP mode is intended for **local** use (`localhost`) only. Exposing Chrome’s remote debugging port over the network is unsafe and is not supported by the `mcp-browser connect` CLI.

### Will CDP interfere with manual browsing?

No, you can browse manually while CDP is connected. Both manual and automated actions will work simultaneously.

### Can I use CDP and the extension together?

Yes, in `"auto"` mode, MCP Browser will try the extension first and fall back to CDP:

```json
{
  "browser_control": {
    "mode": "auto",
    "cdp_enabled": true,
    "fallback_enabled": true
  }
}
```

## Related Documentation

- `docs/guides/QUICK_REFERENCE.md` - MCP Browser command reference
- `docs/guides/TROUBLESHOOTING.md` - General troubleshooting guide
- `docs/developer/DEVELOPER.md` - Maintainer documentation
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/) - Official CDP documentation

## Support

For issues or questions:
- GitHub Issues: https://github.com/masa/mcp-browser/issues
- Documentation: https://github.com/masa/mcp-browser/docs
- Discord Community: [Join here]

---

**Next Steps:**
1. Start Chrome with CDP: `chrome --remote-debugging-port=9222`
2. Test connection: `mcp-browser connect`
3. Configure mode: Update `~/.mcp-browser/config/settings.json`
4. Start using MCP Browser with your existing browser session!
