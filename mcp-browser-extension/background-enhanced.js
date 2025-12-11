/**
 * Enhanced Service worker for MCP Browser extension
 * Features:
 * - Multi-server discovery
 * - Project identification
 * - Smart port selection
 * - Multi-connection manager (supports up to 10 simultaneous connections)
 * - Per-connection state management (heartbeat, queues, sequences)
 * - Tab-to-connection routing
 */

// Configuration
const PORT_RANGE = { start: 8875, end: 8895 };
const SCAN_INTERVAL_MINUTES = 0.5; // Scan for servers every 30 seconds (0.5 minutes)

// Storage keys for persistence
const STORAGE_KEYS = {
  MESSAGE_QUEUE: 'mcp_message_queue',
  LAST_CONNECTED_PORT: 'mcp_last_connected_port',
  LAST_CONNECTED_PROJECT: 'mcp_last_connected_project',
  LAST_SEQUENCE: 'mcp_last_sequence',
  PORT_PROJECT_MAP: 'mcp_port_project_map'
};

// Max queue size to prevent storage bloat
const MAX_QUEUE_SIZE = 500;

// Status colors
const STATUS_COLORS = {
  RED: '#DC3545',    // Not functional / Error
  YELLOW: '#FFC107', // Listening but not connected
  GREEN: '#4CAF50'   // Connected to server
};

// State management
let activeServers = new Map(); // port -> server info
let extensionState = 'starting'; // 'starting', 'scanning', 'idle', 'connected', 'error'

// Port to project mapping for faster reconnection
let portProjectMap = {}; // port -> { project_id, project_name, project_path, last_seen }

// Gap detection configuration
const GAP_DETECTION_ENABLED = true;
const MAX_GAP_SIZE = 50; // Max messages to request in gap recovery

// Heartbeat configuration
const HEARTBEAT_INTERVAL = 15000; // 15 seconds
const PONG_TIMEOUT = 10000; // 10 seconds (25s total before timeout)

// Exponential backoff configuration
const BASE_RECONNECT_DELAY = 1000;  // 1 second
const MAX_RECONNECT_DELAY = 30000;  // 30 seconds max

// Maximum simultaneous connections
const MAX_CONNECTIONS = 10;

// Active ports to content scripts for keepalive
const activePorts = new Map(); // tabId -> port

// LEGACY: Single connection fallback (deprecated)
let currentConnection = null;
let messageQueue = [];
let connectionReady = false;
let lastSequenceReceived = 0;
let pendingGapRecovery = false;
let outOfOrderBuffer = [];
let lastPongTime = Date.now();
let reconnectAttempts = 0;

// Connection status (LEGACY - maintained for backward compatibility)
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
 * ConnectionManager - Manages multiple simultaneous WebSocket connections
 * Supports N connections with per-connection state, heartbeat, and message queuing
 */
class ConnectionManager {
  constructor() {
    this.connections = new Map(); // port -> connection object
    this.tabConnections = new Map(); // tabId -> port
    this.primaryPort = null; // Currently active/primary connection for badge display
  }

  /**
   * Create or return existing connection for a port
   * @param {number} port - Port number to connect to
   * @param {Object} projectInfo - Optional project information
   * @returns {Promise<Object>} Connection object
   */
  async connectToBackend(port, projectInfo = null) {
    console.log(`[ConnectionManager] Connecting to port ${port}...`);

    // Check connection limit
    if (!this.connections.has(port) && this.connections.size >= MAX_CONNECTIONS) {
      throw new Error(`Maximum connections (${MAX_CONNECTIONS}) reached`);
    }

    // Return existing connection if already connected
    if (this.connections.has(port)) {
      const conn = this.connections.get(port);
      if (conn.ws && conn.ws.readyState === WebSocket.OPEN) {
        console.log(`[ConnectionManager] Reusing existing connection to port ${port}`);
        return conn;
      }
      // Clean up stale connection
      await this.disconnectBackend(port);
    }

    // Create new connection object
    const connection = {
      ws: null,
      port: port,
      projectId: projectInfo?.project_id || null,
      projectName: projectInfo?.project_name || projectInfo?.projectName || `Port ${port}`,
      projectPath: projectInfo?.project_path || projectInfo?.projectPath || '',
      tabs: new Set(),
      messageQueue: [],
      connectionReady: false,
      lastSequence: 0,
      reconnectAttempts: 0,
      heartbeatInterval: null,
      lastPongTime: Date.now(),
      pendingGapRecovery: false,
      outOfOrderBuffer: []
    };

    try {
      // Create WebSocket
      const ws = new WebSocket(`ws://localhost:${port}`);
      connection.ws = ws;

      // Wait for connection to open
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          ws.close();
          reject(new Error(`Connection timeout for port ${port}`));
        }, 3000);

        ws.onopen = async () => {
          clearTimeout(timeout);
          console.log(`[ConnectionManager] WebSocket opened for port ${port}`);

          // Load last sequence from storage
          const storageKey = `mcp_last_sequence_${port}`;
          const result = await chrome.storage.local.get(storageKey);
          connection.lastSequence = result[storageKey] || 0;

          // Send connection_init handshake
          const initMessage = {
            type: 'connection_init',
            lastSequence: connection.lastSequence,
            extensionVersion: chrome.runtime.getManifest().version,
            capabilities: ['console_capture', 'dom_interaction']
          };

          try {
            ws.send(JSON.stringify(initMessage));
            console.log(`[ConnectionManager] Sent connection_init for port ${port} with lastSequence: ${connection.lastSequence}`);
          } catch (e) {
            console.error(`[ConnectionManager] Failed to send connection_init for port ${port}:`, e);
            reject(e);
            return;
          }

          resolve();
        };

        ws.onerror = (error) => {
          clearTimeout(timeout);
          console.error(`[ConnectionManager] Connection error for port ${port}:`, error);
          reject(error);
        };

