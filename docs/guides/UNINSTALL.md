# Uninstall

## MCP config only (default)

Removes the `mcp-browser` entry from your MCP client configuration (does not delete logs/data/extension files):

```bash
mcp-browser uninstall
```

Use `--target` to choose which client to update (run `mcp-browser uninstall --help` for the full list).

## Cleanup options

Cleanup flags use the legacy uninstaller under the hood. Preview first:

```bash
mcp-browser uninstall --clean-all --dry-run
```

### `--clean-local`

Removes project-level generated files (if present):
- `./mcp-browser-extensions/`
- `./mcp-browser-extension/` (legacy)
- `./.mcp-browser/`

```bash
mcp-browser uninstall --clean-local
```

### `--clean-global`

Removes global user data:
- `~/.mcp-browser/` (config, logs, data, run/)

```bash
mcp-browser uninstall --clean-global
```

### `--clean-all`

Removes MCP config + local + global data:

```bash
mcp-browser uninstall --clean-all
```

### `--playwright` (optional)

Also removes Playwright browser caches (only relevant if you installed Playwright for older CDP experiments):

```bash
mcp-browser uninstall --clean-all --playwright
```

## Uninstall the package

```bash
pip uninstall mcp-browser
# or
pipx uninstall mcp-browser
```
