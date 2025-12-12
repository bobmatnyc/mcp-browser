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
      // Tab is connected
      tabStatusIndicator.className = 'status-indicator connected';
      tabStatusText.textContent = `Connected to port ${currentTabConnection.assignedPort}`;
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