        ws.onclose = () => {
          clearTimeout(timeout);
          reject(new Error(`Connection closed for port ${port}`));
        };
      });

      // Set up message handlers
      this._setupConnectionHandlers(connection);

      // Store connection
      this.connections.set(port, connection);

      // Set as primary if it's the first connection
      if (!this.primaryPort) {
        this.primaryPort = port;
      }

      console.log(`[ConnectionManager] Successfully connected to port ${port} (${connection.projectName})`);
      return connection;

    } catch (error) {
      console.error(`[ConnectionManager] Failed to connect to port ${port}:`, error);
      throw error;
    }
  }

  /**
   * Disconnect from a specific backend
   * @param {number} port - Port to disconnect from
   */
  async disconnectBackend(port) {
    console.log(`[ConnectionManager] Disconnecting from port ${port}...`);

    const connection = this.connections.get(port);
    if (!connection) {
      console.log(`[ConnectionManager] No connection found for port ${port}`);
      return;
    }

    // Stop heartbeat
    if (connection.heartbeatInterval) {
      clearInterval(connection.heartbeatInterval);
      connection.heartbeatInterval = null;
    }

    // Close WebSocket
    if (connection.ws) {
      try {
        connection.ws.close();
      } catch (e) {
        console.error(`[ConnectionManager] Error closing WebSocket for port ${port}:`, e);
      }
    }

    // Save last sequence
    const storageKey = `mcp_last_sequence_${port}`;
    await chrome.storage.local.set({ [storageKey]: connection.lastSequence });

    // Save message queue if not empty
    if (connection.messageQueue.length > 0) {
      const queueKey = `mcp_message_queue_${port}`;
      await chrome.storage.local.set({ [queueKey]: connection.messageQueue.slice(-MAX_QUEUE_SIZE) });
    }

    // Remove all tab associations
    for (const [tabId, tabPort] of this.tabConnections.entries()) {
      if (tabPort === port) {
        this.tabConnections.delete(tabId);
      }
    }

    // Remove connection
    this.connections.delete(port);

    // Update primary port if this was primary
    if (this.primaryPort === port) {
      const remainingPorts = Array.from(this.connections.keys());
      this.primaryPort = remainingPorts.length > 0 ? remainingPorts[0] : null;
    }

    console.log(`[ConnectionManager] Disconnected from port ${port}`);
  }

  /**
   * Get connection object for a specific tab
   * @param {number} tabId - Tab ID
   * @returns {Object|null} Connection object or null
   */
  getConnectionForTab(tabId) {
    const port = this.tabConnections.get(tabId);
    if (!port) {
      return null;
    }
    return this.connections.get(port) || null;
  }

  /**
   * Assign a tab to a specific connection
   * @param {number} tabId - Tab ID
   * @param {number} port - Port number
   */
  assignTabToConnection(tabId, port) {
    const connection = this.connections.get(port);
    if (!connection) {
      console.warn(`[ConnectionManager] Cannot assign tab ${tabId} to port ${port} - connection not found`);
      return;
    }

    // Remove from previous connection if exists
    const previousPort = this.tabConnections.get(tabId);
    if (previousPort && previousPort !== port) {
      const prevConn = this.connections.get(previousPort);
      if (prevConn) {
        prevConn.tabs.delete(tabId);
      }
    }

    // Assign to new connection
    connection.tabs.add(tabId);
    this.tabConnections.set(tabId, port);
    console.log(`[ConnectionManager] Assigned tab ${tabId} to port ${port}`);
  }

  /**
   * Remove a tab from all connections
   * @param {number} tabId - Tab ID
   */
  removeTab(tabId) {
    const port = this.tabConnections.get(tabId);
    if (port) {
      const connection = this.connections.get(port);
      if (connection) {
        connection.tabs.delete(tabId);
        console.log(`[ConnectionManager] Removed tab ${tabId} from port ${port}`);
      }
      this.tabConnections.delete(tabId);
    }
  }

  /**
   * Send message through the connection associated with a tab
   * @param {number} tabId - Tab ID
   * @param {Object} message - Message to send
   * @returns {Promise<boolean>} Success status
   */
  async sendMessage(tabId, message) {
    const connection = this.getConnectionForTab(tabId);
    if (!connection) {
      console.warn(`[ConnectionManager] No connection found for tab ${tabId}, message queued`);
      return false;
    }

    return this._sendToConnection(connection, message);
  }

  /**
   * Broadcast message to all active connections
   * @param {Object} message - Message to send
   * @returns {Promise<number>} Number of successful sends
   */
  async broadcastToAll(message) {
    let successCount = 0;
    for (const connection of this.connections.values()) {
      const success = await this._sendToConnection(connection, message);
      if (success) successCount++;
    }
    console.log(`[ConnectionManager] Broadcast sent to ${successCount}/${this.connections.size} connections`);
    return successCount;
  }

  /**
   * Get list of active connections
   * @returns {Array} Array of connection info objects
   */
  getActiveConnections() {
    return Array.from(this.connections.values()).map(conn => ({
      port: conn.port,
      projectId: conn.projectId,
      projectName: conn.projectName,
      projectPath: conn.projectPath,
      tabCount: conn.tabs.size,
      queueSize: conn.messageQueue.length,
      ready: conn.connectionReady,
      isPrimary: conn.port === this.primaryPort
    }));
  }

  /**
   * Internal: Send message to a specific connection
   * @private
   */
  async _sendToConnection(connection, message) {
    if (connection.ws && connection.ws.readyState === WebSocket.OPEN && connection.connectionReady) {
      try {
        connection.ws.send(JSON.stringify(message));
        return true;
      } catch (e) {
        console.error(`[ConnectionManager] Failed to send message to port ${connection.port}:`, e);
        return false;
      }
    } else {
      // Queue message
      connection.messageQueue.push(message);
      if (connection.messageQueue.length > MAX_QUEUE_SIZE) {
        connection.messageQueue.shift();
      }
      // Persist queue
      const queueKey = `mcp_message_queue_${connection.port}`;
      await chrome.storage.local.set({ [queueKey]: connection.messageQueue.slice(-MAX_QUEUE_SIZE) });
      return false;
    }
  }

  /**
   * Internal: Set up WebSocket event handlers for a connection
   * @private
   */
  _setupConnectionHandlers(connection) {
    const { ws, port } = connection;

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle connection_ack
        if (data.type === 'connection_ack') {
          console.log(`[ConnectionManager] Connection acknowledged for port ${port}`);
          connection.connectionReady = true;

          // Update project info if provided
          if (data.project_id) {
            connection.projectId = data.project_id;
            connection.projectName = data.project_name || connection.projectName;
            connection.projectPath = data.project_path || connection.projectPath;

            // Update port-project mapping
            await updatePortProjectMapping(port, {
              project_id: data.project_id,
              project_name: data.project_name,
              project_path: data.project_path
            });
          }

          // Handle replayed messages
          if (data.replay && Array.isArray(data.replay)) {
            console.log(`[ConnectionManager] Receiving ${data.replay.length} replayed messages for port ${port}`);
            for (const msg of data.replay) {
              if (msg.sequence !== undefined && msg.sequence > connection.lastSequence) {
                connection.lastSequence = msg.sequence;
              }
            }
          }

          // Update last sequence
          if (data.currentSequence !== undefined) {
            connection.lastSequence = data.currentSequence;
            const storageKey = `mcp_last_sequence_${port}`;
            await chrome.storage.local.set({ [storageKey]: connection.lastSequence });
          }

          // Start heartbeat
          this._startHeartbeat(connection);

          // Flush message queue
          await this._flushMessageQueue(connection);

          // Update status if this is primary connection
          if (this.primaryPort === port) {
            this._updateGlobalStatus();
          }

          return;
        }

        // Handle pong
        if (data.type === 'pong') {
          connection.lastPongTime = Date.now();
          console.log(`[ConnectionManager] Pong received from port ${port}`);
          return;
        }

        // Handle gap recovery
        if (data.type === 'gap_recovery_response') {
          console.log(`[ConnectionManager] Gap recovery response received for port ${port}`);
          connection.pendingGapRecovery = false;

          if (data.messages && Array.isArray(data.messages)) {
            for (const msg of data.messages) {
              if (msg.sequence !== undefined && msg.sequence > connection.lastSequence) {
                connection.lastSequence = msg.sequence;
              }
            }

            const storageKey = `mcp_last_sequence_${port}`;
            await chrome.storage.local.set({ [storageKey]: connection.lastSequence });

            this._processBufferedMessages(connection);
          }

          return;
        }

        // Handle sequenced messages
        if (data.sequence !== undefined) {
          const shouldProcess = this._checkSequenceGap(connection, data.sequence);
          if (!shouldProcess) {
            return;
          }
          connection.lastSequence = data.sequence;
        }

        // Handle regular server messages
        this._handleServerMessage(connection, data);

      } catch (error) {
        console.error(`[ConnectionManager] Failed to parse message from port ${port}:`, error);
      }
    };

    ws.onerror = (error) => {
      console.error(`[ConnectionManager] WebSocket error for port ${port}:`, error);
    };

    ws.onclose = async () => {
      console.log(`[ConnectionManager] Connection closed for port ${port}`);

      // Stop heartbeat
      if (connection.heartbeatInterval) {
        clearInterval(connection.heartbeatInterval);
        connection.heartbeatInterval = null;
      }

      // Save state
      const storageKey = `mcp_last_sequence_${port}`;
      await chrome.storage.local.set({ [storageKey]: connection.lastSequence });

      // Schedule reconnect with exponential backoff
      connection.reconnectAttempts++;
      const delay = this._calculateReconnectDelay(connection.reconnectAttempts);
      console.log(`[ConnectionManager] Scheduling reconnect for port ${port} in ${delay}ms (attempt ${connection.reconnectAttempts})`);

      setTimeout(async () => {
        try {
          // Remove old connection
          this.connections.delete(port);

          // Attempt reconnect
          await this.connectToBackend(port, {
            project_id: connection.projectId,
            project_name: connection.projectName,
            project_path: connection.projectPath
          });

          // Reassign tabs
          for (const tabId of connection.tabs) {
            this.assignTabToConnection(tabId, port);
          }

        } catch (error) {
          console.error(`[ConnectionManager] Reconnect failed for port ${port}:`, error);
        }
      }, delay);

      // Update global status
      this._updateGlobalStatus();
    };
  }

  /**
   * Internal: Start heartbeat for a connection
   * @private
   */
  _startHeartbeat(connection) {
    if (connection.heartbeatInterval) {
      clearInterval(connection.heartbeatInterval);
    }

    console.log(`[ConnectionManager] Starting heartbeat for port ${connection.port}`);
    connection.heartbeatInterval = setInterval(() => {
      if (connection.ws && connection.ws.readyState === WebSocket.OPEN) {
        // Check for pong timeout
        const timeSinceLastPong = Date.now() - connection.lastPongTime;
        if (timeSinceLastPong > HEARTBEAT_INTERVAL + PONG_TIMEOUT) {
          console.warn(`[ConnectionManager] Heartbeat timeout for port ${connection.port} - no pong for ${timeSinceLastPong}ms`);
          connection.ws.close();
          return;
        }

        // Send heartbeat
        try {
          connection.ws.send(JSON.stringify({
            type: 'heartbeat',
            timestamp: Date.now()
          }));
          console.log(`[ConnectionManager] Heartbeat sent to port ${connection.port}`);
        } catch (e) {
          console.warn(`[ConnectionManager] Heartbeat failed for port ${connection.port}:`, e);
        }
      } else {
        clearInterval(connection.heartbeatInterval);
        connection.heartbeatInterval = null;
      }
    }, HEARTBEAT_INTERVAL);
  }

  /**
   * Internal: Flush message queue for a connection
   * @private
   */
  async _flushMessageQueue(connection) {
    if (!connection.ws || connection.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    console.log(`[ConnectionManager] Flushing ${connection.messageQueue.length} queued messages for port ${connection.port}`);

    while (connection.messageQueue.length > 0) {
      const message = connection.messageQueue.shift();
      try {
        connection.ws.send(JSON.stringify(message));
      } catch (e) {
        console.error(`[ConnectionManager] Failed to send queued message to port ${connection.port}:`, e);
        connection.messageQueue.unshift(message);
        break;
      }
    }

    // Clear stored queue
    const queueKey = `mcp_message_queue_${connection.port}`;
    await chrome.storage.local.remove(queueKey);
  }

  /**
   * Internal: Check for sequence gaps
   * @private
   */
  _checkSequenceGap(connection, incomingSequence) {
    if (!GAP_DETECTION_ENABLED || incomingSequence === undefined) {
      return true;
    }

    const expectedSequence = connection.lastSequence + 1;

    if (incomingSequence === expectedSequence) {
      return true;
    }

    if (incomingSequence <= connection.lastSequence) {
      console.log(`[ConnectionManager] Duplicate message (seq ${incomingSequence}) for port ${connection.port}`);
      return false;
    }

    const gapSize = incomingSequence - expectedSequence;
    console.warn(`[ConnectionManager] Gap detected for port ${connection.port}: expected ${expectedSequence}, got ${incomingSequence} (gap: ${gapSize})`);

    if (gapSize > MAX_GAP_SIZE) {
      console.warn(`[ConnectionManager] Gap too large (${gapSize}) for port ${connection.port}, accepting and resetting`);
      return true;
    }

    if (!connection.pendingGapRecovery) {
      this._requestGapRecovery(connection, expectedSequence, incomingSequence - 1);
    }

    connection.outOfOrderBuffer.push({ sequence: incomingSequence });
    return false;
  }

  /**
   * Internal: Request gap recovery
   * @private
   */
  _requestGapRecovery(connection, fromSequence, toSequence) {
    if (!connection.ws || connection.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    connection.pendingGapRecovery = true;
    console.log(`[ConnectionManager] Requesting gap recovery for port ${connection.port}: sequences ${fromSequence} to ${toSequence}`);

    try {
      connection.ws.send(JSON.stringify({
        type: 'gap_recovery',
        fromSequence: fromSequence,
        toSequence: toSequence
      }));
    } catch (e) {
      console.error(`[ConnectionManager] Failed to request gap recovery for port ${connection.port}:`, e);
      connection.pendingGapRecovery = false;
    }
  }

  /**
   * Internal: Process buffered messages
   * @private
   */
  _processBufferedMessages(connection) {
    if (connection.outOfOrderBuffer.length === 0) return;

    connection.outOfOrderBuffer.sort((a, b) => a.sequence - b.sequence);

    const stillBuffered = [];
    for (const item of connection.outOfOrderBuffer) {
      if (item.sequence === connection.lastSequence + 1) {
        connection.lastSequence = item.sequence;
      } else if (item.sequence > connection.lastSequence + 1) {
        stillBuffered.push(item);
      }
    }

    connection.outOfOrderBuffer = stillBuffered;
  }

  /**
   * Internal: Calculate reconnect delay with exponential backoff
   * @private
   */
  _calculateReconnectDelay(attempts) {
    const exponentialDelay = Math.min(
      BASE_RECONNECT_DELAY * Math.pow(2, attempts),
      MAX_RECONNECT_DELAY
    );

    const jitter = exponentialDelay * 0.25 * (Math.random() - 0.5);
    return Math.max(exponentialDelay + jitter, BASE_RECONNECT_DELAY);
  }

  /**
   * Internal: Handle server message
   * @private
   */
  _handleServerMessage(connection, data) {
    // Route to original handler
    handleServerMessage(data);
  }

  /**
   * Internal: Update global connection status
   * @private
   */
  _updateGlobalStatus() {
    // Update legacy connectionStatus for backward compatibility
    const primaryConn = this.primaryPort ? this.connections.get(this.primaryPort) : null;

    if (primaryConn && primaryConn.connectionReady) {
      connectionStatus.connected = true;
      connectionStatus.port = primaryConn.port;
      connectionStatus.projectName = primaryConn.projectName;
      connectionStatus.projectPath = primaryConn.projectPath;
      connectionStatus.lastError = null;
      extensionState = 'connected';
    } else if (this.connections.size > 0) {
      // At least one connection exists
      const anyConn = Array.from(this.connections.values())[0];
      connectionStatus.connected = true;
      connectionStatus.port = anyConn.port;
      connectionStatus.projectName = anyConn.projectName;
      connectionStatus.projectPath = anyConn.projectPath;
      extensionState = 'connected';
    } else {
      connectionStatus.connected = false;
      connectionStatus.port = null;
      connectionStatus.projectName = null;
      connectionStatus.projectPath = null;
      extensionState = activeServers.size > 0 ? 'idle' : 'idle';
    }

    updateBadgeStatus();
  }
}

// Initialize ConnectionManager
const connectionManager = new ConnectionManager();

/**
 * Calculate reconnection delay with exponential backoff and jitter
 * @returns {number} Delay in milliseconds
 */
function calculateReconnectDelay() {
  // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (capped)
  const exponentialDelay = Math.min(
    BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts),
    MAX_RECONNECT_DELAY
  );

  // Add jitter (±25%) to prevent thundering herd
  const jitter = exponentialDelay * 0.25 * (Math.random() - 0.5);
  const delay = Math.max(exponentialDelay + jitter, BASE_RECONNECT_DELAY);

  return delay;
}

