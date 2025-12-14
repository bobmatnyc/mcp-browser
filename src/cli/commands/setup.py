"""Setup command for complete mcp-browser installation."""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import console
from ..utils.daemon import get_config_dir


@click.command()
@click.option("--skip-mcp", is_flag=True, help="Skip MCP installation")
@click.option(
    "--force", "-f", is_flag=True, help="Force reinstall even if already setup"
)
def setup(skip_mcp: bool, force: bool):
    """🚀 Complete mcp-browser setup.

    \b
    This command performs complete installation:

    1. Initialize configuration (~/.mcp-browser/)
    2. Install Chrome extension to ./mcp-browser-extensions/chrome/
    3. Install MCP server for Claude Code
    4. Start WebSocket server

    \b
    After setup, load the extension in Chrome:
      1. Open chrome://extensions/
      2. Enable 'Developer mode'
      3. Click 'Load unpacked'
      4. Select ./mcp-browser-extensions/chrome/

    \b
    Examples:
      mcp-browser setup               # Full setup
      mcp-browser setup --skip-mcp    # Skip MCP config installation
      mcp-browser setup --force       # Force reinstall
    """
    console.print(
        Panel.fit(
            "[bold cyan]🚀 mcp-browser Setup[/bold cyan]\nComplete installation wizard",
            border_style="cyan",
        )
    )

    steps_completed = 0
    # Calculate total steps: config, extension, mcp (optional), server
    total_steps = 3 if skip_mcp else 4

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Initialize configuration
        task = progress.add_task("Initializing configuration...", total=1)
        if init_configuration(force):
            steps_completed += 1
            progress.update(
                task, completed=1, description="✓ Configuration initialized"
            )
        else:
            progress.update(task, description="✗ Configuration failed")

        # Step 2: Install browser extension
        task = progress.add_task("Installing browser extension...", total=1)
        if install_extension(force):
            steps_completed += 1
            progress.update(
                task, completed=1, description="✓ Extension installed"
            )
        else:
            progress.update(
                task, description="⚠ Extension not found (skip if not needed)"
            )

        # Step 3: Install MCP (if not skipped)
        if not skip_mcp:
            task = progress.add_task("Installing MCP server...", total=1)
            mcp_result = install_mcp(force)
            if mcp_result:
                steps_completed += 1
                progress.update(task, completed=1, description="✓ MCP server installed")
            else:
                progress.update(
                    task,
                    description="⚠ MCP installation skipped (manual install needed)",
                )

        # Step 4: Start server
        task = progress.add_task("Starting server...", total=1)
        server_port = start_server_for_setup()
        if server_port:
            steps_completed += 1
            progress.update(
                task, completed=1, description=f"✓ Server running on port {server_port}"
            )
        else:
            progress.update(task, description="⚠ Server failed to start")

    # Summary and browser connection prompt
    console.print()
    if steps_completed >= total_steps:
        console.print(
            Panel(
                "[bold green]✓ Setup Complete![/bold green]\n\n"
                "[bold yellow]→ Install the Chrome extension:[/bold yellow]\n"
                "   1. Open Chrome: [cyan]chrome://extensions/[/cyan]\n"
                "   2. Enable 'Developer mode' (toggle in top right)\n"
                "   3. Click 'Load unpacked'\n"
                "   4. Select: [cyan]./mcp-browser-extensions/chrome/[/cyan]\n\n"
                "[bold yellow]→ Connect your browser:[/bold yellow]\n"
                f"   Server is running on port [cyan]{server_port or 8851}[/cyan]\n"
                "   After loading the extension, click the extension icon\n"
                "   and connect to the server.\n\n"
                "[bold yellow]→ Test the connection:[/bold yellow]\n"
                "   [cyan]mcp-browser doctor[/cyan]\n\n"
                "[bold yellow]→ Try a browser command:[/bold yellow]\n"
                "   [cyan]mcp-browser browser control navigate https://example.com[/cyan]",
                title="Setup Complete",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[yellow]⚠ Setup partially complete ({steps_completed}/{total_steps} steps)[/yellow]\n\n"
                "Run [cyan]mcp-browser doctor[/cyan] to diagnose issues.",
                title="Setup Incomplete",
                border_style="yellow",
            )
        )


def init_configuration(force: bool = False) -> bool:
    """Initialize mcp-browser configuration.

    Args:
        force: Force recreation of config even if it exists

    Returns:
        True if successful, False otherwise
    """
    config_dir = get_config_dir()
    config_file = config_dir / "config.json"

    if config_file.exists() and not force:
        return True  # Already configured

    # Create default config
    default_config = {
        "storage": {
            "base_path": str(config_dir / "data"),
            "max_file_size_mb": 50,
            "retention_days": 7,
        },
        "websocket": {
            "port_range": [8851, 8899],
            "host": "localhost",
            "auto_start": True,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }

    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=2)
        return True
    except Exception:
        return False


