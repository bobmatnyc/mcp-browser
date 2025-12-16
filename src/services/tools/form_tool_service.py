"""Form operations tool service for MCP browser control."""

import logging
from typing import Any, Dict, List

from mcp.types import TextContent

logger = logging.getLogger(__name__)


class FormToolService:
    """MCP tool handler for form operations."""

    def __init__(self, dom_interaction_service=None, port_resolver=None):
        """Initialize form tool service.

        Args:
            dom_interaction_service: DOM interaction service for form operations
            port_resolver: Port resolution service
        """
        self.dom_interaction_service = dom_interaction_service
        self.port_resolver = port_resolver

    async def handle_fill_form(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Fill multiple form fields.

        Args:
            arguments: Dict with:
                - port: Browser daemon port (optional, auto-resolved)
                - form_data: Dict mapping selectors to values
                - submit: Whether to submit form after filling (default: False)

        Returns:
            List[TextContent] with fill results
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        form_data = arguments.get("form_data")
        if not form_data:
            return [
                TextContent(
                    type="text", text="Error: 'form_data' is required for fill action"
                )
            ]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        submit = arguments.get("submit", False)

        result = await self.dom_interaction_service.fill_form(
            port=port, form_data=form_data, submit=submit
        )

        if result.get("success"):
            filled = len(result.get("fields", {}))
            submitted = result.get("submitted", False)
            msg = f"Filled {filled} fields"
            if submit and submitted:
                msg += " and submitted form"
            return [TextContent(type="text", text=msg)]
        else:
            errors = result.get("errors", [])
            return [
                TextContent(
                    type="text",
                    text=f"Form fill failed: {'; '.join(errors)}",
                )
            ]

    async def handle_submit_form(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Submit a form.

        Args:
            arguments: Dict with:
                - port: Browser daemon port (optional, auto-resolved)
                - selector: CSS selector for form (optional)
                - xpath: XPath selector for form (optional)

        Returns:
            List[TextContent] with submit result
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        result = await self.dom_interaction_service.submit_form(
            port=port,
            selector=arguments.get("selector"),
            xpath=arguments.get("xpath"),
        )

        if result.get("success"):
            return [TextContent(type="text", text="Form submitted")]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Submit failed: {result.get('error', 'Unknown error')}",
                )
            ]
