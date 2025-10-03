/**
 * Enhanced Service worker for MCP Browser extension
 * Features:
 * - Multi-server discovery
 * - Project identification
 * - Smart port selection
 */

// Configuration
const PORT_RANGE = { start: 8875, end: 8895 };
const SCAN_INTERVAL = 30000; // Scan for servers every 30 seconds

// State management
let activeServers = new Map(); // port -> server info
let currentConnection = null;
let messageQueue = [];
let scanTimer = null;

// Connection status
const connectionStatus = {
  connected: false,
  port: null,
  projectName: null,
  projectPath: null,
  lastError: null,
  messageCount: 0,
  connectionTime: null,
  availableServers: []
};

/**
 * Scan all ports for running MCP Browser servers
 * @returns {Promise<Array>} Array of available servers
 */
async function scanForServers() {
  console.log(`[MCP Browser] Scanning ports ${PORT_RANGE.start}-${PORT_RANGE.end} for servers...`);
  const servers = [];

  for (let port = PORT_RANGE.start; port <= PORT_RANGE.end; port++) {
    const serverInfo = await probePort(port);
    if (serverInfo) {
      servers.push(serverInfo);
      activeServers.set(port, serverInfo);
    }
  }

  connectionStatus.availableServers = servers;
  console.log(`[MCP Browser] Found ${servers.length} active server(s):`, servers);
  return servers;
}

/**
 * Probe a single port for MCP Browser server
 * @param {number} port - Port to probe
 * @returns {Promise<Object|null>} Server info or null
 */
async function probePort(port) {
  return new Promise((resolve) => {
    let ws = null; // Declare ws in the proper scope

    const timeout = setTimeout(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      resolve(null);
    }, 1000);

    try {
      ws = new WebSocket(`ws://localhost:${port}`);

      ws.onopen = () => {
        // Send server info request
        ws.send(JSON.stringify({ type: 'server_info' }));

        // Wait for response
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'server_info_response') {
              clearTimeout(timeout);
              ws.close();
              // Only accept servers with valid project information
              if (data.project_name && data.project_name !== 'Unknown') {
                resolve({
                  port: port,
                  projectName: data.project_name,
                  projectPath: data.project_path || '',
                  version: data.version || '1.0.0',
                  connected: false
                });
              } else {
                // Not a valid MCP Browser server
                ws.close();
                resolve(null);
              }
            }
          } catch (e) {
            // Not a valid response
          }
        };

        // No fallback - only accept servers that respond with proper server_info
        // This ensures we only show actual MCP Browser servers
      };

      ws.onerror = () => {
        clearTimeout(timeout);
        resolve(null);
      };

      ws.onclose = () => {
        clearTimeout(timeout);
      };
    } catch (error) {
      clearTimeout(timeout);
      resolve(null);
    }
  });
}

/**
 * Connect to a specific server
 * @param {number} port - Port to connect to
 * @param {Object} serverInfo - Optional server info
 * @returns {Promise<boolean>} Success status
 */
async function connectToServer(port, serverInfo = null) {
  console.log(`[MCP Browser] Connecting to server on port ${port}...`);

  // Disconnect from current server if connected
  if (currentConnection) {
    currentConnection.close();
    currentConnection = null;
  }

  try {
    const ws = new WebSocket(`ws://localhost:${port}`);

    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        if (ws && ws.readyState !== WebSocket.CLOSED) {
          ws.close();
        }
        resolve(false);
      }, 3000);

      ws.onopen = () => {
        clearTimeout(timeout);
        currentConnection = ws;
        setupWebSocketHandlers(ws);

        // Update connection status
        connectionStatus.connected = true;
        connectionStatus.port = port;
        connectionStatus.connectionTime = Date.now();
        connectionStatus.lastError = null;

        if (serverInfo) {
          connectionStatus.projectName = serverInfo.projectName;
          connectionStatus.projectPath = serverInfo.projectPath;
        }

        // Update extension badge
        chrome.action.setBadgeText({ text: String(port) });
        chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });

        console.log(`[MCP Browser] Connected to port ${port} (${connectionStatus.projectName})`);

        // Send queued messages
        flushMessageQueue();

        resolve(true);
      };

      ws.onerror = (error) => {
        clearTimeout(timeout);
        connectionStatus.lastError = `Connection error on port ${port}`;
        console.error(`[MCP Browser] Connection error:`, error);
        resolve(false);
      };

      ws.onclose = () => {
        clearTimeout(timeout);
        if (!connectionStatus.connected) {
          resolve(false);
        }
      };
    });
  } catch (error) {
    console.error(`[MCP Browser] Failed to connect to port ${port}:`, error);
    return false;
  }
}

