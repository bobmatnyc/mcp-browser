"""Dashboard service for web interface."""

import asyncio
import json
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
from aiohttp import web

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for serving dashboard web interface and API endpoints."""

    def __init__(
        self,
        websocket_service: Optional[Any] = None,
        browser_service: Optional[Any] = None,
        storage_service: Optional[Any] = None,
    ):
        """Initialize dashboard service.

        Args:
            websocket_service: WebSocket service for connection info
            browser_service: Browser service for console logs
            storage_service: Storage service for log persistence
        """
        self.websocket_service = websocket_service
        self.browser_service = browser_service
        self.storage_service = storage_service
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.port = 8080
        self.project_path = Path.cwd()
        self.extension_path = self.project_path / ".mcp-browser" / "extension"
        self.package_path = Path(__file__).parent.parent

    async def start(self, port: int = 8080) -> None:
        """Start the dashboard HTTP server.

        Args:
            port: Port to serve on (default: 8080)
        """
        self.port = port
        self.app = web.Application()

        # Add routes
        self._setup_routes()

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "localhost", self.port)
        await self.site.start()

        logger.info(f"Dashboard server started at http://localhost:{self.port}")

    async def stop(self) -> None:
        """Stop the dashboard server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Dashboard server stopped")

    def _setup_routes(self) -> None:
        """Setup HTTP routes for dashboard."""
        if not self.app:
            return

        # Static files
        self.app.router.add_get("/", self._serve_dashboard)
        self.app.router.add_get("/test-page", self._serve_test_page)
        self.app.router.add_get("/extension-installer", self._serve_extension_installer)
        self.app.router.add_get("/check-extension", self._serve_check_extension)

        # API endpoints
        self.app.router.add_get("/api/status", self._get_status)
        self.app.router.add_get("/api/project-info", self._get_project_info)
        self.app.router.add_get("/api/logs", self._get_logs)
        self.app.router.add_post("/api/clear-logs", self._clear_logs)
        self.app.router.add_get("/api/download-extension", self._download_extension)

        # WebSocket endpoint for live updates
        self.app.router.add_get("/ws", self._websocket_handler)

    async def _serve_dashboard(self, request: web.Request) -> web.Response:
        """Serve the main dashboard page."""
        dashboard_path = self.package_path / "static" / "dashboard" / "index.html"
        return await self._serve_static_file(dashboard_path)

    async def _serve_test_page(self, request: web.Request) -> web.Response:
        """Serve the console test page."""
        test_page_path = self.package_path / "static" / "test-page.html"
        return await self._serve_static_file(test_page_path)

    async def _serve_extension_installer(self, request: web.Request) -> web.Response:
        """Serve the extension installer page."""
        installer_path = self.package_path / "static" / "extension-installer.html"
        return await self._serve_static_file(installer_path)

    async def _serve_check_extension(self, request: web.Request) -> web.Response:
        """Serve the extension check page."""
        check_path = self.package_path / "static" / "dashboard" / "check-extension.html"
        return await self._serve_static_file(check_path)

    async def _serve_static_file(self, file_path: Path) -> web.Response:
        """Serve a static file.

        Args:
            file_path: Path to the file to serve

        Returns:
            HTTP response with file contents
        """
        if not file_path.exists():
            return web.Response(text="File not found", status=404)

        content_type = "text/html"
        if file_path.suffix == ".css":
            content_type = "text/css"
        elif file_path.suffix == ".js":
            content_type = "application/javascript"

        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
            return web.Response(text=content, content_type=content_type)
        except Exception as e:
            logger.error(f"Failed to serve file {file_path}: {e}")
            return web.Response(text="Internal server error", status=500)

    async def _get_status(self, request: web.Request) -> web.Response:
        """Get current system status.

        Returns:
            JSON response with status information
        """
        status = {
            "extension": {
                "connected": False,
                "version": "1.0.0",
            },
            "mcp": {
                "running": True,
                "port": self.port,
            },
            "websocket": {
                "port": None,
            },
            "logs": {
                "total": 0,
                "bufferSize": 0,
            },
        }

        # Get WebSocket status
        if self.websocket_service:
            try:
                ws_port = getattr(self.websocket_service, "port", None)
                connection_count = (
                    self.websocket_service.get_connection_count()
                    if hasattr(self.websocket_service, "get_connection_count")
                    else 0
                )
                status["websocket"]["port"] = ws_port
                status["extension"]["connected"] = connection_count > 0
            except Exception as e:
                logger.error(f"Failed to get WebSocket status: {e}")

        # Get log stats
        if self.browser_service:
            try:
                # Get message count if browser service has the method
                if hasattr(self.browser_service, "get_message_count"):
                    status["logs"]["total"] = self.browser_service.get_message_count()
                # Get buffer size if available
                if hasattr(self.browser_service, "get_buffer_size"):
                    status["logs"]["bufferSize"] = (
                        self.browser_service.get_buffer_size()
                    )
            except Exception as e:
                logger.error(f"Failed to get log stats: {e}")

        return web.json_response(status)

    async def _get_project_info(self, request: web.Request) -> web.Response:
        """Get project information.

        Returns:
            JSON response with project details
        """
        info = {
            "projectPath": str(self.project_path),
            "extensionPath": str(self.extension_path),
            "extensionExists": self.extension_path.exists(),
        }
        return web.json_response(info)

    async def _get_logs(self, request: web.Request) -> web.Response:
        """Get recent console logs.

        Returns:
            JSON response with log entries
        """
        logs = []
        if self.browser_service:
            try:
                # Get recent logs from browser service
                recent_logs = await self._safe_call_method(
                    self.browser_service, "get_recent_logs", limit=50
                )
                if recent_logs:
                    logs = recent_logs
            except Exception as e:
                logger.error(f"Failed to get logs: {e}")

        return web.json_response({"logs": logs})

    async def _clear_logs(self, request: web.Request) -> web.Response:
        """Clear console logs.

        Returns:
            JSON response indicating success
        """
        if self.browser_service:
            try:
                await self._safe_call_method(self.browser_service, "clear_logs")
            except Exception as e:
                logger.error(f"Failed to clear logs: {e}")
                return web.json_response({"success": False, "error": str(e)})

        return web.json_response({"success": True})

    async def _download_extension(self, request: web.Request) -> web.Response:
        """Download extension as ZIP file.

        Returns:
            ZIP file response or error
        """
        if not self.extension_path.exists():
            return web.Response(text="Extension not initialized", status=404)

        try:
            # Create ZIP file in memory
            from io import BytesIO

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add all extension files
                for file_path in self.extension_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.extension_path)
                        zipf.write(file_path, arcname)

            zip_buffer.seek(0)
            return web.Response(
                body=zip_buffer.read(),
                content_type="application/zip",
                headers={
                    "Content-Disposition": "attachment; filename=mcp-browser-extension.zip"
                },
            )
        except Exception as e:
            logger.error(f"Failed to create extension ZIP: {e}")
            return web.Response(text="Failed to create download", status=500)

    async def _websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for live updates.

        Args:
            request: HTTP request

        Returns:
            WebSocket response
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        try:
            # Send initial status
            status = await self._get_status_data()
            await ws.send_json({"type": "status_update", "data": status})

            # Keep connection alive and send updates
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        # Handle incoming messages if needed
                        if data.get("type") == "ping":
                            await ws.send_json({"type": "pong"})
                    except json.JSONDecodeError:
                        pass
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")

        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            await ws.close()

        return ws

    async def _get_status_data(self) -> Dict[str, Any]:
        """Get current status data.

        Returns:
            Dictionary with status information
        """
        # Reuse the logic from _get_status
        status = {
            "extension": {"connected": False, "version": "1.0.0"},
            "mcp": {"running": True, "port": self.port},
            "websocket": {"port": None},
            "logs": {"total": 0, "bufferSize": 0},
        }

        if self.websocket_service:
            try:
                ws_port = await self._safe_get_attr(
                    self.websocket_service, "current_port"
                )
                connected = await self._safe_get_attr(
                    self.websocket_service, "is_connected"
                )
                status["websocket"]["port"] = ws_port
                status["extension"]["connected"] = connected or False
            except Exception:
                pass

        if self.browser_service:
            try:
                total_logs = await self._safe_call_method(
                    self.browser_service, "get_log_count"
                )
                buffer_size = await self._safe_call_method(
                    self.browser_service, "get_buffer_size"
                )
                status["logs"]["total"] = total_logs or 0
                status["logs"]["bufferSize"] = buffer_size or 0
            except Exception:
                pass

        return status

    async def _safe_get_attr(self, obj: Any, attr: str) -> Any:
        """Safely get an attribute from an object.

        Args:
            obj: Object to get attribute from
            attr: Attribute name

        Returns:
            Attribute value or None
        """
        try:
            if hasattr(obj, attr):
                return getattr(obj, attr)
        except Exception:
            pass
        return None

    async def _safe_call_method(self, obj: Any, method: str, *args, **kwargs) -> Any:
        """Safely call a method on an object.

        Args:
            obj: Object to call method on
            method: Method name
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            Method result or None
        """
        try:
            if hasattr(obj, method):
                result = getattr(obj, method)(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                return result
        except Exception:
            pass
        return None

    def init_project_extension(self) -> bool:
        """Initialize project-specific extension folder.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create .mcp-browser directory if it doesn't exist
            self.extension_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy extension files from package to project
            source_extension = self.package_path.parent / "extension"
            if not source_extension.exists():
                # Try alternative location (development mode)
                source_extension = Path(__file__).parent.parent.parent / "extension"

            if not source_extension.exists():
                logger.error(f"Extension source not found at {source_extension}")
                return False

            # Copy extension files
            if self.extension_path.exists():
                shutil.rmtree(self.extension_path)
            shutil.copytree(source_extension, self.extension_path)

            logger.info(f"Extension initialized at {self.extension_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize extension: {e}")
            return False
