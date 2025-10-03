"""Dashboard command implementation."""

import asyncio
import threading
import webbrowser

import click
from rich.panel import Panel

from ..utils import console


async def run_dashboard_only(config=None) -> None:
    """Run dashboard service only without MCP server."""
    import logging
    from pathlib import Path

    from ....container import ServiceContainer
    from ....services import BrowserService, StorageService, WebSocketService
    from ....services.dashboard_service import DashboardService
    from ....services.storage_service import StorageConfig

    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create minimal container
    container = ServiceContainer()

    # Register minimal services for dashboard
    container.register(
        "storage_service",
        lambda c: StorageService(
            StorageConfig(base_path=Path.cwd() / ".mcp-browser" / "data")
        ),
    )
    container.register("websocket_service", lambda c: WebSocketService())
    container.register(
        "browser_service",
        lambda c: BrowserService(storage_service=container.get("storage_service")),
    )

    # Register dashboard service
    async def create_dashboard_service(c):
        return DashboardService()

    container.register("dashboard_service", create_dashboard_service)

    # Get and start dashboard
    dashboard = await container.get("dashboard_service")
    await dashboard.start(port=8080)

    print("Dashboard running at http://localhost:8080")
    print("Press Ctrl+C to stop")

    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
    finally:
        await dashboard.stop()


@click.command()
@click.option(
    "--port", "-p", default=8080, type=int, help="Dashboard port (default: 8080)"
)
@click.option(
    "--open", "-o", "open_browser", is_flag=True, help="Open dashboard in browser"
)
@click.pass_context
def dashboard(ctx, port, open_browser):
    """🎯 Run the monitoring dashboard.

    \b
    Starts only the web dashboard without the MCP server.
    Useful for monitoring an already-running server or viewing historical logs.

    \b
    Dashboard features:
      • Real-time connection status
      • Console log viewer with search
      • Chrome extension installer
      • Server statistics
      • Log file browser

    \b
    Examples:
      mcp-browser dashboard           # Start on default port 8080
      mcp-browser dashboard -p 3000   # Use custom port
      mcp-browser dashboard --open    # Auto-open in browser

    \b
    Access the dashboard at:
      http://localhost:8080 (or your chosen port)
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Starting Dashboard[/bold cyan]\n\n"
            f"Port: {port}\n"
            f"URL: http://localhost:{port}",
            title="Dashboard",
            border_style="cyan",
        )
    )

    if open_browser:
        # Wait a moment for server to start
        threading.Timer(
            1.0, lambda: webbrowser.open(f"http://localhost:{port}")
        ).start()

    config = ctx.obj.get("config")

    try:
        asyncio.run(run_dashboard_only(config))
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Dashboard error: {e}[/red]")
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
