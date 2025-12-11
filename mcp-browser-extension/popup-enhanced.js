/**
 * Enhanced popup script for MCP Browser - Connection Dashboard
 * Features:
 * - Multi-connection display with detailed status
 * - Unassigned tab management
 * - Per-connection disconnect
 * - Manual tab assignment
 * - Auto-refresh dashboard
 * Version: 2.0.0 - Connection Dashboard
 */

let currentConnections = [];
let pendingTabs = [];
let refreshInterval = null;

/**
 * Load complete dashboard state
 */
async function loadDashboard() {
  try {
    // Get overall status
    const status = await sendMessage({ type: 'get_status' });

    // Get active connections
    const connectionsResponse = await sendMessage({ type: 'get_connections' });
    currentConnections = connectionsResponse?.connections || [];

    // Get pending/unassigned tabs
    const pendingResponse = await sendMessage({ type: 'get_pending_tabs' });
    pendingTabs = pendingResponse?.pendingTabs || [];

    // Update all UI sections
    updateOverallStatus(status);
    renderConnections(currentConnections);
    renderUnassignedTabs(pendingTabs);

  } catch (error) {
    console.error('[Popup] Failed to load dashboard:', error);
    showError('Failed to load dashboard data');
  }
}

/**
 * Update overall status indicators
 */
function updateOverallStatus(status) {
  const statusIndicator = document.getElementById('status-indicator');
  const statusText = document.getElementById('status-text');
  const connectionCount = document.getElementById('connection-count');
  const messageCount = document.getElementById('message-count');

  if (!status) {
    statusIndicator.className = 'status-indicator disconnected';
    statusText.textContent = 'Error';
    connectionCount.textContent = '0';
    messageCount.textContent = '0';
    return;
  }

  // Update connection count
  const activeCount = status.totalConnections || 0;
  connectionCount.textContent = activeCount;

  // Update status indicator
  if (activeCount > 0) {
    statusIndicator.className = 'status-indicator connected';
    statusText.textContent = `Connected (${activeCount})`;
  } else {
    statusIndicator.className = 'status-indicator disconnected';
    statusText.textContent = 'No Connections';
  }

  // Update message count
  messageCount.textContent = status.messageCount || '0';

  // Clear error if connected
  if (activeCount > 0) {
    document.getElementById('error-container').innerHTML = '';
  } else if (status.lastError) {
    showError(status.lastError);
  }
}

/**
 * Render active connections
 */
function renderConnections(connections) {
  const container = document.getElementById('connections-container');
  const list = document.getElementById('connections-list');

  if (!connections || connections.length === 0) {
    container.style.display = 'none';
    return;
  }

  container.style.display = 'block';
  list.innerHTML = '';

  connections.forEach(connection => {
    const card = createConnectionCard(connection);
    list.appendChild(card);
  });
}

/**
 * Create connection card element
 */
