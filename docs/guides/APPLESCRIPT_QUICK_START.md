# AppleScript Fallback Quick Start

## 🚀 30-Second Setup (macOS Users)

### If Browser Extension Unavailable

**1. Enable macOS Permissions** (One-time setup):

```bash
# Open System Settings
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"

# Enable automation permissions:
# Your Terminal App (e.g., Terminal, iTerm2) → Safari ✅
```

**2. Configure Browser** (Optional):

```bash
# Default: Auto-fallback with Safari
# Works out of the box! No configuration needed.

# To customize:
cat > ~/.config/mcp-browser/config.json << EOF
{
  "browser_control": {
    "mode": "auto",
    "applescript_browser": "Safari"
  }
}
EOF
```

**3. Test It**:

```bash
# Start mcp-browser
mcp-browser start

# Use MCP tools (Claude Code, etc.)
# Navigate will automatically use AppleScript if extension unavailable
```

## 💡 Quick Tips

### When AppleScript Activates

✅ **Automatic Fallback**: Extension not installed or disconnected
✅ **You'll See**: "Successfully navigated using AppleScript fallback"
⚠️ **Note**: Console logs require browser extension

### Common Scenarios

**Scenario 1: Extension Installation Restricted**
```bash
# Use AppleScript-only mode
echo '{"browser_control": {"mode": "applescript"}}' > ~/.config/mcp-browser/config.json
```

**Scenario 2: Testing Without Extension**
```bash
# Temporarily force AppleScript
mcp-browser start  # Set mode="applescript" in config first
```

**Scenario 3: Production (Extension Required)**
```bash
# Strict extension-only mode
echo '{"browser_control": {"mode": "extension"}}' > ~/.config/mcp-browser/config.json
```

## 🔧 Troubleshooting (30 Seconds)

### Error: "Safari does not have UI scripting enabled"

**Fix**:
1. Open System Settings > Privacy & Security > Automation
2. Find your terminal app (Terminal, iTerm2, VS Code)
3. Check the box next to "Safari"
4. Restart Safari

### Error: "AppleScript is only available on macOS"

**Fix**: Install browser extension
```bash
mcp-browser quickstart  # Interactive installation guide
```

### Check System Status

```bash
mcp-browser doctor  # Diagnose all issues
```

## 📊 What Works via AppleScript

| Feature | Supported | Notes |
|---------|-----------|-------|
| Navigate URLs | ✅ | Full support |
| Click Buttons | ✅ | CSS selectors only |
| Fill Forms | ✅ | Full support |
| Get Element Info | ✅ | Basic info |
| Execute JavaScript | ✅ | Full JS execution |
| **Console Logs** | ❌ | **Extension required** |
| Screenshot | ✅ | Via Playwright |

## 🎯 Performance Expectations

- **AppleScript**: 100-500ms per operation
- **Extension**: 10-50ms per operation
- **Recommendation**: Use extension for production workflows

## 📚 Full Documentation

- **Complete Guide**: `docs/APPLESCRIPT_FALLBACK.md`
- **Implementation Details**: `APPLESCRIPT_IMPLEMENTATION_SUMMARY.md`
- **Interactive Setup**: `mcp-browser quickstart`
- **Troubleshooting**: `mcp-browser doctor`

## ⚡ One-Line Commands

```bash
# Enable AppleScript mode
echo '{"browser_control":{"mode":"applescript"}}' > ~/.config/mcp-browser/config.json

# Enable Safari (default)
echo '{"browser_control":{"applescript_browser":"Safari"}}' > ~/.config/mcp-browser/config.json

# Enable Chrome
echo '{"browser_control":{"applescript_browser":"Google Chrome"}}' > ~/.config/mcp-browser/config.json

# Back to auto mode
echo '{"browser_control":{"mode":"auto"}}' > ~/.config/mcp-browser/config.json

# Check permissions
osascript -e 'tell application "Safari" to get URL of current tab of window 1'
```

## 🆘 Need Help?

1. **Interactive Setup**: `mcp-browser quickstart`
2. **System Diagnostics**: `mcp-browser doctor`
3. **Feature Tutorial**: `mcp-browser tutorial`
4. **GitHub Issues**: https://github.com/browserpymcp/mcp-browser/issues

---

**Pro Tip**: AppleScript fallback is perfect for quick testing and environments where extension installation is restricted. For production workflows with console logging, install the extension via `mcp-browser quickstart`.
