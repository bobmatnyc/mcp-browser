# Troubleshooting

## Quick checks

```bash
mcp-browser doctor          # Diagnostics
mcp-browser status          # Current project status
mcp-browser start --background  # Start the WebSocket daemon (recommended)
```

## Extension not connecting

Symptoms: extension popup shows disconnected, no logs arrive.

1. Ensure the daemon is running:
   ```bash
   mcp-browser start --background
   mcp-browser status
   ```
2. Reload the extension:
   - Chrome: `chrome://extensions` → enable Developer mode → Reload
3. Confirm you loaded the right folder:
   - If you used `mcp-browser extension install`: load `~/mcp-browser-extensions/chrome/`
   - If you used `mcp-browser extension install --local`: load `./mcp-browser-extensions/chrome/`
   - If you used legacy `mcp-browser init --project`: load `./mcp-browser-extension/`
4. Confirm the port range isn’t blocked:
   - Default daemon port range is `8851-8899` (localhost only).

## No logs showing up

1. Refresh the page after installing/reloading the extension (content scripts load on navigation).
2. Verify the site allows extensions:
   - `chrome://` pages do not allow content scripts.
3. Query logs via CLI (uses the running daemon):
   ```bash
   mcp-browser browser logs --limit 20
   ```
4. Query logs via MCP tools:
   - Use `browser_query` with `{"query":"logs","last_n":...}` (see `docs/reference/MCP_TOOLS.md`).

## Claude Code/Desktop can’t see MCP Browser

1. Ensure MCP config is installed:
   ```bash
   mcp-browser install
   ```
2. Verify the config entry uses `mcp-browser mcp`.
3. Restart the AI tool after updating config.
4. Keep the daemon running while using MCP tools:
   ```bash
   mcp-browser start --background
   ```

## Port conflicts

1. Stop the project server:
   ```bash
   mcp-browser stop
   ```
2. Start on a specific port:
   ```bash
   mcp-browser start --port 8880 --background
   ```
3. Inspect ports (macOS/Linux):
   ```bash
   lsof -i :8851-8899
   ```

Note: port `9222` is Chrome DevTools (CDP), not the MCP Browser daemon port range.

## macOS AppleScript fallback issues

If you rely on AppleScript fallback (limited features), grant Automation permissions:
- System Settings → Privacy & Security → Automation → enable your terminal app to control Safari/Chrome

## Logs

- Main log: `~/.mcp-browser/logs/mcp-browser.log`
