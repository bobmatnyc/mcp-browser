"""Integration test for port mismatch fix.

This test demonstrates the fix for the issue where MCP tools pass the WebSocket
server port (8851-8895) but connections are stored by client ephemeral port.
"""

import pytest
from unittest.mock import AsyncMock
from src.services.browser_service import BrowserService


@pytest.mark.asyncio
async def test_navigation_with_server_port():
    """Test that navigation works when using server port instead of client port.

    Simulates the scenario where:
    1. Browser extension connects on ephemeral client port (e.g., 57803)
    2. MCP tool calls navigate_browser with server port (e.g., 8851)
    3. Fallback logic finds the connection and sends navigation command
    """
    browser_service = BrowserService()

    # Simulate browser extension connecting with ephemeral client port
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    client_port = 57803
    await browser_service.browser_state.add_connection(
        port=client_port,
        websocket=mock_ws,
        user_agent="Test Browser"
    )

    # MCP tool tries to navigate using server port (8851)
    # This previously failed because get_connection(8851) returned None
    # Now it should fall back to any active connection
    server_port = 8851
    result = await browser_service.navigate_browser(server_port, "https://example.com")

    # Should succeed despite port mismatch
    assert result is True, "Navigation should succeed with server port"
    assert mock_ws.send.called, "WebSocket send should be called"

    # Verify correct navigation message was sent
    import json
    call_args = mock_ws.send.call_args[0][0]
    message = json.loads(call_args)

    assert message["type"] == "navigate"
    assert message["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_screenshot_with_server_port():
    """Test that screenshot capture works with server port."""
    browser_service = BrowserService()

    # Create mock websocket
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    # Connect with client port
    client_port = 57804
    await browser_service.browser_state.add_connection(
        port=client_port,
        websocket=mock_ws
    )

    # Try to capture screenshot using server port
    server_port = 8852

    # Start the async operation (don't wait for response since it's mocked)
    import asyncio
    task = asyncio.create_task(
        browser_service.capture_screenshot_via_extension(server_port, timeout=0.5)
    )

    # Give it a moment to send the command
    await asyncio.sleep(0.1)

    # Should have sent the screenshot request
    assert mock_ws.send.called, "WebSocket send should be called"

    # Cancel the task since we're not simulating the response
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_port_range_fallback():
    """Test that fallback only applies to server port range (8851-8895)."""
    browser_service = BrowserService()

    # Add connection with client port
    mock_ws = AsyncMock()
    await browser_service.browser_state.add_connection(
        port=57803,
        websocket=mock_ws
    )

    # Server port in range should trigger fallback
    result = await browser_service._get_connection_with_fallback(8860)
    assert result is not None, "Server port should trigger fallback"
    assert result.port == 57803

    # Random port outside range should NOT trigger fallback
    result = await browser_service._get_connection_with_fallback(12345)
    assert result is None, "Non-server port should not trigger fallback"


@pytest.mark.asyncio
async def test_multiple_connections_fallback():
    """Test fallback behavior with multiple connections."""
    browser_service = BrowserService()

    # Add multiple connections
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()
    mock_ws2.send = AsyncMock()

    await browser_service.browser_state.add_connection(
        port=57803,
        websocket=mock_ws1
    )

    await browser_service.browser_state.add_connection(
        port=57804,
        websocket=mock_ws2
    )

    # Disconnect first connection
    first_conn = await browser_service.browser_state.get_connection(57803)
    first_conn.disconnect()

    # Server port should fall back to second (active) connection
    result = await browser_service._get_connection_with_fallback(8851)
    assert result is not None
    assert result.is_active
    assert result.port == 57804  # Should skip inactive connection
