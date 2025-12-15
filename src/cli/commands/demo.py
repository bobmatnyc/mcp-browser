"""Interactive demo command implementation."""

import asyncio
import json
import sys
import time
from typing import Optional

import click
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from ..utils import console
from ..utils.browser_client import BrowserClient, find_active_port
from ..utils.daemon import ensure_server_running, get_server_status


@click.command()
@click.option(
    "--skip-checks",
    is_flag=True,
    help="Skip prerequisite checks and jump straight to demo",
)
def demo(skip_checks):
    """🎯 Interactive demonstration of MCP Browser capabilities.

    \b
    This demo walks you through all major features:
      • Verifying server and extension connection
      • Browser navigation control
      • Console log capture
      • DOM element interaction
      • JavaScript execution

    \b
    Prerequisites:
      • Chrome extension installed and connected
      • Browser with at least one tab open

    \b
    Example:
      mcp-browser demo              # Full interactive demo
      mcp-browser demo --skip-checks # Skip prereq checks
    """
    try:
        asyncio.run(_demo_command(skip_checks))
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo cancelled by user[/yellow]")
        sys.exit(0)


async def _demo_command(skip_checks: bool):
    """Execute interactive demo."""
    console.clear()

    # Welcome screen
    console.print(
        Panel.fit(
            "[bold cyan]🎯 MCP Browser Interactive Demo[/bold cyan]\n\n"
            "This demo will walk you through:\n"
            "  • Verifying your extension connection\n"
            "  • Navigating to a webpage\n"
            "  • Capturing console logs\n"
            "  • Interacting with page elements\n"
            "  • Executing JavaScript code\n\n"
            "[dim]Press Ctrl+C at any time to exit.[/dim]",
            border_style="cyan",
        )
    )

    if not skip_checks:
        console.print("\n[cyan]Checking prerequisites...[/cyan]")

        # Step 0: Prerequisites Check
        server_ok, port = await _check_prerequisites()

        if not server_ok:
            console.print(
                Panel(
                    "[red]✗ Prerequisites check failed[/red]\n\n"
                    "Please ensure:\n"
                    "  1. Server is running: [cyan]mcp-browser start[/cyan]\n"
                    "  2. Extension is installed and connected\n\n"
                    "Run [cyan]mcp-browser doctor[/cyan] for more details.",
                    title="Setup Required",
                    border_style="red",
                )
            )
            sys.exit(1)
    else:
        # Find port without full checks
        port = await find_active_port()
        if port is None:
            console.print("[red]✗ No active server found[/red]")
            sys.exit(1)

    _wait_for_continue()

    # Step 1: Verify Connection
    await _step_verify_connection(port)
    _wait_for_continue()

    # Step 2: Navigate to Demo Page
    await _step_navigate(port)
    _wait_for_continue()

    # Step 3: Console Log Capture
    await _step_console_logs(port)
    _wait_for_continue()

    # Step 4: DOM Interaction (if possible)
    await _step_dom_interaction(port)
    _wait_for_continue()

    # Step 5: Summary
    _show_summary()


async def _check_prerequisites() -> tuple[bool, Optional[int]]:
    """Check prerequisites and auto-start server if needed.

    Returns:
        Tuple of (success, port)
    """
    # Check if server is running
    is_running, _, existing_port = get_server_status()

    if not is_running:
        console.print("[cyan]→ Server not running, starting now...[/cyan]")
        success, port = ensure_server_running()

        if not success:
            return False, None

        console.print(f"[green]✓ Server started on port {port}[/green]")
        # Wait a moment for server to fully initialize
        await asyncio.sleep(1)
        return True, port
    else:
        console.print(
            f"[green]✓ Server running on port {existing_port}[/green]"
        )
        return True, existing_port


def _wait_for_continue():
    """Wait for user to press Enter to continue."""
    console.print(
        "\n[dim][Press Enter to continue, or Ctrl+C to exit][/dim]", end=""
    )
    try:
        input()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo cancelled[/yellow]")
        sys.exit(0)
    console.print()


def _print_step_header(step_num: int, total: int, title: str):
    """Print a step header."""
    console.print(
        "\n" + "━" * 60 + "\n"
        f"  [bold cyan]Step {step_num} of {total}: {title}[/bold cyan]\n"
        + "━" * 60
    )


