"""DOM interaction tool service for MCP browser control."""

import logging
from typing import Any, Dict, List

from mcp.types import TextContent

logger = logging.getLogger(__name__)


class DOMToolService:
    """MCP tool handler for DOM interactions."""

    def __init__(self, dom_interaction_service=None, port_resolver=None):
        """Initialize DOM tool service.

        Args:
            dom_interaction_service: DOM interaction service for element operations
            port_resolver: Port resolution service
        """
        self.dom_interaction_service = dom_interaction_service
        self.port_resolver = port_resolver

    async def handle_click(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Click an element.

        Args:
            arguments: Dict with:
                - port: Browser daemon port (optional, auto-resolved)
                - selector: CSS selector (optional)
                - xpath: XPath selector (optional)
                - text: Text content to match (optional)
                - index: Element index if multiple matches (default: 0)

        Returns:
            List[TextContent] with click result
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        result = await self.dom_interaction_service.click(
            port=port,
            selector=arguments.get("selector"),
            xpath=arguments.get("xpath"),
            text=arguments.get("text"),
            index=arguments.get("index", 0),
        )

        if result.get("success"):
            element_info = result.get("elementInfo", {})
            return [
                TextContent(
                    type="text",
                    text=f"Clicked {element_info.get('tagName', 'element')} "
                    f"'{element_info.get('text', '')[:50]}'",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Click failed: {result.get('error', 'Unknown error')}",
                )
            ]

    async def handle_fill(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Fill a single form field.

        Args:
            arguments: Dict with:
                - port: Browser daemon port (optional, auto-resolved)
                - value: Value to fill (required)
                - selector: CSS selector (optional)
                - xpath: XPath selector (optional)
                - index: Element index if multiple matches (default: 0)

        Returns:
            List[TextContent] with fill result
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        value = arguments.get("value")
        if value is None:
            return [
                TextContent(
                    type="text", text="Error: 'value' is required for fill action"
                )
            ]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        result = await self.dom_interaction_service.fill_field(
            port=port,
            value=value,
            selector=arguments.get("selector"),
            xpath=arguments.get("xpath"),
            index=arguments.get("index", 0),
        )

        if result.get("success"):
            return [TextContent(type="text", text=f"Filled field with: {value}")]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Fill failed: {result.get('error', 'Unknown error')}",
                )
            ]

    async def handle_select(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Select dropdown option.

        Args:
            arguments: Dict with:
                - port: Browser daemon port (optional, auto-resolved)
                - selector: CSS selector for select element (required)
                - option_value: Option value attribute (optional)
                - option_text: Option text content (optional)
                - option_index: Option index (optional)

        Returns:
            List[TextContent] with select result
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        selector = arguments.get("selector")
        if not selector:
            return [
                TextContent(
                    type="text", text="Error: 'selector' is required for select action"
                )
            ]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        result = await self.dom_interaction_service.select_option(
            port=port,
            selector=selector,
            option_value=arguments.get("option_value"),
            option_text=arguments.get("option_text"),
            option_index=arguments.get("option_index"),
        )

        if result.get("success"):
            return [
                TextContent(
                    type="text",
                    text=f"Selected: {result.get('selectedText', '')} "
                    f"(value: {result.get('selectedValue', '')})",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Select failed: {result.get('error', 'Unknown error')}",
                )
            ]

    async def handle_wait(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Wait for element to appear.

        Args:
            arguments: Dict with:
                - port: Browser daemon port (optional, auto-resolved)
                - selector: CSS selector (required)
                - timeout: Timeout in milliseconds (default: 5000)

        Returns:
            List[TextContent] with wait result
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        selector = arguments.get("selector")
        if not selector:
            return [
                TextContent(
                    type="text", text="Error: 'selector' is required for wait action"
                )
            ]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        timeout = arguments.get("timeout", 5000)

        result = await self.dom_interaction_service.wait_for_element(
            port=port, selector=selector, timeout=timeout
        )

        if result.get("success"):
            element_info = result.get("elementInfo", {})
            return [
                TextContent(
                    type="text",
                    text=f"Element appeared: {element_info.get('tagName', 'element')} "
                    f"'{selector}'",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Wait timeout ({timeout}ms): {result.get('error', '')}",
                )
            ]

    async def handle_get_element(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get element information.

        Args:
            arguments: Dict with:
                - port: Browser daemon port (optional, auto-resolved)
                - selector: CSS selector (optional)
                - xpath: XPath selector (optional)
                - text: Text content to match (optional)

        Returns:
            List[TextContent] with element information
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        result = await self.dom_interaction_service.get_element(
            port=port,
            selector=arguments.get("selector"),
            xpath=arguments.get("xpath"),
            text=arguments.get("text"),
        )

        if result.get("success"):
            el = result.get("elementInfo", {})
            info = (
                f"Element: {el.get('tagName', 'unknown')}\n"
                f"  ID: {el.get('id', 'none')}\n"
                f"  Class: {el.get('className', 'none')}\n"
                f"  Text: {el.get('text', '')[:100]}\n"
                f"  Visible: {el.get('isVisible', False)}\n"
                f"  Enabled: {el.get('isEnabled', False)}"
            )
            if el.get("value"):
                info += f"\n  Value: {el['value']}"
            if el.get("href"):
                info += f"\n  Href: {el['href']}"
            return [TextContent(type="text", text=info)]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Element not found: {result.get('error', 'Unknown error')}",
                )
            ]
