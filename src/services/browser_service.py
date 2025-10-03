"""Browser service for handling browser communication."""

import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import BrowserState, ConsoleMessage

logger = logging.getLogger(__name__)


class BrowserService:
    """Service for handling browser connections and messages."""

    def __init__(self, storage_service=None, dom_interaction_service=None):
        """Initialize browser service.

        Args:
            storage_service: Optional storage service for persistence
            dom_interaction_service: Optional DOM interaction service for element manipulation
        """
        self.storage_service = storage_service
        self.dom_interaction_service = dom_interaction_service
        self.browser_state = BrowserState()
        self._message_buffer: Dict[int, deque] = {}
        self._buffer_tasks: Dict[int, asyncio.Task] = {}
        self._buffer_interval = 2.5  # seconds
        # For async request/response with creation time tracking
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 30.0  # seconds - cleanup check interval
        self._request_timeout = 120.0  # seconds - max age for pending requests

    async def handle_browser_connect(self, connection_info: Dict[str, Any]) -> None:
        """Handle browser connection event.

        Args:
            connection_info: Connection information
        """
        websocket = connection_info["websocket"]
        remote_address = connection_info["remote_address"]

        # Extract port from remote address
        port = (
            remote_address[1]
            if isinstance(remote_address, tuple)
            else self._get_next_port()
        )

        # Add connection to state
        await self.browser_state.add_connection(
            port=port, websocket=websocket, user_agent=connection_info.get("user_agent")
        )

        # Initialize message buffer for this port
        if port not in self._message_buffer:
            self._message_buffer[port] = deque(maxlen=1000)

        # Start buffer flush task
        if port not in self._buffer_tasks or self._buffer_tasks[port].done():
            self._buffer_tasks[port] = asyncio.create_task(
                self._flush_buffer_periodically(port)
            )

        logger.info(f"Browser connected on port {port} from {remote_address}")

        # Send acknowledgment
        await websocket.send(
            json.dumps(
                {
                    "type": "connection_ack",
                    "port": port,
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
        connection = await self.browser_state.get_connection(port)

        if not connection or not connection.websocket:
            logger.warning(f"No active browser connection on port {port}")
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
        connection = await self.browser_state.get_connection(port)

        if not connection or not connection.websocket:
            logger.warning(f"No active browser connection on port {port}")
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
        connection = await self.browser_state.get_connection(port)

        if not connection or not connection.websocket:
            logger.warning(f"No active browser connection on port {port}")
            return {"success": False, "error": "No active browser connection"}

        try:
            import uuid

            request_id = str(uuid.uuid4())

            # Create a future to wait for response with creation time tracking
            response_future = asyncio.Future()
            self._pending_requests[request_id] = {
                "future": response_future,
                "created_at": datetime.now(),
            }

            await connection.websocket.send(
                json.dumps(
                    {
                        "type": "extract_content",
                        "requestId": request_id,
                        "tabId": tab_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            logger.info(
                f"Sent content extraction request to port {port}, tab {tab_id or 'active'}"
            )

            try:
                # Wait for response with timeout
                result = await asyncio.wait_for(response_future, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Content extraction timed out after {timeout}s")
                return {
                    "success": False,
                    "error": f"Content extraction timed out after {timeout} seconds",
                }
            finally:
                # Clean up pending request
                self._pending_requests.pop(request_id, None)

        except Exception as e:
            logger.error(f"Failed to send content extraction command: {e}")
            return {"success": False, "error": str(e)}

    async def handle_content_extracted(self, data: Dict[str, Any]) -> None:
        """Handle content extraction response from browser.

        Args:
            data: Response data including extracted content
        """
        request_id = data.get("requestId")
        if request_id and request_id in self._pending_requests:
            request_data = self._pending_requests[request_id]
            future = request_data["future"]
            if not future.done():
                response = data.get("response", {})
                future.set_result(response)
                logger.info(
                    f"Received content extraction response for request {request_id}"
                )
        else:
            logger.warning(
                f"Received content extraction response for unknown request: {request_id}"
            )

    async def _cleanup_pending_requests(self) -> None:
        """Clean up orphaned or expired pending requests.

        Removes:
        - Requests older than _request_timeout (2 minutes)
        - Completed futures that weren't cleaned up
        """
        now = datetime.now()
        to_remove = []

        for request_id, request_data in self._pending_requests.items():
            future = request_data["future"]
            created_at = request_data["created_at"]
            age = (now - created_at).total_seconds()

            # Remove if completed or expired
            if future.done():
                to_remove.append(request_id)
                logger.debug(f"Cleaning up completed request {request_id}")
            elif age > self._request_timeout:
                to_remove.append(request_id)
                # Cancel the future if it's still pending
                if not future.done():
                    future.cancel()
                logger.warning(
                    f"Cleaning up expired request {request_id} (age: {age:.1f}s)"
                )

        # Remove stale requests
        for request_id in to_remove:
            self._pending_requests.pop(request_id, None)

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} stale pending requests")

    async def _cleanup_pending_requests_loop(self) -> None:
        """Periodically clean up orphaned pending requests."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_pending_requests()
            except asyncio.CancelledError:
                # Final cleanup before cancellation
                await self._cleanup_pending_requests()
                break
            except Exception as e:
                logger.error(f"Error in pending requests cleanup task: {e}")

    async def start_cleanup_task(self) -> None:
        """Start the background cleanup task for pending requests."""
        if self._cleanup_task and not self._cleanup_task.done():
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_pending_requests_loop())
        logger.info("Started pending requests cleanup task")

    async def cleanup(self) -> None:
        """Clean up all resources and background tasks."""
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Cancel all buffer tasks
        for port, task in list(self._buffer_tasks.items()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Final cleanup of pending requests
        await self._cleanup_pending_requests()

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
