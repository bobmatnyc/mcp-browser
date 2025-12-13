# Auto-Start Server Implementation

## Overview

All browser commands in `mcp-browser` now automatically start the server if it's not already running. This removes the manual step of running `mcp-browser start` before using browser control commands.

## Implementation Details

### Core Components

1. **Decorator**: `@requires_server` in `src/cli/commands/browser.py`
   - Wraps command functions to ensure server is running
   - Checks current server status via `get_server_status()`
   - Auto-starts server using `ensure_server_running()`
   - Displays user-friendly status messages
   - Handles startup failures gracefully

2. **Daemon Module**: `src/cli/utils/daemon.py`
   - `ensure_server_running()`: Idempotent server startup
   - `get_server_status()`: Check if server is running
   - `start_daemon()`: Background server process management
   - Service registry using PID file at `~/.mcp-browser/server.pid`

### Commands with Auto-Start

The following commands now auto-start the server:

#### Control Commands
- `mcp-browser browser control navigate <url>`
- `mcp-browser browser control click <selector>`
- `mcp-browser browser control fill <selector> <value>`
- `mcp-browser browser control scroll [--up|--down] [--amount N]`
- `mcp-browser browser control submit <selector>`

#### Extract Commands
- `mcp-browser browser extract content`
- `mcp-browser browser extract semantic`
- `mcp-browser browser extract selector <selector>`

#### Other Commands
- `mcp-browser browser logs`
- `mcp-browser browser screenshot`
- `mcp-browser browser test [--demo]`

### Commands WITHOUT Auto-Start

These commands do NOT auto-start (as specified in requirements):

- `mcp-browser start` / `mcp-browser serve` - They start the server themselves
- `mcp-browser stop` - Stops the server
- `mcp-browser init` - Configuration only
- `mcp-browser doctor` - Diagnostic only
- `mcp-browser setup` - Setup workflow
- `mcp-browser status` - Shows current status (mentions auto-start)

## User Experience

### First Command Run (Server Not Running)

```bash
$ mcp-browser browser control navigate https://example.com
⚡ Starting server... ✓ Started on port 8851
→ Navigating to https://example.com...
✓ Successfully navigated to: https://example.com
```

### Subsequent Commands (Server Already Running)

```bash
$ mcp-browser browser control click "#submit-btn"
→ Clicking element '#submit-btn'...
✓ Successfully clicked: #submit-btn
```

No auto-start message is shown since the server is already running.

### Auto-Start Failure

```bash
$ mcp-browser browser control navigate https://example.com
⚡ Starting server... ✗ Failed

╭─────────────────────────────────────╮
│         Auto-Start Failed           │
│─────────────────────────────────────│
│ ✗ Failed to start server            │
│   automatically                      │
│                                     │
│ Please try starting manually:       │
│   mcp-browser start                 │
│                                     │
│ Or check for errors:                │
│   mcp-browser doctor                │
╰─────────────────────────────────────╯
```

## Status Command Update

The `status` command now indicates that the server will auto-start:

```bash
$ mcp-browser status

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component     ┃ Status                      ┃
┣━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Package       ┃ ✓ Installed                 ┃
┃ Configuration ┃ ✓ Configured                ┃
┃ Extension     ┃ ✓ Initialized               ┃
┃ Server        ┃ ○ Not running               ┃
┃               ┃ (will auto-start on first   ┃
┃               ┃ command)                    ┃
┃ Data Directory┃ ✓ Created                   ┃
┃ Logs Directory┃ ✓ Created                   ┃
┗━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Help Text Updates

The browser command group help now reflects auto-start:

```bash
$ mcp-browser browser --help

🌐 Browser interaction and testing commands.

These commands provide direct browser control for testing and development.
The server will auto-start if not already running.

Prerequisites:
  • Install and connect Chrome extension (mcp-browser setup)
  • Navigate to a website in the browser
```

## Technical Implementation

### Decorator Pattern

```python
def requires_server(f: Callable) -> Callable:
    """Decorator that ensures server is running before command executes."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Check current status first
        is_running, _, existing_port = get_server_status()

        if not is_running:
            console.print("[cyan]⚡ Starting server...[/cyan]", end=" ")
            success, port = ensure_server_running()

            if not success:
                console.print("[red]✗ Failed[/red]")
                # Show error panel
                return

            console.print(f"[green]✓ Started on port {port}[/green]")

        # Server is now running, proceed with command
        return f(*args, **kwargs)

    return wrapper
```

### Usage Example

```python
@control.command(name="navigate")
@click.argument("url")
@click.option("--wait", default=0, type=float)
@click.option("--port", default=None, type=int)
@requires_server  # ← Decorator ensures server is running
def navigate_to_url(url: str, wait: float, port: int):
    """Navigate browser to a URL."""
    asyncio.run(_navigate_command(url, wait, port))
```

## Testing

Run the test script to verify auto-start functionality:

```bash
python test_auto_start.py
```

### Expected Output

```
Testing auto-start functionality...

1. Checking initial status:
   Server running: False
   PID: None
   Port: None

2. Testing ensure_server_running():
   Success: True
   Port: 8851

3. Checking status after ensure_server_running():
   Server running: True
   PID: 12345
   Port: 8851

4. Testing idempotence (calling again):
   Success: True
   Port: 8851
   Same as before: True

✓ Auto-start functionality test complete!

Server is running on port 8851
You can verify by running: mcp-browser status
```

## Benefits

1. **Simplified User Experience**: No need to manually start server
2. **Reduced Friction**: Faster time to first command execution
3. **Idempotent**: Safe to call multiple times (won't start duplicate servers)
4. **Transparent**: Clear messaging when auto-start occurs
5. **Graceful Failures**: Helpful error messages with next steps

## Implementation Notes

- Auto-start uses the existing `start_daemon()` function from `daemon.py`
- Server starts in background as detached process
- Port is auto-selected from available range (8851-8899)
- Service registry tracks PID and port in `~/.mcp-browser/server.pid`
- Commands remain responsive (minimal wait time for server startup)

## Files Modified

1. `src/cli/commands/browser.py`
   - Added `requires_server` decorator
   - Applied decorator to 11 commands
   - Updated help text

2. `src/cli/commands/status.py`
   - Updated server status message to mention auto-start

3. `test_auto_start.py` (new)
   - Test script for validation

4. `AUTO_START_IMPLEMENTATION.md` (new)
   - This documentation file
