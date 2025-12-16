# Setup Command Fixes Summary

## Issues Fixed

### Issue 1: Extension Version Not Synced During Setup
**Problem**: When deploying extensions via `mcp-browser setup` or `make ext-deploy`, the manifest.json versions were not updated to match the current package version.

**Root Cause**: The `generate_build_info.py` script was reading the OLD manifest version and appending the build timestamp, instead of using the current package version from `_version.py`.

**Solution**: Modified `scripts/generate_build_info.py` to use `build_info["version"]` (from `_version.py`) as the base version, not `manifest.get("version")`.

**Files Modified**:
- `scripts/generate_build_info.py` (line 91): Changed to use package version as base
- `src/cli/commands/setup.py` (lines 245-258): Added version sync logic (redundant but safe)

**Test**:
```bash
# Verify extensions have correct version
./verify_fixes.sh

# Should show: chrome/firefox/safari all have X.Y.Z.HHMM where X.Y.Z matches package version
```

---

### Issue 2: Orphaned Server Detection
**Problem**: When a server is running for THIS project but not in the registry (orphaned), `start_daemon()` doesn't detect it and tries to create a duplicate server.

**Root Cause**: `start_daemon()` only checked the registry, not the actual running processes for THIS project directory.

**Solution**: Added `find_orphaned_project_server()` function that scans ports 8851-8899 for mcp-browser processes and checks their working directory matches the current project.

**Files Modified**:
- `src/cli/utils/daemon.py` (lines 295-366): Added `find_orphaned_project_server()`
- `src/cli/utils/daemon.py` (lines 439-447): Updated `start_daemon()` to detect orphaned servers

**Logic**:
1. Check registry first (existing behavior)
2. If not in registry, scan ports for mcp-browser processes
3. Check process working directory using `lsof -d cwd`
4. If match found, add to registry and reuse

**Test**:
```bash
# 1. Start server
mcp-browser start

# 2. Orphan it (remove from registry)
rm ~/.mcp-browser/server.pid

# 3. Try starting again
mcp-browser start

# Should detect orphaned server and reuse it (not create duplicate)
```

---

## Acceptance Criteria Status

✅ `setup` deploys extension with current package version in manifest.json  
✅ `start_daemon()` finds orphaned servers for THIS project  
✅ Orphaned servers are added to registry and reused  
✅ No duplicate servers created for same project  

---

## Testing

### Automated Tests
```bash
# Run comprehensive validation
./verify_fixes.sh

# Or use Python test script
python3 test_setup_fixes.py
```

### Manual Testing
```bash
# Test Issue 1 (Extension Version Sync)
make ext-deploy
cat mcp-browser-extensions/chrome/manifest.json | grep version
# Should show: "version": "X.Y.Z.HHMM" where X.Y.Z matches src/_version.py

# Test Issue 2 (Orphaned Server Detection)
# Requires dependencies installed: make install
mcp-browser start
rm ~/.mcp-browser/server.pid
mcp-browser start  # Should reuse existing server
```

---

## Code Quality

✅ Passed `ruff` linting  
✅ Formatted with `black`  
⚠️ Pre-existing mypy issues in other files (not related to these changes)  

---

## LOC Delta

**Added**: ~80 lines (orphaned server detection + version sync)  
**Modified**: ~10 lines (updated logic)  
**Net Change**: +90 lines

---

## Files Changed

1. `scripts/generate_build_info.py` - Use package version as base
2. `src/cli/commands/setup.py` - Add version sync after copytree
3. `src/cli/utils/daemon.py` - Add orphaned server detection
4. `test_setup_fixes.py` - Automated validation (new)
5. `verify_fixes.sh` - Comprehensive validation script (new)

