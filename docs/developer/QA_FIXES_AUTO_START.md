# QA Fixes: Auto-Start Functionality

## Summary
Fixed two critical issues in auto-start functionality identified during QA testing.

## Issue 1: daemon.py Incorrect Command ✅

**File**: `src/cli/utils/daemon.py`

**Problem**:
- Used `python -m mcp_browser` to start daemon
- Failed because package doesn't have `__main__.py`
- Error: "No module named mcp_browser.__main__"

**Fix**:
- Added `import shutil` to imports
- Use `shutil.which('mcp-browser')` to find CLI executable
- Fallback to checking relative to Python executable
- Command now: `mcp-browser start --port <port> --daemon`

**Changes**:
```python
# Before:
cmd = [sys.executable, "-m", "mcp_browser", "start", "--port", str(port), "--daemon"]

# After:
mcp_browser_path = shutil.which('mcp-browser')
if not mcp_browser_path:
    mcp_browser_path = os.path.join(os.path.dirname(sys.executable), 'mcp-browser')
    if not os.path.exists(mcp_browser_path):
        return False, None, None

cmd = [mcp_browser_path, "start", "--port", str(port), "--daemon"]
```

## Issue 2: validation.py Incorrect Port Range ✅

**File**: `src/cli/utils/validation.py`

**Problem**:
- Used old port range (8875-8896) for server status check
- Didn't match actual port range (8851-8899) in daemon module
- Could miss running server on correct ports

**Fix**:
- Import `get_server_status()` from daemon module
- Replace manual port scanning with authoritative status check
- Also updated `check_system_requirements()` to use correct port range constants

**Changes**:
```python
# Before (check_installation_status):
for port in range(8875, 8896):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1)
        if s.connect_ex(("localhost", port)) == 0:
            status["server_running"] = True
            status["server_port"] = port
            break

# After:
from .daemon import get_server_status

is_running, pid, port = get_server_status()
status["server_running"] = is_running
if port:
    status["server_port"] = port

# Also updated check_system_requirements:
from .daemon import PORT_RANGE_START, PORT_RANGE_END

for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
    # ... port availability check
```

## Testing Checklist

### Basic Functionality
- [ ] `mcp-browser stop` - Stop any running server
- [ ] `mcp-browser browser status` - Should auto-start server
- [ ] Verify server starts successfully with correct port
- [ ] Verify status shows server as running with correct port

### Port Range
- [ ] Server starts on port in range 8851-8899
- [ ] Status correctly detects server on new port range
- [ ] System requirements check shows correct port range

### Error Handling
- [ ] Graceful failure if `mcp-browser` executable not found
- [ ] Clear error messages if server can't start
- [ ] Stale PID file is cleaned up correctly

## Files Modified

1. **src/cli/utils/daemon.py**
   - Added `import shutil`
   - Fixed `start_daemon()` to use CLI executable instead of `python -m`

2. **src/cli/utils/validation.py**
   - Updated `check_installation_status()` to use `daemon.get_server_status()`
   - Updated `check_system_requirements()` to use correct port range constants

## LOC Delta
- Added: 9 lines (shutil import, executable lookup, port range imports)
- Removed: 8 lines (old port scanning logic)
- Net Change: +1 line
- Phase: Bug Fix

## Next Steps

1. **Test Auto-Start**: Run `mcp-browser stop && mcp-browser browser status`
2. **Verify Port**: Check that server starts on correct port range (8851-8899)
3. **Test Status**: Verify `mcp-browser status` shows accurate server info
4. **Test Recovery**: Ensure stale PID files are handled correctly
