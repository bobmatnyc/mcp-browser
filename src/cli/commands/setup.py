"""Setup command for complete mcp-browser installation."""

import json
import shutil
import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import console
from ..utils.daemon import get_config_dir


def get_project_root() -> Path:
    """Get the project root directory.

    This works both in development and when installed as package.
    """
    # Try to find based on current file location
    current = Path(__file__).resolve()

    # Walk up looking for pyproject.toml or mcp-browser-extension
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "mcp-browser-extension").exists():
            return parent

    # Fallback to cwd
    return Path.cwd()


def get_extension_source_dir() -> Optional[Path]:
    """Get the extension source directory."""
    root = get_project_root()

    # Check both possible locations
    if (root / "mcp-browser-extension").exists():
        return root / "mcp-browser-extension"

    # Try package data location
    try:
        if sys.version_info >= (3, 9):
            import importlib.resources as resources

            package = resources.files("mcp_browser")
            extension_dir = package / "extension"
            if extension_dir.is_dir():
                return Path(str(extension_dir))
    except Exception:
        pass

    return None


def get_dist_dir() -> Path:
    """Get or create dist directory."""
    dist = get_project_root() / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    return dist


@click.command()
@click.option("--skip-mcp", is_flag=True, help="Skip MCP installation")
@click.option("--skip-extension", is_flag=True, help="Skip extension packaging")
@click.option(
    "--force", "-f", is_flag=True, help="Force reinstall even if already setup"
)
def setup(skip_mcp: bool, skip_extension: bool, force: bool):
    """🚀 Complete mcp-browser setup.

    \b
    This command performs complete installation:

    1. Initialize configuration (~/.mcp-browser/)
    2. Install MCP server for Claude Desktop/Code
    3. Package browser extension
    4. Display installation instructions

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
    total_steps = 4 - (1 if skip_mcp else 0) - (1 if skip_extension else 0)  # config, mcp, extension, server

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

        # Step 2: Install MCP (if not skipped)
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

        # Step 3: Package extension (if not skipped)
        extension_path = None
        if not skip_extension:
            task = progress.add_task("Packaging browser extension...", total=1)
            extension_path = package_extension()
            if extension_path:
                steps_completed += 1
                progress.update(
                    task,
                    completed=1,
                    description=f"✓ Extension packaged: {extension_path.name}",
                )
            else:
                progress.update(task, description="⚠ Extension packaging failed")

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
        extension_msg = ""
        if extension_path:
            extension_msg = (
                f"[bold yellow]→ Install the Chrome extension:[/bold yellow]\n"
                f"   1. Open Chrome: [cyan]chrome://extensions/[/cyan]\n"
                f"   2. Enable 'Developer mode' (toggle in top right)\n"
                f"   3. Click 'Load unpacked'\n"
                f"   4. Select: [cyan]{extension_path}[/cyan]\n\n"
            )

        console.print(
            Panel(
                "[bold green]✓ Setup Complete![/bold green]\n\n"
                + extension_msg
                + "[bold yellow]→ Connect your browser:[/bold yellow]\n"
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
                f"[yellow]⚠ Setup partially complete ({steps_completed}/{total_steps + 1} steps)[/yellow]\n\n"
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


def install_mcp(force: bool = False) -> bool:
    """Install MCP server configuration for all available platforms.

    Auto-detects and installs MCP configuration for all supported platforms:
    - Claude Code (project scope)
    - Claude Desktop (global scope)
    - Cursor
    - Windsurf
    - And other detected platforms

    Args:
        force: Force reinstallation even if already installed

    Returns:
        True if at least one platform was configured, False otherwise
    """
    import os
    import sys

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

    # Platforms to try (exclude UNKNOWN and less common ones)
    target_platforms = [
        Platform.CLAUDE_CODE,
        Platform.CLAUDE_DESKTOP,
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
            console.print("[dim]  No platforms configured (may need manual setup)[/dim]")
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


def package_extension() -> Optional[Path]:
    """Package browser extensions as unpacked directories.

    Creates dist/chrome/, dist/firefox/, dist/safari/ directories
    ready for loading in developer mode.

    Returns:
        Path to Chrome extension directory, or None if failed
    """
    root = get_project_root()
    dist_dir = get_dist_dir()

    # Extension source locations
    extensions_src = root / "src" / "extensions"
    legacy_chrome = root / "mcp-browser-extension"

    # Determine Chrome source (prefer src/extensions/chrome, fallback to legacy)
    if (extensions_src / "chrome").exists():
        chrome_src = extensions_src / "chrome"
        firefox_src = extensions_src / "firefox"
        safari_src = extensions_src / "safari"
    elif legacy_chrome.exists():
        chrome_src = legacy_chrome
        firefox_src = None
        safari_src = None
    else:
        console.print("[yellow]Extension source not found[/yellow]")
        return None

    # Files to exclude when copying
    exclude_patterns = {
        ".claude-mpm",
        "node_modules",
        ".git",
        ".DS_Store",
        "__pycache__",
        "CHECKLIST.md",
        "README.md",
    }

    def should_exclude(path: Path) -> bool:
        """Check if path should be excluded."""
        return any(pattern in str(path) for pattern in exclude_patterns)

    def copy_extension(src: Path, dest: Path, name: str) -> bool:
        """Copy extension to destination, excluding unwanted files."""
        try:
            # Remove existing destination
            if dest.exists():
                shutil.rmtree(dest)

            # Copy directory
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns(*exclude_patterns),
            )
            console.print(f"[dim]  Created {name} extension: dist/{name}/[/dim]")
            return True
        except Exception as e:
            console.print(f"[yellow]  Warning: Failed to copy {name}: {e}[/yellow]")
            return False

    try:
        # Copy Chrome extension (required)
        chrome_dest = dist_dir / "chrome"
        if not copy_extension(chrome_src, chrome_dest, "Chrome"):
            return None

        # Copy Firefox extension (optional)
        if firefox_src and firefox_src.exists():
            copy_extension(firefox_src, dist_dir / "firefox", "Firefox")

        # Copy Safari extension (optional)
        if safari_src and safari_src.exists():
            copy_extension(safari_src, dist_dir / "safari", "Safari")

        return chrome_dest

    except Exception as e:
        console.print(f"[red]Error packaging extensions: {e}[/red]")
        return None


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
