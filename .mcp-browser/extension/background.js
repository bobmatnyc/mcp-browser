/**
 * Service worker for MCP Browser extension
 */

// WebSocket connection state
let ws = null;
let port = 8875;
const MAX_PORT = 8895;
let reconnectTimer = null;
let messageQueue = [];
let isConnected = false;

// Connection status
const connectionStatus = {
  connected: false,
  port: null,
  lastError: null,
  messageCount: 0,
  connectionTime: null
};

// Find available port and connect
async function findAndConnect() {
  const startPort = 8875; // Always start from beginning of range
  console.log(`Starting port scan from ${startPort} to ${MAX_PORT}`);
  for (let p = startPort; p <= MAX_PORT; p++) {
    console.log(`Scanning port ${p}...`);
    if (await tryConnect(p)) {
      port = p;
      console.log(`Successfully connected on port ${p}`);
      connectionStatus.lastError = null; // Clear any previous errors
      return true;
    }
  }
  console.error(`Failed to find WebSocket server in port range ${startPort}-${MAX_PORT}`);
  connectionStatus.lastError = 'No WebSocket server found in ports 8875-8895';
  return false;
}

// Try to connect to a specific port
function tryConnect(targetPort) {
  return new Promise((resolve) => {
    try {
      // Try both localhost and 127.0.0.1 to handle IPv4/IPv6 issues
      const urls = [
        `ws://localhost:${targetPort}`,
        `ws://127.0.0.1:${targetPort}`,
        `ws://[::1]:${targetPort}`
      ];

      let currentUrlIndex = 0;

      function attemptConnection() {
        if (currentUrlIndex >= urls.length) {
          resolve(false);
          return;
        }

        const url = urls[currentUrlIndex];
        console.log(`Attempting WebSocket connection to ${url}`);
        const testWs = new WebSocket(url);

        const timeout = setTimeout(() => {
          console.log(`Connection timeout for ${url}`);
          testWs.close();
          currentUrlIndex++;
          attemptConnection();
        }, 1000);

        testWs.onopen = () => {
          clearTimeout(timeout);
          ws = testWs;
          setupWebSocket();
          connectionStatus.connected = true;
          connectionStatus.port = targetPort;
          connectionStatus.lastError = null;
          connectionStatus.connectionTime = Date.now();
          isConnected = true;

          // Update extension icon
          chrome.action.setBadgeText({ text: String(targetPort) });
          chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });

          console.log(`Successfully connected to WebSocket at ${url}`);

          // Don't send connection_init - server doesn't handle it
          // Server expects 'batch' or 'navigate' messages

          // Send queued messages
          flushMessageQueue();

          resolve(true);
        };

        testWs.onerror = (error) => {
          console.error(`WebSocket error for ${url}:`, error);
          clearTimeout(timeout);
          currentUrlIndex++;
          attemptConnection();
        };

        testWs.onclose = (event) => {
          if (event.code !== 1000) { // 1000 is normal closure
            console.log(`WebSocket closed abnormally for ${url}: code=${event.code}, reason=${event.reason}`);
          }
          clearTimeout(timeout);
          if (!isConnected) {
            currentUrlIndex++;
            attemptConnection();
          }
        };
      }

      attemptConnection();

    } catch (error) {
      resolve(false);
    }
  });
}

// Set up WebSocket event handlers
function setupWebSocket() {
  if (!ws) return;

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    } catch (error) {
      console.error('Failed to parse server message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    connectionStatus.lastError = 'WebSocket error';
  };

  ws.onclose = () => {
    console.log('WebSocket connection closed');
    ws = null;
    isConnected = false;
    connectionStatus.connected = false;

    // Update extension icon
    chrome.action.setBadgeText({ text: '!' });
    chrome.action.setBadgeBackgroundColor({ color: '#F44336' });

    // Schedule reconnection
    scheduleReconnect();
  };
}

