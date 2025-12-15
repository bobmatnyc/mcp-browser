# CLAUDE.md - AI Agent Instructions for mcp-browser

**Project**: MCP Browser - Browser console log capture and control via MCP
**Location**: `/Users/masa/Projects/mcp-browser`
**Language**: Python 3.10+
**Architecture**: Service-Oriented Architecture (SOA) + Chrome Extension + MCP Server
**Last Updated**: 2025-12-15

---

## 🎯 Priority Index

### 🔴 CRITICAL Instructions
- [Architecture Constraints](#-critical-architecture-constraints)
- [Security & Safety Rules](#-critical-security-rules)
- [WebSocket Communication Protocol](#-critical-websocket-protocol)

### 🟡 IMPORTANT Instructions
- [Single-Path Workflows](#-important-single-path-workflows)
- [Service Layer Patterns](#-important-service-layer-patterns)
- [MCP Tools Implementation](#-important-mcp-tools)
- [Extension Development](#-important-extension-development)

### 🟢 STANDARD Instructions
- [Testing Requirements](#-standard-testing-requirements)
- [CLI Commands](#-standard-cli-commands)
- [Code Quality Standards](#-standard-code-quality)
- [Documentation Updates](#-standard-documentation)

### ⚪ OPTIONAL Instructions
- [Performance Optimization](#-optional-performance-optimization)
- [Advanced Features](#-optional-advanced-features)

---

## 🔴 CRITICAL: Architecture Constraints

### Service-Oriented Architecture (SOA)
**NEVER violate these architectural boundaries:**

```python
# ✅ CORRECT: Services communicate through dependency injection
class BrowserService:
    def __init__(self, storage_service=None):
        self.storage_service = storage_service  # Injected dependency

# ❌ WRONG: Direct service instantiation breaks DI
class BrowserService:
    def __init__(self):
        self.storage_service = StorageService()  # Don't do this!
```

**Service Layer Rules:**
1. **All service methods MUST be async** - No blocking operations
2. **500-line service limit** - Enforces single responsibility principle
3. **Constructor injection only** - Dependencies resolved at creation time
4. **No circular dependencies** - Container enforces dependency graph
5. **Interface segregation** - Services expose minimal public APIs

### Async-First Design
**CRITICAL**: This is an asyncio-based system. ALL I/O operations must be async:

```python
# ✅ CORRECT: Async file operations
async with aiofiles.open(file_path, 'a') as f:
    await f.write(data)

# ❌ WRONG: Blocking file operations
with open(file_path, 'a') as f:
    f.write(data)  # BLOCKS EVENT LOOP!
```

### WebSocket Architecture (NOT HTTP)
**CRITICAL CHANGE (December 2024)**: Dashboard HTTP server completely removed.

**Current Architecture:**
- **WebSocket Server** (port 8875-8895): Browser extension communication
- **MCP JSON-RPC** (stdio): Claude Code integration
- **No HTTP Server**: Removed entirely, do not re-add

```python
# ✅ CORRECT: WebSocket communication only
websocket_service.start()  # Port 8875-8895

# ❌ WRONG: HTTP server removed
# app.run()  # Don't add HTTP endpoints!
```

---

## 🔴 CRITICAL: Security Rules

### Extension Installation Security
**CRITICAL**: Extension installs to `~/.mcp-browser/extension/` NOT the source directory:

```bash
# ✅ CORRECT: Extension deployed to home directory
~/.mcp-browser/extension/

# ❌ WRONG: Never install from project directory
/Users/masa/Projects/mcp-browser/src/extensions/chrome/
```

**Rationale**: Prevents source code modifications from affecting running extensions.

### Secrets and Configuration
1. **NEVER commit** `.env.local` - Contains user-specific settings
2. **Use environment variables** for sensitive data
3. **NEVER log passwords or API keys**
4. **Sanitize console logs** before storage

### Port Security
- **Local-only binding**: WebSocket server binds to `localhost` only
- **No authentication required**: Trusted local-only connections
- **Port range**: 8875-8895 (auto-discovery prevents conflicts)

---

## 🔴 CRITICAL: WebSocket Protocol

### Message Format (Extension → Server)
```javascript
// Console message
{
    "type": "console",
    "level": "log|warn|error|info|debug",
    "message": "Console output",
    "timestamp": "2025-12-15T12:34:56.789Z",
    "url": "https://example.com",
    "stack_trace": "Error: ...\n  at ..."  // Optional
}

// Batch messages (extension sends every 2.5s)
{
    "type": "batch",
    "messages": [/* array of console messages */]
}
```

### Message Format (Server → Extension)
```javascript
// Navigation command
{
    "type": "navigate",
    "url": "https://example.com",
    "timestamp": "2025-12-15T12:34:56.789Z"
}

// DOM interaction commands
{
    "type": "dom_action",
    "action": "click|fill|submit|select",
    "selector": ".button-class",  // CSS selector
    "xpath": "//button[@id='submit']",  // Or XPath
    "value": "input value",  // For fill actions
    "timestamp": "2025-12-15T12:34:56.789Z"
}
```

### Connection Lifecycle
1. **Extension starts** → Tries ports 8875-8895
2. **Connection established** → Server tracks via `BrowserState`
3. **Extension sends messages** → Server buffers and stores
4. **Server sends commands** → Extension executes DOM/navigation
5. **Connection lost** → Server cleans up, extension retries

---

## 🟡 IMPORTANT: Single-Path Workflows

### ONE Way to Do ANYTHING
**Philosophy**: Exactly ONE command for each common task.

```bash
# Installation & Setup
make install              # ONE way to install dependencies
make dev                  # ONE way to start development environment
mcp-browser quickstart    # ONE way for first-time setup

# Development
make dev                  # Start full dev environment (server + extension)
make dev-server           # Start only MCP server
make dev-extension        # Load Chrome extension

# Testing
make test                 # ONE way to run all tests
make test-unit            # Run unit tests only
make test-integration     # Run integration tests only
make test-extension       # Test extension functionality

# Code Quality
make lint-fix             # ONE way to fix linting issues
make format               # ONE way to format code
make typecheck            # ONE way to check types
make quality              # ONE way to run all quality checks

# Release
make release-patch        # ONE way to release patch version (x.x.N+1)
make release-minor        # ONE way to release minor version (x.N+1.0)
make release-major        # ONE way to release major version (N+1.0.0)

# Extension Management
make ext-deploy           # ONE way to deploy extensions from source
make ext-build            # ONE way to build extension package
make ext-release          # ONE way to release extension

# Cleanup
make clean                # ONE way to clean build artifacts
make dev-clean            # ONE way to clean development artifacts
make ext-clean            # ONE way to clean extension packages
```

**NEVER** introduce alternative methods for these tasks without removing existing ones.

---

## 🟡 IMPORTANT: Service Layer Patterns

### Dependency Injection Container
**Location**: `src/container/service_container.py`

```python
# Service Registration Pattern
async def create_browser_service(container):
    storage = await container.get('storage_service')
    websocket = await container.get('websocket_service')
    return BrowserService(
        storage_service=storage,
        websocket_service=websocket
    )

container.register('browser_service', create_browser_service, singleton=True)
```

**Key Features:**
- Async-safe singleton management with locks
- Parameter name matching for dependency resolution
- Service lifecycle management
- Graceful error handling

### Core Services Overview

#### 1. WebSocketService
**File**: `src/services/websocket_service.py`
**Port**: Auto-discovers 8875-8895
**Responsibility**: Browser extension communication

```python
# Handler Registration Pattern
websocket.register_message_handler('console', browser.handle_console_message)
websocket.register_message_handler('batch', browser.handle_batch_messages)
websocket.register_connection_handler('connect', browser.handle_connect)
websocket.register_connection_handler('disconnect', browser.handle_disconnect)
```

#### 2. BrowserService
**File**: `src/services/browser_service.py`
**Responsibility**: Console message processing and browser control

```python
# Message Buffering Pattern (prevents blocking)
self._message_buffer[port] = deque(maxlen=1000)
asyncio.create_task(self._flush_buffer_periodically(port))  # 2.5s intervals
```

#### 3. StorageService
**File**: `src/services/storage_service.py`
**Format**: JSONL with automatic rotation
**Limits**: 50MB per file, 7-day retention

```python
# File Rotation Pattern
async def _should_rotate(self, file_path: Path) -> bool:
    size_mb = file_path.stat().st_size / (1024 * 1024)
    return size_mb >= 50  # 50MB limit
```

#### 4. MCPService
**File**: `src/services/mcp_service.py`
**Responsibility**: Claude Code integration via MCP protocol

```python
# Tool Registration Pattern
@self.server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [Tool(name="browser_navigate", ...), ...]

@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "browser_navigate":
        return await self._handle_navigate(arguments)
```

#### 5. ScreenshotService
**File**: `src/services/screenshot_service.py`
**Engine**: Playwright (Chromium headless)
**Output**: Base64-encoded PNG

#### 6. DOMInteractionService
**File**: `src/services/dom_interaction_service.py`
**Responsibility**: Browser DOM manipulation via WebSocket commands

---

## 🟡 IMPORTANT: MCP Tools

### 11 MCP Tools Available to Claude Code

#### Core Browser Control
1. **`browser_navigate(port, url)`** - Navigate to URL
2. **`browser_query_logs(port, last_n, level_filter)`** - Query console logs
3. **`browser_screenshot(port, url?)`** - Capture screenshot

#### DOM Interaction
4. **`browser_click(port, selector/xpath/text)`** - Click element
5. **`browser_fill_field(port, selector/xpath, value)`** - Fill form field
6. **`browser_fill_form(port, form_data, submit?)`** - Fill multiple fields
7. **`browser_submit_form(port, selector/xpath?)`** - Submit form
8. **`browser_get_element(port, selector/xpath/text)`** - Get element info
9. **`browser_wait_for_element(port, selector, timeout?)`** - Wait for element
10. **`browser_select_option(port, selector, value/text/index)`** - Select dropdown
11. **`browser_evaluate_js(port, code)`** - Execute JavaScript

### Adding New MCP Tools
**Pattern**:
```python
# 1. Define tool in MCPService._setup_tools()
Tool(
    name="browser_new_action",
    description="Description for Claude Code",
    inputSchema={
        "type": "object",
        "properties": {
            "port": {"type": "integer"},
            "param": {"type": "string"}
        },
        "required": ["port"]
    }
)

# 2. Implement handler method
async def _handle_new_action(self, arguments: dict) -> list[TextContent]:
    port = arguments.get("port")
    # Delegate to appropriate service
    result = await self.dom_service.perform_action(port, ...)
    return [TextContent(type="text", text=json.dumps(result))]

# 3. Add to call_tool handler
if name == "browser_new_action":
    return await self._handle_new_action(arguments)
```

---

## 🟡 IMPORTANT: Extension Development

### Three Extensions (Chrome, Firefox, Safari)
**Source**: `src/extensions/`
**Deployed**: `mcp-browser-extensions/`
**Installed**: `~/.mcp-browser/extension/`

### Chrome Extension Architecture
**Manifest V3**: Service worker + content scripts

```javascript
// Background Service Worker (src/extensions/chrome/background.js)
let ws = null;
const PORT_RANGE = { start: 8875, end: 8895 };

async function connectWebSocket() {
    for (let port = PORT_RANGE.start; port <= PORT_RANGE.end; port++) {
        try {
            ws = new WebSocket(`ws://localhost:${port}`);
            ws.onopen = () => updateIcon('connected');
            ws.onmessage = handleCommand;
            break;
        } catch (e) {
            continue;  // Try next port
        }
    }
}
```

### Console Capture Pattern
```javascript
// Content Script (injected into every page)
const originalConsole = { ...console };

['log', 'warn', 'error', 'info', 'debug'].forEach(level => {
    console[level] = function(...args) {
        originalConsole[level].apply(console, args);  // Still log to console
        captureMessage(level, args);  // Send to background
    };
});

function captureMessage(level, args) {
    chrome.runtime.sendMessage({
        type: 'console',
        level: level,
        message: args.map(arg => String(arg)).join(' '),
        timestamp: new Date().toISOString(),
        url: window.location.href
    });
}
```

### Extension Deployment Workflow
```bash
# 1. Edit source: src/extensions/chrome/*
# 2. Deploy to mcp-browser-extensions/: make ext-deploy
# 3. Extension auto-installs to ~/.mcp-browser/extension/
# 4. Reload extension in browser
```

### Safari Extension
**Platform**: macOS only
**Converter**: `safari-web-extension-converter`
**Output**: Native macOS app wrapper
**Guide**: `docs/SAFARI_EXTENSION.md`

```bash
# Create Safari extension
bash scripts/create-safari-extension.sh
```

---

## 🟢 STANDARD: Testing Requirements

### Test Structure
```
tests/
├── unit/                    # Service unit tests
│   ├── test_browser_service.py
│   ├── test_storage_service.py
│   └── test_websocket_service.py
├── integration/             # Integration tests
│   ├── test_mcp_tools.py
│   └── test_websocket_flow.py
└── extension/               # Extension tests
    └── test_console_capture.py
```

### Testing Commands
```bash
make test                    # Run all tests with coverage
make test-unit               # Unit tests only
make test-integration        # Integration tests only
make test-extension          # Extension functionality tests

# With coverage report
pytest --cov=src --cov-report=html
```

### Test Patterns
```python
# Async test pattern (pytest-asyncio)
@pytest.mark.asyncio
async def test_browser_service_message_handling():
    storage = MockStorageService()
    browser = BrowserService(storage_service=storage)

    await browser.handle_console_message({
        "type": "console",
        "level": "log",
        "message": "Test message"
    })

    assert len(storage.stored_messages) == 1

# Service mocking pattern
class MockStorageService:
    def __init__(self):
        self.stored_messages = []

    async def store_message(self, message):
        self.stored_messages.append(message)
```

---

## 🟢 STANDARD: CLI Commands

### Self-Documenting CLI
**Entry Point**: `src/cli/main.py`
**Framework**: Click
**Style**: Rich formatting with colors and emojis

```bash
# Interactive Setup
mcp-browser quickstart       # Complete interactive setup wizard
mcp-browser doctor           # Diagnose and fix issues
mcp-browser tutorial         # Step-by-step feature tour

# Server Management
mcp-browser start            # Start server (auto-discovers port)
mcp-browser stop             # Stop server (project-aware)
mcp-browser restart          # Stop + Start
mcp-browser status           # Show ports, PIDs, connections

# Installation
mcp-browser install          # Install MCP config for Claude Code
mcp-browser uninstall        # Remove MCP config
mcp-browser uninstall --clean-all  # Complete removal

# Monitoring
mcp-browser logs             # Show last 50 lines
mcp-browser logs 100         # Show last 100 lines
mcp-browser follow           # Real-time tail

# Extension
mcp-browser extension install    # Guide extension installation
mcp-browser extension status     # Check extension connection
mcp-browser extension reload     # Reload instructions

# MCP Mode
mcp-browser mcp              # Run in MCP stdio mode (for Claude Code)
mcp-browser test-mcp         # Test all MCP tools

# Utilities
mcp-browser version          # Show version info
mcp-browser config           # Show configuration
mcp-browser clean            # Clean old logs and data
```

### Adding New CLI Commands
**Pattern**:
```python
# src/cli/commands/new_command.py
import click
from rich.console import Console

console = Console()

@click.command()
@click.option('--param', help='Parameter description')
def new_command(param):
    """🎯 Command description for help text."""
    console.print(f"[blue]Executing command with {param}[/blue]")
    # Implementation

# Register in src/cli/main.py
from .commands.new_command import new_command
cli.add_command(new_command)
```

---

## 🟢 STANDARD: Code Quality

### Quality Tools
```bash
make quality                 # Run ALL quality checks
make lint-fix                # Auto-fix linting issues
make format                  # Format code with Black
make typecheck               # Type check with mypy
```

### Linting: Ruff
**Config**: `pyproject.toml`
```toml
[tool.ruff]
line-length = 88
target-version = "py310"
exclude = ["examples/", "tests/", "scripts/"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line length handled by Black
```

### Formatting: Black
**Config**: `pyproject.toml`
```toml
[tool.black]
line-length = 88
target-version = ['py310', 'py311', 'py312']
```

### Type Checking: mypy
**Config**: `pyproject.toml`
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
disallow_untyped_defs = true
check_untyped_defs = true
```

### Pre-commit Hooks
```bash
make pre-commit              # Install pre-commit hooks

# .pre-commit-config.yaml automatically runs:
# - Black (formatting)
# - Ruff (linting)
# - mypy (type checking)
```

---

## 🟢 STANDARD: Documentation

### Documentation Hierarchy
```
README.md                    # Project overview, quick start, features
CLAUDE.md                    # AI agent instructions (this file)
docs/
├── CODE_STRUCTURE.md        # Architecture deep dive
├── DEVELOPER.md             # Technical implementation guide
├── INSTALLATION.md          # Detailed installation guide
├── QUICKSTART.md            # Getting started guide
├── TROUBLESHOOTING.md       # Common issues and solutions
├── SAFARI_EXTENSION.md      # Safari extension setup
├── CDP_CONNECTION.md        # Chrome DevTools Protocol
└── guides/                  # Specific guides
```

### Documentation Update Rules
1. **README.md**: User-facing features and quick start
2. **CLAUDE.md**: AI agent instructions and patterns
3. **CODE_STRUCTURE.md**: Architecture changes
4. **DEVELOPER.md**: Implementation patterns
5. **CHANGELOG.md**: ALL user-visible changes

### Changelog Format
```markdown
## [2.2.25] - 2025-12-15

### Added
- New feature description

### Changed
- Changed behavior description

### Fixed
- Bug fix description

### Removed
- Removed feature description
```

---

## ⚪ OPTIONAL: Performance Optimization

### Message Buffering
**Current**: 2.5s flush interval, 1000 message buffer
```python
# Tune for performance vs. latency
self._message_buffer[port] = deque(maxlen=1000)  # Increase for high volume
self._flush_interval = 2.5  # Decrease for lower latency
```

### File Rotation
**Current**: 50MB per file, 7-day retention
```python
# Adjust in StorageService
self.config.max_file_size_mb = 50  # Increase for longer history
self.config.retention_days = 7     # Increase for audit requirements
```

### WebSocket Connections
**Current**: 8875-8895 (21 ports)
```python
# Expand port range if needed
PORT_START = 8875
PORT_END = 8895  # Increase for more concurrent projects
```

---

## ⚪ OPTIONAL: Advanced Features

### Chrome DevTools Protocol (CDP)
**Status**: Experimental fallback
**File**: `src/services/browser_controller.py`
**Use Case**: Direct browser control when extension unavailable

```bash
# Connect to existing Chrome browser
mcp-browser connect --port 9222
```

### AppleScript Fallback (macOS)
**Status**: Experimental
**File**: `src/services/applescript_service.py`
**Use Case**: Launch Chrome with extension when needed

### Custom Storage Backends
**Current**: JSONL files in `~/.mcp-browser/data/`
**Future**: SQLite, PostgreSQL, or cloud storage

---

## 📚 KuzuMemory Integration

This project uses KuzuMemory for intelligent context management.

### MCP Tools Available
When using Claude Desktop (not Claude Code), these tools are available:
- **`kuzu_enhance`**: Enhance prompts with project memories
- **`kuzu_learn`**: Store new learnings asynchronously
- **`kuzu_recall`**: Query specific memories
- **`kuzu_remember`**: Store important project information
- **`kuzu_stats`**: Get memory system statistics

### Memory Guidelines
- Store project decisions and architectural patterns
- Record technical specifications and API details
- Capture user preferences and workflow patterns
- Document error solutions and workarounds

**Note**: KuzuMemory is separate from mcp-browser functionality. It enhances AI interactions but is not required for core features.

---

## 🔍 Quick Reference

### Project Structure
```
mcp-browser/
├── src/
│   ├── cli/                 # CLI commands and utilities
│   ├── container/           # Dependency injection
│   ├── models/              # Data models (ConsoleMessage, BrowserState)
│   ├── services/            # Core services (WebSocket, Browser, Storage, MCP)
│   └── extensions/          # Browser extension source
├── mcp-browser-extensions/  # Deployed extensions
├── tests/                   # Unit, integration, extension tests
├── scripts/                 # Build and release scripts
├── docs/                    # Documentation
└── Makefile                 # Build system entry point
```

### Key Files
- **`Makefile`**: Main build system (loads modular makefiles)
- **`pyproject.toml`**: Python package configuration
- **`src/cli/main.py`**: CLI entry point and service orchestration
- **`src/services/mcp_service.py`**: MCP tool definitions
- **`src/extensions/chrome/manifest.json`**: Extension configuration

### Environment Files
- **`.env.local`**: User-specific settings (NOT committed)
- **`.env.local.template`**: Template for local settings
- **`.env.development`**: Development defaults

### Runtime Directories
```
~/.mcp-browser/
├── config/settings.json     # Auto-generated configuration
├── logs/mcp-browser.log     # Server logs
├── data/[port]/             # JSONL log storage
├── run/mcp-browser.pid      # Process tracking
└── extension/               # Installed extension
```

---

## 🎓 Learning Path for New Contributors

### Phase 1: Understand Architecture (1-2 hours)
1. Read `docs/CODE_STRUCTURE.md` - Architecture overview
2. Examine `src/container/service_container.py` - DI pattern
3. Review `src/services/websocket_service.py` - WebSocket pattern
4. Study `src/services/browser_service.py` - Message handling

### Phase 2: Run and Explore (30 minutes)
```bash
make install                 # Install dependencies
make dev                     # Start development environment
mcp-browser quickstart       # Interactive setup
mcp-browser tutorial         # Feature tour
```

### Phase 3: Make First Change (1-2 hours)
1. Pick an issue labeled `good-first-issue`
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes following patterns in existing code
4. Run quality checks: `make quality`
5. Test: `make test`
6. Submit PR

### Phase 4: Advanced Topics (ongoing)
- Chrome extension development
- MCP tool creation
- Service layer expansion
- Performance optimization

---

## 🚨 Common Pitfalls

### ❌ Don't Do This
```python
# Don't block the event loop
time.sleep(5)  # Use: await asyncio.sleep(5)

# Don't use direct service instantiation
service = BrowserService()  # Use: container.get('browser_service')

# Don't use synchronous I/O
with open(file) as f:  # Use: async with aiofiles.open(file) as f:

# Don't add HTTP endpoints
app.route('/api')  # Use: WebSocket communication only

# Don't skip tests
# Always run: make test
```

### ✅ Do This Instead
```python
# Async operations
await asyncio.sleep(5)

# Dependency injection
service = await container.get('browser_service')

# Async I/O
async with aiofiles.open(file, 'r') as f:
    data = await f.read()

# WebSocket communication
await websocket.send(json.dumps(message))

# Quality checks before commit
make quality && make test
```

---

## 📞 Getting Help

### Self-Help Resources
```bash
mcp-browser --help           # CLI help
mcp-browser doctor           # Diagnose issues
mcp-browser tutorial         # Interactive tutorial
make help                    # Build system help
```

### Documentation
1. **This file (CLAUDE.md)**: AI agent instructions
2. **`README.md`**: User guide and quick start
3. **`docs/DEVELOPER.md`**: Technical implementation
4. **`docs/CODE_STRUCTURE.md`**: Architecture details
5. **`docs/TROUBLESHOOTING.md`**: Common issues

### Community
- **GitHub Issues**: https://github.com/browserpymcp/mcp-browser/issues
- **Discussions**: GitHub Discussions tab
- **Pull Requests**: Contributions welcome!

---

**End of AI Agent Instructions**

This file is optimized for AI agents like Claude Code. For human developers, start with `README.md` and `docs/DEVELOPER.md`.

**Version**: 2.2.25
**Generated**: 2025-12-15
**Maintained**: Automatically via release process
