"""Install command implementation for Claude Code/Desktop integration."""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

import click
from rich.panel import Panel
from rich.table import Table

from ..utils import console


def detect_installation_type() -> Literal["pipx", "pip", "dev"]:
    """Detect how mcp-browser was installed.

    Returns:
        "pipx" if installed via pipx
        "pip" if installed via pip in a virtual environment
        "dev" if running from development directory
    """
    executable = Path(sys.executable)

    # Check for pipx installation
    # pipx installs in ~/.local/pipx/venvs/<package>/
    if ".local/pipx" in str(executable) or "pipx/venvs" in str(executable):
        return "pipx"

    # Check for development mode
    # In dev mode, we're likely in a venv in the project directory
    project_indicators = [".git", "pyproject.toml", "setup.py"]
    current = Path.cwd()
    for _ in range(5):  # Check up to 5 levels up
        if any((current / indicator).exists() for indicator in project_indicators):
            return "dev"
        if current.parent == current:
            break
        current = current.parent

    # Check if in a virtual environment
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        return "pip"

    # Default to pip
    return "pip"


def get_command_path() -> str:
    """Get the appropriate command path based on installation type.

    Returns:
        Command string to use in MCP configuration
    """
    install_type = detect_installation_type()

    if install_type == "pipx":
        # pipx installations can use the direct command
        return "mcp-browser"

    elif install_type == "pip":
        # Try to find mcp-browser in PATH
        which_path = shutil.which("mcp-browser")
        if which_path:
            return which_path

        # Fallback to direct command
        return "mcp-browser"

    else:  # dev
        # For development, use the mcp-server.py script with the current Python
        # Find the script location
        script_locations = [
            Path.cwd() / "scripts" / "mcp-server.py",
            Path(__file__).parent.parent.parent.parent / "scripts" / "mcp-server.py",
        ]

        for script_path in script_locations:
            if script_path.exists():
                # Return python executable and script path
                return f"{sys.executable}"

        # Fallback to command
        return "mcp-browser"


def get_command_args(install_type: str) -> list:
    """Get command arguments based on installation type.

    Args:
        install_type: The detected installation type

    Returns:
        List of command arguments
    """
    if install_type == "dev":
        # For dev mode, if we're using python directly, include the script path
        script_locations = [
            Path.cwd() / "scripts" / "mcp-server.py",
            Path(__file__).parent.parent.parent.parent / "scripts" / "mcp-server.py",
        ]

        for script_path in script_locations:
            if script_path.exists():
                return [str(script_path), "mcp"]

    return ["mcp"]


def get_claude_code_config_path() -> Path:
    """Get the Claude Code configuration file path."""
    return Path.home() / ".claude" / "settings.local.json"


def get_claude_desktop_config_path() -> Optional[Path]:
    """Get the Claude Desktop configuration file path based on OS.

    Returns:
        Path to config file, or None if OS not supported
    """
    if sys.platform == "darwin":  # macOS
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    elif sys.platform == "linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":
        import os

        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude_desktop_config.json"

    return None


def load_or_create_config(config_path: Path) -> Dict:
    """Load existing config or create new one.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            console.print(
                f"[yellow]Warning: Invalid JSON in {config_path}, creating new config[/yellow]"
            )
            return {}
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not read {config_path}: {e}[/yellow]"
            )
            return {}

    return {}


def save_config(config_path: Path, config: Dict) -> bool:
    """Save configuration to file.

    Args:
        config_path: Path to configuration file
        config: Configuration dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with pretty formatting
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return True
    except Exception as e:
        console.print(f"[red]Error saving config to {config_path}: {e}[/red]")
        return False


def update_mcp_config(config_path: Path, force: bool = False) -> bool:
    """Update MCP configuration with mcp-browser server.

    Args:
        config_path: Path to configuration file
        force: Whether to overwrite existing configuration

    Returns:
        True if successful, False otherwise
    """
    # Load or create config
    config = load_or_create_config(config_path)

    # Ensure mcpServers section exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Check if mcp-browser already configured
    if "mcp-browser" in config["mcpServers"] and not force:
        console.print(
            "[yellow]mcp-browser is already configured. Use --force to overwrite.[/yellow]"
        )
        return False

    # Detect installation and get command
    install_type = detect_installation_type()
    command = get_command_path()
    args = get_command_args(install_type)

    # Update configuration
    config["mcpServers"]["mcp-browser"] = {"command": command, "args": args}

    # Save configuration
    if save_config(config_path, config):
        console.print(f"[green]✓[/green] Updated configuration at {config_path}")
        console.print(f"  Installation type: [cyan]{install_type}[/cyan]")
        console.print(f"  Command: [cyan]{command}[/cyan]")
        console.print(f"  Args: [cyan]{args}[/cyan]")
        return True

    return False