/**
 * Check for sequence gaps and handle accordingly
 * @param {number} incomingSequence - The sequence number of the incoming message
 * @returns {boolean} - True if message should be processed immediately, false if buffered
 */
function checkSequenceGap(incomingSequence) {
  if (!GAP_DETECTION_ENABLED || incomingSequence === undefined) {
    return true; // Process immediately
  }

  const expectedSequence = lastSequenceReceived + 1;

  // Perfect order - process immediately
  if (incomingSequence === expectedSequence) {
    return true;
  }

  // Duplicate - skip
  if (incomingSequence <= lastSequenceReceived) {
    console.log(`[MCP Browser] Duplicate message (seq ${incomingSequence}), skipping`);
    return false;
  }

  // Gap detected - message arrived too early
  const gapSize = incomingSequence - expectedSequence;
  console.warn(`[MCP Browser] Gap detected: expected ${expectedSequence}, got ${incomingSequence} (gap: ${gapSize})`);

  // If gap is too large, just accept and move on (likely server restart)
  if (gapSize > MAX_GAP_SIZE) {
    console.warn(`[MCP Browser] Gap too large (${gapSize}), accepting and resetting sequence`);
    return true;
  }

  // Request gap recovery if not already pending
  if (!pendingGapRecovery) {
    requestGapRecovery(expectedSequence, incomingSequence - 1);
  }

  // Buffer this message for later processing
  outOfOrderBuffer.push({ sequence: incomingSequence, message: null }); // Will be set by caller
  return false;
}

