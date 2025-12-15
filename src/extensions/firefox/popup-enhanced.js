/**
 * Simplified popup script for MCP Browser
 * Features:
 * - Overall server connection status
 * - Current tab connection status
 * - Auto-refresh dashboard
 * Version: 2.1.0 - Simplified Current Tab View
 */

let refreshInterval = null;
let isUpdating = false; // Prevent concurrent updates
let errorDebounceTimer = null; // Debounce error messages

/**
 * Check if URL is a restricted page where extension cannot operate
 */
function isRestrictedPage(url) {
  if (!url) return true;
  const restrictedPrefixes = [
    'chrome://',
    'chrome-extension://',
    'about:',
    'edge://',
    'brave://',
    'opera://',
    'vivaldi://',
    'moz-extension://',
    'file://'  // Local files also restricted by default
  ];
  return restrictedPrefixes.some(prefix => url.startsWith(prefix));
}

/**
 * Load dashboard state
 */
async function loadDashboard() {
  // Prevent concurrent updates that cause flashing
  if (isUpdating) {
    return;
  }

  isUpdating = true;

  try {
    // Get overall status
    const status = await sendMessage({ type: 'get_status' });

    // Get current tab info
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const currentTab = tabs[0];

    // Update UI smoothly (only update changed elements)
    updateOverallStatus(status);
    if (currentTab) {
      await updateCurrentTabStatus(currentTab.id);
    }

    // Update backend list
    await updateBackendList(status);

  } catch (error) {
    console.error('[Popup] Failed to load dashboard:', error);
    showError('Failed to load dashboard data');
  } finally {
    isUpdating = false;
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

  // Only update if changed (prevent flashing)
  const newStatusClass = activeCount > 0 ? 'status-indicator connected' : 'status-indicator disconnected';
  if (statusIndicator.className !== newStatusClass) {
    statusIndicator.className = newStatusClass;
  }

  let newStatusText;
  if (activeCount > 0) {
    newStatusText = activeCount === 1 ? 'Server Connected' : `${activeCount} Servers Connected`;
  } else {
    newStatusText = 'Server Disconnected';
  }

  if (statusText.textContent !== newStatusText) {
    statusText.textContent = newStatusText;
  }

  // Update message count only if changed
  const newCount = status.messageCount || '0';
  if (messageCount.textContent !== newCount.toString()) {
    messageCount.textContent = newCount;
  }

  // Clear error if connected
  if (activeCount > 0) {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer.innerHTML !== '') {
      errorContainer.innerHTML = '';
    }
    // Clear any pending error debounce
    if (errorDebounceTimer) {
      clearTimeout(errorDebounceTimer);
      errorDebounceTimer = null;
    }
  } else if (status.lastError) {
    // Debounce error messages to avoid rapid flashing
    if (errorDebounceTimer) {
      clearTimeout(errorDebounceTimer);
    }
    errorDebounceTimer = setTimeout(() => {
      showError(status.lastError);
      errorDebounceTimer = null;
    }, 500); // Wait 500ms before showing error
  }
}

/**
 * Update current tab connection status
 */
