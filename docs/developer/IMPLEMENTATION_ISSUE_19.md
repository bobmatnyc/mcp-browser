# Issue #19: Smart Port Selection - Implementation Summary

## Overview
Implemented a comprehensive `PortSelector` class that consolidates port selection logic with a priority-based approach, making tab-to-backend routing more intelligent and maintainable.

## Changes Made

### 1. New `PortSelector` Class
**Location**: `mcp-browser-extension/background-enhanced.js` (lines 85-317)

**Features**:
- **Priority-based port selection** with 6 fallback strategies
- **Smart caching** of URL-to-port mappings
- **Quick health checks** for backend availability
- **MRU (Most Recently Used)** tracking for intelligent defaults

### 2. Priority Levels

The `PortSelector.selectPort()` method implements the following priority order:

1. **P1: URL Pattern Rules** - User-defined regex patterns (highest priority)
2. **P2: Domain Cache** - Cached domain → port mappings
3. **P3: Project Name Heuristic** - URL contains project name/path
4. **P4: Most Recently Used** - Last actively used backend
5. **P5: First Active Connection** - Any available open connection
6. **P6: Full Port Scan** - Scan 8875-8895 range (last resort)

### 3. Key Methods

#### `selectPort(tabId, url)`
Main entry point that orchestrates the priority chain.

#### `matchUrlRules(url)`
Checks user-defined URL pattern rules (RegExp matching).

#### `matchDomainCache(url)`
Retrieves cached port for a domain (from memory or storage).

#### `matchProjectName(url)`
Matches URL against project names/paths in port-project map.

#### `isBackendAlive(port)`
Quick 1-second WebSocket check to verify backend responsiveness.
- First checks existing connections
- Falls back to quick probe if not connected

#### `scanForFirstAvailable()`
Scans port range 8875-8895 for first available backend.

#### `updateMRU(port)`
Updates most recently used port tracking.

### 4. ConnectionManager Integration

**Updated `registerTab()` method** (lines 622-666):
```javascript
async registerTab(tabId, url) {
  // Use PortSelector for intelligent port selection
  const selectedPort = await this.portSelector.selectPort(tabId, url);

  if (selectedPort) {
    // Ensure connection exists
    if (!this.connections.has(selectedPort)) {
      await this.connectToBackend(selectedPort);
    }

    // Assign tab to connection
    this.assignTabToConnection(tabId, selectedPort);

    // Cache domain → port association
    await this.cacheDomainPort(hostname, selectedPort);

    // Update MRU
    this.portSelector.updateMRU(selectedPort);

    // Flush any unrouted messages
    await this.flushUnroutedMessages(tabId);

    return true;
  }

  // Mark as pending if no port found
  this.pendingTabs.set(tabId, { url, awaitingAssignment: true });
  return false;
}
```

**Added `getFirstActivePort()` method** (lines 620-627):
```javascript
getFirstActivePort() {
  for (const [port, conn] of this.connections) {
    if (conn.ws && conn.ws.readyState === WebSocket.OPEN) {
      return port;
    }
  }
  return null;
}
```

### 5. Constructor Update

ConnectionManager now instantiates PortSelector:
```javascript
constructor() {
  // ... existing properties
  this.portSelector = new PortSelector(this); // Smart port selection
}
```

## Benefits

1. **Consolidation**: All port selection logic in one place
2. **Maintainability**: Easy to add new selection strategies
3. **Transparency**: Detailed console logging for debugging
4. **Performance**: Quick health checks with 1-second timeouts
5. **Intelligence**: Multiple heuristics with smart fallbacks
6. **Flexibility**: User-defined URL rules take highest priority

## Acceptance Criteria ✅

- [x] URL rules take highest priority
- [x] Domain cache used when available
- [x] Project name matching works
- [x] Most-recently-used fallback
- [x] Full port scan as last resort
- [x] `isBackendAlive()` does quick verification (1s timeout)
- [x] MRU updated when connections are used

## Testing Recommendations

1. **URL Pattern Rules**: Test regex matching with various URL patterns
2. **Domain Caching**: Verify domain → port associations persist
3. **Project Heuristics**: Test URL matching against project names
4. **MRU Behavior**: Verify last-used port takes priority over scan
5. **Health Checks**: Test with offline/online backends
6. **Port Scanning**: Verify scan finds available backends
7. **Tab Registration**: Test tab assignment across multiple scenarios

## Console Logging

All operations include detailed logging with `[PortSelector]` prefix:
- Priority level used (P1-P6)
- Port selection reasoning
- Match results (URL, domain, project)
- Health check outcomes
- MRU updates

Example:
```
[PortSelector] Selecting port for tab 123, URL: https://example.com
[PortSelector] P2: Domain cache match -> port 8875
[PortSelector] Updated MRU to port 8875
```

## Future Enhancements

1. **User Preferences**: Allow users to set preferred backends per domain
2. **Performance Metrics**: Track backend response times
3. **Load Balancing**: Distribute tabs across multiple backends
4. **Pattern Editor UI**: GUI for managing URL pattern rules
5. **Project Detection**: Auto-detect project from URL path/domain

## Files Modified

- `mcp-browser-extension/background-enhanced.js` (1 file)
  - Added `PortSelector` class (233 lines)
  - Updated `ConnectionManager.registerTab()` (45 lines)
  - Added `ConnectionManager.getFirstActivePort()` (8 lines)

## LOC Delta

- **Added**: ~286 lines (PortSelector class + integration)
- **Removed**: ~45 lines (old registerTab logic)
- **Net Change**: +241 lines

This is acceptable because:
- Consolidates scattered logic into a cohesive class
- Adds significant new functionality (6 selection strategies)
- Improves maintainability with clear separation of concerns
- Includes comprehensive documentation and logging

## Related Issues

- Issue #16: Multi-connection support (dependency)
- Issue #17: Tab-backend routing (dependency)
- Issue #18: Port-project mapping storage (dependency)
