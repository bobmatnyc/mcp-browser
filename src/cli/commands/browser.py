"""Browser interaction commands for testing and development."""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ..utils.browser_client import BrowserClient, find_active_port

console = Console()


@click.group()
def browser():
    """🌐 Browser interaction and testing commands.

    \b
    These commands provide direct browser control for testing and development.
    The server must be running before using these commands.

    \b
    Prerequisites:
      • Start the server: mcp-browser start
      • Install and connect Chrome extension
      • Navigate to a website in the browser

    \b
    Examples:
      mcp-browser browser navigate https://example.com
      mcp-browser browser logs --limit 10
      mcp-browser browser fill "#email" "test@example.com"
      mcp-browser browser click "#submit-button"
      mcp-browser browser test --demo
    """
    pass


@browser.command()
@click.argument("url")
@click.option(
    "--wait", default=0, type=float, help="Wait time after navigation (seconds)"
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
def navigate(url: str, wait: float, port: int):
    """Navigate browser to a URL.

    \b
    Examples:
      mcp-browser browser navigate https://example.com
      mcp-browser browser navigate https://google.com --wait 2
      mcp-browser browser navigate https://github.com --port 8875
    """
    asyncio.run(_navigate_command(url, wait, port))


async def _navigate_command(url: str, wait: float, port: Optional[int]):
    """Execute navigate command."""
    # Find active port if not specified
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                Panel(
                    "[red]✗ No active server found[/red]\n\n"
                    "Start the server with:\n"
                    "  [cyan]mcp-browser start[/cyan]",
                    title="Connection Error",
                    border_style="red",
                )
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    # Connect to server
    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        # Navigate
        console.print(f"[cyan]→ Navigating to {url}...[/cyan]")
        result = await client.navigate(url, wait)

        if result["success"]:
            console.print(
                Panel(
                    f"[green]✓ Successfully navigated to:[/green]\n{url}",
                    title="Navigation Complete",
                    border_style="green",
                )
            )
            if wait > 0:
                console.print(f"[dim]Waited {wait} seconds after navigation[/dim]")
        else:
            console.print(
                Panel(
                    f"[red]✗ Navigation failed:[/red]\n{result.get('error', 'Unknown error')}",
                    title="Navigation Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


@browser.command()
@click.option("--limit", default=50, type=int, help="Number of logs to retrieve")
@click.option(
    "--level",
    type=click.Choice(["all", "log", "error", "warn", "info"]),
    default="all",
    help="Filter by log level",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def logs(limit: int, level: str, port: int, json_output: bool):
    """Query captured console logs.

    \b
    Examples:
      mcp-browser browser logs
      mcp-browser browser logs --limit 10 --level error
      mcp-browser browser logs --json
    """
    asyncio.run(_logs_command(limit, level, port, json_output))


async def _logs_command(limit: int, level: str, port: Optional[int], json_output: bool):
    """Execute logs command."""
    # Find active port if not specified
    if port is None:
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)

    # For now, show a message about using MCP tools
    if json_output:
        import json

        print(
            json.dumps(
                {
                    "message": "Console logs are available via MCP tools",
                    "port": port,
                    "limit": limit,
                    "level": level,
                }
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]Console Logs[/yellow]\n\n"
                "Console logs are captured and stored automatically.\n\n"
                "[bold]To query logs:[/bold]\n"
                "  • Use Claude Code with the browser_query_logs tool\n"
                "  • Check the data directory for JSONL files\n"
                f"  • Server port: {port}\n"
                f"  • Filter: {level}, Limit: {limit}",
                title="📋 Console Logs",
                border_style="blue",
            )
        )


@browser.command()
@click.argument("selector")
@click.argument("value")
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
def fill(selector: str, value: str, port: int):
    """Fill a form field.

    \b
    Examples:
      mcp-browser browser fill "#email" "test@example.com"
      mcp-browser browser fill "input[name='username']" "testuser"
      mcp-browser browser fill ".search-box" "query text"
    """
    asyncio.run(_fill_command(selector, value, port))


async def _fill_command(selector: str, value: str, port: Optional[int]):
    """Execute fill command."""
    # Find active port if not specified
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    # Connect to server
    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        console.print(f"[cyan]→ Filling field '{selector}' with '{value}'...[/cyan]")
        result = await client.fill_field(selector, value)

        if result["success"]:
            console.print(
                Panel(
                    f"[green]✓ Successfully filled field:[/green]\n"
                    f"Selector: {selector}\n"
                    f"Value: {value}",
                    title="Fill Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]✗ Fill failed:[/red]\n{result.get('error', 'Unknown error')}",
                    title="Fill Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


@browser.command(name="click")
@click.argument("selector")
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
def click_element(selector: str, port: int):
    """Click an element.

    \b
    Examples:
      mcp-browser browser click "#submit-button"
      mcp-browser browser click "button.login"
      mcp-browser browser click "a[href='/dashboard']"
    """
    asyncio.run(_click_command(selector, port))


async def _click_command(selector: str, port: Optional[int]):
    """Execute click command."""
    # Find active port if not specified
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    # Connect to server
    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        console.print(f"[cyan]→ Clicking element '{selector}'...[/cyan]")
        result = await client.click_element(selector)

        if result["success"]:
            console.print(
                Panel(
                    f"[green]✓ Successfully clicked:[/green]\n{selector}",
                    title="Click Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]✗ Click failed:[/red]\n{result.get('error', 'Unknown error')}",
                    title="Click Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


@browser.command()
@click.argument("selector")
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
def extract(selector: str, port: int):
    """Extract content from an element.

    \b
    Examples:
      mcp-browser browser extract "h1"
      mcp-browser browser extract ".article-content"
      mcp-browser browser extract "#main-title"
    """
    asyncio.run(_extract_command(selector, port))


async def _extract_command(selector: str, port: Optional[int]):
    """Execute extract command."""
    # Find active port if not specified
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    # Connect to server
    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        console.print(f"[cyan]→ Extracting content from '{selector}'...[/cyan]")
        result = await client.extract_content(selector)

        if result["success"]:
            console.print(
                Panel(
                    f"[green]✓ Successfully extracted content from:[/green]\n{selector}\n\n"
                    "[dim]Content will be available in the response[/dim]",
                    title="Extract Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]✗ Extract failed:[/red]\n{result.get('error', 'Unknown error')}",
                    title="Extract Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


@browser.command()
@click.option("--output", default="screenshot.png", help="Output filename")
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
def screenshot(output: str, port: int):
    """Take a screenshot of the current browser tab.

    \b
    Examples:
      mcp-browser browser screenshot
      mcp-browser browser screenshot --output demo.png
      mcp-browser browser screenshot --output /tmp/page.png
    """
    asyncio.run(_screenshot_command(output, port))


async def _screenshot_command(output: str, port: Optional[int]):
    """Execute screenshot command."""
    # Find active port if not specified
    if port is None:
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)

    console.print(
        Panel(
            "[yellow]Screenshot Feature[/yellow]\n\n"
            "Screenshots are available via:\n"
            "  • [cyan]Claude Code[/cyan] - Use browser_screenshot tool\n"
            "  • [cyan]MCP Integration[/cyan] - Direct API access\n\n"
            f"Output file: {output}\n"
            f"Server port: {port}",
            title="📸 Screenshot",
            border_style="blue",
        )
    )


@browser.command()
@click.option("--demo", is_flag=True, help="Run automated demo scenario")
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
def test(demo: bool, port: int):
    """Run interactive browser test session.

    \b
    This command provides:
      • Interactive REPL for testing browser commands
      • Automated demo scenario with --demo flag
      • Step-by-step command execution
      • Real-time feedback and results

    \b
    Examples:
      mcp-browser browser test              # Interactive mode
      mcp-browser browser test --demo       # Run demo scenario
    """
    asyncio.run(_test_command(demo, port))


async def _test_command(demo: bool, port: Optional[int]):
    """Execute test command."""
    # Find active port if not specified
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                Panel(
                    "[red]✗ No active server found[/red]\n\n"
                    "Start the server with:\n"
                    "  [cyan]mcp-browser start[/cyan]\n\n"
                    "Then try again.",
                    title="Connection Error",
                    border_style="red",
                )
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    if demo:
        await _run_demo_scenario(port)
    else:
        await _run_interactive_test(port)


async def _run_demo_scenario(port: int):
    """Run automated demo scenario."""
    console.print(
        Panel(
            "[bold cyan]🚀 MCP Browser Demo Scenario[/bold cyan]\n\n"
            "This demo will:\n"
            "  1. Navigate to example.com\n"
            "  2. Extract page title\n"
            "  3. Show browser interaction capabilities\n\n"
            "[dim]Press Ctrl+C to cancel at any time[/dim]",
            title="Demo Mode",
            border_style="cyan",
        )
    )

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        # Step 1: Navigate
        console.print("\n[bold]Step 1: Navigation[/bold]")
        console.print("[cyan]→ Navigating to example.com...[/cyan]")
        result = await client.navigate("https://example.com", wait=2)

        if result["success"]:
            console.print("[green]✓ Navigation successful[/green]")
        else:
            console.print(f"[red]✗ Navigation failed: {result.get('error')}[/red]")
            return

        await asyncio.sleep(1)

        # Step 2: Extract title
        console.print("\n[bold]Step 2: Extract Page Title[/bold]")
        console.print("[cyan]→ Extracting h1 title...[/cyan]")
        result = await client.extract_content("h1")

        if result["success"]:
            console.print("[green]✓ Extraction command sent[/green]")
        else:
            console.print(f"[red]✗ Extraction failed: {result.get('error')}[/red]")

        await asyncio.sleep(1)

        # Demo complete
        console.print(
            Panel(
                "[green]✓ Demo completed successfully![/green]\n\n"
                "The browser extension captured all interactions.\n"
                "Console logs are stored and available via MCP tools.\n\n"
                "[bold]Next steps:[/bold]\n"
                "  • Try interactive mode: [cyan]mcp-browser browser test[/cyan]\n"
                "  • Use with Claude Code for AI-powered browsing",
                title="Demo Complete",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo cancelled[/yellow]")
    finally:
        await client.disconnect()


async def _run_interactive_test(port: int):
    """Run interactive test session."""
    console.print(
        Panel(
            "[bold cyan]🧪 Interactive Browser Test Session[/bold cyan]\n\n"
            "Available commands:\n"
            "  [cyan]navigate <url>[/cyan]     - Navigate to URL\n"
            "  [cyan]click <selector>[/cyan]   - Click element\n"
            "  [cyan]fill <selector> <value>[/cyan] - Fill form field\n"
            "  [cyan]extract <selector>[/cyan] - Extract content\n"
            "  [cyan]status[/cyan]            - Check server status\n"
            "  [cyan]help[/cyan]              - Show this help\n"
            "  [cyan]exit[/cyan]              - Exit session\n\n"
            "[dim]Type commands at the prompt. Use 'exit' or Ctrl+C to quit.[/dim]",
            title="Interactive Mode",
            border_style="cyan",
        )
    )

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        while True:
            try:
                # Get command from user
                command = Prompt.ask(
                    "\n[bold cyan]browser>[/bold cyan]", default="help"
                )

                if not command or command.strip() == "":
                    continue

                parts = command.strip().split()
                cmd = parts[0].lower()

                if cmd == "exit" or cmd == "quit":
                    console.print("[yellow]Exiting interactive session...[/yellow]")
                    break

                elif cmd == "help":
                    console.print(
                        "\n[bold]Available Commands:[/bold]\n"
                        "  navigate <url>           Navigate to URL\n"
                        "  click <selector>         Click element\n"
                        "  fill <selector> <value>  Fill form field\n"
                        "  extract <selector>       Extract content\n"
                        "  status                   Check server status\n"
                        "  help                     Show this help\n"
                        "  exit                     Exit session\n"
                    )

                elif cmd == "status":
                    status = await client.check_server_status()
                    table = Table(title="Server Status")
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="green")
                    table.add_row("Status", status.get("status", "unknown"))
                    table.add_row("Port", str(port))
                    console.print(table)

                elif cmd == "navigate":
                    if len(parts) < 2:
                        console.print("[red]Usage: navigate <url>[/red]")
                        continue
                    url = parts[1]
                    result = await client.navigate(url, wait=0)
                    if result["success"]:
                        console.print(f"[green]✓ Navigated to {url}[/green]")
                    else:
                        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")

                elif cmd == "click":
                    if len(parts) < 2:
                        console.print("[red]Usage: click <selector>[/red]")
                        continue
                    selector = parts[1]
                    result = await client.click_element(selector)
                    if result["success"]:
                        console.print(f"[green]✓ Clicked {selector}[/green]")
                    else:
                        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")

                elif cmd == "fill":
                    if len(parts) < 3:
                        console.print("[red]Usage: fill <selector> <value>[/red]")
                        continue
                    selector = parts[1]
                    value = " ".join(parts[2:])
                    result = await client.fill_field(selector, value)
                    if result["success"]:
                        console.print(
                            f"[green]✓ Filled {selector} with '{value}'[/green]"
                        )
                    else:
                        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")

                elif cmd == "extract":
                    if len(parts) < 2:
                        console.print("[red]Usage: extract <selector>[/red]")
                        continue
                    selector = parts[1]
                    result = await client.extract_content(selector)
                    if result["success"]:
                        console.print(
                            f"[green]✓ Extracted content from {selector}[/green]"
                        )
                    else:
                        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")

                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]")
                    console.print("[dim]Type 'help' for available commands[/dim]")

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
                continue

    except Exception as e:
        console.print(f"[red]Error in interactive session: {e}[/red]")
    finally:
        await client.disconnect()