async def _step_verify_connection(port: int):
    """Step 1: Verify extension connection."""
    _print_step_header(1, 5, "Verify Connection")

    console.print("\n[cyan]Connecting to server...[/cyan]")

    client = BrowserClient(port=port)
    if not await client.connect():
        console.print("[red]✗ Failed to connect[/red]")
        sys.exit(1)

    try:
        # Get capabilities to verify extension is connected
        console.print("[cyan]Checking for browser extension...[/cyan]")

        request_id = f"demo_caps_{int(time.time() * 1000)}"
        await client.websocket.send(
            json.dumps({"type": "get_capabilities", "requestId": request_id})
        )

        # Wait for response (with timeout)
        caps = None
        try:
            for _ in range(5):  # Try up to 5 messages
                response = await asyncio.wait_for(client.websocket.recv(), timeout=3.0)
                data = json.loads(response)

                # Skip handshake messages
                if data.get("type") in ("connection_ack", "server_info_response"):
                    continue

                if data.get("type") == "capabilities":
                    caps = data.get("capabilities", [])
                    break
        except asyncio.TimeoutError:
            pass

        if caps:
            console.print(
                Panel(
                    f"[green]✓ Extension Connected[/green]\n\n"
                    f"  • Port: [cyan]{port}[/cyan]\n"
                    f"  • Capabilities: [cyan]{', '.join(caps[:3])}[/cyan]",
                    title="Connection Status",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    "[yellow]⚠ Extension may not be connected[/yellow]\n\n"
                    "The demo will continue, but some features may not work.\n"
                    "Make sure the extension is loaded and connected.",
                    title="Connection Warning",
                    border_style="yellow",
                )
            )

    finally:
        await client.disconnect()


async def _step_navigate(port: int):
    """Step 2: Navigate to demo page."""
    _print_step_header(2, 5, "Navigate to Demo Page")

    console.print(
        "\n[cyan]Let's navigate to a demo page that showcases console logging.[/cyan]\n"
    )

    # Ask user for URL or use default
    use_default = (
        Prompt.ask(
            "Use default demo page (example.com)?",
            choices=["y", "n"],
            default="y",
        )
        == "y"
    )

    if use_default:
        url = "https://example.com"
    else:
        url = Prompt.ask("Enter URL to navigate to", default="https://example.com")

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        console.print(f"\n[cyan]→ Navigating to {url}...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Navigating...", total=None)
            result = await client.navigate(url, wait=1.0)
            progress.update(task, completed=True)

        if result["success"]:
            console.print(
                Panel(
                    f"[green]✓ Navigation successful![/green]\n\n"
                    f"The browser should now be at:\n[cyan]{url}[/cyan]",
                    title="Navigation Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]✗ Navigation failed:[/red]\n{result.get('error', 'Unknown error')}",
                    title="Navigation Error",
                    border_style="red",
                )
            )

    finally:
        await client.disconnect()


async def _step_console_logs(port: int):
    """Step 3: Console log capture demonstration."""
    _print_step_header(3, 5, "Console Log Capture")

    console.print(
        "\n[cyan]Now let's generate some console logs and capture them.[/cyan]\n"
    )

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        # Execute JavaScript to generate console logs
        console.print("[cyan]→ Generating console logs in browser...[/cyan]")

        js_code = """
        console.log('🎯 Hello from MCP Browser Demo!');
        console.info('This is an info message');
        console.warn('This is a warning message');
        console.error('This is an error message (not a real error!)');
        console.log('Demo completed successfully!');
        """

        request_id = f"demo_eval_{int(time.time() * 1000)}"
        await client.websocket.send(
            json.dumps(
                {
                    "type": "evaluate_js",
                    "requestId": request_id,
                    "code": js_code.strip(),
                }
            )
        )

        # Wait for execution
        await asyncio.sleep(1)

        console.print("[cyan]→ Querying captured logs...[/cyan]")

        # Query logs
        request_id = f"demo_logs_{int(time.time() * 1000)}"
        await client.websocket.send(
            json.dumps({"type": "get_logs", "requestId": request_id, "lastN": 10})
        )

        # Wait for response
        logs = []
        try:
            for _ in range(5):
                response = await asyncio.wait_for(client.websocket.recv(), timeout=3.0)
                data = json.loads(response)

                if data.get("type") in ("connection_ack", "server_info_response"):
                    continue

                if data.get("type") == "logs":
                    logs = data.get("logs", [])
                    break
        except asyncio.TimeoutError:
            pass

        if logs:
            from rich.table import Table

            table = Table(title="Recent Console Logs", show_header=True)
            table.add_column("Level", style="cyan", width=10)
            table.add_column("Message", style="white")

            # Show last 5 logs
            for log in logs[:5]:
                level = log.get("level", "log")
                message = log.get("message", log.get("text", ""))

                # Truncate long messages
                if len(message) > 60:
                    message = message[:57] + "..."

                # Color by level
                level_style = {
                    "error": "[red]ERROR[/red]",
                    "warn": "[yellow]WARN[/yellow]",
                    "warning": "[yellow]WARN[/yellow]",
                    "info": "[blue]INFO[/blue]",
                    "log": "[green]LOG[/green]",
                }.get(level.lower(), level)

                table.add_row(level_style, message)

            console.print()
            console.print(table)
            console.print(
                f"\n[green]✓ Captured {len(logs)} console logs[/green]"
            )
        else:
            console.print(
                Panel(
                    "[yellow]⚠ No logs captured[/yellow]\n\n"
                    "This might mean:\n"
                    "  • Extension is not connected\n"
                    "  • Page doesn't have console logs\n"
                    "  • Logs haven't synchronized yet",
                    title="No Logs",
                    border_style="yellow",
                )
            )

    finally:
        await client.disconnect()


