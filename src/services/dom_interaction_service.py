"""DOM interaction service for browser element manipulation."""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DOMInteractionService:
    """Service for handling DOM interactions via WebSocket."""

    def __init__(self, browser_service=None):
        """Initialize DOM interaction service.

        Args:
            browser_service: Browser service for WebSocket communication
        """
        self.browser_service = browser_service
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_timeout = 30  # seconds

    async def click(
        self,
        port: int,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        text: Optional[str] = None,
        index: int = 0,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Click an element on the page.

        Args:
            port: Browser port number
            selector: CSS selector
            xpath: XPath expression
            text: Text content to match
            index: Element index if multiple matches
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with success status and element info
        """
        return await self._send_dom_command(
            port=port,
            command_type="click",
            params={"selector": selector, "xpath": xpath, "text": text, "index": index},
            tab_id=tab_id,
        )

    async def fill_field(
        self,
        port: int,
        value: str,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        index: int = 0,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fill a form field with a value.

        Args:
            port: Browser port number
            value: Value to fill
            selector: CSS selector
            xpath: XPath expression
            index: Element index if multiple matches
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with success status and element info
        """
        return await self._send_dom_command(
            port=port,
            command_type="fill",
            params={
                "selector": selector,
                "xpath": xpath,
                "value": value,
                "index": index,
            },
            tab_id=tab_id,
        )

    async def submit_form(
        self,
        port: int,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Submit a form.

        Args:
            port: Browser port number
            selector: CSS selector for form or form element
            xpath: XPath expression
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with success status
        """
        return await self._send_dom_command(
            port=port,
            command_type="submit",
            params={"selector": selector, "xpath": xpath},
            tab_id=tab_id,
        )

    async def get_element(
        self,
        port: int,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        text: Optional[str] = None,
        index: int = 0,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get information about an element.

        Args:
            port: Browser port number
            selector: CSS selector
            xpath: XPath expression
            text: Text content to match
            index: Element index if multiple matches
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with element information
        """
        return await self._send_dom_command(
            port=port,
            command_type="get_element",
            params={"selector": selector, "xpath": xpath, "text": text, "index": index},
            tab_id=tab_id,
        )

    async def get_elements(
        self, port: int, selector: str, limit: int = 10, tab_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get information about multiple elements.

        Args:
            port: Browser port number
            selector: CSS selector
            limit: Maximum number of elements to return
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with list of element information
        """
        return await self._send_dom_command(
            port=port,
            command_type="get_elements",
            params={"selector": selector, "limit": limit},
            tab_id=tab_id,
        )

    async def wait_for_element(
        self,
        port: int,
        selector: str,
        timeout: int = 5000,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Wait for an element to appear.

        Args:
            port: Browser port number
            selector: CSS selector
            timeout: Timeout in milliseconds
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with element information when found
        """
        return await self._send_dom_command(
            port=port,
            command_type="wait_for_element",
            params={"selector": selector, "timeout": timeout},
            tab_id=tab_id,
        )

    async def select_option(
        self,
        port: int,
        selector: Optional[str] = None,
        option_value: Optional[str] = None,
        option_text: Optional[str] = None,
        option_index: Optional[int] = None,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Select an option in a dropdown.

        Args:
            port: Browser port number
            selector: CSS selector for select element
            option_value: Option value attribute
            option_text: Option text content
            option_index: Option index
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with selected option info
        """
        return await self._send_dom_command(
            port=port,
            command_type="select_option",
            params={
                "selector": selector,
                "optionValue": option_value,
                "optionText": option_text,
                "optionIndex": option_index,
            },
            tab_id=tab_id,
        )

    async def check_checkbox(
        self,
        port: int,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        checked: Optional[bool] = None,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Check or uncheck a checkbox.

        Args:
            port: Browser port number
            selector: CSS selector
            xpath: XPath expression
            checked: Desired checked state (None = toggle)
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with checkbox state
        """
        return await self._send_dom_command(
            port=port,
            command_type="check_checkbox",
            params={"selector": selector, "xpath": xpath, "checked": checked},
            tab_id=tab_id,
        )

    async def scroll_to(
        self,
        port: int,
        selector: Optional[str] = None,
        top: Optional[int] = None,
        left: Optional[int] = None,
        block: str = "center",
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Scroll to an element or position.

        Args:
            port: Browser port number
            selector: CSS selector for element to scroll to
            top: Vertical scroll position (if no selector)
            left: Horizontal scroll position (if no selector)
            block: Scroll alignment ('start', 'center', 'end')
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with success status
        """
        return await self._send_dom_command(
            port=port,
            command_type="scroll_to",
            params={"selector": selector, "top": top, "left": left, "block": block},
            tab_id=tab_id,
        )

    async def fill_form(
        self,
        port: int,
        form_data: Dict[str, Any],
        submit: bool = False,
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fill multiple form fields.

        Args:
            port: Browser port number
            form_data: Dictionary mapping selectors to values
            submit: Whether to submit form after filling
            tab_id: Optional specific tab ID

        Returns:
            Result dictionary with field results
        """
        results = {"success": True, "fields": {}, "errors": []}

        # Fill each field
        for selector, value in form_data.items():
            try:
                result = await self.fill_field(
                    port=port, selector=selector, value=value, tab_id=tab_id
                )
                results["fields"][selector] = result
                if not result.get("success"):
                    results["errors"].append(f"{selector}: {result.get('error')}")
            except Exception as e:
                results["errors"].append(f"{selector}: {str(e)}")
                results["success"] = False

        # Submit form if requested
        if submit and results["success"]:
            try:
                # Find form from one of the filled fields
                first_selector = list(form_data.keys())[0]
                submit_result = await self.submit_form(
                    port=port, selector=first_selector, tab_id=tab_id
                )
                results["submitted"] = submit_result.get("success", False)
            except Exception as e:
                results["submitted"] = False
                results["errors"].append(f"Submit failed: {str(e)}")

        return results

    async def get_tabs(self, port: int) -> List[Dict[str, Any]]:
        """Get information about all browser tabs.

        Args:
            port: Browser port number

        Returns:
            List of tab information dictionaries
        """
        request_id = str(uuid.uuid4())
        future = asyncio.Future()
        self._pending_requests[request_id] = future

        # Send get tabs command
        connection = await self.browser_service.browser_state.get_connection(port)
        if not connection or not connection.websocket:
            return []

        try:
            await connection.websocket.send(
                json.dumps({"type": "get_tabs", "requestId": request_id})
            )

            # Wait for response
            result = await asyncio.wait_for(future, timeout=5)
            return result.get("tabs", [])

        except asyncio.TimeoutError:
            logger.error("Timeout getting browser tabs")
            return []
        finally:
            self._pending_requests.pop(request_id, None)

    async def activate_tab(self, port: int, tab_id: int) -> bool:
        """Activate a specific browser tab.

        Args:
            port: Browser port number
            tab_id: Tab ID to activate

        Returns:
            True if tab was activated successfully
        """
        request_id = str(uuid.uuid4())
        future = asyncio.Future()
        self._pending_requests[request_id] = future

        # Send activate tab command
        connection = await self.browser_service.browser_state.get_connection(port)
        if not connection or not connection.websocket:
            return False

        try:
            await connection.websocket.send(
                json.dumps(
                    {"type": "activate_tab", "tabId": tab_id, "requestId": request_id}
                )
            )

            # Wait for response
            result = await asyncio.wait_for(future, timeout=5)
            return result.get("success", False)

        except asyncio.TimeoutError:
            logger.error(f"Timeout activating tab {tab_id}")
            return False
        finally:
            self._pending_requests.pop(request_id, None)

    async def _send_dom_command(
        self,
        port: int,
        command_type: str,
        params: Dict[str, Any],
        tab_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Send a DOM command to the browser.

        Args:
            port: Browser port number
            command_type: Type of DOM command
            params: Command parameters
            tab_id: Optional specific tab ID

        Returns:
            Command response dictionary
        """
        if not self.browser_service:
            return {"success": False, "error": "Browser service not available"}

        connection = await self.browser_service.browser_state.get_connection(port)
        if not connection or not connection.websocket:
            return {
                "success": False,
                "error": f"No active browser connection on port {port}",
            }

        # Generate request ID
        request_id = str(uuid.uuid4())
        future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            # Send DOM command via WebSocket
            import json

            await connection.websocket.send(
                json.dumps(
                    {
                        "type": "dom_command",
                        "requestId": request_id,
                        "tabId": tab_id,
                        "command": {"type": command_type, "params": params},
                    }
                )
            )

            # Wait for response with timeout
            result = await asyncio.wait_for(future, timeout=self._request_timeout)

            return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for DOM command response: {command_type}")
            return {
                "success": False,
                "error": f"Command timeout after {self._request_timeout} seconds",
            }
        except Exception as e:
            logger.error(f"Error sending DOM command: {e}")
            return {"success": False, "error": str(e)}
        finally:
            # Clean up pending request
            self._pending_requests.pop(request_id, None)

    async def handle_dom_response(self, data: Dict[str, Any]) -> None:
        """Handle DOM response from browser.

        Args:
            data: Response data from browser
        """
        request_id = data.get("requestId")
        if request_id and request_id in self._pending_requests:
            future = self._pending_requests[request_id]
            response = data.get("response", {})

            if not future.done():
                future.set_result(response)

    async def cleanup_pending_requests(self) -> None:
        """Clean up old pending requests."""
        # This can be called periodically to clean up abandoned requests
        expired_requests = []

        for request_id, future in self._pending_requests.items():
            if not future.done():
                # Cancel futures that have been pending too long
                future.cancel()
                expired_requests.append(request_id)

        for request_id in expired_requests:
            self._pending_requests.pop(request_id, None)

        if expired_requests:
            logger.debug(f"Cleaned up {len(expired_requests)} expired DOM requests")
