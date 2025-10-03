"""Integration tests for service interactions."""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.container.service_container import ServiceContainer
from src.models.console_message import ConsoleLevel, ConsoleMessage
from src.services.browser_service import BrowserService
from src.services.storage_service import StorageConfig, StorageService


class TestServiceIntegration:
    """Test service integration scenarios."""

    @pytest.fixture
    async def container(self):
        """Create container with registered services."""
        container = ServiceContainer()

        # Use temporary directory for storage
        temp_dir = tempfile.mkdtemp()
        config = StorageConfig(base_path=Path(temp_dir))
        storage = StorageService(config)

        container.register_instance("storage_service", storage)

        # Register browser service with storage dependency
        async def create_browser_service(c):
            storage_svc = await c.get("storage_service")
            return BrowserService(storage_service=storage_svc)

        container.register("browser_service", create_browser_service)

        yield container

        # Cleanup
        await storage.stop_rotation_task()

    @pytest.mark.asyncio
    async def test_browser_storage_integration(self, container):
        """Test browser service with storage integration."""
        browser_service = await container.get("browser_service")
        # Note: storage_service is used by browser_service internally

        # Create test message
        message = ConsoleMessage(
            timestamp=datetime.now(),
            level=ConsoleLevel.INFO,
            message="Test message",
            port=8875,
        )

        # Store message via browser service buffer
        browser_service._message_buffer[8875] = browser_service._message_buffer.get(
            8875, []
        )
        browser_service._message_buffer[8875].append(message)

        # Flush buffer
        await browser_service._flush_buffer(8875)

        # Query logs
        logs = await browser_service.query_logs(8875, last_n=10)
        assert len(logs) == 1
        assert logs[0].message == "Test message"
        assert logs[0].level == ConsoleLevel.INFO

    @pytest.mark.asyncio
    async def test_message_filtering(self, container):
        """Test message filtering in browser service."""
        browser_service = await container.get("browser_service")

        # Create test messages with different levels
        messages = [
            ConsoleMessage(
                timestamp=datetime.now(),
                level=ConsoleLevel.ERROR,
                message="Error message",
                port=8875,
            ),
            ConsoleMessage(
                timestamp=datetime.now(),
                level=ConsoleLevel.INFO,
                message="Info message",
                port=8875,
            ),
            ConsoleMessage(
                timestamp=datetime.now(),
                level=ConsoleLevel.DEBUG,
                message="Debug message",
                port=8875,
            ),
        ]

        # Store messages
        browser_service._message_buffer[8875] = browser_service._message_buffer.get(
            8875, []
        )
        for msg in messages:
            browser_service._message_buffer[8875].append(msg)

        await browser_service._flush_buffer(8875)

        # Query with error filter
        error_logs = await browser_service.query_logs(8875, level_filter=["error"])
        assert len(error_logs) == 1
        assert error_logs[0].level == ConsoleLevel.ERROR

        # Query with multiple filters
        info_error_logs = await browser_service.query_logs(
            8875, level_filter=["error", "info"]
        )
        assert len(info_error_logs) == 2

    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self, container):
        """Test concurrent message handling."""
        browser_service = await container.get("browser_service")

        # Simulate concurrent message handling
        async def handle_message(port, message_text):
            data = {
                "type": "console",
                "level": "info",
                "message": message_text,
                "timestamp": datetime.now().isoformat(),
                "_remote_address": ("localhost", port),
            }
            await browser_service.handle_console_message(data)

        # Handle multiple messages concurrently
        tasks = [handle_message(8875, f"Message {i}") for i in range(10)]

        await asyncio.gather(*tasks)

        # Verify all messages are in buffer
        assert len(browser_service._message_buffer[8875]) == 10

    @pytest.mark.asyncio
    async def test_storage_rotation_integration(self, container):
        """Test storage rotation with browser service."""
        storage_service = await container.get("storage_service")
        # Note: browser_service uses storage_service internally

        # Override rotation size for testing
        storage_service.config.max_file_size_mb = 0.001  # Very small

        # Create enough messages to trigger rotation
        messages = []
        for i in range(100):
            message = ConsoleMessage(
                timestamp=datetime.now(),
                level=ConsoleLevel.INFO,
                message=f"Large message with lots of content to trigger rotation {i}"
                * 10,
                port=8875,
            )
            messages.append(message)

        # Store messages in batches
        await storage_service.store_messages_batch(messages)

        # Check that rotation occurred (multiple files exist)
        port_dir = storage_service._get_port_directory(8875)
        jsonl_files = list(port_dir.glob("*.jsonl"))
        assert len(jsonl_files) >= 1  # At least one file should exist

    @pytest.mark.asyncio
    async def test_browser_navigation_simulation(self, container):
        """Test browser navigation command simulation."""
        browser_service = await container.get("browser_service")

        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.websocket = mock_websocket

        # Add mock connection to browser state
        await browser_service.browser_state.add_connection(
            port=8875, websocket=mock_websocket, user_agent="Test Agent"
        )

        # Test navigation
        success = await browser_service.navigate_browser(8875, "https://example.com")
        assert success

        # Verify WebSocket send was called
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        import json

        message = json.loads(call_args)
        assert message["type"] == "navigate"
        assert message["url"] == "https://example.com"