// Handle messages from server
function handleServerMessage(data) {
  if (data.type === 'navigate') {
    // Send navigation command to content script
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, {
          type: 'navigate',
          url: data.url
        });
      }
    });
  } else if (data.type === 'dom_command') {
    // Route DOM commands to appropriate tab
    const targetTabId = data.tabId;
    const command = data.command;

    if (targetTabId) {
      // Send to specific tab
      chrome.tabs.sendMessage(targetTabId, command, (response) => {
        // Send response back to server
        sendToServer({
          type: 'dom_response',
          requestId: data.requestId,
          response: response || { success: false, error: 'No response from tab' }
        });
      });
    } else {
      // Send to active tab
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, command, (response) => {
            // Send response back to server
            sendToServer({
              type: 'dom_response',
              requestId: data.requestId,
              tabId: tabs[0].id,
              response: response || { success: false, error: 'No response from tab' }
            });
          });
        } else {
          sendToServer({
            type: 'dom_response',
            requestId: data.requestId,
            response: { success: false, error: 'No active tab found' }
          });
        }
      });
    }
  } else if (data.type === 'get_tabs') {
    // Get information about all tabs
    chrome.tabs.query({}, (tabs) => {
      const tabInfo = tabs.map(tab => ({
        id: tab.id,
        url: tab.url,
        title: tab.title,
        active: tab.active,
        windowId: tab.windowId
      }));

      sendToServer({
        type: 'tabs_info',
        requestId: data.requestId,
        tabs: tabInfo
      });
    });
  } else if (data.type === 'activate_tab') {
    // Activate a specific tab
    chrome.tabs.update(data.tabId, { active: true }, (tab) => {
      sendToServer({
        type: 'tab_activated',
        requestId: data.requestId,
        success: !!tab,
        tabId: tab?.id
      });
    });
  } else if (data.type === 'extract_content') {
    // Extract content from a tab using Readability
    const targetTabId = data.tabId;

    if (targetTabId) {
      // Extract from specific tab
      chrome.tabs.sendMessage(targetTabId, {
        type: 'extractContent',
        params: data.params || {}
      }, (response) => {
        sendToServer({
          type: 'content_extracted',
          requestId: data.requestId,
          tabId: targetTabId,
          response: response || { success: false, error: 'No response from tab' }
        });
      });
    } else {
      // Extract from active tab
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, {
            type: 'extractContent',
            params: data.params || {}
          }, (response) => {
            sendToServer({
              type: 'content_extracted',
              requestId: data.requestId,
              tabId: tabs[0].id,
              url: tabs[0].url,
              title: tabs[0].title,
              response: response || { success: false, error: 'No response from tab' }
            });
          });
        } else {
          sendToServer({
            type: 'content_extracted',
            requestId: data.requestId,
            response: { success: false, error: 'No active tab found' }
          });
        }
      });
    }
  } else if (data.type === 'connection_ack') {
    console.log('Connection acknowledged by server');
  }
}

// Send message to WebSocket server
function sendToServer(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
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

// Flush queued messages
function flushMessageQueue() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;

  while (messageQueue.length > 0) {
    const message = messageQueue.shift();
    ws.send(JSON.stringify(message));
    connectionStatus.messageCount++;
  }
}

// Schedule reconnection
function scheduleReconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
  }

  reconnectTimer = setTimeout(async () => {
    console.log('Attempting to reconnect...');
    await findAndConnect();
  }, 5000);
}

// Handle messages from content scripts and popup
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
      console.log('WebSocket not connected, message queued');
    }

    sendResponse({ received: true });
  } else if (request.type === 'get_status') {
    sendResponse(connectionStatus);
  } else if (request.type === 'dom_result') {
    // Forward DOM operation results to server
    sendToServer({
      type: 'dom_result',
      ...request,
      tabId: sender.tab?.id
    });
    sendResponse({ received: true });
  } else if (request.type === 'connect_to_port') {
    // Handle specific port connection
    console.log(`User requested connection to port ${request.port}`);
    if (ws) {
      ws.close();
    }
    port = request.port;
    tryConnect(request.port).then(success => {
      if (!success) {
        connectionStatus.lastError = `Failed to connect to port ${request.port}`;
      }
    });
    sendResponse({ received: true });
  } else if (request.type === 'set_port_mode') {
    // Handle auto mode
    if (request.mode === 'auto') {
      console.log('Switching to auto port discovery');
      if (ws) {
        ws.close();
        ws = null;
      }
      isConnected = false;
      connectionStatus.connected = false;
      port = 8875; // Reset to start of range
      setTimeout(() => findAndConnect(), 100); // Small delay to ensure clean state
    }
    sendResponse({ received: true });
  } else if (request.type === 'reconnect') {
    // Handle reconnect request
    console.log('Reconnect requested');
    if (ws) {
      ws.close();
    }
    findAndConnect();
    sendResponse({ received: true });
  }
});

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('MCP Browser extension installed');

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

  // Try to connect
  findAndConnect();
});

// Handle browser startup
chrome.runtime.onStartup.addListener(() => {
  console.log('Browser started, connecting to WebSocket...');
  findAndConnect();
});

// Initialize connection
findAndConnect();