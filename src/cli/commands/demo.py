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
            "  • Extracting page content\n"
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

    # Step 4: Content Extraction
    await _step_content_extraction(port)
    _wait_for_continue()

    # Step 5: DOM Interaction (if possible)
    await _step_dom_interaction(port)
    _wait_for_continue()

    # Step 6: Summary
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
        console.print(f"[green]✓ Server running on port {existing_port}[/green]")
        return True, existing_port


def _wait_for_continue():
    """Wait for user to press Enter to continue."""
    console.print("\n[dim][Press Enter to continue, or Ctrl+C to exit][/dim]", end="")
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
        f"  [bold cyan]Step {step_num} of {total}: {title}[/bold cyan]\n" + "━" * 60
    )


async def _step_verify_connection(port: int):
    """Step 1: Verify extension connection."""
    _print_step_header(1, 6, "Verify Connection")

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


async def _step_navigate(port: int) -> str:
    """Step 2: Navigate to demo page.

    Returns:
        The URL navigated to
    """
    _print_step_header(2, 6, "Navigate to Demo Page")

    console.print("\n[cyan]Choose a demo page to explore:[/cyan]\n")

    # Present URL choices
    console.print("  [1] httpbin.org/forms/post - Form with multiple inputs")
    console.print("  [2] the-internet.herokuapp.com - Interactive testing site")
    console.print("  [3] Enter your own URL")
    console.print("  [4] Stay on current page")

    choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"], default="1")

    url_map = {
        "1": "https://httpbin.org/forms/post",
        "2": "https://the-internet.herokuapp.com/",
    }

    if choice == "4":
        console.print("\n[cyan]Staying on current page[/cyan]")
        return None  # Stay on current page
    elif choice == "3":
        url = Prompt.ask("Enter URL to navigate to", default="https://example.com")
    else:
        url = url_map[choice]

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
            return url
        else:
            console.print(
                Panel(
                    f"[red]✗ Navigation failed:[/red]\n{result.get('error', 'Unknown error')}",
                    title="Navigation Error",
                    border_style="red",
                )
            )
            return None

    finally:
        await client.disconnect()


async def _step_console_logs(port: int):
    """Step 3: Console log capture demonstration."""
    _print_step_header(3, 6, "Console Log Capture")

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
            console.print(f"\n[green]✓ Captured {len(logs)} console logs[/green]")
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