/**
 * Request recovery of missed messages
 */
function requestGapRecovery(fromSequence, toSequence) {
  if (!currentConnection || currentConnection.readyState !== WebSocket.OPEN) {
    return;
  }

  pendingGapRecovery = true;
  console.log(`[MCP Browser] Requesting gap recovery: sequences ${fromSequence} to ${toSequence}`);

  try {
    currentConnection.send(JSON.stringify({
      type: 'gap_recovery',
      fromSequence: fromSequence,
      toSequence: toSequence
    }));
  } catch (e) {
    console.error('[MCP Browser] Failed to request gap recovery:', e);
    pendingGapRecovery = false;
  }
}

/**
 * Process messages that were buffered during gap recovery
 */
function processBufferedMessages() {
  if (outOfOrderBuffer.length === 0) return;

  // Sort by sequence
  outOfOrderBuffer.sort((a, b) => a.sequence - b.sequence);

  // Process messages that are now valid
  const stillBuffered = [];
  for (const item of outOfOrderBuffer) {
    if (item.sequence === lastSequenceReceived + 1) {
      lastSequenceReceived = item.sequence;
      console.log(`[MCP Browser] Processing buffered message seq ${item.sequence}`);
    } else if (item.sequence > lastSequenceReceived + 1) {
      stillBuffered.push(item);
    }
    // Skip if already processed (duplicate)
  }

  outOfOrderBuffer = stillBuffered;

  if (stillBuffered.length > 0) {
    console.log(`[MCP Browser] ${stillBuffered.length} messages still buffered`);
  }
}

/**
 * Handle keepalive port connections from content scripts.
 * Maintaining open ports prevents service worker termination.
 */
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === 'keepalive') {
    const tabId = port.sender?.tab?.id;
    if (tabId) {
      console.log(`[MCP Browser] Keepalive port connected from tab ${tabId}`);
      activePorts.set(tabId, port);

      port.onDisconnect.addListener(() => {
        console.log(`[MCP Browser] Keepalive port disconnected from tab ${tabId}`);
        activePorts.delete(tabId);
      });

      // Optional: Send acknowledgment
      port.postMessage({ type: 'keepalive_ack' });
    }
  }
});

