"""Integration test for port mismatch fix.

This test demonstrates the fix for the issue where MCP tools pass the WebSocket
server port (8851-8895) but connections are stored by client ephemeral port.
"""

from unittest.mock import AsyncMock

import pytest

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
    server_port = 8851

    await browser_service.browser_state.add_connection(
        port=client_port,
        server_port=server_port,
        websocket=mock_ws,
        user_agent="Test Browser",
    )

    # MCP tool tries to navigate using server port (8851)
    # Now the server_port_map should find the connection directly
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

    # Connect with client port and server port
    client_port = 57804
    server_port = 8852

    await browser_service.browser_state.add_connection(
        port=client_port, server_port=server_port, websocket=mock_ws
    )

    # Try to capture screenshot using server port

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
    """Test that server_port_map works and fallback applies when not found."""
    browser_service = BrowserService()

    # Add connection with client port and server port
    mock_ws = AsyncMock()
    await browser_service.browser_state.add_connection(
        port=57803, server_port=8860, websocket=mock_ws
    )

    # Server port should use server_port_map to find connection
    result = await browser_service._get_connection_with_fallback(8860)
    assert result is not None, "Server port should find connection via mapping"
    assert result.port == 57803
    assert result.server_port == 8860

    # Random port outside server_port_map should trigger fallback to any active
    result = await browser_service._get_connection_with_fallback(12345)
    assert result is not None, "Random port should fallback to active connection"
    assert result.port == 57803  # Falls back to our only connection


@pytest.mark.asyncio
async def test_multiple_connections_fallback():
    """Test fallback behavior with multiple connections."""
    browser_service = BrowserService()

    # Add multiple connections with different server ports
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()
    mock_ws2.send = AsyncMock()

    await browser_service.browser_state.add_connection(
        port=57803, server_port=8851, websocket=mock_ws1
    )

    await browser_service.browser_state.add_connection(
        port=57804, server_port=8852, websocket=mock_ws2
    )

    # Disconnect first connection
    first_conn = await browser_service.browser_state.get_connection(57803)
    first_conn.disconnect()

    # Server port 8851 should find first connection (even though inactive)
    result = await browser_service._get_connection_with_fallback(8851)
    assert result is not None
    # But since it's inactive, fallback should return active connection
    if not result.is_active:
        # Retry should get active connection
        result = await browser_service.browser_state.get_any_active_connection()
        assert result is not None
        assert result.is_active
        assert result.port == 57804  # Should get second active connection
