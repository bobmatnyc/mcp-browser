"""Doctor command implementation with comprehensive functional tests."""

import asyncio
import json
import time
from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table

from ..utils import (
    CONFIG_FILE,
    DATA_DIR,
    check_system_requirements,
    console,
)
from ..utils.daemon import (
    PORT_RANGE_END,
    PORT_RANGE_START,
    get_config_dir,
    get_server_status,
    is_port_available,
)


def create_default_config():
    """Create default configuration file."""
    default_config = {
        "storage": {
            "base_path": str(DATA_DIR),
            "max_file_size_mb": 50,
            "retention_days": 7,
        },
        "websocket": {"port_range": [8875, 8895], "host": "localhost"},
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f, indent=2)


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to fix issues automatically")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed diagnostic information"
)
@click.option(
    "--no-start", is_flag=True, help="Don't auto-start server (default: auto-start)"
)
@click.pass_context
def doctor(ctx, fix, verbose, no_start):
    """🩺 Diagnose and fix common MCP Browser issues.

    \b
    Performs comprehensive system checks:
      • Configuration files and directories
      • Python dependencies
      • MCP installer availability
      • Server status and ports (auto-starts if needed)
      • Extension package
      • Claude MCP integration
      • WebSocket connectivity
      • Browser extension connection

    \b
    Examples:
      mcp-browser doctor           # Run diagnostic (auto-starts server)
      mcp-browser doctor --no-start # Skip auto-start
      mcp-browser doctor --fix     # Auto-fix issues
      mcp-browser doctor -v        # Verbose output

    \b
    Common issues and solutions:
      • "Port in use" - Another process using ports 8851-8899
      • "Extension not found" - Run 'mcp-browser setup'
      • "Chrome not detected" - Install Chrome or Chromium
      • "Permission denied" - Check directory permissions
    """
    # Auto-start is default (unless --no-start is passed)
    start = not no_start
    asyncio.run(_doctor_command(fix, verbose, start))


async def _doctor_command(fix: bool, verbose: bool, start: bool = True):
    """Execute doctor diagnostic checks."""
    console.print(
        Panel.fit(
            "[bold blue]🩺 MCP Browser Doctor[/bold blue]\n"
            "Running comprehensive diagnostic checks...",
            border_style="blue",
        )
    )

    results = []

    # Test 1: Configuration
    console.print("[cyan]→ Checking configuration...[/cyan]")
    results.append(_check_configuration())

    # Test 2: Python Dependencies
    console.print("[cyan]→ Checking Python dependencies...[/cyan]")
    results.append(_check_dependencies())

    # Test 3: py-mcp-installer
    console.print("[cyan]→ Checking MCP installer...[/cyan]")
    results.append(_check_mcp_installer())

    # Test 4: Server Status (with optional auto-start)
    console.print("[cyan]→ Checking server status...[/cyan]")
    server_result = _check_server_status()

    # Auto-start server if requested and not running
    if start and server_result["status"] != "pass":
        console.print("[cyan]→ Starting server...[/cyan]")
        server_result = await _start_server_for_doctor()

    results.append(server_result)

    # Test 5: Port Availability
    console.print("[cyan]→ Checking port availability...[/cyan]")
    results.append(_check_port_availability())

    # Test 6: Extension Package
    console.print("[cyan]→ Checking extension package...[/cyan]")
    results.append(_check_extension_package())

    # Test 7: MCP Configuration
    console.print("[cyan]→ Checking MCP configuration...[/cyan]")
    results.append(_check_mcp_config())

    # Test 8: WebSocket Connectivity (if server running)
    console.print("[cyan]→ Checking WebSocket connectivity...[/cyan]")
    ws_result = await _check_websocket_connectivity()
    results.append(ws_result)

    # Test 9: Browser Extension Connection (if server running)
    console.print("[cyan]→ Checking browser extension connection...[/cyan]")
    ext_result = await _check_browser_extension_connection()
    results.append(ext_result)

    # Test 10: Console Log Capture (if extension connected)
    if ext_result.get("status") == "pass":
        console.print("[cyan]→ Testing console log capture...[/cyan]")
        results.append(await _check_console_log_capture())

        # Test 11: Browser Control (if extension connected)
        console.print("[cyan]→ Testing browser control...[/cyan]")
        results.append(await _check_browser_control())

    # Test 12: System Requirements (if verbose)
    if verbose:
        console.print("[cyan]→ Checking system requirements...[/cyan]")
        results.append(await _check_system_requirements())

    # Display results
    _display_results(results, verbose)

    # Summary
    passed = sum(1 for r in results if r["status"] == "pass")
    warnings = sum(1 for r in results if r["status"] == "warning")
    failed = sum(1 for r in results if r["status"] == "fail")

    console.print(
        f"\n[bold]Summary:[/bold] {passed} passed, {warnings} warnings, {failed} failed"
    )

    # Auto-fix if requested
    if fix and failed > 0:
        console.print("\n[bold]Attempting to fix issues...[/bold]")
        _auto_fix_issues(results)

    # Final message
    if failed > 0:
        console.print("[yellow]Run 'mcp-browser setup' to fix issues[/yellow]")
        if not fix:
            console.print("[dim]Or run 'mcp-browser doctor --fix' to auto-fix[/dim]")
    elif warnings > 0:
        console.print(
            "[yellow]Some warnings present - system should still work[/yellow]"
        )
    else:
        console.print("[green]✓ All checks passed! System is healthy.[/green]")


