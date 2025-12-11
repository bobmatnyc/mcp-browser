"""Connect to existing browser via CDP command."""

import asyncio
import sys

import click
from rich.panel import Panel
from rich.table import Table

from ..utils import console

# Import required for CDP connection
try:
    from ...services.browser_controller import BrowserController, BrowserNotAvailableError
    from ...services import BrowserService, WebSocketService
    from ...services.applescript_service import AppleScriptService
    CDP_IMPORTS_AVAILABLE = True
except ImportError:
    CDP_IMPORTS_AVAILABLE = False


@click.command()
@click.option(
    "--cdp-port",
    default=9222,
    type=int,
    help="CDP port where Chrome is running (default: 9222)",
)
@click.pass_context
def connect(ctx, cdp_port: int):
    """🔌 Connect to existing Chrome browser via CDP.

    \b
    This command connects to a Chrome browser that's already running
    with remote debugging enabled. Useful for preserving browser state
    (cookies, sessions, extensions) while using MCP Browser.

    \b
    Prerequisites:
      1. Start Chrome with remote debugging:
         macOS:   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
         Linux:   google-chrome --remote-debugging-port=9222
         Windows: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222

      2. Ensure Playwright is installed:
         pip install playwright && playwright install

    \b
    Examples:
      mcp-browser connect                    # Connect to port 9222 (default)
      mcp-browser connect --cdp-port 9223    # Connect to custom port

    \b
    Once connected, you can use all MCP Browser features while preserving
    your existing browser session, cookies, and installed extensions.
    """
    asyncio.run(_connect_command(cdp_port))


async def _connect_command(cdp_port: int):
    """Execute connect command."""
    console.print(
        Panel(
            f"[bold cyan]🔌 Connecting to Chrome via CDP[/bold cyan]\n\n"
            f"Port: {cdp_port}\n"
            f"Checking browser availability...",
            title="CDP Connection",
            border_style="cyan",
        )
    )

    if not CDP_IMPORTS_AVAILABLE:
        console.print(
            Panel(
                "[red]✗ Required dependencies not available[/red]\n\n"
                "Install Playwright to use CDP connection:\n"
                "  [cyan]pip install playwright[/cyan]\n"
                "  [cyan]playwright install[/cyan]",
                title="Error",
                border_style="red",
            )
        )
        sys.exit(1)

    try:
        # Create minimal service instances for BrowserController
        # Note: In real usage, these would come from ServiceContainer
        websocket_service = WebSocketService(host="localhost", port_range=[8875, 8895])
        browser_service = BrowserService()
        applescript_service = AppleScriptService()

        # Create browser controller
        config = {
            "browser_control": {
                "mode": "cdp",
                "cdp_port": cdp_port,
                "cdp_enabled": True,
                "fallback_enabled": False,
            }
        }
        controller = BrowserController(
            websocket_service=websocket_service,
            browser_service=browser_service,
            applescript_service=applescript_service,
            config=config,
        )

        # Attempt connection
        console.print("[cyan]→ Attempting CDP connection...[/cyan]\n")
        result = await controller.connect_to_existing_browser(cdp_port=cdp_port)

        if result["success"]:
            # Show success table
            table = Table(title="✓ Connection Successful", show_header=False)
            table.add_column("Property", style="cyan", width=20)
            table.add_column("Value", style="green")

            table.add_row("Status", "[green]✓ Connected[/green]")
            table.add_row("Browser Version", result.get("browser_version", "Unknown"))
            table.add_row("CDP Port", str(result.get("cdp_port", cdp_port)))
            table.add_row("Active Pages", str(result.get("page_count", 0)))

            console.print(table)
            console.print(
                Panel(
                    "[green]✓ Successfully connected to Chrome![/green]\n\n"
                    "[bold]Next Steps:[/bold]\n"
                    "  • Your browser session is preserved (cookies, extensions)\n"
                    "  • Use MCP Browser tools with your existing browser\n"
                    "  • Navigate, click, and interact while maintaining state\n\n"
                    "[bold]Usage with Claude Code:[/bold]\n"
                    "  Configure CDP mode in your config.json:\n"
                    '  [dim]{"browser_control": {"mode": "cdp", "cdp_port": '
                    + str(cdp_port)
                    + "}}[/dim]",
                    title="Connection Established",
                    border_style="green",
                )
            )

            # Clean up
            await controller.close_cdp()

        else:
            console.print(
                Panel(
                    f"[red]✗ Connection failed[/red]\n\n"
                    f"Error: {result.get('error', 'Unknown error')}\n\n"
                    "[bold]Troubleshooting:[/bold]\n"
                    f"  1. Ensure Chrome is running with --remote-debugging-port={cdp_port}\n"
                    "  2. Check that no firewall is blocking the connection\n"
                    "  3. Verify Playwright is installed: [cyan]playwright install[/cyan]\n\n"
                    "[bold]Start Chrome with CDP:[/bold]\n"
                    "  macOS:   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port="
                    + str(cdp_port)
                    + "\n"
                    f"  Linux:   google-chrome --remote-debugging-port={cdp_port}\n"
                    f'  Windows: chrome.exe --remote-debugging-port={cdp_port}',
                    title="Connection Failed",
                    border_style="red",
                )
            )
            sys.exit(1)

    except BrowserNotAvailableError as e:
        console.print(
            Panel(
                f"[red]✗ Browser not available[/red]\n\n"
                f"{str(e)}\n\n"
                "[bold]How to start Chrome with CDP:[/bold]\n\n"
                "[bold cyan]macOS:[/bold cyan]\n"
                f'  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={cdp_port}\n\n'
                "[bold cyan]Linux:[/bold cyan]\n"
                f"  google-chrome --remote-debugging-port={cdp_port}\n\n"
                "[bold cyan]Windows:[/bold cyan]\n"
                f'  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port={cdp_port}\n\n'
                "[dim]Note: Close all Chrome instances before starting with CDP[/dim]",
                title="Browser Not Available",
                border_style="red",
            )
        )
        sys.exit(1)

    except Exception as e:
        console.print(
            Panel(
                f"[red]✗ Unexpected error[/red]\n\n"
                f"Error: {str(e)}\n\n"
                "Check the logs for more details.",
                title="Error",
                border_style="red",
            )
        )
        import traceback

        traceback.print_exc()
        sys.exit(1)
