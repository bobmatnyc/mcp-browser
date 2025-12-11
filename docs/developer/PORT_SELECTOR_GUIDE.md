# PortSelector Developer Guide

## Overview

The `PortSelector` class provides intelligent port selection for tabs using a priority-based approach. It's designed to automatically route tabs to the most appropriate backend based on multiple heuristics.

## Quick Start

The PortSelector is automatically instantiated by ConnectionManager:

```javascript
const connectionManager = new ConnectionManager();
// PortSelector is available at: connectionManager.portSelector
```

## Usage

### Automatic Tab Registration

The PortSelector is invoked automatically when tabs are registered:

```javascript
// Automatically called by Chrome extension events
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    connectionManager.registerTab(tabId, tab.url);
    // PortSelector.selectPort() is called internally
  }
});
```

### Manual Port Selection

You can also manually select a port:

```javascript
const port = await connectionManager.portSelector.selectPort(tabId, url);
if (port) {
  console.log(`Selected port ${port} for tab ${tabId}`);
}
```

## Priority Levels

### P1: URL Pattern Rules (Highest Priority)

User-defined regex patterns for explicit routing.

**Setup**:
```javascript
// Set URL pattern rules
await connectionManager.saveUrlPatternRules([
  { pattern: 'localhost:3000', port: 8875 },
  { pattern: 'github\\.com.*mcp-browser', port: 8876 },
  { pattern: 'staging\\.example\\.com', port: 8877 }
]);
```

**Example**:
- URL: `https://localhost:3000/app`
- Match: First rule matches → port 8875
- Log: `[PortSelector] P1: URL rule match -> port 8875`

### P2: Domain Cache

Cached domain → port mappings from previous sessions.

**How it works**:
- When a tab is assigned to a port, the domain is cached
- Future tabs from the same domain use the cached port
- Persists across browser restarts

**Example**:
- Tab opened: `https://github.com/user/repo` → assigned to port 8876
- Cache stored: `github.com → 8876`
- Next time: Any github.com URL → port 8876 (if alive)
- Log: `[PortSelector] P2: Domain cache match -> port 8876`

### P3: Project Name Heuristic

Matches URL against project names/paths in the port-project map.

**How it works**:
- Checks if URL contains project name (case-insensitive)
- Checks if URL contains last path segment of project path
- Useful for local dev servers with project names in URLs

**Example**:
- Project: `mcp-browser` at port 8875
- URL: `https://example.com/docs/mcp-browser/api`
- Match: URL contains "mcp-browser" → port 8875
- Log: `[PortSelector] P3: Project name match -> port 8875`

### P4: Most Recently Used (MRU)

Falls back to the last actively used backend.

**How it works**:
- Updated whenever a tab successfully uses a connection
- Provides a sensible default for new tabs
- Only used if the backend is still alive

**Example**:
- Last used port: 8877
- New tab with no matches → tries port 8877
- Log: `[PortSelector] P4: MRU -> port 8877`

### P5: First Active Connection

Uses any available open connection.

**How it works**:
- Iterates through active connections
- Returns first port with open WebSocket
- Ensures new tabs aren't left unassigned

**Example**:
- Active connections: 8875, 8876, 8877
- New tab → assigned to 8875 (first in list)
- Log: `[PortSelector] P5: First active -> port 8875`

### P6: Full Port Scan (Last Resort)

Scans the entire port range (8875-8895) for any available backend.

**How it works**:
- Quick 1-second timeout per port
- Stops at first responding port
- Only used when no other strategy succeeds

**Example**:
- No connections, no cache, no matches
- Scans 8875, 8876, ... until one responds
- Log: `[PortSelector] P6: Scan result -> port 8878`

## Methods Reference

### `selectPort(tabId, url)`

Main entry point for port selection.

**Parameters**:
- `tabId` (number): Tab ID
- `url` (string): Tab URL

**Returns**: `Promise<number|null>` - Selected port or null

**Example**:
```javascript
const port = await portSelector.selectPort(123, 'https://example.com');
```

### `matchUrlRules(url)`

Check URL against pattern rules.

**Returns**: `Promise<number|null>` - Matching port or null

### `matchDomainCache(url)`

Look up port in domain cache.

**Returns**: `Promise<number|null>` - Cached port or null

### `matchProjectName(url)`

Match URL against project names.

**Returns**: `Promise<number|null>` - Matching port or null

### `isBackendAlive(port)`

Quick health check for a backend.

**Parameters**:
- `port` (number): Port to check

**Returns**: `Promise<boolean>` - True if responsive

**Timeout**: 1 second

**Example**:
```javascript
const alive = await portSelector.isBackendAlive(8875);
if (alive) {
  console.log('Backend is responsive');
}
```

### `scanForFirstAvailable()`

Scan port range for available backend.

**Returns**: `Promise<number|null>` - First available port or null

### `updateMRU(port)`

Update most recently used port.

**Parameters**:
- `port` (number): Port to mark as MRU