async function updateCurrentTabStatus(tabId) {
  const tabStatusIndicator = document.getElementById('tab-status-indicator');
  const tabStatusText = document.getElementById('tab-status-text');
  const tabInfoElement = document.getElementById('tab-info');

  try {
    // Get current tab info
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const currentTab = tabs[0];

    // Check if this is a restricted page
    if (currentTab && isRestrictedPage(currentTab.url)) {
      tabStatusIndicator.className = 'status-indicator warning';
      tabStatusText.textContent = 'Restricted page';
      if (tabInfoElement) {
        tabInfoElement.textContent = 'Cannot connect on browser internal pages';
        tabInfoElement.style.display = 'block';
      }
      return;
    }

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

      // Show tab title/URL
      if (tabInfoElement && currentTab) {
        const tabTitle = currentTab.title || currentTab.url || 'Unknown';
        tabInfoElement.textContent = `Tab: ${tabTitle}`;
        tabInfoElement.style.display = 'block';
      }
    } else {
      // Tab is not connected
      tabStatusIndicator.className = 'status-indicator disconnected';
      tabStatusText.textContent = 'Not connected';

      // Hide tab info when not connected
      if (tabInfoElement) {
        tabInfoElement.style.display = 'none';
      }
    }
  } catch (error) {
    console.error('[Popup] Failed to get current tab status:', error);
    tabStatusIndicator.className = 'status-indicator disconnected';
    tabStatusText.textContent = 'Error';

    // Hide tab info on error
    if (tabInfoElement) {
      tabInfoElement.style.display = 'none';
    }
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

  // Don't show backend list on restricted pages
  if (currentTab && isRestrictedPage(currentTab.url)) {
    backendListContainer.style.display = 'none';
    return;
  }

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

    // Clear any error message since we found servers
    document.getElementById('error-container').innerHTML = '';

    // Clear existing list
    backendList.innerHTML = '';

    // Render each backend
    console.log(`[Popup] Rendering ${availableServers.length} backends, currentTab:`, currentTab);
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
      const tabIdToUse = currentTab?.id;
      console.log(`[Popup] Adding click handler for port ${server.port}, tabId: ${tabIdToUse}`);

      connectBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        console.log(`[Popup] Connect button clicked for port ${server.port}, tabId: ${tabIdToUse}`);
        if (!tabIdToUse) {
          console.error('[Popup] No tab ID available!');
          showError('No active tab found');
          return;
        }
        await handleConnectToBackend(server.port, tabIdToUse);
      });

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
  const connectBtn = document.querySelector(`.backend-connect-btn[data-port="${port}"]`);
  const progressContainer = document.getElementById('connect-progress-container');
  const progressBar = document.getElementById('connect-progress-bar');
  const progressText = document.getElementById('connect-progress-text');

  try {
    console.log(`[Popup] Connecting tab ${tabId} to backend on port ${port}`);

    if (!tabId) {
      throw new Error('No tab ID provided');
    }
    if (!port) {
      throw new Error('No port provided');
    }

    // Update button state
    if (connectBtn) {
      connectBtn.disabled = true;
      connectBtn.textContent = 'Connecting...';
    }

    // Show progress bar
    progressContainer.classList.add('visible');
    progressText.classList.add('visible');
    progressText.textContent = `Connecting to port ${port}...`;
    progressBar.style.width = '30%';

    // Assign tab to the selected port
    const response = await sendMessage({
      type: 'assign_tab_to_port',
      tabId: tabId,
      port: port
    });

    console.log(`[Popup] assign_tab_to_port response:`, response);

    // Update progress
    progressBar.style.width = '70%';

    if (response && response.success) {
      console.log(`[Popup] Successfully connected tab ${tabId} to port ${port}`);

      // Complete progress
      progressBar.style.width = '100%';
      progressText.textContent = `Connected to port ${port}!`;

      // Hide the backend list immediately
      const backendListContainer = document.getElementById('backend-list-container');
      if (backendListContainer) {
        backendListContainer.style.display = 'none';
      }

      // Update current tab status immediately
      const tabStatusIndicator = document.getElementById('tab-status-indicator');
      const tabStatusText = document.getElementById('tab-status-text');
      if (tabStatusIndicator && tabStatusText) {
        tabStatusIndicator.className = 'status-indicator connected';
        tabStatusText.textContent = `Connected to port ${port}`;
      }

      // Refresh dashboard to get full status
      await loadDashboard();

      // Hide progress after a short delay
      setTimeout(() => {
        progressContainer.classList.remove('visible');
        progressText.classList.remove('visible');
        progressBar.style.width = '0%';
      }, 1000);
    } else {
      throw new Error(response?.error || 'Failed to connect');
    }

  } catch (error) {
    console.error('[Popup] Failed to connect to backend:', error);
    showError(`Failed to connect: ${error.message}`);

    // Hide progress bar
    progressContainer.classList.remove('visible');
    progressText.classList.remove('visible');
    progressBar.style.width = '0%';

    // Re-enable button
    if (connectBtn) {
      connectBtn.disabled = false;
      connectBtn.textContent = 'Connect';
    }
  }
}


/**
 * Handle scan for backends
 */
