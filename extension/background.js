/**
 * Service worker for BrowserPyMCP extension
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
  messageCount: 0
};

// Find available port and connect
async function findAndConnect() {
  for (let p = port; p <= MAX_PORT; p++) {
    if (await tryConnect(p)) {
      port = p;
      return true;
    }
  }
  return false;
}

// Try to connect to a specific port
function tryConnect(targetPort) {
  return new Promise((resolve) => {
    try {
      const testWs = new WebSocket(`ws://localhost:${targetPort}`);

      const timeout = setTimeout(() => {
        testWs.close();
        resolve(false);
      }, 3000);

      testWs.onopen = () => {
        clearTimeout(timeout);
        ws = testWs;
        setupWebSocket();
        connectionStatus.connected = true;
        connectionStatus.port = targetPort;
        connectionStatus.lastError = null;
        isConnected = true;

        // Update extension icon
        chrome.action.setBadgeText({ text: String(targetPort) });
        chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });

        console.log(`Connected to WebSocket on port ${targetPort}`);

        // Send queued messages
        flushMessageQueue();

        resolve(true);
      };

      testWs.onerror = () => {
        clearTimeout(timeout);
        resolve(false);
      };

      testWs.onclose = () => {
        clearTimeout(timeout);
        resolve(false);
      };

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

// Handle messages from content scripts
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
  }
});

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('BrowserPyMCP extension installed');

  // Set initial badge
  chrome.action.setBadgeText({ text: '?' });
  chrome.action.setBadgeBackgroundColor({ color: '#9E9E9E' });

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