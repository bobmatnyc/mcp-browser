"""CLI entry point for mcp-browser.

Professional MCP server implementation with browser integration.
Provides console log capture, navigation control, and screenshot capabilities.
"""

import asyncio
import json
import sys
from pathlib import Path

import click
from rich.panel import Panel

# Import version information from single source of truth
from .._version import __version__
from .commands import (
    browser,
    dashboard,
    doctor,
    extension,
    init,
    install,
    quickstart,
    start,
    status,
    tutorial,
    uninstall,
)
from .utils import BrowserMCPServer, console, is_first_run, show_version_info


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.option("--version", "-v", is_flag=True, help="Show version information")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option(
    "--config", type=click.Path(exists=True), help="Path to configuration file"
)
@click.pass_context
def cli(ctx, version, debug, config):
    """🌐 MCP Browser - Browser console log capture and control for Claude Code.

    \b
    MCP Browser creates a bridge between your browser and Claude Code, enabling:
      • Real-time console log capture from any website
      • Browser navigation control via MCP tools
      • Screenshot capture with Playwright
      • Persistent log storage with automatic rotation

    \b
    Quick Start:
      1. Run 'mcp-browser quickstart' for interactive setup
      2. Or manually: 'mcp-browser init' then 'mcp-browser start'
      3. Install Chrome extension from the dashboard

    \b
    For detailed help on any command, use:
      mcp-browser COMMAND --help
    """
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["config_file"] = config

    # Store config in context
    if config:
        try:
            with open(config, "r") as f:
                ctx.obj["config"] = json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            sys.exit(1)
    else:
        ctx.obj["config"] = None

    if version:
        show_version_info()
        ctx.exit()

    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        # Check if first run
        if is_first_run():
            console.print(
                Panel.fit(
                    "[bold yellow]👋 Welcome to MCP Browser![/bold yellow]\n\n"
                    "It looks like this is your first time running mcp-browser.\n\n"
                    "[bold]Get started with:[/bold]\n"
                    "  • [cyan]mcp-browser quickstart[/cyan] - Interactive setup wizard\n"
                    "  • [cyan]mcp-browser --help[/cyan] - Show all commands\n"
                    "  • [cyan]mcp-browser doctor[/cyan] - Check system requirements",
                    title="First Run Detected",
                    border_style="yellow",
                )
            )
        else:
            click.echo(ctx.get_help())


@cli.command()
@click.pass_context
def mcp(ctx):
    """🔧 Run in MCP stdio mode for Claude Code integration.

    \b
    This mode is used by Claude Code to communicate with MCP Browser.
    It runs in stdio mode without any console output to avoid corrupting
    the JSON-RPC communication.

    \b
    Configuration for Claude Desktop:
      {
        "mcpServers": {
          "mcp-browser": {
            "command": "mcp-browser",
            "args": ["mcp"]
          }
        }
      }

    \b
    Note: This command should not be run manually. It's designed to be
    invoked by Claude Code or other MCP clients.
    """
    # Run in MCP mode (no console output)
    config = ctx.obj.get("config")
    server = BrowserMCPServer(config=config, mcp_mode=True)

    try:
        asyncio.run(server.run_mcp_stdio())
    except Exception:
        # Errors logged to stderr to avoid corrupting stdio
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


@cli.command()
@click.option(
    "--detailed", "-d", is_flag=True, help="Show detailed version information"
)
def version(detailed):
    """📦 Show version information.

    \b
    Displays version and build information for MCP Browser.

    Examples:
      mcp-browser version          # Basic version
      mcp-browser version -d       # Detailed info
    """
    if detailed:
        show_version_info()
    else:
        console.print(f"[bold]MCP Browser[/bold] version [cyan]{__version__}[/cyan]")


