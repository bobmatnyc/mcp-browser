# DEVELOPER.md - Technical Implementation Guide

**Architecture**: Service-Oriented Architecture (SOA) with Dependency Injection
**Framework**: Python asyncio + MCP SDK + Chrome Extension

## Quick Start

### 5-Minute Setup
```bash
# 1. Install dependencies
make install

# 2. Start development server
make dev

# 3. Load Chrome extension
# Navigate to chrome://extensions/
# Enable "Developer mode" → "Load unpacked" → Select extension/ folder

# 4. Configure Claude Code
# The MCP server integrates directly with Claude Code.
# Start the MCP server with:
# browserpymcp mcp
```

## Service Architecture Deep Dive

### Dependency Injection Container

**Location**: `src/container/service_container.py`

The DI container uses constructor parameter name matching for dependency resolution:

```python
class BrowserService:
    def __init__(self, storage_service=None):  # Parameter name matches service name
        self.storage_service = storage_service

# Registration
async def create_browser_service(container):
    storage = await container.get('storage_service')  # Auto-resolved
    return BrowserService(storage_service=storage)

container.register('browser_service', create_browser_service)
```

**Key Methods**:
- `register(name, factory, singleton=True)`: Register service factory
- `register_instance(name, instance)`: Register existing instance
- `get(name) -> Any`: Resolve service with dependencies
- `inject(*service_names)`: Decorator for function injection

### Service Interfaces

#### WebSocketService
**File**: `src/services/websocket_service.py`
**Responsibility**: Browser connection management with port auto-discovery

```python
class WebSocketService:
    async def start() -> int:
        """Start server on first available port (8875-8895)"""

    async def stop() -> None:
        """Gracefully close all connections and stop server"""

    def register_message_handler(message_type: str, handler: Callable):
        """Register handler for specific message types"""

    def register_connection_handler(event: str, handler: Callable):
        """Register handler for connect/disconnect events"""

    async def broadcast_message(message: Dict[str, Any]) -> None:
        """Send message to all connected clients"""

    def get_server_info() -> Dict[str, Any]:
        """Get server status and connection count"""
```

**Message Handler Pattern**:
```python
# In main.py setup
websocket.register_message_handler('console', browser.handle_console_message)
websocket.register_message_handler('batch', browser.handle_batch_messages)
websocket.register_connection_handler('connect', browser.handle_browser_connect)
websocket.register_connection_handler('disconnect', browser.handle_browser_disconnect)
```

#### BrowserService
**File**: `src/services/browser_service.py`
**Responsibility**: Console message processing and browser control

```python
class BrowserService:
    async def handle_console_message(data: Dict[str, Any]) -> None:
        """Process incoming console message from WebSocket"""

    async def handle_batch_messages(data: Dict[str, Any]) -> None:
        """Process batch of console messages"""

    async def navigate_browser(port: int, url: str) -> bool:
        """Send navigation command to browser"""

    async def query_logs(
        port: int,
        last_n: int = 100,
        level_filter: Optional[List[str]] = None
    ) -> List[ConsoleMessage]:
        """Query console logs with filtering"""

    async def get_browser_stats() -> Dict[str, Any]:
        """Get browser connection and buffer statistics"""
```

**Message Buffering Pattern**:
```python
# Messages buffered in memory with periodic flush
self._message_buffer[port] = deque(maxlen=1000)
self._buffer_interval = 2.5  # seconds

# Background task for periodic flush
asyncio.create_task(self._flush_buffer_periodically(port))
```

#### StorageService
**File**: `src/services/storage_service.py`
**Responsibility**: JSONL persistence with automatic rotation

```python
class StorageService:
    async def store_message(message: ConsoleMessage) -> None:
        """Store single console message"""

    async def store_messages_batch(messages: List[ConsoleMessage]) -> None:
        """Batch store multiple messages"""

    async def query_messages(
        port: int,
        last_n: int = 100,
        level_filter: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[ConsoleMessage]:
        """Query stored messages with filters"""

    async def start_rotation_task() -> None:
        """Start background rotation and cleanup"""

    async def stop_rotation_task() -> None:
        """Stop background tasks"""

    async def get_storage_stats() -> Dict[str, Any]:
        """Get storage usage statistics"""
```

**Storage Configuration**:
```python
@dataclass
class StorageConfig:
    base_path: Path = Path.home() / '.browserPYMCP' / 'browser'
    max_file_size_mb: int = 50
    retention_days: int = 7
    rotation_check_interval: int = 300  # 5 minutes
```

#### MCPService
**File**: `src/services/mcp_service.py`
**Responsibility**: Claude Code tool integration

```python
class MCPService:
    # Available MCP tools
    async def _handle_navigate(arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle browser_navigate tool"""

    async def _handle_query_logs(arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle browser_query_logs tool"""

    async def _handle_screenshot(arguments: Dict[str, Any]) -> List[ImageContent]:
        """Handle browser_screenshot tool"""

    async def run_stdio() -> None:
        """Run MCP server with stdio transport for Claude Code"""
```

**Tool Registration Pattern**:
```python
@self.server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(name="browser_navigate", description="...", inputSchema={...}),
        Tool(name="browser_query_logs", description="...", inputSchema={...}),
        Tool(name="browser_screenshot", description="...", inputSchema={...})
    ]

@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "browser_navigate":
        return await self._handle_navigate(arguments)
    # ... other tools
```

#### ScreenshotService
**File**: `src/services/screenshot_service.py`
**Responsibility**: Playwright browser automation for screenshots

```python
class ScreenshotService:
    async def start() -> None:
        """Initialize Playwright and launch browser"""

    async def stop() -> None:
        """Close browser and cleanup resources"""

    async def capture_screenshot(
        port: int,
        url: Optional[str] = None,
        viewport_only: bool = True
    ) -> Optional[str]:
        """Capture screenshot as base64 string"""

    async def navigate_page(port: int, url: str) -> bool:
        """Navigate page to URL"""

    async def execute_script(port: int, script: str) -> Any:
        """Execute JavaScript in page"""

    def get_service_info() -> Dict[str, Any]:
        """Get service status information"""
```

**Page Management Pattern**:
```python
# One Playwright page per port
async def _get_or_create_page(self, port: int) -> Page:
    if port not in self._pages:
        context = await self._browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        self._pages[port] = await context.new_page()
    return self._pages[port]
```

## Data Models

### ConsoleMessage
**File**: `src/models/console_message.py`

```python
@dataclass
class ConsoleMessage:
    timestamp: datetime
    level: ConsoleLevel  # Enum: DEBUG, INFO, LOG, WARN, ERROR
    message: str
    port: int
    url: Optional[str] = None
    stack_trace: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    source_file: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_websocket_data(cls, data: Dict[str, Any], port: int) -> 'ConsoleMessage':
        """Create from WebSocket message"""

    def to_jsonl(self) -> str:
        """Serialize to JSONL for storage"""

    @classmethod
    def from_jsonl(cls, line: str) -> 'ConsoleMessage':
        """Deserialize from JSONL"""

    def matches_filter(self, level_filter: Optional[List[str]] = None) -> bool:
        """Check if message matches level filter"""
```

### BrowserState
**File**: `src/models/browser_state.py`
Manages connection state tracking with async-safe operations.

## Chrome Extension Development

### Content Script Pattern
**File**: `extension/content.js`

```javascript
// Console method override pattern
function overrideConsole() {
    const methods = ['log', 'warn', 'error', 'info', 'debug'];

    methods.forEach(method => {
        const original = console[method];
        console[method] = function(...args) {
            original.apply(console, args);
            captureConsoleMessage(method, args);
        };
    });
}

function captureConsoleMessage(level, args) {
    const message = {
        type: 'console',
        level: level,
        args: args.map(arg => String(arg)),
        timestamp: new Date().toISOString(),
        url: window.location.href,
        lineNumber: getLineNumber(),
        sourceFile: getSourceFile()
    };

    // Send to background script
    chrome.runtime.sendMessage(message);
}
```

### Background Script Pattern
**File**: `extension/background.js`

```javascript
// WebSocket connection with retry
class WebSocketManager {
    constructor() {
        this.ws = null;
        this.messageQueue = [];
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
    }

    async connect() {
        for (let port = 8875; port <= 8895; port++) {
            try {
                this.ws = new WebSocket(`ws://localhost:${port}`);
                await this.waitForConnection();
                this.onConnected(port);
                return;
            } catch (e) {
                continue; // Try next port
            }
        }
        this.scheduleReconnect();
    }

    send(message) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            this.messageQueue.push(message);
        }
    }
}
```

### Popup Interface
**File**: `extension/popup.html` + `extension/popup.js`

Visual status indicator showing:
- Connection status (connected/disconnected)
- Active port number
- Message count
- Recent console activity

## Development Workflows

### Adding New Services

1. **Create Service Class**:
```python
# src/services/new_service.py
class NewService:
    def __init__(self, dependency_service=None):
        self.dependency = dependency_service

    async def some_method(self) -> str:
        return "result"
```

2. **Register in Container**:
```python
# In cli/main.py _setup_services()
async def create_new_service(container):
    dependency = await container.get('dependency_service')
    return NewService(dependency_service=dependency)

