"""Doctor command implementation."""

import asyncio
import json
import subprocess
import sys

import click
from rich.panel import Panel

from ..utils import (
    CONFIG_FILE,
    DATA_DIR,
    check_installation_status,
    check_system_requirements,
    console,
)
from .init import init_project_extension


def create_default_config():
    """Create default configuration file."""
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


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to fix issues automatically")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed diagnostic information"
)
def doctor(ctx):
    """🩺 Diagnose and fix common MCP Browser issues.

    \b
    Performs comprehensive system checks:
      • System requirements (Python, Chrome, Node.js)
      • Port availability (8875-8895)
      • Directory permissions
      • Extension installation
      • Configuration validity
      • Server connectivity

    \b
    Examples:
      mcp-browser doctor         # Run diagnostic
      mcp-browser doctor --fix   # Auto-fix issues
      mcp-browser doctor -v      # Verbose output

    \b
    Common issues and solutions:
      • "Port in use" - Another process using ports 8875-8895
      • "Extension not found" - Run 'mcp-browser init'
      • "Chrome not detected" - Install Chrome or Chromium
      • "Permission denied" - Check directory permissions
    """
    console.print(
        Panel.fit(
            "[bold cyan]🩺 MCP Browser Diagnostic Tool[/bold cyan]\n\n"
            "Running comprehensive system checks...",
            title="Doctor",
            border_style="cyan",
        )
    )

    issues_found = []
    fixes_available = []

    # System requirements
    console.print("\n[bold]Checking system requirements...[/bold]")
    checks = asyncio.run(check_system_requirements())

    for name, ok, details in checks:
        if not ok and "optional" not in name.lower():
            issues_found.append(f"{name}: {details}")
            if name == "Playwright":
                fixes_available.append(
                    (
                        "Install Playwright browsers",
                        lambda: subprocess.run(
                            [sys.executable, "-m", "playwright", "install"]
                        ),
                    )
                )

    # Installation status
    console.print("\n[bold]Checking installation...[/bold]")
    status = asyncio.run(check_installation_status())

    if not status["config_exists"]:
        issues_found.append("Configuration file missing")
        fixes_available.append(("Create default configuration", create_default_config))

    if not status["extension_initialized"]:
        issues_found.append("Chrome extension not initialized")
        fixes_available.append(
            ("Initialize extension", lambda: asyncio.run(init_project_extension()))
        )

    if not status["data_dir_exists"]:
        issues_found.append("Data directory missing")
        fixes_available.append(
            (
                "Create data directory",
                lambda: DATA_DIR.mkdir(parents=True, exist_ok=True),
            )
        )

    # Show results
    console.print("\n" + "=" * 50)

    if not issues_found:
        console.print("\n[bold green]✅ All checks passed![/bold green]")
        console.print("\nYour MCP Browser installation is healthy.")
    else:
        console.print(
            f"\n[bold yellow]⚠ Found {len(issues_found)} issue(s):[/bold yellow]"
        )
        for issue in issues_found:
            console.print(f"  • {issue}")

        if ctx.params.get("fix") and fixes_available:
            console.print(
                f"\n[bold]Attempting to fix {len(fixes_available)} issue(s)...[/bold]"
            )
            for desc, fix_func in fixes_available:
                try:
                    console.print(f"  Fixing: {desc}...")
                    fix_func()
                    console.print("    [green]✓[/green] Fixed")
                except Exception as e:
                    console.print(f"    [red]✗[/red] Failed: {e}")
        elif fixes_available:
            console.print(
                "\n[dim]Run 'mcp-browser doctor --fix' to attempt automatic fixes[/dim]"
            )