async def _step_dom_interaction(port: int):
    """Step 4: DOM interaction demonstration."""
    _print_step_header(4, 5, "DOM Interaction")

    console.print(
        "\n[cyan]MCP Browser can also interact with page elements.[/cyan]\n"
    )

    console.print(
        Panel(
            "[bold]Available DOM Operations:[/bold]\n\n"
            "  • [cyan]Click elements[/cyan] - Click buttons, links, etc.\n"
            "  • [cyan]Fill forms[/cyan] - Enter text into input fields\n"
            "  • [cyan]Submit forms[/cyan] - Submit form data\n"
            "  • [cyan]Get element info[/cyan] - Retrieve element properties\n"
            "  • [cyan]Wait for elements[/cyan] - Wait for elements to appear\n"
            "  • [cyan]Select options[/cyan] - Choose from dropdown menus\n\n"
            "[dim]To try these features, navigate to a page with forms and elements.[/dim]",
            title="DOM Control Features",
            border_style="blue",
        )
    )

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        # Try to get element info from current page
        console.print("\n[cyan]→ Inspecting page structure...[/cyan]")

        request_id = f"demo_element_{int(time.time() * 1000)}"
        await client.websocket.send(
            json.dumps(
                {
                    "type": "get_element",
                    "requestId": request_id,
                    "selector": "h1",  # Try to find an h1 element
                }
            )
        )

        # Wait for response
        element_found = False
        try:
            for _ in range(3):
                response = await asyncio.wait_for(client.websocket.recv(), timeout=2.0)
                data = json.loads(response)

                if data.get("type") in ("connection_ack", "server_info_response"):
                    continue

                if data.get("type") == "element_info":
                    element_found = True
                    element_text = data.get("text", "")
                    console.print(
                        f"[green]✓ Found page heading: [/green][cyan]{element_text[:50]}[/cyan]"
                    )
                    break
        except asyncio.TimeoutError:
            pass

        if not element_found:
            console.print(
                "[dim]Page inspection completed (no h1 element found)[/dim]"
            )

    finally:
        await client.disconnect()


def _show_summary():
    """Step 5: Show summary and next steps."""
    _print_step_header(5, 5, "Demo Complete!")

    console.print(
        Panel.fit(
            "[bold green]🎉 Congratulations![/bold green]\n\n"
            "You've completed the MCP Browser interactive demo!\n\n"
            "[bold]What you learned:[/bold]\n"
            "  ✓ Verifying server and extension connection\n"
            "  ✓ Navigating to web pages programmatically\n"
            "  ✓ Capturing and viewing console logs\n"
            "  ✓ Interacting with DOM elements\n\n"
            "[bold cyan]Useful next commands:[/bold cyan]\n"
            "  • [cyan]mcp-browser status[/cyan] - Check current status\n"
            "  • [cyan]mcp-browser browser logs[/cyan] - View recent logs\n"
            "  • [cyan]mcp-browser browser control navigate <url>[/cyan] - Navigate\n"
            "  • [cyan]mcp-browser doctor[/cyan] - Diagnose issues\n"
            "  • [cyan]mcp-browser tutorial[/cyan] - Interactive tutorial\n\n"
            "[bold]Using with Claude Code:[/bold]\n"
            "Once configured, Claude Code can use all these features\n"
            "automatically through MCP tools to help you debug and\n"
            "interact with web applications!\n\n"
            "[dim]Run 'mcp-browser install' if you haven't set up Claude integration yet.[/dim]",
            title="Demo Summary",
            border_style="green",
        )
    )