/**
 * Get count of active keepalive ports
 */
function getActivePortCount() {
  return activePorts.size;
}

/**
 * Chrome Alarms handler for persistent timers
 * Handles reconnection, server scanning, and heartbeat
 */
chrome.alarms.onAlarm.addListener((alarm) => {
  console.log(`[MCP Browser] Alarm triggered: ${alarm.name}`);
  if (alarm.name === 'reconnect') {
    autoConnect();
  } else if (alarm.name === 'serverScan') {
    scanForServers();
  } else if (alarm.name === 'heartbeat') {
    sendHeartbeat();
  }
});

/**
 * Start heartbeat alarm to keep service worker alive during active connections
 */
function startHeartbeat() {
  console.log('[MCP Browser] Starting heartbeat alarm');
  chrome.alarms.create('heartbeat', {
    delayInMinutes: HEARTBEAT_INTERVAL / 60000,
    periodInMinutes: HEARTBEAT_INTERVAL / 60000
  });
}

/**
 * Stop heartbeat alarm
 */
function stopHeartbeat() {
  console.log('[MCP Browser] Stopping heartbeat alarm');
  chrome.alarms.clear('heartbeat');
}

/**
 * Send heartbeat and check for pong timeout
 */
function sendHeartbeat() {
  if (currentConnection && currentConnection.readyState === WebSocket.OPEN) {
    // Check if we received pong recently
    const timeSinceLastPong = Date.now() - lastPongTime;
    if (timeSinceLastPong > HEARTBEAT_INTERVAL + PONG_TIMEOUT) {
      console.warn(`[MCP Browser] Heartbeat timeout - no pong for ${timeSinceLastPong}ms, reconnecting`);
      // Close connection and trigger reconnect
      currentConnection.close();
      stopHeartbeat();

      // Calculate delay with backoff
      const delay = calculateReconnectDelay();
      reconnectAttempts++;
      console.log(`[MCP Browser] Scheduling reconnect in ${delay}ms (attempt ${reconnectAttempts})`);
      chrome.alarms.create('reconnect', { delayInMinutes: delay / 60000 });
      return;
    }

    // Send heartbeat with timestamp
    try {
      currentConnection.send(JSON.stringify({
        type: 'heartbeat',
        timestamp: Date.now()
      }));
      console.log('[MCP Browser] Heartbeat sent');
    } catch (e) {
      console.warn('[MCP Browser] Heartbeat failed:', e);
    }
  } else {
    // Stop heartbeat if connection is not open
    stopHeartbeat();
  }
}

/**
 * Save message queue to chrome.storage.local
 */
async function saveMessageQueue() {
  try {
    // Limit queue size before saving
    const queueToSave = messageQueue.slice(-MAX_QUEUE_SIZE);
    await chrome.storage.local.set({ [STORAGE_KEYS.MESSAGE_QUEUE]: queueToSave });
    console.log(`[MCP Browser] Queue saved: ${queueToSave.length} messages`);
  } catch (e) {
    console.error('[MCP Browser] Failed to save queue:', e);
  }
}

/**
 * Load message queue from chrome.storage.local
 */
async function loadMessageQueue() {
  try {
    const result = await chrome.storage.local.get(STORAGE_KEYS.MESSAGE_QUEUE);
    if (result[STORAGE_KEYS.MESSAGE_QUEUE]) {
      messageQueue = result[STORAGE_KEYS.MESSAGE_QUEUE];
      console.log(`[MCP Browser] Queue loaded: ${messageQueue.length} messages`);
    }
  } catch (e) {
    console.error('[MCP Browser] Failed to load queue:', e);
  }
}

/**
 * Clear message queue from storage after successful flush
 */
async function clearStoredQueue() {
  try {
    await chrome.storage.local.remove(STORAGE_KEYS.MESSAGE_QUEUE);
    console.log('[MCP Browser] Stored queue cleared');
  } catch (e) {
    console.error('[MCP Browser] Failed to clear stored queue:', e);
  }
}

/**
 * Save last connected server info for faster reconnection
 */
async function saveConnectionState(port, projectName) {
  try {
    await chrome.storage.local.set({
      [STORAGE_KEYS.LAST_CONNECTED_PORT]: port,
      [STORAGE_KEYS.LAST_CONNECTED_PROJECT]: projectName
    });
    console.log(`[MCP Browser] Connection state saved: port ${port}, project ${projectName}`);
  } catch (e) {
    console.error('[MCP Browser] Failed to save connection state:', e);
  }
}

/**
 * Load last connected server info
 */
async function loadConnectionState() {
  try {
    const result = await chrome.storage.local.get([
      STORAGE_KEYS.LAST_CONNECTED_PORT,
      STORAGE_KEYS.LAST_CONNECTED_PROJECT
    ]);
    return {
      port: result[STORAGE_KEYS.LAST_CONNECTED_PORT] || null,
      projectName: result[STORAGE_KEYS.LAST_CONNECTED_PROJECT] || null
    };
  } catch (e) {
    console.error('[MCP Browser] Failed to load connection state:', e);
    return { port: null, projectName: null };
  }
}

/**
 * Clear connection state (on intentional disconnect)
 */
async function clearConnectionState() {
  try {
    await chrome.storage.local.remove([
      STORAGE_KEYS.LAST_CONNECTED_PORT,
      STORAGE_KEYS.LAST_CONNECTED_PROJECT
    ]);
  } catch (e) {
    console.error('[MCP Browser] Failed to clear connection state:', e);
  }
}

/**
 * Load port-project mapping from storage
 */
async function loadPortProjectMap() {
  try {
    const result = await chrome.storage.local.get(STORAGE_KEYS.PORT_PROJECT_MAP);
    portProjectMap = result[STORAGE_KEYS.PORT_PROJECT_MAP] || {};
    console.log(`[MCP Browser] Loaded ${Object.keys(portProjectMap).length} port-project mappings`);
  } catch (e) {
    console.error('[MCP Browser] Failed to load port-project map:', e);
  }
}

/**
 * Save port-project mapping to storage
 */
async function savePortProjectMap() {
  try {
    await chrome.storage.local.set({ [STORAGE_KEYS.PORT_PROJECT_MAP]: portProjectMap });
  } catch (e) {
    console.error('[MCP Browser] Failed to save port-project map:', e);
  }
}

/**
 * Update port-project mapping from server info
 */
