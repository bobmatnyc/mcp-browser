# CLAUDE.md - MCP Browser AI Agent Instructions

**Type**: Python MCP Server + Chrome Extension
**Architecture**: Service-Oriented Architecture (SOA) with Dependency Injection
**Focus**: Browser console log capture and control via Claude Code integration

## 🔴 CRITICAL: Core Architecture Requirements

### Temporary Files and Test Scripts
- **ALL temporary files MUST go in `tmp/` directory**
- **Test scripts**: `tmp/test_*.py` or `tmp/*_test.py`
- **Debug logs**: `tmp/debug_*.log`
- **Temporary documentation**: `tmp/docs/*.md`
- **Scratch files**: `tmp/scratch_*.py`
- **NEVER commit tmp/ directory contents to git**

### SOA Dependency Injection Container
- **Location**: `src/container/service_container.py`
- **Pattern**: Constructor injection via parameter name matching
- **Lifecycle**: Singletons by default, async-safe with locks
- **Usage**: `await container.get('service_name')` for dependency resolution

### Service Boundaries (500-line max per service)
1. **WebSocketService**: Browser connection management, port discovery (8875-8895)
2. **BrowserService**: Console message handling, navigation commands
3. **StorageService**: JSONL persistence with 50MB rotation, 7-day retention
4. **MCPService**: Claude Code tool exposure (navigate, query_logs, screenshot)
5. **ScreenshotService**: Playwright integration for browser captures

### Async Patterns
- **All services are async**: Use `async def` for service methods
- **Message buffering**: 2.5s periodic flush to prevent blocking
- **Connection handling**: Graceful cleanup with `finally` blocks
- **Error isolation**: Service failures don't cascade

### Key Constraints
- **No synchronous operations** in service layer
- **Service constructors**: Only store dependencies, no initialization
- **Port range**: Fixed 8875-8895 for auto-discovery
- **Log rotation**: Automatic at 50MB, files named `console_YYYYMMDD_HHMMSS.jsonl`

## 🟡 IMPORTANT: Service Responsibilities

### Service Container Registration Pattern
```python
# In cli/main.py _setup_services()
self.container.register('service_name', factory_function)

# Async factory with dependencies
async def create_browser_service(container):
    storage = await container.get('storage_service')
    return BrowserService(storage_service=storage)
```

### MCP Tool Integration
- **browser_navigate**: Send WebSocket navigation commands
- **browser_query_logs**: Retrieve buffered + stored console messages
- **browser_screenshot**: Playwright capture with optional URL navigation

### Chrome Extension Architecture
- **Content script**: Captures console messages from all tabs (background script filters to active only)
- **Background script**: Manages WebSocket connections, active tab filtering, and message buffering
- **Popup**: Shows connection status with three-color indicator (🔴🟡🟢) and active ports

## 🟢 STANDARD: Development Workflows

### Single Command Patterns
```bash
# ONE way to build
make build

# ONE way to test
make test

# ONE way to develop
make dev

# ONE way to lint/format
make lint-fix
```

### Service Development Pattern
1. **Create service class** in `src/services/`
2. **Add to container** in `cli/main.py`
3. **Inject dependencies** via constructor parameters
4. **Implement async methods** for all operations
5. **Add error handling** with proper logging

### Testing Framework
- **pytest-asyncio**: For async service testing
- **Mock dependencies**: Inject test doubles via container
- **Integration tests**: Test service interactions
- **Chrome extension tests**: Via WebSocket simulation

## ⚪ OPTIONAL: Project Enhancements

### Extension Development
- **Source of truth**: `src/extension/` (edit here only)
- **Deployed to**: `mcp-browser-extension/` (via `mcp-browser init --project`)
- Uses vanilla JavaScript (no frameworks)
- Manifest V3 structure with three-color status indicators (🔴🟡🟢)
- Active tab filtering prevents duplicate console messages

### Future Architecture
- Multi-browser support (Firefox, Safari)
- Plugin system for custom message processors
- Cloud storage integration for log persistence

## Essential File Structure
```
src/
├── cli/main.py                    # Entry point, service orchestration
├── container/service_container.py # DI container implementation
├── extension/                     # Chrome extension source (EDIT HERE)
│   ├── manifest.json              # Extension manifest
│   ├── background-enhanced.js     # Service worker with active tab filtering
│   ├── content.js                 # Console capture script
│   ├── popup.html                 # Extension popup UI
│   └── popup-enhanced.html        # Multi-server popup UI
├── services/                      # Service layer (SOA)
│   ├── browser_service.py         # Console handling, navigation
│   ├── websocket_service.py       # Connection management
│   ├── storage_service.py         # JSONL persistence
│   ├── mcp_service.py             # Claude Code integration
│   └── screenshot_service.py      # Playwright screenshots
└── models/                        # Data models
    ├── console_message.py         # Console log structure
    └── browser_state.py           # Connection state tracking

mcp-browser-extension/             # Deployed extension (auto-generated)
├── manifest.json                  # DO NOT EDIT - deployed from src/extension/
├── background-enhanced.js         # DO NOT EDIT - deployed from src/extension/
└── README.md                      # Installation instructions
```

## Memory Notes
- Service dependencies resolved by parameter name matching
- WebSocket port auto-discovery prevents conflicts
- Message buffering prevents blocking on storage I/O
- Chrome extension handles tab lifecycle automatically

---
📋 For detailed technical implementation: See [DEVELOPER.md](DEVELOPER.md)
🏗️ For project structure analysis: See [CODE_STRUCTURE.md](CODE_STRUCTURE.md)
🚀 For deployment procedures: See [README.md](README.md)