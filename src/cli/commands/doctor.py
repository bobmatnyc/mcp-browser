"""Doctor command implementation with comprehensive functional tests."""

import asyncio
import json
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
@click.pass_context
def doctor(ctx, fix, verbose):
    """🩺 Diagnose and fix common MCP Browser issues.

    \b
    Performs comprehensive system checks:
      • Configuration files and directories
      • Python dependencies
      • MCP installer availability
      • Server status and ports
      • Extension package
      • Claude MCP integration
      • WebSocket connectivity
      • System requirements (Python, Chrome, Node.js)

    \b
    This command does NOT require browser connection.
    It will NOT auto-start the server (only reports status).

    \b
    Examples:
      mcp-browser doctor         # Run diagnostic
      mcp-browser doctor --fix   # Auto-fix issues
      mcp-browser doctor -v      # Verbose output

    \b
    Common issues and solutions:
      • "Port in use" - Another process using ports 8851-8899
      • "Extension not found" - Run 'mcp-browser setup'
      • "Chrome not detected" - Install Chrome or Chromium
      • "Permission denied" - Check directory permissions
    """
    asyncio.run(_doctor_command(fix, verbose))


async def _doctor_command(fix: bool, verbose: bool):
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

    # Test 4: Server Status
    console.print("[cyan]→ Checking server status...[/cyan]")
    results.append(_check_server_status())

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

    # Test 9: System Requirements (if verbose)
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
    """Check if extension ZIP exists."""
    # Try to find extension in common locations
    possible_paths = [
        Path.cwd() / "dist" / "mcp-browser-extension.zip",
        Path(__file__).parent.parent.parent.parent
        / "dist"
        / "mcp-browser-extension.zip",
        Path.home() / ".mcp-browser" / "mcp-browser-extension.zip",
    ]

    for zip_path in possible_paths:
        if zip_path.exists():
            size = zip_path.stat().st_size / 1024  # KB
            return {
                "name": "Extension Package",
                "status": "pass",
                "message": f"Found at {zip_path.relative_to(Path.cwd() if zip_path.is_relative_to(Path.cwd()) else Path.home())} ({size:.1f} KB)",
            }

    return {
        "name": "Extension Package",
        "status": "warning",
        "message": "Extension ZIP not found in common locations",
        "fix": "Run: mcp-browser setup",
    }


def _check_mcp_config() -> dict:
    """Check if MCP is configured for Claude."""
    # Check common MCP config locations
    claude_config = Path.home() / ".config" / "claude" / "claude_desktop_config.json"

    if claude_config.exists():
        try:
            with open(claude_config) as f:
                config = json.load(f)
            if "mcpServers" in config and "mcp-browser" in config.get("mcpServers", {}):
                return {
                    "name": "MCP Configuration",
                    "status": "pass",
                    "message": "mcp-browser configured in Claude",
                }
        except Exception:
            pass

    return {
        "name": "MCP Configuration",
        "status": "warning",
        "message": "MCP not configured for Claude",
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
