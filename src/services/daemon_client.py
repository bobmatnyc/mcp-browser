"""Daemon client for MCP process to communicate with running WebSocket daemon."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import websockets

logger = logging.getLogger(__name__)


class DaemonClient:
    """Client for MCP process to communicate with running WebSocket daemon.

    This enables MCP tools (running in stdio mode) to relay commands to the
    browser extension via the WebSocket daemon that manages extension connections.

    Architecture:
        MCP stdio process → DaemonClient → WebSocket daemon → Browser extension
    """

    def __init__(self, host: str = "localhost", port: int = 8851):
        """Initialize daemon client.

        Args:
            host: WebSocket daemon host
            port: WebSocket daemon port
        """
        self.host = host
        self.port = port
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Connect to WebSocket daemon.

        Returns:
            True if connected successfully
        """
        try:
            uri = f"ws://{self.host}:{self.port}"
            self.websocket = await websockets.connect(
                uri, open_timeout=2.0, ping_interval=20, ping_timeout=10
            )
            self._connected = True

            # Start background listener for responses
            self._listen_task = asyncio.create_task(self._listen_for_responses())

            logger.info(f"DaemonClient connected to {uri}")
            return True
        except Exception as e:
            logger.warning(
                f"Failed to connect to daemon at {self.host}:{self.port}: {e}"
            )
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket daemon."""
        self._connected = False

        # Cancel listener task
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def _listen_for_responses(self) -> None:
        """Background task to listen for responses from daemon."""
        try:
            while self._connected and self.websocket:
                try:
                    msg = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    data = json.loads(msg)

                    # Check if this is a response to a pending request
                    request_id = data.get("requestId")
                    if request_id and request_id in self._pending_requests:
                        future = self._pending_requests[request_id]
                        if not future.done():
                            future.set_result(data)

                except asyncio.TimeoutError:
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse daemon response: {e}")
                except Exception as e:
                    logger.warning(f"Error receiving from daemon: {e}")
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Listener task error: {e}")

    async def send_command(
        self, message: Dict[str, Any], timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Send command to daemon and wait for response.

        Args:
            message: Command message to send
            timeout: Response timeout in seconds

        Returns:
            Response dictionary
        """
        if not self._connected or not self.websocket:
            return {"success": False, "error": "Not connected to daemon"}

        # Ensure message has requestId
        request_id = message.get("requestId") or str(uuid.uuid4())
        message["requestId"] = request_id
        message["timestamp"] = message.get("timestamp") or datetime.now().isoformat()

        # Create future for response
        response_future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = response_future

        try:
            # Send command to daemon
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent command to daemon: {message['type']}")

            # Wait for response
            try:
                result = await asyncio.wait_for(response_future, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                return {
                    "success": False,
                    "error": f"Timeout waiting for daemon response after {timeout}s",
                }
        except Exception as e:
            return {"success": False, "error": f"Failed to send command: {e}"}
        finally:
            self._pending_requests.pop(request_id, None)

    async def send_fire_and_forget(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send command without waiting for response.

        Used for commands like navigate that don't send acknowledgments.

        Args:
            message: Command message to send

        Returns:
            Success indicator (not a response from daemon)
        """
        if not self._connected or not self.websocket:
            return {"success": False, "error": "Not connected to daemon"}

        message["timestamp"] = message.get("timestamp") or datetime.now().isoformat()

        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent fire-and-forget command: {message['type']}")
            return {"success": True, "method": "extension"}
        except Exception as e:
            return {"success": False, "error": f"Failed to send command: {e}"}

    async def navigate(self, url: str, port: Optional[int] = None) -> Dict[str, Any]:
        """Navigate browser to URL via daemon.

        Args:
            url: URL to navigate to
            port: Optional port number (for compatibility)

        Returns:
            Success indicator (navigate is fire-and-forget)
        """
        message = {"type": "navigate", "url": url}
        if port:
            message["port"] = port

        # Navigate is fire-and-forget since extension doesn't send acknowledgment
        return await self.send_fire_and_forget(message)

    async def dom_action(
        self,
        action: str,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        value: Optional[str] = None,
        port: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute DOM action via daemon.

        Args:
            action: Action type (click, fill, submit, select, etc.)
            selector: CSS selector
            xpath: XPath selector
            value: Value for fill actions
            port: Optional port number

        Returns:
            Response dictionary
        """
        message = {"type": "dom_action", "action": action}

        if selector:
            message["selector"] = selector
        if xpath:
            message["xpath"] = xpath
        if value:
            message["value"] = value
        if port:
            message["port"] = port

        return await self.send_command(message)

    async def screenshot(
        self, url: Optional[str] = None, port: Optional[int] = None
    ) -> Dict[str, Any]:
        """Request screenshot via daemon.

        Args:
            url: Optional URL to navigate to first
            port: Optional port number

        Returns:
            Response dictionary with screenshot data
        """
        message = {"type": "capture_screenshot"}

        if url:
            message["url"] = url
        if port:
            message["port"] = port

        return await self.send_command(message, timeout=30.0)

    async def query_logs(
        self,
        port: Optional[int] = None,
        last_n: int = 100,
        level_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query console logs via daemon.

        Args:
            port: Optional port number
            last_n: Number of recent logs to retrieve
            level_filter: Log level filter

        Returns:
            Response dictionary with logs
        """
        message = {"type": "query_logs", "last_n": last_n}

        if port:
            message["port"] = port
        if level_filter:
            message["level_filter"] = level_filter

        return await self.send_command(message)

    async def get_capabilities(self) -> Dict[str, Any]:
        """Get daemon capabilities and connection status.

        Returns:
            Response dictionary with capabilities
        """
        message = {"type": "get_capabilities"}
        return await self.send_command(message)

    @property
    def is_connected(self) -> bool:
        """Check if connected to daemon."""
        return self._connected and self.websocket is not None
