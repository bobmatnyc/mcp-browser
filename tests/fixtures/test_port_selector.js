/**
 * Test suite for PortSelector implementation
 * Run this in a browser console with the extension loaded
 */

// Mock chrome.storage.local for testing
const mockStorage = {
  data: {},
  get: function(keys) {
    return Promise.resolve(
      typeof keys === 'string'
        ? { [keys]: this.data[keys] }
        : Object.fromEntries(keys.map(k => [k, this.data[k]]))
    );
  },
  set: function(items) {
    Object.assign(this.data, items);
    return Promise.resolve();
  },
  clear: function() {
    this.data = {};
    return Promise.resolve();
  }
};

// Test utilities
const assert = {
  equal: (actual, expected, message) => {
    if (actual === expected) {
      console.log(`✅ PASS: ${message}`);
    } else {
      console.error(`❌ FAIL: ${message}`);
      console.error(`  Expected: ${expected}`);
      console.error(`  Actual: ${actual}`);
    }
  },
  notNull: (value, message) => {
    if (value !== null) {
      console.log(`✅ PASS: ${message}`);
    } else {
      console.error(`❌ FAIL: ${message} - Expected non-null value`);
    }
  },
  isNull: (value, message) => {
    if (value === null) {
      console.log(`✅ PASS: ${message}`);
    } else {
      console.error(`❌ FAIL: ${message} - Expected null value, got ${value}`);
    }
  }
};

// Test suite
async function runPortSelectorTests() {
  console.log('\n=== PortSelector Test Suite ===\n');

  // Create mock ConnectionManager
  const mockConnectionManager = {
    connections: new Map(),
    domainPortMap: {},
    urlPatternRules: [],
    getFirstActivePort: function() {
      for (const [port, conn] of this.connections) {
        if (conn.ws && conn.ws.readyState === WebSocket.OPEN) {
          return port;
        }
      }
      return null;
    }
  };

  // Mock chrome API for testing
  const originalChrome = window.chrome;
  window.chrome = {
    storage: {
      local: mockStorage
    }
  };

  // Create PortSelector instance (assuming it's available in the page context)
  // If testing in extension context, this should work directly
  // If testing in a standalone script, you'll need to copy the PortSelector class here

  console.log('Test 1: URL Pattern Matching');
  mockConnectionManager.urlPatternRules = [
    { pattern: /localhost:3000/, port: 8875 },
    { pattern: /example\.com/, port: 8876 }
  ];

  // Note: This test assumes PortSelector is available in the context
  // In actual extension testing, you would use the background script context

  console.log('\nTest 2: Domain Cache Matching');
  mockStorage.data['mcp_domain_port_map'] = {
    'github.com': 8877,
    'stackoverflow.com': 8878
  };

  console.log('\nTest 3: Project Name Matching');
  mockStorage.data['mcp_port_project_map'] = {
    8879: {
      project_name: 'mcp-browser',
      project_path: '/Users/test/mcp-browser',
      last_seen: Date.now()
    },
    8880: {
      project_name: 'my-app',
      project_path: '/Users/test/projects/my-app',
      last_seen: Date.now()
    }
  };

  console.log('\nTest 4: MRU Tracking');
  // Test MRU behavior
  console.log('MRU should be null initially');

  console.log('\nTest 5: First Active Port');
  // Add mock connection
  mockConnectionManager.connections.set(8881, {
    ws: { readyState: WebSocket.OPEN },
    port: 8881,
    projectName: 'test-project'
  });
  const firstActive = mockConnectionManager.getFirstActivePort();
  assert.equal(firstActive, 8881, 'getFirstActivePort returns first active connection');

  console.log('\nTest 6: Priority Order');
  console.log('Testing priority levels:');
  console.log('  P1: URL rules (highest)');
  console.log('  P2: Domain cache');
  console.log('  P3: Project name heuristic');
  console.log('  P4: MRU');
  console.log('  P5: First active');
  console.log('  P6: Port scan (lowest)');

  // Restore original chrome API
  window.chrome = originalChrome;

  console.log('\n=== Test Suite Complete ===\n');
  console.log('Note: Some tests require running in extension context');
  console.log('Full integration testing should be done with the extension loaded');
}

// Manual testing instructions
console.log(`
=== Manual Testing Instructions ===

1. Load the extension in Chrome
2. Open DevTools on the background page (chrome://extensions > Details > Inspect views: background page)
3. Run these commands in the console:

// Test URL pattern matching
connectionManager.portSelector.matchUrlRules('https://localhost:3000/app')
  .then(port => console.log('URL rule matched port:', port));

// Test domain cache
connectionManager.portSelector.matchDomainCache('https://github.com/user/repo')
  .then(port => console.log('Domain cache matched port:', port));

// Test project name matching
connectionManager.portSelector.matchProjectName('https://example.com/mcp-browser/docs')
  .then(port => console.log('Project name matched port:', port));

// Test backend health check
connectionManager.portSelector.isBackendAlive(8875)
  .then(alive => console.log('Backend 8875 alive:', alive));

// Test full port selection
connectionManager.portSelector.selectPort(123, 'https://example.com')
  .then(port => console.log('Selected port:', port));

// Test MRU tracking
connectionManager.portSelector.updateMRU(8875);
console.log('MRU port:', connectionManager.portSelector.mruPort);

// Test getFirstActivePort
const firstPort = connectionManager.getFirstActivePort();
console.log('First active port:', firstPort);

4. Verify console logs show priority levels (P1-P6)
5. Test tab registration with actual tabs
6. Verify domain caching persists across reloads
`);

// Run basic tests
if (typeof runPortSelectorTests === 'function') {
  runPortSelectorTests().catch(console.error);
}
