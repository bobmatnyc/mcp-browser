/**
 * Enhanced popup script for MCP Browser
 * Features:
 * - Multi-server display
 * - Project identification
 * - Server selection
 * Version: 1.0.4 - Auto-versioning enabled
 */

let currentServers = [];
let connectedPort = null;

// Update UI based on connection status
function updateStatus() {
  chrome.runtime.sendMessage({ type: 'get_status' }, (response) => {
    if (!response) {
      showError('Extension error');
      return;
    }

    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const projectRow = document.getElementById('project-row');
    const projectName = document.getElementById('project-name');
    const portRow = document.getElementById('port-row');
    const portValue = document.getElementById('port-value');
    const messageCount = document.getElementById('message-count');
    const disconnectButton = document.getElementById('disconnect-button');

    if (response.connected) {
      statusIndicator.className = 'status-indicator connected';
      statusText.textContent = 'Connected';
      connectedPort = response.port;

      // Show project info
      if (response.projectName) {
        projectRow.style.display = 'flex';
        projectName.textContent = response.projectName;
      }

      // Show port
      portRow.style.display = 'flex';
      portValue.textContent = response.port;

      // Show disconnect button
      disconnectButton.style.display = 'block';

      // Update message count
      messageCount.textContent = response.messageCount || '0';

      // Clear error
      document.getElementById('error-container').innerHTML = '';

      // Update server list to show connected state
      updateServerList();
    } else {
      statusIndicator.className = 'status-indicator disconnected';
      statusText.textContent = 'Disconnected';
      projectRow.style.display = 'none';
      portRow.style.display = 'none';
      disconnectButton.style.display = 'none';
      connectedPort = null;

      if (response.lastError) {
        showError(response.lastError);
      }
    }

    // Update available servers if present
    if (response.availableServers && response.availableServers.length > 0) {
      // Filter to only show valid MCP Browser servers
      const validServers = response.availableServers.filter(server => {
        return server.projectName &&
               server.projectName !== 'Unknown' &&
               server.projectName !== 'Unknown Project' &&
               !server.projectName.startsWith('Port ');
      });
      currentServers = validServers;
      showServers(validServers);
    }
  });
}

// Show available servers
function showServers(servers) {
  const container = document.getElementById('servers-container');
  const list = document.getElementById('servers-list');

  // Filter out any servers without valid project names
  const validServers = servers.filter(server => {
    return server.projectName &&
           server.projectName !== 'Unknown' &&
           server.projectName !== 'Unknown Project' &&
           !server.projectName.startsWith('Port ');
  });

  if (!validServers || validServers.length === 0) {
    container.style.display = 'none';
    return;
  }

  container.style.display = 'block';
  list.innerHTML = '';

  validServers.forEach(server => {
    const item = document.createElement('div');
    item.className = 'server-item';

    if (server.port === connectedPort) {
      item.className += ' connected';
    }

    item.innerHTML = `
      <div style="display: flex; align-items: center; margin-bottom: 4px;">
        <span class="server-port">${server.port}</span>
        <span class="server-project">${server.projectName}</span>
      </div>
      <div class="server-path">${server.projectPath || 'No path specified'}</div>
    `;

    item.onclick = () => connectToServer(server);
    list.appendChild(item);
  });
}

// Connect to a specific server
function connectToServer(server) {
  if (server.port === connectedPort) {
    return; // Already connected
  }

  const statusText = document.getElementById('status-text');
  statusText.textContent = 'Connecting...';

  chrome.runtime.sendMessage({
    type: 'connect_to_server',
    port: server.port,
    serverInfo: server
  }, (response) => {
    if (response && response.success) {
      updateStatus();
    } else {
      showError(`Failed to connect to port ${server.port}`);
      updateStatus();
    }
  });
}

// Scan for available servers
function scanServers() {
  const statusText = document.getElementById('status-text');
  const scanButton = document.getElementById('scan-button');

  statusText.textContent = 'Scanning...';
  scanButton.disabled = true;

  chrome.runtime.sendMessage({ type: 'scan_servers' }, (response) => {
    scanButton.disabled = false;

    if (response && response.servers) {
      // Filter to only valid MCP Browser servers
      const validServers = response.servers.filter(server => {
        return server.projectName &&
               server.projectName !== 'Unknown' &&
               server.projectName !== 'Unknown Project' &&
               !server.projectName.startsWith('Port ');
      });

      currentServers = validServers;

      if (validServers.length === 0) {
        showError('No MCP Browser servers found');
        document.getElementById('servers-container').style.display = 'none';
      } else {
        showServers(validServers);

        // Auto-connect if only one server
        if (validServers.length === 1 && !connectedPort) {
          connectToServer(validServers[0]);
        }
      }
    }

    updateStatus();
  });
}

// Disconnect from current server
function disconnect() {
  chrome.runtime.sendMessage({ type: 'disconnect' }, () => {
    updateStatus();
    scanServers(); // Rescan after disconnect
  });
}

// Show error message
function showError(message) {
  const errorContainer = document.getElementById('error-container');
  errorContainer.innerHTML = `
    <div class="error-message">
      ${message}
    </div>
  `;
}

// Update server list display
function updateServerList() {
  if (currentServers.length > 0) {
    showServers(currentServers);
  }
}

// Test button handler
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
          updateStatus();
        }, 1500);
      });
    }
  });
});

// Scan button handler
document.getElementById('scan-button').addEventListener('click', scanServers);

// Disconnect button handler
document.getElementById('disconnect-button').addEventListener('click', disconnect);

// Initial load
updateStatus();
scanServers(); // Auto-scan on popup open

// Update status periodically
setInterval(updateStatus, 2000);