/**
 * Popup script for status display
 */

// Update status display
function updateStatus() {
  chrome.runtime.sendMessage({ type: 'get_status' }, (response) => {
    if (!response) {
      document.getElementById('status-text').textContent = 'Extension Error';
      document.getElementById('status-indicator').className = 'status-indicator disconnected';
      return;
    }

    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const portValue = document.getElementById('port-value');
    const messageCount = document.getElementById('message-count');
    const errorContainer = document.getElementById('error-container');

    if (response.connected) {
      statusIndicator.className = 'status-indicator connected';
      statusText.textContent = 'Connected';
      portValue.textContent = response.port || '-';
      messageCount.textContent = response.messageCount || '0';
      errorContainer.innerHTML = '';
    } else {
      statusIndicator.className = 'status-indicator disconnected';
      statusText.textContent = 'Disconnected';
      portValue.textContent = '-';

      if (response.lastError) {
        errorContainer.innerHTML = `
          <div class="error-message">
            ${response.lastError}
          </div>
        `;
      }
    }
  });
}

// Reconnect button handler
document.getElementById('reconnect-button').addEventListener('click', () => {
  // Send reconnect message to background script
  chrome.runtime.sendMessage({ type: 'reconnect' });

  // Update button text temporarily
  const button = document.getElementById('reconnect-button');
  button.textContent = 'Reconnecting...';
  button.disabled = true;

  setTimeout(() => {
    button.textContent = 'Reconnect';
    button.disabled = false;
    updateStatus();
  }, 2000);
});

// Update status on load
updateStatus();

// Update status periodically
setInterval(updateStatus, 2000);