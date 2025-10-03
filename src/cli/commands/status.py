"""Status command implementation."""

import asyncio

import click
from rich.table import Table

from ..utils import check_installation_status, console


@click.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="Output format",
)
@click.pass_context
def status(ctx, format):
    """📊 Show current server and installation status.

    \b
    Displays comprehensive information about:
      • Server running status
      • WebSocket connections
      • Chrome extension status
      • Storage statistics
      • Recent console logs
      • System configuration

    \b
    Examples:
      mcp-browser status          # Table format (default)
      mcp-browser status --json   # JSON output
      mcp-browser status -f simple # Simple text output
    """
    status_info = asyncio.run(check_installation_status())

    if format == "json":
        console.print_json(data=status_info)
    elif format == "simple":
        for key, value in status_info.items():
            console.print(f"{key}: {value}")
    else:
        # Table format
        table = Table(title="MCP Browser Status", show_header=False)
        table.add_column("Component", style="cyan", width=30)
        table.add_column("Status", width=50)

        # Package
        table.add_row(
            "Package",
            (
                "[green]✓ Installed[/green]"
                if status_info["package_installed"]
                else "[red]✗ Not installed[/red]"
            ),
        )

        # Configuration
        table.add_row(
            "Configuration",
            (
                "[green]✓ Configured[/green]"
                if status_info["config_exists"]
                else "[yellow]⚠ Not configured[/yellow]"
            ),
        )

        # Extension
        ext_status = (
            "[green]✓ Initialized[/green]"
            if status_info["extension_initialized"]
            else "[yellow]⚠ Not initialized[/yellow]"
        )
        table.add_row("Extension", ext_status)

        # Server
        if status_info["server_running"]:
            server_status = f"[green]✓ Running on port {status_info.get('server_port', 'unknown')}[/green]"
        else:
            server_status = "[dim]○ Not running[/dim]"
        table.add_row("Server", server_status)

        # Data directories
        table.add_row(
            "Data Directory",
            (
                "[green]✓ Created[/green]"
                if status_info["data_dir_exists"]
                else "[yellow]⚠ Not created[/yellow]"
            ),
        )

        table.add_row(
            "Logs Directory",
            (
                "[green]✓ Created[/green]"
                if status_info["logs_dir_exists"]
                else "[yellow]⚠ Not created[/yellow]"
            ),
        )

        console.print(table)

        # Show tips if not everything is set up
        if not all(
            [status_info["config_exists"], status_info["extension_initialized"]]
        ):
            console.print(
                "\n[yellow]💡 Tip:[/yellow] Run [cyan]mcp-browser quickstart[/cyan] for guided setup"
            )
