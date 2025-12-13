"""Install command implementation using py-mcp-installer-service.

This is a thin wrapper around py-mcp-installer-service that provides
mcp-browser specific configuration and maintains backward compatibility
with the original CLI interface.
"""

import sys

import click
from py_mcp_installer import (
    InstallationError,
    MCPInstaller,
    Platform,
    PlatformDetectionError,
    Scope,
)
from rich.panel import Panel

from ...services.mcp_installer_bridge import (
    detect_installation_type,
    get_installation_metadata,
    get_mcp_browser_config,
    get_platform_display_name,
    map_target_to_platforms,
)
from ..utils import console


def install_to_platform(
    platform: Platform, force: bool = False, dry_run: bool = False
) -> tuple[bool, str]:
    """Install mcp-browser to a specific platform.

    Args:
        platform: Target platform
        force: Whether to overwrite existing configuration
        dry_run: If True, preview changes without applying

    Returns:
        Tuple of (success, message)
    """
    try:
        installer = MCPInstaller(platform=platform, dry_run=dry_run, verbose=False)
        config = get_mcp_browser_config()

        # Check if already installed
        if not force:
            existing = installer.get_server("mcp-browser", scope=Scope.PROJECT)
            if existing:
                return (
                    False,
                    "mcp-browser is already configured. Use --force to overwrite.",
                )

        # Install the server
        result = installer.install_server(
            name=config.name,
            command=config.command,
            args=config.args,
            env=config.env,
            description=config.description,
            scope=Scope.PROJECT if platform == Platform.CLAUDE_CODE else Scope.GLOBAL,
        )

        if result.success:
            install_type = detect_installation_type()
            metadata = get_installation_metadata(install_type)

            return (
                True,
                f"Successfully installed to {result.config_path}\n"
                f"  Installation type: {metadata['installation_type']}\n"
                f"  Command: {metadata['command']}\n"
                f"  Args: {metadata['args']}",
            )
        else:
            return (False, result.message)

    except PlatformDetectionError as e:
        return (False, f"Platform detection failed: {e}")
    except InstallationError as e:
        return (False, f"Installation failed: {e}")
    except Exception as e:
        return (False, f"Unexpected error: {e}")


def uninstall_from_platform(
    platform: Platform, dry_run: bool = False
) -> tuple[bool, str]:
    """Uninstall mcp-browser from a specific platform.

    Args:
        platform: Target platform
        dry_run: If True, preview changes without applying

    Returns:
        Tuple of (success, message)
    """
    try:
        installer = MCPInstaller(platform=platform, dry_run=dry_run, verbose=False)

        # Check if installed
        existing = installer.get_server("mcp-browser", scope=Scope.PROJECT)
        if not existing:
            return (False, "mcp-browser is not configured")

        # Uninstall
        result = installer.uninstall_server(
            "mcp-browser",
            scope=Scope.PROJECT if platform == Platform.CLAUDE_CODE else Scope.GLOBAL,
        )

        if result.success:
            return (True, f"Removed mcp-browser from {result.config_path}")
        else:
            return (False, result.message)

    except Exception as e:
        return (False, f"Uninstallation failed: {e}")


