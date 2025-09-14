"""CLI entry point for mcp-browser."""

import asyncio
import sys
import signal
import logging
import argparse
from pathlib import Path
from typing import Optional

from ..container import ServiceContainer
from ..services import (
    StorageService,
    WebSocketService,
    BrowserService,
    MCPService,
    ScreenshotService
)
from ..services.storage_service import StorageConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrowserMCPServer:
    """Main server orchestrating all services."""

    def __init__(self):
        """Initialize the server."""
        self.container = ServiceContainer()
        self.running = False
        self._setup_services()

    def _setup_services(self) -> None:
        """Set up all services in the container."""

        # Register storage service
        self.container.register('storage_service', lambda c: StorageService(
            StorageConfig()
        ))

        # Register WebSocket service
        self.container.register('websocket_service', lambda c: WebSocketService())

        # Register browser service with storage dependency
        async def create_browser_service(c):
            storage = await c.get('storage_service')
            return BrowserService(storage_service=storage)

        self.container.register('browser_service', create_browser_service)

        # Register screenshot service
        self.container.register('screenshot_service', lambda c: ScreenshotService())

        # Register MCP service with dependencies
        async def create_mcp_service(c):
            browser = await c.get('browser_service')
            screenshot = await c.get('screenshot_service')
            return MCPService(
                browser_service=browser,
                screenshot_service=screenshot
            )

        self.container.register('mcp_service', create_mcp_service)

    async def start(self) -> None:
        """Start all services."""
        logger.info("Starting BrowserPyMCP server...")

        # Get services
        storage = await self.container.get('storage_service')
        websocket = await self.container.get('websocket_service')
        browser = await self.container.get('browser_service')
        screenshot = await self.container.get('screenshot_service')
        mcp = await self.container.get('mcp_service')

        # Start storage rotation task
        await storage.start_rotation_task()

        # Set up WebSocket handlers
        websocket.register_connection_handler('connect', browser.handle_browser_connect)
        websocket.register_connection_handler('disconnect', browser.handle_browser_disconnect)
        websocket.register_message_handler('console', browser.handle_console_message)
        websocket.register_message_handler('batch', browser.handle_batch_messages)

        # Start WebSocket server
        port = await websocket.start()
        logger.info(f"WebSocket server listening on port {port}")

        # Start screenshot service
        await screenshot.start()

        self.running = True
        logger.info("BrowserPyMCP server started successfully")

        # Show status
        await self.show_status()

    async def stop(self) -> None:
        """Stop all services."""
        logger.info("Stopping BrowserPyMCP server...")

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
        logger.info("BrowserPyMCP server stopped")

    async def show_status(self) -> None:
        """Show server status."""
        websocket = await self.container.get('websocket_service')
        browser = await self.container.get('browser_service')
        storage = await self.container.get('storage_service')
        screenshot = await self.container.get('screenshot_service')

        print("\n" + "=" * 50)
        print("BrowserPyMCP Server Status")
        print("=" * 50)

        # WebSocket info
        ws_info = websocket.get_server_info()
        print(f"WebSocket Server: {ws_info['host']}:{ws_info['port']}")
        print(f"Active Connections: {ws_info['connection_count']}")

        # Browser stats
        browser_stats = await browser.get_browser_stats()
        print(f"Total Browsers: {browser_stats['total_connections']}")
        print(f"Total Messages: {browser_stats['total_messages']}")

        # Storage stats
        storage_stats = await storage.get_storage_stats()
        print(f"Storage Path: {storage_stats['base_path']}")
        print(f"Total Size: {storage_stats['total_size_mb']} MB")

        # Screenshot service
        screenshot_info = screenshot.get_service_info()
        print(f"Screenshot Service: {'Running' if screenshot_info['is_running'] else 'Stopped'}")

        print("=" * 50 + "\n")

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
        # Get MCP service
        mcp = await self.container.get('mcp_service')

        # Start other services in background
        storage = await self.container.get('storage_service')
        websocket = await self.container.get('websocket_service')
        browser = await self.container.get('browser_service')
        screenshot = await self.container.get('screenshot_service')

        # Start services
        await storage.start_rotation_task()

        websocket.register_connection_handler('connect', browser.handle_browser_connect)
        websocket.register_connection_handler('disconnect', browser.handle_browser_disconnect)
        websocket.register_message_handler('console', browser.handle_console_message)
        websocket.register_message_handler('batch', browser.handle_batch_messages)

        await websocket.start()
        await screenshot.start()

        # Run MCP server with stdio
        try:
            await mcp.run_stdio()
        finally:
            await self.stop()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='BrowserPyMCP Server')
    parser.add_argument(
        'command',
        choices=['start', 'status', 'mcp'],
        help='Command to execute'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create server
    server = BrowserMCPServer()

    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal, shutting down...")
        asyncio.create_task(server.stop())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run command
    try:
        if args.command == 'start':
            asyncio.run(server.run_server())
        elif args.command == 'status':
            asyncio.run(server.show_status())
        elif args.command == 'mcp':
            asyncio.run(server.run_mcp_stdio())
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()