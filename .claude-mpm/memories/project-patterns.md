# MCP Browser Project Patterns

**Updated**: 2025-09-14
**Architecture**: Service-Oriented Architecture (SOA) with Dependency Injection

## Core Architectural Decisions

### Dependency Injection Container Pattern
- **Parameter Name Matching**: Services resolved by constructor parameter names
- **Async-Safe Singletons**: Uses asyncio.Lock for thread-safe singleton creation
- **Factory Functions**: Both sync and async factory functions supported
- **Circular Dependency Prevention**: Container enforces dependency graph

### Service Lifecycle Management
- **Service Registration**: `container.register(name, factory, singleton=True)`
- **Dependency Resolution**: `await container.get('service_name')`
- **Graceful Shutdown**: Services have start/stop lifecycle methods
- **Error Isolation**: Service failures don't cascade

## Critical Patterns

### WebSocket Port Auto-Discovery
```python
# Port range 8875-8895 to avoid conflicts
for port in range(8875, 8895):
    try:
        server = await websockets.serve(handler, host, port)
        break
    except OSError:
        continue  # Try next port
```

### Message Buffering Strategy
```python
# Prevent blocking I/O with periodic flush
self._message_buffer[port] = deque(maxlen=1000)
self._buffer_interval = 2.5  # seconds
asyncio.create_task(self._flush_buffer_periodically(port))
```

### File Rotation with Locks
```python
# Per-port file locking for thread safety
async with self._get_file_lock(port):
    if await self._should_rotate(file_path):
        await self._rotate_log_file(port)
    async with aiofiles.open(file_path, 'a') as f:
        await f.write(message.to_jsonl() + '\n')
```

## Service Interface Patterns

### BrowserService Interface
- `handle_console_message(data)`: Process incoming console logs
- `navigate_browser(port, url)`: Send navigation commands
- `query_logs(port, last_n, level_filter)`: Query stored messages
- `get_browser_stats()`: Connection and buffer statistics

### StorageService Interface
- `store_message(message)`: Store single console message
- `store_messages_batch(messages)`: Batch storage operation
- `query_messages(port, last_n, level_filter)`: Query with filters
- `start_rotation_task()`: Background file management

### WebSocketService Interface
- `start()`: Auto-discover port and start server
- `register_message_handler(type, handler)`: Event handling
- `register_connection_handler(event, handler)`: Connection lifecycle
- `broadcast_message(message)`: Send to all connections

## Data Model Patterns

### ConsoleMessage Serialization
```python
# WebSocket → ConsoleMessage
message = ConsoleMessage.from_websocket_data(data, port)

# ConsoleMessage → JSONL storage
jsonl_line = message.to_jsonl()

# JSONL → ConsoleMessage
message = ConsoleMessage.from_jsonl(line)
```

### Configuration Objects
```python
@dataclass
class StorageConfig:
    base_path: Path = Path.home() / '.browserPYMCP' / 'browser'
    max_file_size_mb: int = 50
    retention_days: int = 7
```

## Chrome Extension Patterns

### Console Capture Injection
```javascript
// Override console methods to capture messages
const original = console[method];
console[method] = function(...args) {
    original.apply(console, args);
    captureMessage(method, args);
};
```

### WebSocket Connection Strategy
```javascript
// Try multiple ports with exponential backoff
function connectWithRetry() {
    for (let port = 8875; port <= 8895; port++) {
        try {
            ws = new WebSocket(`ws://localhost:${port}`);
            return; // Success
        } catch (e) {
            continue; // Try next port
        }
    }
    setTimeout(connectWithRetry, delay);
}
```

## Performance Optimizations

### Memory Management
- **Bounded Buffers**: `deque(maxlen=1000)` prevents memory leaks
- **File Rotation**: 50MB automatic rotation with timestamp archives
- **Page Lifecycle**: Playwright pages closed when ports disconnect
- **Connection Tracking**: WeakSet for automatic cleanup

### Async Concurrency
- **Parallel Operations**: `asyncio.gather()` for concurrent tasks
- **Non-blocking I/O**: `aiofiles` for file operations
- **Background Tasks**: Separate tasks for rotation and cleanup
- **Lock Granularity**: Per-port locks to avoid contention

## Error Handling Standards

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
    await ensure_cleanup()
```

## Development Standards

### Service Creation
1. Create class in `src/services/`
2. Register in `cli/main.py` with dependencies
3. Implement async methods with error handling
4. Add to lifecycle management in orchestrator

### Testing Patterns
- **Unit Tests**: Mock dependencies via container
- **Integration Tests**: Use temporary directories for storage
- **Async Testing**: `pytest-asyncio` for async test methods
- **Service Mocking**: `AsyncMock` for WebSocket connections

### Documentation Requirements
- **Service interfaces**: Document public methods and parameters
- **Dependency requirements**: List constructor dependencies
- **Error conditions**: Document exception types
- **Performance characteristics**: Memory and I/O patterns

## Memory Keys for Future Reference

### Critical Constraints
- Services must be under 500 lines
- All service methods must be async
- Port range is fixed at 8875-8895
- File rotation at 50MB with 7-day retention

### Service Dependencies
- BrowserService depends on StorageService
- MCPService depends on BrowserService + ScreenshotService
- WebSocketService has no dependencies
- All services use dependency injection via parameter names

### Extension Integration
- Content scripts capture console via method override
- Background script manages WebSocket with retry logic
- Message batching every 2-3 seconds to reduce load
- Visual status indicators in popup UI