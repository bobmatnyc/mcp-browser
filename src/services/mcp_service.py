"""MCP server implementation with consolidated tools.

This module provides 5 consolidated MCP tools for browser control:
- browser_action: navigate, click, fill, select, wait
- browser_query: logs, element, capabilities
- browser_screenshot: capture screenshots
- browser_form: fill_form (multi-field), submit_form
- browser_extract: content, semantic_dom
"""

import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import ImageContent, TextContent, Tool

from .tools import (
    CapabilityToolService,
    DOMToolService,
    FormToolService,
    LogQueryToolService,
    NavigationToolService,
    PortResolver,
    ScreenshotToolService,
)

logger = logging.getLogger(__name__)


class MCPService:
    """MCP server for browser tools with consolidated tool set.

    Provides 5 tools instead of 13 for improved LLM efficiency:
    - browser_action: navigate, click, fill, select, wait
    - browser_query: logs, element, capabilities
    - browser_screenshot: capture screenshots
    - browser_form: fill_form, submit_form
    - browser_extract: content, semantic_dom
    """

    def __init__(
        self,
        browser_service=None,
        dom_interaction_service=None,
        browser_controller=None,
        capability_detector=None,
    ):
        """Initialize MCP service.

        Args:
            browser_service: Browser service for navigation and logs
            dom_interaction_service: DOM interaction service for element manipulation
            browser_controller: Optional BrowserController for AppleScript fallback
            capability_detector: Optional CapabilityDetector for capability reporting
        """
        self.browser_service = browser_service
        self.dom_interaction_service = dom_interaction_service
        self.browser_controller = browser_controller
        self.capability_detector = capability_detector
        self.port_resolver = PortResolver()
        self.navigation_tool_service = NavigationToolService(
            browser_service=browser_service,
            browser_controller=browser_controller,
        )
        self.screenshot_tool_service = ScreenshotToolService(
            browser_service=browser_service
        )
        self.dom_tool_service = DOMToolService(
            dom_interaction_service=dom_interaction_service,
            port_resolver=self.port_resolver,
        )
        self.form_tool_service = FormToolService(
            dom_interaction_service=dom_interaction_service,
            port_resolver=self.port_resolver,
        )
        self.log_query_tool_service = LogQueryToolService(
            browser_service=browser_service
        )
        self.capability_tool_service = CapabilityToolService(
            capability_detector=capability_detector
        )
        # Initialize server with version info
        self.server = Server(
            name="mcp-browser",
            version="2.0.0",  # Major version bump for consolidated tools
            instructions="Browser control and console log capture for web automation. "
            "Uses 5 consolidated tools for efficient interaction.",
        )
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Set up consolidated MCP tools (5 tools instead of 13)."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                # Tool 1: browser_action - navigate, click, fill, select, wait
                Tool(
                    name="browser_action",
                    description="Perform browser actions: navigate to URL, click elements, "
                    "fill single form field, select dropdown option, or wait for element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["navigate", "click", "fill", "select", "wait"],
                                "description": "Action to perform",
                            },
                            "port": {
                                "type": "integer",
                                "description": "Browser port (optional, auto-detected from running daemon)",
                            },
                            # navigate params
                            "url": {
                                "type": "string",
                                "description": "[navigate] URL to navigate to",
                            },
                            # click/fill/select/wait params
                            "selector": {
                                "type": "string",
                                "description": "[click/fill/select/wait] CSS selector for element",
                            },
                            "xpath": {
                                "type": "string",
                                "description": "[click/fill/select] XPath expression for element",
                            },
                            "text": {
                                "type": "string",
                                "description": "[click] Text content to match for clicking",
                            },
                            "index": {
                                "type": "integer",
                                "description": "[click/fill] Element index if multiple matches",
                                "default": 0,
                            },
                            # fill params
                            "value": {
                                "type": "string",
                                "description": "[fill] Value to fill in the field",
                            },
                            # select params
                            "option_value": {
                                "type": "string",
                                "description": "[select] Option value attribute to select",
                            },
                            "option_text": {
                                "type": "string",
                                "description": "[select] Option text content to select",
                            },
                            "option_index": {
                                "type": "integer",
                                "description": "[select] Option index to select",
                            },
                            # wait params
                            "timeout": {
                                "type": "integer",
                                "description": "[wait] Timeout in milliseconds",
                                "default": 5000,
                            },
                        },
                        "required": ["action"],
                    },
                ),
                # Tool 2: browser_query - logs, element, capabilities
                Tool(
                    name="browser_query",
                    description="Query browser state: get console logs, element info, or capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "enum": ["logs", "element", "capabilities"],
                                "description": "Type of query to perform",
                            },
                            "port": {
                                "type": "integer",
                                "description": "Browser port (optional, auto-detected from running daemon)",
                            },
                            # logs params
                            "last_n": {
                                "type": "integer",
                                "description": "[logs] Number of recent logs to return",
                                "default": 100,
                            },
                            "level_filter": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["debug", "info", "log", "warn", "error"],
                                },
                                "description": "[logs] Filter by log levels",
                            },
                            # element params
                            "selector": {
                                "type": "string",
                                "description": "[element] CSS selector for the element",
                            },
                            "xpath": {
                                "type": "string",
                                "description": "[element] XPath expression for the element",
                            },
                            "text": {
                                "type": "string",
                                "description": "[element] Text content to match",
                            },
                        },
                        "required": ["query"],
                    },
                ),
                # Tool 3: browser_screenshot - standalone for visual feedback
                Tool(
                    name="browser_screenshot",
                    description="Capture a screenshot of browser viewport",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "Browser port (optional, auto-detected from running daemon)",
                            },
                            "url": {
                                "type": "string",
                                "description": "Optional URL to navigate to before screenshot",
                            },
                        },
                        "required": [],
                    },
                ),
                # Tool 4: browser_form - fill_form (multi-field), submit
                Tool(
                    name="browser_form",
                    description="Form operations: fill multiple fields at once or submit form",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["fill", "submit"],
                                "description": "Form action to perform",
                            },
                            "port": {
                                "type": "integer",
                                "description": "Browser port (optional, auto-detected from running daemon)",
                            },
                            # fill params
                            "form_data": {
                                "type": "object",
                                "description": "[fill] Object mapping selectors to values",
                                "additionalProperties": {"type": "string"},
                            },
                            "submit": {
                                "type": "boolean",
                                "description": "[fill] Submit form after filling",
                                "default": False,
                            },
                            # submit params
                            "selector": {
                                "type": "string",
                                "description": "[submit] CSS selector for form or form element",
                            },
                            "xpath": {
                                "type": "string",
                                "description": "[submit] XPath expression for form",
                            },
                        },
                        "required": ["action"],
                    },
                ),
                # Tool 5: browser_extract - content, semantic_dom
                Tool(
                    name="browser_extract",
                    description="Extract page content: readable article content or semantic DOM structure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "extract": {
                                "type": "string",
                                "enum": ["content", "semantic_dom"],
                                "description": "Type of extraction: content (readable article) or semantic_dom (structure)",
                            },
                            "port": {
                                "type": "integer",
                                "description": "Browser port (optional, auto-detected from running daemon)",
                            },
                            "tab_id": {
                                "type": "integer",
                                "description": "Optional specific tab ID to extract from",
                            },
                            # semantic_dom params
                            "include_headings": {
                                "type": "boolean",
                                "description": "[semantic_dom] Extract h1-h6 headings (default: true)",
                            },
                            "include_landmarks": {
                                "type": "boolean",
                                "description": "[semantic_dom] Extract ARIA landmarks (default: true)",
                            },
                            "include_links": {
                                "type": "boolean",
                                "description": "[semantic_dom] Extract links with text (default: true)",
                            },
                            "include_forms": {
                                "type": "boolean",
                                "description": "[semantic_dom] Extract forms and fields (default: true)",
                            },
                            "max_text_length": {
                                "type": "integer",
                                "description": "[semantic_dom] Max characters per text field (default: 100)",
                            },
                        },
                        "required": ["extract"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict
        ) -> list[TextContent | ImageContent]:
            """Handle tool calls with routing to consolidated handlers."""

            if name == "browser_action":
                return await self._handle_browser_action(arguments)
            elif name == "browser_query":
                return await self._handle_browser_query(arguments)
            elif name == "browser_screenshot":
                return await self._handle_screenshot(arguments)
            elif name == "browser_form":
                return await self._handle_browser_form(arguments)
            elif name == "browser_extract":
                return await self._handle_browser_extract(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    # ========================================================================
    # Consolidated Handler: browser_action (navigate, click, fill, select, wait)
    # ========================================================================

    async def _handle_browser_action(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle browser_action tool - consolidated actions.

        Actions: navigate, click, fill, select, wait
        """
        action = arguments.get("action")

        if action == "navigate":
            return await self._action_navigate(arguments)
        elif action == "click":
            return await self._action_click(arguments)
        elif action == "fill":
            return await self._action_fill(arguments)
        elif action == "select":
            return await self._action_select(arguments)
        elif action == "wait":
            return await self._action_wait(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown action: {action}. Valid: navigate, click, fill, select, wait",
                )
            ]

    async def _action_navigate(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle navigation action."""
        url = arguments.get("url")
        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        return await self.navigation_tool_service.handle_navigate(port, url)

    async def _action_click(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle click action."""
        return await self.dom_tool_service.handle_click(arguments)

    async def _action_fill(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle fill action (single field)."""
        return await self.dom_tool_service.handle_fill(arguments)

    async def _action_select(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle select action (dropdown)."""
        return await self.dom_tool_service.handle_select(arguments)

    async def _action_wait(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle wait action."""
        return await self.dom_tool_service.handle_wait(arguments)

    # ========================================================================
    # Consolidated Handler: browser_query (logs, element, capabilities)
    # ========================================================================

    async def _handle_browser_query(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle browser_query tool - consolidated queries.

        Queries: logs, element, capabilities
        """
        query = arguments.get("query")

        if query == "logs":
            return await self._query_logs(arguments)
        elif query == "element":
            return await self._query_element(arguments)
        elif query == "capabilities":
            return await self._query_capabilities(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown query: {query}. Valid: logs, element, capabilities",
                )
            ]

    async def _query_logs(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle logs query."""
        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        last_n = arguments.get("last_n", 100)
        level_filter = arguments.get("level_filter")

        # Delegate to log query tool service
        result = await self.log_query_tool_service.handle_query_logs(
            port=port, last_n=last_n, level_filter=level_filter
        )

        return [TextContent(type="text", text=result["formatted_text"])]

    async def _query_element(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle element query."""
        return await self.dom_tool_service.handle_get_element(arguments)

    async def _query_capabilities(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle capabilities query."""
        # Delegate to capability tool service
        result = await self.capability_tool_service.handle_get_capabilities()
        return [TextContent(type="text", text=result["formatted_text"])]

    # ========================================================================
    # Standalone Handler: browser_screenshot
    # ========================================================================

    async def _handle_screenshot(
        self, arguments: Dict[str, Any]
    ) -> List[ImageContent | TextContent]:
        """Handle screenshot capture via browser extension."""
        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        # Delegate to screenshot tool service
        url = arguments.get("url")
        result = await self.screenshot_tool_service.handle_screenshot(
            port=port, url=url
        )

        if result.get("success"):
            return [
                ImageContent(type="image", data=result["data"], mimeType="image/png")
            ]
        else:
            error_msg = result.get("error", "Unknown error")
            return [
                TextContent(
                    type="text",
                    text=f"Screenshot capture failed for port {port}: {error_msg}. "
                    f"Ensure browser extension is connected.",
                )
            ]

    # ========================================================================
    # Consolidated Handler: browser_form (fill, submit)
    # ========================================================================

    async def _handle_browser_form(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle browser_form tool - consolidated form operations.

        Actions: fill (multi-field), submit
        """
        action = arguments.get("action")

        if action == "fill":
            return await self._form_fill(arguments)
        elif action == "submit":
            return await self._form_submit(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown form action: {action}. Valid: fill, submit",
                )
            ]

    async def _form_fill(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle form fill (multiple fields)."""
        return await self.form_tool_service.handle_fill_form(arguments)

    async def _form_submit(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle form submit."""
        return await self.form_tool_service.handle_submit_form(arguments)

    # ========================================================================
    # Consolidated Handler: browser_extract (content, semantic_dom)
    # ========================================================================

    async def _handle_browser_extract(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle browser_extract tool - consolidated extraction.

        Extractions: content (readable article), semantic_dom (structure)
        """
        extract = arguments.get("extract")

        if extract == "content":
            return await self._extract_content(arguments)
        elif extract == "semantic_dom":
            return await self._extract_semantic_dom(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown extract type: {extract}. Valid: content, semantic_dom",
                )
            ]

    async def _extract_content(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle content extraction using Readability."""
        if not self.browser_service:
            return [TextContent(type="text", text="Browser service not available")]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

        tab_id = arguments.get("tab_id")

        result = await self.browser_service.extract_content(port=port, tab_id=tab_id)

        if result.get("success"):
            content = result.get("content", {})
            lines = [f"# {content.get('title', 'Untitled')}", ""]

            # Metadata
            if content.get("byline"):
                lines.append(f"**Author:** {content['byline']}")
            if content.get("siteName"):
                lines.append(f"**Source:** {content['siteName']}")
            if content.get("wordCount"):
                lines.append(f"**Words:** {content['wordCount']:,}")

            lines.extend(["", "---", ""])

            # Excerpt
            if content.get("excerpt"):
                lines.extend([f"> {content['excerpt']}", ""])

            # Main text
            text = content.get("textContent", "")
            if text:
                max_chars = 50000
                if len(text) > max_chars:
                    text = (
                        text[:max_chars]
                        + f"\n\n[Truncated {len(text) - max_chars:,} chars]"
                    )
                lines.append(text)
            else:
                lines.append("[No readable content extracted]")

            if content.get("fallback"):
                lines.extend(
                    [
                        "",
                        "---",
                        "*Fallback extraction - page may not be optimized for reading*",
                    ]
                )

            return [TextContent(type="text", text="\n".join(lines))]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Content extraction failed: {result.get('error', 'Unknown error')}",
                )
            ]

    async def _extract_semantic_dom(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle semantic DOM extraction."""
        if not self.browser_service:
            return [TextContent(type="text", text="Browser service not available")]

        port, port_warning = self.port_resolver.resolve_port(arguments.get("port"))
        if port is None:
            return [TextContent(type="text", text=port_warning or "No port available")]

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
            return [
                TextContent(
                    type="text",
                    text=f"Semantic DOM extraction failed: {result.get('error', 'Unknown error')}",
                )
            ]

    def _format_semantic_dom(self, dom: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Format semantic DOM as readable text output."""
        lines = []
        lines.append(f"# {dom.get('title', 'Untitled')}")
        lines.append(f"URL: {dom.get('url', 'unknown')}")
        lines.append("")

        # Headings
        headings = dom.get("headings", [])
        if headings and options.get("include_headings", True):
            lines.append("## Outline")
            for h in headings:
                indent = "  " * (h.get("level", 1) - 1)
                text = h.get("text", "")[:100]
                lines.append(f"{indent}- H{h.get('level')}: {text}")
            lines.append("")

        # Landmarks
        landmarks = dom.get("landmarks", [])
        if landmarks and options.get("include_landmarks", True):
            lines.append("## Sections")
            for lm in landmarks:
                role = lm.get("role", "unknown")
                label = lm.get("label") or lm.get("tag", "")
                lines.append(f"- [{role}] {label}" if label else f"- [{role}]")
            lines.append("")

        # Links
        links = dom.get("links", [])
        if links and options.get("include_links", True):
            lines.append(f"## Links ({len(links)})")
            for link in links[:50]:
                text = (
                    link.get("text", "").strip()[:80]
                    or link.get("ariaLabel", "")
                    or "[no text]"
                )
                href = link.get("href", "")
                lines.append(f"- {text}")
                if href and not href.startswith("javascript:"):
                    lines.append(f"  → {href[:100]}")
            if len(links) > 50:
                lines.append(f"  ... +{len(links) - 50} more")
            lines.append("")

        # Forms
        forms = dom.get("forms", [])
        if forms and options.get("include_forms", True):
            lines.append(f"## Forms ({len(forms)})")
            for form in forms:
                name = (
                    form.get("name")
                    or form.get("id")
                    or form.get("ariaLabel")
                    or "[unnamed]"
                )
                lines.append(f"### {name}")
                if form.get("action"):
                    lines.append(f"  Action: {form.get('action')}")
                lines.append(f"  Method: {form.get('method', 'GET').upper()}")
                fields = form.get("fields", [])
                if fields:
                    lines.append("  Fields:")
                    for field in fields:
                        ftype = field.get("type", "text")
                        fname = field.get("name") or field.get("id") or "[unnamed]"
                        label = (
                            field.get("label")
                            or field.get("ariaLabel")
                            or field.get("placeholder")
                            or ""
                        )
                        req = " (required)" if field.get("required") else ""
                        if label:
                            lines.append(f"    - {fname} ({ftype}): {label}{req}")
                        else:
                            lines.append(f"    - {fname} ({ftype}){req}")
            lines.append("")

        return "\n".join(lines)

    # ========================================================================
    # Server lifecycle methods
    # ========================================================================

    async def start(self) -> None:
        """Start the MCP server."""
        # The actual server start is handled by the stdio transport
        pass

    async def run_stdio(self) -> None:
        """Run the MCP server with stdio transport."""
        from mcp.server import NotificationOptions
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            init_options = self.server.create_initialization_options(
                notification_options=NotificationOptions(
                    tools_changed=False, prompts_changed=False, resources_changed=False
                ),
                experimental_capabilities={},
            )

            await self.server.run(
                read_stream,
                write_stream,
                init_options,
                raise_exceptions=False,
                stateless=False,
            )
