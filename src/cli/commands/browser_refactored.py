"""Refactored interactive command handlers for browser.py."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from ..utils.browser_client import BrowserClient

console = Console()

if TYPE_CHECKING:
    KwargsDict = Dict[str, Any]


def display_skeletal_dom(skeletal_data: Dict[str, Any]) -> None:
    """Display skeletal DOM in a readable format.

    Args:
        skeletal_data: Skeletal DOM data from browser (may be wrapped in response)
    """
    # Unwrap nested response structure if present
    # Response format: {type: "dom_command_response", requestId: "...", response: {success, skeletal_dom}}
    if "response" in skeletal_data and isinstance(skeletal_data["response"], dict):
        skeletal_data = skeletal_data["response"]

    if not skeletal_data.get("success"):
        console.print(
            f"[yellow]⚠ Could not fetch page structure: {skeletal_data.get('error', 'Unknown error')}[/yellow]"
        )
        return

    dom = skeletal_data.get("skeletal_dom", {})
    if not dom:
        console.print("[yellow]⚠ No page structure data available[/yellow]")
        return

    # Create tree structure
    tree = Tree(f"[bold blue]📄 {dom.get('title', 'Untitled Page')}[/bold blue]")
    tree.add(f"[dim]🔗 {dom.get('url', 'Unknown URL')}[/dim]")

    # Add headings
    headings = dom.get("headings", [])
    if headings:
        heading_node = tree.add("[bold cyan]Headings[/bold cyan]")
        for h in headings:
            heading_node.add(f"[{h['level']}] {h['text']}")

    # Add inputs
    inputs = dom.get("inputs", [])
    if inputs:
        input_node = tree.add("[bold green]Input Fields[/bold green]")
        for inp in inputs:
            input_label = (
                inp.get("placeholder")
                or inp.get("name")
                or inp.get("id")
                or "(unnamed)"
            )
            input_node.add(f"[{inp['type']}] {input_label}")

    # Add buttons
    buttons = dom.get("buttons", [])
    if buttons:
        button_node = tree.add("[bold yellow]Buttons[/bold yellow]")
        for btn in buttons:
            button_node.add(f"[{btn['type']}] {btn['text']}")

    # Add links
    links = dom.get("links", [])
    if links:
        link_node = tree.add(
            f"[bold magenta]Links (showing {len(links)})[/bold magenta]"
        )
        for link in links[:5]:  # Show first 5
            link_node.add(f"{link['text']} → [dim]{link['href']}[/dim]")
        if len(links) > 5:
            link_node.add(f"[dim]... and {len(links) - 5} more[/dim]")

    console.print(Panel(tree, title="[bold]Page Structure[/bold]", border_style="blue"))


# Interactive Command Handlers
class InteractiveCommandHandler:
    """Base handler for interactive commands."""

    async def validate(self, parts: List[str]) -> Optional[str]:
        """Validate command arguments.

        Args:
            parts: Command parts (including command name)

        Returns:
            Error message if invalid, None if valid
        """
        return None

    async def execute(self, client: BrowserClient, parts: List[str]) -> Dict[str, Any]:
        """Execute the command.

        Args:
            client: BrowserClient instance
            parts: Command parts (including command name)

        Returns:
            Result dictionary
        """
        raise NotImplementedError

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        """Display command result.

        Args:
            result: Result dictionary from execute
            kwargs: Additional display parameters
        """
        if result["success"]:
            console.print("[green]✓ Command successful[/green]")
        else:
            console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


class NavigateHandler(InteractiveCommandHandler):
    """Handler for navigate command."""

    async def validate(self, parts: List[str]) -> Optional[str]:
        if len(parts) < 2:
            return "Usage: navigate <url>"
        return None

    async def execute(self, client: BrowserClient, parts: List[str]) -> Dict[str, Any]:
        url = parts[1]
        result = await client.navigate(url, wait=0)

        # Wait briefly for page to load, then verify URL and fetch skeletal DOM
        if result.get("success"):
            import asyncio

            await asyncio.sleep(1.5)  # Give page time to load

            # Verify actual URL matches expected
            tab_info = await client.get_tab_info(timeout=5.0)
            if tab_info.get("success"):
                result["verified_url"] = tab_info.get("url")
                result["page_title"] = tab_info.get("title")
                result["page_status"] = tab_info.get("status")
            else:
                result["verified_url"] = None
                result["verification_error"] = tab_info.get("error")

            result["skeletal_dom"] = await client.get_skeletal_dom()

        return result

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        url = parts[1] if len(parts) > 1 else "unknown"
        if result["success"]:
            verified_url = result.get("verified_url")
            page_title = result.get("page_title")

            if verified_url:
                console.print(f"[green]✓ Browser confirmed at:[/green] {verified_url}")
                if page_title:
                    console.print(f"[dim]  Title: {page_title}[/dim]")
            else:
                console.print(f"[yellow]✓ Navigation sent to {url}[/yellow]")
                if result.get("verification_error"):
                    console.print(
                        f"[dim]  (URL verification unavailable: {result.get('verification_error')})[/dim]"
                    )

            # Display skeletal DOM if available
            skeletal_dom = result.get("skeletal_dom")
            if skeletal_dom:
                display_skeletal_dom(skeletal_dom)
        else:
            console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


class ClickHandler(InteractiveCommandHandler):
    """Handler for click command."""

    async def validate(self, parts: List[str]) -> Optional[str]:
        if len(parts) < 2:
            return "Usage: click <selector>"
        return None

    async def execute(self, client: BrowserClient, parts: List[str]) -> Dict[str, Any]:
        selector = parts[1]
        result = await client.click_element(selector)

        # Wait briefly for any page changes, then fetch skeletal DOM
        if result.get("success"):
            import asyncio

            await asyncio.sleep(0.8)  # Give time for page updates
            result["skeletal_dom"] = await client.get_skeletal_dom()

        return result

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        selector = parts[1] if len(parts) > 1 else "unknown"
        if result["success"]:
            console.print(f"[green]✓ Clicked {selector}[/green]")

            # Display skeletal DOM if available
            skeletal_dom = result.get("skeletal_dom")
            if skeletal_dom:
                display_skeletal_dom(skeletal_dom)
        else:
            console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


class FillHandler(InteractiveCommandHandler):
    """Handler for fill command."""

    async def validate(self, parts: List[str]) -> Optional[str]:
        if len(parts) < 3:
            return "Usage: fill <selector> <value>"
        return None

    async def execute(self, client: BrowserClient, parts: List[str]) -> Dict[str, Any]:
        selector = parts[1]
        value = " ".join(parts[2:])
        result = await client.fill_field(selector, value)

        # Wait briefly, then fetch skeletal DOM to show current state
        if result.get("success"):
            import asyncio

            await asyncio.sleep(0.5)
            result["skeletal_dom"] = await client.get_skeletal_dom()

        return result

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        selector = parts[1] if len(parts) > 1 else "unknown"
        value = " ".join(parts[2:]) if len(parts) > 2 else ""
        if result["success"]:
            console.print(f"[green]✓ Filled {selector} with '{value}'[/green]")

            # Display skeletal DOM if available
            skeletal_dom = result.get("skeletal_dom")
            if skeletal_dom:
                display_skeletal_dom(skeletal_dom)
        else:
            console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


class ScrollHandler(InteractiveCommandHandler):
    """Handler for scroll command."""

    async def validate(self, parts: List[str]) -> Optional[str]:
        if len(parts) >= 2 and parts[1].lower() not in ["up", "down"]:
            return "Direction must be 'up' or 'down'"
        if len(parts) >= 3:
            try:
                int(parts[2])
            except ValueError:
                return "Amount must be a number"
        return None

    async def execute(self, client: BrowserClient, parts: List[str]) -> Dict[str, Any]:
        direction = parts[1].lower() if len(parts) >= 2 else "down"
        amount = int(parts[2]) if len(parts) >= 3 else 500
        return await client.scroll(direction, amount)

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        direction = parts[1].lower() if len(parts) >= 2 else "down"
        amount = int(parts[2]) if len(parts) >= 3 else 500
        if result["success"]:
            console.print(f"[green]✓ Scrolled {direction} by {amount}px[/green]")
        else:
            console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


class SubmitHandler(InteractiveCommandHandler):
    """Handler for submit command."""

    async def validate(self, parts: List[str]) -> Optional[str]:
        if len(parts) < 2:
            return "Usage: submit <selector>"
        return None

    async def execute(self, client: BrowserClient, parts: List[str]) -> Dict[str, Any]:
        selector = parts[1]
        return await client.submit_form(selector)

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        selector = parts[1] if len(parts) > 1 else "unknown"
        if result["success"]:
            console.print(f"[green]✓ Submitted form {selector}[/green]")
        else:
            console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


class ExtractHandler(InteractiveCommandHandler):
    """Handler for extract command."""

    async def validate(self, parts: List[str]) -> Optional[str]:
        if len(parts) < 2:
            return "Usage: extract <selector>"
        return None

    async def execute(self, client: BrowserClient, parts: List[str]) -> Dict[str, Any]:
        selector = parts[1]
        return await client.extract_content(selector)

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        selector = parts[1] if len(parts) > 1 else "unknown"
        if result["success"]:
            console.print(f"[green]✓ Extracted content from {selector}[/green]")
        else:
            console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


# Helper functions
async def handle_status_command(client: BrowserClient, port: int) -> None:
    """Handle status command in interactive mode."""
    status = await client.check_server_status()
    table = Table(title="Server Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Status", status.get("status", "unknown"))
    table.add_row("Port", str(port))
    console.print(table)


def display_interactive_help() -> None:
    """Display help text for interactive mode."""
    console.print(
        "\n[bold]Available Commands:[/bold]\n"
        "  navigate <url>           Navigate to URL\n"
        "  click <selector>         Click element\n"
        "  fill <selector> <value>  Fill form field\n"
        "  scroll <up|down> [px]    Scroll page\n"
        "  submit <selector>        Submit form\n"
        "  extract <selector>       Extract content\n"
        "  status                   Check server status\n"
        "  help                     Show this help\n"
        "  exit                     Exit session\n"
    )


def create_command_handlers() -> Dict[str, InteractiveCommandHandler]:
    """Create and return dictionary of command handlers."""
    return {
        "navigate": NavigateHandler(),
        "click": ClickHandler(),
        "fill": FillHandler(),
        "scroll": ScrollHandler(),
        "submit": SubmitHandler(),
        "extract": ExtractHandler(),
    }


async def process_interactive_command(
    command: str,
    handlers: Dict[str, InteractiveCommandHandler],
    client: BrowserClient,
    port: int,
) -> bool:
    """Process a single interactive command.

    Args:
        command: User input command
        handlers: Dictionary of command handlers
        client: BrowserClient instance
        port: Server port number

    Returns:
        True if should continue loop, False if should exit
    """
    if not command or command.strip() == "":
        return True

    parts = command.strip().split()
    cmd = parts[0].lower()

    # Handle exit commands
    if cmd in ("exit", "quit"):
        console.print("[yellow]Exiting interactive session...[/yellow]")
        return False

    # Handle help command
    if cmd == "help":
        display_interactive_help()
        return True

    # Handle status command
    if cmd == "status":
        await handle_status_command(client, port)
        return True

    # Handle commands with registered handlers
    if cmd in handlers:
        handler = handlers[cmd]

        # Validate command
        error = await handler.validate(parts)
        if error:
            console.print(f"[red]{error}[/red]")
            return True

        # Execute command
        result = await handler.execute(client, parts)

        # Display result
        handler.display_result(result, parts=parts)
    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")
        console.print("[dim]Type 'help' for available commands[/dim]")

    return True
