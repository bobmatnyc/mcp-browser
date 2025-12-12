"""WebSocket service for browser communication."""

import asyncio
import hashlib
import json
import logging
import os
from collections import deque
from typing import Any, Callable, Dict, List, Optional, Set

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class WebSocketService:
    """WebSocket server with port auto-discovery."""

    def __init__(
        self, start_port: int = 8875, end_port: int = 8895, host: str = "localhost"
    ):
        """Initialize WebSocket service.

        Args:
            start_port: Starting port for auto-discovery
            end_port: Ending port for auto-discovery
            host: Host to bind to
        """
        self.start_port = start_port
        self.end_port = end_port
        self.host = host
        self.port: Optional[int] = None
        self.server: Optional[websockets.WebSocketServer] = None
        self._connections: Set[WebSocketServerProtocol] = set()
        self._message_handlers: Dict[str, Callable] = {}
        self._connection_handlers: Dict[str, Callable] = {}

        # State recovery components
        self.message_buffer: deque = deque(maxlen=1000)  # Keep last 1000 messages
        self.current_sequence: int = 0

        # Generate project identity
        self.project_identity = self._generate_project_identity()
        logger.info(f"Project identity: {self.project_identity['project_id']} ({self.project_identity['project_name']})")

    def _generate_project_identity(self) -> dict:
        """Generate stable identity for this project.

        Identity is based on the working directory, making it stable across
        restarts but unique per project.
        """
        project_path = os.getcwd()
        # Generate stable 8-char ID from path hash
        project_id = hashlib.md5(project_path.encode()).hexdigest()[:8]
        project_name = os.path.basename(project_path)

        return {
            'project_id': project_id,
            'project_name': project_name,
            'project_path': project_path
        }

    def _get_version(self) -> str:
        """Get the current version string."""
        try:
            from .._version import __version__
            return __version__
        except ImportError:
            return 'unknown'

    async def start(self) -> int:
        """Start WebSocket server with port auto-discovery.

        Returns:
            Port number the server is listening on

        Raises:
            RuntimeError: If no available port is found
        """
        for port in range(self.start_port, self.end_port + 1):
            try:
                self.server = await websockets.serve(
                    self._handle_connection,
                    self.host,
                    port,
                    ping_interval=20,
                    ping_timeout=10,
                )
                self.port = port
                logger.info(f"WebSocket server started on {self.host}:{port}")
                return port
            except OSError as e:
                if port == self.end_port:
                    raise RuntimeError(
                        f"No available port found in range {self.start_port}-{self.end_port}"
                    ) from e
                continue

        raise RuntimeError("Failed to start WebSocket server")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if self.server:
            # Close all connections
            for conn in list(self._connections):
                await conn.close()

            self.server.close()
            await self.server.wait_closed()
            self.server = None
            self.port = None
            logger.info("WebSocket server stopped")

    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a specific message type.

        Args:
            message_type: Type of message to handle
            handler: Async function to handle the message
        """
        self._message_handlers[message_type] = handler

    def register_connection_handler(self, event: str, handler: Callable) -> None:
        """Register a handler for connection events.

        Args:
            event: Event type ('connect' or 'disconnect')
            handler: Async function to handle the event
        """
        self._connection_handlers[event] = handler

    async def handle_connection_init(self, message: dict, websocket: WebSocketServerProtocol) -> None:
        """Handle connection initialization handshake.

        Args:
            message: The connection_init message
            websocket: WebSocket connection
        """
        last_sequence = message.get('lastSequence', 0)
        extension_version = message.get('extensionVersion', 'unknown')
        capabilities = message.get('capabilities', [])

        logger.info(f"Connection init from extension v{extension_version}, lastSequence={last_sequence}")
        logger.info(f"Client capabilities: {capabilities}")

        # Find messages the client missed
        replay_messages = self._get_messages_after_sequence(last_sequence)

        # Send connection acknowledgment with replay
        ack_message = {
            'type': 'connection_ack',
            'serverVersion': self._get_version(),
            'project_id': self.project_identity['project_id'],
            'project_name': self.project_identity['project_name'],
            'currentSequence': self.current_sequence,
            'replay': replay_messages[:100]  # Limit replay to 100 messages
        }

        await self.send_message(websocket, ack_message)
        logger.info(f"Sent connection_ack with {len(replay_messages[:100])} replayed messages")

    async def handle_gap_recovery(self, message: dict, websocket: WebSocketServerProtocol) -> None:
        """Handle gap recovery request - send messages in requested sequence range.

        Args:
            message: Gap recovery request message
            websocket: WebSocket connection
        """
        from_sequence = message.get('fromSequence', 0)
        to_sequence = message.get('toSequence', 0)

        logger.info(f"Gap recovery requested: sequences {from_sequence} to {to_sequence}")

        # Validate request
        if from_sequence <= 0 or to_sequence < from_sequence:
            logger.warning(f"Invalid gap recovery request: {from_sequence} to {to_sequence}")
            await self.send_message(websocket, {
                'type': 'gap_recovery_response',
                'success': False,
                'error': 'Invalid sequence range',
                'messages': []
            })
            return

        # Limit recovery size to prevent abuse
        max_recovery = 100
        if to_sequence - from_sequence + 1 > max_recovery:
            to_sequence = from_sequence + max_recovery - 1
            logger.warning(f"Gap recovery limited to {max_recovery} messages")

        # Find messages in range
        recovery_messages = self._get_messages_in_range(from_sequence, to_sequence)

        # Send recovery response
        await self.send_message(websocket, {
            'type': 'gap_recovery_response',
            'success': True,
            'fromSequence': from_sequence,
            'toSequence': to_sequence,
            'messages': recovery_messages
        })

        logger.info(f"Gap recovery complete: sent {len(recovery_messages)} messages")

    def _get_messages_after_sequence(self, last_sequence: int) -> List[dict]:
        """Get messages with sequence > last_sequence.

        Args:
            last_sequence: Last sequence number received by client

        Returns:
            List of messages that occurred after the given sequence
        """
        return [
            msg for msg in self.message_buffer
            if msg.get('sequence', 0) > last_sequence
        ]

    def _get_messages_in_range(self, from_seq: int, to_seq: int) -> List[Dict[str, Any]]:
        """Get messages with sequence numbers in the given range (inclusive).

        Args:
            from_seq: Starting sequence number (inclusive)
            to_seq: Ending sequence number (inclusive)

        Returns:
            List of messages in the sequence range
        """
        return [
            msg for msg in self.message_buffer
            if msg.get('sequence', 0) >= from_seq and msg.get('sequence', 0) <= to_seq
        ]

    def _add_sequence(self, message: dict) -> dict:
        """Add sequence number to message and buffer it.

        Args:
            message: Message to sequence

        Returns:
            Message with sequence number added
        """
        self.current_sequence += 1
        message['sequence'] = self.current_sequence
        self.message_buffer.append(message.copy())
        return message

    async def _handle_connection(
        self, websocket: WebSocketServerProtocol, path: str = None
    ) -> None:
        """Handle a WebSocket connection.

        Args:
            websocket: WebSocket connection
            path: Request path (optional for newer websockets versions)
        """
        # Handle both old and new websockets library signatures
        if path is None:
            path = websocket.path if hasattr(websocket, "path") else "/"

        self._connections.add(websocket)
        connection_info = {
            "remote_address": websocket.remote_address,
            "path": path,
            "websocket": websocket,
        }

        # Notify connection handler
        if "connect" in self._connection_handlers:
            try:
                await self._connection_handlers["connect"](connection_info)
            except Exception as e:
                logger.error(f"Error in connection handler: {e}")

        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"Connection closed from {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
        finally:
            self._connections.discard(websocket)

            # Notify disconnection handler
            if "disconnect" in self._connection_handlers:
                try:
                    await self._connection_handlers["disconnect"](connection_info)
                except Exception as e:
                    logger.error(f"Error in disconnection handler: {e}")

    async def _handle_message(
        self, websocket: WebSocketServerProtocol, message: str
    ) -> None:
        """Handle an incoming WebSocket message.

        Args:
            websocket: WebSocket connection
            message: Raw message string
        """
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")

            # Handle connection initialization handshake
            if message_type == "connection_init":
                await self.handle_connection_init(data, websocket)
                return

            # Handle gap recovery request
            if message_type == "gap_recovery":
                await self.handle_gap_recovery(data, websocket)
                return

            # Handle heartbeat - respond with pong immediately
            if message_type == "heartbeat":
                pong_response = {
                    "type": "pong",
                    "timestamp": data.get("timestamp", 0)
                }
                await self.send_message(websocket, pong_response)
                return

            # Handle server info request
            if message_type == "server_info":
                server_info = {
                    "type": "server_info_response",
                    "project_id": self.project_identity['project_id'],
                    "project_name": self.project_identity['project_name'],
                    "project_path": self.project_identity['project_path'],
                    "port": self.port,
                    "version": self._get_version(),
                    "capabilities": ['console_capture', 'dom_interaction', 'screenshots']
                }
                await self.send_message(websocket, server_info)
                return

            # Handle response messages from extension - broadcast back to other connections (CLI/MCP clients)
            response_messages = ['content_extracted', 'dom_response', 'page_content', 'semantic_dom_extracted']
            if message_type in response_messages:
                logger.info(f"Broadcasting response message: {message_type}")
                other_connections = [c for c in self._connections if c != websocket]
                for conn in other_connections:
                    try:
                        await conn.send(json.dumps(data))
                        logger.debug(f"Sent {message_type} response to client")
                    except Exception as e:
                        logger.error(f"Failed to send response to client: {e}")
                # Also call handler if registered (for MCP tool Future resolution)
                handler = self._message_handlers.get(message_type)
                if handler:
                    await handler(data)
                return

            # Handle browser control commands - broadcast to all connections (including browser extension)
            browser_commands = ['navigate', 'click', 'fill_field', 'scroll', 'get_page_content', 'dom_command', 'extract_content', 'extract_semantic_dom']
            if message_type in browser_commands:
                logger.info(f"Broadcasting browser command: {message_type}")
                # Check if there are other connections besides the sender
                other_connections = [c for c in self._connections if c != websocket]
                if not other_connections:
                    logger.warning(f"No browser extension connected to receive command: {message_type}")
                    # Send error back to sender
                    await self.send_message(websocket, {
                        "type": "error",
                        "message": "No browser extension connected. Please ensure the extension is installed and connected.",
                        "command": message_type
                    })
                    return
                # Broadcast to all other connections (browser extensions)
                for conn in other_connections:
                    try:
                        await conn.send(json.dumps(data))
                        logger.debug(f"Sent {message_type} command to browser extension")
                    except Exception as e:
                        logger.error(f"Failed to send command to browser: {e}")
                return

            # Add connection info to data
            data["_websocket"] = websocket
            data["_remote_address"] = websocket.remote_address

            # Find and call appropriate handler
            handler = self._message_handlers.get(
                message_type, self._message_handlers.get("default")
            )

            if handler:
                await handler(data)
            else:
                logger.warning(f"No handler for message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def send_message(
        self, websocket: WebSocketServerProtocol, message: Dict[str, Any], add_sequence: bool = False
    ) -> None:
        """Send a message to a specific WebSocket connection.

        Args:
            websocket: WebSocket connection
            message: Message to send
            add_sequence: If True, add sequence number and buffer message for replay
        """
        try:
            if add_sequence:
                message = self._add_sequence(message)
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def broadcast_message(self, message: Dict[str, Any], add_sequence: bool = False) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: Message to broadcast
            add_sequence: If True, add sequence number and buffer message for replay
        """
        if not self._connections:
            return

        if add_sequence:
            message = self._add_sequence(message)

        message_str = json.dumps(message)
        tasks = []

        for websocket in self._connections:
            tasks.append(websocket.send(message_str))

        # Send to all connections concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any errors
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to broadcast message: {result}")

    def get_connection_count(self) -> int:
        """Get the number of active connections.

        Returns:
            Number of active connections
        """
        return len(self._connections)

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information.

        Returns:
            Dictionary with server information
        """
        return {
            "host": self.host,
            "port": self.port,
            "is_running": self.server is not None,
            "connection_count": self.get_connection_count(),
            "port_range": f"{self.start_port}-{self.end_port}",
        }
