"""Quickstart command implementation."""

import asyncio
import json
import subprocess
import sys

import click
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

from ..utils import (
    CONFIG_FILE,
    DATA_DIR,
    HOME_DIR,
    LOG_DIR,
    check_system_requirements,
    console,
)
from .init import init_project_extension_interactive


@click.command()
@click.pass_context
def quickstart(ctx):
    """🚀 Interactive setup wizard for first-time users.

    \b
    This wizard will:
      1. Check system requirements
      2. Create necessary directories
      3. Initialize the Chrome extension
      4. Configure MCP settings
      5. Start the server
      6. Help you install the Chrome extension

    Perfect for getting started quickly without reading documentation!
    """
    console.print(
        Panel.fit(
            "[bold cyan]🚀 MCP Browser Quick Start Wizard[/bold cyan]\n\n"
            "This wizard will help you set up MCP Browser in just a few steps.",
            title="Welcome",
            border_style="cyan",
        )
    )

    # Step 1: Check requirements
    console.print("\n[bold]Step 1: Checking system requirements...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Checking...", total=None)
        checks = asyncio.run(check_system_requirements())

    table = Table(title="System Requirements", show_header=True)
    table.add_column("Requirement", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    all_ok = True
    for name, ok, details in checks:
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        table.add_row(name, status, details)
        if not ok and "optional" not in name.lower():
            all_ok = False

    console.print(table)

    if not all_ok:
        if not Confirm.ask(
            "\n[yellow]Some requirements are missing. Continue anyway?[/yellow]"
        ):
            console.print("[red]Setup cancelled.[/red]")
            return

    # Step 2: Create directories
    console.print("\n[bold]Step 2: Creating directories...[/bold]")

    dirs_to_create = [
        (HOME_DIR / "config", "Configuration"),
        (DATA_DIR, "Data storage"),
        (LOG_DIR, "Logs"),
    ]

    for dir_path, desc in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"  [green]✓[/green] Created {desc}: {dir_path}")
        else:
            console.print(f"  [dim]✓ {desc} exists: {dir_path}[/dim]")

    # Step 3: Initialize extension
    console.print("\n[bold]Step 3: Setting up Chrome extension...[/bold]")

    use_local = Confirm.ask(
        "\nInitialize extension in current directory? (recommended for projects)"
    )

    if use_local:
        asyncio.run(init_project_extension_interactive())
    else:
        console.print(
            "[dim]Skipping local extension setup. You can run 'mcp-browser init' later.[/dim]"
        )

    # Step 4: Configure settings
    console.print("\n[bold]Step 4: Configuring settings...[/bold]")

    if not CONFIG_FILE.exists():
        default_config = {
            "storage": {
                "base_path": str(DATA_DIR),
                "max_file_size_mb": 50,
                "retention_days": 7,
            },
            "websocket": {"port_range": [8875, 8895], "host": "localhost"},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }

        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=2)
        console.print("  [green]✓[/green] Created default configuration")
    else:
        console.print("  [dim]✓ Configuration exists[/dim]")

    # Step 5: Install Playwright browsers if needed
    console.print("\n[bold]Step 5: Setting up Playwright (for screenshots)...[/bold]")

    try:
        import importlib.util

        playwright_spec = importlib.util.find_spec("playwright")
        if playwright_spec is None:
            raise ImportError("playwright not found")

        if Confirm.ask("\nInstall Playwright browsers for screenshot support?"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task("Installing Playwright browsers...", total=None)
                subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    check=True,
                )
            console.print("  [green]✓[/green] Playwright browsers installed")
    except ImportError:
        console.print(
            "  [yellow]⚠[/yellow] Playwright not installed (screenshots won't work)"
        )
    except Exception as e:
        console.print(
            f"  [yellow]⚠[/yellow] Could not install Playwright browsers: {e}"
        )

    # Step 6: Start server
    console.print("\n[bold]Step 6: Starting the server...[/bold]")

    if Confirm.ask("\nStart the MCP Browser server now?"):
        console.print("\n[green]✨ Setup complete![/green]")
        console.print("\nStarting server with dashboard...")
        console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")

        # Import here to avoid circular dependency
        from ...cli.main import BrowserMCPServer

        # Start the server
        config = ctx.obj.get("config")
        server = BrowserMCPServer(config=config, mcp_mode=False)

        try:
            asyncio.run(server.run_server_with_dashboard())
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped by user[/yellow]")
    else:
        console.print("\n[green]✨ Setup complete![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run [cyan]mcp-browser start[/cyan] to start the server")
        console.print(
            "  2. Open [link=http://localhost:8080]http://localhost:8080[/link] in your browser"
        )
        console.print("  3. Install the Chrome extension from the dashboard")
        console.print("  4. Configure Claude Code to use MCP Browser")