@click.command()
@click.option(
    "--target",
    type=click.Choice(
        [
            "claude-code",
            "claude-desktop",
            "both",
            "cursor",
            "cline",
            "roo-code",
            "continue",
            "zed",
            "windsurf",
            "void",
        ],
        case_sensitive=False,
    ),
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
    """Install MCP Browser configuration for AI coding tools.

    \b
    Automatically detects your installation type and configures MCP Browser
    for use with various AI coding platforms.

    \b
    Supported platforms:
      • claude-code:    Claude Code (project scope)
      • claude-desktop: Claude Desktop (global scope)
      • cursor:         Cursor editor
      • cline:          Cline VS Code extension
      • roo-code:       Roo-Code VS Code extension
      • continue:       Continue VS Code extension
      • zed:            Zed editor
      • windsurf:       Windsurf editor
      • void:           Void editor
      • both:           Both Claude Code and Claude Desktop

    \b
    Installation types detected:
      • pipx: Installed via pipx (uses 'mcp-browser' command)
      • pip:  Installed via pip (uses full path)
      • dev:  Development mode (uses Python script)

    \b
    Examples:
      mcp-browser install                         # Install for Claude Code
      mcp-browser install --target claude-desktop # Install for Claude Desktop
      mcp-browser install --target cursor         # Install for Cursor
      mcp-browser install --target both           # Install for both Claude versions
      mcp-browser install --force                 # Overwrite existing config

    \b
    After installation:
      1. Restart your AI coding tool
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
            console.print(
                f"[yellow]Warning: Extension installation failed: {e}[/yellow]"
            )
            console.print(
                "[dim]You can install it later with: mcp-browser init --project[/dim]"
            )

    # Map target to platforms
    platforms = map_target_to_platforms(target)

    if not platforms:
        console.print(
            Panel.fit(
                f"[bold red]Error: Unknown target '{target}'[/bold red]\n\n"
                "Supported targets: claude-code, claude-desktop, cursor, cline, "
                "roo-code, continue, zed, windsurf, void, both",
                title="Error",
                border_style="red",
            )
        )
        sys.exit(1)

    # Install to each platform
    success_count = 0
    results = []

    for platform in platforms:
        console.print(
            f"\n[bold]Installing for {get_platform_display_name(platform)}...[/bold]"
        )
        success, message = install_to_platform(platform, force=force)

        results.append((platform, success, message))

        if success:
            console.print(f"[green]✓[/green] {message}")
            success_count += 1
        else:
            console.print(f"[red]✗[/red] {message}")

    # Summary
    console.print()
    if success_count == len(platforms):
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
                "1. Restart your AI coding tool\n"
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
                f"Configured {success_count} of {len(platforms)} targets\n"
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
    type=click.Choice(
        [
            "claude-code",
            "claude-desktop",
            "both",
            "cursor",
            "cline",
            "roo-code",
            "continue",
            "zed",
            "windsurf",
            "void",
        ],
        case_sensitive=False,
    ),
    default="claude-code",
    help="Target to uninstall from (default: claude-code)",
)
@click.option(
    "--clean-all",
    is_flag=True,
    help="Remove all MCP config, data, and extensions (uses legacy uninstall)",
)
@click.option(
    "--clean-global",
    is_flag=True,
    help="Remove ~/.mcp-browser/ directory (uses legacy uninstall)",
)
@click.option(
    "--clean-local",
    is_flag=True,
    help="Remove local mcp-browser-extensions/ (uses legacy uninstall)",
)
@click.option(
    "--backup/--no-backup",
    default=True,
    help="Create backup before removing data (legacy uninstall only)",
)
@click.option(
    "--playwright",
    is_flag=True,
    help="Also remove Playwright browser cache (legacy uninstall only)",
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
    help="Skip confirmation prompts (legacy uninstall only)",
)
def uninstall(
    target: str,
    clean_all: bool,
    clean_global: bool,
    clean_local: bool,
    backup: bool,
    playwright: bool,
    dry_run: bool,
    yes: bool,
):
    """Remove MCP Browser configuration from AI coding tools.

    \b
    Removes the mcp-browser configuration from various AI coding platforms.
    For cleanup operations (--clean-*), the legacy uninstaller is used.

    \b
    Examples:
      mcp-browser uninstall                         # Remove from Claude Code
      mcp-browser uninstall --target claude-desktop # Remove from Claude Desktop
      mcp-browser uninstall --target cursor         # Remove from Cursor
      mcp-browser uninstall --target both           # Remove from both Claude versions
      mcp-browser uninstall --clean-all             # Remove everything (uses legacy)
      mcp-browser uninstall --dry-run               # Preview what would be removed

    \b
    Cleanup options (uses legacy uninstaller):
      --clean-local:   Remove ./mcp-browser-extension/ and ./.mcp-browser/
      --clean-global:  Remove ~/.mcp-browser/ (data, logs, config)
      --clean-all:     Remove all of the above
      --playwright:    Also remove Playwright browser cache
      --backup:        Create backup before removal (default: True)
      --dry-run:       Preview without making changes
      -y, --yes:       Skip confirmation prompts

    \b
    After uninstallation:
      1. Restart your AI coding tool
      2. The 'mcp-browser' MCP server will no longer be available
      3. To uninstall the package itself, use: pip uninstall mcp-browser
    """
    # If any cleanup flags are set, delegate to legacy uninstaller
    if clean_all or clean_global or clean_local or playwright:
        console.print("[dim]Using legacy uninstaller for cleanup operations...[/dim]\n")
        from .install_legacy import uninstall as legacy_uninstall

        # Create a context with the same options
        ctx = click.Context(legacy_uninstall)
        ctx.invoke(
            legacy_uninstall,
            target=target,
            clean_global=clean_global,
            clean_local=clean_local,
            clean_all=clean_all,
            backup=backup,
            playwright=playwright,
            dry_run=dry_run,
            yes=yes,
        )
        return

    # Standard uninstall using py-mcp-installer
    console.print(
        Panel.fit(
            "[bold]Removing MCP Browser Configuration[/bold]\n\n"
            f"Target: [cyan]{target}[/cyan]"
            + ("\n[yellow]Mode: DRY RUN[/yellow]" if dry_run else ""),
            title="Uninstallation",
            border_style="blue",
        )
    )

    # Map target to platforms
    platforms = map_target_to_platforms(target)

    if not platforms:
        console.print(
            Panel.fit(
                f"[bold red]Error: Unknown target '{target}'[/bold red]\n\n"
                "Supported targets: claude-code, claude-desktop, cursor, cline, "
                "roo-code, continue, zed, windsurf, void, both",
                title="Error",
                border_style="red",
            )
        )
        sys.exit(1)

    # Uninstall from each platform
    removed_count = 0
    results = []

    for platform in platforms:
        console.print(
            f"\n[bold]Removing from {get_platform_display_name(platform)}...[/bold]"
        )
        success, message = uninstall_from_platform(platform, dry_run=dry_run)

        results.append((platform, success, message))

        if success:
            console.print(f"[green]✓[/green] {message}")
            removed_count += 1
        else:
            console.print(f"[yellow]⚠[/yellow] {message}")

    # Summary
    console.print()
    summary_lines = []

    if dry_run:
        summary_lines.append("[bold yellow]DRY RUN COMPLETE[/bold yellow]\n")
        summary_lines.append("No actual changes were made\n\n")

    if removed_count == len(platforms):
        summary_lines.append(
            f"[green]✓[/green] {'Would remove' if dry_run else 'Removed'} mcp-browser from {removed_count} platform(s)\n\n"
        )
    elif removed_count > 0:
        summary_lines.append(
            f"[yellow]⚠[/yellow] Removed from {removed_count} of {len(platforms)} platforms\n\n"
        )
    else:
        summary_lines.append(
            "[yellow]⚠[/yellow] mcp-browser was not configured on any target platforms\n\n"
        )

    if not dry_run:
        summary_lines.append("[bold]Next steps:[/bold]\n")
        summary_lines.append("1. Restart your AI coding tool\n")
        summary_lines.append(
            "2. The mcp-browser MCP server will no longer be available\n\n"
        )
        summary_lines.append("[dim]To uninstall the package:[/dim]\n")
        summary_lines.append("  [cyan]pip uninstall mcp-browser[/cyan]")

    console.print(
        Panel.fit(
            "".join(summary_lines),
            title="Complete" if not dry_run else "Dry Run Summary",
            border_style="green" if removed_count > 0 else "yellow",
        )
    )
