# CODE_STRUCTURE.md - Architecture Analysis

**Generated**: 2025-09-14
**Architecture**: Service-Oriented Architecture (SOA) with Dependency Injection
**Framework**: Custom AsyncIO + MCP Python SDK + Chrome Extension

## Core Architecture Overview

### Dependency Injection Container
**Location**: `src/container/service_container.py`
```python
# Service registration pattern
container.register('service_name', factory_function, singleton=True)

# Dependency resolution via parameter name matching
async def create_browser_service(container):
    storage = await container.get('storage_service')  # Auto-injected
    return BrowserService(storage_service=storage)
```

**Key Features**:
- Async-safe singleton management with locks
- Constructor injection via parameter name matching
- Service lifecycle management
- Graceful error handling for missing dependencies

### Service Layer Architecture

#### 1. WebSocketService (`src/services/websocket_service.py`)
**Responsibility**: Browser connection management
```python
# Port auto-discovery pattern
for port in range(8875, 8895):
    try:
        server = await websockets.serve(handler, host, port)
        break  # Success
    except OSError:
        continue  # Try next port
```

**Core Patterns**:
- Port auto-discovery (8875-8895 range)
- Event-driven handler registration
- Connection lifecycle management
- Concurrent broadcast messaging

#### 2. BrowserService (`src/services/browser_service.py`)
**Responsibility**: Console message processing and browser control
```python
# Message buffering pattern to prevent blocking
self._message_buffer[port] = deque(maxlen=1000)
asyncio.create_task(self._flush_buffer_periodically(port))

# Navigation command pattern
await websocket.send(json.dumps({
    'type': 'navigate',
    'url': url,
    'timestamp': datetime.now().isoformat()
}))
```

**Key Patterns**:
- Message buffering with periodic 2.5s flush
- Port-based connection tracking
- Async navigation command dispatch
- Memory-bounded deque for message storage

#### 3. StorageService (`src/services/storage_service.py`)
**Responsibility**: JSONL persistence with rotation
```python
# File rotation pattern
async def _should_rotate(self, file_path: Path) -> bool:
    size_mb = file_path.stat().st_size / (1024 * 1024)
    return size_mb >= self.config.max_file_size_mb  # 50MB

# Async file operations with locks
async with self._get_file_lock(port):
    async with aiofiles.open(file_path, 'a') as f:
        await f.write(message.to_jsonl() + '\n')
```

**Critical Features**:
- Automatic 50MB file rotation
- 7-day retention with background cleanup
- Per-port file locking for thread safety
- JSONL format for streaming reads

#### 4. MCPService (`src/services/mcp_service.py`)
**Responsibility**: Claude Code integration
```python
# Tool registration pattern
@self.server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(name="browser_navigate", ...),
        Tool(name="browser_query_logs", ...),
        Tool(name="browser_screenshot", ...)
    ]

# Tool execution pattern
@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "browser_navigate":
        return await self._handle_navigate(arguments)
```

**Integration Points**:
- MCP Python SDK tool registration
- Async tool handler delegation
- Service dependency injection
- Structured response formatting

#### 5. ScreenshotService (`src/services/screenshot_service.py`)
**Responsibility**: Playwright browser automation
```python
# Page management pattern
async def _get_or_create_page(self, port: int) -> Page:
    if port not in self._pages:
        context = await self._browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        self._pages[port] = await context.new_page()
    return self._pages[port]
```

**Automation Patterns**:
- Per-port Playwright page management
- Headless Chromium with security flags
- Base64 screenshot encoding
- Async lifecycle management

## Data Models

### ConsoleMessage (`src/models/console_message.py`)
```python
@dataclass
class ConsoleMessage:
    timestamp: datetime
    level: ConsoleLevel  # Enum: DEBUG, INFO, LOG, WARN, ERROR
    message: str
    port: int
    url: Optional[str] = None
    stack_trace: Optional[str] = None
```

**Serialization Patterns**:
- WebSocket → ConsoleMessage via `from_websocket_data()`
- ConsoleMessage → JSONL via `to_jsonl()`
- JSONL → ConsoleMessage via `from_jsonl()`
- Level filtering via `matches_filter()`

