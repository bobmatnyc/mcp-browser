"""CLI entry point for mcp-browser.

Professional MCP server implementation with browser integration.
Provides console log capture, navigation control, and screenshot capabilities.
"""

import asyncio
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Import version information from single source of truth
from .._version import __version__, get_version_info
from ..container import ServiceContainer
from ..services import (
    BrowserService,
    MCPService,
    ScreenshotService,
    StorageService,
    WebSocketService,
)
from ..services.dashboard_service import DashboardService
from ..services.dom_interaction_service import DOMInteractionService
from ..services.storage_service import StorageConfig

# Default paths
HOME_DIR = Path.home() / '.mcp-browser'
CONFIG_FILE = HOME_DIR / 'config' / 'settings.json'
LOG_DIR = HOME_DIR / 'logs'
DATA_DIR = HOME_DIR / 'data'

# Logging configuration
logger = logging.getLogger(__name__)


class BrowserMCPServer:
    """Main server orchestrating all services.

    Implements Service-Oriented Architecture with dependency injection
    for managing browser connections, console log storage, and MCP integration.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, mcp_mode: bool = False):
        """Initialize the server with optional configuration.

        Args:
            config: Optional configuration dictionary
            mcp_mode: Whether running in MCP stdio mode (suppresses stdout logging)
        """
        self.container = ServiceContainer()
        self.running = False
        self.mcp_mode = mcp_mode
        self.config = self._load_config(config)
        self._setup_logging()
        self._setup_services()
        self.start_time = None
        self.websocket_port = None

    def _load_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults.

        Args:
            config: Optional configuration override

        Returns:
            Configuration dictionary
        """
        default_config = {
            'storage': {
                'base_path': str(DATA_DIR),
                'max_file_size_mb': 50,
                'retention_days': 7
            },
            'websocket': {
                'port_range': [8875, 8895],
                'host': 'localhost'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }

        # Try to load from config file
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    file_config = json.load(f)
                    default_config.update(file_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")

        # Apply any provided overrides
        if config:
            default_config.update(config)

        return default_config

    def _setup_logging(self) -> None:
        """Configure logging based on settings."""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        format_str = log_config.get(
            'format',
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Configure handlers based on mode
        handlers = []

        if self.mcp_mode:
            # In MCP mode, only log to file and stderr, never stdout
            handlers.append(logging.FileHandler(LOG_DIR / 'mcp-browser.log'))
            # Create a stderr handler for critical errors only
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.ERROR)
            handlers.append(stderr_handler)
        else:
            # Normal mode: log to both stdout and file
            handlers.append(logging.StreamHandler())
            handlers.append(logging.FileHandler(LOG_DIR / 'mcp-browser.log'))

        # Configure root logger
        logging.basicConfig(
            level=level,
            format=format_str,
            handlers=handlers
        )

    def _setup_services(self) -> None:
        """Set up all services in the container with configuration."""

        # Get configuration sections
        storage_config = self.config.get('storage', {})

        # Register storage service with configuration
        self.container.register('storage_service', lambda c: StorageService(
            StorageConfig(
                base_path=Path(storage_config.get('base_path', DATA_DIR)),
                max_file_size_mb=storage_config.get('max_file_size_mb', 50),
                retention_days=storage_config.get('retention_days', 7)
            )
        ))

        # Register WebSocket service
        self.container.register('websocket_service', lambda c: WebSocketService())

        # Register browser service with storage dependency
        async def create_browser_service(c):
            storage = await c.get('storage_service')
            return BrowserService(storage_service=storage)

        self.container.register('browser_service', create_browser_service)

        # Register DOM interaction service with browser dependency
        async def create_dom_service(c):
            browser = await c.get('browser_service')
            dom_service = DOMInteractionService(browser_service=browser)
            # Set bidirectional reference for response handling
            browser.set_dom_interaction_service(dom_service)
            return dom_service

        self.container.register('dom_interaction_service', create_dom_service)

        # Register screenshot service
        self.container.register('screenshot_service', lambda c: ScreenshotService())

        # Register MCP service with dependencies
        async def create_mcp_service(c):
            browser = await c.get('browser_service')
            screenshot = await c.get('screenshot_service')
            dom_interaction = await c.get('dom_interaction_service')
            return MCPService(
                browser_service=browser,
                screenshot_service=screenshot,
                dom_interaction_service=dom_interaction
            )

        self.container.register('mcp_service', create_mcp_service)

        # Register dashboard service with dependencies
        async def create_dashboard_service(c):
            websocket = await c.get('websocket_service')
            browser = await c.get('browser_service')
            storage = await c.get('storage_service')
            return DashboardService(
                websocket_service=websocket,
                browser_service=browser,
                storage_service=storage
            )

        self.container.register('dashboard_service', create_dashboard_service)

    async def start(self) -> None:
        """Start all services."""
        if not self.mcp_mode:
            logger.info(f"Starting MCP Browser Server v{__version__}...")
        self.start_time = datetime.now()

        # Get services
        storage = await self.container.get('storage_service')
        websocket = await self.container.get('websocket_service')
        browser = await self.container.get('browser_service')
        screenshot = await self.container.get('screenshot_service')
        dom_interaction = await self.container.get('dom_interaction_service')
        # Note: MCP service initialized via container but not used in start phase

        # Start storage rotation task
        await storage.start_rotation_task()

        # Set up WebSocket handlers
        websocket.register_connection_handler('connect', browser.handle_browser_connect)
        websocket.register_connection_handler('disconnect', browser.handle_browser_disconnect)
        websocket.register_message_handler('console', browser.handle_console_message)
        websocket.register_message_handler('batch', browser.handle_batch_messages)
        websocket.register_message_handler('dom_response', browser.handle_dom_response)
        websocket.register_message_handler('tabs_info', dom_interaction.handle_dom_response)
        websocket.register_message_handler('tab_activated', dom_interaction.handle_dom_response)
        websocket.register_message_handler('content_extracted', browser.handle_content_extracted)

        # Start WebSocket server
        self.websocket_port = await websocket.start()
        if not self.mcp_mode:
            logger.info(f"WebSocket server listening on port {self.websocket_port}")

        # Create port-specific log directory
        port_log_dir = LOG_DIR / str(self.websocket_port)
        port_log_dir.mkdir(parents=True, exist_ok=True)

        # Start screenshot service
        await screenshot.start()

        self.running = True
        if not self.mcp_mode:
            logger.info("MCP Browser Server started successfully")

        # Show status
        await self.show_status()

    async def stop(self) -> None:
        """Stop all services gracefully."""
        if not self.mcp_mode:
            logger.info("Stopping MCP Browser Server...")

        if self.start_time and not self.mcp_mode:
            uptime = datetime.now() - self.start_time
            logger.info(f"Server uptime: {uptime}")

        # Get services
        try:
            storage = await self.container.get('storage_service')
            await storage.stop_rotation_task()
        except Exception as e:
            logger.error(f"Error stopping storage service: {e}")

        try:
            websocket = await self.container.get('websocket_service')
            await websocket.stop()
        except Exception as e:
            logger.error(f"Error stopping WebSocket service: {e}")

        try:
            screenshot = await self.container.get('screenshot_service')
            await screenshot.stop()
        except Exception as e:
            logger.error(f"Error stopping screenshot service: {e}")

        self.running = False
        if not self.mcp_mode:
            logger.info("MCP Browser Server stopped successfully")

    async def show_status(self) -> None:
        """Show comprehensive server status."""
        # Skip status output in MCP mode
        if self.mcp_mode:
            return

        websocket = await self.container.get('websocket_service')
        browser = await self.container.get('browser_service')
        storage = await self.container.get('storage_service')
        screenshot = await self.container.get('screenshot_service')

        print("\n" + "═" * 60)
        print(f"  MCP Browser Server Status (v{__version__})")
        print("═" * 60)

        # Server info
        print("\n📊 Server Information:")
        if self.start_time:
            uptime = datetime.now() - self.start_time
            print(f"  Uptime: {uptime}")
        print(f"  PID: {os.getpid()}")
        print(f"  Python: {sys.version.split()[0]}")

        # WebSocket info
        print("\n🌐 WebSocket Service:")
        ws_info = websocket.get_server_info()
        print(f"  Server: {ws_info['host']}:{ws_info['port']}")
        print(f"  Active Connections: {ws_info['connection_count']}")
        print("  Port Range: 8875-8895")

        # Browser stats
        print("\n🌍 Browser Service:")
        browser_stats = await browser.get_browser_stats()
        print(f"  Total Browsers: {browser_stats['total_connections']}")
        print(f"  Total Messages: {browser_stats['total_messages']:,}")
        if browser_stats['total_messages'] > 0:
            print(f"  Message Rate: ~{browser_stats['total_messages'] // max(1, browser_stats.get('uptime_seconds', 1))}/sec")

        # Storage stats
        print("\n💾 Storage Service:")
        storage_stats = await storage.get_storage_stats()
        print(f"  Base Path: {storage_stats['base_path']}")
        print(f"  Total Size: {storage_stats['total_size_mb']:.2f} MB")
        print(f"  Log Files: {storage_stats.get('file_count', 0)}")
        print(f"  Retention: {self.config['storage']['retention_days']} days")

        # Screenshot service
        print("\n📸 Screenshot Service:")
        screenshot_info = screenshot.get_service_info()
        status = '✅ Running' if screenshot_info['is_running'] else '⭕ Stopped'
        print(f"  Status: {status}")
        if screenshot_info.get('browser_type'):
            print(f"  Browser: {screenshot_info['browser_type']}")

        # MCP Integration
        print("\n🔧 MCP Integration:")
        print("  Tools Available:")
        print("    • browser_navigate - Navigate to URLs")
        print("    • browser_query_logs - Query console logs")
        print("    • browser_screenshot - Capture screenshots")

        print("\n" + "═" * 60 + "\n")

    async def run_server(self) -> None:
        """Run the server until interrupted."""
        await self.start()

        # Keep running until interrupted
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def run_mcp_stdio(self) -> None:
        """Run in MCP stdio mode."""
        # In MCP mode, we need a simpler initialization to avoid blocking
        # Register minimal services needed for MCP

        # Create simple service instances without full initialization
        storage_config = self.config.get('storage', {})
        storage = StorageService(
            StorageConfig(
                base_path=Path(storage_config.get('base_path', DATA_DIR)),
                max_file_size_mb=storage_config.get('max_file_size_mb', 50),
                retention_days=storage_config.get('retention_days', 7)
            )
        )

        # Create browser service
        browser = BrowserService(storage_service=storage)

        # Create screenshot service
        screenshot = ScreenshotService()

        # Create DOM interaction service with simple initialization
        dom_interaction = DOMInteractionService(browser_service=browser)
        browser.set_dom_interaction_service(dom_interaction)

        # Create MCP service with dependencies
        mcp = MCPService(
            browser_service=browser,
            screenshot_service=screenshot,
            dom_interaction_service=dom_interaction
        )

        # Note: We don't start WebSocket server in MCP mode
        # The MCP service will handle stdio communication only

        # Run MCP server with stdio
        try:
            await mcp.run_stdio()
        except Exception:
            # Log to stderr to avoid corrupting stdio
            import traceback
            traceback.print_exc(file=sys.stderr)

    async def run_server_with_dashboard(self) -> None:
        """Run the server with dashboard enabled."""
        await self.start()

        # Start dashboard service
        try:
            dashboard = await self.container.get('dashboard_service')
            await dashboard.start(port=8080)
            if not self.mcp_mode:
                logger.info("Dashboard available at http://localhost:8080")
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")

        # Keep running until interrupted
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            try:
                dashboard = await self.container.get('dashboard_service')
                await dashboard.stop()
            except Exception:
                pass
            await self.stop()


async def init_project_extension() -> None:
    """Initialize project-specific extension folder."""
    import shutil
    project_path = Path.cwd()
    extension_path = project_path / ".mcp-browser" / "extension"

    print(f"Initializing MCP Browser extension in {project_path}")

    # Create .mcp-browser directory
    extension_path.parent.mkdir(parents=True, exist_ok=True)

    # Find source extension - try multiple locations

    # Try to use importlib.resources for packaged data (Python 3.9+)
    source_extension = None

    try:
        # For pip/pipx installations - use package resources
        if sys.version_info >= (3, 9):
            import importlib.resources as resources
            # Check if extension exists as package data
            package = resources.files('mcp_browser')
            extension_dir = package / 'extension'
            if extension_dir.is_dir():
                source_extension = Path(str(extension_dir))
        else:
            # Fallback for older Python versions
            import pkg_resources
            try:
                extension_files = pkg_resources.resource_listdir('mcp_browser', 'extension')
                if extension_files:
                    # Extract to temp location
                    import tempfile
                    temp_dir = tempfile.mkdtemp(prefix='mcp_browser_ext_')
                    for file in extension_files:
                        content = pkg_resources.resource_string('mcp_browser', f'extension/{file}')
                        (Path(temp_dir) / file).write_bytes(content)
                    source_extension = Path(temp_dir)
            except Exception:
                pass
    except Exception:
        pass

    # Fallback to development locations
    if not source_extension or not source_extension.exists():
        # Try relative to current file (development mode)
        package_path = Path(__file__).parent.parent
        source_extension = package_path.parent / "extension"

        if not source_extension.exists():
            # Try from project root
            source_extension = Path(__file__).parent.parent.parent / "extension"

    if not source_extension or not source_extension.exists():
        print("Error: Extension source not found. Tried multiple locations.", file=sys.stderr)
        print("Please ensure the package was installed correctly.", file=sys.stderr)
        sys.exit(1)

    # Copy extension files
    if extension_path.exists():
        print(f"Extension already exists at {extension_path}")
        response = input("Overwrite existing extension? (y/N): ")
        if response.lower() != 'y':
            print("Initialization cancelled.")
            return
        shutil.rmtree(extension_path)

    shutil.copytree(source_extension, extension_path)
    print(f"✓ Extension copied to {extension_path}")

    # Create data directory
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
    print(f"  📁 {project_path / '.mcp-browser'}/")
    print("     📁 extension/     - Chrome extension files")
    print("     📁 data/          - Console log storage")
    print("     📁 logs/          - Server logs")
    print("     📄 .gitignore     - Git ignore rules")

    print("\nNext steps:")
    print("1. Start the server: mcp-browser start")
    print("2. Open dashboard: http://localhost:8080")
    print("3. Install the Chrome extension from the dashboard")


async def run_dashboard_only(config: Optional[Dict[str, Any]] = None) -> None:
    """Run dashboard service only without MCP server."""
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create minimal container
    container = ServiceContainer()

    # Register minimal services for dashboard
    container.register('storage_service', lambda c: StorageService(
        StorageConfig(base_path=Path.cwd() / ".mcp-browser" / "data")
    ))
    container.register('websocket_service', lambda c: WebSocketService())
    container.register('browser_service', lambda c: BrowserService(
        storage_service=container.get('storage_service')
    ))

    # Register dashboard service
    async def create_dashboard_service(c):
        return DashboardService()

    container.register('dashboard_service', create_dashboard_service)

    # Get and start dashboard
    dashboard = await container.get('dashboard_service')
    await dashboard.start(port=8080)

    print("Dashboard running at http://localhost:8080")
    print("Press Ctrl+C to stop")

    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
    finally:
        await dashboard.stop()


def show_version_info():
    """Display detailed version and build information."""
    info = get_version_info()

    print(f"MCP Browser v{info['version']}")
    print(f"{'=' * 40}")
    print(f"Version:        {info['full_version']}")
    print(f"  Major:        {info['major']}")
    print(f"  Minor:        {info['minor']}")
    print(f"  Patch:        {info['patch']}")
    print()
    print("Build Info:")
    print(f"  Date:         {info['build_date']}")
    if info['git_commit']:
        print(f"  Git Commit:   {info['git_commit']}")
    if info['git_branch']:
        print(f"  Git Branch:   {info['git_branch']}")
    if info['git_dirty']:
        print("  Git Status:   Modified (uncommitted changes)")
    print(f"  Environment:  {'Development' if info['is_development'] else 'Production'}")
    print()
    print("Project Info:")
    print(f"  Title:        {info['title']}")
    print(f"  Description:  {info['description']}")
    print(f"  Author:       {info['author']}")
    print(f"  License:      {info['license']}")
    print()
    print(f"Python:         {sys.version.split()[0]}")
    print(f"Platform:       {sys.platform}")
    print(f"{'=' * 40}")


# Create console for rich output
console = Console()

# Track if this is first run
def is_first_run() -> bool:
    """Check if this is the first time running mcp-browser."""
    return not HOME_DIR.exists() or not CONFIG_FILE.exists()


class DiagnosticCheck:
    """Represents a diagnostic check."""
    def __init__(self, name: str, check_func, fix_func=None, fix_description=None):
        self.name = name
        self.check_func = check_func
        self.fix_func = fix_func
        self.fix_description = fix_description


async def check_system_requirements() -> List[Tuple[str, bool, str]]:
    """Check system requirements and return status."""
    checks = []

    # Python version
    py_version = sys.version_info
    py_ok = py_version >= (3, 10)
    checks.append(("Python 3.10+", py_ok, f"Python {py_version.major}.{py_version.minor}.{py_version.micro}"))

    # Chrome/Chromium
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/chromium",  # Linux Chromium
    ]
    chrome_found = any(Path(p).exists() for p in chrome_paths) or shutil.which("chrome") or shutil.which("chromium")
    checks.append(("Chrome/Chromium", chrome_found, "Required for extension"))

    # Node.js (optional but useful)
    node_found = shutil.which("node") is not None
    node_version = "Not installed"
    if node_found:
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            node_version = result.stdout.strip()
        except:
            pass
    checks.append(("Node.js (optional)", node_found, node_version))

    # Playwright browsers
    playwright_ok = False
    try:
        playwright_ok = True
    except:
        pass
    checks.append(("Playwright", playwright_ok, "For screenshots"))

    # Port availability
    import socket
    port_available = False
    for port in range(8875, 8896):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                port_available = True
                break
            except:
                pass
    checks.append(("Port availability", port_available, "Ports 8875-8895"))

    return checks


async def check_installation_status() -> Dict[str, Any]:
    """Check the installation status of mcp-browser."""
    status = {
        "package_installed": True,  # We're running, so it's installed
        "config_exists": CONFIG_FILE.exists(),
        "extension_initialized": False,
        "data_dir_exists": DATA_DIR.exists(),
        "logs_dir_exists": LOG_DIR.exists(),
        "server_running": False,
        "extension_installed": False,
    }

    # Check for project-local extension
    local_ext = Path.cwd() / ".mcp-browser" / "extension"
    status["extension_initialized"] = local_ext.exists()

    # Check if server is running (by checking port)
    import socket
    for port in range(8875, 8896):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex(('localhost', port)) == 0:
                status["server_running"] = True
                status["server_port"] = port
                break

    return status


@click.group(invoke_without_command=True, context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--version', '-v', is_flag=True, help='Show version information')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config', type=click.Path(exists=True), help='Path to configuration file')
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
    ctx.obj['debug'] = debug
    ctx.obj['config_file'] = config

    # Store config in context
    if config:
        try:
            with open(config, 'r') as f:
                ctx.obj['config'] = json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            sys.exit(1)
    else:
        ctx.obj['config'] = None

    if version:
        show_version_info()
        ctx.exit()

    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        # Check if first run
        if is_first_run():
            console.print(Panel.fit(
                "[bold yellow]👋 Welcome to MCP Browser![/bold yellow]\n\n"
                "It looks like this is your first time running mcp-browser.\n\n"
                "[bold]Get started with:[/bold]\n"
                "  • [cyan]mcp-browser quickstart[/cyan] - Interactive setup wizard\n"
                "  • [cyan]mcp-browser --help[/cyan] - Show all commands\n"
                "  • [cyan]mcp-browser doctor[/cyan] - Check system requirements",
                title="First Run Detected",
                border_style="yellow"
            ))
        else:
            click.echo(ctx.get_help())


@cli.command()
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
    console.print(Panel.fit(
        "[bold cyan]🚀 MCP Browser Quick Start Wizard[/bold cyan]\n\n"
        "This wizard will help you set up MCP Browser in just a few steps.",
        title="Welcome",
        border_style="cyan"
    ))

    # Step 1: Check requirements
    console.print("\n[bold]Step 1: Checking system requirements...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Checking...", total=None)
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
        if not Confirm.ask("\n[yellow]Some requirements are missing. Continue anyway?[/yellow]"):
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

    use_local = Confirm.ask("\nInitialize extension in current directory? (recommended for projects)")

    if use_local:
        asyncio.run(init_project_extension_interactive())
    else:
        console.print("[dim]Skipping local extension setup. You can run 'mcp-browser init' later.[/dim]")

    # Step 4: Configure settings
    console.print("\n[bold]Step 4: Configuring settings...[/bold]")

    if not CONFIG_FILE.exists():
        default_config = {
            'storage': {
                'base_path': str(DATA_DIR),
                'max_file_size_mb': 50,
                'retention_days': 7
            },
            'websocket': {
                'port_range': [8875, 8895],
                'host': 'localhost'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }

        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        console.print("  [green]✓[/green] Created default configuration")
    else:
        console.print("  [dim]✓ Configuration exists[/dim]")

    # Step 5: Install Playwright browsers if needed
    console.print("\n[bold]Step 5: Setting up Playwright (for screenshots)...[/bold]")

    try:
        import playwright
        if Confirm.ask("\nInstall Playwright browsers for screenshot support?"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Installing Playwright browsers...", total=None)
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            console.print("  [green]✓[/green] Playwright browsers installed")
    except ImportError:
        console.print("  [yellow]⚠[/yellow] Playwright not installed (screenshots won't work)")
    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] Could not install Playwright browsers: {e}")

    # Step 6: Start server
    console.print("\n[bold]Step 6: Starting the server...[/bold]")

    if Confirm.ask("\nStart the MCP Browser server now?"):
        console.print("\n[green]✨ Setup complete![/green]")
        console.print("\nStarting server with dashboard...")
        console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")

        # Start the server
        config = ctx.obj.get('config')
        server = BrowserMCPServer(config=config, mcp_mode=False)

        try:
            asyncio.run(server.run_server_with_dashboard())
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped by user[/yellow]")
    else:
        console.print("\n[green]✨ Setup complete![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run [cyan]mcp-browser start[/cyan] to start the server")
        console.print("  2. Open [link=http://localhost:8080]http://localhost:8080[/link] in your browser")
        console.print("  3. Install the Chrome extension from the dashboard")
        console.print("  4. Configure Claude Code to use MCP Browser")


async def init_project_extension_interactive() -> None:
    """Interactive version of init_project_extension with better UX."""
    import shutil
    project_path = Path.cwd()
    extension_path = project_path / ".mcp-browser" / "extension"

    console.print(f"\n  Initializing extension in: [cyan]{project_path}[/cyan]")

    # Find source extension
    source_extension = None
    try:
        if sys.version_info >= (3, 9):
            import importlib.resources as resources
            package = resources.files('mcp_browser')
            extension_dir = package / 'extension'
            if extension_dir.is_dir():
                source_extension = Path(str(extension_dir))
    except:
        pass

    if not source_extension or not source_extension.exists():
        package_path = Path(__file__).parent.parent
        source_extension = package_path.parent / "extension"
        if not source_extension.exists():
            source_extension = Path(__file__).parent.parent.parent / "extension"

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
    console.print("  [green]✓[/green] Extension copied")

    # Create other directories
    for dir_name in ['data', 'logs']:
        dir_path = project_path / ".mcp-browser" / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"  [green]✓[/green] Created {dir_name} directory")

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


@cli.command()
@click.option('--project', '-p', is_flag=True, help='Initialize in current project directory')
@click.option('--global', '-g', 'global_init', is_flag=True, help='Initialize globally in home directory')
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
    if not project and not global_init:
        # Interactive mode
        console.print(Panel.fit(
            "[bold]Choose initialization mode:[/bold]\n\n"
            "[cyan]Project[/cyan]: Creates .mcp-browser/ in current directory\n"
            "  Best for: Development projects, version control\n\n"
            "[cyan]Global[/cyan]: Uses ~/.mcp-browser/ directory\n"
            "  Best for: System-wide installation, personal use",
            title="Initialization Mode"
        ))

        choice = Prompt.ask(
            "\nChoose mode",
            choices=["project", "global", "cancel"],
            default="project"
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


@cli.command()
@click.option('--port', '-p', default=None, type=int, help='WebSocket port (default: auto 8875-8895)')
@click.option('--dashboard/--no-dashboard', default=True, help='Enable/disable dashboard')
@click.option('--dashboard-port', default=8080, type=int, help='Dashboard port (default: 8080)')
@click.option('--background', '-b', is_flag=True, help='Run server in background')
@click.pass_context
def start(ctx, port, dashboard, dashboard_port, background):
    """🚀 Start the MCP Browser server.

    \b
    Starts the MCP Browser server with WebSocket listener and optional dashboard.
    The server will:
      • Listen for browser connections on WebSocket (ports 8875-8895)
      • Store console logs with automatic rotation
      • Provide MCP tools for Claude Code
      • Serve dashboard for monitoring (if enabled)

    \b
    Examples:
      mcp-browser start                    # Start with defaults
      mcp-browser start --no-dashboard     # Start without dashboard
      mcp-browser start --port 8880        # Use specific port
      mcp-browser start --background       # Run in background

    \b
    Default settings:
      WebSocket: Auto-select from ports 8875-8895
      Dashboard: http://localhost:8080
      Data storage: ~/.mcp-browser/data/ or ./.mcp-browser/data/
      Log rotation: 50MB per file, 7-day retention

    \b
    Troubleshooting:
      • Port in use: Server auto-selects next available port
      • Extension not connecting: Check port in extension popup
      • Logs not appearing: Verify extension is installed
      • Use 'mcp-browser doctor' to diagnose issues
    """
    config = ctx.obj.get('config')

    if background:
        console.print("[yellow]Background mode not yet implemented[/yellow]")
        console.print("[dim]Tip: Use screen/tmux or run with '&' on Unix systems[/dim]")
        return

    # Override port if specified
    if port and config is None:
        config = {}
    if port:
        config.setdefault('websocket', {})['port_range'] = [port, port]

    console.print(Panel.fit(
        f"[bold green]Starting MCP Browser Server v{__version__}[/bold green]\n\n"
        f"WebSocket: Ports {config.get('websocket', {}).get('port_range', [8875, 8895]) if config else [8875, 8895]}\n"
        f"Dashboard: {'Enabled' if dashboard else 'Disabled'} (port {dashboard_port})\n"
        f"Data: {DATA_DIR}",
        title="Server Starting",
        border_style="green"
    ))

    server = BrowserMCPServer(config=config, mcp_mode=False)

    # Set up signal handlers
    def signal_handler(sig, frame):
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        if server.running:
            loop = asyncio.get_event_loop()
            loop.create_task(server.stop())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if dashboard:
            asyncio.run(server.run_server_with_dashboard())
        else:
            asyncio.run(server.run_server())
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Server error: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'simple']), default='table', help='Output format')
@click.pass_context
def status(ctx, format):
    """📊 Show current server and installation status.

    \b
    Displays comprehensive information about:
      • Server running status
      • WebSocket connections
      • Chrome extension status
      • Storage statistics
      • Recent console logs
      • System configuration

    \b
    Examples:
      mcp-browser status          # Table format (default)
      mcp-browser status --json   # JSON output
      mcp-browser status -f simple # Simple text output
    """
    status_info = asyncio.run(check_installation_status())

    if format == 'json':
        console.print_json(data=status_info)
    elif format == 'simple':
        for key, value in status_info.items():
            console.print(f"{key}: {value}")
    else:
        # Table format
        table = Table(title="MCP Browser Status", show_header=False)
        table.add_column("Component", style="cyan", width=30)
        table.add_column("Status", width=50)

        # Package
        table.add_row(
            "Package",
            "[green]✓ Installed[/green]" if status_info['package_installed'] else "[red]✗ Not installed[/red]"
        )

        # Configuration
        table.add_row(
            "Configuration",
            "[green]✓ Configured[/green]" if status_info['config_exists'] else "[yellow]⚠ Not configured[/yellow]"
        )

        # Extension
        ext_status = "[green]✓ Initialized[/green]" if status_info['extension_initialized'] else "[yellow]⚠ Not initialized[/yellow]"
        table.add_row("Extension", ext_status)

        # Server
        if status_info['server_running']:
            server_status = f"[green]✓ Running on port {status_info.get('server_port', 'unknown')}[/green]"
        else:
            server_status = "[dim]○ Not running[/dim]"
        table.add_row("Server", server_status)

        # Data directories
        table.add_row(
            "Data Directory",
            "[green]✓ Created[/green]" if status_info['data_dir_exists'] else "[yellow]⚠ Not created[/yellow]"
        )

        table.add_row(
            "Logs Directory",
            "[green]✓ Created[/green]" if status_info['logs_dir_exists'] else "[yellow]⚠ Not created[/yellow]"
        )

        console.print(table)

        # Show tips if not everything is set up
        if not all([status_info['config_exists'], status_info['extension_initialized']]):
            console.print("\n[yellow]💡 Tip:[/yellow] Run [cyan]mcp-browser quickstart[/cyan] for guided setup")


