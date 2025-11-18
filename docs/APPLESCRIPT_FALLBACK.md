# AppleScript Fallback Documentation

## Overview

mcp-browser provides automatic AppleScript fallback support for macOS users when the browser extension is unavailable. This enables basic browser control without requiring extension installation, though with reduced functionality.

## Architecture

### Control Methods

mcp-browser uses a **unified browser control architecture** with automatic method selection:

1. **Primary: Browser Extension** (Full Features)
   - ✅ Real-time console log capture
   - ✅ Advanced DOM manipulation (wait, extract, complex selectors)
   - ✅ Multi-tab management
   - ✅ Fast performance (~10-50ms operations)
   - ❌ Requires extension installation

2. **Fallback: AppleScript** (Basic Control)
   - ✅ Navigation to URLs
   - ✅ Basic element clicking (CSS selectors)
   - ✅ Form field filling
   - ✅ JavaScript execution
   - ✅ Element inspection
   - ❌ **Cannot read console logs** (extension-only feature)
   - ❌ Slower performance (~100-500ms operations)
   - ❌ macOS only (Safari/Chrome)

### Automatic Fallback Logic

The `BrowserController` service automatically selects the best available method:

```
User Request → BrowserController
                    ↓
        Extension Available? ──Yes→ Use Extension (WebSocket)
                    ↓ No
        macOS + AppleScript? ──Yes→ Use AppleScript Fallback
                    ↓ No
              Error Message (Install extension)
```

## Configuration

### Browser Control Modes

Configure fallback behavior in `~/.config/mcp-browser/config.json`:

```json
{
  "browser_control": {
    "mode": "auto",                    // "auto", "extension", "applescript"
    "applescript_browser": "Safari",   // "Safari" or "Google Chrome"
    "fallback_enabled": true,          // Enable AppleScript fallback
    "prompt_for_permissions": true     // Show permission instructions
  }
}
```

**Mode Options:**
- **`auto`** (default): Try extension first, fall back to AppleScript if unavailable
- **`extension`**: Only use extension, fail if unavailable (strict mode)
- **`applescript`**: Only use AppleScript, ignore extension (testing mode)

## macOS Permission Setup

### Enable AppleScript Automation

AppleScript requires macOS automation permissions. If you see permission errors:

**Error Message:**
```
Safari does not have UI scripting enabled. To enable:

1. Open System Settings > Privacy & Security > Automation
2. Enable permissions for your terminal app (Terminal, iTerm2, etc.) to control Safari
3. If 'mcp-browser' appears in the list, enable it
4. Restart Safari

Alternatively, install the browser extension for full functionality:
   mcp-browser quickstart

Note: Console log capture requires the browser extension.
```

**Setup Steps:**

1. **Open System Settings**:
   - Click Apple menu → System Settings
   - Navigate to **Privacy & Security** → **Automation**

2. **Enable Terminal Permissions**:
   - Find your terminal app (e.g., "Terminal", "iTerm2", "Visual Studio Code")
   - Check the box next to "Safari" (or "Google Chrome")
   - Click "OK" to confirm

3. **Restart Browser**:
   - Quit and relaunch Safari/Chrome
   - AppleScript commands should now work

4. **Verify Permissions**:
   ```bash
   mcp-browser doctor  # Check system status
   ```

### Supported Browsers

**Safari (Recommended)**
- ✅ Native macOS support
- ✅ Faster AppleScript execution
- ✅ Better permission handling
- ⚠️ Requires "Allow JavaScript from Apple Events" (enabled by default)

**Google Chrome**
- ✅ AppleScript support
- ⚠️ Slightly slower execution
- ⚠️ May require additional permissions

## Feature Comparison

| Feature | Extension | AppleScript | Notes |
|---------|-----------|-------------|-------|
| **Navigation** | ✅ | ✅ | Full support both methods |
| **Console Logs** | ✅ | ❌ | **Extension only** |
| **Click Elements** | ✅ | ✅ (CSS only) | AppleScript: no XPath/text matching |
| **Fill Forms** | ✅ | ✅ | Full support both methods |
| **Submit Forms** | ✅ | ✅ | Full support both methods |
| **Get Element** | ✅ | ✅ (CSS only) | AppleScript: basic info only |
| **Wait for Element** | ✅ | ❌ | Extension only |
| **Select Dropdown** | ✅ | ❌ | Extension only |
| **Extract Content** | ✅ | ❌ | Extension only (Readability) |
| **JavaScript Execution** | ❌ | ✅ | AppleScript only |
| **Multi-tab Management** | ✅ | ❌ | Extension only |
| **Screenshot** | ✅ | ✅ | Playwright (independent) |
| **Performance** | ~10-50ms | ~100-500ms | Extension is 5-10x faster |

