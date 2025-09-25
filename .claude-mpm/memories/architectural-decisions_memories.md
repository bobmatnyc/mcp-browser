# Architectural Decision Records (ADR)

**Project**: MCP Browser
**Updated**: 2025-09-14

## ADR-001: Service-Oriented Architecture with Dependency Injection

**Status**: Implemented
**Decision**: Use SOA with custom DI container for service management

**Context**:
- Need clean separation between WebSocket, storage, browser control, and MCP concerns
- Want testable, maintainable code with clear dependencies
- Async-first architecture for non-blocking operations

**Decision**:
- Custom `ServiceContainer` with constructor injection
- Parameter name matching for dependency resolution
- Async-safe singleton management with locks

**Consequences**:
- ✅ Clear service boundaries and testability
- ✅ Flexible dependency management
- ❌ Custom DI adds complexity vs. existing frameworks

## ADR-002: WebSocket Port Auto-Discovery (8875-8895)

**Status**: Implemented
**Decision**: Use port auto-discovery in range 8875-8895 for WebSocket server

**Context**:
- Multiple instances may run simultaneously
- Hard-coded ports create conflicts
- Chrome extension needs to find server

**Decision**:
- Try ports 8875-8895 sequentially
- Extension tries same range to connect
- First available port is used

**Consequences**:
- ✅ Zero configuration required
- ✅ Supports multiple instances
- ❌ Limited to 21 concurrent instances

## ADR-003: Message Buffering with Periodic Flush

**Status**: Implemented
**Decision**: Buffer console messages in memory with 2.5s periodic flush to storage

**Context**:
- High-frequency console messages could block I/O
- Need balance between performance and data safety
- Memory usage must be bounded

**Decision**:
- `deque(maxlen=1000)` per port for message buffering
- Background task flushes every 2.5 seconds
- Bounded memory with automatic overflow handling

**Consequences**:
- ✅ Non-blocking message handling
- ✅ Bounded memory usage
- ❌ Potential 2.5s data loss on crash

## ADR-004: JSONL Storage with 50MB Rotation

**Status**: Implemented
**Decision**: Use JSONL format with automatic 50MB file rotation

**Context**:
- Need streaming read/write capability
- Log files can grow very large
- Want human-readable format

**Decision**:
- One JSONL file per port in `~/.browserPYMCP/browser/{port}/`
- Automatic rotation at 50MB with timestamp archiving
- 7-day retention with background cleanup

**Consequences**:
- ✅ Streaming operations possible
- ✅ Human-readable format
- ✅ Automatic space management
- ❌ No compression (larger disk usage)

## ADR-005: Chrome Extension with Vanilla JavaScript

**Status**: Implemented
**Decision**: Use vanilla JavaScript (no frameworks) for Chrome extension

**Context**:
- Extension needs to be lightweight
- Framework overhead not justified for simple functionality
- Easier debugging and maintenance

**Decision**:
- Manifest V3 structure
- Vanilla JS for content/background scripts
- Direct WebSocket connection to server

**Consequences**:
- ✅ Lightweight and fast
- ✅ No build process required
- ✅ Easy debugging
- ❌ More manual DOM manipulation

## ADR-006: Playwright for Screenshot Service

**Status**: Implemented
**Decision**: Use Playwright Chromium for screenshot capture

**Context**:
- Need programmatic browser control
- Screenshots must match actual browser rendering
- Want reliable automation

**Decision**:
- Playwright with headless Chromium
- Per-port page management
- Base64 encoding for MCP integration

**Consequences**:
- ✅ Reliable screenshot capture
- ✅ Matches Chrome rendering
- ❌ Additional dependency (Chromium download)
- ❌ Memory usage for headless browser

## ADR-007: MCP Python SDK Integration

**Status**: Implemented
**Decision**: Use official MCP Python SDK for Claude Code integration

**Context**:
- Need Claude Code integration
- Want standard protocol compliance
- Official SDK provides proper types and patterns

**Decision**:
- MCP Python SDK with stdio transport
- Three tools: navigate, query_logs, screenshot
- Service delegation pattern for tool handlers

**Consequences**:
- ✅ Standard MCP compliance
- ✅ Type safety and validation
- ✅ Future protocol compatibility
- ❌ Additional dependency

## ADR-008: 500-Line Service Limit

**Status**: Implemented
**Decision**: Enforce 500-line maximum per service file

**Context**:
- Want maintainable, focused services
- Encourage single responsibility principle
- Make code review easier

**Decision**:
- Hard limit of 500 lines per service
- Split larger services into multiple focused services
- Document in development guidelines

**Consequences**:
- ✅ Forces good design practices
- ✅ Easier code review and testing
- ❌ May require service splitting

## ADR-009: Async-First Design

**Status**: Implemented
**Decision**: All service layer methods must be async

**Context**:
- WebSocket and file I/O are inherently async
- Want to avoid blocking operations
- Need consistent programming model

**Decision**:
- All service methods are `async def`
- Use `aiofiles` for file operations
- Background tasks for periodic operations

**Consequences**:
- ✅ Non-blocking operations
- ✅ Consistent async model
- ❌ All callers must handle async

## Future Decisions to Consider

### Multi-Browser Support
- **Context**: Currently Chrome-only via extension
- **Options**: Firefox WebExtensions, Safari support
- **Considerations**: Development effort vs. user demand

### Cloud Storage Integration
- **Context**: Currently local file storage only
- **Options**: S3, Google Cloud, Azure integration
- **Considerations**: Privacy, cost, complexity

### Real-time Dashboard
- **Context**: Currently CLI status only
- **Options**: Web dashboard, desktop app
- **Considerations**: Additional attack surface, maintenance

### Compression and Optimization
- **Context**: JSONL files can be large
- **Options**: Gzip compression, binary format
- **Considerations**: Human readability vs. space efficiency