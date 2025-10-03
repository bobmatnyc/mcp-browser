"""Extension command implementation for Chrome extension management."""

import shutil
import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import console


def find_extension_source() -> Optional[Path]:
    """Find the source extension directory.

    Tries multiple locations to find extension files:
    1. Package resources (for installed packages)
    2. Development directory
    3. Project root

    Returns:
        Path to extension directory, or None if not found
    """
    # Try package resources first (for installed packages)
    source_extension = None

    try:
        if sys.version_info >= (3, 9):
            import importlib.resources as resources

            package = resources.files("mcp_browser")
            extension_dir = package / "extension"
            if extension_dir.is_dir():
                source_extension = Path(str(extension_dir))
        else:
            # Fallback for older Python versions
            import pkg_resources

            try:
                extension_files = pkg_resources.resource_listdir(
                    "mcp_browser", "extension"
                )
                if extension_files:
                    # For older Python, we need to extract files
                    import tempfile

                    temp_dir = tempfile.mkdtemp(prefix="mcp_browser_ext_")
                    for file in extension_files:
                        try:
                            content = pkg_resources.resource_string(
                                "mcp_browser", f"extension/{file}"
                            )
                            (Path(temp_dir) / file).write_bytes(content)
                        except Exception:
                            # Skip directories and problematic files
                            pass
                    source_extension = Path(temp_dir)
            except Exception:
                pass
    except Exception:
        pass

    # Fallback to development locations
    if not source_extension or not source_extension.exists():
        # Try relative to current file (development mode)
        package_path = Path(__file__).parent.parent.parent
        source_extension = package_path / "extension"

        if not source_extension.exists():
            # Try from project root (old location for compatibility)
            source_extension = Path(__file__).parent.parent.parent.parent / "extension"

    if source_extension and source_extension.exists():
        return source_extension

    return None


def get_extension_install_path(local: bool = False) -> Path:
    """Get the extension installation path.

    Args:
        local: If True, use local .mcp-browser directory, else use home directory

    Returns:
        Path to extension installation directory
    """
    if local:
        return Path.cwd() / ".mcp-browser" / "extension"
    else:
        return Path.home() / ".mcp-browser" / "extension"