function createConnectionCard(connection) {
  const card = document.createElement('div');
  card.className = 'connection-card';
  if (!connection.ready) {
    card.classList.add('disconnected');
  }

  // Connection header
  const header = document.createElement('div');
  header.className = 'connection-header';

  const info = document.createElement('div');
  info.className = 'connection-info';

  const title = document.createElement('div');
  title.className = 'connection-title';

  // Status dot
  const statusDot = document.createElement('span');
  statusDot.className = `connection-status-dot ${connection.ready ? '' : 'disconnected'}`;
  title.appendChild(statusDot);

  // Project name
  const projectName = document.createElement('span');
  projectName.className = 'connection-project';
  projectName.textContent = connection.projectName || `Port ${connection.port}`;
  title.appendChild(projectName);

  // Expand indicator
  const expandIndicator = document.createElement('span');
  expandIndicator.className = 'expand-indicator';
  expandIndicator.textContent = '▶';
  title.appendChild(expandIndicator);

  info.appendChild(title);

  // Port and tab count
  const meta = document.createElement('div');
  meta.style.display = 'flex';
  meta.style.gap = '8px';
  meta.style.alignItems = 'center';

  const portBadge = document.createElement('span');
  portBadge.className = 'connection-port';
  portBadge.textContent = `Port ${connection.port}`;
  meta.appendChild(portBadge);

  const tabBadge = document.createElement('span');
  tabBadge.className = 'tab-count-badge';
  tabBadge.textContent = `${connection.tabCount} tab${connection.tabCount !== 1 ? 's' : ''}`;
  meta.appendChild(tabBadge);

  if (connection.isPrimary) {
    const primaryBadge = document.createElement('span');
    primaryBadge.style.fontSize = '10px';
    primaryBadge.style.opacity = '0.7';
    primaryBadge.textContent = '(primary)';
    meta.appendChild(primaryBadge);
  }

  info.appendChild(meta);
  header.appendChild(info);

  // Disconnect button
  const disconnectBtn = document.createElement('button');
  disconnectBtn.className = 'disconnect-btn';
  disconnectBtn.textContent = '×';
  disconnectBtn.title = 'Disconnect';
  disconnectBtn.onclick = (e) => {
    e.stopPropagation();
    handleDisconnect(connection.port);
  };
  header.appendChild(disconnectBtn);

  card.appendChild(header);

  // Connection details (expandable)
  const details = document.createElement('div');
  details.className = 'connection-details';

  if (connection.projectPath) {
    const pathRow = document.createElement('div');
    pathRow.className = 'connection-detail-row';
    pathRow.innerHTML = `<span>Path:</span><span style="font-size: 10px; opacity: 0.8;">${truncate(connection.projectPath, 40)}</span>`;
    details.appendChild(pathRow);
  }

  const queueRow = document.createElement('div');
  queueRow.className = 'connection-detail-row';
  queueRow.innerHTML = `<span>Queue Size:</span><span>${connection.queueSize || 0}</span>`;
  details.appendChild(queueRow);

  const statusRow = document.createElement('div');
  statusRow.className = 'connection-detail-row';
  statusRow.innerHTML = `<span>Status:</span><span>${connection.ready ? 'Ready' : 'Connecting...'}</span>`;
  details.appendChild(statusRow);

  card.appendChild(details);

  // Toggle details on header click
  header.onclick = () => {
    details.classList.toggle('expanded');
    expandIndicator.classList.toggle('expanded');
  };

  return card;
}

/**
 * Render unassigned tabs
 */
function renderUnassignedTabs(tabs) {
  const container = document.getElementById('unassigned-container');
  const list = document.getElementById('unassigned-list');
  const count = document.getElementById('unassigned-count');

  count.textContent = tabs.length;

  if (!tabs || tabs.length === 0) {
    container.style.display = 'none';
    return;
  }

  container.style.display = 'block';
  list.innerHTML = '';

  tabs.forEach(tab => {
    const tabCard = createUnassignedTabCard(tab);
    list.appendChild(tabCard);
  });
}

/**
 * Create unassigned tab card
 */
function createUnassignedTabCard(tab) {
  const card = document.createElement('div');
  card.className = 'unassigned-tab';

  // Tab info
  const info = document.createElement('div');
  info.className = 'unassigned-tab-info';

  const title = document.createElement('div');
  title.className = 'unassigned-tab-title';
  title.textContent = getTitleFromUrl(tab.url);
  title.title = getTitleFromUrl(tab.url);
  info.appendChild(title);

  const url = document.createElement('div');
  url.className = 'unassigned-tab-url';
  url.textContent = truncate(tab.url, 50);
  url.title = tab.url;
  info.appendChild(url);

  card.appendChild(info);

  // Backend selection dropdown
  const dropdown = document.createElement('select');
  dropdown.className = 'tab-assign-dropdown';

  const defaultOption = document.createElement('option');
  defaultOption.value = '';
  defaultOption.textContent = 'Select...';
  dropdown.appendChild(defaultOption);

  currentConnections.forEach(conn => {
    const option = document.createElement('option');
    option.value = conn.port;
    option.textContent = `${conn.projectName} (${conn.port})`;
    dropdown.appendChild(option);
  });

  card.appendChild(dropdown);

  // Assign button
  const assignBtn = document.createElement('button');
  assignBtn.className = 'assign-btn';
  assignBtn.textContent = 'Assign';
  assignBtn.disabled = true;

  dropdown.onchange = () => {
    assignBtn.disabled = !dropdown.value;
  };

  assignBtn.onclick = () => {
    if (dropdown.value) {
      handleAssignTab(tab.tabId, parseInt(dropdown.value));
    }
  };

  card.appendChild(assignBtn);

  return card;
}