async def _step_content_extraction(port: int):
    """Step 4: Content extraction demonstration."""
    _print_step_header(4, 6, "Content Extraction")

    console.print(
        "\n[cyan]MCP Browser can extract page content in multiple ways.[/cyan]\n"
    )

    # Present extraction mode choices
    console.print("Choose extraction mode:")
    console.print("  [1] Readable content - Main text/article (Readability)")
    console.print("  [2] Semantic DOM - Structure (headings, links, forms)")
    console.print("  [3] Both")
    console.print("  [4] Skip this step")

    choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"], default="1")

    if choice == "4":
        console.print("\n[dim]Skipping content extraction[/dim]")
        return

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        # Extract readable content
        if choice in ["1", "3"]:
            console.print("\n[cyan]→ Extracting readable content...[/cyan]")

            request_id = f"demo_extract_{int(time.time() * 1000)}"
            await client.websocket.send(
                json.dumps(
                    {
                        "type": "extract_content",
                        "requestId": request_id,
                    }
                )
            )

            # Wait for response
            try:
                for _ in range(5):
                    response = await asyncio.wait_for(
                        client.websocket.recv(), timeout=3.0
                    )
                    data = json.loads(response)

                    if data.get("type") in ("connection_ack", "server_info_response"):
                        continue

                    if data.get("type") == "content_extracted":
                        content = data.get("content", data)
                        title = content.get("title", "No title")
                        text = content.get("textContent", "")
                        excerpt = content.get("excerpt", "")

                        # Truncate text for display
                        display_text = excerpt if excerpt else text[:500]
                        if len(text) > 500 and not excerpt:
                            display_text += "..."

                        console.print(
                            Panel(
                                f"[bold]Title:[/bold] {title}\n\n"
                                f"[bold]Content:[/bold]\n{display_text}",
                                title="Readable Content",
                                border_style="green",
                            )
                        )
                        break
            except asyncio.TimeoutError:
                console.print(
                    "[yellow]⚠ Timeout waiting for content extraction[/yellow]"
                )

        # Extract semantic DOM
        if choice in ["2", "3"]:
            console.print("\n[cyan]→ Extracting semantic DOM...[/cyan]")

            request_id = f"demo_semantic_{int(time.time() * 1000)}"
            await client.websocket.send(
                json.dumps(
                    {
                        "type": "extract_semantic_dom",
                        "requestId": request_id,
                        "include_headings": True,
                        "include_links": True,
                        "include_forms": True,
                        "include_landmarks": True,
                    }
                )
            )

            # Wait for response
            try:
                for _ in range(5):
                    response = await asyncio.wait_for(
                        client.websocket.recv(), timeout=3.0
                    )
                    data = json.loads(response)

                    if data.get("type") in ("connection_ack", "server_info_response"):
                        continue

                    if data.get("type") == "semantic_dom_extracted":
                        semantic = data.get("semantic", data)
                        headings = semantic.get("headings", [])
                        links = semantic.get("links", [])
                        forms = semantic.get("forms", [])
                        landmarks = semantic.get("landmarks", [])

                        # Build summary
                        summary_parts = []
                        if headings:
                            summary_parts.append(
                                f"[cyan]Headings:[/cyan] {len(headings)}"
                            )
                        if links:
                            summary_parts.append(f"[cyan]Links:[/cyan] {len(links)}")
                        if forms:
                            summary_parts.append(f"[cyan]Forms:[/cyan] {len(forms)}")
                        if landmarks:
                            summary_parts.append(
                                f"[cyan]Landmarks:[/cyan] {len(landmarks)}"
                            )

                        # Show sample headings
                        headings_text = ""
                        if headings:
                            headings_text = "\n\n[bold]Sample Headings:[/bold]\n"
                            for h in headings[:5]:
                                level = h.get("level", "h1")
                                text = h.get("text", "")[:50]
                                headings_text += f"  {level}: {text}\n"

                        # Show sample links
                        links_text = ""
                        if links:
                            links_text = "\n[bold]Sample Links:[/bold]\n"
                            for link in links[:5]:
                                text = link.get("text", "")[:40]
                                href = link.get("href", "")[:40]
                                links_text += f"  {text} → {href}\n"

                        console.print(
                            Panel(
                                " • ".join(summary_parts) + headings_text + links_text,
                                title="Semantic DOM Structure",
                                border_style="blue",
                            )
                        )
                        break
            except asyncio.TimeoutError:
                console.print(
                    "[yellow]⚠ Timeout waiting for semantic DOM extraction[/yellow]"
                )

    finally:
        await client.disconnect()


