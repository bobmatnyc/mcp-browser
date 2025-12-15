"""Unit tests for port mismatch fallback logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.models.browser_state import BrowserState, BrowserConnection
from src.services.browser_service import BrowserService
from datetime import datetime


@pytest.mark.asyncio
async def test_get_connection_exact_match():
    """Test that exact port match works."""
    browser_state = BrowserState()

    # Add a connection with client port
    mock_ws = MagicMock()
    connection = await browser_state.add_connection(
        port=57803,
        websocket=mock_ws,
        user_agent="Test Browser"
    )

    # Should find exact match
    result = await browser_state.get_connection(57803)
    assert result is not None
    assert result.port == 57803
    assert result.is_active


@pytest.mark.asyncio
async def test_get_any_active_connection():
    """Test fallback to any active connection."""
    browser_state = BrowserState()

    # Add multiple connections
    mock_ws1 = MagicMock()
    mock_ws2 = MagicMock()

    conn1 = await browser_state.add_connection(
        port=57803,
        websocket=mock_ws1
    )

    conn2 = await browser_state.add_connection(
        port=57804,
        websocket=mock_ws2
    )

    # Should get first active connection
    result = await browser_state.get_any_active_connection()
    assert result is not None
    assert result.is_active
    assert result.port in [57803, 57804]


@pytest.mark.asyncio
async def test_get_any_active_connection_no_active():
    """Test get_any_active_connection returns None when no active connections."""
    browser_state = BrowserState()

    # Add an inactive connection
    mock_ws = MagicMock()
    conn = await browser_state.add_connection(port=57803, websocket=mock_ws)
    conn.disconnect()

    # Should return None
    result = await browser_state.get_any_active_connection()
    assert result is None


@pytest.mark.asyncio
async def test_browser_service_connection_fallback_exact_match():
    """Test BrowserService._get_connection_with_fallback with exact match."""
    browser_service = BrowserService()

    # Add connection with client port
    mock_ws = MagicMock()
    await browser_service.browser_state.add_connection(
        port=57803,
        websocket=mock_ws
    )

    # Exact match should work
    connection = await browser_service._get_connection_with_fallback(57803)
    assert connection is not None
    assert connection.port == 57803


@pytest.mark.asyncio
async def test_browser_service_connection_fallback_server_port():
    """Test BrowserService._get_connection_with_fallback with server port."""
    browser_service = BrowserService()

    # Add connection with client port (ephemeral)
    mock_ws = MagicMock()
    await browser_service.browser_state.add_connection(
        port=57803,
        websocket=mock_ws
    )

    # Server port lookup (8851-8895 range) should fall back
    connection = await browser_service._get_connection_with_fallback(8851)
    assert connection is not None
    assert connection.port == 57803  # Returns client port connection


@pytest.mark.asyncio
async def test_browser_service_connection_fallback_no_connection():
    """Test BrowserService._get_connection_with_fallback with no connections."""
    browser_service = BrowserService()

    # No connections exist
    connection = await browser_service._get_connection_with_fallback(8851)
    assert connection is None


@pytest.mark.asyncio
async def test_browser_service_navigate_with_fallback():
    """Test navigate_browser uses fallback logic."""
    browser_service = BrowserService()

    # Create mock websocket with send method
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    # Add connection with client port
    await browser_service.browser_state.add_connection(
        port=57803,
        websocket=mock_ws
    )

    # Navigate using server port (should fall back to client port)
    result = await browser_service.navigate_browser(8851, "https://example.com")

    assert result is True
    assert mock_ws.send.called

    # Verify the message sent
    call_args = mock_ws.send.call_args[0][0]
    import json
    message = json.loads(call_args)
    assert message["type"] == "navigate"
    assert message["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_browser_service_navigate_exact_port():
    """Test navigate_browser with exact client port."""
    browser_service = BrowserService()

    # Create mock websocket
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    # Add connection with client port
    await browser_service.browser_state.add_connection(
        port=57803,
        websocket=mock_ws
    )

    # Navigate using exact client port
    result = await browser_service.navigate_browser(57803, "https://example.com")

    assert result is True
    assert mock_ws.send.called


@pytest.mark.asyncio
async def test_browser_service_navigate_no_connection():
    """Test navigate_browser fails gracefully with no connection."""
    browser_service = BrowserService()

    # No connections exist
    result = await browser_service.navigate_browser(8851, "https://example.com")

    assert result is False
