"""Init command implementation."""

import shutil
import sys
from pathlib import Path

import click
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ..utils import DATA_DIR, HOME_DIR, LOG_DIR, console


async def init_project_extension() -> None:
    """Initialize project-specific extension folder."""
    project_path = Path.cwd()
    extension_path = project_path / "mcp-browser-extension"

    print(f"Initializing MCP Browser extension in {project_path}")

    # Create .mcp-browser directory
    extension_path.parent.mkdir(parents=True, exist_ok=True)

    # Find source extension - try multiple locations
    source_extension = None

    try:
        # For pip/pipx installations - use package resources
        if sys.version_info >= (3, 9):
            import importlib.resources as resources

            # Check if extension exists as package data
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
                    # Extract to temp location
                    import tempfile

                    temp_dir = tempfile.mkdtemp(prefix="mcp_browser_ext_")
                    for file in extension_files:
                        content = pkg_resources.resource_string(
                            "mcp_browser", f"extension/{file}"
                        )
                        (Path(temp_dir) / file).write_bytes(content)
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

    if not source_extension or not source_extension.exists():
        print(
            "Error: Extension source not found. Tried multiple locations.",
            file=sys.stderr,
        )
        print("Please ensure the package was installed correctly.", file=sys.stderr)
        sys.exit(1)

    # Copy extension files
    if extension_path.exists():
        print(f"Extension already exists at {extension_path}")
        response = input("Overwrite existing extension? (y/N): ")
        if response.lower() != "y":
            print("Initialization cancelled.")
            return
        shutil.rmtree(extension_path)

    shutil.copytree(source_extension, extension_path)
    print(f"✓ Extension copied to {extension_path}")

    # Create README in extension directory
    readme_path = extension_path / "README.md"
    readme_content = """# MCP Browser Chrome Extension

This directory contains the Chrome extension for MCP Browser.

## Installation

1. Open Chrome and navigate to `chrome://extensions`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this directory (`mcp-browser-extension/`)

## Status Colors

The extension badge shows connection status:

- 🔴 **RED** - Error or not functional
- 🟡 **YELLOW** - Listening but not connected
- 🟢 **GREEN** - Connected to server (shows port number)

## Testing the Extension

Open the included **demo.html** test page to verify extension functionality:

```
file:///path/to/mcp-browser-extension/demo.html
```

Or from Chrome:
```
chrome-extension://<your-extension-id>/demo.html
```

The demo page includes:
- Console logging tests (log, info, warn, error, objects, arrays)
- DOM interaction examples (buttons, inputs, dropdowns)
- Active tab filtering verification
- Command examples for Claude Code integration

### Example Commands

Once the demo page is open and generating console messages:

```python
# Query recent console logs
browser_query_logs(port=8875, last_n=10)

# Filter by level
browser_query_logs(port=8875, level_filter=["error"], last_n=5)

# Take screenshot
browser_screenshot(port=8875)
```

## Version

See `manifest.json` for current version.

## Server Connection

The extension automatically scans ports 8875-8895 for MCP Browser servers.
When connected, the badge will show the port number (e.g., "8875").

## Features

- ✅ **Active tab filtering** - Only the active tab sends console messages
- ✅ **Multi-server discovery** - Automatically finds servers on ports 8875-8895
- ✅ **Three-color status** - Visual connection state indicator
- ✅ **Message batching** - Efficient WebSocket communication
- ✅ **Auto-reconnection** - Handles connection failures gracefully
"""
    readme_path.write_text(readme_content)
    print(f"✓ Created {readme_path}")

    # Create data directory in .mcp-browser (for logs and data)
    data_path = project_path / ".mcp-browser" / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created data directory at {data_path}")

    # Create logs directory
    logs_path = project_path / ".mcp-browser" / "logs"
    logs_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created logs directory at {logs_path}")

    # Create .gitignore if not exists
    gitignore_path = project_path / ".mcp-browser" / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# MCP Browser local data
logs/
data/
*.log
*.jsonl
*.tmp
.DS_Store
"""
        gitignore_path.write_text(gitignore_content)
        print(f"✓ Created {gitignore_path}")

    print("\n" + "=" * 50)
    print("✅ MCP Browser initialization complete!")
    print("=" * 50)
    print("\nProject structure created:")
    print(f"  📁 {extension_path}/")
    print("     📄 manifest.json       - Extension manifest")
    print("     📄 background-enhanced.js - Background service worker")
    print("     📄 content.js          - Content script")
    print("     📄 README.md           - Installation instructions")
    print(f"\n  📁 {project_path / '.mcp-browser'}/")
    print("     📁 data/               - Console log storage")
    print("     📁 logs/               - Server logs")
    print("     📄 .gitignore          - Git ignore rules")

    print("\nNext steps:")
    print("1. Start the server: mcp-browser start")
    print(f"2. Load extension from: {extension_path}")
    print("   - Chrome → Extensions → Load unpacked → Select directory")
    print("3. Extension should connect automatically")


async def init_project_extension_interactive() -> None:
    """Interactive version of init_project_extension with better UX."""
    project_path = Path.cwd()
    extension_path = project_path / "mcp-browser-extension"

    console.print(f"\n  Initializing extension in: [cyan]{extension_path}[/cyan]")

    # Find source extension
    source_extension = None
    try:
        if sys.version_info >= (3, 9):
            import importlib.resources as resources

            package = resources.files("mcp_browser")
            extension_dir = package / "extension"
            if extension_dir.is_dir():
                source_extension = Path(str(extension_dir))
    except Exception:
        pass

    if not source_extension or not source_extension.exists():
        package_path = Path(__file__).parent.parent.parent
        source_extension = package_path / "extension"
        if not source_extension.exists():
            source_extension = Path(__file__).parent.parent.parent.parent / "extension"

    if not source_extension or not source_extension.exists():
        console.print("  [red]✗[/red] Extension source not found")
        return

    # Copy extension files
    if extension_path.exists():
        if Confirm.ask("\n  Extension already exists. Overwrite?"):
            shutil.rmtree(extension_path)
        else:
            console.print("  [yellow]⚠[/yellow] Skipping extension initialization")
            return

    shutil.copytree(source_extension, extension_path)
    console.print(
        "  [green]✓[/green] Extension copied to [cyan]mcp-browser-extension/[/cyan]"
    )

    # Create README in extension directory
    readme_path = extension_path / "README.md"
    readme_content = """# MCP Browser Chrome Extension

