"""Browser interaction commands for testing and development."""

import asyncio
import functools
import sys
from typing import Any, Callable, Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ..utils.browser_client import BrowserClient, find_active_port
from ..utils.daemon import ensure_server_running, get_server_status
from .browser_refactored import (
    create_command_handlers,
    process_interactive_command,
)

console = Console()


def _display_skeletal_dom(skeletal: Dict[str, Any]) -> None:
    """Display skeletal DOM in a readable tree format."""
    # Unwrap nested response if present
    if "response" in skeletal and isinstance(skeletal["response"], dict):
        skeletal = skeletal["response"]
    dom = skeletal.get("skeletal_dom", {})
    if not dom:
        return

    from rich.tree import Tree

    title = dom.get("title", "Unknown Page")
    url = dom.get("url", "")

    tree = Tree(f"[bold]📄 {title}[/bold]")
    tree.add(f"[dim]🔗 {url}[/dim]")

    # Headings
    headings = dom.get("headings", [])
    if headings:
        h_branch = tree.add("[cyan]Headings[/cyan]")
        for h in headings[:5]:
            h_branch.add(f"[{h.get('tag', 'h?')}] {h.get('text', '')[:50]}")

    # Inputs
    inputs = dom.get("inputs", [])
    if inputs:
        i_branch = tree.add("[yellow]Inputs[/yellow]")
        for inp in inputs[:5]:
            name = inp.get("name") or inp.get("id") or inp.get("type", "?")
            i_branch.add(f"[input] {name}")

    # Buttons
    buttons = dom.get("buttons", [])
    if buttons:
        b_branch = tree.add("[green]Buttons[/green]")
        for btn in buttons[:5]:
            b_branch.add(f"[button] {btn.get('text', '')[:30]}")

    # Links
    links = dom.get("links", [])
    if links:
        l_branch = tree.add(f"[blue]Links ({len(links)} found)[/blue]")
        for link in links[:8]:
            text = link.get("text", "")[:25] or "(no text)"
            href = link.get("href", "")[:40]
            l_branch.add(f"{text} → [dim]{href}[/dim]")

    console.print(tree)
    console.print()


def requires_server(f: Callable) -> Callable:
    """Decorator that ensures server is running before command executes.

    This decorator will:
    1. Check if server is already running
    2. Auto-start server if not running
    3. Show brief status messages
    4. Handle failure gracefully with helpful error messages

    Usage:
        @requires_server
        async def my_command():
            # Server is now guaranteed to be running
            ...
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Check current status first
        is_running, _, existing_port = get_server_status()

        if not is_running:
            console.print("[cyan]⚡ Starting server...[/cyan]", end=" ")
            success, port = ensure_server_running()

            if not success:
                console.print("[red]✗ Failed[/red]")
                console.print(
                    Panel(
                        "[red]✗ Failed to start server automatically[/red]\n\n"
                        "Please try starting manually:\n"
                        "  [cyan]mcp-browser start[/cyan]\n\n"
                        "Or check for errors:\n"
                        "  [cyan]mcp-browser doctor[/cyan]",
                        title="Auto-Start Failed",
                        border_style="red",
                    )
                )
                return

            console.print(f"[green]✓ Started on port {port}[/green]")

        # Server is now running, proceed with command
        return f(*args, **kwargs)

    return wrapper


@click.group()
def browser():
    """🌐 Browser interaction and testing commands.

    \b
    These commands provide direct browser control for testing and development.
    The server will auto-start if not already running.

    \b
    Prerequisites:
      • Install and connect Chrome extension (mcp-browser setup)
      • Navigate to a website in the browser

    \b
    Examples:
      mcp-browser browser control navigate https://example.com
      mcp-browser browser control fill "#email" "test@example.com"
      mcp-browser browser control click "#submit-button"
      mcp-browser browser extract content
      mcp-browser browser logs --limit 10
      mcp-browser browser test --demo
    """
    pass


@browser.group()
def control():
    """🎮 Control browser interactions.

    \b
    Control commands:
      navigate  - Go to URL
      click     - Click element
      fill      - Fill form field
      scroll    - Scroll page
      submit    - Submit form

    \b
    Examples:
      mcp-browser browser control navigate https://example.com
      mcp-browser browser control click "#submit-btn"
      mcp-browser browser control fill "#email" "test@example.com"
      mcp-browser browser control scroll --down 500
    """
    pass


@control.command(name="navigate")
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
@requires_server
def navigate_to_url(url: str, wait: float, port: int):
    """Navigate browser to a URL.

    \b
    Examples:
      mcp-browser browser control navigate https://example.com
      mcp-browser browser control navigate https://google.com --wait 2
      mcp-browser browser control navigate https://github.com --port 8875
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
            # Wait for page load then verify actual URL
            await asyncio.sleep(1.5)
            tab_info = await client.get_tab_info(timeout=3.0)

            if tab_info.get("success"):
                actual_url = tab_info.get("url", url)
                title = tab_info.get("title", "")
                console.print(
                    Panel(
                        f"[green]✓ Browser confirmed at:[/green]\n{actual_url}"
                        + (f"\n[dim]Title: {title}[/dim]" if title else ""),
                        title="Navigation Complete",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        f"[green]✓ Navigation sent to:[/green]\n{url}\n"
                        f"[dim](URL verification unavailable)[/dim]",
                        title="Navigation Complete",
                        border_style="green",
                    )
                )

            if wait > 0:
                console.print(f"[dim]Waited {wait} seconds after navigation[/dim]")
            console.print("[dim]Fetching page structure...[/dim]")
            skeletal = await client.get_skeletal_dom()
            # Unwrap nested response for success check
            skeletal_inner = (
                skeletal.get("response", skeletal)
                if "response" in skeletal
                else skeletal
            )
            if skeletal_inner.get("success"):
                _display_skeletal_dom(skeletal)
            else:
                console.print(
                    f"[yellow]⚠ Could not get page structure: {skeletal_inner.get('error', 'Unknown')}[/yellow]"
                )
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
@requires_server
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


