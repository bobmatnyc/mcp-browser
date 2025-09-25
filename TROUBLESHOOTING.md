# MCP Browser Troubleshooting Guide

## Quick Diagnostics

Run the diagnostic tool first:
```bash
mcp-browser doctor        # Check for issues
mcp-browser doctor --fix  # Attempt auto-fix
```

## Common Issues and Solutions

### 1. Extension Not Connecting

**Symptoms:**
- Extension popup shows "Disconnected"
- No console logs being captured
- Red icon in extension popup

**Solutions:**

1. **Check server is running:**
   ```bash
   mcp-browser status
   ```

2. **Verify port matches:**
   - Check extension popup for port number
   - Ensure it matches server port (8875-8895)

3. **Try different port:**
   ```bash
   mcp-browser start --port 8880
   ```

4. **Check firewall:**
   - Ensure localhost connections aren't blocked
   - Windows: Check Windows Defender Firewall
   - macOS: Check System Preferences > Security

5. **Reload extension:**
   - Go to chrome://extensions
   - Click reload button on MCP Browser extension

### 2. Server Won't Start

**Symptoms:**
- "Port in use" error
- "Permission denied" error
- Server crashes immediately

**Solutions:**

1. **Port already in use:**
   ```bash
   # Find what's using the port
   lsof -i :8875-8895  # macOS/Linux
   netstat -ano | findstr :8875  # Windows

   # Kill the process or use different port
   mcp-browser start --port 8890
   ```

2. **Permission issues:**
   ```bash
   # Check directory permissions
   ls -la ~/.mcp-browser

   # Fix permissions
   chmod 755 ~/.mcp-browser
   chmod -R 644 ~/.mcp-browser/data
   ```

3. **Missing dependencies:**
   ```bash
   pip install --upgrade mcp-browser
   pip install -r requirements.txt
   ```

### 3. No Console Logs Appearing

**Symptoms:**
- Extension connected but no logs captured
- Dashboard shows empty log list
- Console messages not being stored

**Solutions:**

1. **Refresh the webpage:**
   - Chrome extension needs page refresh to inject content script

2. **Check extension permissions:**
   - Ensure extension has permission for the current site
   - Some sites (chrome://, file://) are restricted

3. **Verify content script injection:**
   - Open Chrome DevTools
   - Check Console for MCP Browser messages

4. **Clear browser cache:**
   - Sometimes cached scripts interfere
   - Chrome: Ctrl+Shift+Del (Cmd+Shift+Del on Mac)

### 4. MCP Integration Not Working

**Symptoms:**
- Claude Code can't find mcp-browser
- "Command not found" errors
- Tools not available in Claude

**Solutions:**

1. **Check installation:**
   ```bash
   which mcp-browser  # Should show path
   mcp-browser --version  # Should show version
   ```

2. **Verify Claude Desktop config:**
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

3. **Test MCP mode:**
   ```bash
   # This should output JSON-RPC, not text
   echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | mcp-browser mcp
   ```

4. **Check PATH:**
   ```bash
   # Ensure mcp-browser is in PATH
   export PATH="$HOME/.local/bin:$PATH"  # Linux
   export PATH="/usr/local/bin:$PATH"    # macOS
   ```

### 5. Screenshot Not Working

**Symptoms:**
- Screenshot tool fails
- "Playwright not installed" error
- Timeout errors

**Solutions:**

1. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   # or
   python -m playwright install
   ```

2. **Check Playwright installation:**
   ```python
   python -c "from playwright.sync_api import sync_playwright; print('OK')"
   ```

3. **Increase timeout:**
   - Edit config to increase screenshot timeout
   - Some sites load slowly

### 6. High Memory/CPU Usage

**Symptoms:**
- Server consuming excessive resources
- System becomes slow
- Log files growing too large

**Solutions:**

1. **Check log file size:**
   ```bash
   du -sh ~/.mcp-browser/data/*
   ```

2. **Adjust retention settings:**
   ```json
   {
     "storage": {
       "max_file_size_mb": 25,
       "retention_days": 3
     }
   }
   ```

3. **Limit connections:**
   - Reduce number of tabs with extension active
   - Close unused browser tabs

### 7. Dashboard Not Loading

**Symptoms:**
- http://localhost:8080 shows error
- "Connection refused" in browser
- Blank page

**Solutions:**

1. **Check if dashboard is enabled:**
   ```bash
   mcp-browser start  # Should include dashboard
   # or explicitly
   mcp-browser dashboard
   ```

2. **Try different port:**
   ```bash
   mcp-browser dashboard --port 3000
   ```

3. **Check browser console:**
   - Open DevTools (F12)
   - Look for JavaScript errors

## Platform-Specific Issues

### macOS

1. **"Operation not permitted" error:**
   - System Integrity Protection may block access
   - Try running from user directory instead of system

2. **Chrome not found:**
   ```bash
   # Check if Chrome is installed
   ls /Applications/ | grep Chrome
   ```

### Windows

1. **PowerShell execution policy:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Path separators:**
   - Use forward slashes in config files
   - Or escape backslashes: `C:\\Users\\...`

### Linux

1. **Chrome/Chromium path:**
   ```bash
   # Find Chrome/Chromium
   which google-chrome chromium-browser chromium
   ```

2. **Permissions for port < 1024:**
   - Use ports 8875+ (no sudo required)

## Getting Help

1. **Run diagnostics:**
   ```bash
   mcp-browser doctor -v  # Verbose output
   ```

2. **Check logs:**
   ```bash
   tail -f ~/.mcp-browser/logs/mcp-browser.log
   ```

3. **Enable debug mode:**
   ```bash
   mcp-browser start --debug
   ```

4. **Report issues:**
   - GitHub: https://github.com/mcp-browser/mcp-browser/issues
   - Include output of `mcp-browser doctor`
   - Include relevant log files

## Emergency Recovery

If all else fails:

1. **Complete reinstall:**
   ```bash
   # Backup data if needed
   cp -r ~/.mcp-browser/data /tmp/mcp-backup

   # Remove everything
   rm -rf ~/.mcp-browser
   pip uninstall mcp-browser

   # Reinstall
   pip install mcp-browser
   mcp-browser quickstart
   ```

2. **Manual cleanup:**
   ```bash
   # Kill any running processes
   pkill -f mcp-browser

   # Clear Chrome extension
   # Go to chrome://extensions
   # Remove MCP Browser extension
   # Reinstall from dashboard
   ```

## Debug Checklist

- [ ] Python version >= 3.10
- [ ] mcp-browser installed (`pip show mcp-browser`)
- [ ] Chrome/Chromium installed
- [ ] Extension loaded in Chrome
- [ ] Server running (`mcp-browser status`)
- [ ] Port available (8875-8895)
- [ ] No firewall blocking localhost
- [ ] Correct permissions on directories
- [ ] Playwright installed (for screenshots)
- [ ] Valid configuration file