This directory contains the Chrome extension for MCP Browser.

## Installation

1. Open Chrome and navigate to `chrome://extensions`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this directory (`mcp-browser-extension/`)

## Status Colors

The extension badge shows connection status:

- 🔴 **RED** - Error or not functional
- 🟡 **YELLOW** - Listening but not connected
- 🟢 **GREEN** - Connected to server (shows port number)

## Testing the Extension

Open the included **demo.html** test page to verify extension functionality:

```
file:///path/to/mcp-browser-extension/demo.html
```

Or from Chrome:
```
chrome-extension://<your-extension-id>/demo.html
```

The demo page includes:
- Console logging tests (log, info, warn, error, objects, arrays)
- DOM interaction examples (buttons, inputs, dropdowns)
- Active tab filtering verification
- Command examples for Claude Code integration

### Example Commands

Once the demo page is open and generating console messages:

```python
# Query recent console logs
browser_query_logs(port=8875, last_n=10)

# Filter by level
browser_query_logs(port=8875, level_filter=["error"], last_n=5)

# Take screenshot
browser_screenshot(port=8875)
```

## Version

See `manifest.json` for current version.

## Server Connection

The extension automatically scans ports 8875-8895 for MCP Browser servers.
When connected, the badge will show the port number (e.g., "8875").

## Features

- ✅ **Active tab filtering** - Only the active tab sends console messages
- ✅ **Multi-server discovery** - Automatically finds servers on ports 8875-8895
- ✅ **Three-color status** - Visual connection state indicator
- ✅ **Message batching** - Efficient WebSocket communication
- ✅ **Auto-reconnection** - Handles connection failures gracefully
"""
    readme_path.write_text(readme_content)
    console.print("  [green]✓[/green] Created README.md in extension directory")

    # Create other directories in .mcp-browser
    for dir_name in ["data", "logs"]:
        dir_path = project_path / ".mcp-browser" / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(
            f"  [green]✓[/green] Created {dir_name} directory in .mcp-browser/"
        )

    # Create .gitignore
    gitignore_path = project_path / ".mcp-browser" / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# MCP Browser local data
logs/
data/
*.log
*.jsonl
*.tmp
.DS_Store
"""
        gitignore_path.write_text(gitignore_content)
        console.print("  [green]✓[/green] Created .gitignore")


@click.command()
@click.option(
    "--project", "-p", is_flag=True, help="Initialize in current project directory"
)
@click.option(
    "--global",
    "-g",
    "global_init",
    is_flag=True,
    help="Initialize globally in home directory",
)
@click.pass_context
def init(ctx, project, global_init):
    """📦 Initialize MCP Browser extension and configuration.

    \b
    This command sets up the Chrome extension files and creates necessary
    directories for MCP Browser operation.

    \b
    Options:
      --project  Initialize in current directory (.mcp-browser/)
      --global   Initialize globally (~/.mcp-browser/)

    \b
    Examples:
      mcp-browser init           # Interactive mode
      mcp-browser init --project # Initialize in current directory
      mcp-browser init --global  # Initialize globally

    \b
    What gets created:
      📁 .mcp-browser/
         📁 extension/     - Chrome extension files
         📁 data/          - Console log storage
         📁 logs/          - Server logs
         📄 .gitignore     - Git ignore rules
    """
    import asyncio

    if not project and not global_init:
        # Interactive mode
        console.print(
            Panel.fit(
                "[bold]Choose initialization mode:[/bold]\n\n"
                "[cyan]Project[/cyan]: Creates .mcp-browser/ in current directory\n"
                "  Best for: Development projects, version control\n\n"
                "[cyan]Global[/cyan]: Uses ~/.mcp-browser/ directory\n"
                "  Best for: System-wide installation, personal use",
                title="Initialization Mode",
            )
        )

        choice = Prompt.ask(
            "\nChoose mode", choices=["project", "global", "cancel"], default="project"
        )

        if choice == "cancel":
            console.print("[yellow]Initialization cancelled[/yellow]")
            return

        project = choice == "project"
        global_init = choice == "global"

    if project:
        asyncio.run(init_project_extension())
    else:
        # Global initialization
        console.print("[cyan]Initializing global MCP Browser configuration...[/cyan]")
        # Create global directories
        for dir_path in [HOME_DIR / "config", DATA_DIR, LOG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"  [green]✓[/green] Created {dir_path}")

        console.print("\n[green]✅ Global initialization complete![/green]")