@control.command(name="fill")
@click.argument("selector")
@click.argument("value")
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
@requires_server
def fill_field(selector: str, value: str, port: int):
    """Fill a form field.

    \b
    Examples:
      mcp-browser browser control fill "#email" "test@example.com"
      mcp-browser browser control fill "input[name='username']" "testuser"
      mcp-browser browser control fill ".search-box" "query text"
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


@control.command(name="click")
@click.argument("selector")
@click.option(
    "--port",
    default=None,
    type=int,
    help="WebSocket port (auto-detect if not specified)",
)
@requires_server
def click_element(selector: str, port: int):
    """Click an element.

    \b
    Examples:
      mcp-browser browser control click "#submit-button"
      mcp-browser browser control click "button.login"
      mcp-browser browser control click "a[href='/home']"
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


@control.command(name="scroll")
@click.option("--up", "direction", flag_value="up", help="Scroll up")
@click.option(
    "--down", "direction", flag_value="down", default=True, help="Scroll down"
)
@click.option("--amount", default=500, type=int, help="Pixels to scroll")
@click.option("--port", default=None, type=int, help="WebSocket port")
@requires_server
def scroll_page(direction: str, amount: int, port: int):
    """Scroll the page up or down.

    \b
    Examples:
      mcp-browser browser control scroll
      mcp-browser browser control scroll --down 1000
      mcp-browser browser control scroll --up 300
    """
    asyncio.run(_scroll_command(direction, amount, port))