## Usage Examples

### Automatic Fallback (Default)

```python
# In Claude Code or MCP client
# Extension connected → uses extension
browser_navigate(port=8875, url="https://example.com")

# Extension disconnected → automatic AppleScript fallback
browser_navigate(port=8875, url="https://example.com")
# Response: "Successfully navigated to https://example.com using AppleScript fallback.
#            Note: Console log capture requires the browser extension.
#            Install extension: mcp-browser quickstart"
```

### Force Extension Mode

```json
{
  "browser_control": {
    "mode": "extension"  // Never fall back to AppleScript
  }
}
```

```python
# This will fail with clear error if extension unavailable
browser_navigate(port=8875, url="https://example.com")
# Error: "No browser extension connected on port 8875. Install extension: mcp-browser quickstart"
```

### Force AppleScript Mode

```json
{
  "browser_control": {
    "mode": "applescript",
    "applescript_browser": "Safari"
  }
}
```

```python
# Always uses AppleScript, ignores extension
browser_navigate(port=8875, url="https://example.com")
# Uses Safari via AppleScript
```

## Limitations & Workarounds

### Console Log Capture

**Limitation**: AppleScript **cannot read browser console logs**. This is a browser security restriction.

**Workarounds**:
1. **Install Extension** (Recommended):
   ```bash
   mcp-browser quickstart  # Interactive extension installation
   ```

2. **Use JavaScript Injection** (AppleScript can execute JavaScript):
   ```javascript
   // Inject custom logging that writes to page DOM
   console.log = (function(oldLog) {
     return function(message) {
       oldLog.apply(console, arguments);
       document.body.setAttribute('data-last-log', message);
     };
   })(console.log);

   // Read via AppleScript:
   // do JavaScript "document.body.getAttribute('data-last-log')"
   ```

3. **External Logging Service**:
   - Use browser developer tools manually
   - Set up remote logging (e.g., Sentry, LogRocket)

### Advanced DOM Operations

**Limitation**: AppleScript doesn't support:
- XPath selectors (CSS only)
- Text content matching
- Waiting for elements
- Dropdown selection

**Workarounds**:
- Use CSS selectors instead of XPath
- Execute custom JavaScript for complex operations:
  ```javascript
  // Custom wait for element via JavaScript
  await browser_controller.execute_javascript(`
    (async function() {
      while (!document.querySelector('.target')) {
        await new Promise(r => setTimeout(r, 100));
      }
      return true;
    })();
  `)
  ```

### Performance

**Limitation**: AppleScript operations are 5-10x slower than extension (~100-500ms vs ~10-50ms).

**Optimization**:
- Batch operations where possible
- Use extension for performance-critical workflows
- Cache results to minimize AppleScript calls

## Troubleshooting

### Common Errors

#### "Safari is not running"
**Solution**: Launch Safari before running commands
```bash
open -a Safari  # Launch Safari
```

#### "AppleScript is only available on macOS"
**Solution**: Install browser extension (required on Linux/Windows)
```bash
mcp-browser quickstart
```

#### "osascript command not found"
**Solution**: AppleScript is built into macOS. If missing, reinstall macOS or use extension.

