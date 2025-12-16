"""Port resolution utility for MCP tools.

This module provides port resolution and validation for browser connections.
It handles auto-detection from daemon registry and warns about common mistakes.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class PortResolver:
    """Utility for resolving and validating browser ports.

    Features:
    - Auto-detects port from running daemon registry
    - Caches daemon port for performance
    - Warns if CDP port (9222) is used incorrectly
    - Provides helpful error messages

    Example:
        resolver = PortResolver()
        port, warning = resolver.resolve_port(None)  # Auto-detect
        if port is None:
            print(warning)
        else:
            # Use port
            pass
    """

    CDP_DEFAULT_PORT = 9222

    def __init__(self) -> None:
        """Initialize port resolver with empty cache."""
        self._cached_daemon_port: Optional[int] = None

    def resolve_port(self, port: Optional[int]) -> Tuple[Optional[int], Optional[str]]:
        """Resolve port with validation and caching.

        Args:
            port: User-provided port or None for auto-detection

        Returns:
            Tuple of (resolved_port, warning_message)
            - resolved_port: Port to use, or None if unavailable
            - warning_message: Optional warning/error message

        Examples:
            # Auto-detect from daemon
            port, warning = resolver.resolve_port(None)

            # Validate provided port
            port, warning = resolver.resolve_port(8875)

            # Detect CDP port mistake
            port, warning = resolver.resolve_port(9222)
        """
        warning = None

        # Warn if CDP port is used (common mistake)
        if port == self.CDP_DEFAULT_PORT:
            warning = (
                f"Warning: Port {self.CDP_DEFAULT_PORT} is the Chrome DevTools Protocol port, "
                f"not the mcp-browser daemon port. "
            )
            # Try to get the correct daemon port
            daemon_port = self._cached_daemon_port or self._get_daemon_port()
            if daemon_port:
                self._cached_daemon_port = daemon_port
                warning += f"Using daemon port {daemon_port} instead."
                return daemon_port, warning
            else:
                warning += "No running daemon found. Start with: mcp-browser start"
                return None, warning

        # If port provided, use it
        if port is not None:
            return port, None

        # No port provided - get from daemon registry
        if self._cached_daemon_port:
            return self._cached_daemon_port, None

        daemon_port = self._get_daemon_port()
        if daemon_port:
            self._cached_daemon_port = daemon_port
            return daemon_port, None

        # No daemon running
        return (
            None,
            "No port specified and no running daemon found. Start with: mcp-browser start",
        )

    def _get_daemon_port(self) -> Optional[int]:
        """Get the port of the running mcp-browser daemon from registry.

        Returns:
            Port number if daemon is running, None otherwise

        Note:
            This method imports CLI utilities lazily to avoid circular dependencies
            and unnecessary imports when running in MCP stdio mode.
        """
        try:
            from ...cli.utils.daemon import is_process_running, read_service_registry

            registry = read_service_registry()
            for server in registry.get("servers", []):
                pid = server.get("pid")
                port = server.get("port")
                if pid is not None and is_process_running(pid) and isinstance(port, int):
                    return port
            return None
        except Exception as e:
            logger.debug(f"Could not read daemon registry: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear cached daemon port.

        Useful when daemon is restarted or port changes.
        Next resolve_port() call will re-query the registry.
        """
        self._cached_daemon_port = None
