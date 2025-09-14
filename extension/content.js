/**
 * Content script to capture console messages
 */

(function() {
  'use strict';

  // Message buffer
  const messageBuffer = [];
  let bufferTimer = null;
  const BUFFER_INTERVAL = 2500; // 2.5 seconds
  const MAX_BUFFER_SIZE = 100;

  // Store original console methods
  const originalConsole = {
    log: console.log,
    warn: console.warn,
    error: console.error,
    info: console.info,
    debug: console.debug
  };

  // Send message to background script
  function sendToBackground(messages) {
    chrome.runtime.sendMessage({
      type: 'console_messages',
      messages: messages,
      url: window.location.href,
      timestamp: new Date().toISOString()
    });
  }

  // Flush message buffer
  function flushBuffer() {
    if (messageBuffer.length > 0) {
      sendToBackground([...messageBuffer]);
      messageBuffer.length = 0;
    }
  }

  // Schedule buffer flush
  function scheduleFlush() {
    if (bufferTimer) {
      clearTimeout(bufferTimer);
    }
    bufferTimer = setTimeout(flushBuffer, BUFFER_INTERVAL);
  }

  // Capture console method
  function captureConsoleMethod(method, level) {
    console[method] = function(...args) {
      // Call original method
      originalConsole[method].apply(console, args);

      // Create message object
      const message = {
        level: level,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        args: args.map(arg => {
          try {
            if (typeof arg === 'object') {
              return JSON.stringify(arg, null, 2);
            }
            return String(arg);
          } catch (e) {
            return '[Object]';
          }
        }),
        message: args.map(arg => {
          try {
            if (typeof arg === 'object') {
              return JSON.stringify(arg);
            }
            return String(arg);
          } catch (e) {
            return '[Object]';
          }
        }).join(' ')
      };

      // Add stack trace for errors
      if (level === 'error') {
        const error = new Error();
        message.stackTrace = error.stack;
      }

      // Add to buffer
      messageBuffer.push(message);

      // Flush if buffer is full
      if (messageBuffer.length >= MAX_BUFFER_SIZE) {
        flushBuffer();
      } else {
        scheduleFlush();
      }
    };
  }

  // Capture all console methods
  captureConsoleMethod('log', 'log');
  captureConsoleMethod('warn', 'warn');
  captureConsoleMethod('error', 'error');
  captureConsoleMethod('info', 'info');
  captureConsoleMethod('debug', 'debug');

  // Capture unhandled errors
  window.addEventListener('error', function(event) {
    const message = {
      level: 'error',
      timestamp: new Date().toISOString(),
      url: window.location.href,
      message: `${event.message}`,
      stackTrace: event.error ? event.error.stack : '',
      lineNumber: event.lineno,
      columnNumber: event.colno,
      sourceFile: event.filename
    };

    messageBuffer.push(message);
    scheduleFlush();
  });

  // Capture unhandled promise rejections
  window.addEventListener('unhandledrejection', function(event) {
    const message = {
      level: 'error',
      timestamp: new Date().toISOString(),
      url: window.location.href,
      message: `Unhandled Promise Rejection: ${event.reason}`,
      stackTrace: event.reason && event.reason.stack ? event.reason.stack : ''
    };

    messageBuffer.push(message);
    scheduleFlush();
  });

  // Flush buffer before page unload
  window.addEventListener('beforeunload', function() {
    flushBuffer();
  });

  // Listen for navigation commands from background
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'navigate') {
      window.location.href = request.url;
      sendResponse({ success: true });
    }
  });

  // Initial console message to confirm injection
  console.log('[BrowserPyMCP] Console capture initialized');

})();