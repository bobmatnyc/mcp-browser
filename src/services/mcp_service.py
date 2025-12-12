"""MCP server implementation."""

import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import ImageContent, TextContent, Tool

logger = logging.getLogger(__name__)


class MCPService:
    """MCP server for browser tools."""

    def __init__(
        self,
        browser_service=None,
        screenshot_service=None,
        dom_interaction_service=None,
        browser_controller=None,
        capability_detector=None,
    ):
        """Initialize MCP service.

        Args:
            browser_service: Browser service for navigation and logs
            screenshot_service: Screenshot service for captures
            dom_interaction_service: DOM interaction service for element manipulation
            browser_controller: Optional BrowserController for AppleScript fallback
            capability_detector: Optional CapabilityDetector for capability reporting
        """
        self.browser_service = browser_service
        self.screenshot_service = screenshot_service
        self.dom_interaction_service = dom_interaction_service
        self.browser_controller = browser_controller
        self.capability_detector = capability_detector
        # Initialize server with version info
        self.server = Server(
            name="mcp-browser",
            version="1.0.3",
            instructions="Browser control and console log capture for web automation",
        )
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Set up MCP tools."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="browser_navigate",
                    description="Navigate browser to a specific URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "url": {
                                "type": "string",
                                "description": "URL to navigate to",
                            },
                        },
                        "required": ["port", "url"],
                    },
                ),
                Tool(
                    name="browser_query_logs",
                    description="Query console logs from browser",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "last_n": {
                                "type": "integer",
                                "description": "Number of recent logs to return",
                                "default": 100,
                            },
                            "level_filter": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["debug", "info", "log", "warn", "error"],
                                },
                                "description": "Filter by log levels",
                            },
                        },
                        "required": ["port"],
                    },
                ),
                Tool(
                    name="browser_screenshot",
                    description="Capture a screenshot of browser viewport",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "url": {
                                "type": "string",
                                "description": "Optional URL to navigate to before screenshot",
                            },
                        },
                        "required": ["port"],
                    },
                ),
                Tool(
                    name="browser_click",
                    description="Click an element on the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the element",
                            },
                            "xpath": {
                                "type": "string",
                                "description": "XPath expression for the element",
                            },
                            "text": {
                                "type": "string",
                                "description": "Text content to match",
                            },
                            "index": {
                                "type": "integer",
                                "description": "Element index if multiple matches",
                                "default": 0,
                            },
                        },
                        "required": ["port"],
                    },
                ),
                Tool(
                    name="browser_fill_field",
                    description="Fill a form field with a value",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the field",
                            },
                            "xpath": {
                                "type": "string",
                                "description": "XPath expression for the field",
                            },
                            "value": {
                                "type": "string",
                                "description": "Value to fill in the field",
                            },
                            "index": {
                                "type": "integer",
                                "description": "Field index if multiple matches",
                                "default": 0,
                            },
                        },
                        "required": ["port", "value"],
                    },
                ),
                Tool(
                    name="browser_fill_form",
                    description="Fill multiple form fields at once",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "form_data": {
                                "type": "object",
                                "description": "Object mapping selectors to values",
                                "additionalProperties": {"type": "string"},
                            },
                            "submit": {
                                "type": "boolean",
                                "description": "Submit form after filling",
                                "default": False,
                            },
                        },
                        "required": ["port", "form_data"],
                    },
                ),
                Tool(
                    name="browser_submit_form",
                    description="Submit a form",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for form or form element",
                            },
                            "xpath": {
                                "type": "string",
                                "description": "XPath expression for form",
                            },
                        },
                        "required": ["port"],
                    },
                ),
                Tool(
                    name="browser_get_element",
                    description="Get information about an element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the element",
                            },
                            "xpath": {
                                "type": "string",
                                "description": "XPath expression for the element",
                            },
                            "text": {
                                "type": "string",
                                "description": "Text content to match",
                            },
                        },
                        "required": ["port"],
                    },
                ),
                Tool(
                    name="browser_wait_for_element",
                    description="Wait for an element to appear on the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the element",
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Timeout in milliseconds",
                                "default": 5000,
                            },
                        },
                        "required": ["port", "selector"],
                    },
                ),
                Tool(
                    name="browser_select_option",
                    description="Select an option from a dropdown",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for select element",
                            },
                            "option_value": {
                                "type": "string",
                                "description": "Option value attribute",
                            },
                            "option_text": {
                                "type": "string",
                                "description": "Option text content",
                            },
                            "option_index": {
                                "type": "integer",
                                "description": "Option index",
                            },
                        },
                        "required": ["port", "selector"],
                    },
                ),
                Tool(
                    name="browser_extract_content",
                    description="Extract readable content from the current page using Mozilla's Readability",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "tab_id": {
                                "type": "integer",
                                "description": "Optional specific tab ID to extract from",
                            },
                        },
                        "required": ["port"],
                    },
                ),
                Tool(
                    name="browser_extract_semantic_dom",
                    description="Extract semantic DOM structure (headings, landmarks, links, forms) for quick page understanding",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port number",
                            },
                            "tab_id": {
                                "type": "integer",
                                "description": "Optional specific tab ID",
                            },
                            "include_headings": {
                                "type": "boolean",
                                "description": "Extract h1-h6 headings (default: true)",
                            },
                            "include_landmarks": {
                                "type": "boolean",
                                "description": "Extract ARIA landmarks and HTML5 sectioning (default: true)",
                            },
                            "include_links": {
                                "type": "boolean",
                                "description": "Extract links with text (default: true)",
                            },
                            "include_forms": {
                                "type": "boolean",
                                "description": "Extract forms and fields (default: true)",
                            },
                            "max_text_length": {
                                "type": "integer",
                                "description": "Max characters per text field (default: 100)",
                            },
                        },
                        "required": ["port"],
                    },
                ),
                Tool(
                    name="get_capabilities",
                    description="Get current browser control capabilities and available methods",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict
        ) -> list[TextContent | ImageContent]:
            """Handle tool calls."""

            if name == "browser_navigate":
                return await self._handle_navigate(arguments)
            elif name == "browser_query_logs":
                return await self._handle_query_logs(arguments)
            elif name == "browser_screenshot":
                return await self._handle_screenshot(arguments)
            elif name == "browser_click":
                return await self._handle_click(arguments)
            elif name == "browser_fill_field":
                return await self._handle_fill_field(arguments)
            elif name == "browser_fill_form":
                return await self._handle_fill_form(arguments)
            elif name == "browser_submit_form":
                return await self._handle_submit_form(arguments)
            elif name == "browser_get_element":
                return await self._handle_get_element(arguments)
            elif name == "browser_wait_for_element":
                return await self._handle_wait_for_element(arguments)
            elif name == "browser_select_option":
                return await self._handle_select_option(arguments)
            elif name == "browser_extract_content":
                return await self._handle_extract_content(arguments)
            elif name == "browser_extract_semantic_dom":
                return await self._handle_extract_semantic_dom(arguments)
            elif name == "get_capabilities":
                return await self._handle_get_capabilities(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _handle_navigate(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle browser navigation with automatic AppleScript fallback.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        port = arguments.get("port")
        url = arguments.get("url")

        # Try BrowserController first for automatic fallback support
        if self.browser_controller:
            result = await self.browser_controller.navigate(url=url, port=port)

            if result["success"]:
                method = result.get("method", "extension")
                if method == "applescript":
                    return [
                        TextContent(
                            type="text",
                            text=f"Successfully navigated to {url} using AppleScript fallback.\n\n"
                            f"Note: Console log capture requires the browser extension.\n"
                            f"Install extension: mcp-browser quickstart",
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Successfully navigated browser on port {port} to {url}",
                        )
                    ]
            else:
                error_msg = result.get("error", "Unknown error")
                return [
                    TextContent(type="text", text=f"Failed to navigate: {error_msg}")
                ]

        # Fallback to direct browser_service (legacy path)
        if not self.browser_service:
            return [TextContent(type="text", text="Browser service not available")]

        success = await self.browser_service.navigate_browser(port, url)

        if success:
            return [
                TextContent(
                    type="text",
                    text=f"Successfully navigated browser on port {port} to {url}",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to navigate browser on port {port}. "
                    f"No active connection found.",
                )
            ]

    async def _handle_query_logs(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle log query.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        port = arguments.get("port")
        last_n = arguments.get("last_n", 100)
        level_filter = arguments.get("level_filter")

        if not self.browser_service:
            return [TextContent(type="text", text="Browser service not available")]

        messages = await self.browser_service.query_logs(
            port=port, last_n=last_n, level_filter=level_filter
        )

        if not messages:
            return [
                TextContent(type="text", text=f"No console logs found for port {port}")
            ]

        # Format messages
        log_lines = []
        for msg in messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S.%f")[:-3]
            level = msg.level.value.upper()
            log_lines.append(f"[{timestamp}] [{level}] {msg.message}")

            if msg.stack_trace:
                log_lines.append(f"  Stack: {msg.stack_trace[:200]}")

        log_text = "\n".join(log_lines)

        return [
            TextContent(
                type="text",
                text=f"Console logs from port {port} (last {len(messages)} messages):\n\n{log_text}",
            )
        ]

    async def _handle_screenshot(
        self, arguments: Dict[str, Any]
    ) -> List[ImageContent | TextContent]:
        """Handle screenshot capture.

        Args:
            arguments: Tool arguments

        Returns:
            List of image or text content responses
        """
        port = arguments.get("port")
        url = arguments.get("url")

        if not self.screenshot_service:
            return [TextContent(type="text", text="Screenshot service not available")]

        screenshot_base64 = await self.screenshot_service.capture_screenshot(
            port=port, url=url
        )

        if screenshot_base64:
            return [
                ImageContent(type="image", data=screenshot_base64, mimeType="image/png")
            ]
        else:
            return [
                TextContent(
                    type="text", text=f"Failed to capture screenshot for port {port}"
                )
            ]

    async def _handle_click(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle element click.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port = arguments.get("port")
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
                    text=f"Successfully clicked element: {element_info.get('tagName', 'unknown')} "
                    f"with text '{element_info.get('text', '')[:50]}'",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to click element: {result.get('error', 'Unknown error')}",
                )
            ]

    async def _handle_fill_field(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle form field filling.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port = arguments.get("port")
        value = arguments.get("value")
        result = await self.dom_interaction_service.fill_field(
            port=port,
            value=value,
            selector=arguments.get("selector"),
            xpath=arguments.get("xpath"),
            index=arguments.get("index", 0),
        )

        if result.get("success"):
            return [
                TextContent(
                    type="text", text=f"Successfully filled field with value: {value}"
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to fill field: {result.get('error', 'Unknown error')}",
                )
            ]

    async def _handle_fill_form(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle multiple form fields filling.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port = arguments.get("port")
        form_data = arguments.get("form_data", {})
        submit = arguments.get("submit", False)

        result = await self.dom_interaction_service.fill_form(
            port=port, form_data=form_data, submit=submit
        )

        if result.get("success"):
            filled_count = len(result.get("fields", {}))
            submitted = result.get("submitted", False)
            msg = f"Successfully filled {filled_count} form fields"
            if submit and submitted:
                msg += " and submitted the form"
            return [TextContent(type="text", text=msg)]
        else:
            errors = result.get("errors", [])
            return [
                TextContent(
                    type="text",
                    text=f"Failed to fill form. Errors: {'; '.join(errors)}",
                )
            ]

    async def _handle_submit_form(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle form submission.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port = arguments.get("port")
        result = await self.dom_interaction_service.submit_form(
            port=port, selector=arguments.get("selector"), xpath=arguments.get("xpath")
        )

        if result.get("success"):
            return [TextContent(type="text", text="Successfully submitted form")]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to submit form: {result.get('error', 'Unknown error')}",
                )
            ]

    async def _handle_get_element(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle getting element information.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port = arguments.get("port")
        result = await self.dom_interaction_service.get_element(
            port=port,
            selector=arguments.get("selector"),
            xpath=arguments.get("xpath"),
            text=arguments.get("text"),
        )

        if result.get("success"):
            element_info = result.get("elementInfo", {})
            info_text = (
                f"Element found: {element_info.get('tagName', 'unknown')}\n"
                f"  ID: {element_info.get('id', 'none')}\n"
                f"  Class: {element_info.get('className', 'none')}\n"
                f"  Text: {element_info.get('text', '')[:100]}\n"
                f"  Visible: {element_info.get('isVisible', False)}\n"
                f"  Enabled: {element_info.get('isEnabled', False)}"
            )

            if element_info.get("value"):
                info_text += f"\n  Value: {element_info['value']}"
            if element_info.get("href"):
                info_text += f"\n  Href: {element_info['href']}"

            return [TextContent(type="text", text=info_text)]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Element not found: {result.get('error', 'Unknown error')}",
                )
            ]

    async def _handle_wait_for_element(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle waiting for element.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port = arguments.get("port")
        selector = arguments.get("selector")
        timeout = arguments.get("timeout", 5000)

        result = await self.dom_interaction_service.wait_for_element(
            port=port, selector=selector, timeout=timeout
        )

        if result.get("success"):
            element_info = result.get("elementInfo", {})
            return [
                TextContent(
                    type="text",
                    text=f"Element appeared: {element_info.get('tagName', 'unknown')} "
                    f"with selector '{selector}'",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Element did not appear within {timeout}ms: {result.get('error', '')}",
                )
            ]

    async def _handle_select_option(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle dropdown option selection.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if not self.dom_interaction_service:
            return [
                TextContent(type="text", text="DOM interaction service not available")
            ]

        port = arguments.get("port")
        result = await self.dom_interaction_service.select_option(
            port=port,
            selector=arguments.get("selector"),
            option_value=arguments.get("option_value"),
            option_text=arguments.get("option_text"),
            option_index=arguments.get("option_index"),
        )

        if result.get("success"):
            return [
                TextContent(
                    type="text",
                    text=f"Selected option: {result.get('selectedText', '')} "
                    f"(value: {result.get('selectedValue', '')})",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to select option: {result.get('error', 'Unknown error')}",
                )
            ]

    async def _handle_extract_content(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle content extraction using Readability.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if not self.browser_service:
            return [TextContent(type="text", text="Browser service not available")]

        port = arguments.get("port")
        tab_id = arguments.get("tab_id")

        result = await self.browser_service.extract_content(port=port, tab_id=tab_id)

        if result.get("success"):
            content = result.get("content", {})

            # Format the extracted content for output
            output_lines = [f"# {content.get('title', 'Untitled')}", ""]

            # Add metadata if available
            metadata = content.get("metadata", {})
            if content.get("byline"):
                output_lines.append(f"**Author:** {content['byline']}")
            if metadata.get("publishDate"):
                output_lines.append(f"**Published:** {metadata['publishDate']}")
            if content.get("siteName"):
                output_lines.append(f"**Source:** {content['siteName']}")
            if metadata.get("url"):
                output_lines.append(f"**URL:** {metadata['url']}")
            if content.get("wordCount"):
                output_lines.append(f"**Word Count:** {content['wordCount']:,}")
            if content.get("length"):
                output_lines.append(f"**Reading Time:** ~{content['length']} minutes")

            output_lines.extend(["", "---", ""])

            # Add excerpt if available
            if content.get("excerpt"):
                output_lines.extend(["**Excerpt:**", f"> {content['excerpt']}", ""])

            # Add main text content
            output_lines.append("## Content")
            output_lines.append("")

            text = content.get("textContent", "")
            if text:
                # Limit text length for LLM consumption
                max_chars = 50000  # ~12,500 tokens
                if len(text) > max_chars:
                    text = (
                        text[:max_chars]
                        + f"\n\n[Content truncated - {len(text) - max_chars:,} characters omitted]"
                    )
                output_lines.append(text)
            else:
                output_lines.append("[No readable content extracted]")

            # Add fallback notice if applicable
            if content.get("fallback"):
                output_lines.extend(
                    [
                        "",
                        "---",
                        "*Note: This is a fallback extraction. The page may not be optimized for article reading.*",
                    ]
                )

            return [TextContent(type="text", text="\n".join(output_lines))]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to extract content: {result.get('error', 'Unknown error')}",
                )
            ]

    async def _handle_extract_semantic_dom(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle semantic DOM extraction."""
        if not self.browser_service:
            return [TextContent(type="text", text="Browser service not available")]

        port = arguments.get("port")
        tab_id = arguments.get("tab_id")
        options = {
            "include_headings": arguments.get("include_headings", True),
            "include_landmarks": arguments.get("include_landmarks", True),
            "include_links": arguments.get("include_links", True),
            "include_forms": arguments.get("include_forms", True),
            "max_text_length": arguments.get("max_text_length", 100),
        }

        result = await self.browser_service.extract_semantic_dom(port, tab_id, options)

        if result.get("success"):
            dom = result.get("dom", {})
            output = self._format_semantic_dom(dom, options)
            return [TextContent(type="text", text=output)]
        else:
            error = result.get("error", "Unknown error")
            return [TextContent(type="text", text=f"Semantic DOM extraction failed: {error}")]

    def _format_semantic_dom(self, dom: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Format semantic DOM as readable text output."""
        lines = []
        lines.append(f"# Semantic Structure: {dom.get('title', 'Untitled')}")
        lines.append(f"URL: {dom.get('url', 'unknown')}")
        lines.append("")

        # Headings
        headings = dom.get("headings", [])
        if headings and options.get("include_headings", True):
            lines.append("## Document Outline")
            for h in headings:
                indent = "  " * (h.get("level", 1) - 1)
                text = h.get("text", "")[:100]
                lines.append(f"{indent}- H{h.get('level')}: {text}")
            lines.append("")

        # Landmarks
        landmarks = dom.get("landmarks", [])
        if landmarks and options.get("include_landmarks", True):
            lines.append("## Page Sections")
            for lm in landmarks:
                role = lm.get("role", "unknown")
                label = lm.get("label") or lm.get("tag", "")
                if label:
                    lines.append(f"- [{role}] {label}")
                else:
                    lines.append(f"- [{role}]")
            lines.append("")

        # Links
        links = dom.get("links", [])
        if links and options.get("include_links", True):
            lines.append(f"## Links ({len(links)} total)")
            # Show first 50 links to avoid overwhelming output
            for link in links[:50]:
                text = link.get("text", "").strip()[:80] or link.get("ariaLabel", "") or "[no text]"
                href = link.get("href", "")
                lines.append(f"- {text}")
                if href and not href.startswith("javascript:"):
                    lines.append(f"  → {href[:100]}")
            if len(links) > 50:
                lines.append(f"  ... and {len(links) - 50} more links")
            lines.append("")

        # Forms
        forms = dom.get("forms", [])
        if forms and options.get("include_forms", True):
            lines.append(f"## Forms ({len(forms)} total)")
            for form in forms:
                form_name = form.get("name") or form.get("id") or form.get("ariaLabel") or "[unnamed form]"
                lines.append(f"### {form_name}")
                if form.get("action"):
                    lines.append(f"  Action: {form.get('action')}")
                lines.append(f"  Method: {form.get('method', 'GET').upper()}")
                fields = form.get("fields", [])
                if fields:
                    lines.append("  Fields:")
                    for field in fields:
                        field_type = field.get("type", "text")
                        name = field.get("name") or field.get("id") or "[unnamed]"
                        label = field.get("label") or field.get("ariaLabel") or field.get("placeholder") or ""
                        required = " (required)" if field.get("required") else ""
                        if label:
                            lines.append(f"    - {name} ({field_type}): {label}{required}")
                        else:
                            lines.append(f"    - {name} ({field_type}){required}")
            lines.append("")

        return "\n".join(lines)

    async def _handle_get_capabilities(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle capability detection request.

        Args:
            arguments: Tool arguments (empty for this tool)

        Returns:
            List of text content responses
        """
        if not self.capability_detector:
            return [
                TextContent(
                    type="text",
                    text="Capability detection not available (detector not initialized)"
                )
            ]

        try:
            report = await self.capability_detector.get_capability_report()

            # Format the report nicely
            output_lines = [
                "# Browser Control Capabilities",
                "",
                f"**Summary:** {report['summary']}",
                "",
                "## Available Capabilities",
                ""
            ]

            if report['capabilities']:
                for cap in report['capabilities']:
                    output_lines.append(f"- {cap}")
            else:
                output_lines.append("- None")

            output_lines.extend(["", "## Control Methods", ""])

            for method_name, method_info in report['methods'].items():
                status = "✓ Available" if method_info['available'] else "✗ Unavailable"
                output_lines.append(f"### {method_name.title()} {status}")
                output_lines.append(f"*{method_info['description']}*")
                output_lines.append("")
                output_lines.append("**Capabilities:**")
                for cap in method_info['capabilities']:
                    output_lines.append(f"- {cap}")
                output_lines.append("")

            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:
            logger.exception("Failed to get capabilities")
            return [
                TextContent(
                    type="text",
                    text=f"Failed to detect capabilities: {str(e)}"
                )
            ]

    async def start(self) -> None:
        """Start the MCP server."""
        # Initialize server with options
        # Note: InitializationOptions configured for mcp-browser v1.0.1

        # The actual server start is handled by the stdio transport
        # Note: No logging here as it could interfere with MCP JSON-RPC

    async def run_stdio(self) -> None:
        """Run the MCP server with stdio transport."""
        from mcp.server import NotificationOptions
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            # Use the server's create_initialization_options method to properly
            # register all handlers with correct capabilities
            init_options = self.server.create_initialization_options(
                notification_options=NotificationOptions(
                    tools_changed=False, prompts_changed=False, resources_changed=False
                ),
                experimental_capabilities={},
            )

            # Run with stateless=True to avoid initialization state issues
            await self.server.run(
                read_stream,
                write_stream,
                init_options,
                raise_exceptions=False,
                stateless=False,  # Keep stateful for now, but could try True if issues persist
            )
