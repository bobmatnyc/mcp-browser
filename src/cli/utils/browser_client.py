"""Browser client utility for CLI commands."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import websockets
from rich.console import Console

from .daemon import PORT_RANGE_START, PORT_RANGE_END, read_service_info

console = Console()
logger = logging.getLogger(__name__)


class BrowserClient:
    """Client for interacting with mcp-browser WebSocket server."""

    def __init__(self, host: str = "localhost", port: int = PORT_RANGE_START):
        """Initialize browser client.

        Args:
            host: WebSocket server host
            port: WebSocket server port (default: PORT_RANGE_START)
        """
        self.host = host
        self.port = port
        self.websocket = None
        self._connected = False
        self._pending_requests: Dict[str, asyncio.Future] = {}

    async def connect(self) -> bool:
        """Connect to WebSocket server.

        Returns:
            True if connected successfully
        """
        try:
            uri = f"ws://{self.host}:{self.port}"
            self.websocket = await websockets.connect(uri)
            self._connected = True
            logger.debug(f"Connected to {uri}")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to connect to server: {e}[/red]")
            console.print(
                "\n[yellow]Make sure the server is running:[/yellow]\n"
                "  mcp-browser start\n"
            )
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self._connected = False

    async def _send_and_wait(
        self, message: Dict[str, Any], timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Send message and wait for response with matching requestId."""
        if not self._connected or not self.websocket:
            return {"success": False, "error": "Not connected to server"}

        request_id = message.get("requestId") or str(uuid.uuid4())
        message["requestId"] = request_id

        # Create future for response
        response_future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = response_future

        try:
            await self.websocket.send(json.dumps(message))

            # Start listener task if not running
            listen_task = asyncio.create_task(self._listen_for_response(request_id))

            try:
                result = await asyncio.wait_for(response_future, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                return {"success": False, "error": f"Timeout after {timeout}s"}
            finally:
                listen_task.cancel()
                self._pending_requests.pop(request_id, None)

        except Exception as e:
            self._pending_requests.pop(request_id, None)
            return {"success": False, "error": str(e)}

    async def _listen_for_response(self, request_id: str) -> None:
        """Listen for response matching request_id."""
        try:
            while request_id in self._pending_requests:
                try:
                    msg = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    data = json.loads(msg)

                    # Check if this response matches our request
                    resp_id = data.get("requestId")
                    if resp_id and resp_id in self._pending_requests:
                        future = self._pending_requests.get(resp_id)
                        if future and not future.done():
                            future.set_result(data)
                            break
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
        except asyncio.CancelledError:
            pass

    async def navigate(self, url: str, wait: float = 0) -> Dict[str, Any]:
        """Navigate browser to URL.

        Args:
            url: URL to navigate to
            wait: Wait time after navigation

        Returns:
            Response dictionary
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to server"}

        try:
            message = {"type": "navigate", "url": url}
            await self.websocket.send(json.dumps(message))

            # Wait if specified
            if wait > 0:
                await asyncio.sleep(wait)

            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def query_logs(self, limit: int = 50, level: str = "all") -> Dict[str, Any]:
        """Query console logs from browser.

        Args:
            limit: Number of logs to retrieve
            level: Log level filter (all, log, error, warn, info)

        Returns:
            Response dictionary with logs
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to server"}

        try:
            # For CLI usage, we'll read from the storage directly
            # This is a simplified version - in production you'd use the MCP tools
            return {
                "success": True,
                "logs": [],
                "message": "Query logs functionality requires server integration",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fill_field(self, selector: str, value: str) -> Dict[str, Any]:
        """Fill a form field.

        Args:
            selector: CSS selector for the field
            value: Value to fill

        Returns:
            Response dictionary
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to server"}

        try:
            import uuid

            request_id = str(uuid.uuid4())
            message = {
                "type": "dom_command",
                "requestId": request_id,
                "command": {
                    "type": "fill",
                    "params": {"selector": selector, "value": value, "index": 0},
                },
            }
            await self.websocket.send(json.dumps(message))

            # Wait for response (simplified for now)
            return {"success": True, "selector": selector, "value": value}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click_element(self, selector: str) -> Dict[str, Any]:
        """Click an element.

        Args:
            selector: CSS selector for the element

        Returns:
            Response dictionary
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to server"}

        try:
            import uuid

            request_id = str(uuid.uuid4())
            message = {
                "type": "dom_command",
                "requestId": request_id,
                "command": {
                    "type": "click",
                    "params": {"selector": selector, "index": 0},
                },
            }
            await self.websocket.send(json.dumps(message))

            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract_content(self, selector: str) -> Dict[str, Any]:
        """Extract content from element.

        Args:
            selector: CSS selector for the element

        Returns:
            Response dictionary with content
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to server"}

        try:
            import uuid

            request_id = str(uuid.uuid4())
            message = {
                "type": "dom_command",
                "requestId": request_id,
                "command": {
                    "type": "get_element",
                    "params": {"selector": selector, "index": 0},
                },
            }
            await self.websocket.send(json.dumps(message))

            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def take_screenshot(self, output: str = "screenshot.png") -> Dict[str, Any]:
        """Take a screenshot.

        Args:
            output: Output filename

        Returns:
            Response dictionary
        """
        # Screenshot functionality would require integration with ScreenshotService
        return {
            "success": False,
            "error": "Screenshot functionality requires server integration",
        }

    async def check_server_status(self) -> Dict[str, Any]:
        """Check if server is running and get status.

        Returns:
            Server status dictionary
        """
        try:
            uri = f"ws://{self.host}:{self.port}"
            async with websockets.connect(uri, open_timeout=2) as ws:
                # Send server info request
                await ws.send(json.dumps({"type": "server_info"}))

                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(response)
                    return {"success": True, "status": "running", "info": data}
                except asyncio.TimeoutError:
                    return {"success": True, "status": "running", "info": {}}

        except Exception as e:
            return {"success": False, "status": "not_running", "error": str(e)}

    async def extract_readable_content(self, timeout: float = 10.0) -> Dict[str, Any]:
        """Extract readable content using Readability.js."""
        message = {
            "type": "extract_content",
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
        }
        return await self._send_and_wait(message, timeout)

    async def extract_semantic_dom(
        self,
        include_headings: bool = True,
        include_landmarks: bool = True,
        include_links: bool = True,
        include_forms: bool = True,
        max_text_length: int = 100,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Extract semantic DOM structure."""
        message = {
            "type": "extract_semantic_dom",
            "requestId": str(uuid.uuid4()),
            "options": {
                "include_headings": include_headings,
                "include_landmarks": include_landmarks,
                "include_links": include_links,
                "include_forms": include_forms,
                "max_text_length": max_text_length,
            },
            "timestamp": datetime.now().isoformat(),
        }
        return await self._send_and_wait(message, timeout)

    async def extract_element(self, selector: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Extract content from specific element."""
        message = {
            "type": "dom_command",
            "requestId": str(uuid.uuid4()),
            "command": {
                "type": "get_element",
                "params": {"selector": selector, "index": 0},
            },
        }
        return await self._send_and_wait(message, timeout)

    async def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """Scroll the page.

        Args:
            direction: Direction to scroll (up or down)
            amount: Pixels to scroll

        Returns:
            Response dictionary
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to server"}

        try:
            message = {
                "type": "dom_command",
                "requestId": str(uuid.uuid4()),
                "command": {
                    "type": "scroll",
                    "params": {"direction": direction, "amount": amount},
                },
            }
            await self.websocket.send(json.dumps(message))
            return {"success": True, "direction": direction, "amount": amount}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def submit_form(self, selector: str) -> Dict[str, Any]:
        """Submit a form.

        Args:
            selector: CSS selector for the form

        Returns:
            Response dictionary
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to server"}

        try:
            message = {
                "type": "dom_command",
                "requestId": str(uuid.uuid4()),
                "command": {
                    "type": "submit",
                    "params": {"selector": selector, "index": 0},
                },
            }
            await self.websocket.send(json.dumps(message))
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def find_active_port(
    start_port: int = PORT_RANGE_START, end_port: int = PORT_RANGE_END
) -> Optional[int]:
    """Find the active WebSocket server port.

    First checks service registry, then scans port range.

    Args:
        start_port: Starting port to scan
        end_port: Ending port to scan

    Returns:
        Active port number or None if not found
    """
    # Check service registry first
    info = read_service_info()
    if info and info.get("port"):
        port = info["port"]
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, open_timeout=0.5):
                return port
        except Exception:
            pass

    # Fallback to port scanning
    for port in range(start_port, end_port + 1):
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, open_timeout=0.5):
                return port
        except Exception:
            continue
    return None
