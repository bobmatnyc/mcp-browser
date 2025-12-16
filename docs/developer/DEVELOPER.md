# Developer Guide

This guide is for contributors and maintainers of `mcp-browser`.

## How it works (runtime)

`mcp-browser` has two cooperating runtimes:

1. **WebSocket daemon** (`mcp-browser start [--background]`)
   - Listens on `localhost` (default port range `8851-8899`)
   - Accepts browser extension connections
   - Captures console logs and serves DOM/screenshot/extract requests

2. **MCP stdio server** (`mcp-browser mcp`)
   - Runs under an MCP client (Claude Code/Desktop)
   - Exposes the consolidated tool surface (`browser_action`, `browser_query`, `browser_screenshot`, `browser_form`, `browser_extract`)
   - Uses the running daemon for extension-backed operations

## Code map

- CLI entry point: `src/cli/main.py`
- Server orchestration: `src/cli/utils/server.py` (`BrowserMCPServer`)
- WebSocket transport: `src/services/websocket_service.py`
- Console/log handling: `src/services/browser_service.py`
- Storage (JSONL rotation): `src/services/storage_service.py`
- MCP tools: `src/services/mcp_service.py` (5 consolidated tools)
- DOM/extraction protocol: `src/services/dom_interaction_service.py`
- Unified control + fallbacks: `src/services/browser_controller.py`

## Extension sources

There are two relevant extension trees:

- Packaged extension assets (used by `mcp-browser extension …`): `src/extension/`
- Multi-browser unpacked sources (dev/build/deploy): `src/extensions/{chrome,firefox,safari}/`

Local deploy output (gitignored):
- `./mcp-browser-extensions/` (created by `make ext-deploy` or CLI setup helpers)

## Common workflows

### Install dev deps

```bash
make install
```

### Run locally

```bash
make dev-server                 # foreground server
mcp-browser start --background   # daemon (recommended for MCP clients)
```

### Deploy unpacked extensions for manual loading

```bash
make ext-deploy
```

Then load the unpacked extension:
- Chrome: `chrome://extensions` → Load unpacked → `./mcp-browser-extensions/chrome/`

### Tests and quality

```bash
make test
make lint
make format
```

## Documentation expectations

- Keep the tool surface accurate in `docs/reference/MCP_TOOLS.md`.
- Keep the project organization standard up to date in `docs/reference/PROJECT_ORGANIZATION.md`.
- Prefer a single canonical doc per topic; archive or delete superseded docs in `docs/_archive/`.