async function updatePortProjectMapping(port, serverInfo) {
  portProjectMap[port] = {
    project_id: serverInfo.project_id,
    project_name: serverInfo.project_name,
    project_path: serverInfo.project_path,
    last_seen: Date.now()
  };

  await savePortProjectMap();

  // Update badge tooltip with project name
  const projectName = serverInfo.project_name || 'Unknown';
  chrome.action.setTitle({
    title: `MCP Browser: ${projectName} (port ${port})`
  });

  console.log(`[MCP Browser] Updated mapping: port ${port} → ${projectName}`);
}

/**
 * Update extension badge to reflect current status
 * States:
 * - RED: Not functional or error state
 * - YELLOW: Scanning/ready but not connected
 * - GREEN: Connected to server
 */
function updateBadgeStatus() {
  if (extensionState === 'error' || (!connectionStatus.connected && connectionStatus.lastError)) {
    // RED: Error state or not functional
    chrome.action.setBadgeBackgroundColor({ color: STATUS_COLORS.RED });
    chrome.action.setBadgeText({ text: '!' });
  } else if (connectionStatus.connected && currentConnection) {
    // GREEN: Connected to server
    chrome.action.setBadgeBackgroundColor({ color: STATUS_COLORS.GREEN });
    chrome.action.setBadgeText({ text: String(connectionStatus.port) });
  } else if (connectionStatus.availableServers.length > 0) {
    // YELLOW: Servers available but not connected
    chrome.action.setBadgeBackgroundColor({ color: STATUS_COLORS.YELLOW });
    chrome.action.setBadgeText({ text: String(connectionStatus.availableServers.length) });
  } else {
    // YELLOW: Listening/scanning for servers
    chrome.action.setBadgeBackgroundColor({ color: STATUS_COLORS.YELLOW });
    chrome.action.setBadgeText({ text: '...' });
  }
}

/**
 * Scan all ports for running MCP Browser servers
 * @returns {Promise<Array>} Array of available servers
 */