/**
 * Set up WebSocket event handlers
 * @param {WebSocket} ws - WebSocket connection
 */
function setupWebSocketHandlers(ws) {
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    } catch (error) {
      console.error('[MCP Browser] Failed to parse server message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('[MCP Browser] WebSocket error:', error);
    connectionStatus.lastError = 'WebSocket error';
  };

  ws.onclose = () => {
    console.log('[MCP Browser] Connection closed');
    currentConnection = null;
    connectionStatus.connected = false;
    connectionStatus.port = null;
    connectionStatus.projectName = null;

    // Update extension badge
    chrome.action.setBadgeText({ text: '!' });
    chrome.action.setBadgeBackgroundColor({ color: '#F44336' });

    // Try to reconnect after a delay
    setTimeout(() => {
      autoConnect();
    }, 5000);
  };
}

/**
 * Auto-connect to the best available server
 */
async function autoConnect() {
  const servers = await scanForServers();

  if (servers.length === 0) {
    console.log('[MCP Browser] No servers found');
    connectionStatus.lastError = 'No MCP Browser servers found';
    return;
  }

  // If only one server, connect to it
  if (servers.length === 1) {
    await connectToServer(servers[0].port, servers[0]);
    return;
  }

  // If multiple servers, prefer the first one (could be enhanced with preferences)
  // In the future, we could remember the last connected project
  await connectToServer(servers[0].port, servers[0]);
}

/**
 * Handle messages from server
 * @param {Object} data - Message data
 */
function handleServerMessage(data) {
  // Handle navigation, DOM commands, etc.
  // (Same as original implementation)

  if (data.type === 'navigate') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.update(tabs[0].id, { url: data.url });
      }
    });
  }
  // ... other message handlers
}

/**
 * Send message to server
 * @param {Object} message - Message to send
 * @returns {boolean} Success status
 */
function sendToServer(message) {
  if (currentConnection && currentConnection.readyState === WebSocket.OPEN) {
    currentConnection.send(JSON.stringify(message));
    connectionStatus.messageCount++;
    return true;
  } else {
    // Queue message if not connected
    messageQueue.push(message);
    if (messageQueue.length > 1000) {
      messageQueue.shift(); // Remove oldest message if queue is too large
    }
    return false;
  }
}

/**
 * Flush queued messages
 */
function flushMessageQueue() {
  if (!currentConnection || currentConnection.readyState !== WebSocket.OPEN) return;

  while (messageQueue.length > 0) {
    const message = messageQueue.shift();
    currentConnection.send(JSON.stringify(message));
    connectionStatus.messageCount++;
  }
}

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'console_messages') {
    // Batch console messages
    const batchMessage = {
      type: 'batch',
      messages: request.messages,
      url: request.url,
      timestamp: request.timestamp,
      tabId: sender.tab?.id,
      frameId: sender.frameId
    };

    if (!sendToServer(batchMessage)) {
      console.log('[MCP Browser] WebSocket not connected, message queued');
    }

    sendResponse({ received: true });
  } else if (request.type === 'get_status') {
    sendResponse(connectionStatus);
  } else if (request.type === 'scan_servers') {
    // Scan for available servers
    scanForServers().then(servers => {
      sendResponse({ servers: servers });
    });
    return true; // Keep channel open for async response
  } else if (request.type === 'connect_to_server') {
    // Connect to specific server
    const { port, serverInfo } = request;
    connectToServer(port, serverInfo).then(success => {
      sendResponse({ success: success });
    });
    return true; // Keep channel open for async response
  } else if (request.type === 'disconnect') {
    // Disconnect from current server
    if (currentConnection) {
      currentConnection.close();
      currentConnection = null;
    }
    sendResponse({ received: true });
  }
});

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('[MCP Browser] Extension installed');

  // Set initial badge
  chrome.action.setBadgeText({ text: '?' });
  chrome.action.setBadgeBackgroundColor({ color: '#9E9E9E' });

  // Inject content script into all existing tabs
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach(tab => {
      if (tab.url && !tab.url.startsWith('chrome://')) {
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        }).catch(err => console.log('Failed to inject into tab:', tab.id, err));
      }
    });
  });

  // Start server scanning
  autoConnect();

  // Set up periodic scanning
  scanTimer = setInterval(() => {
    scanForServers();
  }, SCAN_INTERVAL);
});

// Handle browser startup
chrome.runtime.onStartup.addListener(() => {
  console.log('[MCP Browser] Browser started');
  autoConnect();

  // Set up periodic scanning
  scanTimer = setInterval(() => {
    scanForServers();
  }, SCAN_INTERVAL);
});

// Initialize on load
autoConnect();