def _check_configuration() -> dict:
    """Check if configuration exists and is valid."""
    config_dir = get_config_dir()
    config_file = config_dir / "config.json"

    if not config_dir.exists():
        return {
            "name": "Configuration Directory",
            "status": "fail",
            "message": "~/.mcp-browser/ not found",
            "fix": "Run: mcp-browser setup",
            "fix_func": lambda: config_dir.mkdir(parents=True, exist_ok=True),
        }

    if not config_file.exists():
        return {
            "name": "Configuration File",
            "status": "warning",
            "message": "config.json not found (using defaults)",
            "fix": "Run: mcp-browser setup",
            "fix_func": create_default_config,
        }

    try:
        with open(config_file) as f:
            json.load(f)
        return {
            "name": "Configuration",
            "status": "pass",
            "message": f"Valid config at {config_file}",
        }
    except Exception as e:
        return {
            "name": "Configuration",
            "status": "fail",
            "message": f"Invalid config: {e}",
            "fix": "Run: mcp-browser setup",
            "fix_func": create_default_config,
        }


def _check_dependencies() -> dict:
    """Check Python dependencies are installed."""
    required = ["websockets", "click", "rich", "aiohttp", "mcp"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        return {
            "name": "Python Dependencies",
            "status": "fail",
            "message": f"Missing: {', '.join(missing)}",
            "fix": f"Run: pip install {' '.join(missing)}",
        }

    return {
        "name": "Python Dependencies",
        "status": "pass",
        "message": f"All {len(required)} required packages installed",
    }


def _check_mcp_installer() -> dict:
    """Check if py-mcp-installer is available."""
    import importlib.util

    if importlib.util.find_spec("py_mcp_installer") is not None:
        return {
            "name": "MCP Installer",
            "status": "pass",
            "message": "py-mcp-installer is available",
        }
    else:
        return {
            "name": "MCP Installer",
            "status": "warning",
            "message": "py-mcp-installer not installed",
            "fix": "Run: pip install py-mcp-installer",
        }


def _check_server_status() -> dict:
    """Check if server is running."""
    is_running, pid, port = get_server_status()

    if is_running:
        return {
            "name": "Server Status",
            "status": "pass",
            "message": f"Running on port {port} (PID: {pid})",
        }

    return {
        "name": "Server Status",
        "status": "warning",
        "message": "Not running (will auto-start on first command)",
        "fix": "Run: mcp-browser start",
    }


def _check_port_availability() -> dict:
    """Check if ports are available in range."""
    available = 0
    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        if is_port_available(port):
            available += 1

    total = PORT_RANGE_END - PORT_RANGE_START + 1

    if available == 0:
        return {
            "name": "Port Availability",
            "status": "fail",
            "message": f"No ports available in {PORT_RANGE_START}-{PORT_RANGE_END}",
            "fix": "Close applications using these ports",
        }

    return {
        "name": "Port Availability",
        "status": "pass",
        "message": f"{available}/{total} ports available ({PORT_RANGE_START}-{PORT_RANGE_END})",
    }


def _check_extension_package() -> dict:
    """Check extension availability.

    Checks for extensions in the local project directories.
    """
    # Check if we're inside the mcp-browser project (has extension source)
    project_root = Path(__file__).parent.parent.parent.parent
    possible_dirs = [
        # Primary: mcp-browser-extensions/chrome/ (deployed via make ext-deploy)
        Path.cwd() / "mcp-browser-extensions" / "chrome",
        project_root / "mcp-browser-extensions" / "chrome",
        # Alternative: src/extensions/chrome (source)
        Path.cwd() / "src" / "extensions" / "chrome",
        project_root / "src" / "extensions" / "chrome",
    ]

    for ext_dir in possible_dirs:
        manifest = ext_dir / "manifest.json"
        if manifest.exists():
            # Count files in extension
            file_count = len(list(ext_dir.rglob("*")))
            try:
                rel_path = ext_dir.relative_to(Path.cwd())
            except ValueError:
                rel_path = ext_dir
            return {
                "name": "Extension Source",
                "status": "pass",
                "message": f"Found at {rel_path} ({file_count} files)",
            }

    # Not in mcp-browser project - this is expected for users
    return {
        "name": "Extension Source",
        "status": "pass",
        "message": "Load from: https://github.com/bobmatnyc/mcp-browser",
    }


def _check_mcp_config() -> dict:
    """Check if MCP is configured for Claude Code."""
    # Claude Code stores config in ~/.claude.json
    claude_code_config = Path.home() / ".claude.json"

    if claude_code_config.exists():
        try:
            with open(claude_code_config) as f:
                config = json.load(f)
            if "mcpServers" in config and "mcp-browser" in config.get("mcpServers", {}):
                return {
                    "name": "MCP Configuration",
                    "status": "pass",
                    "message": "MCP configured for Claude Code",
                }
        except Exception:
            pass

    return {
        "name": "MCP Configuration",
        "status": "warning",
        "message": "MCP not configured for Claude Code",
        "fix": "Run: mcp-browser setup",
    }


async def _check_websocket_connectivity() -> dict:
    """Check WebSocket connectivity if server running."""
    is_running, _, port = get_server_status()

    if not is_running:
        return {
            "name": "WebSocket Connectivity",
            "status": "warning",
            "message": "Server not running, skipping connectivity test",
        }

    try:
        import websockets

        async def test_connection():
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, open_timeout=2.0) as _:
                return True

        await test_connection()

        return {
            "name": "WebSocket Connectivity",
            "status": "pass",
            "message": f"Successfully connected to ws://localhost:{port}",
        }
    except Exception as e:
        return {
            "name": "WebSocket Connectivity",
            "status": "fail",
            "message": f"Connection failed: {e}",
            "fix": "Restart server: kill existing process and run 'mcp-browser start'",
        }


