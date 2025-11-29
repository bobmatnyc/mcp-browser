# MCP Browser Uninstallation Guide

Complete guide for removing MCP Browser from your system with flexible cleanup options.

## Quick Start

### Basic Uninstall (MCP Config Only)

Remove MCP Browser from Claude Code configuration:

```bash
mcp-browser uninstall
```

This removes only the MCP server configuration entry. Your data, logs, and extensions remain untouched.

### Complete Removal

Remove everything including data, logs, and caches:

```bash
# Preview what would be removed (recommended)
mcp-browser uninstall --clean-all --dry-run

# Remove everything with confirmation
mcp-browser uninstall --clean-all

# Remove everything without confirmation (dangerous)
mcp-browser uninstall --clean-all --yes
```

---

## Uninstall Options Reference

### Command Flags

| Flag | Description | Default | Safety Level |
|------|-------------|---------|--------------|
| `--target` | Which config to update (`claude-code`, `claude-desktop`, `both`) | `claude-code` | ✅ Safe |
| `--clean-local` | Remove project-level files (`./mcp-browser-extension/`, `./.mcp-browser/`) | `false` | ⚠️ Moderate |
| `--clean-global` | Remove global user data (`~/.mcp-browser/`) | `false` | ⚠️ Moderate |
| `--clean-all` | Remove all MCP config, data, and extensions | `false` | 🔴 Destructive |
| `--playwright` | Remove Playwright browser cache | `false` | ⚠️ Moderate |
| `--backup` | Create timestamped backup before removal | `true` | ✅ Safe |
| `--no-backup` | Skip backup creation | `false` | 🔴 Dangerous |
| `--dry-run` | Preview changes without making them | `false` | ✅ Safe |
| `-y`, `--yes` | Skip all confirmation prompts | `false` | 🔴 Dangerous |

### What Gets Removed

#### MCP Configuration Only (Default)
- **Location**: `~/.claude/settings.local.json` or `~/Library/Application Support/Claude/claude_desktop_config.json`
- **What's removed**: Only the `mcp-browser` entry from `mcpServers`
- **What's preserved**: All other MCP servers, your data, logs, extensions

#### `--clean-local` Flag
Removes project-level directories:
- `./mcp-browser-extension/` - Chrome extension files in current directory
- `./.mcp-browser/` - Project-specific configuration and data

#### `--clean-global` Flag
Removes global user data:
- `~/.mcp-browser/data/` - JSONL log files
- `~/.mcp-browser/logs/` - Server and browser logs
- `~/.mcp-browser/config/` - Configuration files
- `~/.mcp-browser/run/` - PID files
- `~/.mcp-browser/` - Parent directory (if empty)

#### `--playwright` Flag
Removes Playwright browser cache:
- **macOS/Linux**: `~/.cache/ms-playwright/`
- **Windows**: `%LOCALAPPDATA%\ms-playwright\`
- **Size**: Can be 200MB-1GB+ depending on browsers installed

#### `--clean-all` Flag
Combines all of the above:
- MCP configuration entries
- Local project files
- Global user data
- Playwright cache (when combined with `--playwright`)

---

## Usage Scenarios

### Scenario 1: Remove MCP Config Only

**Use case**: Want to stop using MCP Browser but keep data for later

```bash
mcp-browser uninstall
```

**What happens**:
- ✅ Removes `mcp-browser` from Claude Code configuration
- ✅ MCP Browser tools no longer available in Claude
- ✅ All data, logs, and extensions preserved

**To restore**: Run `mcp-browser install` again

---

### Scenario 2: Clean Local Project Files

**Use case**: Cleaning up project directory, keeping global data

```bash
mcp-browser uninstall --clean-local
```

**What happens**:
- ✅ Removes MCP config
- ✅ Removes `./mcp-browser-extension/`
- ✅ Removes `./.mcp-browser/`
- ✅ Global data in `~/.mcp-browser/` preserved

**Recovery**: Extension can be re-downloaded with `mcp-browser init --project`

---

### Scenario 3: Clean Global Data

**Use case**: Fresh start while keeping project extension

```bash
mcp-browser uninstall --clean-global
```

**What happens**:
- ✅ Removes MCP config
- ✅ Removes `~/.mcp-browser/` directory
- ✅ Creates backup at `~/.mcp-browser-backups/YYYYMMDD_HHMMSS/`
- ✅ Local project files preserved

**Recovery**: Restore from backup or start fresh with `mcp-browser start`

---

### Scenario 4: Preview Complete Removal

**Use case**: See what would be removed before committing

```bash
mcp-browser uninstall --clean-all --dry-run
```

**What happens**:
- ✅ Shows table of all directories that would be removed
- ✅ Displays total size to be freed
- ✅ No actual changes made
- ✅ Safe to run multiple times

**Example output**:
```
Preview of directories to be removed:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Directory                        ┃     Size ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ ./mcp-browser-extension          │   2.3 MB │
│ ~/.mcp-browser                   │  45.7 MB │
│ ~/.cache/ms-playwright           │ 512.8 MB │
└──────────────────────────────────┴──────────┘

