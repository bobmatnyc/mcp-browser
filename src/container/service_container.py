"""Service container for dependency injection."""

import asyncio
import inspect
from functools import wraps
from typing import Any, Callable, Dict, TypeVar

T = TypeVar("T")


class ServiceNotFoundError(Exception):
    """Raised when a service is not found in the container."""

    pass


class ServiceContainer:
    """Dependency injection container for managing services."""

    def __init__(self):
        """Initialize the service container."""
        self._services: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._singleton_flags: Dict[str, bool] = {}
        self._lock = asyncio.Lock()
        # Per-service creation locks to prevent race conditions during singleton creation
        self._creating: Dict[str, asyncio.Lock] = {}

    def register(self, name: str, factory: Callable, singleton: bool = True) -> None:
        """Register a service factory.

        Args:
            name: Service name
            factory: Factory function or class to create the service
            singleton: Whether to create a single instance
        """
        self._services[name] = factory
        self._singleton_flags[name] = singleton

    def register_instance(self, name: str, instance: Any) -> None:
        """Register an existing instance as a singleton.

        Args:
            name: Service name
            instance: Service instance
        """
        self._singletons[name] = instance
        self._singleton_flags[name] = True

    async def get(self, name: str) -> Any:
        """Get a service instance.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            ServiceNotFoundError: If service is not registered
        """
        if name not in self._services and name not in self._singletons:
            raise ServiceNotFoundError(f"Service '{name}' not found")

        # Return existing singleton if available
        if name in self._singletons:
            return self._singletons[name]

        # Check if we should create a singleton
        if self._singleton_flags.get(name, False):
            # Ensure per-service lock exists (thread-safe creation of lock itself)
            async with self._lock:
                if name not in self._creating:
                    self._creating[name] = asyncio.Lock()
                service_lock = self._creating[name]

            # Use per-service lock for double-check pattern
            async with service_lock:
                # Double-check after acquiring lock - another coroutine may have created it
                if name in self._singletons:
                    return self._singletons[name]

                # Create singleton instance - only one coroutine per service reaches here
                instance = await self._create_instance(name)
                self._singletons[name] = instance
                return instance

        # Create new instance
        return await self._create_instance(name)

    async def _create_instance(self, name: str) -> Any:
        """Create a new instance of a service.

        Args:
            name: Service name

        Returns:
            Service instance
        """
        factory = self._services[name]

        # Check if factory needs dependency injection
        if inspect.isclass(factory):
            # Get constructor parameters
            sig = inspect.signature(factory.__init__)
            params = {}

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                # Try to resolve parameter by name
                if param_name in self._services or param_name in self._singletons:
                    params[param_name] = await self.get(param_name)
                elif param.default is not param.empty:
                    # Use default value if available
                    params[param_name] = param.default
                # Skip if parameter has no default and can't be resolved

            # Create instance with resolved dependencies
            return factory(**params)

        # If it's a function, check if it's async
        if asyncio.iscoroutinefunction(factory):
            return await factory(self)
        else:
            return factory(self)

    def get_sync(self, name: str) -> Any:
        """Get a service instance synchronously.

        Args:
            name: Service name

        Returns:
            Service instance

        Note:
            This should only be used when async is not available.
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get(name))

    def has(self, name: str) -> bool:
        """Check if a service is registered.

        Args:
            name: Service name

        Returns:
            True if service is registered
        """
        return name in self._services or name in self._singletons

    def clear(self) -> None:
        """Clear all registered services and singletons."""
        self._services.clear()
        self._singletons.clear()
        self._singleton_flags.clear()

    def get_all_service_names(self) -> list[str]:
        """Get names of all registered services.

        Returns:
            List of service names
        """
        return list(set(self._services.keys()) | set(self._singletons.keys()))

    def inject(self, *service_names: str) -> Callable:
        """Decorator for dependency injection.

        Args:
            service_names: Names of services to inject

        Returns:
            Decorated function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Inject services
                services = {}
                for name in service_names:
                    services[name] = await self.get(name)
                return await func(*args, **services, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Inject services
                services = {}
                for name in service_names:
                    services[name] = self.get_sync(name)
                return func(*args, **services, **kwargs)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator
