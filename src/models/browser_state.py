"""Browser state tracking model."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class BrowserConnection:
    """Represents a browser connection."""

    port: int
    connected_at: datetime
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    url: Optional[str] = None
    user_agent: Optional[str] = None
    websocket: Any = None  # WebSocket connection object
    is_active: bool = True

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
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add_connection(
        self, port: int, websocket: Any, user_agent: Optional[str] = None
    ) -> BrowserConnection:
        """Add a new browser connection.

        Args:
            port: Port number
            websocket: WebSocket connection object
            user_agent: Optional user agent string

        Returns:
            BrowserConnection instance
        """
        async with self._lock:
            connection = BrowserConnection(
                port=port,
                connected_at=datetime.now(),
                websocket=websocket,
                user_agent=user_agent,
            )
            self.connections[port] = connection
            return connection

    async def remove_connection(self, port: int) -> None:
        """Remove a browser connection.

        Args:
            port: Port number to remove
        """
        async with self._lock:
            if port in self.connections:
                self.connections[port].disconnect()
                del self.connections[port]

    async def get_connection(self, port: int) -> Optional[BrowserConnection]:
        """Get a browser connection by port.

        Args:
            port: Port number

        Returns:
            BrowserConnection if exists, None otherwise
        """
        async with self._lock:
            return self.connections.get(port)

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
