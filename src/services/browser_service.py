"""Browser service for handling browser communication."""

import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import BrowserState, ConsoleMessage
from .async_request_response_service import AsyncRequestResponseService

logger = logging.getLogger(__name__)


class BrowserService:
    """Service for handling browser connections and messages."""

    def __init__(
        self,
        storage_service=None,
        dom_interaction_service=None,
        async_request_response_service=None,
    ):
        """Initialize browser service.

        Args:
            storage_service: Optional storage service for persistence
            dom_interaction_service: Optional DOM interaction service for element manipulation
            async_request_response_service: Optional async request/response service (auto-created if None)
        """
        self.storage_service = storage_service
        self.dom_interaction_service = dom_interaction_service
        self.browser_state = BrowserState()
        self._message_buffer: Dict[int, deque] = {}
        self._buffer_tasks: Dict[int, asyncio.Task] = {}
        self._buffer_interval = 2.5  # seconds

        # Async request/response service for WebSocket communication
        self._async_rr_service = (
            async_request_response_service or AsyncRequestResponseService()
        )

    async def handle_browser_connect(self, connection_info: Dict[str, Any]) -> None:
        """Handle browser connection event.

        Args:
            connection_info: Connection information
        """
        websocket = connection_info["websocket"]
        remote_address = connection_info["remote_address"]

        # Extract client port from remote address (ephemeral port for internal tracking)
        client_port = (
            remote_address[1]
            if isinstance(remote_address, tuple)
            else self._get_next_port()
        )

        # Extract server port from connection_info (listening port for user-facing API)
        server_port = connection_info.get("server_port", client_port)

        # SINGLE-CONNECTION MODE: Disconnect any existing browser connections
        # Only ONE browser tab should be connected at a time
        existing_connections = await self.browser_state.get_active_connections()
        for existing_port, existing_conn in existing_connections.items():
            if existing_conn.is_active and existing_conn.websocket:
                logger.info(
                    f"Disconnecting existing browser connection on port {existing_port} "
                    f"(new connection from port {client_port})"
                )
                try:
                    # Send disconnect message before closing
                    await existing_conn.websocket.send(
                        json.dumps(
                            {
                                "type": "disconnect",
                                "reason": "new_connection",
                                "message": "Another browser tab has connected",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )
                    await existing_conn.websocket.close()
                except Exception as e:
                    logger.warning(
                        f"Error closing existing connection on port {existing_port}: {e}"
                    )

        # Add connection to state with both ports
        await self.browser_state.add_connection(
            port=client_port,
            server_port=server_port,
            websocket=websocket,
            user_agent=connection_info.get("user_agent"),
        )

        # Initialize message buffer for this port
        if client_port not in self._message_buffer:
            self._message_buffer[client_port] = deque(maxlen=1000)

        # Start buffer flush task
        if (
            client_port not in self._buffer_tasks
            or self._buffer_tasks[client_port].done()
        ):
            self._buffer_tasks[client_port] = asyncio.create_task(
                self._flush_buffer_periodically(client_port)
            )

        logger.info(
            f"Browser connected: client_port={client_port}, server_port={server_port}, remote={remote_address}"
        )

        # Send acknowledgment with server_port (user-facing port)
        await websocket.send(
            json.dumps(
                {
                    "type": "connection_ack",
                    "port": server_port,  # Return server port to client
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    async def handle_browser_disconnect(self, connection_info: Dict[str, Any]) -> None:
        """Handle browser disconnection event.

        Args:
            connection_info: Connection information
        """
        remote_address = connection_info["remote_address"]
        port = remote_address[1] if isinstance(remote_address, tuple) else None

        if port:
            # Flush any remaining buffered messages
            await self._flush_buffer(port)

            # Cancel buffer task
            if port in self._buffer_tasks:
                self._buffer_tasks[port].cancel()
                del self._buffer_tasks[port]

            # Remove connection from state
            await self.browser_state.remove_connection(port)

            logger.info(f"Browser disconnected on port {port}")

    async def handle_console_message(self, data: Dict[str, Any]) -> None:
        """Handle console message from browser.

        Args:
            data: Message data including console information
        """
        try:
            # Extract port from connection info
            remote_address = data.get("_remote_address")
            port = (
                remote_address[1]
                if isinstance(remote_address, tuple)
                else self._get_current_port()
            )

            # Create console message
            message = ConsoleMessage.from_websocket_data(data, port)

            # Update browser state
            await self.browser_state.update_connection_activity(port)

            # Update URL if provided
            if message.url:
                await self.browser_state.update_connection_url(port, message.url)

            # Initialize buffer if not present
            if port not in self._message_buffer:
                self._message_buffer[port] = deque(maxlen=1000)

            # Add to buffer
            self._message_buffer[port].append(message)

            # Log high-priority messages immediately
            if message.level.value in ["error", "warn", "warning"]:
                logger.info(
                    f"[{message.level.value.upper()}] from port {port}: {message.message[:100]}"
                )

        except Exception as e:
            logger.error(f"Failed to handle console message: {e}")

    async def handle_batch_messages(self, data: Dict[str, Any]) -> None:
        """Handle batch of console messages.

        Args:
            data: Batch message data
        """
        messages = data.get("messages", [])
        remote_address = data.get("_remote_address")
        port = (
            remote_address[1]
            if isinstance(remote_address, tuple)
            else self._get_current_port()
        )

        for msg_data in messages:
            msg_data["_remote_address"] = remote_address
            await self.handle_console_message(msg_data)

        logger.debug(f"Processed batch of {len(messages)} messages from port {port}")

    async def handle_dom_response(self, data: Dict[str, Any]) -> None:
        """Handle DOM operation response from browser.

        Args:
            data: DOM response data
        """
        # Forward to DOM interaction service if available
        if hasattr(self, "dom_interaction_service"):
            await self.dom_interaction_service.handle_dom_response(data)
        else:
            logger.warning(
                "DOM response received but no DOM interaction service available"
            )

    async def _get_connection_with_fallback(
        self, port: Optional[int]
    ) -> Optional[Any]:  # Returns BrowserConnection
        """Get connection by port, with fallback to any active connection.

        BrowserState.get_connection now handles both server and client port lookups
        via the server_port_map.

        Args:
            port: Port number (supports both server port and client port, or None)

        Returns:
            BrowserConnection if found, None otherwise
        """
        if port is None:
            # No port specified, return any active connection
            return await self.browser_state.get_any_active_connection()

        # BrowserState.get_connection now automatically handles server→client port mapping
        connection = await self.browser_state.get_connection(port)

        if connection and connection.is_active:
            return connection

        # Fallback to any active connection if specific port not found
        return await self.browser_state.get_any_active_connection()

    async def send_dom_command(
        self, port: int, command: Dict[str, Any], tab_id: Optional[int] = None
    ) -> bool:
        """Send a DOM command to the browser.

        Args:
            port: Port number
            command: DOM command to send
            tab_id: Optional specific tab ID

        Returns:
            True if command was sent successfully
        """
        connection = await self._get_connection_with_fallback(port)

        if not connection or not connection.websocket:
            logger.warning(f"No active browser connection for port {port}")
            return False

        try:
            import uuid

            request_id = str(uuid.uuid4())

            await connection.websocket.send(
                json.dumps(
                    {
                        "type": "dom_command",
                        "requestId": request_id,
                        "tabId": tab_id,
                        "command": command,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            logger.debug(f"Sent DOM command to port {port}: {command.get('type')}")
            return True

        except Exception as e:
            logger.error(f"Failed to send DOM command: {e}")
            return False

    async def navigate_browser(self, port: int, url: str) -> bool:
        """Navigate browser to a URL.

        Args:
            port: Port number
            url: URL to navigate to

        Returns:
            True if navigation command was sent successfully
        """
        connection = await self._get_connection_with_fallback(port)

        if not connection or not connection.websocket:
            logger.warning(f"No active browser connection for port {port}")
            return False

        try:
            await connection.websocket.send(
                json.dumps(
                    {
                        "type": "navigate",
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            await self.browser_state.update_connection_url(port, url)
            logger.info(f"Sent navigation command to port {port}: {url}")
            return True

        except Exception as e:
            logger.error(f"Failed to send navigation command: {e}")
            return False

    async def query_logs(
        self, port: int, last_n: int = 100, level_filter: Optional[List[str]] = None
    ) -> List[ConsoleMessage]:
        """Query console logs for a port.

        Args:
            port: Port number
            last_n: Number of recent messages to return
            level_filter: Optional filter by log levels

        Returns:
            List of console messages
        """
        messages = []

        # Get messages from buffer
        if port in self._message_buffer:
            buffer_messages = list(self._message_buffer[port])
            for msg in buffer_messages:
                if msg.matches_filter(level_filter):
                    messages.append(msg)

        # Get messages from storage if available
        if self.storage_service:
            stored_messages = await self.storage_service.query_messages(
                port=port,
                last_n=max(0, last_n - len(messages)),
                level_filter=level_filter,
            )
            messages = stored_messages + messages

        # Return last N messages
        return messages[-last_n:] if last_n else messages

    async def extract_content(
        self, port: int, tab_id: Optional[int] = None, timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Extract readable content from a browser tab using Readability.

        Args:
            port: Port number
            tab_id: Optional specific tab ID
            timeout: Timeout for extraction operation

        Returns:
            Dict containing extracted content or error information
        """
        connection = await self._get_connection_with_fallback(port)

        if not connection or not connection.websocket:
            logger.warning(f"No active browser connection for port {port}")
            return {"success": False, "error": "No active browser connection"}

        try:
            logger.info(
                f"Sending content extraction request to port {port}, tab {tab_id or 'active'}"
            )

            result = await self._async_rr_service.send_request(
                websocket=connection.websocket,
                message_type="extract_content",
                timeout=timeout,
                tab_id=tab_id,
            )

            if result is None:
                # Timeout occurred
                return {
                    "success": False,
                    "error": f"Content extraction timed out after {timeout} seconds",
                }

            return result

        except Exception as e:
            logger.error(f"Failed to send content extraction command: {e}")
            return {"success": False, "error": str(e)}

    async def extract_semantic_dom(
        self,
        port: int,
        tab_id: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Extract semantic DOM structure from browser tab.

        Args:
            port: Port number
            tab_id: Optional specific tab ID
            options: Optional extraction options (include_headings, include_links, etc.)
            timeout: Timeout for extraction operation

        Returns:
            Dict containing semantic DOM structure or error information
        """
        connection = await self._get_connection_with_fallback(port)

        if not connection or not connection.websocket:
            return {"success": False, "error": "No active browser connection"}

        try:
            logger.info(f"Sending semantic DOM extraction request to port {port}")

            result = await self._async_rr_service.send_request(
                websocket=connection.websocket,
                message_type="extract_semantic_dom",
                payload={"options": options or {}},
                timeout=timeout,
                tab_id=tab_id,
            )

            if result is None:
                # Timeout occurred
                return {"success": False, "error": f"Timeout after {timeout}s"}

            return result

        except Exception as e:
            logger.error(f"Failed to extract semantic DOM: {e}")
            return {"success": False, "error": str(e)}

    async def handle_content_extracted(self, data: Dict[str, Any]) -> None:
        """Handle content extraction response from browser.

        Args:
            data: Response data including extracted content
        """
        request_id = data.get("requestId")
        response = data.get("response", {})

        if request_id:
            success = await self._async_rr_service.handle_response(request_id, response)
            if success:
                logger.info(
                    f"Received content extraction response for request {request_id}"
                )
        else:
            logger.warning("Received content extraction response without requestId")

    async def handle_semantic_dom_extracted(self, data: Dict[str, Any]) -> None:
        """Handle semantic DOM extraction response from browser.

        Args:
            data: Response data including semantic DOM structure
        """
        request_id = data.get("requestId")
        response = data.get("response", {})

        if request_id:
            success = await self._async_rr_service.handle_response(request_id, response)
            if success:
                logger.info(f"Received semantic DOM for request {request_id}")

    async def capture_screenshot_via_extension(
        self, port: int, timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Capture screenshot via browser extension.

        Args:
            port: Port number
            timeout: Timeout for capture operation

        Returns:
            Dict with success, data (base64), and mimeType or error
        """
        connection = await self._get_connection_with_fallback(port)

        if not connection or not connection.websocket:
            return {"success": False, "error": "No active browser connection"}

        try:
            logger.info(f"Sending screenshot capture request to port {port}")

            result = await self._async_rr_service.send_request(
                websocket=connection.websocket,
                message_type="capture_screenshot",
                timeout=timeout,
            )

            if result is None:
                # Timeout occurred
                return {
                    "success": False,
                    "error": f"Screenshot timed out after {timeout}s",
                }

            return result

        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return {"success": False, "error": str(e)}

    async def handle_screenshot_captured(self, data: Dict[str, Any]) -> None:
        """Handle screenshot captured response from extension.

        Args:
            data: Response data including screenshot base64 data
        """
        request_id = data.get("requestId")

        if request_id:
            success = await self._async_rr_service.handle_response(request_id, data)
            if success:
                logger.info(
                    f"Received screenshot_captured response for request {request_id}"
                )

    async def start_cleanup_task(self) -> None:
        """Start the background cleanup task for pending requests."""
        await self._async_rr_service.start_cleanup_task()
        logger.info("Started async request/response cleanup task")

    async def cleanup(self) -> None:
        """Clean up all resources and background tasks."""
        # Shutdown async request/response service
        await self._async_rr_service.shutdown()

        # Cancel all buffer tasks
        for port, task in list(self._buffer_tasks.items()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("BrowserService cleanup completed")

    async def _flush_buffer(self, port: int) -> None:
        """Flush message buffer for a port.

        Args:
            port: Port number
        """
        if port not in self._message_buffer or not self._message_buffer[port]:
            return

        messages = list(self._message_buffer[port])
        self._message_buffer[port].clear()

        # Store messages if storage service is available
        if self.storage_service and messages:
            try:
                await self.storage_service.store_messages_batch(messages)
                logger.debug(f"Flushed {len(messages)} messages for port {port}")
            except Exception as e:
                logger.error(f"Failed to store messages: {e}")
                # Put messages back in buffer on failure
                self._message_buffer[port].extend(messages)

    async def _flush_buffer_periodically(self, port: int) -> None:
        """Periodically flush message buffer for a port.

        Args:
            port: Port number
        """
        while True:
            try:
                await asyncio.sleep(self._buffer_interval)
                await self._flush_buffer(port)
            except asyncio.CancelledError:
                # Final flush before cancellation
                await self._flush_buffer(port)
                break
            except Exception as e:
                logger.error(f"Error in buffer flush task: {e}")

    def _get_next_port(self) -> int:
        """Get next available port number.

        Returns:
            Next available port number
        """
        # Simple incrementing port assignment
        used_ports = set(self._message_buffer.keys())
        for port in range(8875, 8895):
            if port not in used_ports:
                return port
        return 8875

    def _get_current_port(self) -> int:
        """Get current active port.

        Returns:
            Current active port or default
        """
        if self._message_buffer:
            return next(iter(self._message_buffer.keys()))
        return 8875

    async def get_browser_stats(self) -> Dict[str, Any]:
        """Get browser statistics.

        Returns:
            Dictionary with browser statistics
        """
        stats = await self.browser_state.get_connection_stats()

        # Add buffer information
        stats["buffers"] = {
            port: len(buffer) for port, buffer in self._message_buffer.items()
        }

        return stats
