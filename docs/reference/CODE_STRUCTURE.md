# CODE_STRUCTURE.md - Architecture Overview

**Architecture**: Service-Oriented Architecture (SOA) with Dependency Injection
**Runtime**: asyncio + WebSocket daemon (browser) + MCP stdio server (assistant)

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
for port in range(self.start_port, self.end_port + 1):
    try:
        server = await websockets.serve(handler, host, port)
        break  # Success
    except OSError:
        continue  # Try next port
```

**Core Patterns**:
- Port auto-discovery (default 8851-8899 range, configurable)
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
- Request/response correlation for DOM + screenshot operations

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
**Responsibility**: MCP (stdio) integration for AI coding assistants
```python
# Tool registration pattern
@self.server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [Tool(name="browser_action", ...), Tool(name="browser_query", ...), ...]

# Tool execution pattern
@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "browser_action":
        return await self._handle_browser_action(arguments)
```

**Integration Points**:
- MCP Python SDK tool registration
- Async tool handler delegation
- Service dependency injection
- Structured response formatting

#### 5. BrowserController (`src/services/browser_controller.py`)
**Responsibility**: Unified browser control with extension/daemon/AppleScript fallbacks

**Key Patterns**:
- Extension-first control (via WebSocket daemon when available)
- Optional AppleScript fallback on macOS (reduced feature set)
- Capability detection to guide tool behavior

#### 6. DOMInteractionService (`src/services/dom_interaction_service.py`)
**Responsibility**: DOM manipulation and semantic extraction via extension protocol

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
    for (let port = 8851; port <= 8899; port++) {
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

### Main Entry Points

- CLI: `src/cli/main.py` (Click commands)
- Server orchestrator: `src/cli/utils/server.py` (`BrowserMCPServer`)

### Orchestration (`BrowserMCPServer`)
```python
class BrowserMCPServer:
    def _setup_services(self):
        # Service registration with dependency chains
        self.container.register('storage_service', ...)
        self.container.register('websocket_service', ...)
        self.container.register('browser_service', create_browser_service)  # Depends on storage
        self.container.register('mcp_service', create_mcp_service)  # Depends on browser + DOM + controller
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
- **Request tracking**: Timeouts + cleanup for screenshot/DOM requests

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
- **Port range**: 8851-8899 by default (49 available ports; configurable)
- **Connection lifecycle**: Automatic reconnection from extension
- **Message batching**: Extension batches messages every 2-3 seconds
- **Concurrent clients**: Supports multiple browser tabs per port

### Storage Operations
- **Async I/O**: Non-blocking file operations via `aiofiles`
- **Batch writes**: Multiple messages written in single operation
- **Background rotation**: Separate task for cleanup operations
- **Query optimization**: JSONL allows streaming reads

### Screenshot Performance
- **Mechanism**: Extension-backed screenshot capture (no Playwright service)
- **Latency**: Depends on browser and page complexity
- **Concurrency**: Requests are correlated and time out if no response

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
4. Update `docs/reference/MCP_TOOLS.md`
5. Test via Claude Code integration

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
