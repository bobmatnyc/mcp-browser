// MCP Browser Test Page JavaScript
// Comprehensive testing functionality for installation and verification

class MCPBrowserTester {
    constructor() {
        this.ws = null;
        this.extensionDetected = false;
        this.extensionVersion = null;
        this.extensionId = null;
        this.activePort = null;
        this.portRange = { start: 8875, end: 8895 };
        this.consoleBuffer = [];
        this.domEvents = [];
        this.detectionAttempts = 0;
        this.maxDetectionAttempts = 3;

        this.init();
    }

    init() {
        // Initialize all components when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.setupDiagnostics();
        this.setupExtensionDetection();
        this.setupWebSocketConnection();
        this.setupEventListeners();
        this.setupConsoleInterception();
        this.checkSystemStatus();
    }

    // Extension Detection
    setupExtensionDetection() {
        // Inject detection marker for extension to find
        const marker = document.createElement('div');
        marker.id = 'mcp-browser-extension-detector';
        marker.style.display = 'none';
        marker.dataset.version = '1.0.0';
        document.body.appendChild(marker);

        // Listen for extension messages
        window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'MCP_BROWSER_EXTENSION') {
                this.handleExtensionMessage(event.data);
            }
        });

        // Listen for custom event from extension
        document.addEventListener('mcp-browser-extension-ready', (event) => {
            this.extensionDetected = true;
            if (event.detail) {
                this.extensionVersion = event.detail.version;
                this.extensionId = event.detail.id;
            }
            this.updateExtensionStatus(true);
        });

        // Try multiple detection methods
        this.detectExtension();

        // Send detection ping repeatedly
        this.sendExtensionPing();
    }

    sendExtensionPing() {
        // Send ping to detect extension
        window.postMessage({
            type: 'MCP_BROWSER_PING',
            timestamp: Date.now(),
            url: window.location.href
        }, '*');

        // Also try dispatching a custom event
        const pingEvent = new CustomEvent('mcp-browser-test-ping', {
            detail: { timestamp: Date.now() }
        });
        document.dispatchEvent(pingEvent);

        // Retry if not detected yet
        if (!this.extensionDetected && this.detectionAttempts < this.maxDetectionAttempts) {
            this.detectionAttempts++;
            setTimeout(() => this.sendExtensionPing(), 1000);
        }
    }

    detectExtension() {
        // Check multiple methods for extension detection
        const detectionMethods = [
            // Method 1: Check for injected DOM element
            () => {
                const marker = document.querySelector('[data-mcp-browser-extension]');
                if (marker) {
                    this.extensionVersion = marker.dataset.version;
                    return true;
                }
                return false;
            },
            // Method 2: Check for global variable
            () => {
                if (window.__MCP_BROWSER_EXTENSION__) {
                    this.extensionVersion = window.__MCP_BROWSER_EXTENSION__.version;
                    return true;
                }
                return false;
            },
            // Method 3: Check for modified console
            () => {
                // Extension modifies console.log, check for our marker
                const testMarker = '__mcp_browser_test__';
                const originalLog = console.log.toString();
                return originalLog.includes('MCP') || originalLog.includes('chrome.runtime');
            },
            // Method 4: Check for extension-specific CSS class
            () => {
                return document.documentElement.classList.contains('mcp-browser-extension-active');
            },
            // Method 5: Try to access extension resources (Chrome only)
            () => {
                if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.getManifest) {
                    try {
                        // This will only work if we're running as part of the extension
                        const manifest = chrome.runtime.getManifest();
                        if (manifest && manifest.name && manifest.name.includes('mcp-browser')) {
                            this.extensionVersion = manifest.version;
                            return true;
                        }
                    } catch (e) {
                        // Not running as extension
                    }
                }
                return false;
            }
        ];

        // Try each detection method
        for (const method of detectionMethods) {
            try {
                if (method()) {
                    this.extensionDetected = true;
                    break;
                }
            } catch (e) {
                // Method failed, try next
                console.debug('Detection method failed:', e);
            }
        }

        // Check if console has been intercepted by looking at console message in buffer
        if (!this.extensionDetected && this.consoleBuffer.length > 0) {
            const hasExtensionMessage = this.consoleBuffer.some(entry =>
                entry.message.includes('[mcp-browser]')
            );
            if (hasExtensionMessage) {
                this.extensionDetected = true;
            }
        }

        this.updateExtensionStatus(this.extensionDetected);
        return this.extensionDetected;
    }

    handleExtensionMessage(data) {
        if (data.status === 'connected' || data.type === 'MCP_BROWSER_PONG') {
            this.extensionDetected = true;
            if (data.version) {
                this.extensionVersion = data.version;
                const versionEl = document.getElementById('extension-version');
                if (versionEl) versionEl.textContent = data.version;
            }
            if (data.id) {
                this.extensionId = data.id;
            }
            this.updateExtensionStatus(true);

            // Show additional info if available
            if (data.info) {
                console.log('[Extension Info]', data.info);
            }
        }
    }

    updateExtensionStatus(detected) {
        const extStatus = document.getElementById('extension-status');
        const extConnStatus = document.getElementById('ext-connection-status');
        const detectedEl = document.getElementById('extension-detected');
        const notDetectedEl = document.getElementById('extension-not-detected');
        const versionEl = document.getElementById('extension-version');
        const installGuideBtn = document.getElementById('install-guide-btn');
        const refreshExtBtn = document.getElementById('refresh-extension-btn');

        if (detected) {
            if (extStatus) extStatus.className = 'status-dot status-active';
            if (extConnStatus) {
                extConnStatus.textContent = 'Installed';
                extConnStatus.className = 'status-value status-connected';
            }
            if (detectedEl) detectedEl.style.display = 'block';
            if (notDetectedEl) notDetectedEl.style.display = 'none';
            if (versionEl && this.extensionVersion) {
                versionEl.textContent = `v${this.extensionVersion}`;
            }
            if (installGuideBtn) installGuideBtn.style.display = 'none';
            if (refreshExtBtn) refreshExtBtn.style.display = 'none';
        } else {
            if (extStatus) extStatus.className = 'status-dot status-inactive';
            if (extConnStatus) {
                extConnStatus.textContent = 'Not Installed';
                extConnStatus.className = 'status-value status-disconnected';
            }
            if (detectedEl) detectedEl.style.display = 'none';
            if (notDetectedEl) notDetectedEl.style.display = 'block';
            if (versionEl) versionEl.textContent = 'Not detected';
            if (installGuideBtn) installGuideBtn.style.display = 'inline-block';
            if (refreshExtBtn) refreshExtBtn.style.display = 'inline-block';
        }
    }

    // WebSocket Connection
    async setupWebSocketConnection() {
        await this.scanForActivePort();
    }

    async scanForActivePort() {
        for (let port = this.portRange.start; port <= this.portRange.end; port++) {
            const connected = await this.tryConnect(port);
            if (connected) {
                this.activePort = port;
                this.updateConnectionStatus(true, port);
                return;
            }
        }
        this.updateConnectionStatus(false, null);
    }

    tryConnect(port) {
        return new Promise((resolve) => {
            const ws = new WebSocket(`ws://localhost:${port}/browser`);
            const timeout = setTimeout(() => {
                ws.close();
                resolve(false);
            }, 1000);

            ws.onopen = () => {
                clearTimeout(timeout);
                this.ws = ws;
                this.setupWebSocketHandlers(ws);
                resolve(true);
            };

            ws.onerror = () => {
                clearTimeout(timeout);
                resolve(false);
            };
        });
    }

    setupWebSocketHandlers(ws) {
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        };

        ws.onclose = () => {
            this.ws = null;
            this.updateConnectionStatus(false, null);
            // Try to reconnect after 3 seconds
            setTimeout(() => this.scanForActivePort(), 3000);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        // Send initial handshake
        ws.send(JSON.stringify({
            type: 'handshake',
            url: window.location.href,
            timestamp: new Date().toISOString()
        }));
    }

    handleWebSocketMessage(data) {
        if (data.type === 'console_log') {
            this.addConsoleEntry(data);
        } else if (data.type === 'status') {
            this.updateServerStatus(data);
        }
    }

    updateConnectionStatus(connected, port) {
        const wsStatus = document.getElementById('ws-connection-status');
        const serverStatus = document.getElementById('server-status');
        const mcpStatus = document.getElementById('mcp-connection-status');
        const activePortEl = document.getElementById('active-port');
        const serverInfo = document.getElementById('server-info');

        if (connected) {
            if (wsStatus) {
                wsStatus.textContent = 'Connected';
                wsStatus.className = 'status-value status-connected';
            }
            if (serverStatus) serverStatus.className = 'status-dot status-active';
            if (mcpStatus) {
                mcpStatus.textContent = 'Running';
                mcpStatus.className = 'status-value status-connected';
            }
            if (activePortEl) activePortEl.textContent = port;
            if (serverInfo) {
                serverInfo.style.display = 'block';
                document.getElementById('server-port').textContent = port;
                document.getElementById('server-state').textContent = 'Active';
            }
        } else {
            if (wsStatus) {
                wsStatus.textContent = 'Disconnected';
                wsStatus.className = 'status-value status-disconnected';
            }
            if (serverStatus) serverStatus.className = 'status-dot status-inactive';
            if (mcpStatus) {
                mcpStatus.textContent = 'Not Running';
                mcpStatus.className = 'status-value status-disconnected';
            }
            if (activePortEl) activePortEl.textContent = '-';
            if (serverInfo) serverInfo.style.display = 'none';
        }

        this.updateOverallStatus();
    }

    updateServerStatus(data) {
        const mcpStatus = document.getElementById('mcp-status');
        if (mcpStatus && data.mcp_active) {
            mcpStatus.className = 'status-dot status-active';
        }
    }

    updateOverallStatus() {
        const overallStatus = document.getElementById('overall-status');
        if (!overallStatus) return;

        if (this.extensionDetected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            overallStatus.textContent = 'All Systems Operational';
            overallStatus.className = 'status-indicator status-active';
        } else if (this.extensionDetected || this.ws) {
            overallStatus.textContent = 'Partially Connected';
            overallStatus.className = 'status-indicator status-warning';
        } else {
            overallStatus.textContent = 'Not Connected';
            overallStatus.className = 'status-indicator status-inactive';
        }
    }

    // Console Management
    setupConsoleInterception() {
        // Store original console methods
        const originalConsole = {
            log: console.log,
            error: console.error,
            warn: console.warn,
            info: console.info
        };

        // Override console methods
        ['log', 'error', 'warn', 'info'].forEach(method => {
            console[method] = (...args) => {
                // Call original method
                originalConsole[method](...args);

                // Capture for display
                this.captureConsoleOutput(method, args);

                // Send to WebSocket if connected
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'console',
                        method: method,
                        args: args.map(arg => {
                            try {
                                return typeof arg === 'object' ? JSON.stringify(arg) : String(arg);
                            } catch (e) {
                                return String(arg);
                            }
                        }),
                        timestamp: new Date().toISOString(),
                        url: window.location.href
                    }));
                }
            };
        });
    }

    captureConsoleOutput(method, args) {
        const entry = {
            method,
            message: args.map(arg => {
                try {
                    return typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg);
                } catch (e) {
                    return String(arg);
                }
            }).join(' '),
            timestamp: new Date().toISOString()
        };

        this.consoleBuffer.push(entry);
        if (this.consoleBuffer.length > 100) {
            this.consoleBuffer.shift();
        }

        this.addConsoleEntry(entry);
    }

    addConsoleEntry(entry) {
        const output = document.getElementById('console-output');
        if (!output) return;

        // Remove placeholder if present
        const placeholder = output.querySelector('.console-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        const entryEl = document.createElement('div');
        entryEl.className = `console-entry ${entry.method}`;

        const timestamp = document.createElement('span');
        timestamp.className = 'console-timestamp';
        timestamp.textContent = new Date(entry.timestamp).toLocaleTimeString();

        const message = document.createElement('span');
        message.textContent = entry.message;

        entryEl.appendChild(timestamp);
        entryEl.appendChild(message);
        output.appendChild(entryEl);

        // Auto-scroll to bottom
        output.scrollTop = output.scrollHeight;

        // Limit entries to 100
        while (output.children.length > 100) {
            output.removeChild(output.firstChild);
        }
    }

    // Event Listeners
    setupEventListeners() {
        // Test connection button
        const testConnBtn = document.getElementById('test-connection-btn');
        if (testConnBtn) {
            testConnBtn.addEventListener('click', () => this.testAllConnections());
        }

        // Refresh status button
        const refreshBtn = document.getElementById('refresh-status-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.checkSystemStatus());
        }

        // Console test buttons
        document.getElementById('test-console-log')?.addEventListener('click', () => {
            console.log('Test log message at', new Date().toISOString());
        });

        document.getElementById('test-console-error')?.addEventListener('click', () => {
            console.error('Test error message at', new Date().toISOString());
        });

        document.getElementById('test-console-warn')?.addEventListener('click', () => {
            console.warn('Test warning message at', new Date().toISOString());
        });

        document.getElementById('test-console-info')?.addEventListener('click', () => {
            console.info('Test info message at', new Date().toISOString());
        });

        document.getElementById('clear-console')?.addEventListener('click', () => {
            const output = document.getElementById('console-output');
            if (output) {
                output.innerHTML = '<div class="console-placeholder">Console output will appear here...</div>';
            }
            this.consoleBuffer = [];
        });

        // DOM interaction tests
        this.setupDOMTests();

        // Form tests
        this.setupFormTests();

        // Copy buttons
        this.setupCopyButtons();

        // Diagnostics
        document.getElementById('run-diagnostics')?.addEventListener('click', () => {
            this.runFullDiagnostics();
        });

        document.getElementById('export-diagnostics')?.addEventListener('click', () => {
            this.exportDiagnostics();
        });

        // Open DevTools link
        document.getElementById('open-devtools')?.addEventListener('click', (e) => {
            e.preventDefault();
            console.info('Press F12 or Cmd+Option+I (Mac) / Ctrl+Shift+I (Windows/Linux) to open DevTools');
            alert('Press F12 or Cmd+Option+I (Mac) / Ctrl+Shift+I (Windows/Linux) to open DevTools');
        });

        // Extension installation guide button
        document.getElementById('install-guide-btn')?.addEventListener('click', () => {
            window.open('extension-installer.html', '_blank');
        });

        // Refresh extension detection button
        document.getElementById('refresh-extension-btn')?.addEventListener('click', () => {
            this.detectionAttempts = 0;
            this.detectExtension();
            this.sendExtensionPing();

            const btn = document.getElementById('refresh-extension-btn');
            if (btn) {
                btn.textContent = 'Checking...';
                btn.disabled = true;
                setTimeout(() => {
                    btn.textContent = 'Refresh Detection';
                    btn.disabled = false;
                    if (this.extensionDetected) {
                        alert('Extension detected successfully!');
                    } else {
                        alert('Extension not detected. Please ensure it\'s installed and enabled.');
                    }
                }, 2000);
            }
        });

        // Generate manifest button
        document.getElementById('generate-manifest-btn')?.addEventListener('click', () => {
            this.generateManifest();
        });
    }

    setupDOMTests() {
        const domTarget = document.getElementById('dom-target');
        const eventsList = document.getElementById('events-list');

        if (!domTarget || !eventsList) return;

        const logDOMEvent = (eventType, details = {}) => {
            const timestamp = new Date().toLocaleTimeString();
            const eventItem = document.createElement('div');
            eventItem.className = 'event-item';
            eventItem.textContent = `[${timestamp}] ${eventType}: ${JSON.stringify(details)}`;
            eventsList.appendChild(eventItem);

            // Limit to 20 events
            while (eventsList.children.length > 20) {
                eventsList.removeChild(eventsList.firstChild);
            }

            // Auto-scroll
            eventsList.scrollTop = eventsList.scrollHeight;

            // Send to WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'dom_event',
                    eventType,
                    details,
                    timestamp: new Date().toISOString()
                }));
            }
        };

        // Click test
        document.getElementById('test-dom-click')?.addEventListener('click', () => {
            domTarget.click();
        });

        domTarget.addEventListener('click', (e) => {
            domTarget.classList.add('active');
            domTarget.querySelector('.dom-status').textContent = 'Clicked!';
            logDOMEvent('click', { x: e.clientX, y: e.clientY });
            setTimeout(() => {
                domTarget.classList.remove('active');
                domTarget.querySelector('.dom-status').textContent = 'Waiting for interaction...';
            }, 1000);
        });

        // Hover test
        document.getElementById('test-dom-hover')?.addEventListener('click', () => {
            const event = new MouseEvent('mouseenter');
            domTarget.dispatchEvent(event);
            setTimeout(() => {
                const leaveEvent = new MouseEvent('mouseleave');
                domTarget.dispatchEvent(leaveEvent);
            }, 1000);
        });

        domTarget.addEventListener('mouseenter', () => {
            domTarget.classList.add('active');
            domTarget.querySelector('.dom-status').textContent = 'Hovering...';
            logDOMEvent('mouseenter');
        });

        domTarget.addEventListener('mouseleave', () => {
            domTarget.classList.remove('active');
            domTarget.querySelector('.dom-status').textContent = 'Waiting for interaction...';
            logDOMEvent('mouseleave');
        });

        // Scroll test
        document.getElementById('test-dom-scroll')?.addEventListener('click', () => {
            window.scrollTo({ top: domTarget.offsetTop, behavior: 'smooth' });
            logDOMEvent('scroll', { scrollY: window.scrollY });
        });

        window.addEventListener('scroll', () => {
            logDOMEvent('scroll', { scrollY: window.scrollY });
        });
    }

    setupFormTests() {
        const form = document.getElementById('test-form');
        const output = document.getElementById('form-output');

        if (!form || !output) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const data = {};

            for (const [key, value] of formData.entries()) {
                if (data[key]) {
                    if (Array.isArray(data[key])) {
                        data[key].push(value);
                    } else {
                        data[key] = [data[key], value];
                    }
                } else {
                    data[key] = value;
                }
            }

            // Get checkboxes
            const checkboxes = form.querySelectorAll('input[type="checkbox"]:checked');
            data['test-checkbox'] = Array.from(checkboxes).map(cb => cb.value);

            output.innerHTML = `<strong>Form Submitted:</strong><br><pre>${JSON.stringify(data, null, 2)}</pre>`;

            // Send to WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'form_submit',
                    data,
                    timestamp: new Date().toISOString()
                }));
            }

            console.log('Form submitted:', data);
        });

        // Track form changes
        form.addEventListener('change', (e) => {
            console.log(`Form field changed: ${e.target.name} = ${e.target.value}`);
        });
    }

    setupCopyButtons() {
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const textToCopy = btn.dataset.copy;
                try {
                    await navigator.clipboard.writeText(textToCopy);
                    btn.textContent = 'Copied!';
                    btn.classList.add('copied');
                    setTimeout(() => {
                        btn.textContent = 'Copy';
                        btn.classList.remove('copied');
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy:', err);
                }
            });
        });
    }

    // System Status Checks
    async checkSystemStatus() {
        this.detectionAttempts = 0;
        this.detectExtension();
        this.sendExtensionPing();
        await this.scanForActivePort();
        this.updateOverallStatus();

        // Auto-refresh extension detection after a delay
        setTimeout(() => {
            if (!this.extensionDetected) {
                this.detectExtension();
            }
        }, 2000);
    }

    async testAllConnections() {
        const btn = document.getElementById('test-connection-btn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Testing...';
        }

        // Test extension
        this.detectExtension();
        await new Promise(r => setTimeout(r, 500));

        // Test WebSocket
        await this.scanForActivePort();
        await new Promise(r => setTimeout(r, 500));

        // Test console capture
        console.log('Connection test completed at', new Date().toISOString());

        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Test All Connections';
        }

        this.updateOverallStatus();
    }

    // Diagnostics
    setupDiagnostics() {
        // Browser info
        const browserInfo = this.getBrowserInfo();
        document.getElementById('browser-info').textContent = browserInfo;

        // Page URL
        document.getElementById('page-url').textContent = window.location.href;

        // WebSocket support
        document.getElementById('websocket-support').textContent =
            'WebSocket' in window ? 'Supported' : 'Not Supported';

        // Console API
        document.getElementById('console-api').textContent =
            typeof console !== 'undefined' ? 'Available' : 'Not Available';

        // LocalStorage
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
            document.getElementById('localstorage-support').textContent = 'Supported';
        } catch (e) {
            document.getElementById('localstorage-support').textContent = 'Not Supported';
        }
    }

    getBrowserInfo() {
        const ua = navigator.userAgent;
        let browser = 'Unknown';

        if (ua.indexOf('Chrome') > -1) {
            browser = 'Chrome';
        } else if (ua.indexOf('Safari') > -1) {
            browser = 'Safari';
        } else if (ua.indexOf('Firefox') > -1) {
            browser = 'Firefox';
        } else if (ua.indexOf('Edge') > -1) {
            browser = 'Edge';
        }

        const version = navigator.appVersion;
        return `${browser} (${version.split(' ')[0]})`;
    }

    async runFullDiagnostics() {
        const results = {
            timestamp: new Date().toISOString(),
            browser: this.getBrowserInfo(),
            url: window.location.href,
            extension: {
                detected: this.extensionDetected,
                version: document.getElementById('extension-version')?.textContent || 'Unknown'
            },
            websocket: {
                supported: 'WebSocket' in window,
                connected: this.ws && this.ws.readyState === WebSocket.OPEN,
                port: this.activePort
            },
            console: {
                available: typeof console !== 'undefined',
                intercepted: true
            },
            storage: {
                localStorage: this.testLocalStorage(),
                sessionStorage: this.testSessionStorage()
            },
            dom: {
                readyState: document.readyState,
                documentMode: document.documentMode || 'N/A'
            },
            network: {
                online: navigator.onLine,
                connection: navigator.connection || 'N/A'
            }
        };

        console.log('Diagnostic Report:', results);

        // Display results
        alert(`Diagnostics Complete!\n\nExtension: ${results.extension.detected ? 'Detected' : 'Not Found'}\nWebSocket: ${results.websocket.connected ? `Connected on port ${results.websocket.port}` : 'Not Connected'}\n\nFull report logged to console.`);

        return results;
    }

    testLocalStorage() {
        try {
            const test = 'test_' + Date.now();
            localStorage.setItem(test, 'value');
            const value = localStorage.getItem(test);
            localStorage.removeItem(test);
            return value === 'value';
        } catch (e) {
            return false;
        }
    }

    testSessionStorage() {
        try {
            const test = 'test_' + Date.now();
            sessionStorage.setItem(test, 'value');
            const value = sessionStorage.getItem(test);
            sessionStorage.removeItem(test);
            return value === 'value';
        } catch (e) {
            return false;
        }
    }

    async exportDiagnostics() {
        const report = await this.runFullDiagnostics();
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `mcp-browser-diagnostics-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Generate manifest.json for easy setup
    generateManifest() {
        const manifest = {
            manifest_version: 3,
            name: 'MCP Browser Console Capture',
            version: '1.0.0',
            description: 'Captures browser console logs and sends them to local MCP server',
            permissions: [
                'activeTab',
                'tabs',
                'storage',
                'scripting'
            ],
            host_permissions: [
                'http://localhost/*',
                'ws://localhost/*'
            ],
            background: {
                service_worker: 'background.js'
            },
            content_scripts: [
                {
                    matches: ['<all_urls>'],
                    js: ['content.js'],
                    run_at: 'document_start',
                    all_frames: true
                }
            ],
            action: {
                default_popup: 'popup.html',
                default_icon: {
                    '16': 'icon-16.png',
                    '48': 'icon-48.png',
                    '128': 'icon-128.png'
                }
            },
            icons: {
                '16': 'icon-16.png',
                '48': 'icon-48.png',
                '128': 'icon-128.png'
            }
        };

        const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = 'manifest.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('Manifest.json downloaded. Place this in your extension folder.');
    }

    // Get current extension folder path
    getExtensionPath() {
        const currentPath = window.location.pathname;
        const projectRoot = currentPath.substring(0, currentPath.lastIndexOf('/'));
        return `${projectRoot}/extension`;
    }
}

// Initialize the tester
const tester = new MCPBrowserTester();

// Export for debugging
window.MCPBrowserTester = tester;