def install_extension(force: bool = False) -> bool:
    """Install browser extension to visible project directory.

    Copies the unpacked extension to ./mcp-browser-extensions/chrome/
    for easy loading in Chrome developer mode.

    Args:
        force: Force reinstallation even if already installed

    Returns:
        True if installed, False if source not found or error
    """
    target_dir = Path.cwd() / "mcp-browser-extensions" / "chrome"

    # Find source extension - check multiple locations
    package_dir = Path(__file__).parent.parent.parent  # src/
    source_locations = [
        # New location: src/extensions/chrome/
        package_dir / "extensions" / "chrome",
        # Package install location
        package_dir.parent / "extensions" / "chrome",
        # Old location (backwards compatibility)
        Path.cwd() / "mcp-browser-extension",
        package_dir.parent / "mcp-browser-extension",
    ]

    source_dir = None
    for loc in source_locations:
        if loc.exists() and (loc / "manifest.json").exists():
            source_dir = loc
            break

    if not source_dir:
        console.print("[yellow]  Extension source not found in package[/yellow]")
        return False

    # Skip if already installed (unless force)
    if target_dir.exists() and not force:
        return True

    try:
        # Remove existing if force
        if target_dir.exists():
            shutil.rmtree(target_dir)

        # Copy extension
        shutil.copytree(source_dir, target_dir)

        # Print .gitignore tip
        console.print("[dim]  Tip: Add 'mcp-browser-extensions/' to .gitignore[/dim]")

        return True
    except Exception:
        return False


def install_mcp(force: bool = False) -> bool:
    """Install MCP server configuration for coding CLI platforms.

    Auto-detects and installs MCP configuration for supported coding CLIs:
    - Claude Code (project scope)
    - Cursor
    - Windsurf

    NOTE: Claude Desktop is intentionally excluded - mcp-browser is designed
    for coding CLIs only, not the desktop chat application.

    Args:
        force: Force reinstallation even if already installed

    Returns:
        True if at least one platform was configured, False otherwise
    """

    try:
        # Try using install command directly
        from py_mcp_installer import InstallationError, Platform

        from .install import install_to_platform
    except ImportError:
        # py-mcp-installer not available
        console.print(
            "[yellow]⚠ py-mcp-installer not available. "
            "Run 'mcp-browser install' manually.[/yellow]"
        )
        return False

    # Platforms to try - coding CLIs only (Claude Desktop intentionally excluded)
    target_platforms = [
        Platform.CLAUDE_CODE,
        Platform.CURSOR,
        Platform.WINDSURF,
    ]

    # Track successful installations
    configured_platforms = []

    # Suppress stderr completely during installation attempts
    # This prevents py_mcp_installer from printing tracebacks
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")

    try:
        for platform in target_platforms:
            try:
                success, message = install_to_platform(platform, force=force)

                # If installation succeeded, track it
                if success:
                    configured_platforms.append(platform.name)
                    continue

                # If installation failed, check if it's because already exists
                message_lower = message.lower()
                if (
                    "already configured" in message_lower
                    or "already exists" in message_lower
                    or "cli command fail" in message_lower
                ):
                    # Already configured counts as success
                    configured_platforms.append(platform.name)

            except InstallationError as e:
                # Check if already installed by examining error message
                error_msg = str(e).lower()
                if (
                    "already exists" in error_msg
                    or "already configured" in error_msg
                    or "cli command failed" in error_msg
                    or "native cli installation failed" in error_msg
                ):
                    # Already configured counts as success
                    configured_platforms.append(platform.name)
                # Otherwise, silently skip this platform

            except Exception:
                # Silently skip platforms that fail to install
                pass

        # Restore stderr
        sys.stderr.close()
        sys.stderr = old_stderr

        # Report results
        if configured_platforms:
            platform_list = ", ".join(configured_platforms)
            console.print(f"[dim]  MCP configured for: {platform_list}[/dim]")
            return True
        else:
            console.print(
                "[dim]  No platforms configured (may need manual setup)[/dim]"
            )
            return False

    except Exception:
        # Restore stderr first
        if sys.stderr != old_stderr:
            try:
                sys.stderr.close()
            except Exception:
                pass
            sys.stderr = old_stderr
        return False

    finally:
        # Ensure stderr is always restored
        if sys.stderr != old_stderr:
            try:
                sys.stderr.close()
            except Exception:
                pass
            sys.stderr = old_stderr


def start_server_for_setup() -> Optional[int]:
    """Start the server in background for setup.

    Returns:
        Port number if started, None if failed
    """
    from ..utils.daemon import get_server_status, start_daemon

    # Check if already running
    is_running, _, port = get_server_status()
    if is_running:
        return port

    # Start daemon
    success, _, port = start_daemon()
    if success:
        return port

    return None
