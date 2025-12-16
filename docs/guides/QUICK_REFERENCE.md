# Quick Reference

## Install + connect

```bash
pip install mcp-browser
mcp-browser install                    # Configure your AI tool
mcp-browser extension install          # Install extension files (global)
mcp-browser start --background         # Start WebSocket daemon (recommended)
```

Load the extension in Chrome:
- `chrome://extensions` → enable Developer mode → Load unpacked → select `~/mcp-browser-extensions/chrome/`

## Essential commands

- `mcp-browser quickstart` — interactive setup wizard
- `mcp-browser setup` — setup helper (may not install extensions in pip installs)
- `mcp-browser extension install [--local]` — install unpacked extension files
- `mcp-browser start [--background]` — start the WebSocket daemon
- `mcp-browser stop` — stop daemon for current project
- `mcp-browser status` — status for current project
- `mcp-browser doctor [--fix]` — diagnostics and repair hints
- `mcp-browser tutorial` / `mcp-browser demo` — guided walkthroughs
- `mcp-browser connect --cdp-port 9222` — CDP mode (optional; requires Playwright)

## Browser CLI (local testing)

```bash
mcp-browser browser --help
mcp-browser browser logs --limit 20
mcp-browser browser extract content
```

## MCP tools (Claude/assistant)

See `docs/reference/MCP_TOOLS.md` for the authoritative tool names and schemas.