/**
 * Handle disconnect from backend
 */
async function handleDisconnect(port) {
  try {
    const response = await sendMessage({
      type: 'disconnect',
      port: port
    });

    if (response) {
      console.log(`[Popup] Disconnected from port ${port}`);
      // Refresh dashboard immediately
      await loadDashboard();
    }
  } catch (error) {
    console.error(`[Popup] Failed to disconnect from port ${port}:`, error);
    showError(`Failed to disconnect from port ${port}`);
  }
}

/**
 * Handle manual tab assignment
 */
async function handleAssignTab(tabId, port) {
  try {
    const response = await sendMessage({
      type: 'assign_tab_to_port',
      tabId: tabId,
      port: port
    });

    if (response && response.success) {
      console.log(`[Popup] Assigned tab ${tabId} to port ${port}`);
      // Refresh dashboard immediately
      await loadDashboard();
    } else {
      showError(`Failed to assign tab to port ${port}`);
    }
  } catch (error) {
    console.error(`[Popup] Failed to assign tab ${tabId}:`, error);
    showError(`Failed to assign tab`);
  }
}

/**
 * Handle scan for backends
 */
async function handleScanBackends() {
  const scanButton = document.getElementById('scan-button');
  const originalText = scanButton.textContent;

  try {
    scanButton.disabled = true;
    scanButton.classList.add('scanning');
    scanButton.textContent = '🔄 Scanning...';

    const response = await sendMessage({ type: 'scan_servers' });

    if (response && response.servers) {
      console.log(`[Popup] Found ${response.servers.length} servers`);
    }

    // Refresh dashboard after scan
    await loadDashboard();

  } catch (error) {
    console.error('[Popup] Scan failed:', error);
    showError('Failed to scan for backends');
  } finally {
    scanButton.disabled = false;
    scanButton.classList.remove('scanning');
    scanButton.textContent = originalText;
  }
}

/**
 * Send message to background script with promise wrapper
 */
function sendMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve(response);
      }
    });
  });
}

/**
 * Show error message
 */
function showError(message) {
  const errorContainer = document.getElementById('error-container');
  errorContainer.innerHTML = `
    <div class="error-message">
      ${message}
    </div>
  `;

  // Auto-hide after 5 seconds
  setTimeout(() => {
    errorContainer.innerHTML = '';
  }, 5000);
}

/**
 * Truncate text to max length
 */
function truncate(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Get readable title from URL
 */
function getTitleFromUrl(url) {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname;
    const path = urlObj.pathname;

    if (path && path !== '/') {
      return `${hostname}${path}`;
    }
    return hostname;
  } catch (e) {
    return url;
  }
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }

  refreshInterval = setInterval(() => {
    loadDashboard();
  }, 2000);
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
}

// Event Listeners
document.getElementById('scan-button').addEventListener('click', handleScanBackends);

document.getElementById('test-button').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        func: () => {
          console.log('[MCP Browser Test] Test message at', new Date().toISOString());
          console.info('[MCP Browser Test] Extension is working!');
          console.warn('[MCP Browser Test] This is a warning');
          console.error('[MCP Browser Test] This is an error (test only)');
        }
      }, () => {
        const button = document.getElementById('test-button');
        button.textContent = 'Messages Sent!';
        button.disabled = true;

        setTimeout(() => {
          button.textContent = 'Generate Test Message';
          button.disabled = false;
        }, 1500);
      });
    }
  });
});

// Cleanup on popup close
window.addEventListener('unload', () => {
  stopAutoRefresh();
});

// Initial load
loadDashboard();
startAutoRefresh();