**Example**:
```javascript
portSelector.updateMRU(8875);
```

## Configuration

### URL Pattern Rules

Store rules in `chrome.storage.local`:

```javascript
// Get current rules
const rules = connectionManager.urlPatternRules;

// Save new rules
await connectionManager.saveUrlPatternRules([
  { pattern: 'localhost', port: 8875 },
  { pattern: 'example\\.com', port: 8876 }
]);

// Rules are loaded automatically on startup
await connectionManager.loadUrlPatternRules();
```

### Domain Cache

Managed automatically, but can be cleared:

```javascript
// Clear domain cache
connectionManager.domainPortMap = {};
await chrome.storage.local.remove('mcp_domain_port_map');
```

## Debugging

### Console Logging

All PortSelector operations include detailed logging:

```javascript
[PortSelector] Selecting port for tab 123, URL: https://example.com
[PortSelector] P2: Domain cache match -> port 8875
[PortSelector] Updated MRU to port 8875
```

### Inspection

Check PortSelector state in console:

```javascript
// Current MRU port
console.log('MRU:', connectionManager.portSelector.mruPort);

// URL pattern rules
console.log('Rules:', connectionManager.urlPatternRules);

// Domain cache
console.log('Domain cache:', connectionManager.domainPortMap);

// Active connections
console.log('Active ports:', connectionManager.getFirstActivePort());
```

## Best Practices

### 1. Use URL Rules for Critical Routing

Define explicit rules for production/staging environments:

```javascript
await connectionManager.saveUrlPatternRules([
  { pattern: 'production\\.example\\.com', port: 8875 },
  { pattern: 'staging\\.example\\.com', port: 8876 }
]);
```

### 2. Let Domain Cache Build Naturally

Don't manually populate domain cache - let it build through usage.

### 3. Monitor MRU Behavior

If MRU is too aggressive, consider adjusting priority order or adding exclusion rules.

### 4. Test Health Checks

Ensure backends respond quickly to WebSocket connections (< 1 second).

### 5. Handle No Port Found

Always check for null result:

```javascript
const port = await portSelector.selectPort(tabId, url);
if (!port) {
  console.log('No port available - tab marked as pending');
  // Tab will be assigned when a backend becomes available
}
```

## Common Scenarios

### Scenario 1: Multi-Project Development

Developer working on 3 projects simultaneously:

```javascript
// Projects running on:
// - mcp-browser (port 8875)
// - my-app (port 8876)
// - client-project (port 8877)

// URLs automatically route to correct backend:
// https://localhost:3000/mcp-browser → 8875 (P3: project name)
// https://localhost:8080/my-app → 8876 (P3: project name)
// https://client.example.com → 8877 (P2: domain cache)
```

### Scenario 2: Production Monitoring

Monitor multiple production environments:

```javascript
// Set URL rules
await connectionManager.saveUrlPatternRules([
  { pattern: 'prod-us\\.example\\.com', port: 8875 },
  { pattern: 'prod-eu\\.example\\.com', port: 8876 },
  { pattern: 'prod-asia\\.example\\.com', port: 8877 }
]);

// Each environment routes to dedicated backend
```

### Scenario 3: Single Backend, Multiple Domains

Work across many domains with one backend:

```javascript
// All tabs route to single backend (port 8875)
// Via P5 (first active) or MRU (P4)
// No configuration needed - just works!
```

## Troubleshooting

### Problem: Tabs Not Assigned to Backend

**Check**:
1. Is at least one backend running?
2. Are backends listening on ports 8875-8895?
3. Check console for `[PortSelector]` logs

**Solution**:
```javascript
// Manually scan for backends
const port = await portSelector.scanForFirstAvailable();
if (port) {
  console.log(`Found backend at ${port}`);
} else {
  console.log('No backends found - check server processes');
}
```

### Problem: Wrong Backend Assigned

**Check**:
1. URL pattern rules (P1 takes priority)
2. Domain cache (might have stale mapping)
3. MRU port (might be wrong project)

**Solution**:
```javascript
// Clear domain cache
connectionManager.domainPortMap = {};
await chrome.storage.local.remove('mcp_domain_port_map');

// Or set explicit URL rules
await connectionManager.saveUrlPatternRules([
  { pattern: 'myapp\\.com', port: 8876 }
]);
```

### Problem: Health Checks Too Slow

**Check**:
- Backend response time
- Network latency

**Note**: Health checks have 1-second timeout. If backends are slow to respond, they may be marked as unavailable.

## API Reference

See `background-enhanced.js` for full implementation details:
- `PortSelector` class (lines 85-317)
- `ConnectionManager.registerTab()` (lines 622-666)
- `ConnectionManager.getFirstActivePort()` (lines 620-627)

## Related Documentation

- Issue #19: Smart Port Selection
- `IMPLEMENTATION_ISSUE_19.md`: Implementation details
- `test_port_selector.js`: Test suite