def copy_extension(source: Path, destination: Path, force: bool = False) -> bool:
    """Copy extension files from source to destination.

    Args:
        source: Source extension directory
        destination: Destination directory
        force: If True, overwrite existing files

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if destination exists
        if destination.exists():
            if not force:
                console.print(
                    f"[yellow]Extension already exists at {destination}[/yellow]"
                )
                console.print("[yellow]Use --force to overwrite[/yellow]")
                return False

            # Remove existing extension
            shutil.rmtree(destination)

        # Create parent directory
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Copy extension files
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Copying extension files...", total=None)
            shutil.copytree(source, destination)

        # Count files
        file_count = sum(1 for _ in destination.rglob("*") if _.is_file())

        console.print(f"[green]✓[/green] Copied {file_count} files to {destination}")
        return True

    except Exception as e:
        console.print(f"[red]Error copying extension: {e}[/red]")
        return False


@click.group()
def extension():
    """🧩 Manage Chrome extension files.

    \b
    Commands for installing, updating, and managing the MCP Browser
    Chrome extension files.

    \b
    The extension can be installed:
      • Locally:  ./.mcp-browser/extension/ (project-specific)
      • Globally: ~/.mcp-browser/extension/ (user-wide)

    \b
    Examples:
      mcp-browser extension install          # Install to home directory
      mcp-browser extension install --local  # Install to current directory
      mcp-browser extension update           # Update existing installation
      mcp-browser extension path             # Show installation path
    """
    pass


@extension.command()
@click.option(
    "--local", "-l", is_flag=True, help="Install to current directory (./.mcp-browser/)"
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing installation")
def install(local: bool, force: bool):
    """📦 Install Chrome extension files.

    \b
    Installs the MCP Browser Chrome extension files to the specified location.

    \b
    Installation locations:
      Default: ~/.mcp-browser/extension/
      --local: ./.mcp-browser/extension/

    \b
    Examples:
      mcp-browser extension install          # Install globally
      mcp-browser extension install --local  # Install locally
      mcp-browser extension install --force  # Overwrite existing
    """
    console.print(
        Panel.fit(
            "[bold]Installing Chrome Extension[/bold]\n\n"
            f"Location: [cyan]{'Local (.mcp-browser/)' if local else 'Global (~/.mcp-browser/)'}[/cyan]\n"
            f"Force: [cyan]{force}[/cyan]",
            title="Extension Install",
            border_style="blue",
        )
    )

    # Find source extension
    source = find_extension_source()
    if not source:
        console.print(
            Panel.fit(
                "[bold red]✗ Extension Source Not Found[/bold red]\n\n"
                "Could not locate extension files.\n"
                "This may indicate a corrupted installation.\n\n"
                "Try reinstalling mcp-browser:\n"
                "  [cyan]pip install --force-reinstall mcp-browser[/cyan]",
                title="Error",
                border_style="red",
            )
        )
        sys.exit(1)

    # Get destination
    destination = get_extension_install_path(local)

    # Copy extension
    if copy_extension(source, destination, force):
        console.print(
            Panel.fit(
                "[bold green]✓ Extension Installed Successfully![/bold green]\n\n"
                f"Location: [cyan]{destination}[/cyan]\n\n"
                "[bold]Loading the extension in Chrome:[/bold]\n"
                "1. Open Chrome and go to [cyan]chrome://extensions[/cyan]\n"
                "2. Enable [cyan]Developer mode[/cyan] (top-right toggle)\n"
                "3. Click [cyan]Load unpacked[/cyan]\n"
                f"4. Select: [cyan]{destination}[/cyan]\n\n"
                "[bold]Or use the dashboard:[/bold]\n"
                "1. Start server: [cyan]mcp-browser start[/cyan]\n"
                "2. Open: [cyan]http://localhost:8080[/cyan]\n"
                "3. Click [cyan]Install Extension[/cyan] button",
                title="Success",
                border_style="green",
            )
        )
    else:
        sys.exit(1)


@extension.command()
@click.option(
    "--local", "-l", is_flag=True, help="Update local installation (./.mcp-browser/)"
)
def update(local: bool):
    """🔄 Update Chrome extension files.

    \b
    Forces an update of the Chrome extension files, overwriting
    the existing installation.

    \b
    Examples:
      mcp-browser extension update          # Update global installation
      mcp-browser extension update --local  # Update local installation
    """
    console.print(
        Panel.fit(
            "[bold]Updating Chrome Extension[/bold]\n\n"
            f"Location: [cyan]{'Local (.mcp-browser/)' if local else 'Global (~/.mcp-browser/)'}[/cyan]",
            title="Extension Update",
            border_style="blue",
        )
    )

    # Find source extension
    source = find_extension_source()
    if not source:
        console.print("[red]✗ Extension source not found[/red]")
        sys.exit(1)

    # Get destination
    destination = get_extension_install_path(local)

    # Check if extension is installed
    if not destination.exists():
        console.print(
            f"[yellow]Extension not found at {destination}[/yellow]\n"
            "Use 'mcp-browser extension install' to install first."
        )
        sys.exit(1)

    # Update (force copy)
    if copy_extension(source, destination, force=True):
        console.print(
            Panel.fit(
                "[bold green]✓ Extension Updated Successfully![/bold green]\n\n"
                f"Location: [cyan]{destination}[/cyan]\n\n"
                "[bold]Reload the extension in Chrome:[/bold]\n"
                "1. Go to [cyan]chrome://extensions[/cyan]\n"
                "2. Find [cyan]MCP Browser[/cyan] extension\n"
                "3. Click the [cyan]Reload[/cyan] button",
                title="Success",
                border_style="green",
            )
        )
    else:
        sys.exit(1)


@extension.command()
@click.option("--local", "-l", is_flag=True, help="Show local installation path")
@click.option("--check", "-c", is_flag=True, help="Check if extension is installed")
def path(local: bool, check: bool):
    """📍 Show Chrome extension installation path.

    \b
    Displays the path where the Chrome extension is installed.
    Use --check to verify if the extension exists.

    \b
    Examples:
      mcp-browser extension path           # Show global path
      mcp-browser extension path --local   # Show local path
      mcp-browser extension path --check   # Check if installed
    """
    install_path = get_extension_install_path(local)

    if check:
        exists = install_path.exists()
        status = "[green]Installed[/green]" if exists else "[red]Not installed[/red]"

        console.print(
            Panel.fit(
                f"[bold]Extension Status[/bold]\n\n"
                f"Path: [cyan]{install_path}[/cyan]\n"
                f"Status: {status}",
                title="Extension Path",
                border_style="blue",
            )
        )

        if exists:
            # Count files
            file_count = sum(1 for _ in install_path.rglob("*") if _.is_file())
            console.print(f"\n  Files: [cyan]{file_count}[/cyan]")
        else:
            console.print("\n[dim]Run 'mcp-browser extension install' to install[/dim]")
    else:
        console.print(f"[bold]Extension path:[/bold] [cyan]{install_path}[/cyan]")

        if install_path.exists():
            console.print("[green]✓[/green] Installed")
        else:
            console.print("[yellow]✗[/yellow] Not installed")
