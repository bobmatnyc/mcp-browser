/**
 * Simplified popup script for MCP Browser
 * Features:
 * - Overall server connection status
 * - Current tab connection status
 * - Auto-refresh dashboard
 * Version: 2.1.0 - Simplified Current Tab View
 */

let refreshInterval = null;

/**
 * Load dashboard state
 */
async function loadDashboard() {
  try {
    // Get overall status
    const status = await sendMessage({ type: 'get_status' });

    // Get current tab info
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const currentTab = tabs[0];

    // Update UI
    updateOverallStatus(status);
    if (currentTab) {
      await updateCurrentTabStatus(currentTab.id);
    }

    // Update backend list
    await updateBackendList(status);

  } catch (error) {
    console.error('[Popup] Failed to load dashboard:', error);
    showError('Failed to load dashboard data');
  }
}

/**
 * Update overall server status indicators
 */
function updateOverallStatus(status) {
  const statusIndicator = document.getElementById('status-indicator');
  const statusText = document.getElementById('status-text');
  const messageCount = document.getElementById('message-count');

  if (!status) {
    statusIndicator.className = 'status-indicator disconnected';
    statusText.textContent = 'Error';
    messageCount.textContent = '0';
    return;
  }

  // Update server connection status
  const activeCount = status.totalConnections || 0;

  if (activeCount > 0) {
    statusIndicator.className = 'status-indicator connected';
    if (activeCount === 1) {
      statusText.textContent = 'Server Connected';
    } else {
      statusText.textContent = `${activeCount} Servers Connected`;
    }
  } else {
    statusIndicator.className = 'status-indicator disconnected';
    statusText.textContent = 'Server Disconnected';
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
 * Update current tab connection status
 */
async function updateCurrentTabStatus(tabId) {
  const tabStatusIndicator = document.getElementById('tab-status-indicator');
  const tabStatusText = document.getElementById('tab-status-text');

  try {
    // Get tab connections
    const tabConnectionsResponse = await sendMessage({ type: 'get_tab_connections' });
    const tabConnections = tabConnectionsResponse?.tabConnections || [];

    // Find current tab
    const currentTabConnection = tabConnections.find(tc => tc.tabId === tabId);

    if (currentTabConnection && currentTabConnection.assignedPort) {
      // Tab is connected - show project name if available
      tabStatusIndicator.className = 'status-indicator connected';
      const projectName = currentTabConnection.backendName || `Port ${currentTabConnection.assignedPort}`;
      tabStatusText.textContent = `Connected to ${projectName} (port ${currentTabConnection.assignedPort})`;
    } else {
      // Tab is not connected
      tabStatusIndicator.className = 'status-indicator disconnected';
      tabStatusText.textContent = 'Not connected';
    }
  } catch (error) {
    console.error('[Popup] Failed to get current tab status:', error);
    tabStatusIndicator.className = 'status-indicator disconnected';
    tabStatusText.textContent = 'Error';
  }
}

/**
 * Update backend list display
 */
async function updateBackendList(status) {
  const backendListContainer = document.getElementById('backend-list-container');
  const backendList = document.getElementById('backend-list');

  // Get available servers from status
  const availableServers = status?.availableServers || [];

  // Get current tab to check if connected
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const currentTab = tabs[0];
  let isCurrentTabConnected = false;

  if (currentTab) {
    const tabConnectionsResponse = await sendMessage({ type: 'get_tab_connections' });
    const tabConnections = tabConnectionsResponse?.tabConnections || [];
    const currentTabConnection = tabConnections.find(tc => tc.tabId === currentTab.id);
    isCurrentTabConnected = currentTabConnection && currentTabConnection.assignedPort;
  }

  // Show backend list only if:
  // 1. There are available backends
  // 2. Current tab is not connected
  if (availableServers.length > 0 && !isCurrentTabConnected) {
    backendListContainer.style.display = 'block';

    // Clear existing list
    backendList.innerHTML = '';

    // Render each backend
    availableServers.forEach(server => {
      const item = document.createElement('div');
      item.className = 'backend-item';

      item.innerHTML = `
        <div class="backend-info">
          <div class="backend-name">${server.projectName || 'Unknown Project'}</div>
          <div class="backend-port">Port ${server.port}</div>
        </div>
        <button class="backend-connect-btn" data-port="${server.port}">Connect</button>
      `;

      // Add click handler to connect button
      const connectBtn = item.querySelector('.backend-connect-btn');
      connectBtn.addEventListener('click', () => handleConnectToBackend(server.port, currentTab.id));

      backendList.appendChild(item);
    });
  } else {
    // Hide backend list if connected or no backends available
    backendListContainer.style.display = 'none';
  }
}

/**
 * Handle connecting current tab to a specific backend
 */
async function handleConnectToBackend(port, tabId) {
  try {
    console.log(`[Popup] Connecting tab ${tabId} to backend on port ${port}`);

    // Disable all connect buttons
    document.querySelectorAll('.backend-connect-btn').forEach(btn => {
      btn.disabled = true;
      btn.textContent = 'Connecting...';
    });

    // Assign tab to the selected port
    const response = await sendMessage({
      type: 'assign_tab_to_port',
      tabId: tabId,
      port: port
    });

    if (response && response.success) {
      console.log(`[Popup] Successfully connected tab ${tabId} to port ${port}`);

      // Refresh dashboard to update UI
      await loadDashboard();
    } else {
      throw new Error(response?.error || 'Failed to assign tab to port');
    }

  } catch (error) {
    console.error('[Popup] Failed to connect to backend:', error);
    showError(`Failed to connect: ${error.message}`);

    // Re-enable buttons
    document.querySelectorAll('.backend-connect-btn').forEach(btn => {
      btn.disabled = false;
      btn.textContent = 'Connect';
    });
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

/**
 * Handle scan for backends button click
 */
async function handleScanBackends() {
  const button = document.getElementById('scan-button');
  const originalText = button.textContent;

  button.textContent = 'Scanning...';
  button.disabled = true;

  try {
    await sendMessage({ type: 'scan_backends' });
    // Refresh dashboard to show new backends
    await loadDashboard();
  } catch (error) {
    console.error('[Popup] Scan failed:', error);
    showError('Scan failed: ' + error.message);
  } finally {
    button.textContent = originalText;
    button.disabled = false;
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
