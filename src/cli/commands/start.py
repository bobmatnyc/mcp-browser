"""Start command implementation."""

import asyncio
import os
import signal
import sys

import click
from rich.panel import Panel

from ..._version import __version__
from ..utils import DATA_DIR, console
from ..utils.daemon import (
    get_server_status,
    remove_project_server,
    start_daemon,
)


@click.command()
@click.option(
    "--port",
    "-p",
    default=None,
    type=int,
    help="WebSocket port (default: auto 8851-8899)",
)
@click.option(
    "--dashboard/--no-dashboard", default=True, help="Enable/disable dashboard"
)
@click.option(
    "--dashboard-port", default=8080, type=int, help="Dashboard port (default: 8080)"
)
@click.option("--background", "-b", is_flag=True, help="Run server in background")
@click.option(
    "--daemon", is_flag=True, hidden=True, help="Run as daemon (internal use)"
)
@click.pass_context
def start(ctx, port, dashboard, dashboard_port, background, daemon):
    """🚀 Start the MCP Browser server.

    \b
    Starts the MCP Browser server with WebSocket listener and optional dashboard.
    The server will:
      • Listen for browser connections on WebSocket (ports 8851-8899)
      • Store console logs with automatic rotation
      • Provide MCP tools for Claude Code
      • Serve dashboard for monitoring (if enabled)

    \b
    Examples:
      mcp-browser start                    # Start with defaults
      mcp-browser start --no-dashboard     # Start without dashboard
      mcp-browser start --port 8880        # Use specific port
      mcp-browser start --background       # Run in background

    \b
    Default settings:
      WebSocket: Auto-select from ports 8851-8899
      Dashboard: http://localhost:8080
      Data storage: ~/.mcp-browser/data/ or ./.mcp-browser/data/
      Log rotation: 50MB per file, 7-day retention

    \b
    Troubleshooting:
      • Port in use: Server auto-selects next available port
      • Extension not connecting: Check port in extension popup
      • Logs not appearing: Verify extension is installed
      • Use 'mcp-browser doctor' to diagnose issues
    """
    from ...cli.main import BrowserMCPServer

    config = ctx.obj.get("config")
    project_path = os.getcwd()

    # Handle background mode
    if background:
        # Check if server already running for this project
        is_running, existing_pid, existing_port = get_server_status()

        if is_running:
            console.print(
                Panel.fit(
                    f"[yellow]Server already running for this project[/yellow]\n\n"
                    f"PID: {existing_pid}\n"
                    f"Port: {existing_port}\n"
                    f"Project: {project_path}\n\n"
                    f"[dim]Stop it with 'mcp-browser stop' or restart with --port flag[/dim]",
                    title="Already Running",
                    border_style="yellow",
                )
            )
            return

        # Start daemon
        success, pid, actual_port = start_daemon(port)

        if success:
            console.print(
                Panel.fit(
                    f"[bold green]Server started in background[/bold green]\n\n"
                    f"PID: {pid}\n"
                    f"Port: {actual_port}\n"
                    f"Project: {project_path}\n\n"
                    f"[dim]Check status: mcp-browser status[/dim]\n"
                    f"[dim]Stop server: mcp-browser stop[/dim]",
                    title="Background Server Started",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel.fit(
                    "[red]Failed to start server in background[/red]\n\n"
                    "[dim]Try running without --background to see errors[/dim]",
                    title="Startup Failed",
                    border_style="red",
                )
            )
            sys.exit(1)
        return

    # Override port if specified
    if port and config is None:
        config = {}
    if port:
        config.setdefault("websocket", {})["port_range"] = [port, port]

    # Suppress output in daemon mode
    if not daemon:
        # Check if server already running for this project (foreground mode)
        is_running, existing_pid, existing_port = get_server_status()
        if is_running:
            console.print(
                Panel.fit(
                    f"[yellow]Server already running for this project[/yellow]\n\n"
                    f"PID: {existing_pid}\n"
                    f"Port: {existing_port}\n"
                    f"Project: {project_path}\n\n"
                    f"[dim]Stop it with 'mcp-browser stop' first[/dim]",
                    title="Already Running",
                    border_style="yellow",
                )
            )
            sys.exit(1)

        console.print(
            Panel.fit(
                f"[bold green]Starting MCP Browser Server v{__version__}[/bold green]\n\n"
                f"WebSocket: Ports {config.get('websocket', {}).get('port_range', [8851, 8899]) if config else [8851, 8899]}\n"
                f"Dashboard: {'Enabled' if dashboard else 'Disabled'} (port {dashboard_port})\n"
                f"Data: {DATA_DIR}\n"
                f"Project: {project_path}",
                title="Server Starting",
                border_style="green",
            )
        )

    server = BrowserMCPServer(config=config, mcp_mode=daemon)

    # Set up signal handlers
    def signal_handler(sig, frame):
        if not daemon:
            console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        if server.running:
            loop = asyncio.get_event_loop()
            loop.create_task(server.stop())
        # Clean up registry on shutdown
        if not daemon:
            remove_project_server(project_path)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if dashboard:
            asyncio.run(server.run_server_with_dashboard())
        else:
            asyncio.run(server.run_server())
    except KeyboardInterrupt:
        if not daemon:
            console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        if not daemon:
            console.print(f"\n[red]Server error: {e}[/red]")
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)
    finally:
        # Ensure cleanup on all exit paths
        if not daemon:
            remove_project_server(project_path)
