"""Stop command implementation."""

import click
from rich.panel import Panel

from ..utils import console
from ..utils.daemon import get_server_status, stop_daemon


@click.command()
def stop():
    """🛑 Stop the MCP Browser server for the current project.

    \b
    Stops the background server running for the current directory.
    The server will be gracefully shut down and removed from the registry.

    \b
    Examples:
      mcp-browser stop            # Stop server for current project

    \b
    Notes:
      • Each project can have its own server instance
      • Only stops the server for the current directory
      • Use 'mcp-browser status' to verify server is stopped

    \b
    Troubleshooting:
      • Server not found: No server running for this project
      • Permission denied: Check process ownership
      • Use 'mcp-browser doctor' to diagnose issues
    """
    # Check if server is running for this project
    is_running, pid, port = get_server_status()

    if not is_running:
        console.print(
            Panel.fit(
                "[yellow]No server running for current project[/yellow]\n\n"
                "The server is not currently running in this directory.\n\n"
                "[dim]Tip: Use 'mcp-browser status' to check server status[/dim]",
                title="Server Not Running",
                border_style="yellow",
            )
        )
        return

    # Show current server info
    console.print(
        Panel.fit(
            f"[bold yellow]Stopping MCP Browser Server[/bold yellow]\n\n"
            f"PID: {pid}\n"
            f"Port: {port}",
            title="Server Shutdown",
            border_style="yellow",
        )
    )

    # Stop the daemon
    success = stop_daemon()

    if success:
        console.print(
            Panel.fit(
                "[bold green]✓ Server stopped successfully[/bold green]\n\n"
                f"The server (PID {pid}) has been shut down.\n\n"
                "[dim]Tip: Use 'mcp-browser start' to restart the server[/dim]",
                title="Shutdown Complete",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel.fit(
                "[bold red]✗ Failed to stop server[/bold red]\n\n"
                f"Could not shut down server (PID {pid}).\n\n"
                "[dim]Try: Check process permissions or use 'mcp-browser doctor --fix'[/dim]",
                title="Shutdown Failed",
                border_style="red",
            )
        )
