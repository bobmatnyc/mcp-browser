"""Start command implementation."""

import asyncio
import signal
import sys

import click
from rich.panel import Panel

from ..._version import __version__
from ..utils import DATA_DIR, console


@click.command()
@click.option(
    "--port",
    "-p",
    default=None,
    type=int,
    help="WebSocket port (default: auto 8875-8895)",
)
@click.option(
    "--dashboard/--no-dashboard", default=True, help="Enable/disable dashboard"
)
@click.option(
    "--dashboard-port", default=8080, type=int, help="Dashboard port (default: 8080)"
)
@click.option("--background", "-b", is_flag=True, help="Run server in background")
@click.pass_context
def start(ctx, port, dashboard, dashboard_port, background):
    """🚀 Start the MCP Browser server.

    \b
    Starts the MCP Browser server with WebSocket listener and optional dashboard.
    The server will:
      • Listen for browser connections on WebSocket (ports 8875-8895)
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
      WebSocket: Auto-select from ports 8875-8895
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

    if background:
        console.print("[yellow]Background mode not yet implemented[/yellow]")
        console.print("[dim]Tip: Use screen/tmux or run with '&' on Unix systems[/dim]")
        return

    # Override port if specified
    if port and config is None:
        config = {}
    if port:
        config.setdefault("websocket", {})["port_range"] = [port, port]

    console.print(
        Panel.fit(
            f"[bold green]Starting MCP Browser Server v{__version__}[/bold green]\n\n"
            f"WebSocket: Ports {config.get('websocket', {}).get('port_range', [8875, 8895]) if config else [8875, 8895]}\n"
            f"Dashboard: {'Enabled' if dashboard else 'Disabled'} (port {dashboard_port})\n"
            f"Data: {DATA_DIR}",
            title="Server Starting",
            border_style="green",
        )
    )

    server = BrowserMCPServer(config=config, mcp_mode=False)

    # Set up signal handlers
    def signal_handler(sig, frame):
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        if server.running:
            loop = asyncio.get_event_loop()
            loop.create_task(server.stop())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if dashboard:
            asyncio.run(server.run_server_with_dashboard())
        else:
            asyncio.run(server.run_server())
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Server error: {e}[/red]")
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)