@cli.command()
@click.option('--fix', is_flag=True, help='Attempt to fix issues automatically')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed diagnostic information')
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
    console.print(Panel.fit(
        "[bold cyan]🩺 MCP Browser Diagnostic Tool[/bold cyan]\n\n"
        "Running comprehensive system checks...",
        title="Doctor",
        border_style="cyan"
    ))

    issues_found = []
    fixes_available = []

    # System requirements
    console.print("\n[bold]Checking system requirements...[/bold]")
    checks = asyncio.run(check_system_requirements())

    for name, ok, details in checks:
        if not ok and "optional" not in name.lower():
            issues_found.append(f"{name}: {details}")
            if name == "Playwright":
                fixes_available.append(("Install Playwright browsers",
                                      lambda: subprocess.run([sys.executable, "-m", "playwright", "install"])))

    # Installation status
    console.print("\n[bold]Checking installation...[/bold]")
    status = asyncio.run(check_installation_status())

    if not status['config_exists']:
        issues_found.append("Configuration file missing")
        fixes_available.append(("Create default configuration", create_default_config))

    if not status['extension_initialized']:
        issues_found.append("Chrome extension not initialized")
        fixes_available.append(("Initialize extension",
                              lambda: asyncio.run(init_project_extension())))

    if not status['data_dir_exists']:
        issues_found.append("Data directory missing")
        fixes_available.append(("Create data directory",
                              lambda: DATA_DIR.mkdir(parents=True, exist_ok=True)))

    # Show results
    console.print("\n" + "="*50)

    if not issues_found:
        console.print("\n[bold green]✅ All checks passed![/bold green]")
        console.print("\nYour MCP Browser installation is healthy.")
    else:
        console.print(f"\n[bold yellow]⚠ Found {len(issues_found)} issue(s):[/bold yellow]")
        for issue in issues_found:
            console.print(f"  • {issue}")

        if ctx.params.get('fix') and fixes_available:
            console.print(f"\n[bold]Attempting to fix {len(fixes_available)} issue(s)...[/bold]")
            for desc, fix_func in fixes_available:
                try:
                    console.print(f"  Fixing: {desc}...")
                    fix_func()
                    console.print("    [green]✓[/green] Fixed")
                except Exception as e:
                    console.print(f"    [red]✗[/red] Failed: {e}")
        elif fixes_available:
            console.print("\n[dim]Run 'mcp-browser doctor --fix' to attempt automatic fixes[/dim]")