async function scanForServers() {
  console.log(`[MCP Browser] Scanning ports ${PORT_RANGE.start}-${PORT_RANGE.end} for servers...`);
  extensionState = 'scanning';
  updateBadgeStatus();

  const servers = [];

  for (let port = PORT_RANGE.start; port <= PORT_RANGE.end; port++) {
    const serverInfo = await probePort(port);
    if (serverInfo) {
      servers.push(serverInfo);
      activeServers.set(port, serverInfo);
    }
  }

  connectionStatus.availableServers = servers;
  extensionState = servers.length > 0 ? 'idle' : 'idle';
  updateBadgeStatus();

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
    let serverInfoRequested = false;

    const timeout = setTimeout(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      resolve(null);
    }, 2000); // Increased timeout to handle two-message protocol

    try {
      ws = new WebSocket(`ws://localhost:${port}`);

      ws.onopen = () => {
        console.log(`[MCP Browser] WebSocket opened for port ${port}`);
        // Don't send server_info immediately - wait for connection_ack first
        // The server sends connection_ack automatically on connect
      };

      // Handle incoming messages
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle connection_ack - server sends this first
          if (data.type === 'connection_ack') {
            // Now request server info
            if (!serverInfoRequested) {
              serverInfoRequested = true;
              ws.send(JSON.stringify({ type: 'server_info' }));
            }
            return;
          }

          // Handle server_info_response - this is what we're waiting for
          if (data.type === 'server_info_response') {
            clearTimeout(timeout);
            ws.close();
            // Only accept servers with valid project information
            if (data.project_name && data.project_name !== 'Unknown') {
              const serverInfo = {
                port: port,
                projectName: data.project_name,
                projectPath: data.project_path || '',
                version: data.version || '1.0.0',
                connected: false
              };

              // Update port-project mapping if identity is present
              if (data.project_id) {
                updatePortProjectMapping(port, data).catch(err => {
                  console.error('[MCP Browser] Failed to update port mapping:', err);
                });
              }

              resolve(serverInfo);
            } else {
              // Not a valid MCP Browser server
              ws.close();
              resolve(null);
            }
          }
        } catch (e) {
          // Not a valid response - ignore and wait for more messages
          console.warn(`[MCP Browser] Failed to parse message from port ${port}:`, e);
        }
      };

      ws.onerror = (error) => {
        console.warn(`[MCP Browser] WebSocket error for port ${port}:`, error);
        clearTimeout(timeout);
        resolve(null);
      };

      ws.onclose = (event) => {
        console.log(`[MCP Browser] WebSocket closed for port ${port}, code: ${event.code}`);
        clearTimeout(timeout);
      };
    } catch (error) {
      console.error(`[MCP Browser] Failed to create WebSocket for port ${port}:`, error);
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

      ws.onopen = async () => {
        clearTimeout(timeout);
        currentConnection = ws;
        lastPongTime = Date.now();
        reconnectAttempts = 0;
        console.log('[MCP Browser] Connection successful, reset reconnect attempts');

        // Reset gap detection state
        pendingGapRecovery = false;
        outOfOrderBuffer = [];

        // Load last sequence from storage
        const result = await chrome.storage.local.get(STORAGE_KEYS.LAST_SEQUENCE);
        lastSequenceReceived = result[STORAGE_KEYS.LAST_SEQUENCE] || 0;

        // Send connection_init handshake
        const initMessage = {
          type: 'connection_init',
          lastSequence: lastSequenceReceived,
          extensionVersion: chrome.runtime.getManifest().version,
          capabilities: ['console_capture', 'dom_interaction']
        };

        try {
          currentConnection.send(JSON.stringify(initMessage));
          console.log(`[MCP Browser] Sent connection_init with lastSequence: ${lastSequenceReceived}`);
        } catch (e) {
          console.error('[MCP Browser] Failed to send connection_init:', e);
        }

        setupWebSocketHandlers(ws);
        // Don't call startHeartbeat or set connectionReady yet - wait for connection_ack

        resolve(true);
      };

      ws.onerror = (error) => {
        clearTimeout(timeout);
        connectionStatus.lastError = `Connection error on port ${port}`;
        extensionState = 'error';
        updateBadgeStatus();
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
 * Handle a replayed message from the server
 */
function handleReplayedMessage(message) {
  console.log(`[MCP Browser] Processing replayed message: ${message.type}`);
  // For now, just log - actual handling depends on message types
  // In the future, this could trigger UI updates or other actions

  // Update sequence if message has one
  if (message.sequence !== undefined && message.sequence > lastSequenceReceived) {
    lastSequenceReceived = message.sequence;
  }
}

/**
 * Set up WebSocket event handlers
 * @param {WebSocket} ws - WebSocket connection
 */
function setupWebSocketHandlers(ws) {
  ws.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data);

      // Handle connection_ack from server
      if (data.type === 'connection_ack') {
        console.log(`[MCP Browser] Connection acknowledged by server`);
        connectionReady = true;

        // Start heartbeat after handshake complete
        startHeartbeat();

        // Update connection status
        connectionStatus.connected = true;
        connectionStatus.port = ws.url.match(/:(\d+)/)?.[1] || connectionStatus.port;
        connectionStatus.connectionTime = Date.now();
        connectionStatus.lastError = null;
        extensionState = 'connected';
        updateBadgeStatus();

        // Update port-project mapping if identity is present
        if (data.project_id) {
          updatePortProjectMapping(connectionStatus.port, {
            project_id: data.project_id,
            project_name: data.project_name,
            project_path: data.project_path || connectionStatus.projectPath
          }).catch(err => {
            console.error('[MCP Browser] Failed to update port mapping:', err);
          });
        }

        // Handle replayed messages if any
        if (data.replay && Array.isArray(data.replay)) {
          console.log(`[MCP Browser] Receiving ${data.replay.length} replayed messages`);
          for (const msg of data.replay) {
            // Process replayed message
            handleReplayedMessage(msg);
          }
        }

        // Update last sequence if provided
        if (data.currentSequence !== undefined) {
          lastSequenceReceived = data.currentSequence;
          await chrome.storage.local.set({ [STORAGE_KEYS.LAST_SEQUENCE]: lastSequenceReceived });
        }

        // Now flush any queued messages
        await flushMessageQueue();

        return; // Don't process further
      }

      // Handle pong response
      if (data.type === 'pong') {
        lastPongTime = Date.now();
        console.log('[MCP Browser] Pong received');
        return; // Don't process further
      }

      // Handle gap recovery response
      if (data.type === 'gap_recovery_response') {
        console.log(`[MCP Browser] Gap recovery response received`);
        pendingGapRecovery = false;

        // Process recovered messages in order
        if (data.messages && Array.isArray(data.messages)) {
          console.log(`[MCP Browser] Processing ${data.messages.length} recovered messages`);
          for (const msg of data.messages) {
            if (msg.sequence !== undefined && msg.sequence > lastSequenceReceived) {
              lastSequenceReceived = msg.sequence;
              // Process the message content (if applicable)
            }
          }

          // Persist updated sequence
          chrome.storage.local.set({ [STORAGE_KEYS.LAST_SEQUENCE]: lastSequenceReceived });

          // Process any buffered out-of-order messages that are now valid
          processBufferedMessages();
        }

        return;
      }

      // Check for sequence gaps (before processing messages with sequences)
      if (data.sequence !== undefined) {
        const shouldProcess = checkSequenceGap(data.sequence);
        if (!shouldProcess) {
          // Message is buffered or duplicate, don't process further
          return;
        }
        // Update sequence tracking
        lastSequenceReceived = data.sequence;
      }

      handleServerMessage(data);
    } catch (error) {
      console.error('[MCP Browser] Failed to parse server message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('[MCP Browser] WebSocket error:', error);
    connectionStatus.lastError = 'WebSocket error';
    extensionState = 'error';
    updateBadgeStatus();
  };

  ws.onclose = async () => {
    console.log('[MCP Browser] Connection closed');

    // Reset connection state
    connectionReady = false;
    currentConnection = null;
    connectionStatus.connected = false;
    connectionStatus.port = null;
    connectionStatus.projectName = null;

    // Reset gap detection state
    pendingGapRecovery = false;
    outOfOrderBuffer = [];

    // Save last sequence before reconnect
    await chrome.storage.local.set({ [STORAGE_KEYS.LAST_SEQUENCE]: lastSequenceReceived });

    // Stop heartbeat when disconnected
    stopHeartbeat();

    // Update state - back to YELLOW (listening but not connected)
    extensionState = connectionStatus.availableServers.length > 0 ? 'idle' : 'idle';
    updateBadgeStatus();

    // Try to reconnect after a delay with exponential backoff
    const delay = calculateReconnectDelay();
    reconnectAttempts++;
    console.log(`[MCP Browser] Scheduling reconnect in ${delay}ms (attempt ${reconnectAttempts})`);
    chrome.alarms.create('reconnect', { delayInMinutes: delay / 60000 });
  };
}

/**
 * Try to connect to a specific port
 */
async function tryConnectToPort(port) {
  const serverInfo = await probePort(port);
  if (serverInfo) {
    const connected = await connectToServer(port);
    if (connected) {
      console.log(`[MCP Browser] Connected to port ${port}`);
      return true;
    }
  }
  return false;
}

/**
 * Auto-connect to the best available server
 */
async function autoConnect() {
  try {
    console.log('[MCP Browser] Auto-connect starting...');

    // Load port mappings if not already loaded
    if (Object.keys(portProjectMap).length === 0) {
      await loadPortProjectMap();
    }

    // First, try to reconnect to last known server
    const { port: lastPort, projectName: lastProject } = await loadConnectionState();
    if (lastPort) {
      console.log(`[MCP Browser] Trying last connected port: ${lastPort}`);
      const connected = await tryConnectToPort(lastPort);
      if (connected) return;
    }

    // Second, try known project ports (from mapping)
    const knownPorts = Object.keys(portProjectMap).map(p => parseInt(p)).sort((a, b) => {
      // Sort by last_seen, most recent first
      return (portProjectMap[b]?.last_seen || 0) - (portProjectMap[a]?.last_seen || 0);
    });

    for (const port of knownPorts) {
      if (port !== lastPort) { // Don't retry lastPort
        console.log(`[MCP Browser] Trying known project port: ${port} (${portProjectMap[port]?.project_name})`);
        const connected = await tryConnectToPort(port);
        if (connected) return;
      }
    }

    // Fall back to full port scan
    console.log('[MCP Browser] Known ports failed, scanning...');
    const servers = await scanForServers();

    if (servers.length === 0) {
      console.log('[MCP Browser] No servers found');
      connectionStatus.lastError = 'No MCP Browser servers found';
      extensionState = 'idle';
      updateBadgeStatus();
      return;
    }

    // If only one server, connect to it
    if (servers.length === 1) {
      console.log(`[MCP Browser] Connecting to single server on port ${servers[0].port}`);
      await connectToServer(servers[0].port, servers[0]);
      return;
    }

    // If multiple servers, prefer the first one (could be enhanced with preferences)
    console.log(`[MCP Browser] Found ${servers.length} servers, connecting to first one`);
    await connectToServer(servers[0].port, servers[0]);
  } catch (error) {
    console.error('[MCP Browser] Auto-connect failed:', error);
    extensionState = 'error';
    connectionStatus.lastError = error.message || 'Auto-connect failed';
    updateBadgeStatus();
  }
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
 * @returns {Promise<boolean>} Success status
 */
async function sendToServer(message) {
  if (currentConnection && currentConnection.readyState === WebSocket.OPEN && connectionReady) {
    // Connection is open AND handshake is complete
    currentConnection.send(JSON.stringify(message));
    connectionStatus.messageCount++;
    return true;
  } else {
    // Queue message if not connected or handshake not complete
    messageQueue.push(message);
    // Enforce max queue size
    if (messageQueue.length > MAX_QUEUE_SIZE) {
      messageQueue.shift();
    }
    // Persist queue to storage
    await saveMessageQueue();
    return false;
  }
}

/**
 * Flush queued messages
 */
async function flushMessageQueue() {
  if (!currentConnection || currentConnection.readyState !== WebSocket.OPEN) {
    return;
  }

  console.log(`[MCP Browser] Flushing ${messageQueue.length} queued messages`);

  while (messageQueue.length > 0) {
    const message = messageQueue.shift();
    try {
      currentConnection.send(JSON.stringify(message));
      connectionStatus.messageCount++;
    } catch (e) {
      console.error('[MCP Browser] Failed to send queued message:', e);
      // Put message back and stop flushing
      messageQueue.unshift(message);
      await saveMessageQueue();
      return;
    }
  }

  // Clear stored queue after successful flush
  await clearStoredQueue();
  console.log('[MCP Browser] Queue flush complete');
}

/**
 * Clean up ports when tabs are closed
 */
chrome.tabs.onRemoved.addListener((tabId) => {
  if (activePorts.has(tabId)) {
    console.log(`[MCP Browser] Tab ${tabId} closed, removing port`);
    activePorts.delete(tabId);
  }

  // Remove tab from ConnectionManager
  connectionManager.removeTab(tabId);
});

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'console_messages') {
    // Only process messages from the active tab
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      const activeTab = tabs[0];

      // Check if this message is from the active tab
      if (sender.tab && activeTab && sender.tab.id === activeTab.id) {
        // Batch console messages
        const batchMessage = {
          type: 'batch',
          messages: request.messages,
          url: request.url,
          timestamp: request.timestamp,
          tabId: sender.tab.id,
          frameId: sender.frameId
        };

        // Try ConnectionManager first (multi-connection mode)
        const tabConnection = connectionManager.getConnectionForTab(sender.tab.id);
        if (tabConnection) {
          const sent = await connectionManager.sendMessage(sender.tab.id, batchMessage);
          if (!sent) {
            console.log(`[MCP Browser] Message queued for tab ${sender.tab.id}`);
          }
        } else {
          // Fallback to legacy single-connection mode
          if (!sendToServer(batchMessage)) {
            console.log('[MCP Browser] WebSocket not connected, message queued');
          }
        }
      } else {
        // Silently ignore messages from inactive tabs
        console.log(`[MCP Browser] Ignoring console messages from inactive tab ${sender.tab?.id}`);
      }
    });

    sendResponse({ received: true });
  } else if (request.type === 'get_status') {
    // Return enhanced status with all connections
    const connections = connectionManager.getActiveConnections();
    const enhancedStatus = {
      ...connectionStatus,
      multiConnection: true,
      connections: connections,
      totalConnections: connections.length
    };
    sendResponse(enhancedStatus);
  } else if (request.type === 'scan_servers') {
    // Scan for available servers
    scanForServers().then(servers => {
      sendResponse({ servers: servers });
    });
    return true; // Keep channel open for async response
  } else if (request.type === 'connect_to_server') {
    // Connect to specific server using ConnectionManager
    const { port, serverInfo } = request;
    connectionManager.connectToBackend(port, serverInfo).then(connection => {
      sendResponse({ success: true, connection: {
        port: connection.port,
        projectName: connection.projectName,
        projectPath: connection.projectPath
      }});
    }).catch(error => {
      console.error(`[MCP Browser] Failed to connect to port ${port}:`, error);
      sendResponse({ success: false, error: error.message });
    });
    return true; // Keep channel open for async response
  } else if (request.type === 'disconnect') {
    // Disconnect from specific server or all servers
    const { port } = request;
    if (port) {
      // Disconnect from specific port
      connectionManager.disconnectBackend(port).then(() => {
        sendResponse({ received: true, port: port });
      });
    } else {
      // Disconnect from all (legacy behavior + all ConnectionManager connections)
      if (currentConnection) {
        currentConnection.close();
        currentConnection = null;
      }
      // Disconnect all managed connections
      const ports = Array.from(connectionManager.connections.keys());
      Promise.all(ports.map(p => connectionManager.disconnectBackend(p))).then(() => {
        clearConnectionState();
        reconnectAttempts = 0;
        sendResponse({ received: true, disconnectedAll: true });
      });
    }
    return true; // Keep channel open for async response
  } else if (request.type === 'assign_tab_to_port') {
    // Assign a tab to a specific port/connection
    const { tabId, port } = request;
    try {
      connectionManager.assignTabToConnection(tabId, port);
      sendResponse({ success: true });
    } catch (error) {
      sendResponse({ success: false, error: error.message });
    }
  } else if (request.type === 'get_connections') {
    // Get list of all active connections
    const connections = connectionManager.getActiveConnections();
    sendResponse({ connections: connections });
  }
});

