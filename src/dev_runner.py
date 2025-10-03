"""Development runner with hot reload for MCP Browser."""

import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .cli.main import BrowserMCPServer

# Create log directory if it doesn't exist
os.makedirs("./tmp/logs", exist_ok=True)

# Configure development logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("./tmp/logs/dev-server.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


class HotReloadHandler(FileSystemEventHandler):
    """File system event handler for hot reload."""

    def __init__(self, restart_callback):
        """Initialize handler with restart callback."""
        super().__init__()
        self.restart_callback = restart_callback
        self.last_reload = 0
        self.reload_delay = 1.0  # Minimum seconds between reloads
        self.watched_extensions = {".py", ".json", ".js"}
        self.ignore_patterns = {
            "__pycache__",
            ".pyc",
            ".git",
            "node_modules",
            "tmp",
            "logs",
            ".DS_Store",
        }

    def should_reload(self, file_path: str) -> bool:
        """Check if file change should trigger reload."""
        path = Path(file_path)

        # Check extension
        if path.suffix not in self.watched_extensions:
            return False

        # Check ignore patterns
        if any(pattern in str(path) for pattern in self.ignore_patterns):
            return False

        # Check timing
        now = time.time()
        if now - self.last_reload < self.reload_delay:
            return False

        return True

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        if self.should_reload(event.src_path):
            self.last_reload = time.time()
            logger.info(f"File changed: {event.src_path}")
            logger.info("Triggering hot reload...")
            self.restart_callback()


class DevelopmentServer:
    """Development server with hot reload capabilities."""

    def __init__(self):
        """Initialize development server."""
        self.server: Optional[BrowserMCPServer] = None
        self.observer: Optional[Observer] = None
        self.running = False
        self.restart_requested = False
        self.restart_event = asyncio.Event()

        # Create tmp directories
        os.makedirs("./tmp/logs", exist_ok=True)
        os.makedirs("./tmp", exist_ok=True)

        # Load environment
        self._load_environment()

    def _load_environment(self):
        """Load development environment variables."""
        env_file = Path(".env.development")
        if env_file.exists():
            logger.info("Loading development environment...")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key] = value
                            logger.debug(f"Set {key}={value}")

    def request_restart(self):
        """Request server restart."""
        self.restart_requested = True
        self.restart_event.set()

    def setup_file_watcher(self):
        """Set up file system watcher for hot reload."""
        project_root = Path(".")
        watch_paths = [project_root / "src", project_root / "extension"]

        # Create observer
        self.observer = Observer()
        handler = HotReloadHandler(self.request_restart)

        # Watch paths
        for watch_path in watch_paths:
            if watch_path.exists():
                self.observer.schedule(handler, str(watch_path), recursive=True)
                logger.info(f"Watching for changes: {watch_path}")

        self.observer.start()
        logger.info("File watcher started")

    async def start_server(self):
        """Start the MCP server."""
        try:
            logger.info("Starting MCP Browser server...")
            self.server = BrowserMCPServer()
            await self.server.start()
            logger.info("Server started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    async def stop_server(self):
        """Stop the MCP server."""
        if self.server:
            try:
                logger.info("Stopping MCP server...")
                await self.server.stop()
                logger.info("Server stopped")
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
            finally:
                self.server = None

    async def restart_server(self):
        """Restart the MCP server."""
        logger.info("Restarting server...")
        await self.stop_server()
        await asyncio.sleep(1)  # Brief pause
        success = await self.start_server()
        if success:
            logger.info("Server restarted successfully")
        else:
            logger.error("Failed to restart server")
        return success

    async def run(self):
        """Run the development server with hot reload."""
        logger.info("Starting development server with hot reload...")

        # Set up signal handlers
        def signal_handler(sig, frame):
            logger.info("Received interrupt signal, shutting down...")
            self.running = False
            if self.restart_event:
                self.restart_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Setup file watcher
        try:
            self.setup_file_watcher()
        except Exception as e:
            logger.warning(f"Could not setup file watcher: {e}")
            logger.warning("Hot reload disabled")

        # Start initial server
        self.running = True
        if not await self.start_server():
            logger.error("Failed to start initial server")
            return

        logger.info(
            "Development server ready! Making changes to files will trigger restart."
        )

        # Main loop
        try:
            while self.running:
                # Wait for restart request or timeout
                try:
                    await asyncio.wait_for(self.restart_event.wait(), timeout=1.0)

                    if self.restart_requested and self.running:
                        self.restart_requested = False
                        self.restart_event.clear()
                        await self.restart_server()

                except asyncio.TimeoutError:
                    # Periodic check - keep server alive
                    pass

        except asyncio.CancelledError:
            logger.info("Development server cancelled")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up development server...")

        # Stop file watcher
        if self.observer:
            self.observer.stop()
            self.observer.join()

        # Stop server
        await self.stop_server()

        logger.info("Development server cleanup complete")


async def main():
    """Main entry point for development server."""
    dev_server = DevelopmentServer()
    await dev_server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Development server interrupted")
    except Exception as e:
        logger.error(f"Development server error: {e}")
        sys.exit(1)
