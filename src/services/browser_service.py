"""Browser service for handling browser communication."""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

from ..models import ConsoleMessage, BrowserState

logger = logging.getLogger(__name__)


class BrowserService:
    """Service for handling browser connections and messages."""

    def __init__(self, storage_service=None):
        """Initialize browser service.

        Args:
            storage_service: Optional storage service for persistence
        """
        self.storage_service = storage_service
        self.browser_state = BrowserState()
        self._message_buffer: Dict[int, deque] = {}
        self._buffer_tasks: Dict[int, asyncio.Task] = {}
        self._buffer_interval = 2.5  # seconds

    async def handle_browser_connect(self, connection_info: Dict[str, Any]) -> None:
        """Handle browser connection event.

        Args:
            connection_info: Connection information
        """
        websocket = connection_info['websocket']
        remote_address = connection_info['remote_address']

        # Extract port from remote address
        port = remote_address[1] if isinstance(remote_address, tuple) else self._get_next_port()

        # Add connection to state
        await self.browser_state.add_connection(
            port=port,
            websocket=websocket,
            user_agent=connection_info.get('user_agent')
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
        await websocket.send(json.dumps({
            'type': 'connection_ack',
            'port': port,
            'timestamp': datetime.now().isoformat()
        }))

    async def handle_browser_disconnect(self, connection_info: Dict[str, Any]) -> None:
        """Handle browser disconnection event.

        Args:
            connection_info: Connection information
        """
        remote_address = connection_info['remote_address']
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
            remote_address = data.get('_remote_address')
            port = remote_address[1] if isinstance(remote_address, tuple) else self._get_current_port()

            # Create console message
            message = ConsoleMessage.from_websocket_data(data, port)

            # Update browser state
            await self.browser_state.update_connection_activity(port)

            # Update URL if provided
            if message.url:
                await self.browser_state.update_connection_url(port, message.url)

            # Add to buffer
            if port in self._message_buffer:
                self._message_buffer[port].append(message)

            # Log high-priority messages immediately
            if message.level.value in ['error', 'warn', 'warning']:
                logger.info(f"[{message.level.value.upper()}] from port {port}: {message.message[:100]}")

        except Exception as e:
            logger.error(f"Failed to handle console message: {e}")

    async def handle_batch_messages(self, data: Dict[str, Any]) -> None:
        """Handle batch of console messages.

        Args:
            data: Batch message data
        """
        messages = data.get('messages', [])
        remote_address = data.get('_remote_address')
        port = remote_address[1] if isinstance(remote_address, tuple) else self._get_current_port()

        for msg_data in messages:
            msg_data['_remote_address'] = remote_address
            await self.handle_console_message(msg_data)

        logger.debug(f"Processed batch of {len(messages)} messages from port {port}")

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
            await connection.websocket.send(json.dumps({
                'type': 'navigate',
                'url': url,
                'timestamp': datetime.now().isoformat()
            }))

            await self.browser_state.update_connection_url(port, url)
            logger.info(f"Sent navigation command to port {port}: {url}")
            return True

        except Exception as e:
            logger.error(f"Failed to send navigation command: {e}")
            return False

    async def query_logs(
        self,
        port: int,
        last_n: int = 100,
        level_filter: Optional[List[str]] = None
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
                level_filter=level_filter
            )
            messages = stored_messages + messages

        # Return last N messages
        return messages[-last_n:] if last_n else messages

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
        stats['buffers'] = {
            port: len(buffer)
            for port, buffer in self._message_buffer.items()
        }

        return stats