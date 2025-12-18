"""Browser MCP Server implementation."""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..._version import __version__
from ...container import ServiceContainer
from ...services import (
    BrowserService,
    MCPService,
    StorageService,
    WebSocketService,
)
from ...services.dom_interaction_service import DOMInteractionService
from ...services.storage_service import StorageConfig
from .validation import CONFIG_FILE, LOG_DIR

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
        # Use project-local data directory by default
        project_data_dir = Path.cwd() / ".mcp-browser" / "data"
        project_data_dir.mkdir(parents=True, exist_ok=True)

        default_config = {
            "storage": {
                "base_path": str(project_data_dir),
                "max_file_size_mb": 50,
                "retention_days": 7,
            },
            "websocket": {"port_range": [8851, 8899], "host": "localhost"},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "browser_control": {
                "mode": "auto",  # "auto", "extension", "applescript"
                "applescript_browser": "Safari",  # "Safari", "Google Chrome"
                "fallback_enabled": True,
                "prompt_for_permissions": True,  # Show permission instructions
            },
        }

        # Try to load from config file
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
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
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "INFO"))
        format_str = log_config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Configure handlers based on mode
        handlers = []

        if self.mcp_mode:
            # In MCP mode, only log to file and stderr, never stdout
            handlers.append(logging.FileHandler(LOG_DIR / "mcp-browser.log"))
            # Create a stderr handler for critical errors only
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.ERROR)
            handlers.append(stderr_handler)
        else:
            # Normal mode: log to both stdout and file
            handlers.append(logging.StreamHandler())
            handlers.append(logging.FileHandler(LOG_DIR / "mcp-browser.log"))

        # Configure root logger
        logging.basicConfig(level=level, format=format_str, handlers=handlers)

    def _setup_services(self) -> None:
        """Set up all services in the container with configuration."""
        import sys

        # Get configuration sections
        storage_config = self.config.get("storage", {})

        # Default to project-local data directory
        default_data_dir = Path.cwd() / ".mcp-browser" / "data"

        # Register storage service with configuration
        self.container.register(
            "storage_service",
            lambda c: StorageService(
                StorageConfig(
                    base_path=Path(
                        storage_config.get("base_path", str(default_data_dir))
                    ),
                    max_file_size_mb=storage_config.get("max_file_size_mb", 50),
                    retention_days=storage_config.get("retention_days", 7),
                )
            ),
        )

        # Register WebSocket service with configuration
        websocket_config = self.config.get("websocket", {})
        port_range = websocket_config.get("port_range", [8875, 8895])
        self.container.register(
            "websocket_service",
            lambda c: WebSocketService(
                start_port=port_range[0],
                end_port=port_range[-1],
                host=websocket_config.get("host", "localhost"),
            ),
        )

        # Register browser service and DOM interaction service together to avoid circular dependency
        # Both services are created in the same factory to handle bidirectional references properly
        async def create_browser_service(c):
            storage = await c.get("storage_service")
            # Create browser service without DOM service initially
            browser = BrowserService(storage_service=storage)
            # Create DOM service with browser reference
            dom_service = DOMInteractionService(browser_service=browser)
            # Set bidirectional reference - browser now has DOM service
            browser.dom_interaction_service = dom_service
            # Register DOM service as singleton for other services to use
            c.register_instance("dom_interaction_service", dom_service)
            return browser

        self.container.register("browser_service", create_browser_service)

        # Register capability detector
        async def create_capability_detector(c):
            browser_controller = await c.get("browser_controller")
            # Import here to avoid circular dependency
            from ...services.browser_controller import CapabilityDetector

            return CapabilityDetector(browser_controller)

        self.container.register("capability_detector", create_capability_detector)

        # Register MCP service with dependencies
        async def create_mcp_service(c):
            browser = await c.get("browser_service")
            dom_interaction = await c.get("dom_interaction_service")
            browser_controller = await c.get("browser_controller")
            capability_detector = await c.get("capability_detector")
            return MCPService(
                browser_service=browser,
                dom_interaction_service=dom_interaction,
                browser_controller=browser_controller,
                capability_detector=capability_detector,
            )

        self.container.register("mcp_service", create_mcp_service)

        # Register AppleScript service (macOS only)
        if sys.platform == "darwin":
            from ...services.applescript_service import AppleScriptService

            self.container.register(
                "applescript_service",
                lambda c: AppleScriptService(),
            )
        else:
            # Register a stub for non-macOS platforms
            self.container.register_instance("applescript_service", None)

        # Register BrowserController with dependencies
        async def create_browser_controller(c):
            websocket = await c.get("websocket_service")
            browser = await c.get("browser_service")
            applescript = await c.get("applescript_service")

            # Import here to avoid circular dependency
            from ...services.browser_controller import BrowserController

            return BrowserController(
                websocket_service=websocket,
                browser_service=browser,
                applescript_service=applescript,
                config=self.config,
            )

        self.container.register("browser_controller", create_browser_controller)

    async def start(self) -> None:
        """Start all services."""
        if not self.mcp_mode:
            logger.info(f"Starting MCP Browser Server v{__version__}...")
        self.start_time = datetime.now()

        # Register early with placeholder port to prevent race conditions
        # This claims the project slot immediately before websocket starts
        if not self.mcp_mode:
            from .daemon import add_project_server

            project_path = os.getcwd()
            # Use port 0 as placeholder - will be updated after websocket starts
            add_project_server(os.getpid(), 0, project_path)

        # Get services
        storage = await self.container.get("storage_service")
        websocket = await self.container.get("websocket_service")
        browser = await self.container.get("browser_service")
        dom_interaction = await self.container.get("dom_interaction_service")
        # Note: MCP service initialized via container but not used in start phase

        # Start storage rotation task
        await storage.start_rotation_task()

        # Set up WebSocket handlers
        websocket.register_connection_handler("connect", browser.handle_browser_connect)
        websocket.register_connection_handler(
            "disconnect", browser.handle_browser_disconnect
        )
        websocket.register_message_handler("console", browser.handle_console_message)
        websocket.register_message_handler("batch", browser.handle_batch_messages)
        websocket.register_message_handler("dom_response", browser.handle_dom_response)
        websocket.register_message_handler(
            "tabs_info", dom_interaction.handle_dom_response
        )
        websocket.register_message_handler(
            "tab_activated", dom_interaction.handle_dom_response
        )
        websocket.register_message_handler(
            "content_extracted", browser.handle_content_extracted
        )
        websocket.register_message_handler(
            "semantic_dom_extracted", browser.handle_semantic_dom_extracted
        )
        websocket.register_message_handler(
            "ascii_layout_extracted", browser.handle_ascii_layout_extracted
        )
        websocket.register_message_handler(
            "screenshot_captured", browser.handle_screenshot_captured
        )

        # Register connection_init handler to mark extension connections
        # This allows BrowserService to distinguish extension from CLI connections
        websocket.register_message_handler(
            "connection_init", browser.handle_extension_init
        )

        # Register query_logs handler for get_logs message type
        # The websocket service will call this with extracted parameters
        websocket.register_message_handler("query_logs", browser.query_logs)

        # Start WebSocket server
        self.websocket_port = await websocket.start()
        if not self.mcp_mode:
            logger.info(f"WebSocket server listening on port {self.websocket_port}")

        # Create port-specific log directory
        port_log_dir = LOG_DIR / str(self.websocket_port)
        port_log_dir.mkdir(parents=True, exist_ok=True)

        self.running = True
        if not self.mcp_mode:
            logger.info("MCP Browser Server started successfully")

        # Update service info in registry with actual port (replaces placeholder)
        if self.websocket_port and not self.mcp_mode:
            from .daemon import add_project_server

            project_path = os.getcwd()
            add_project_server(os.getpid(), self.websocket_port, project_path)

        # Show status
        await self.show_status()

    async def stop(self) -> None:
        """Stop all services gracefully."""
        if not self.mcp_mode:
            logger.info("Stopping MCP Browser Server...")

        # Clear service info from registry
        if not self.mcp_mode:
            from .daemon import clear_service_info

            clear_service_info()

        if self.start_time and not self.mcp_mode:
            uptime = datetime.now() - self.start_time
            logger.info(f"Server uptime: {uptime}")

        # Get services
        try:
            storage = await self.container.get("storage_service")
            await storage.stop_rotation_task()
        except Exception as e:
            logger.error(f"Error stopping storage service: {e}")

        try:
            websocket = await self.container.get("websocket_service")
            await websocket.stop()
        except Exception as e:
            logger.error(f"Error stopping WebSocket service: {e}")

        self.running = False
        if not self.mcp_mode:
            logger.info("MCP Browser Server stopped successfully")

    async def show_status(self) -> None:
        """Show comprehensive server status."""
        # Skip status output in MCP mode
        if self.mcp_mode:
            return

        websocket = await self.container.get("websocket_service")
        browser = await self.container.get("browser_service")
        storage = await self.container.get("storage_service")

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
        print(f"  Port Range: {ws_info['port_range']}")

        # Browser stats
        print("\n🌍 Browser Service:")
        browser_stats = await browser.get_browser_stats()
        print(f"  Total Browsers: {browser_stats['total_connections']}")
        print(f"  Total Messages: {browser_stats['total_messages']:,}")
        if browser_stats["total_messages"] > 0:
            print(
                f"  Message Rate: ~{browser_stats['total_messages'] // max(1, browser_stats.get('uptime_seconds', 1))}/sec"
            )

        # Storage stats
        print("\n💾 Storage Service:")
        storage_stats = await storage.get_storage_stats()
        print(f"  Base Path: {storage_stats['base_path']}")
        print(f"  Total Size: {storage_stats['total_size_mb']:.2f} MB")
        print(f"  Log Files: {storage_stats.get('file_count', 0)}")
        print(f"  Retention: {self.config['storage']['retention_days']} days")

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
        storage_config = self.config.get("storage", {})
        default_data_dir = Path.cwd() / ".mcp-browser" / "data"
        storage = StorageService(
            StorageConfig(
                base_path=Path(storage_config.get("base_path", str(default_data_dir))),
                max_file_size_mb=storage_config.get("max_file_size_mb", 50),
                retention_days=storage_config.get("retention_days", 7),
            )
        )

        # Create browser service
        browser = BrowserService(storage_service=storage)

        # Create DOM interaction service with simple initialization
        dom_interaction = DOMInteractionService(browser_service=browser)
        browser.dom_interaction_service = dom_interaction

        # Try to connect to running WebSocket daemon for extension communication
        daemon_client = None
        from .daemon import (
            get_project_server,
            is_process_running,
            read_service_registry,
        )

        # First try to find server for current project
        project_server = get_project_server(os.getcwd())

        # Fallback: if no matching project, try ANY running server
        # (Claude Code might spawn MCP from different directory)
        if not project_server:
            registry = read_service_registry()
            for server in registry.get("servers", []):
                if is_process_running(server.get("pid")) and server.get("port"):
                    project_server = server
                    logger.info(
                        f"MCP mode: Using fallback server on port {server.get('port')} "
                        f"(cwd mismatch: {os.getcwd()} vs {server.get('project_path', 'unknown')})"
                    )
                    break

        if project_server and project_server.get("port"):
            from ...services.daemon_client import DaemonClient

            daemon_port = project_server["port"]
            daemon_client = DaemonClient(port=daemon_port)

            # Try to connect (non-blocking)
            try:
                connected = await daemon_client.connect()
                if connected:
                    logger.info(
                        f"MCP mode connected to WebSocket daemon on port {daemon_port}"
                    )
                else:
                    logger.warning(
                        "Failed to connect to daemon, extension commands will fall back to AppleScript"
                    )
                    daemon_client = None
            except Exception as e:
                logger.warning(f"Could not connect to daemon: {e}")
                daemon_client = None

        # Create AppleScript service (macOS only)
        applescript = None
        if sys.platform == "darwin":
            from ...services.applescript_service import AppleScriptService

            applescript = AppleScriptService()

        # Create BrowserController with daemon client or AppleScript fallback
        browser_controller = None
        if daemon_client or applescript:
            from ...services.browser_controller import BrowserController

            # Pass daemon_client to BrowserController for extension communication
            browser_controller = BrowserController(
                websocket_service=None,  # Not available in stdio mode
                browser_service=browser,
                applescript_service=applescript,
                config=self.config,
                daemon_client=daemon_client,  # New: relay commands via daemon
            )

        # Create capability detector
        capability_detector = None
        if browser_controller:
            from ...services.browser_controller import CapabilityDetector

            capability_detector = CapabilityDetector(browser_controller)

        # Create MCP service with dependencies
        mcp = MCPService(
            browser_service=browser,
            dom_interaction_service=dom_interaction,
            browser_controller=browser_controller,
            capability_detector=capability_detector,
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
