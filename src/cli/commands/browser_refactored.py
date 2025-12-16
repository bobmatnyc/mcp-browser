"""Refactored interactive command handlers for browser.py."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from ..utils.browser_client import BrowserClient

console = Console()

if TYPE_CHECKING:
    KwargsDict = Dict[str, Any]


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
        return await client.navigate(url, wait=0)

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        url = parts[1] if len(parts) > 1 else "unknown"
        if result["success"]:
            console.print(f"[green]✓ Navigated to {url}[/green]")
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
        return await client.click_element(selector)

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        selector = parts[1] if len(parts) > 1 else "unknown"
        if result["success"]:
            console.print(f"[green]✓ Clicked {selector}[/green]")
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
        return await client.fill_field(selector, value)

    def display_result(self, result: Dict[str, Any], **kwargs: Any) -> None:
        parts = kwargs.get("parts", [])
        selector = parts[1] if len(parts) > 1 else "unknown"
        value = " ".join(parts[2:]) if len(parts) > 2 else ""
        if result["success"]:
            console.print(f"[green]✓ Filled {selector} with '{value}'[/green]")
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