async def _step_dom_interaction(port: int) -> Optional[str]:
    """Step 5: DOM interaction demonstration.

    Returns:
        The current URL if detected
    """
    _print_step_header(5, 6, "DOM Interaction")

    console.print("\n[cyan]MCP Browser can also interact with page elements.[/cyan]\n")

    console.print(
        Panel(
            "[bold]Available DOM Operations:[/bold]\n\n"
            "  • [cyan]Click elements[/cyan] - Click buttons, links, etc.\n"
            "  • [cyan]Fill forms[/cyan] - Enter text into input fields\n"
            "  • [cyan]Submit forms[/cyan] - Submit form data\n"
            "  • [cyan]Get element info[/cyan] - Retrieve element properties\n"
            "  • [cyan]Wait for elements[/cyan] - Wait for elements to appear\n"
            "  • [cyan]Select options[/cyan] - Choose from dropdown menus",
            title="DOM Control Features",
            border_style="blue",
        )
    )

    # Ask user if they want to try DOM interaction
    console.print("\n[cyan]Would you like to try a DOM interaction demo?[/cyan]")
    console.print("  [1] Yes - Demo form filling (httpbin forms)")
    console.print("  [2] Yes - Demo element inspection")
    console.print("  [3] No - Skip this step")

    choice = Prompt.ask("\nSelect option", choices=["1", "2", "3"], default="2")

    if choice == "3":
        console.print("\n[dim]Skipping DOM interaction[/dim]")
        return None

    client = BrowserClient(port=port)
    if not await client.connect():
        sys.exit(1)

    try:
        if choice == "1":
            # Demo form filling
            console.print("\n[cyan]→ Demonstrating form filling...[/cyan]")
            console.print(
                "[dim]Note: This works best on httpbin.org/forms/post[/dim]\n"
            )

            # Try to fill a form field
            request_id = f"demo_fill_{int(time.time() * 1000)}"
            await client.websocket.send(
                json.dumps(
                    {
                        "type": "fill_field",
                        "requestId": request_id,
                        "selector": 'input[name="custname"]',
                        "value": "MCP Browser Demo User",
                    }
                )
            )

            # Wait for response
            try:
                for _ in range(3):
                    response = await asyncio.wait_for(
                        client.websocket.recv(), timeout=2.0
                    )
                    data = json.loads(response)

                    if data.get("type") in ("connection_ack", "server_info_response"):
                        continue

                    if data.get("type") == "fill_result":
                        success = data.get("success", False)
                        if success:
                            console.print(
                                Panel(
                                    "[green]✓ Form field filled successfully![/green]\n\n"
                                    "Filled customer name field with 'MCP Browser Demo User'",
                                    title="Form Interaction",
                                    border_style="green",
                                )
                            )
                        else:
                            error = data.get("error", "Unknown error")
                            console.print(
                                f"[yellow]⚠ Could not fill form: {error}[/yellow]\n"
                                "[dim]Make sure you're on httpbin.org/forms/post[/dim]"
                            )
                        break
            except asyncio.TimeoutError:
                console.print(
                    "[yellow]⚠ Timeout waiting for form fill response[/yellow]"
                )

        else:
            # Demo element inspection
            console.print("\n[cyan]→ Inspecting page structure...[/cyan]")

            request_id = f"demo_element_{int(time.time() * 1000)}"
            await client.websocket.send(
                json.dumps(
                    {
                        "type": "get_element",
                        "requestId": request_id,
                        "selector": "h1",
                    }
                )
            )

            # Wait for response
            element_found = False
            try:
                for _ in range(3):
                    response = await asyncio.wait_for(
                        client.websocket.recv(), timeout=2.0
                    )
                    data = json.loads(response)

                    if data.get("type") in ("connection_ack", "server_info_response"):
                        continue

                    if data.get("type") == "element_info":
                        element_found = True
                        element_text = data.get("text", "")
                        tag_name = data.get("tagName", "h1")
                        console.print(
                            Panel(
                                f"[green]✓ Found page element![/green]\n\n"
                                f"Tag: [cyan]{tag_name}[/cyan]\n"
                                f"Text: [cyan]{element_text[:80]}[/cyan]",
                                title="Element Info",
                                border_style="green",
                            )
                        )
                        break
            except asyncio.TimeoutError:
                pass

            if not element_found:
                console.print("[yellow]⚠ No h1 element found on current page[/yellow]")

    finally:
        await client.disconnect()

    return None


def _show_summary():
    """Step 6: Show summary and next steps."""
    _print_step_header(6, 6, "Demo Complete!")

    console.print(
        Panel.fit(
            "[bold green]🎉 Congratulations![/bold green]\n\n"
            "You've completed the MCP Browser interactive demo!\n\n"
            "[bold]What you learned:[/bold]\n"
            "  ✓ Verifying server and extension connection\n"
            "  ✓ Navigating to web pages programmatically\n"
            "  ✓ Capturing and viewing console logs\n"
            "  ✓ Extracting page content (readable & semantic)\n"
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
