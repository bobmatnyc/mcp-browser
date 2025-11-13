# Uninstall Command - Usage Examples

This document provides practical examples of using the newly implemented `uninstall` command.

## Basic Usage

### Uninstall from Claude Code (Default)
```bash
mcp-browser uninstall
```

**Output:**
```
╭────────── Uninstallation ──────────╮
│ Removing MCP Browser Configuration │
│                                    │
│ Target: claude-code                │
╰────────────────────────────────────╯

Removing from Claude Code...
✓ Removed mcp-browser from /Users/user/.claude/settings.local.json

╭───────────────────── Success ─────────────────────╮
│ ✓ Uninstallation Complete!                       │
│                                                  │
│ Removed mcp-browser from 1 configuration(s)      │
│                                                  │
│ Next steps:                                      │
│ 1. Restart Claude Code or Claude Desktop         │
│ 2. The mcp-browser MCP server will no longer be │
│    available                                     │
│                                                  │
│ To uninstall the package:                        │
│   pip uninstall mcp-browser                      │
╰──────────────────────────────────────────────────╯
```

---

## Target-Specific Uninstall

### Uninstall from Claude Desktop Only
```bash
mcp-browser uninstall --target claude-desktop
```

**Output:**
```
╭────────── Uninstallation ──────────╮
│ Removing MCP Browser Configuration │
│                                    │
│ Target: claude-desktop             │
╰────────────────────────────────────╯

Removing from Claude Desktop...
✓ Removed mcp-browser from /Users/user/Library/Application Support/Claude/claude_desktop_config.json

╭───────────────────── Success ─────────────────────╮
│ ✓ Uninstallation Complete!                       │
│                                                  │
│ Removed mcp-browser from 1 configuration(s)      │
│ ...                                              │
╰──────────────────────────────────────────────────╯
```

### Uninstall from Both Targets
```bash
mcp-browser uninstall --target both
```

**Output:**
```
╭────────── Uninstallation ──────────╮
│ Removing MCP Browser Configuration │
│                                    │
│ Target: both                       │
╰────────────────────────────────────╯

Removing from Claude Code...
✓ Removed mcp-browser from /Users/user/.claude/settings.local.json

Removing from Claude Desktop...
✓ Removed mcp-browser from /Users/user/Library/Application Support/Claude/claude_desktop_config.json

╭───────────────────── Success ─────────────────────╮
│ ✓ Uninstallation Complete!                       │
│                                                  │
│ Removed mcp-browser from 2 configuration(s)      │
│ ...                                              │
╰──────────────────────────────────────────────────╯
```

---

## Error Scenarios

### When mcp-browser is Not Configured
```bash
mcp-browser uninstall
```

**Output:**
```
╭────────── Uninstallation ──────────╮
│ Removing MCP Browser Configuration │
│                                    │
│ Target: claude-code                │
╰────────────────────────────────────╯

Removing from Claude Code...
mcp-browser is not configured

╭─────────────── Not Found ───────────────╮
│ ⚠ Nothing to Remove                    │
│                                        │
│ mcp-browser was not found in any of    │
│ the specified configurations           │
│                                        │
│ To install, use: mcp-browser install   │
╰────────────────────────────────────────╯
```

### When Config File Doesn't Exist
```bash
mcp-browser uninstall
```

**Output:**
```
╭────────── Uninstallation ──────────╮
│ Removing MCP Browser Configuration │
│                                    │
│ Target: claude-code                │
╰────────────────────────────────────╯

Removing from Claude Code...
Configuration file not found: /Users/user/.claude/settings.local.json

╭─────────────── Not Found ───────────────╮
│ ⚠ Nothing to Remove                    │
│                                        │
│ mcp-browser was not found in any of    │
│ the specified configurations           │
│                                        │
│ To install, use: mcp-browser install   │
╰────────────────────────────────────────╯
```

### Partial Success (One Target Fails)
```bash
mcp-browser uninstall --target both
```

**Output (when only Claude Code has mcp-browser):**
```
╭────────── Uninstallation ──────────╮
│ Removing MCP Browser Configuration │
│                                    │
│ Target: both                       │
╰────────────────────────────────────╯

Removing from Claude Code...
✓ Removed mcp-browser from /Users/user/.claude/settings.local.json

Removing from Claude Desktop...
mcp-browser is not configured

╭────────────── Warning ──────────────╮
│ ⚠ Partial Removal                  │
│                                    │
│ Removed from 1 of 2 targets        │
│ Not found in 1 target(s)           │
│                                    │
│ Check messages above for details   │
╰────────────────────────────────────╯
```

---

## Help and Information

### View Help
```bash
mcp-browser uninstall --help
```