def remove_from_mcp_config(config_path: Path) -> bool:
    """Remove mcp-browser from MCP configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        True if removed successfully, False if not found or error
    """
    # Check if config exists
    if not config_path.exists():
        console.print(f"[yellow]Configuration file not found: {config_path}[/yellow]")
        return False

    # Load configuration
    config = load_or_create_config(config_path)

    # Check if mcpServers section exists
    if "mcpServers" not in config:
        console.print("[yellow]No mcpServers configuration found[/yellow]")
        return False

    # Check if mcp-browser is configured
    if "mcp-browser" not in config["mcpServers"]:
        console.print("[yellow]mcp-browser is not configured[/yellow]")
        return False

    # Remove mcp-browser entry
    del config["mcpServers"]["mcp-browser"]

    # Save updated configuration
    if save_config(config_path, config):
        console.print(f"[green]✓[/green] Removed mcp-browser from {config_path}")
        return True

    return False


# ============================================================================
# Enhanced Uninstall Helper Functions
# ============================================================================


def find_extension_directories() -> List[Path]:
    """Find all mcp-browser extension directories.

    Returns:
        List of paths to extension directories
    """
    directories = []

    # Check current directory for extension
    local_extension = Path.cwd() / "mcp-browser-extension"
    if local_extension.exists() and local_extension.is_dir():
        directories.append(local_extension)

    # Check .mcp-browser/extension in current directory
    local_mcp_extension = Path.cwd() / ".mcp-browser" / "extension"
    if local_mcp_extension.exists() and local_mcp_extension.is_dir():
        directories.append(local_mcp_extension)

    return directories


def get_data_directories() -> List[Path]:
    """Find all data directories to clean.

    Returns:
        List of paths to data directories
    """
    directories = []
    home = Path.home()

    # Check global .mcp-browser directory
    global_mcp = home / ".mcp-browser"
    if global_mcp.exists() and global_mcp.is_dir():
        # Add subdirectories individually
        for subdir in ["data", "logs", "config"]:
            subdir_path = global_mcp / subdir
            if subdir_path.exists() and subdir_path.is_dir():
                directories.append(subdir_path)

        # Also check for the parent directory itself
        directories.append(global_mcp)

    # Check local .mcp-browser directory
    local_mcp = Path.cwd() / ".mcp-browser"
    if local_mcp.exists() and local_mcp.is_dir():
        directories.append(local_mcp)

    return directories


def get_playwright_cache_dir() -> Optional[Path]:
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


def get_directory_size(path: Path) -> int:
    """Calculate total size of a directory in bytes.

    Args:
        path: Directory path

    Returns:
        Total size in bytes
    """
    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass

    return total


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_cleanup_summary(
    include_extensions: bool, include_data: bool, include_playwright: bool
) -> Dict:
    """Generate preview of what will be removed (read-only).

    Args:
        include_extensions: Whether to include extension directories
        include_data: Whether to include data directories
        include_playwright: Whether to include Playwright cache

    Returns:
        Dictionary with files, directories, and total_size keys
    """
    directories = []
    total_size = 0

    if include_extensions:
        ext_dirs = find_extension_directories()
        for ext_dir in ext_dirs:
            directories.append(ext_dir)
            total_size += get_directory_size(ext_dir)

    if include_data:
        data_dirs = get_data_directories()
        for data_dir in data_dirs:
            if data_dir not in directories:  # Avoid duplicates
                directories.append(data_dir)
                total_size += get_directory_size(data_dir)

    if include_playwright:
        pw_cache = get_playwright_cache_dir()
        if pw_cache:
            directories.append(pw_cache)
            total_size += get_directory_size(pw_cache)

    return {
        "directories": [str(d) for d in directories],
        "total_size": total_size,
        "formatted_size": format_size(total_size),
    }


