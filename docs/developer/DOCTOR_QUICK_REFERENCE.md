# Doctor Command Quick Reference

## Usage
```bash
mcp-browser doctor           # Basic diagnostic
mcp-browser doctor -v        # Verbose mode (adds system requirements check)
mcp-browser doctor --fix     # Auto-fix issues
mcp-browser doctor -v --fix  # Verbose + auto-fix
```

## What It Checks

| Check | Description | Auto-Fixable |
|-------|-------------|--------------|
| Configuration | Validates `~/.mcp-browser/config.json` | ✅ Yes |
| Python Dependencies | Checks required packages installed | ❌ No (shows install command) |
| MCP Installer | Verifies `py-mcp-installer` available | ❌ No (optional) |
| Server Status | Reports if server is running | ❌ No (shows start command) |
| Port Availability | Scans ports 8851-8899 | ❌ No |
| Extension Package | Finds `mcp-browser-extension.zip` | ❌ No (shows setup command) |
| MCP Configuration | Checks Claude integration | ❌ No (shows setup command) |
| WebSocket Connectivity | Tests actual connection (if server running) | ❌ No |
| System Requirements | Python, Chrome, Node.js (verbose only) | ❌ No |

## Status Indicators

- ✓ **PASS** (green) - Check passed, no action needed
- ⚠ **WARN** (yellow) - Warning, system should still work
- ✗ **FAIL** (red) - Critical issue, needs fixing

## Common Scenarios

### Fresh Install
```bash
$ mcp-browser doctor
Summary: 2 passed, 5 warnings, 1 failed
Run 'mcp-browser setup' to fix issues
```

### After Setup
```bash
$ mcp-browser doctor
Summary: 7 passed, 1 warnings, 0 failed
Some warnings present - system should still work
```

### Production Ready
```bash
$ mcp-browser doctor
Summary: 8 passed, 0 warnings, 0 failed
✓ All checks passed! System is healthy.
```

## Fix Commands

| Issue | Fix Command |
|-------|-------------|
| Config missing | `mcp-browser setup` or `mcp-browser doctor --fix` |
| Server not running | `mcp-browser start` |
| Extension not found | `mcp-browser setup` |
| MCP not configured | `mcp-browser setup` |
| Missing dependencies | `pip install websockets click rich aiohttp mcp` |
| MCP installer missing | `pip install py-mcp-installer` (optional) |

## Important Notes

- ✅ **Does NOT auto-start server** (just reports status)
- ✅ **Does NOT require browser connection**
- ✅ **Does NOT modify system** unless `--fix` is used
- ✅ **Safe to run anytime** - read-only by default
- ✅ **Fast** - completes in < 2 seconds

## Troubleshooting

### WebSocket Connection Fails
```bash
# Check if server is actually running
mcp-browser status

# Restart server
# (Note: There's no 'stop' command, kill the process manually)
ps aux | grep mcp-browser
kill <PID>
mcp-browser start
```

### All Ports in Use
```bash
# Find what's using the ports
lsof -i :8851-8899

# Kill specific process
kill <PID>
```

### Extension Not Found
```bash
# Run setup to build extension
mcp-browser setup

# Verify it exists
ls -lh dist/mcp-browser-extension.zip
```

## Integration Examples

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
- name: Health Check
  run: |
    mcp-browser doctor --verbose
    if [ $? -ne 0 ]; then
      echo "Doctor check failed"
      exit 1
    fi
```

### Pre-Deployment Script
```bash
#!/bin/bash
# deploy.sh

echo "Running health check..."
mcp-browser doctor --verbose

if [ $? -ne 0 ]; then
    echo "❌ Health check failed. Fix issues before deploying."
    exit 1
fi

echo "✅ Health check passed. Proceeding with deployment..."
# ... deployment steps
```

### Support Ticket Template
```markdown
## System Diagnostics

Please run this command and paste the output:

```bash
mcp-browser doctor --verbose
```

This helps us identify the issue quickly.
```

## For Developers

### Adding New Checks

1. Create check function in `src/cli/commands/doctor.py`:
```python
def _check_your_feature() -> dict:
    """Check your feature."""
    # Perform check
    if feature_ok:
        return {
            "name": "Your Feature",
            "status": "pass",
            "message": "Feature is working",
        }
    else:
        return {
            "name": "Your Feature",
            "status": "fail",
            "message": "Feature broken",
            "fix": "Run: fix-command",
            "fix_func": lambda: fix_it(),  # Optional auto-fix
        }
```

2. Add to `_doctor_command()`:
```python
console.print("[cyan]→ Checking your feature...[/cyan]")
results.append(_check_your_feature())
```

3. Test it:
```bash
mcp-browser doctor
```

## Related Commands

- `mcp-browser status` - Quick server status check
- `mcp-browser setup` - Full installation setup
- `mcp-browser start` - Start the server
- `mcp-browser quickstart` - Interactive setup wizard
