"""Dependency injection container for mcp-browser."""

from .service_container import ServiceContainer, ServiceNotFoundError

__all__ = ["ServiceContainer", "ServiceNotFoundError"]