def create_backup(directories: List[Path], backup_path: Path) -> bool:
    """Create timestamped backup of directories before removal.

    Args:
        directories: List of directories to backup
        backup_path: Path to backup directory

    Returns:
        True on success, False on failure
    """
    try:
        # Create backup directory
        backup_path.mkdir(parents=True, exist_ok=True)

        for directory in directories:
            if not directory.exists():
                continue

            # Create backup subdirectory preserving structure
            rel_path = directory.name
            backup_dest = backup_path / rel_path

            # Use shutil.copytree for directory copy
            try:
                if directory.is_dir():
                    shutil.copytree(directory, backup_dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(directory, backup_dest)

                console.print(f"  [dim]Backed up: {directory} → {backup_dest}[/dim]")
            except (OSError, PermissionError) as e:
                console.print(f"  [yellow]⚠ Could not backup {directory}: {e}[/yellow]")
                # Continue with other directories

        return True

    except Exception as e:
        console.print(f"[red]✗ Backup failed: {e}[/red]")
        return False


def remove_extension_directories(dry_run: bool = False) -> Tuple[int, List[str]]:
    """Remove extension directories.

    Args:
        dry_run: If True, only show what would be removed

    Returns:
        Tuple of (count_removed, errors)
    """
    directories = find_extension_directories()
    count = 0
    errors = []

    for directory in directories:
        try:
            if dry_run:
                console.print(f"  [dim]Would remove: {directory}[/dim]")
                count += 1
            else:
                shutil.rmtree(directory)
                console.print(f"  [green]✓[/green] Removed: {directory}")
                count += 1
        except (OSError, PermissionError) as e:
            error_msg = f"Could not remove {directory}: {e}"
            errors.append(error_msg)
            console.print(f"  [red]✗ {error_msg}[/red]")

    return count, errors


def remove_data_directories(
    dry_run: bool = False, backup: bool = True
) -> Tuple[int, List[str]]:
    """Remove data directories with optional backup.

    Args:
        dry_run: If True, only show what would be removed
        backup: If True and not dry_run, create backup before removal

    Returns:
        Tuple of (count_removed, errors)
    """
    directories = get_data_directories()
    count = 0
    errors = []

    # Create backup if requested
    if backup and not dry_run and directories:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path.home() / ".mcp-browser-backups" / timestamp

        console.print("\n[bold]Creating backup...[/bold]")
        if not create_backup(directories, backup_path):
            error_msg = "Backup failed - aborting removal"
            errors.append(error_msg)
            console.print(f"[red]✗ {error_msg}[/red]")
            return 0, errors

        console.print(f"[green]✓[/green] Backup created at: {backup_path}\n")

    for directory in directories:
        try:
            if dry_run:
                console.print(f"  [dim]Would remove: {directory}[/dim]")
                count += 1
            else:
                # Remove subdirectories first, then parent if it's empty
                if directory.exists():
                    shutil.rmtree(directory)
                    console.print(f"  [green]✓[/green] Removed: {directory}")
                    count += 1
        except (OSError, PermissionError) as e:
            error_msg = f"Could not remove {directory}: {e}"
            errors.append(error_msg)
            console.print(f"  [red]✗ {error_msg}[/red]")

    return count, errors


def remove_playwright_cache(dry_run: bool = False) -> Tuple[int, List[str]]:
    """Remove Playwright browser cache.

    Args:
        dry_run: If True, only show what would be removed

    Returns:
        Tuple of (count_removed, errors)
    """
    cache_dir = get_playwright_cache_dir()
    errors = []

    if not cache_dir:
        return 0, errors

    try:
        if dry_run:
            console.print(f"  [dim]Would remove: {cache_dir}[/dim]")
            return 1, errors
        else:
            shutil.rmtree(cache_dir)
            console.print(f"  [green]✓[/green] Removed: {cache_dir}")
            return 1, errors
    except (OSError, PermissionError) as e:
        error_msg = f"Could not remove {cache_dir}: {e}"
        errors.append(error_msg)
        console.print(f"  [red]✗ {error_msg}[/red]")
        return 0, errors


def confirm_removal(items: List[str], operation: str) -> bool:
    """Prompt user for confirmation with detailed item list.

    Args:
        items: List of items to be removed
        operation: Description of operation

    Returns:
        True if confirmed, False otherwise
    """
    if not items:
        return False

    # Create a Rich table for display
    table = Table(title=f"Items to {operation}", show_header=True, header_style="bold")
    table.add_column("Path", style="cyan")

    for item in items:
        table.add_row(item)

    console.print()
    console.print(table)
    console.print()

    return click.confirm(f"Do you want to {operation}?", default=False)


# ============================================================================


@click.command()
@click.option(
    "--target",
    type=click.Choice(["claude-code", "claude-desktop", "both"], case_sensitive=False),
    default="claude-code",
    help="Installation target (default: claude-code)",
)
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option(
    "--extension/--no-extension",
    default=True,
    help="Also install Chrome extension in project (default: True)",
)
def install(target: str, force: bool, extension: bool):
    """⚙️ Install MCP Browser configuration for Claude Code/Desktop.

    \b
    Automatically detects your installation type and configures MCP Browser
    for use with Claude Code or Claude Desktop.

    \b
    Installation types detected:
      • pipx: Installed via pipx (uses 'mcp-browser' command)
      • pip:  Installed via pip (uses full path)
      • dev:  Development mode (uses Python script)

    \b
    Examples:
      mcp-browser install                         # Install for Claude Code
      mcp-browser install --target claude-desktop # Install for Claude Desktop
      mcp-browser install --target both           # Install for both
      mcp-browser install --force                 # Overwrite existing config

    \b
    Configuration locations:
      Claude Code:    ~/.claude/settings.local.json
      Claude Desktop: OS-specific location
        • macOS:   ~/Library/Application Support/Claude/
        • Linux:   ~/.config/Claude/
        • Windows: %APPDATA%/Claude/

    \b
    After installation:
      1. Restart Claude Code or Claude Desktop
      2. The 'mcp-browser' MCP server should be available
      3. Start the server with: mcp-browser start
    """
    console.print(
        Panel.fit(
            "[bold]Installing MCP Browser Configuration[/bold]\n\n"
            f"Target: [cyan]{target}[/cyan]\n"
            f"Force overwrite: [cyan]{force}[/cyan]\n"
            f"Install extension: [cyan]{extension}[/cyan]",
            title="Installation",
            border_style="blue",
        )
    )

    # Install extension if requested
    if extension:
        console.print("\n[bold]Installing Chrome Extension...[/bold]")
        try:
            import asyncio

            from .init import init_project_extension_interactive

            asyncio.run(init_project_extension_interactive())
        except Exception as e:
            console.print(f"[yellow]⚠ Extension installation failed: {e}[/yellow]")
            console.print(
                "[dim]You can install it later with: mcp-browser init --project[/dim]"
            )

    success_count = 0
    total_count = 0

    # Install for Claude Code
    if target in ["claude-code", "both"]:
        total_count += 1
        console.print("\n[bold]Installing for Claude Code...[/bold]")
        config_path = get_claude_code_config_path()

        if update_mcp_config(config_path, force):
            success_count += 1
        else:
            console.print("[red]✗[/red] Failed to update Claude Code configuration")

    # Install for Claude Desktop
    if target in ["claude-desktop", "both"]:
        total_count += 1
        console.print("\n[bold]Installing for Claude Desktop...[/bold]")
        config_path = get_claude_desktop_config_path()

        if config_path is None:
            console.print(
                f"[red]✗[/red] Claude Desktop config path not found for {sys.platform}"
            )
        elif update_mcp_config(config_path, force):
            success_count += 1
        else:
            console.print("[red]✗[/red] Failed to update Claude Desktop configuration")

    # Summary
    console.print()
    if success_count == total_count:
        extension_msg = ""
        if extension:
            extension_msg = (
                "3. Load Chrome extension:\n"
                "   - Open chrome://extensions\n"
                "   - Enable Developer mode\n"
                "   - Load unpacked → Select mcp-browser-extension/\n\n"
            )
        else:
            extension_msg = "3. Install Chrome extension:\n   [cyan]mcp-browser init --project[/cyan]\n\n"

        console.print(
            Panel.fit(
                "[bold green]✓ Installation Complete![/bold green]\n\n"
                "[bold]Next steps:[/bold]\n"
                "1. Restart Claude Code or Claude Desktop\n"
                "2. Start the MCP Browser server:\n"
                "   [cyan]mcp-browser start[/cyan]\n"
                + extension_msg
                + "[dim]The mcp-browser MCP server should now be available[/dim]",
                title="Success",
                border_style="green",
            )
        )
    elif success_count > 0:
        console.print(
            Panel.fit(
                f"[bold yellow]⚠ Partial Success[/bold yellow]\n\n"
                f"Configured {success_count} of {total_count} targets\n"
                "Check error messages above for details",
                title="Warning",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel.fit(
                "[bold red]✗ Installation Failed[/bold red]\n\n"
                "No configurations were updated\n"
                "Check error messages above for details",
                title="Error",
                border_style="red",
            )
        )
        sys.exit(1)


@click.command()
@click.option(
    "--target",
    type=click.Choice(["claude-code", "claude-desktop", "both"], case_sensitive=False),
    default="claude-code",
    help="Target to uninstall from (default: claude-code)",
)
@click.option(
    "--clean-global",
    is_flag=True,
    help="Remove ~/.mcp-browser/ directory",
)
@click.option(
    "--clean-local",
    is_flag=True,
    help="Remove local .mcp-browser/ and extension/",
)
@click.option(
    "--clean-all",
    is_flag=True,
    help="Remove all MCP config, data, and extensions",
)
@click.option(
    "--backup/--no-backup",
    default=True,
    help="Create backup before removing data (default: True)",
)
@click.option(
    "--playwright",
    is_flag=True,
    help="Also remove Playwright browser cache",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be removed without doing it",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompts",
)
def uninstall(
    target: str,
    clean_global: bool,
    clean_local: bool,
    clean_all: bool,
    backup: bool,
    playwright: bool,
    dry_run: bool,
    yes: bool,
):
    """🗑️ Remove MCP Browser configuration from Claude Code/Desktop.

    \b
    Removes the mcp-browser configuration from Claude Code or Claude Desktop
    MCP server settings. Can also clean up data directories and extensions.

    \b
    Examples:
      mcp-browser uninstall                         # Remove from Claude Code
      mcp-browser uninstall --target claude-desktop # Remove from Claude Desktop
      mcp-browser uninstall --target both           # Remove from both
      mcp-browser uninstall --clean-all             # Remove everything
      mcp-browser uninstall --clean-global          # Remove ~/.mcp-browser/
      mcp-browser uninstall --dry-run --clean-all   # Preview what would be removed
      mcp-browser uninstall --clean-all --no-backup # Skip backup
      mcp-browser uninstall --clean-all -y          # Skip confirmation

    \b
    Configuration locations:
      Claude Code:    ~/.claude/settings.local.json
      Claude Desktop: OS-specific location
        • macOS:   ~/Library/Application Support/Claude/
        • Linux:   ~/.config/Claude/
        • Windows: %APPDATA%/Claude/

    \b
    Cleanup options:
      --clean-local:   Remove ./mcp-browser-extension/ and ./.mcp-browser/
      --clean-global:  Remove ~/.mcp-browser/ (data, logs, config)
      --clean-all:     Remove all of the above
      --playwright:    Also remove Playwright browser cache
      --backup:        Create backup before removal (default: True)
      --dry-run:       Preview without making changes
      -y, --yes:       Skip confirmation prompts

    \b
    After uninstallation:
      1. Restart Claude Code or Claude Desktop
      2. The 'mcp-browser' MCP server will no longer be available
      3. To uninstall the package itself, use: pip uninstall mcp-browser
    """
    # Determine what to clean
    clean_extensions = clean_local or clean_all
    clean_data = clean_global or clean_all
    clean_playwright = playwright or clean_all

    # Build status message
    status_parts = [f"Target: [cyan]{target}[/cyan]"]
    if clean_all:
        status_parts.append("Clean: [cyan]All data and extensions[/cyan]")
    else:
        clean_items = []
        if clean_local:
            clean_items.append("local")
        if clean_global:
            clean_items.append("global")
        if playwright:
            clean_items.append("playwright")
        if clean_items:
            status_parts.append(f"Clean: [cyan]{', '.join(clean_items)}[/cyan]")

    if dry_run:
        status_parts.append("[yellow]Mode: DRY RUN[/yellow]")
    if not backup:
        status_parts.append("[yellow]Backup: Disabled[/yellow]")

    console.print(
        Panel.fit(
            "[bold]Removing MCP Browser Configuration[/bold]\n\n"
            + "\n".join(status_parts),
            title="Uninstallation",
            border_style="blue",
        )
    )

    # Phase 1: Show preview if dry-run or if cleanup requested
    if dry_run or clean_extensions or clean_data or clean_playwright:
        summary = get_cleanup_summary(clean_extensions, clean_data, clean_playwright)

        if summary["directories"]:
            console.print("\n[bold]Preview of directories to be removed:[/bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("Directory", style="cyan")
            table.add_column("Size", style="yellow", justify="right")

            for directory in summary["directories"]:
                dir_path = Path(directory)
                if dir_path.exists():
                    size = get_directory_size(dir_path)
                    table.add_row(directory, format_size(size))
                else:
                    table.add_row(directory, "[dim]N/A[/dim]")

            console.print(table)
            console.print(f"\n[bold]Total size:[/bold] {summary['formatted_size']}\n")

            if dry_run:
                console.print(
                    "[yellow]This is a dry run - no changes will be made[/yellow]\n"
                )

    # Phase 2: Handle MCP config removal
    removed_count = 0
    not_found_count = 0
    total_count = 0

    # Uninstall from Claude Code
    if target in ["claude-code", "both"]:
        total_count += 1
        console.print("[bold]Removing from Claude Code...[/bold]")
        config_path = get_claude_code_config_path()

        if not dry_run:
            if remove_from_mcp_config(config_path):
                removed_count += 1
            else:
                not_found_count += 1
        else:
            console.print(f"  [dim]Would remove mcp-browser from {config_path}[/dim]")
            removed_count += 1

    # Uninstall from Claude Desktop
    if target in ["claude-desktop", "both"]:
        total_count += 1
        console.print("[bold]Removing from Claude Desktop...[/bold]")
        config_path = get_claude_desktop_config_path()

        if config_path is None:
            console.print(
                f"[red]✗[/red] Claude Desktop config path not found for {sys.platform}"
            )
            not_found_count += 1
        elif not dry_run:
            if remove_from_mcp_config(config_path):
                removed_count += 1
            else:
                not_found_count += 1
        else:
            console.print(f"  [dim]Would remove mcp-browser from {config_path}[/dim]")
            removed_count += 1

    # Phase 3: Handle cleanup operations
    cleanup_errors = []
    cleanup_count = 0

    if clean_extensions or clean_data or clean_playwright:
        console.print()

        # Confirm unless --yes flag is set or it's a dry-run
        if not dry_run and not yes:
            summary = get_cleanup_summary(
                clean_extensions, clean_data, clean_playwright
            )
            if summary["directories"]:
                if not confirm_removal(summary["directories"], "remove these items"):
                    console.print("\n[yellow]⚠ Cleanup cancelled by user[/yellow]")
                    # Skip cleanup but continue with summary
                    clean_extensions = False
                    clean_data = False
                    clean_playwright = False

        # Remove extensions
        if clean_extensions:
            console.print("\n[bold]Removing extension directories...[/bold]")
            count, errors = remove_extension_directories(dry_run)
            cleanup_count += count
            cleanup_errors.extend(errors)

        # Remove data directories
        if clean_data:
            console.print("\n[bold]Removing data directories...[/bold]")
            count, errors = remove_data_directories(dry_run, backup)
            cleanup_count += count
            cleanup_errors.extend(errors)

        # Remove Playwright cache
        if clean_playwright:
            console.print("\n[bold]Removing Playwright cache...[/bold]")
            count, errors = remove_playwright_cache(dry_run)
            cleanup_count += count
            cleanup_errors.extend(errors)

    # Phase 4: Summary
    console.print()

    # Build summary message
    summary_lines = []

    if dry_run:
        summary_lines.append("[bold yellow]DRY RUN COMPLETE[/bold yellow]\n")
        summary_lines.append("No actual changes were made\n")

    if removed_count == total_count:
        summary_lines.append(
            f"[green]✓[/green] Would remove mcp-browser from {removed_count} configuration(s)\n"
            if dry_run
            else f"[green]✓[/green] Removed mcp-browser from {removed_count} configuration(s)\n"
        )
    elif removed_count > 0:
        summary_lines.append(
            f"[yellow]⚠[/yellow] Removed from {removed_count} of {total_count} targets\n"
        )

    if cleanup_count > 0:
        summary_lines.append(
            f"[green]✓[/green] Would clean {cleanup_count} directories\n"
            if dry_run
            else f"[green]✓[/green] Cleaned {cleanup_count} directories\n"
        )

    if cleanup_errors:
        summary_lines.append(f"[red]✗[/red] {len(cleanup_errors)} errors occurred\n")

    if not dry_run:
        summary_lines.append("[bold]Next steps:[/bold]\n")
        summary_lines.append("1. Restart Claude Code or Claude Desktop\n")
        summary_lines.append(
            "2. The mcp-browser MCP server will no longer be available\n\n"
        )
        summary_lines.append("[dim]To uninstall the package:[/dim]\n")
        summary_lines.append("  [cyan]pip uninstall mcp-browser[/cyan]")

    console.print(
        Panel.fit(
            "".join(summary_lines),
            title="Complete" if not dry_run else "Dry Run Summary",
            border_style="green" if not cleanup_errors else "yellow",
        )
    )
