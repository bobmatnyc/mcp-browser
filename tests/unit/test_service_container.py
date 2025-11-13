"""Tests for service container dependency injection."""

import asyncio

import pytest

from src.container.service_container import ServiceContainer, ServiceNotFoundError


class TestServiceContainer:
    """Test suite for ServiceContainer."""

    @pytest.fixture
    def container(self):
        """Create a fresh service container."""
        return ServiceContainer()

    def test_register_service(self, container):
        """Test service registration."""

        def test_factory(c):
            return "test_service"

        container.register("test", test_factory)
        assert container.has("test")

    def test_register_instance(self, container):
        """Test instance registration."""
        instance = "test_instance"
        container.register_instance("test", instance)
        assert container.has("test")

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, container):
        """Test getting non-existent service raises error."""
        with pytest.raises(ServiceNotFoundError):
            await container.get("non_existent")

    @pytest.mark.asyncio
    async def test_get_registered_instance(self, container):
        """Test getting registered instance."""
        instance = "test_instance"
        container.register_instance("test", instance)

        result = await container.get("test")
        assert result == instance

    @pytest.mark.asyncio
    async def test_singleton_behavior(self, container):
        """Test singleton service behavior."""
        call_count = 0

        def factory(c):
            nonlocal call_count
            call_count += 1
            return f"instance_{call_count}"

        container.register("test", factory, singleton=True)

        result1 = await container.get("test")
        result2 = await container.get("test")

        assert result1 == result2
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_non_singleton_behavior(self, container):
        """Test non-singleton service behavior."""
        call_count = 0

        def factory(c):
            nonlocal call_count
            call_count += 1
            return f"instance_{call_count}"

        container.register("test", factory, singleton=False)

        result1 = await container.get("test")
        result2 = await container.get("test")

        assert result1 != result2
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_dependency_injection(self, container):
        """Test constructor dependency injection."""
        # Register dependency
        container.register_instance("dependency", "dep_value")

        # Register service that depends on it
        class TestService:
            def __init__(self, dependency=None):
                self.dependency = dependency

        container.register("test_service", TestService)

        # Get service
        service = await container.get("test_service")
        assert service.dependency == "dep_value"

    @pytest.mark.asyncio
    async def test_async_factory(self, container):
        """Test async factory function."""

        async def async_factory(c):
            await asyncio.sleep(0.01)  # Simulate async work
            return "async_result"

        container.register("async_test", async_factory)

        result = await container.get("async_test")
        assert result == "async_result"

    def test_clear_services(self, container):
        """Test clearing all services."""
        container.register_instance("test1", "value1")
        container.register_instance("test2", "value2")

        assert container.has("test1")
        assert container.has("test2")

        container.clear()

        assert not container.has("test1")
        assert not container.has("test2")

    def test_get_all_service_names(self, container):
        """Test getting all service names."""
        container.register_instance("service1", "value1")
        container.register("service2", lambda c: "value2")

        names = container.get_all_service_names()
        assert "service1" in names
        assert "service2" in names
        assert len(names) == 2

    @pytest.mark.asyncio
    async def test_inject_decorator_async(self, container):
        """Test inject decorator with async function."""
        container.register_instance("dep1", "value1")
        container.register_instance("dep2", "value2")

        @container.inject("dep1", "dep2")
        async def test_func(arg1, dep1=None, dep2=None):
            return f"{arg1}_{dep1}_{dep2}"

        result = await test_func("test")
        assert result == "test_value1_value2"

    def test_inject_decorator_sync(self, container):
        """Test inject decorator with sync function."""
        container.register_instance("dep1", "value1")

        @container.inject("dep1")
        def test_func(arg1, dep1=None):
            return f"{arg1}_{dep1}"

        result = test_func("test")
        assert result == "test_value1"