// Handle extension installation
chrome.runtime.onInstalled.addListener(async () => {
  console.log('[MCP Browser] Extension installed');

  // Set initial badge - YELLOW (starting state)
  extensionState = 'starting';
  updateBadgeStatus();

  // Load persisted message queue
  await loadMessageQueue();

  // Load port-project mappings
  await loadPortProjectMap();

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

  // Set up periodic scanning with Chrome Alarms
  chrome.alarms.create('serverScan', {
    delayInMinutes: SCAN_INTERVAL_MINUTES,
    periodInMinutes: SCAN_INTERVAL_MINUTES
  });
});

// Handle browser startup
chrome.runtime.onStartup.addListener(async () => {
  console.log('[MCP Browser] Browser started');

  // Load persisted message queue
  await loadMessageQueue();

  // Load port-project mappings
  await loadPortProjectMap();

  autoConnect();

  // Set up periodic scanning with Chrome Alarms
  chrome.alarms.create('serverScan', {
    delayInMinutes: SCAN_INTERVAL_MINUTES,
    periodInMinutes: SCAN_INTERVAL_MINUTES
  });
});

// Initialize on load
try {
  extensionState = 'starting';
  updateBadgeStatus();

  // Delay initial scan slightly to ensure extension is fully loaded
  chrome.alarms.create('reconnect', { delayInMinutes: 100 / 60000 }); // ~100ms
} catch (error) {
  console.error('[MCP Browser] Initialization error:', error);
  extensionState = 'error';
  updateBadgeStatus();
}