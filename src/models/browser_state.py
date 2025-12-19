"""Browser state tracking model."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class BrowserConnection:
    """Represents a browser connection."""

    port: int  # client ephemeral port (internal tracking)
    server_port: int  # server listening port (user-facing, for MCP tools)
    connected_at: datetime
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    url: Optional[str] = None
    user_agent: Optional[str] = None
    websocket: Any = None  # WebSocket connection object
    is_active: bool = True
    is_extension: bool = (
        False  # True if this is a browser extension (sent connection_init)
    )

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_message_at = datetime.now()
        self.message_count += 1

    def disconnect(self) -> None:
        """Mark connection as disconnected."""
        self.is_active = False

    @property
    def connection_duration(self) -> float:
        """Get connection duration in seconds."""
        return (datetime.now() - self.connected_at).total_seconds()

    @property
    def idle_time(self) -> float:
        """Get idle time since last message in seconds."""
        if self.last_message_at:
            return (datetime.now() - self.last_message_at).total_seconds()
        return self.connection_duration


@dataclass
class BrowserState:
    """Manages state for all browser connections."""

    connections: Dict[int, BrowserConnection] = field(default_factory=dict)
    server_port_map: Dict[int, int] = field(
        default_factory=dict
    )  # server_port → client_port mapping
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add_connection(
        self,
        port: int,
        server_port: int,
        websocket: Any,
        user_agent: Optional[str] = None,
    ) -> BrowserConnection:
        """Add a new browser connection.

        Args:
            port: Client ephemeral port number (internal tracking)
            server_port: Server listening port number (user-facing, for MCP tools)
            websocket: WebSocket connection object
            user_agent: Optional user agent string

        Returns:
            BrowserConnection instance
        """
        async with self._lock:
            connection = BrowserConnection(
                port=port,
                server_port=server_port,
                connected_at=datetime.now(),
                websocket=websocket,
                user_agent=user_agent,
            )
            self.connections[port] = connection
            # Map server port to client port for user-facing API
            self.server_port_map[server_port] = port
            return connection

    async def remove_connection(self, port: int) -> None:
        """Remove a browser connection.

        Args:
            port: Port number to remove (client port)
        """
        async with self._lock:
            if port in self.connections:
                # Clean up server_port_map ONLY if it still points to this connection
                # This prevents a race condition where:
                # 1. New connection A opens, server_port_map[8851] = A
                # 2. Old connection B disconnects, would wrongly delete server_port_map[8851]
                conn = self.connections[port]
                if (
                    conn.server_port in self.server_port_map
                    and self.server_port_map[conn.server_port] == port
                ):
                    del self.server_port_map[conn.server_port]

                # Then remove connection
                self.connections[port].disconnect()
                del self.connections[port]

    async def get_connection(self, port: int) -> Optional[BrowserConnection]:
        """Get a browser connection by port.

        Supports both server port (8851-8899) and client ephemeral port lookups.
        When a server port is provided, it's automatically mapped to the client port.

        Args:
            port: Port number (can be server port or client port)

        Returns:
            BrowserConnection if exists, None otherwise
        """
        async with self._lock:
            # Try server port mapping first (if it's a server port like 8852)
            lookup_port = self.server_port_map.get(port, port)
            return self.connections.get(lookup_port)

    async def update_connection_activity(self, port: int) -> None:
        """Update connection activity timestamp.

        Args:
            port: Port number
        """
        async with self._lock:
            if port in self.connections:
                self.connections[port].update_activity()

    async def update_connection_url(self, port: int, url: str) -> None:
        """Update the current URL for a connection.

        Args:
            port: Port number
            url: Current URL
        """
        async with self._lock:
            if port in self.connections:
                self.connections[port].url = url

    async def get_any_active_connection(self) -> Optional[BrowserConnection]:
        """Get any active connection (fallback when server port is used instead of client port).

        This is useful when MCP tools pass the server port (8851-8895) but connections
        are keyed by the client's ephemeral port (e.g., 57803).

        Returns:
            First active connection found, or None if no active connections exist
        """
        async with self._lock:
            logger.info(
                f"get_any_active_connection: {len(self.connections)} total connections"
            )
            for port, conn in self.connections.items():
                logger.info(
                    f"  Port {port}: is_active={conn.is_active}, websocket={conn.websocket is not None}"
                )
                if conn.is_active:
                    return conn
            return None

    async def get_extension_connection(self) -> Optional[BrowserConnection]:
        """Get the active browser extension connection.

        Extension connections are identified by sending connection_init message.
        These are the only connections that can respond to DOM commands,
        extract content, capture screenshots, etc.

        Returns:
            Active extension connection, or None if no extension is connected
        """
        async with self._lock:
            for port, conn in self.connections.items():
                if conn.is_active and conn.is_extension:
                    # Verify WebSocket is still open
                    if conn.websocket and not getattr(conn.websocket, "closed", True):
                        logger.debug(f"Found extension connection on port {port}")
                        return conn
                    else:
                        # WebSocket closed but not cleaned up yet
                        logger.warning(
                            f"Extension connection on port {port} has closed WebSocket, skipping"
                        )
                        conn.is_active = False  # Mark as inactive

            # Log diagnostic info
            total = len(self.connections)
            extensions = sum(1 for c in self.connections.values() if c.is_extension)
            active = sum(1 for c in self.connections.values() if c.is_active)
            logger.warning(
                f"No extension connection found. "
                f"(Total: {total}, Extensions: {extensions}, Active: {active})"
            )
            return None

    async def verify_extension_health(self) -> Dict[str, Any]:
        """Verify extension connection health and return diagnostic info.

        Returns:
            Dict with connection health status and diagnostic information
        """
        async with self._lock:
            total_connections = len(self.connections)
            extension_connections = []
            non_extension_connections = []

            for port, conn in self.connections.items():
                ws_open = conn.websocket and not getattr(conn.websocket, "closed", True)
                conn_info = {
                    "port": port,
                    "server_port": conn.server_port,
                    "is_active": conn.is_active,
                    "is_extension": conn.is_extension,
                    "websocket_open": ws_open,
                    "idle_time": conn.idle_time,
                    "message_count": conn.message_count,
                }
                if conn.is_extension:
                    extension_connections.append(conn_info)
                else:
                    non_extension_connections.append(conn_info)

            has_healthy_extension = any(
                c["is_active"] and c["websocket_open"] for c in extension_connections
            )

            return {
                "healthy": has_healthy_extension,
                "total_connections": total_connections,
                "extension_connections": extension_connections,
                "non_extension_connections": non_extension_connections,
                "server_port_map": dict(self.server_port_map),
            }

    async def mark_as_extension(self, port: int) -> bool:
        """Mark a connection as a browser extension.

        Called when a connection sends connection_init message.

        Args:
            port: Client port number

        Returns:
            True if connection was found and marked, False otherwise
        """
        async with self._lock:
            if port in self.connections:
                self.connections[port].is_extension = True
                logger.info(f"Marked connection on port {port} as extension")
                return True
            return False

    async def get_active_connections(self) -> Dict[int, BrowserConnection]:
        """Get all active connections.

        Returns:
            Dictionary of active connections
        """
        async with self._lock:
            return {
                port: conn for port, conn in self.connections.items() if conn.is_active
            }

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about all connections.

        Returns:
            Dictionary with connection statistics
        """
        async with self._lock:
            active_connections = [c for c in self.connections.values() if c.is_active]
            total_messages = sum(c.message_count for c in self.connections.values())

            return {
                "total_connections": len(self.connections),
                "active_connections": len(active_connections),
                "total_messages": total_messages,
                "ports": list(self.connections.keys()),
                "connections": [
                    {
                        "port": c.port,
                        "connected_at": c.connected_at.isoformat(),
                        "message_count": c.message_count,
                        "url": c.url,
                        "is_active": c.is_active,
                        "duration": c.connection_duration,
                        "idle_time": c.idle_time,
                    }
                    for c in self.connections.values()
                ],
            }
