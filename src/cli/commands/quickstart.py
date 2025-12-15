"""Quickstart command implementation."""

import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

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


def get_playwright_cache_dir():
    """Get Playwright browser cache directory.

    Returns:
        Path to Playwright cache, or None if not found
    """
    if sys.platform == "darwin" or sys.platform == "linux":
        cache_dir = Path.home() / ".cache" / "ms-playwright"
    elif sys.platform == "win32":
        import os

        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            cache_dir = Path(local_appdata) / "ms-playwright"
        else:
            return None
    else:
        return None

    if cache_dir.exists() and cache_dir.is_dir():
        return cache_dir

    return None


def get_directory_size_mb(path: Path) -> float:
    """Get directory size in megabytes."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except (OSError, PermissionError):
        pass
    return total / (1024 * 1024)


@click.command()
@click.pass_context
def quickstart(ctx):
    """🚀 Interactive setup wizard for first-time users.

    \b
    This wizard will:
      1. Check system requirements
      2. Clean up legacy Playwright cache (if present)
      3. Create necessary directories
      4. Initialize the Chrome extension
      5. Configure MCP settings
      6. Start the server

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

    # Step 2: Clean up Playwright cache (no longer needed)
    console.print("\n[bold]Step 2: Checking for legacy Playwright cache...[/bold]")

    playwright_cache = get_playwright_cache_dir()
    if playwright_cache:
        cache_size_mb = get_directory_size_mb(playwright_cache)
        console.print(
            f"  [yellow]⚠[/yellow] Found Playwright browser cache: {playwright_cache}"
        )
        console.print(f"  [dim]Size: {cache_size_mb:.1f} MB[/dim]")
        console.print(
            "\n  [dim]Note: Playwright is no longer used by mcp-browser (removed in v2.2.29[/dim]"
        )
        console.print(
            "  [dim]to fix a critical memory leak). This cache can be safely removed.[/dim]"
        )

        if Confirm.ask("\n  Remove Playwright cache to free disk space?", default=True):
            try:
                shutil.rmtree(playwright_cache)
                console.print(
                    f"  [green]✓[/green] Removed {cache_size_mb:.1f} MB of Playwright cache"
                )
            except (OSError, PermissionError) as e:
                console.print(f"  [red]✗[/red] Could not remove cache: {e}")
        else:
            console.print("  [dim]Skipping Playwright cache cleanup[/dim]")
    else:
        console.print("  [green]✓[/green] No Playwright cache found (clean install)")

    # Step 3: Create directories
    console.print("\n[bold]Step 3: Creating directories...[/bold]")

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

    # Step 4: Initialize extension
    console.print("\n[bold]Step 4: Setting up Chrome extension...[/bold]")

    use_local = Confirm.ask(
        "\nInitialize extension in current directory? (recommended for projects)"
    )

    if use_local:
        asyncio.run(init_project_extension_interactive())
    else:
        console.print(
            "[dim]Skipping local extension setup. You can run 'mcp-browser init' later.[/dim]"
        )

    # Step 5: Configure settings
    console.print("\n[bold]Step 5: Configuring settings...[/bold]")

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

    # Step 6: Start server
    console.print("\n[bold]Step 6: Starting the server...[/bold]")

    if Confirm.ask("\nStart the MCP Browser server now?"):
        console.print("\n[green]✨ Setup complete![/green]")
        console.print("\nStarting server...")
        console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")

        # Import here to avoid circular dependency
        from ...cli.main import BrowserMCPServer

        # Start the server
        config = ctx.obj.get("config")
        server = BrowserMCPServer(config=config, mcp_mode=False)

        try:
            asyncio.run(server.run_server())
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped by user[/yellow]")
    else:
        console.print("\n[green]✨ Setup complete![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run [cyan]mcp-browser start[/cyan] to start the server")
        console.print("  2. Load Chrome extension from mcp-browser-extensions/chrome/")
        console.print("  3. Configure Claude Code to use MCP Browser")