async def _scroll_command(direction: str, amount: int, port: Optional[int]):
    """Execute scroll command."""
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
        console.print(f"[cyan]→ Scrolling {direction} by {amount}px...[/cyan]")
        result = await client.scroll(direction, amount)

        if result["success"]:
            console.print(
                Panel(
                    f"[green]✓ Successfully scrolled:[/green]\n"
                    f"Direction: {direction}\n"
                    f"Amount: {amount}px",
                    title="Scroll Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]✗ Scroll failed:[/red]\n{result.get('error', 'Unknown error')}",
                    title="Scroll Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


@control.command(name="submit")
@click.argument("selector")
@click.option("--port", default=None, type=int, help="WebSocket port")
@requires_server
def submit_form(selector: str, port: int):
    """Submit a form.

    \b
    Examples:
      mcp-browser browser control submit "form#login"
      mcp-browser browser control submit "form.search-form"
    """
    asyncio.run(_submit_command(selector, port))


async def _submit_command(selector: str, port: Optional[int]):
    """Execute submit command."""
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
        console.print(f"[cyan]→ Submitting form '{selector}'...[/cyan]")
        result = await client.submit_form(selector)

        if result["success"]:
            console.print(
                Panel(
                    f"[green]✓ Successfully submitted form:[/green]\n{selector}",
                    title="Submit Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]✗ Submit failed:[/red]\n{result.get('error', 'Unknown error')}",
                    title="Submit Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


@browser.group()
def extract():
    """📄 Extract content from browser pages.

    \b
    Extraction strategies:
      content   - Readable article content (Readability.js)
      semantic  - Page structure (headings, landmarks, links, forms)
      ascii     - ASCII box diagram of element positions
      selector  - Specific element by CSS selector

    \b
    Examples:
      mcp-browser browser extract content
      mcp-browser browser extract semantic
      mcp-browser browser extract semantic --no-links
      mcp-browser browser extract selector "h1"
      mcp-browser browser extract selector ".article-body"
    """
    pass


@extract.command(name="content")
@click.option("--port", default=None, type=int, help="WebSocket port")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@requires_server
def extract_content(port: int, json_output: bool):
    """Extract readable content using Readability.js.

    Best for articles, documentation, and text-heavy pages.

    \b
    Examples:
      mcp-browser browser extract content
      mcp-browser browser extract content --json
    """
    asyncio.run(_extract_content_command(port, json_output))


async def _extract_content_command(port: Optional[int], json_output: bool):
    """Execute content extraction."""
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        console.print("[cyan]→ Extracting readable content...[/cyan]")
        result = await client.extract_readable_content(timeout=15.0)

        if json_output:
            import json as json_module

            print(json_module.dumps(result, indent=2))
            return

        if result.get("success") or result.get("response", {}).get("success"):
            response = result.get("response", result)
            content = response.get("content", {})

            # Display formatted output
            console.print(
                Panel(
                    f"[bold]{content.get('title', 'Untitled')}[/bold]\n\n"
                    f"[dim]By: {content.get('byline', 'Unknown')}[/dim]\n"
                    f"[dim]Words: {content.get('wordCount', 'N/A')}[/dim]\n\n"
                    f"{(content.get('excerpt', '') or content.get('textContent', ''))[:500]}...",
                    title="📄 Extracted Content",
                    border_style="green",
                )
            )
        else:
            error = result.get("error") or result.get("response", {}).get(
                "error", "Unknown error"
            )
            console.print(
                Panel(
                    f"[red]✗ Extraction failed:[/red]\n{error}",
                    title="Extract Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


@extract.command(name="ascii")
@click.option("--port", default=None, type=int, help="WebSocket port")
@click.option("--width", default=80, type=int, help="ASCII canvas width")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@requires_server
def extract_ascii(port: int, width: int, json_output: bool):
    """Extract ASCII layout visualization of page elements.

    Shows element positions as ASCII box diagram - token-efficient
    alternative to screenshots (~100x smaller).

    \b
    Examples:
      mcp-browser browser extract ascii
      mcp-browser browser extract ascii --width 100
      mcp-browser browser extract ascii --json
    """
    asyncio.run(_extract_ascii_command(port, width, json_output))


async def _extract_ascii_command(port: Optional[int], width: int, json_output: bool):
    """Execute ASCII layout extraction."""
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        console.print("[cyan]→ Extracting ASCII layout...[/cyan]")
        result = await client.extract_ascii_layout(timeout=15.0)

        if json_output:
            import json as json_module
            print(json_module.dumps(result, indent=2))
            return

        if result.get("success") or result.get("response", {}).get("success"):
            response = result.get("response", result)
            layout = response.get("layout", {})

            # Format ASCII output
            formatted = _format_ascii_layout(layout, width)
            console.print(formatted)
        else:
            error = result.get("error") or result.get("response", {}).get(
                "error", "Unknown error"
            )
            console.print(
                Panel(
                    f"[red]✗ ASCII extraction failed:[/red]\n{error}",
                    title="Extract Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


def _format_ascii_layout(layout: Dict[str, Any], width: int = 80) -> str:
    """Convert element positions to ASCII box diagram."""
    viewport = layout.get("viewport", {"width": 1200, "height": 800})
    elements = layout.get("elements", [])
    url = layout.get("url", "")
    title = layout.get("title", "")

    if not elements:
        return f"# ASCII Layout: {title}\nURL: {url}\n\n(No visible elements found)"

    vp_width = max(viewport.get("width", 1200), 1)
    vp_height = max(viewport.get("height", 800), 1)
    scale_x = (width - 2) / vp_width
    scale_y = ((width // 2) - 2) / vp_height

    height = max(int(vp_height * scale_y) + 2, 10)
    height = min(height, 60)

    canvas = [[" " for _ in range(width)] for _ in range(height)]

    sorted_elements = sorted(
        elements, key=lambda e: e.get("width", 0) * e.get("height", 0), reverse=True
    )

    for el in sorted_elements:
        x1 = int(el.get("x", 0) * scale_x)
        y1 = int(el.get("y", 0) * scale_y)
        el_width = int(el.get("width", 0) * scale_x)
        el_height = int(el.get("height", 0) * scale_y)

        x2 = min(x1 + el_width, width - 1)
        y2 = min(y1 + el_height, height - 1)

        if x2 > x1 + 2 and y2 > y1 + 1 and x1 >= 0 and y1 >= 0:
            _draw_ascii_box(canvas, x1, y1, x2, y2, el.get("type", "?"))

    lines = [
        f"# ASCII Layout: {title}",
        f"URL: {url}",
        f"Viewport: {vp_width}x{vp_height}",
        "",
    ]
    lines.extend("".join(row).rstrip() for row in canvas)

    element_types = set(el.get("type", "?") for el in elements)
    lines.append("")
    lines.append("## Elements Found:")
    for el_type in sorted(element_types):
        count = sum(1 for el in elements if el.get("type") == el_type)
        lines.append(f"  [{el_type}]: {count}")

    return "\n".join(lines)


def _draw_ascii_box(
    canvas: list, x1: int, y1: int, x2: int, y2: int, el_type: str
) -> None:
    """Draw a box on the ASCII canvas."""
    height = len(canvas)
    width = len(canvas[0]) if canvas else 0

    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(0, min(x2, width - 1))
    y2 = max(0, min(y2, height - 1))

    if x2 <= x1 or y2 <= y1:
        return

    canvas[y1][x1] = "┌"
    canvas[y1][x2] = "┐"
    canvas[y2][x1] = "└"
    canvas[y2][x2] = "┘"

    for x in range(x1 + 1, x2):
        if canvas[y1][x] == " ":
            canvas[y1][x] = "─"
        if canvas[y2][x] == " ":
            canvas[y2][x] = "─"

    for y in range(y1 + 1, y2):
        if canvas[y][x1] == " ":
            canvas[y][x1] = "│"
        if canvas[y][x2] == " ":
            canvas[y][x2] = "│"

    label = f"[{el_type}]"
    if len(label) < x2 - x1 - 1 and y1 + 1 < y2:
        for i, c in enumerate(label):
            if x1 + 1 + i < x2:
                canvas[y1 + 1][x1 + 1 + i] = c


@extract.command(name="semantic")
@click.option("--port", default=None, type=int, help="WebSocket port")
@click.option("--headings/--no-headings", default=True, help="Include headings")
@click.option("--landmarks/--no-landmarks", default=True, help="Include landmarks")
@click.option("--links/--no-links", default=True, help="Include links")
@click.option("--forms/--no-forms", default=True, help="Include forms")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@requires_server
def extract_semantic(
    port: int,
    headings: bool,
    landmarks: bool,
    links: bool,
    forms: bool,
    json_output: bool,
):
    """Extract semantic DOM structure.

    Provides quick page understanding without screenshots:
    - Headings (h1-h6) with hierarchy
    - ARIA landmarks and HTML5 sections
    - Links with text
    - Forms with fields

    \b
    Examples:
      mcp-browser browser extract semantic
      mcp-browser browser extract semantic --no-links
      mcp-browser browser extract semantic --json
    """
    asyncio.run(
        _extract_semantic_command(port, headings, landmarks, links, forms, json_output)
    )


async def _extract_semantic_command(
    port: Optional[int],
    headings: bool,
    landmarks: bool,
    links: bool,
    forms: bool,
    json_output: bool,
):
    """Execute semantic DOM extraction."""
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        console.print("[cyan]→ Extracting semantic DOM...[/cyan]")
        result = await client.extract_semantic_dom(
            include_headings=headings,
            include_landmarks=landmarks,
            include_links=links,
            include_forms=forms,
            timeout=15.0,
        )

        if json_output:
            import json as json_module

            print(json_module.dumps(result, indent=2))
            return

        response = result.get("response", result)
        if response.get("success"):
            dom = response.get("dom", {})
            _display_semantic_dom(dom, headings, landmarks, links, forms)
        else:
            error = response.get("error", "Unknown error")
            console.print(
                Panel(
                    f"[red]✗ Extraction failed:[/red]\n{error}",
                    title="Extract Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    finally:
        await client.disconnect()


def _format_heading_text(heading: Dict[str, Any]) -> str:
    """Format a single heading with indentation."""
    level = heading.get("level", 1)
    text = heading.get("text", "")[:80]
    indent = "  " * (level - 1)
    return f"{indent}[yellow]H{level}[/yellow] {text}"


def _format_landmark_text(landmark: Dict[str, Any]) -> str:
    """Format a single landmark with role and label."""
    label = landmark.get("label") or landmark.get("tag", "")
    role = landmark.get("role", "unknown")
    if label:
        return f"  [{role}] {label}"
    return f"  [{role}]"


def _format_link_text(link: Dict[str, Any]) -> str:
    """Format a single link with text or aria label."""
    text = link.get("text", "")[:60] or link.get("ariaLabel", "") or "[no text]"
    return f"  • {text}"


def _format_form_field(field: Dict[str, Any]) -> str:
    """Format a single form field with name, type, and label."""
    field_name = field.get("name") or field.get("id") or "[unnamed]"
    field_type = field.get("type", "text")
    label = field.get("label") or field.get("placeholder") or ""
    required = " *" if field.get("required") else ""
    return f"    - {field_name} ({field_type}){required}: {label[:30]}"


def _format_form_summary(form: Dict[str, Any]) -> str:
    """Format form header with name, method, and field count."""
    name = form.get("name") or form.get("id") or form.get("ariaLabel") or "[unnamed]"
    method = (form.get("method") or "GET").upper()
    fields = form.get("fields", [])
    return f"  [bold]{name}[/bold] ({method}, {len(fields)} fields)"


def _display_headings_section(headings: list[Dict[str, Any]]) -> None:
    """Display document outline section."""
    console.print("\n[bold cyan]📑 Document Outline[/bold cyan]")
    for heading in headings:
        console.print(_format_heading_text(heading))


def _display_landmarks_section(landmarks: list[Dict[str, Any]]) -> None:
    """Display page sections section."""
    console.print("\n[bold cyan]🏛️ Page Sections[/bold cyan]")
    for landmark in landmarks:
        console.print(_format_landmark_text(landmark))


def _display_links_section(links: list[Dict[str, Any]], max_display: int = 20) -> None:
    """Display links section with truncation."""
    console.print(f"\n[bold cyan]🔗 Links ({len(links)} total)[/bold cyan]")
    for link in links[:max_display]:
        console.print(_format_link_text(link))
    if len(links) > max_display:
        console.print(f"  [dim]... and {len(links) - max_display} more[/dim]")


def _display_forms_section(forms: list[Dict[str, Any]], max_fields: int = 5) -> None:
    """Display forms section with field details."""
    console.print(f"\n[bold cyan]📝 Forms ({len(forms)} total)[/bold cyan]")
    for form in forms:
        console.print(_format_form_summary(form))
        fields = form.get("fields", [])
        for field in fields[:max_fields]:
            console.print(_format_form_field(field))
        if len(fields) > max_fields:
            console.print(
                f"    [dim]... and {len(fields) - max_fields} more fields[/dim]"
            )


def _display_semantic_dom(
    dom: Dict[str, Any],
    show_headings: bool,
    show_landmarks: bool,
    show_links: bool,
    show_forms: bool,
) -> None:
    """Display semantic DOM in rich format."""
    console.print(
        Panel(
            f"[bold]{dom.get('title', 'Untitled')}[/bold]\n"
            f"[dim]{dom.get('url', '')}[/dim]",
            title="🔍 Semantic Structure",
            border_style="cyan",
        )
    )

    # Dispatch to section handlers
    section_handlers = {
        "headings": (show_headings, _display_headings_section),
        "landmarks": (show_landmarks, _display_landmarks_section),
        "links": (show_links, _display_links_section),
        "forms": (show_forms, _display_forms_section),
    }

    for key, (should_show, handler) in section_handlers.items():
        if should_show and dom.get(key):
            handler(dom[key])


@extract.command(name="selector")
@click.argument("selector")
@click.option("--port", default=None, type=int, help="WebSocket port")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@requires_server
def extract_selector(selector: str, port: int, json_output: bool):
    """Extract content from specific CSS selector.

    \b
    Examples:
      mcp-browser browser extract selector "h1"
      mcp-browser browser extract selector ".article-content"
      mcp-browser browser extract selector "#main" --json
    """
    asyncio.run(_extract_selector_command(selector, port, json_output))


async def _extract_selector_command(
    selector: str, port: Optional[int], json_output: bool
):
    """Execute selector extraction."""
    if port is None:
        console.print("[cyan]🔍 Searching for active server...[/cyan]")
        port = await find_active_port()
        if port is None:
            console.print(
                "[red]✗ No active server found. Start with: mcp-browser start[/red]"
            )
            sys.exit(1)
        console.print(f"[green]✓ Found server on port {port}[/green]\n")

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        console.print(f"[cyan]→ Extracting content from '{selector}'...[/cyan]")
        result = await client.extract_element(selector, timeout=10.0)

        if json_output:
            import json as json_module

            print(json_module.dumps(result, indent=2))
            return

        response = result.get("response", result)
        if response.get("success") or result.get("success"):
            element = response.get("element", response)
            console.print(
                Panel(
                    f"[bold]Selector:[/bold] {selector}\n\n"
                    f"[bold]Tag:[/bold] {element.get('tagName', 'unknown')}\n"
                    f"[bold]Text:[/bold] {(element.get('textContent', '') or element.get('innerText', ''))[:500]}",
                    title="📌 Element Content",
                    border_style="green",
                )
            )
        else:
            error = response.get("error", "Element not found or extraction failed")
            console.print(
                Panel(
                    f"[red]✗ Extraction failed:[/red]\n{error}",
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
@requires_server
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
@requires_server
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
    """Run interactive test session with command handler pattern.

    This refactored version uses:
    - Handler classes for each command (complexity reduction)
    - Helper functions for common operations
    - Dictionary-based command dispatch
    """
    # Display welcome message
    console.print(
        Panel(
            "[bold cyan]🧪 Interactive Browser Test Session[/bold cyan]\n\n"
            "Available commands:\n"
            "  [cyan]navigate <url>[/cyan]     - Navigate to URL\n"
            "  [cyan]click <selector>[/cyan]   - Click element\n"
            "  [cyan]fill <selector> <value>[/cyan] - Fill form field\n"
            "  [cyan]scroll <up|down> [px][/cyan] - Scroll page\n"
            "  [cyan]submit <selector>[/cyan] - Submit form\n"
            "  [cyan]extract <selector>[/cyan] - Extract content\n"
            "  [cyan]status[/cyan]            - Check server status\n"
            "  [cyan]help[/cyan]              - Show this help\n"
            "  [cyan]exit[/cyan]              - Exit session\n\n"
            "[dim]Type commands at the prompt. Use 'exit' or Ctrl+C to quit.[/dim]",
            title="Interactive Mode",
            border_style="cyan",
        )
    )

    # Initialize command handlers
    handlers = create_command_handlers()

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

                # Process command and check if should continue
                should_continue = await process_interactive_command(
                    command, handlers, client, port
                )
                if not should_continue:
                    break

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
                continue

    except Exception as e:
        console.print(f"[red]Error in interactive session: {e}[/red]")
    finally:
        await client.disconnect()