@cli.command()
def reference():
    """📚 Show quick reference guide.

    \b
    Displays a quick reference guide with common commands,
    options, and usage patterns for MCP Browser.

    Perfect for a quick reminder of how to use the tool!
    """
    from rich.panel import Panel

    reference_text = """
[bold cyan]MCP Browser Quick Reference[/bold cyan]

[bold]Essential Commands:[/bold]
  [cyan]quickstart[/cyan]  - Interactive setup wizard
  [cyan]init[/cyan]        - Initialize extension
  [cyan]start[/cyan]       - Start server + dashboard
  [cyan]status[/cyan]      - Check installation status
  [cyan]doctor[/cyan]      - Diagnose & fix issues
  [cyan]dashboard[/cyan]   - Run dashboard only
  [cyan]tutorial[/cyan]    - Interactive tutorial
  [cyan]install[/cyan]     - Install MCP config for Claude
  [cyan]uninstall[/cyan]   - Remove MCP config from Claude
  [cyan]extension[/cyan]   - Manage Chrome extension
  [cyan]browser[/cyan]     - Browser interaction and testing

[bold]Quick Start:[/bold]
  1. pip install mcp-browser
  2. mcp-browser quickstart
  3. Install Chrome extension from dashboard

[bold]Common Options:[/bold]
  --help         Show help for any command
  --debug        Enable debug logging
  --config FILE  Use custom config file

[bold]Start Options:[/bold]
  --port 8880           Specific WebSocket port
  --no-dashboard        Skip dashboard
  --dashboard-port 3000 Custom dashboard port

[bold]Chrome Extension:[/bold]
  • Start server: mcp-browser start
  • Open: http://localhost:8080
  • Click "Install Extension"

[bold]Browser Testing Commands:[/bold]
  mcp-browser browser navigate <url>
  mcp-browser browser logs [--limit N]
  mcp-browser browser fill <selector> <value>
  mcp-browser browser click <selector>
  mcp-browser browser test [--demo]

[bold]Claude Desktop Config:[/bold]
  {
    "mcpServers": {
      "mcp-browser": {
        "command": "mcp-browser",
        "args": ["mcp"]
      }
    }
  }

[bold]Troubleshooting:[/bold]
  mcp-browser doctor        Check for issues
  mcp-browser doctor --fix  Auto-fix issues
  mcp-browser status        Check status

[bold]Port Ranges:[/bold]
  WebSocket: 8875-8895 (auto-select)
  Dashboard: 8080 (default)

[bold]Get Help:[/bold]
  mcp-browser COMMAND --help
  mcp-browser tutorial
"""
    console.print(
        Panel(
            reference_text,
            title="📚 Quick Reference",
            border_style="blue",
            padding=(1, 2),
        )
    )


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell):
    """🔧 Generate shell completion script.

    \b
    Generates shell completion scripts for tab completion support.

    \b
    Installation:
      Bash:
        eval "$(mcp-browser completion bash)"
        # Or add to ~/.bashrc

      Zsh:
        eval "$(mcp-browser completion zsh)"
        # Or add to ~/.zshrc

      Fish:
        mcp-browser completion fish | source
        # Or save to ~/.config/fish/completions/mcp-browser.fish

    \b
    Examples:
      mcp-browser completion bash >> ~/.bashrc
      mcp-browser completion zsh >> ~/.zshrc
    """
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"

    # Inline completion scripts
    bash_completion = """
_mcp_browser_completions() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local commands="quickstart init start status doctor dashboard tutorial install uninstall extension browser mcp version completion --help --version"
    COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
}
complete -F _mcp_browser_completions mcp-browser
"""

    zsh_completion = """
#compdef mcp-browser
_mcp_browser() {
    local commands=(
        'quickstart:Interactive setup wizard'
        'init:Initialize extension'
        'start:Start server'
        'status:Show status'
        'doctor:Diagnose issues'
        'dashboard:Run dashboard'
        'tutorial:Interactive tutorial'
        'install:Install MCP config for Claude'
        'uninstall:Remove MCP config from Claude'
        'extension:Manage Chrome extension'
        'browser:Browser interaction and testing'
        'mcp:MCP stdio mode'
        'version:Show version'
        'completion:Generate completion'
    )
    _describe 'command' commands
}
"""

    fish_completion = """
complete -c mcp-browser -n "__fish_use_subcommand" -a quickstart -d "Interactive setup wizard"
complete -c mcp-browser -n "__fish_use_subcommand" -a init -d "Initialize extension"
complete -c mcp-browser -n "__fish_use_subcommand" -a start -d "Start server"
complete -c mcp-browser -n "__fish_use_subcommand" -a status -d "Show status"
complete -c mcp-browser -n "__fish_use_subcommand" -a doctor -d "Diagnose issues"
complete -c mcp-browser -n "__fish_use_subcommand" -a dashboard -d "Run dashboard"
complete -c mcp-browser -n "__fish_use_subcommand" -a tutorial -d "Interactive tutorial"
complete -c mcp-browser -n "__fish_use_subcommand" -a install -d "Install MCP config for Claude"
complete -c mcp-browser -n "__fish_use_subcommand" -a uninstall -d "Remove MCP config from Claude"
complete -c mcp-browser -n "__fish_use_subcommand" -a extension -d "Manage Chrome extension"
complete -c mcp-browser -n "__fish_use_subcommand" -a browser -d "Browser interaction and testing"
complete -c mcp-browser -n "__fish_use_subcommand" -a mcp -d "MCP stdio mode"
complete -c mcp-browser -n "__fish_use_subcommand" -a version -d "Show version"
complete -c mcp-browser -n "__fish_use_subcommand" -a completion -d "Generate completion"
"""

    if shell == "bash":
        script_path = scripts_dir / "completion.bash"
        if script_path.exists():
            console.print(script_path.read_text())
        else:
            console.print(bash_completion)
    elif shell == "zsh":
        script_path = scripts_dir / "completion.zsh"
        if script_path.exists():
            console.print(script_path.read_text())
        else:
            console.print(zsh_completion)
    elif shell == "fish":
        console.print(fish_completion)


# Register command modules
cli.add_command(quickstart)
cli.add_command(init)
cli.add_command(start)
cli.add_command(status)
cli.add_command(doctor)
cli.add_command(dashboard)
cli.add_command(tutorial)
cli.add_command(install)
cli.add_command(uninstall)
cli.add_command(extension)
cli.add_command(browser)


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
