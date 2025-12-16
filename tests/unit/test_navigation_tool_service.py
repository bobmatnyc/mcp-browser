"""Test navigation tool service."""

import pytest

from src.services.tools.navigation_tool_service import NavigationToolService


class MockBrowserService:
    """Mock browser service for testing."""

    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.navigate_calls = []

    async def navigate_browser(self, port: int, url: str) -> bool:
        """Mock navigate_browser method."""
        self.navigate_calls.append({"port": port, "url": url})
        return self.should_succeed


@pytest.mark.asyncio
async def test_navigate_success():
    """Test successful navigation."""
    mock_browser = MockBrowserService(should_succeed=True)
    service = NavigationToolService(browser_service=mock_browser)

    result = await service.handle_navigate(port=8851, url="https://example.com")

    # Verify browser_service.navigate_browser was called
    assert len(mock_browser.navigate_calls) == 1
    assert mock_browser.navigate_calls[0]["port"] == 8851
    assert mock_browser.navigate_calls[0]["url"] == "https://example.com"

    # Verify success response
    assert len(result) == 1
    assert result[0].type == "text"
    assert "Navigated to https://example.com on port 8851" in result[0].text


@pytest.mark.asyncio
async def test_navigate_failure():
    """Test failed navigation."""
    mock_browser = MockBrowserService(should_succeed=False)
    service = NavigationToolService(browser_service=mock_browser)

    result = await service.handle_navigate(port=8851, url="https://example.com")

    # Verify browser_service.navigate_browser was called
    assert len(mock_browser.navigate_calls) == 1

    # Verify error response
    assert len(result) == 1
    assert result[0].type == "text"
    assert "Navigation failed on port 8851" in result[0].text
    assert "no active connection" in result[0].text.lower()


@pytest.mark.asyncio
async def test_navigate_missing_url():
    """Test navigation with missing URL."""
    mock_browser = MockBrowserService()
    service = NavigationToolService(browser_service=mock_browser)

    result = await service.handle_navigate(port=8851, url="")

    # Verify browser_service.navigate_browser was NOT called
    assert len(mock_browser.navigate_calls) == 0

    # Verify error response
    assert len(result) == 1
    assert result[0].type == "text"
    assert "url" in result[0].text.lower()
    assert "required" in result[0].text.lower()


@pytest.mark.asyncio
async def test_navigate_no_browser_service():
    """Test navigation without browser service."""
    service = NavigationToolService(browser_service=None)

    result = await service.handle_navigate(port=8851, url="https://example.com")

    # Verify error response
    assert len(result) == 1
    assert result[0].type == "text"
    assert "Browser service not available" in result[0].text