### BrowserState (`src/models/browser_state.py`)
Connection state tracking with async-safe operations.

## Chrome Extension Architecture

### Content Script Pattern
```javascript
// Console capture injection
const originalLog = console.log;
console.log = function(...args) {
    originalLog.apply(console, args);
    captureConsoleMessage('log', args);
};
```

### Background Script Pattern
```javascript
// WebSocket connection with retry
function connectWebSocket() {
    for (let port = 8875; port <= 8895; port++) {
        try {
            ws = new WebSocket(`ws://localhost:${port}`);
            // Connection success handling
        } catch (e) {
            // Try next port
        }
    }
}
```

## Service Orchestration

### Main Entry Point (`src/cli/main.py`)
```python
class BrowserMCPServer:
    def _setup_services(self):
        # Service registration with dependency chains
        self.container.register('storage_service', ...)
        self.container.register('websocket_service', ...)
        self.container.register('browser_service', create_browser_service)  # Depends on storage
        self.container.register('mcp_service', create_mcp_service)  # Depends on browser + screenshot
```

**Orchestration Patterns**:
- Dependency graph resolution
- Service lifecycle coordination
- Handler registration chains
- Graceful shutdown sequences

## Key Architectural Constraints

### Async-First Design
- **All service methods are async**: No blocking operations in service layer
- **Message buffering**: Prevents I/O blocking via periodic flush
- **Concurrent operations**: Uses `asyncio.gather()` for parallel execution
- **Lock management**: Per-port locks for file operations

### Service Boundaries
- **500-line service limit**: Enforces single responsibility
- **Constructor injection only**: Dependencies resolved at creation
- **No circular dependencies**: Container enforces dependency graph
- **Interface segregation**: Services expose minimal public APIs

### Memory Management
- **Bounded message buffers**: `deque(maxlen=1000)` prevents memory leaks
- **File rotation**: Automatic 50MB limit with timestamp-based archives
- **Connection tracking**: Weak references to prevent resource leaks
- **Page lifecycle**: Playwright pages cleaned up per port

## Error Handling Patterns

### Service-Level Isolation
```python
try:
    await service_operation()
except Exception as e:
    logger.error(f"Service error: {e}")
    # Service continues running
```

### Resource Cleanup
```python
try:
    await operation()
except asyncio.CancelledError:
    await cleanup()
    raise
finally:
    await final_cleanup()
```

## Performance Characteristics

### WebSocket Connections
- **Port range**: 8875-8895 (21 available ports)
- **Connection lifecycle**: Automatic reconnection from extension
- **Message batching**: Extension batches messages every 2-3 seconds
- **Concurrent clients**: Supports multiple browser tabs per port

### Storage Operations
- **Async I/O**: Non-blocking file operations via `aiofiles`
- **Batch writes**: Multiple messages written in single operation
- **Background rotation**: Separate task for cleanup operations
- **Query optimization**: JSONL allows streaming reads

### Screenshot Performance
- **Page reuse**: Playwright pages cached per port
- **Headless mode**: No GUI overhead
- **Concurrent captures**: Multiple screenshots can be taken simultaneously
- **Memory management**: Pages closed when ports disconnect

## Development Patterns

### Adding New Services
1. Create service class in `src/services/`
2. Register in `cli/main.py` with dependencies
3. Add to container lifecycle management
4. Implement async methods with proper error handling

### Extending MCP Tools
1. Add tool definition to `MCPService._setup_tools()`
2. Implement handler method with service delegation
3. Add validation and error responses
4. Test via Claude Code integration

### Chrome Extension Modifications
1. Update content script for new console capture patterns
2. Modify background script for additional WebSocket messages
3. Update popup for new status indicators
4. Test across different browser versions

---

**Memory Notes**:
- Service container resolves dependencies by parameter name matching
- Message buffering prevents blocking on storage I/O operations
- Port auto-discovery eliminates configuration requirements
- JSONL format enables efficient streaming and rotation