**Output:**
```
Usage: mcp-browser uninstall [OPTIONS]

  🗑️ Remove MCP Browser configuration from Claude Code/Desktop.

  Removes the mcp-browser configuration from Claude Code or Claude Desktop
  MCP server settings. This does not uninstall the package itself.

  Examples:
    mcp-browser uninstall                         # Remove from Claude Code
    mcp-browser uninstall --target claude-desktop # Remove from Claude Desktop
    mcp-browser uninstall --target both           # Remove from both

  Configuration locations:
    Claude Code:    ~/.claude/settings.local.json
    Claude Desktop: OS-specific location
      • macOS:   ~/Library/Application Support/Claude/
      • Linux:   ~/.config/Claude/
      • Windows: %APPDATA%/Claude/

  After uninstallation:
    1. Restart Claude Code or Claude Desktop
    2. The 'mcp-browser' MCP server will no longer be available
    3. To uninstall the package itself, use: pip uninstall mcp-browser

Options:
  --target [claude-code|claude-desktop|both]
                                  Target to uninstall from (default: claude-
                                  code)
  -h, --help                      Show this message and exit.
```

---

## Common Workflows

### Complete Removal Workflow
```bash
# 1. Uninstall from all MCP configurations
mcp-browser uninstall --target both

# 2. Uninstall the package itself
pip uninstall mcp-browser

# 3. Remove project extension directory (optional)
rm -rf mcp-browser-extension/
```

### Reinstall Workflow
```bash
# 1. Uninstall from MCP config
mcp-browser uninstall

# 2. Reinstall with different settings
mcp-browser install --force
```

### Clean Slate Workflow
```bash
# 1. Remove from both targets
mcp-browser uninstall --target both

# 2. Remove package
pip uninstall mcp-browser

# 3. Reinstall fresh
pip install mcp-browser

# 4. Install fresh MCP config
mcp-browser install --target both
```

---

## Configuration File Examples

### Before Uninstall
**~/.claude/settings.local.json:**
```json
{
  "mcpServers": {
    "mcp-browser": {
      "command": "mcp-browser",
      "args": ["mcp"]
    },
    "other-server": {
      "command": "other-command",
      "args": ["arg1"]
    }
  }
}
```

### After Uninstall
**~/.claude/settings.local.json:**
```json
{
  "mcpServers": {
    "other-server": {
      "command": "other-command",
      "args": ["arg1"]
    }
  }
}
```

**Note:** Other server entries are preserved, only mcp-browser is removed.

---

## Shell Completion

The `uninstall` command supports tab completion in bash, zsh, and fish:

### Bash/Zsh
```bash
mcp-browser uninstall --<TAB>
# Completes: --target --help

mcp-browser uninstall --target <TAB>
# Completes: claude-code claude-desktop both
```

### Fish
```fish
mcp-browser uninstall --<TAB>
# Shows: --target --help with descriptions
```

---

## Exit Codes

The `uninstall` command uses the following exit codes:

- `0` - Success (even if mcp-browser wasn't configured)
- `0` - Partial success (some targets succeeded)
- `0` - Not found (file doesn't exist or not configured)

**Note:** The command always exits with code 0 to indicate graceful handling. Success is determined by the output message, not the exit code.

---

## Related Commands

- `mcp-browser install` - Install MCP Browser configuration
- `mcp-browser status` - Check installation status
- `mcp-browser doctor` - Diagnose configuration issues
- `pip uninstall mcp-browser` - Uninstall the package itself

---

## Tips and Best Practices

1. **Always restart Claude after uninstalling** - Changes to MCP configuration require a restart
2. **Check status before uninstalling** - Use `mcp-browser status` to verify what's configured
3. **Use --target both for clean removal** - Ensures removal from all possible locations
4. **Don't confuse with pip uninstall** - `mcp-browser uninstall` only removes MCP config, not the package
5. **Backup configs if needed** - Consider backing up config files before uninstalling if you have custom configurations

---

## Troubleshooting

### "Configuration file not found"
**Cause:** Config file doesn't exist
**Solution:** Nothing to uninstall, you can safely install fresh

### "mcp-browser is not configured"
**Cause:** Config file exists but doesn't have mcp-browser entry
**Solution:** Nothing to uninstall, already clean

### "No mcpServers configuration found"
**Cause:** Config file exists but has no mcpServers section
**Solution:** Nothing to uninstall, config is clean

---

## Platform-Specific Notes

### macOS
- Claude Code config: `~/.claude/settings.local.json`
- Claude Desktop config: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Linux
- Claude Code config: `~/.claude/settings.local.json`
- Claude Desktop config: `~/.config/Claude/claude_desktop_config.json`

### Windows
- Claude Code config: `%USERPROFILE%\.claude\settings.local.json`
- Claude Desktop config: `%APPDATA%\Claude\claude_desktop_config.json`

---

**Last Updated:** 2025-11-12
**Command Version:** mcp-browser 2.0.9