async def _check_system_requirements() -> dict:
    """Check system requirements (verbose mode)."""
    checks = await check_system_requirements()

    issues = []
    for name, ok, details in checks:
        if not ok and "optional" not in name.lower():
            issues.append(f"{name}: {details}")

    if issues:
        return {
            "name": "System Requirements",
            "status": "warning",
            "message": "\n".join(issues),
            "fix": "Install missing requirements",
        }

    return {
        "name": "System Requirements",
        "status": "pass",
        "message": "All system requirements met",
    }


async def _start_server_for_doctor() -> dict:
    """Start the server for doctor testing."""
    import subprocess
    import sys

    try:
        # Start server in background
        subprocess.Popen(
            [sys.executable, "-m", "mcp_browser.cli.main", "start"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait a moment for server to start
        await asyncio.sleep(2)

        # Check if it started
        is_running, pid, port = get_server_status()

        if is_running:
            return {
                "name": "Server Status",
                "status": "pass",
                "message": f"Started on port {port} (PID: {pid})",
            }
        else:
            return {
                "name": "Server Status",
                "status": "fail",
                "message": "Failed to start server",
                "fix": "Run: mcp-browser start --verbose",
            }
    except Exception as e:
        return {
            "name": "Server Status",
            "status": "fail",
            "message": f"Failed to start: {e}",
            "fix": "Run: mcp-browser start",
        }


async def _check_browser_extension_connection() -> dict:
    """Check if browser extension is connected to the server."""
    is_running, pid, port = get_server_status()

    if not is_running or port is None:
        return {
            "name": "Browser Extension",
            "status": "warning",
            "message": "Server not running, cannot check extension",
        }

    try:
        import subprocess

        # Check for ESTABLISHED connections to the WebSocket port
        result = subprocess.run(
            ["lsof", "-i", f":{port}"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Count ESTABLISHED connections (excluding the LISTEN entry which is the server itself)
        lines = result.stdout.strip().split("\n")
        established_connections = [line for line in lines if "ESTABLISHED" in line]

        if established_connections:
            return {
                "name": "Browser Extension",
                "status": "pass",
                "message": f"Extension connected on port {port} ({len(established_connections)} active connection(s))",
            }
        else:
            return {
                "name": "Browser Extension",
                "status": "warning",
                "message": f"No extension connection detected on port {port}",
                "fix": "Open extension popup and click 'Connect' on a backend",
            }
    except subprocess.TimeoutExpired:
        return {
            "name": "Browser Extension",
            "status": "warning",
            "message": "Connection check timed out",
        }
    except Exception as e:
        return {
            "name": "Browser Extension",
            "status": "warning",
            "message": f"Could not verify extension: {e}",
            "fix": "Ensure extension is loaded and connected",
        }


async def _check_console_log_capture() -> dict:
    """Test console log capture functionality."""
    is_running, _, port = get_server_status()

    if not is_running:
        return {
            "name": "Console Log Capture",
            "status": "warning",
            "message": "Server not running",
        }

    try:
        import websockets

        async def test_logs():
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, open_timeout=3.0) as ws:
                # Request console logs
                await ws.send(
                    json.dumps(
                        {
                            "type": "get_logs",
                            "requestId": f"doctor_logs_{int(time.time() * 1000)}",
                            "lastN": 10,
                        }
                    )
                )

                try:
                    # Server sends connection_ack first, then our response
                    for _ in range(3):  # Try up to 3 messages
                        response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        data = json.loads(response)

                        # Skip connection_ack and other handshake messages
                        if data.get("type") in (
                            "connection_ack",
                            "server_info_response",
                        ):
                            continue

                        if data.get("type") == "logs":
                            logs = data.get("logs", [])
                            return logs, None
                        elif data.get("type") == "error":
                            return [], data.get("message", "Unknown error")

                    return [], "No logs response received"
                except asyncio.TimeoutError:
                    return [], "Timeout waiting for response"

            return [], "Connection closed"

        logs, error = await test_logs()

        if error:
            return {
                "name": "Console Log Capture",
                "status": "warning",
                "message": f"Log capture not working: {error}",
                "fix": "Ensure tab is connected via extension",
            }

        log_count = len(logs)
        message = f"Working ({log_count} recent logs)"

        # Show sample of recent logs if available
        if logs:
            # Get log levels breakdown
            levels = {}
            for log in logs:
                level = log.get("level", "log")
                levels[level] = levels.get(level, 0) + 1

            level_summary = ", ".join(
                f"{count} {level}" for level, count in levels.items()
            )
            message += f"\n    → Types: {level_summary}"

            # Show most recent log entry (truncated)
            recent = logs[0] if logs else None
            if recent:
                log_msg = recent.get("message", recent.get("text", ""))
                if log_msg:
                    display_msg = log_msg if len(log_msg) < 40 else log_msg[:37] + "..."
                    message += (
                        f"\n    → Latest: [{recent.get('level', 'log')}] {display_msg}"
                    )

        return {
            "name": "Console Log Capture",
            "status": "pass",
            "message": message,
        }

    except Exception as e:
        return {
            "name": "Console Log Capture",
            "status": "warning",
            "message": f"Could not test: {e}",
        }


async def _check_browser_control() -> dict:
    """Test browser control capabilities."""
    is_running, _, port = get_server_status()

    if not is_running:
        return {
            "name": "Browser Control",
            "status": "warning",
            "message": "Server not running",
        }

    try:
        import websockets

        async def test_control():
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, open_timeout=3.0) as ws:
                # Request capabilities
                await ws.send(
                    json.dumps(
                        {
                            "type": "get_capabilities",
                            "requestId": f"doctor_caps_{int(time.time() * 1000)}",
                        }
                    )
                )

                try:
                    # Server sends connection_ack first, then our response
                    for _ in range(3):  # Try up to 3 messages
                        response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        data = json.loads(response)

                        # Skip connection_ack and other handshake messages
                        if data.get("type") in (
                            "connection_ack",
                            "server_info_response",
                        ):
                            continue

                        if data.get("type") == "capabilities":
                            return data.get("capabilities", []), data.get(
                                "controlMethod"
                            )
                        elif data.get("type") == "error":
                            return [], None

                    return [], None
                except asyncio.TimeoutError:
                    return [], None

            return [], None

        caps, method = await test_control()

        if caps:
            cap_str = ", ".join(caps[:3])
            method_str = f" via {method}" if method else ""
            return {
                "name": "Browser Control",
                "status": "pass",
                "message": f"Available{method_str}: {cap_str}",
            }
        else:
            return {
                "name": "Browser Control",
                "status": "warning",
                "message": "No browser control available",
                "fix": "Connect extension or launch Chrome with --remote-debugging-port",
            }

    except Exception as e:
        return {
            "name": "Browser Control",
            "status": "warning",
            "message": f"Could not test: {e}",
        }


def _display_results(results: list, verbose: bool):
    """Display test results in a formatted table."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", style="cyan", width=25)
    table.add_column("Status", width=12)
    table.add_column("Details")

    for r in results:
        status_icon = {
            "pass": "[green]✓ PASS[/green]",
            "warning": "[yellow]⚠ WARN[/yellow]",
            "fail": "[red]✗ FAIL[/red]",
        }.get(r["status"], "?")

        details = r.get("message", "")
        if verbose and r.get("fix"):
            details += f"\n[dim]{r['fix']}[/dim]"

        table.add_row(r["name"], status_icon, details)

    console.print("\n")
    console.print(table)


def _auto_fix_issues(results: list):
    """Attempt to auto-fix issues."""
    fixes_applied = 0

    for r in results:
        if r["status"] == "fail" and "fix_func" in r:
            try:
                console.print(f"[cyan]→ Fixing {r['name']}...[/cyan]")
                r["fix_func"]()
                console.print(f"[green]✓ Fixed {r['name']}[/green]")
                fixes_applied += 1
            except Exception as e:
                console.print(f"[red]✗ Failed to fix {r['name']}: {e}[/red]")

    if fixes_applied > 0:
        console.print(
            f"\n[green]Applied {fixes_applied} fixes. Re-run doctor to verify.[/green]"
        )
    else:
        console.print(
            "\n[yellow]No auto-fixes available. Manual intervention required.[/yellow]"
        )
