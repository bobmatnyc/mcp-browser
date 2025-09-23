"""CLI entry point for mcp-browser.

Professional MCP server implementation with browser integration.
Provides console log capture, navigation control, and screenshot capabilities.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

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

# Version information
__version__ = '1.0.1'
__author__ = 'MCP Browser Team'
__description__ = 'Browser Console Log Capture via Claude Code Integration'

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


def main():
    """Main CLI entry point with comprehensive argument parsing."""
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init           Initialize project extension folder
  %(prog)s start          Start MCP server with dashboard
  %(prog)s dashboard      Run dashboard only (port 8080)
  %(prog)s status         Show server status
  %(prog)s mcp            Run in MCP stdio mode for Claude Code
  %(prog)s start --debug  Start with debug logging

For more information, visit: https://github.com/yourusername/mcp-browser
        """
    )

    parser.add_argument(
        'command',
        choices=['start', 'status', 'mcp', 'init', 'dashboard'],
        help='Command to execute'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (JSON)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'MCP Browser v{__version__}'
    )

    args = parser.parse_args()

    # Load custom config if provided
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            sys.exit(1)

    # Override debug setting if flag provided
    if args.debug:
        if config is None:
            config = {}
        config.setdefault('logging', {})['level'] = 'DEBUG'

    # Create server with configuration, set mcp_mode for mcp command
    mcp_mode = args.command == 'mcp'
    server = BrowserMCPServer(config=config, mcp_mode=mcp_mode)

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        if not server.mcp_mode:
            sig_name = signal.Signals(sig).name
            logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        if server.running:
            # Create task to stop server
            loop = asyncio.get_event_loop()
            loop.create_task(server.stop())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run command
    try:
        if args.command == 'init':
            # Initialize project extension folder
            asyncio.run(init_project_extension())
        elif args.command == 'dashboard':
            # Run dashboard only
            asyncio.run(run_dashboard_only(config))
        elif args.command == 'start':
            if not server.mcp_mode:
                logger.info(f"Starting MCP Browser Server v{__version__}")
            asyncio.run(server.run_server_with_dashboard())
        elif args.command == 'status':
            # For status, we just show current state without starting
            asyncio.run(server.show_status())
        elif args.command == 'mcp':
            # No logging in MCP mode - it would corrupt JSON-RPC output
            asyncio.run(server.run_mcp_stdio())
    except KeyboardInterrupt:
        if not server.mcp_mode:
            logger.info("Server interrupted by user")
    except Exception as e:
        if server.mcp_mode:
            # In MCP mode, log errors only to stderr
            import traceback
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(f"Server error: {e}", file=sys.stderr)
        else:
            logger.error(f"Server error: {e}", exc_info=args.debug)
        sys.exit(1)


if __name__ == '__main__':
    main()