async function handleScanBackends() {
  const scanButton = document.getElementById('scan-button');
  const originalText = scanButton.textContent;
  const progressContainer = document.getElementById('scan-progress-container');
  const progressBar = document.getElementById('scan-progress-bar');
  const progressText = document.getElementById('scan-progress-text');

  try {
    scanButton.disabled = true;
    scanButton.classList.add('scanning');
    scanButton.textContent = '🔄 Scanning...';

    // Show progress bar
    progressContainer.classList.add('visible');
    progressText.classList.add('visible');
    progressBar.style.width = '0%';

    console.log('[Popup] Starting server scan...');

    // Simulate scanning progress (ports 8851-8899, ~49 ports)
    const totalPorts = 49;
    let currentPort = 8851;

    // Start progress animation
    const progressInterval = setInterval(() => {
      const portOffset = currentPort - 8851;
      const progress = Math.min((portOffset / totalPorts) * 100, 95);
      progressBar.style.width = `${progress}%`;
      progressText.textContent = `Scanning port ${currentPort}...`;
      currentPort++;

      if (currentPort > 8899) {
        clearInterval(progressInterval);
      }
    }, 30); // Update every 30ms for smooth animation

    const response = await sendMessage({ type: 'scan_servers' });

    // Clear the progress interval
    clearInterval(progressInterval);

    if (response && response.servers) {
      console.log(`[Popup] Found ${response.servers.length} servers:`, response.servers);

      // Complete progress
      progressBar.style.width = '100%';
      progressText.textContent = `Found ${response.servers.length} backend${response.servers.length !== 1 ? 's' : ''}!`;

      if (response.servers.length > 0) {
        // Clear error container immediately
        document.getElementById('error-container').innerHTML = '';
      }
    } else {
      console.log('[Popup] Scan response:', response);
      progressBar.style.width = '100%';
      progressText.textContent = 'Scan complete';
    }

    // Refresh dashboard after scan
    console.log('[Popup] Refreshing dashboard...');
    await loadDashboard();
    console.log('[Popup] Dashboard refreshed');

    // Hide progress bar after a short delay
    setTimeout(() => {
      progressContainer.classList.remove('visible');
      progressText.classList.remove('visible');
      progressBar.style.width = '0%';
    }, 1500);

  } catch (error) {
    console.error('[Popup] Scan failed:', error);
    showError('Failed to scan for backends');

    // Hide progress bar on error
    progressContainer.classList.remove('visible');
    progressText.classList.remove('visible');
    progressBar.style.width = '0%';
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

  // Increased to 5 seconds to reduce flashing
  // UI updates are now smooth and only change elements that have changed
  refreshInterval = setInterval(() => {
    loadDashboard();
  }, 5000);
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
 * Toggle technical details panel
 */
function toggleTechnicalPanel() {
  const panel = document.getElementById('technical-panel');
  const isVisible = panel.classList.contains('visible');

  if (isVisible) {
    panel.classList.remove('visible');
  } else {
    panel.classList.add('visible');
    // Load detailed technical info when opening
    loadTechnicalDetails();
  }
}

/**
 * Load detailed technical information
 */
async function loadTechnicalDetails() {
  try {
    // Get detailed status from background
    const detailedStatus = await sendMessage({ type: 'get_detailed_status' });

    // Get manifest version
    const manifest = chrome.runtime.getManifest();

    // Update technical panel fields
    document.getElementById('tech-version').textContent = manifest.version || 'unknown';
    document.getElementById('tech-ws-port').textContent = detailedStatus.port || '-';
    document.getElementById('tech-conn-state').textContent = detailedStatus.connectionState || 'disconnected';
    document.getElementById('tech-retry-count').textContent = detailedStatus.retryCount || '0';
    document.getElementById('tech-project-name').textContent = detailedStatus.projectName || '-';
    document.getElementById('tech-server-pid').textContent = detailedStatus.serverPid || '-';
    document.getElementById('tech-msg-count').textContent = detailedStatus.messageCount || '0';
    document.getElementById('tech-last-error').textContent = detailedStatus.lastError || 'none';

  } catch (error) {
    console.error('[Popup] Failed to load technical details:', error);
  }
}

/**
 * Copy debug info to clipboard
 */
async function copyDebugInfo() {
  const btn = document.getElementById('copy-debug-btn');

  try {
    // Get detailed status
    const detailedStatus = await sendMessage({ type: 'get_detailed_status' });
    const manifest = chrome.runtime.getManifest();

    // Format debug info
    const debugInfo = `MCP Browser Extension - Debug Info
=====================================
Extension Version: ${manifest.version}
WebSocket Port: ${detailedStatus.port || 'not connected'}
Connection State: ${detailedStatus.connectionState || 'disconnected'}
Retry Count: ${detailedStatus.retryCount || '0'}
Server Project: ${detailedStatus.projectName || 'none'}
Server PID: ${detailedStatus.serverPid || 'unknown'}
Messages Captured: ${detailedStatus.messageCount || '0'}
Last Error: ${detailedStatus.lastError || 'none'}
Timestamp: ${new Date().toISOString()}
=====================================`;

    // Copy to clipboard
    await navigator.clipboard.writeText(debugInfo);

    // Show feedback
    const originalText = btn.textContent;
    btn.textContent = '✓ Copied!';
    btn.classList.add('copied');

    setTimeout(() => {
      btn.textContent = originalText;
      btn.classList.remove('copied');
    }, 2000);

  } catch (error) {
    console.error('[Popup] Failed to copy debug info:', error);
    btn.textContent = '✗ Failed';
    setTimeout(() => {
      btn.textContent = '📋 Copy Debug Info';
    }, 2000);
  }
}

// Event Listeners
document.getElementById('scan-button').addEventListener('click', handleScanBackends);
document.getElementById('gear-icon').addEventListener('click', toggleTechnicalPanel);
document.getElementById('close-tech-panel').addEventListener('click', toggleTechnicalPanel);
document.getElementById('copy-debug-btn').addEventListener('click', copyDebugInfo);

// Cleanup on popup close
window.addEventListener('unload', () => {
  stopAutoRefresh();
});

// Initial load
loadDashboard();
startAutoRefresh();