self.container.register('new_service', create_new_service)
```

3. **Add Lifecycle Management**:
```python
# In start() and stop() methods
new_service = await self.container.get('new_service')
await new_service.start()  # if applicable
```

### Adding MCP Tools

1. **Add Tool Definition**:
```python
# In MCPService._setup_tools()
Tool(
    name="new_tool",
    description="Tool description",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter"}
        },
        "required": ["param"]
    }
)
```

2. **Implement Handler**:
```python
async def _handle_new_tool(self, arguments: Dict[str, Any]) -> List[TextContent]:
    param = arguments.get("param")
    result = await self.some_service.do_something(param)
    return [TextContent(type="text", text=result)]
```

3. **Add to Call Router**:
```python
# In handle_call_tool()
elif name == "new_tool":
    return await self._handle_new_tool(arguments)
```

### Testing Patterns

#### Unit Testing Services
```python
@pytest.mark.asyncio
async def test_service_method():
    # Mock dependencies
    mock_dependency = AsyncMock()
    service = NewService(dependency_service=mock_dependency)

    # Test method
    result = await service.some_method()
    assert result == "expected"

    # Verify interactions
    mock_dependency.some_call.assert_called_once()
```

#### Integration Testing
```python
@pytest.mark.asyncio
async def test_service_integration():
    container = ServiceContainer()

    # Setup test dependencies
    temp_dir = tempfile.mkdtemp()
    container.register_instance('config', TestConfig(temp_dir))

    # Test service interactions
    service = await container.get('test_service')
    result = await service.integrated_operation()

    assert result.success
```

### Chrome Extension Testing

1. **Load Extension in Developer Mode**:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" → Select `extension/` folder

2. **Debug Console Capture**:
   - Open browser DevTools (F12)
   - Check console for extension messages
   - Look for "[mcp-browser] Console capture initialized"

3. **Test WebSocket Connection**:
   - Open extension popup
   - Verify connection status and port
   - Check background script for connection errors

## Performance Considerations

### Memory Management
- **Message Buffers**: Bounded to 1000 messages per port
- **File Handles**: Async context managers ensure proper closing
- **WebSocket Connections**: Cleaned up on disconnect
- **Playwright Pages**: Closed when ports become inactive

### I/O Optimization
- **Batch Writes**: Multiple messages written in single operation
- **Async File Operations**: Non-blocking with `aiofiles`
- **Background Tasks**: Rotation and cleanup don't block main operations
- **Concurrent Operations**: `asyncio.gather()` for parallel execution

### Storage Efficiency
- **JSONL Format**: Streaming reads without loading entire file
- **Automatic Rotation**: Prevents large file performance issues
- **Retention Policy**: Automatic cleanup prevents disk filling
- **Per-Port Locking**: Minimizes lock contention

## Debugging and Troubleshooting

### Service Debugging
```python
# Enable debug logging
logging.getLogger().setLevel(logging.DEBUG)

# Check service container status
container = ServiceContainer()
print("Registered services:", container.get_all_service_names())

# Verify service dependencies
service = await container.get('browser_service')
print("Service dependencies resolved:", hasattr(service, 'storage_service'))
```

### WebSocket Debugging
```bash
# Check if server is running
make status

# Test WebSocket connection manually
python -c "import asyncio, websockets; asyncio.run(websockets.connect('ws://localhost:8875'))"

# Monitor WebSocket traffic
# Use browser DevTools → Network → WS filter
```

### Extension Debugging
```javascript
// In extension background script
console.log('WebSocket state:', ws.readyState);
console.log('Message queue length:', messageQueue.length);
console.log('Last error:', lastError);

// In content script
console.log('[mcp-browser] Console capture active');
console.log('[mcp-browser] Messages captured:', messageCount);
```

## Configuration

### Environment Variables
```bash
# Port range configuration
export BROWSERPYMCP_PORT_START=8875
export BROWSERPYMCP_PORT_END=8895

# Logging level
export BROWSERPYMCP_LOG_LEVEL=INFO

# Storage path override
export BROWSERPYMCP_STORAGE_PATH=/custom/path/browser
```

### Claude Code Configuration
```bash
# Start the MCP server for Claude Code
browserpymcp mcp

# The server will automatically be discovered
# by Claude Code in this environment
```

## Security Considerations

### WebSocket Security
- **Localhost Only**: Server binds to localhost (127.0.0.1)
- **No Authentication**: Relies on localhost access control
- **CORS**: Extensions can only connect from same origin
- **No Sensitive Data**: Console logs may contain sensitive information

### File System Security
- **User Directory**: Stores files in user's home directory
- **File Permissions**: Uses default system permissions
- **Path Traversal**: All paths are within base directory
- **Log Rotation**: Prevents disk space exhaustion

### Extension Security
- **Manifest V3**: Uses latest Chrome extension security model
- **Content Script Isolation**: Limited access to page context
- **Host Permissions**: Only localhost WebSocket connections
- **No External Requests**: All communication through WebSocket

---

See [CLAUDE.md](CLAUDE.md) for AI agent instructions and [CODE_STRUCTURE.md](CODE_STRUCTURE.md) for architecture analysis.