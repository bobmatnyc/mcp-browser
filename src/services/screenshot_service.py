"""Screenshot service using Playwright."""

import asyncio
import base64
import logging
from typing import Any, Dict, Optional

from playwright.async_api import Browser, Page, async_playwright

logger = logging.getLogger(__name__)


class ScreenshotService:
    """Service for capturing browser screenshots using Playwright."""

    def __init__(self):
        """Initialize screenshot service."""
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._pages: Dict[int, Page] = {}
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start Playwright and launch browser."""
        if self._playwright:
            return

        async with self._lock:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            logger.info("Playwright browser started")

    async def stop(self) -> None:
        """Stop Playwright and close browser."""
        async with self._lock:
            # Close all pages
            for page in self._pages.values():
                try:
                    await page.close()
                except Exception as e:
                    logger.error(f"Error closing page: {e}")

            self._pages.clear()

            # Close browser
            if self._browser:
                await self._browser.close()
                self._browser = None

            # Stop playwright
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            logger.info("Playwright browser stopped")

    async def capture_screenshot(
        self, port: int, url: Optional[str] = None, viewport_only: bool = True
    ) -> Optional[str]:
        """Capture a screenshot of a browser page.

        Args:
            port: Port number (used as page identifier)
            url: Optional URL to navigate to before screenshot
            viewport_only: Whether to capture only viewport (not full page)

        Returns:
            Base64 encoded screenshot or None if failed
        """
        if not self._browser:
            await self.start()

        try:
            # Get or create page for this port
            page = await self._get_or_create_page(port)

            # Navigate if URL provided
            if url:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(1)  # Allow page to stabilize

            # Capture screenshot
            screenshot_bytes = await page.screenshot(
                full_page=not viewport_only, type="png"
            )

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            logger.info(f"Captured screenshot for port {port}")
            return screenshot_base64

        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None

    async def _get_or_create_page(self, port: int) -> Page:
        """Get existing page or create new one for port.

        Args:
            port: Port number

        Returns:
            Page instance
        """
        async with self._lock:
            if port not in self._pages:
                context = await self._browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                )
                self._pages[port] = await context.new_page()

                # Enable console logging
                self._pages[port].on(
                    "console",
                    lambda msg: logger.debug(f"Browser console [{port}]: {msg.text}"),
                )

            return self._pages[port]

    async def close_page(self, port: int) -> None:
        """Close a page for a specific port.

        Args:
            port: Port number
        """
        async with self._lock:
            if port in self._pages:
                try:
                    await self._pages[port].close()
                    del self._pages[port]
                    logger.info(f"Closed page for port {port}")
                except Exception as e:
                    logger.error(f"Error closing page for port {port}: {e}")

    async def navigate_page(self, port: int, url: str) -> bool:
        """Navigate a page to a URL.

        Args:
            port: Port number
            url: URL to navigate to

        Returns:
            True if navigation succeeded
        """
        try:
            page = await self._get_or_create_page(port)
            await page.goto(url, wait_until="networkidle", timeout=30000)
            logger.info(f"Navigated port {port} to {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate: {e}")
            return False

    async def execute_script(self, port: int, script: str) -> Any:
        """Execute JavaScript in a page.

        Args:
            port: Port number
            script: JavaScript to execute

        Returns:
            Script execution result
        """
        try:
            page = await self._get_or_create_page(port)
            result = await page.evaluate(script)
            return result
        except Exception as e:
            logger.error(f"Failed to execute script: {e}")
            return None

    def get_service_info(self) -> Dict[str, Any]:
        """Get service information.

        Returns:
            Dictionary with service information
        """
        return {
            "is_running": self._browser is not None,
            "active_pages": list(self._pages.keys()),
            "page_count": len(self._pages),
        }