Total size: 560.8 MB
```

---

### Scenario 5: Complete Removal with Backup

**Use case**: Uninstalling but want ability to restore

```bash
mcp-browser uninstall --clean-all
```

**What happens**:
- ✅ Shows preview table
- ✅ Asks for confirmation
- ✅ Creates backup at `~/.mcp-browser-backups/YYYYMMDD_HHMMSS/`
- ✅ Removes all directories
- ✅ Removes MCP configuration

**Backup location**: `~/.mcp-browser-backups/20240321_143022/`

---

### Scenario 6: Complete Removal without Backup

**Use case**: Complete cleanup, no recovery needed

⚠️ **WARNING**: This is irreversible!

```bash
mcp-browser uninstall --clean-all --no-backup --yes
```

**What happens**:
- 🔴 No backup created
- 🔴 No confirmation prompts
- 🔴 Immediate permanent removal
- 🔴 Cannot be undone

**Use with extreme caution!**

---

### Scenario 7: Remove Playwright Cache Only

**Use case**: Free up disk space, keep MCP Browser

```bash
mcp-browser uninstall --playwright --target none
```

**What happens**:
- ✅ Removes Playwright browser cache (200MB-1GB+)
- ✅ MCP configuration preserved
- ✅ MCP Browser data preserved

**To restore**: Run `playwright install chromium` when needed

---

## Backup and Recovery

### Backup Behavior

**When backups are created**:
- ✅ Automatically when using `--clean-global` or `--clean-all`
- ✅ Only for data directories (not MCP config)
- ✅ Disabled with `--no-backup` flag
- ✅ Skipped in `--dry-run` mode

**Backup location**:
```
~/.mcp-browser-backups/
├── 20240321_143022/       # Timestamp format: YYYYMMDD_HHMMSS
│   ├── .mcp-browser/      # Copy of global data
│   └── mcp-browser-extension/  # Copy of extension (if present)
└── 20240322_091544/
    └── .mcp-browser/
```

**What gets backed up**:
- All files in `~/.mcp-browser/`
- All files in `./.mcp-browser/` (if using `--clean-local`)
- Extension directory (if using `--clean-local`)

**What does NOT get backed up**:
- MCP configuration files (can be restored with `mcp-browser install`)
- Playwright cache (can be re-downloaded)

### Restoring from Backup

**Manual restore**:
```bash
# List available backups
ls -lt ~/.mcp-browser-backups/

# Restore specific backup
cp -r ~/.mcp-browser-backups/20240321_143022/.mcp-browser ~/

# Verify restoration
mcp-browser status
```

**Selective restore**:
```bash
# Restore only logs
cp -r ~/.mcp-browser-backups/20240321_143022/.mcp-browser/logs ~/.mcp-browser/