def create_default_config():
    """Create default configuration file."""
    default_config = {
        'storage': {
            'base_path': str(DATA_DIR),
            'max_file_size_mb': 50,
            'retention_days': 7
        },
        'websocket': {
            'port_range': [8875, 8895],
            'host': 'localhost'
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=2)


@cli.command()
@click.option('--port', '-p', default=8080, type=int, help='Dashboard port (default: 8080)')
@click.option('--open', '-o', 'open_browser', is_flag=True, help='Open dashboard in browser')
@click.pass_context
def dashboard(ctx, port, open_browser):
    """🎯 Run the monitoring dashboard.

    \b
    Starts only the web dashboard without the MCP server.
    Useful for monitoring an already-running server or viewing historical logs.

    \b
    Dashboard features:
      • Real-time connection status
      • Console log viewer with search
      • Chrome extension installer
      • Server statistics
      • Log file browser

    \b
    Examples:
      mcp-browser dashboard           # Start on default port 8080
      mcp-browser dashboard -p 3000   # Use custom port
      mcp-browser dashboard --open    # Auto-open in browser

    \b
    Access the dashboard at:
      http://localhost:8080 (or your chosen port)
    """
    console.print(Panel.fit(
        f"[bold cyan]Starting Dashboard[/bold cyan]\n\n"
        f"Port: {port}\n"
        f"URL: http://localhost:{port}",
        title="Dashboard",
        border_style="cyan"
    ))

    if open_browser:
        # Wait a moment for server to start
        import threading
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    config = ctx.obj.get('config')

    try:
        asyncio.run(run_dashboard_only(config))
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Dashboard error: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            traceback.print_exc()


@cli.command()
@click.pass_context
def tutorial(ctx):
    """📚 Interactive tutorial for using MCP Browser.

    \b
    Step-by-step guide that covers:
      1. Installation and setup
      2. Starting the server
      3. Installing the Chrome extension
      4. Capturing console logs
      5. Using MCP tools with Claude Code
      6. Troubleshooting common issues

    Perfect for new users who want to learn by doing!
    """
    console.print(Panel.fit(
        "[bold magenta]📚 MCP Browser Interactive Tutorial[/bold magenta]\n\n"
        "This tutorial will guide you through using MCP Browser step by step.",
        title="Tutorial",
        border_style="magenta"
    ))

    lessons = [
        {
            "title": "Lesson 1: Understanding MCP Browser",
            "content": """
MCP Browser creates a bridge between your web browser and Claude Code.

Key concepts:
• **WebSocket Server**: Listens for browser connections (ports 8875-8895)
• **Chrome Extension**: Captures console logs from any website
• **MCP Tools**: Exposes browser control to Claude Code
• **Storage**: Persists logs with automatic rotation

The flow:
1. Chrome extension connects to local WebSocket server
2. Extension captures all console.log messages
3. Server stores messages and exposes them via MCP
4. Claude Code can query logs and control browser
"""
        },
        {
            "title": "Lesson 2: Installation",
            "content": """
Let's verify your installation:

1. **Check Python version** (needs 3.10+):
   $ python --version

2. **Install mcp-browser**:
   $ pip install mcp-browser

3. **Initialize extension**:
   $ mcp-browser init --project  # For current project
   $ mcp-browser init --global   # For system-wide

4. **Verify installation**:
   $ mcp-browser doctor
"""
        },
        {
            "title": "Lesson 3: Starting the Server",
            "content": """
Start the MCP Browser server:

$ mcp-browser start

This will:
• Start WebSocket server (auto-selects port 8875-8895)
• Launch dashboard at http://localhost:8080
• Begin listening for browser connections

Options:
• --no-dashboard: Skip dashboard
• --port 8880: Use specific WebSocket port
• --debug: Enable debug logging
"""
        },
        {
            "title": "Lesson 4: Installing Chrome Extension",
            "content": """
Install the Chrome extension:

1. Start the server: `mcp-browser start`
2. Open dashboard: http://localhost:8080
3. Click "Install Extension" button
4. Or manually:
   a. Open Chrome Extensions (chrome://extensions)
   b. Enable "Developer mode"
   c. Click "Load unpacked"
   d. Select .mcp-browser/extension folder

5. Verify connection in extension popup (puzzle icon)
"""
        },
        {
            "title": "Lesson 5: Capturing Console Logs",
            "content": """
Once connected, the extension captures all console output:

1. Open any website
2. Open DevTools Console (F12)
3. Type: console.log('Hello from MCP!')
4. Check dashboard to see captured message

Captured data includes:
• Message content
• Timestamp
• URL and title
• Log level (log, warn, error)
• Stack traces for errors
"""
        },
        {
            "title": "Lesson 6: Using with Claude Code",
            "content": """
Configure Claude Code to use MCP Browser:

1. **For Claude Desktop**, add to config:
   {
     "mcpServers": {
       "mcp-browser": {
         "command": "mcp-browser",
         "args": ["mcp"]
       }
     }
   }

2. **Available MCP tools**:
   • browser_navigate: Navigate to URL
   • browser_query_logs: Search console logs
   • browser_screenshot: Capture screenshots

3. **Example usage in Claude**:
   "Navigate to example.com and show me any console errors"
"""
        },
        {
            "title": "Lesson 7: Troubleshooting",
            "content": """
Common issues and solutions:

**Extension not connecting:**
• Check server is running: `mcp-browser status`
• Verify port in extension popup matches server
• Try different port: `mcp-browser start --port 8880`

**No logs appearing:**
• Refresh the webpage
• Check extension is enabled in Chrome
• Verify connection status in extension popup

**Server won't start:**
• Port in use: Server auto-tries next port
• Permission issues: Check directory permissions
• Run `mcp-browser doctor --fix`
"""
        },
    ]

    current_lesson = 0

    while current_lesson < len(lessons):
        lesson = lessons[current_lesson]

        console.clear()
        console.print(Panel(
            Markdown(lesson["content"]),
            title=f"[bold]{lesson['title']}[/bold]",
            border_style="blue",
            padding=(1, 2)
        ))

        console.print("\n" + "─" * 50)

        if current_lesson < len(lessons) - 1:
            choice = Prompt.ask(
                "\n[bold]Continue?[/bold]",
                choices=["next", "previous", "quit", "practice"],
                default="next"
            )
        else:
            choice = Prompt.ask(
                "\n[bold]Tutorial complete![/bold]",
                choices=["previous", "quit", "restart"],
                default="quit"
            )

        if choice == "next":
            current_lesson += 1
        elif choice == "previous":
            current_lesson = max(0, current_lesson - 1)
        elif choice == "restart":
            current_lesson = 0
        elif choice == "practice":
            console.print("\n[cyan]Opening a new terminal for practice...[/cyan]")
            console.print("[dim]Type 'exit' to return to the tutorial[/dim]")
            input("\nPress Enter to continue...")
        else:  # quit
            break

    console.print("\n[green]Thanks for completing the tutorial![/green]")
    console.print("\nNext steps:")
    console.print("  • Run [cyan]mcp-browser quickstart[/cyan] for setup")
    console.print("  • Run [cyan]mcp-browser start[/cyan] to begin")
    console.print("  • Visit [link=https://docs.mcp-browser.dev]documentation[/link] for more info")


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
    config = ctx.obj.get('config')
    server = BrowserMCPServer(config=config, mcp_mode=True)

    try:
        asyncio.run(server.run_mcp_stdio())
    except Exception:
        # Errors logged to stderr to avoid corrupting stdio
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


@cli.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed version information')
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
    console.print(Panel(
        reference_text,
        title="📚 Quick Reference",
        border_style="blue",
        padding=(1, 2)
    ))


@cli.command()
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
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

    if shell == 'bash':
        script_path = scripts_dir / "completion.bash"
        if script_path.exists():
            console.print(script_path.read_text())
        else:
            # Generate inline if file not found
            console.print(BASH_COMPLETION_SCRIPT)
    elif shell == 'zsh':
        script_path = scripts_dir / "completion.zsh"
        if script_path.exists():
            console.print(script_path.read_text())
        else:
            console.print(ZSH_COMPLETION_SCRIPT)
    elif shell == 'fish':
        console.print(FISH_COMPLETION_SCRIPT)


# Inline completion scripts as fallback
BASH_COMPLETION_SCRIPT = """
_mcp_browser_completions() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local commands="quickstart init start status doctor dashboard tutorial mcp version completion --help --version"
    COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
}
complete -F _mcp_browser_completions mcp-browser
"""

ZSH_COMPLETION_SCRIPT = """
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
        'mcp:MCP stdio mode'
        'version:Show version'
        'completion:Generate completion'
    )
    _describe 'command' commands
}
"""

FISH_COMPLETION_SCRIPT = """
complete -c mcp-browser -n "__fish_use_subcommand" -a quickstart -d "Interactive setup wizard"
complete -c mcp-browser -n "__fish_use_subcommand" -a init -d "Initialize extension"
complete -c mcp-browser -n "__fish_use_subcommand" -a start -d "Start server"
complete -c mcp-browser -n "__fish_use_subcommand" -a status -d "Show status"
complete -c mcp-browser -n "__fish_use_subcommand" -a doctor -d "Diagnose issues"
complete -c mcp-browser -n "__fish_use_subcommand" -a dashboard -d "Run dashboard"
complete -c mcp-browser -n "__fish_use_subcommand" -a tutorial -d "Interactive tutorial"
complete -c mcp-browser -n "__fish_use_subcommand" -a mcp -d "MCP stdio mode"
complete -c mcp-browser -n "__fish_use_subcommand" -a version -d "Show version"
complete -c mcp-browser -n "__fish_use_subcommand" -a completion -d "Generate completion"
"""


def main():
    """Main CLI entry point."""
    cli()


if __name__ == '__main__':
    main()