#### Permission Denied Errors
**Solution**: Follow [macOS Permission Setup](#enable-applescript-automation) above

### Diagnostic Commands

```bash
# Check system status
mcp-browser doctor

# Test AppleScript availability
osascript -e 'tell application "Safari" to get URL of current tab of window 1'

# Verify permissions
# System Settings > Privacy & Security > Automation
```

## Performance Benchmarks

| Operation | Extension | AppleScript | Difference |
|-----------|-----------|-------------|------------|
| Navigate | 15ms | 250ms | 16.7x slower |
| Click | 20ms | 180ms | 9x slower |
| Fill Field | 18ms | 200ms | 11x slower |
| Get Element | 12ms | 150ms | 12.5x slower |
| Execute JS | N/A | 300ms | AppleScript only |

**Recommendation**: Use extension for production workflows. AppleScript is suitable for:
- Quick ad-hoc testing
- Environments where extension installation is restricted
- Simple navigation tasks

## Migration Guide

### From AppleScript to Extension

**Step 1**: Install Extension
```bash
mcp-browser quickstart  # Interactive installation
```

**Step 2**: Update Configuration (Optional)
```json
{
  "browser_control": {
    "mode": "auto"  // Default: automatic fallback
  }
}
```

**Step 3**: Restart mcp-browser Server
```bash
mcp-browser start
```

**No Code Changes Required**: The `BrowserController` automatically switches to extension when available.

### Testing Fallback Behavior

**Test AppleScript Fallback**:
```bash
# 1. Stop browser extension (remove or disable)
# 2. Configure AppleScript mode
cat > ~/.config/mcp-browser/config.json << EOF
{
  "browser_control": {
    "mode": "applescript",
    "applescript_browser": "Safari"
  }
}
EOF

# 3. Test navigation
mcp-browser start
# In separate terminal:
# Use MCP tools - they will use AppleScript
```

**Test Extension Mode**:
```bash
# 1. Install extension
mcp-browser quickstart

# 2. Configure extension mode
cat > ~/.config/mcp-browser/config.json << EOF
{
  "browser_control": {
    "mode": "extension"
  }
}
EOF

# 3. Test - will fail if extension not connected
```

## API Reference

### BrowserController Methods

All methods automatically fall back to AppleScript when extension unavailable:

```python
# Navigation (supports fallback)
await browser_controller.navigate(
    url="https://example.com",
    port=8875  # Optional: None uses AppleScript
)
# Returns: {"success": bool, "method": "extension"|"applescript", "error": str}

# Click element (supports fallback with CSS only)
await browser_controller.click(
    selector=".button",  # CSS selector required for AppleScript
    port=8875
)

# Fill form field (supports fallback)
await browser_controller.fill_field(
    selector="input[name='email']",
    value="user@example.com",
    port=8875
)

# Get element info (supports fallback)
await browser_controller.get_element(
    selector=".heading",
    port=8875
)

# Execute JavaScript (AppleScript only)
await browser_controller.execute_javascript(
    script="document.querySelector('.btn').click();",
    port=None  # Uses AppleScript
)
```

### AppleScriptService Direct API

For advanced use cases, call AppleScript service directly:

```python
from mcp_browser.services.applescript_service import AppleScriptService

applescript = AppleScriptService()

# Check browser availability
availability = await applescript.check_browser_availability("Safari")
# Returns: {"available": bool, "installed": bool, "applescript_enabled": bool, "message": str}

# Navigate
result = await applescript.navigate(
    url="https://example.com",
    browser="Safari"  # or "Google Chrome"
)

# Execute JavaScript
result = await applescript.execute_javascript(
    script="document.title",
    browser="Safari"
)
# Returns: {"success": bool, "data": str, "error": str}

# Get current URL
url = await applescript.get_current_url("Safari")
```

## Security Considerations

### AppleScript Permissions

AppleScript requires system-level automation permissions:
- ⚠️ Grants terminal app control over browser
- ⚠️ Can execute arbitrary JavaScript in browser context
- ⚠️ Review automation permissions periodically

**Best Practices**:
1. Only grant permissions to trusted terminal apps
2. Review automation settings in System Settings
3. Revoke permissions when no longer needed
4. Use extension mode for production (more sandboxed)

### JavaScript Execution

AppleScript can execute arbitrary JavaScript via `do JavaScript`:
- ⚠️ Same security context as webpage
- ⚠️ Can access page data, cookies, localStorage
- ⚠️ Cannot bypass same-origin policy

**Security Tips**:
- Validate and sanitize JavaScript input
- Avoid executing user-provided scripts
- Use CSP (Content Security Policy) on target pages

## Support & Resources

- **Documentation**: https://github.com/browserpymcp/mcp-browser
- **Issues**: https://github.com/browserpymcp/mcp-browser/issues
- **Diagnostics**: `mcp-browser doctor`
- **Interactive Setup**: `mcp-browser quickstart`
- **Feature Tutorial**: `mcp-browser tutorial`

## Version History

- **v2.0.10**: AppleScript fallback implementation
  - Automatic fallback for macOS users
  - Safari and Chrome support
  - Configuration-driven mode selection
  - Comprehensive permission instructions

## License

MIT License - See LICENSE file for details