# Restore only data
cp -r ~/.mcp-browser-backups/20240321_143022/.mcp-browser/data ~/.mcp-browser/
```

### Backup Cleanup

**Backups are NOT automatically deleted**. To clean old backups:

```bash
# List all backups with sizes
du -sh ~/.mcp-browser-backups/*

# Remove specific backup
rm -rf ~/.mcp-browser-backups/20240321_143022

# Remove all backups older than 30 days
find ~/.mcp-browser-backups -type d -mtime +30 -exec rm -rf {} +

# Remove all backups
rm -rf ~/.mcp-browser-backups
```

---

## Troubleshooting

### Permission Errors

**Problem**: "Permission denied" when removing directories

**Solution**:
```bash
# Check ownership
ls -la ~/.mcp-browser

# Fix permissions if owned by root (macOS/Linux)
sudo chown -R $USER:$USER ~/.mcp-browser

# Try uninstall again
mcp-browser uninstall --clean-all
```

**Windows**:
- Run Command Prompt as Administrator
- Or use File Explorer to manually delete locked directories

---

### Incomplete Removal

**Problem**: Some directories not removed

**Symptoms**:
```
✗ Could not remove /path/to/directory: Directory not empty
```

**Solution**:
```bash
# Use dry-run to see what's left
mcp-browser uninstall --clean-all --dry-run

# Manually inspect directory
ls -la ~/.mcp-browser

# Force remove manually (be careful!)
rm -rf ~/.mcp-browser
```

---

### Backup Failures

**Problem**: "Backup failed - aborting removal"

**Cause**: Insufficient disk space or permission issues

**Solution**:
```bash
# Check disk space
df -h ~

# Skip backup if space is issue (DANGEROUS!)
mcp-browser uninstall --clean-all --no-backup

# Or free up space first
mcp-browser clean
```

---

### MCP Config Not Found

**Problem**: "Configuration file not found" or "mcp-browser is not configured"

**This is normal!** It means:
- ✅ MCP Browser was never installed
- ✅ Or was already uninstalled
- ✅ Nothing to remove

**No action needed** - you can proceed to remove data with `--clean-global` if desired.

---

### Extension Still Loaded in Chrome

**Problem**: Extension still appears in Chrome after uninstall

**This is expected!** The uninstall command doesn't automatically remove Chrome extensions.

**To remove**:
1. Open `chrome://extensions`
2. Find "MCP Browser Console Capture"
3. Click "Remove"
4. Manually delete extension directory if desired

---

## Advanced Usage

### Scripted Uninstall

**Complete silent removal** (for scripts/automation):

```bash
#!/bin/bash
# Uninstall script for CI/CD or automation

# Complete removal without interaction
mcp-browser uninstall --clean-all --no-backup --yes

# Uninstall package
pip uninstall -y mcp-browser

# Verify removal
[ ! -d ~/.mcp-browser ] && echo "✓ Successfully removed"
```

---

### CI/CD Integration

**Example GitHub Actions workflow**:

```yaml
- name: Cleanup MCP Browser
  run: |
    mcp-browser uninstall --clean-all --no-backup --yes || true
    pip uninstall -y mcp-browser || true
```

**Example Makefile target**:

```makefile
.PHONY: uninstall-clean
uninstall-clean:
	mcp-browser uninstall --clean-all --no-backup --yes
	pip uninstall -y mcp-browser
	rm -rf ~/.mcp-browser-backups
```

---

### Multi-Project Cleanup

**If you have multiple projects using MCP Browser**:

```bash
# Option 1: Remove global data only
mcp-browser uninstall --clean-global

# Option 2: Clean each project individually
cd ~/project1
mcp-browser uninstall --clean-local

cd ~/project2
mcp-browser uninstall --clean-local

# Then clean global data
mcp-browser uninstall --clean-global
```

---

### Selective Cleanup

**Clean specific directories manually**:

```bash
# Remove only logs (keep data)
rm -rf ~/.mcp-browser/logs

# Remove only data (keep logs)
rm -rf ~/.mcp-browser/data

# Remove only Playwright cache
rm -rf ~/.cache/ms-playwright  # macOS/Linux

# Restart fresh (keeps MCP config)
rm -rf ~/.mcp-browser
mcp-browser start
```

---

## Complete Uninstall Checklist

Follow this checklist for complete removal:

- [ ] **Step 1**: Preview removal with dry-run
  ```bash
  mcp-browser uninstall --clean-all --dry-run
  ```

- [ ] **Step 2**: Create manual backup if needed (optional)
  ```bash
  cp -r ~/.mcp-browser ~/.mcp-browser-manual-backup
  ```

- [ ] **Step 3**: Remove MCP Browser data and config
  ```bash
  mcp-browser uninstall --clean-all
  ```

- [ ] **Step 4**: Remove Chrome extension
  - Open `chrome://extensions`
  - Remove "MCP Browser Console Capture"

- [ ] **Step 5**: Uninstall Python package
  ```bash
  pip uninstall mcp-browser    # If installed with pip
  pipx uninstall mcp-browser   # If installed with pipx
  ```

- [ ] **Step 6**: Remove Playwright browsers (optional)
  ```bash
  playwright uninstall --all
  ```

- [ ] **Step 7**: Clean backups (optional)
  ```bash
  rm -rf ~/.mcp-browser-backups
  ```

- [ ] **Step 8**: Restart Claude Code/Desktop
  - Quit and restart to clear MCP server references

- [ ] **Step 9**: Verify complete removal
  ```bash
  # Check for remaining files
  ls -la ~/.mcp-browser        # Should not exist
  ls -la ~/.claude/settings.local.json  # Should not contain mcp-browser

  # Check package
  pip show mcp-browser         # Should show "not found"
  ```

---

## After Uninstallation

### Reinstalling Later

To reinstall MCP Browser:

```bash
# Install package
pip install mcp-browser

# Run quickstart
mcp-browser quickstart
```

Your old backups in `~/.mcp-browser-backups/` will be preserved unless manually deleted.

---

### Switching to Different Version

**Downgrade to older version**:
```bash
# Uninstall current
mcp-browser uninstall --clean-all

# Install specific version
pip install mcp-browser==1.0.0

# Configure
mcp-browser install
```

**Upgrade to newer version**:
```bash
# Upgrade package (keeps data)
pip install --upgrade mcp-browser

# Reconfigure if needed
mcp-browser install --force
```

---

## Getting Help

### Diagnostic Commands

**Before uninstalling**, gather diagnostic info:

```bash
# Check current installation
mcp-browser status
mcp-browser version
mcp-browser config

# List all MCP Browser files
find ~ -name "*mcp-browser*" 2>/dev/null
```

### Support Resources

- **Documentation**: [README.md](../../README.md)
- **Installation Guide**: [INSTALLATION.md](INSTALLATION.md)
- **Issues**: [GitHub Issues](https://github.com/browserpymcp/mcp-browser/issues)
- **CLI Help**: `mcp-browser uninstall --help`

---

## Summary

**Quick Reference**:

| Goal | Command |
|------|---------|
| Remove MCP config only | `mcp-browser uninstall` |
| Preview complete removal | `mcp-browser uninstall --clean-all --dry-run` |
| Complete removal with backup | `mcp-browser uninstall --clean-all` |
| Complete removal without backup | `mcp-browser uninstall --clean-all --no-backup --yes` |
| Clean local project files | `mcp-browser uninstall --clean-local` |
| Clean global user data | `mcp-browser uninstall --clean-global` |
| Remove Playwright cache | `mcp-browser uninstall --playwright` |

**Safety Levels**:
- 🟢 **Safe**: Default uninstall, `--dry-run`, `--backup`
- 🟡 **Moderate**: `--clean-local`, `--clean-global`, `--playwright`
- 🔴 **Destructive**: `--clean-all`, `--no-backup`, `--yes`

**Always use `--dry-run` first to preview changes!**
