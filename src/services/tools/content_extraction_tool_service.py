"""Content extraction tool service for MCP browser control.

Handles:
- browser_extract_content: Readability-based article extraction
- browser_extract_semantic_dom: Semantic DOM structure extraction
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ContentExtractionToolService:
    """MCP tool handler for content and semantic DOM extraction."""

    def __init__(self, browser_service=None):
        """Initialize content extraction tool service.

        Args:
            browser_service: Browser service for extraction operations
        """
        self.browser_service = browser_service

    async def handle_extract_content(
        self, port: int, tab_id: int | None = None
    ) -> Dict[str, Any]:
        """Extract readable article content using Readability.

        Args:
            port: Browser port number
            tab_id: Optional specific tab ID to extract from

        Returns:
            Dict with formatted_text (markdown article) and raw content
        """
        if not self.browser_service:
            return {
                "success": False,
                "error": "Browser service not available",
                "formatted_text": "Content extraction failed: Browser service not available",
            }

        result = await self.browser_service.extract_content(port=port, tab_id=tab_id)

        if result.get("success"):
            content = result.get("content", {})
            formatted = self._format_article_content(content)
            return {
                "success": True,
                "formatted_text": formatted,
                "raw_content": content,
            }
        else:
            error = result.get("error", "Unknown error")
            return {
                "success": False,
                "error": error,
                "formatted_text": f"Content extraction failed: {error}",
            }

    async def handle_extract_semantic_dom(
        self,
        port: int,
        tab_id: int | None = None,
        include_headings: bool = True,
        include_landmarks: bool = True,
        include_links: bool = True,
        include_forms: bool = True,
        max_text_length: int = 100,
    ) -> Dict[str, Any]:
        """Extract semantic DOM structure.

        Args:
            port: Browser port number
            tab_id: Optional specific tab ID to extract from
            include_headings: Extract h1-h6 headings
            include_landmarks: Extract ARIA landmarks
            include_links: Extract links with text
            include_forms: Extract forms and fields
            max_text_length: Max characters per text field

        Returns:
            Dict with formatted_text (structured output) and raw DOM
        """
        if not self.browser_service:
            return {
                "success": False,
                "error": "Browser service not available",
                "formatted_text": "Semantic DOM extraction failed: Browser service not available",
            }

        options = {
            "include_headings": include_headings,
            "include_landmarks": include_landmarks,
            "include_links": include_links,
            "include_forms": include_forms,
            "max_text_length": max_text_length,
        }

        result = await self.browser_service.extract_semantic_dom(port, tab_id, options)

        if result.get("success"):
            dom = result.get("dom", {})
            formatted = self._format_semantic_dom(dom, options)
            return {"success": True, "formatted_text": formatted, "raw_dom": dom}
        else:
            error = result.get("error", "Unknown error")
            return {
                "success": False,
                "error": error,
                "formatted_text": f"Semantic DOM extraction failed: {error}",
            }

    def _format_article_content(self, content: Dict[str, Any]) -> str:
        """Format extracted article as markdown.

        Args:
            content: Article content from Readability extraction

        Returns:
            Formatted markdown text
        """
        lines = [f"# {content.get('title', 'Untitled')}", ""]

        # Metadata section
        metadata = self._format_metadata(content)
        if metadata:
            lines.extend(metadata)
            lines.extend(["", "---", ""])

        # Excerpt
        if content.get("excerpt"):
            lines.extend([f"> {content['excerpt']}", ""])

        # Main text content
        text = content.get("textContent", "")
        if text:
            lines.append(self._truncate_text(text, max_chars=50000))
        else:
            lines.append("[No readable content extracted]")

        # Fallback indicator
        if content.get("fallback"):
            lines.extend(
                [
                    "",
                    "---",
                    "*Fallback extraction - page may not be optimized for reading*",
                ]
            )

        return "\n".join(lines)

    def _format_metadata(self, content: Dict[str, Any]) -> List[str]:
        """Format article metadata (author, source, word count).

        Args:
            content: Article content

        Returns:
            List of formatted metadata lines
        """
        lines = []
        if content.get("byline"):
            lines.append(f"**Author:** {content['byline']}")
        if content.get("siteName"):
            lines.append(f"**Source:** {content['siteName']}")
        if content.get("wordCount"):
            lines.append(f"**Words:** {content['wordCount']:,}")
        return lines

    def _truncate_text(self, text: str, max_chars: int) -> str:
        """Truncate text with ellipsis if too long.

        Args:
            text: Text to truncate
            max_chars: Maximum character length

        Returns:
            Truncated text with suffix if truncated
        """
        if len(text) > max_chars:
            return text[:max_chars] + f"\n\n[Truncated {len(text) - max_chars:,} chars]"
        return text

    def _format_semantic_dom(self, dom: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Format semantic DOM structure.

        Args:
            dom: Semantic DOM data (headings, landmarks, links, forms)
            options: Extraction options (what to include)

        Returns:
            Formatted text output
        """
        lines = []

        # Header
        lines.append(f"# {dom.get('title', 'Untitled')}")
        lines.append(f"URL: {dom.get('url', 'unknown')}")
        lines.append("")

        # Headings outline
        if options.get("include_headings", True):
            headings_output = self._format_headings(dom.get("headings", []))
            if headings_output:
                lines.extend(headings_output)

        # Landmarks (sections)
        if options.get("include_landmarks", True):
            landmarks_output = self._format_landmarks(dom.get("landmarks", []))
            if landmarks_output:
                lines.extend(landmarks_output)

        # Links
        if options.get("include_links", True):
            links_output = self._format_links(dom.get("links", []))
            if links_output:
                lines.extend(links_output)

        # Forms
        if options.get("include_forms", True):
            forms_output = self._format_forms(dom.get("forms", []))
            if forms_output:
                lines.extend(forms_output)

        return "\n".join(lines)

    def _format_headings(self, headings: List[Dict[str, Any]]) -> List[str]:
        """Format headings as indented outline.

        Args:
            headings: List of heading dictionaries

        Returns:
            List of formatted heading lines
        """
        if not headings:
            return []

        lines = ["## Outline"]
        for h in headings:
            level = h.get("level", 1)
            text = h.get("text", "")[:100]
            indent = "  " * (level - 1)
            lines.append(f"{indent}- H{level}: {text}")
        lines.append("")

        return lines

    def _format_landmarks(self, landmarks: List[Dict[str, Any]]) -> List[str]:
        """Format ARIA landmarks as section list.

        Args:
            landmarks: List of landmark dictionaries

        Returns:
            List of formatted landmark lines
        """
        if not landmarks:
            return []

        lines = ["## Sections"]
        for lm in landmarks:
            role = lm.get("role", "unknown")
            label = lm.get("label") or lm.get("tag", "")
            if label:
                lines.append(f"- [{role}] {label}")
            else:
                lines.append(f"- [{role}]")
        lines.append("")

        return lines

    def _format_links(
        self, links: List[Dict[str, Any]], max_links: int = 50
    ) -> List[str]:
        """Format links with text and href.

        Args:
            links: List of link dictionaries
            max_links: Maximum number of links to display

        Returns:
            List of formatted link lines
        """
        if not links:
            return []

        lines = [f"## Links ({len(links)})"]

        for link in links[:max_links]:
            text = (
                link.get("text", "").strip()[:80]
                or link.get("ariaLabel", "")
                or "[no text]"
            )
            href = link.get("href", "")

            lines.append(f"- {text}")
            if href and not href.startswith("javascript:"):
                lines.append(f"  → {href[:100]}")

        if len(links) > max_links:
            lines.append(f"  ... +{len(links) - max_links} more")

        lines.append("")
        return lines

    def _format_forms(self, forms: List[Dict[str, Any]]) -> List[str]:
        """Format forms with fields.

        Args:
            forms: List of form dictionaries

        Returns:
            List of formatted form lines
        """
        if not forms:
            return []

        lines = [f"## Forms ({len(forms)})"]

        for form in forms:
            # Form name/identifier
            name = (
                form.get("name")
                or form.get("id")
                or form.get("ariaLabel")
                or "[unnamed]"
            )
            lines.append(f"### {name}")

            # Form attributes
            if form.get("action"):
                lines.append(f"  Action: {form.get('action')}")
            lines.append(f"  Method: {form.get('method', 'GET').upper()}")

            # Fields
            fields = form.get("fields", [])
            if fields:
                lines.append("  Fields:")
                for field in fields:
                    field_line = self._format_field(field)
                    lines.append(f"    - {field_line}")

        lines.append("")
        return lines

    def _format_field(self, field: Dict[str, Any]) -> str:
        """Format a single form field.

        Args:
            field: Field dictionary

        Returns:
            Formatted field string
        """
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
            return f"{fname} ({ftype}): {label}{req}"
        else:
            return f"{fname} ({ftype}){req}"

    async def handle_extract_ascii(
        self,
        port: int,
        tab_id: int | None = None,
        width: int = 80,
        max_text: int = 20,
    ) -> Dict[str, Any]:
        """Handle ASCII layout extraction request.

        Args:
            port: Browser WebSocket port
            tab_id: Optional tab ID
            width: ASCII canvas width in characters
            max_text: Max text length per element

        Returns:
            Dict with formatted ASCII layout and raw data
        """
        if not self.browser_service:
            return {
                "success": False,
                "error": "Browser service not available",
                "formatted_text": "ASCII extraction failed: Browser service not available",
            }

        result = await self.browser_service.extract_ascii_layout(
            port=port,
            tab_id=tab_id,
            options={"max_text": max_text},
        )

        if result.get("success"):
            layout = result.get("layout", {})
            formatted = self._format_ascii_layout(layout, width)
            return {
                "success": True,
                "formatted_text": formatted,
                "raw_layout": layout,
            }
        else:
            error = result.get("error", "Unknown error")
            return {
                "success": False,
                "error": error,
                "formatted_text": f"ASCII layout extraction failed: {error}",
            }

    def _format_ascii_layout(self, layout: Dict[str, Any], width: int = 80) -> str:
        """Convert element positions to ASCII box diagram.

        Args:
            layout: Dict with viewport and elements from browser
            width: Output width in characters

        Returns:
            ASCII art representation of page layout
        """
        viewport = layout.get("viewport", {"width": 1200, "height": 800})
        elements = layout.get("elements", [])
        url = layout.get("url", "")
        title = layout.get("title", "")

        if not elements:
            return f"# ASCII Layout: {title}\nURL: {url}\n\n(No visible elements found)"

        # Scale factors
        vp_width = max(viewport.get("width", 1200), 1)
        vp_height = max(viewport.get("height", 800), 1)
        scale_x = (width - 2) / vp_width
        scale_y = ((width // 2) - 2) / vp_height  # ASCII chars are ~2x tall

        # Calculate canvas height
        height = max(int(vp_height * scale_y) + 2, 10)
        height = min(height, 60)  # Cap at 60 rows

        # Create canvas
        canvas = [[" " for _ in range(width)] for _ in range(height)]

        # Sort elements by area (largest first for background)
        sorted_elements = sorted(
            elements, key=lambda e: e.get("width", 0) * e.get("height", 0), reverse=True
        )

        # Draw elements
        for el in sorted_elements:
            x1 = int(el.get("x", 0) * scale_x)
            y1 = int(el.get("y", 0) * scale_y)
            el_width = int(el.get("width", 0) * scale_x)
            el_height = int(el.get("height", 0) * scale_y)

            x2 = min(x1 + el_width, width - 1)
            y2 = min(y1 + el_height, height - 1)

            # Ensure valid box dimensions
            if x2 > x1 + 2 and y2 > y1 + 1 and x1 >= 0 and y1 >= 0:
                self._draw_box(canvas, x1, y1, x2, y2, el.get("type", "?"))

        # Build output
        lines = [
            f"# ASCII Layout: {title}",
            f"URL: {url}",
            f"Viewport: {vp_width}x{vp_height}",
            "",
        ]
        lines.extend("".join(row).rstrip() for row in canvas)

        # Add element legend
        element_types = set(el.get("type", "?") for el in elements)
        lines.append("")
        lines.append("## Elements Found:")
        for el_type in sorted(element_types):
            count = sum(1 for el in elements if el.get("type") == el_type)
            lines.append(f"  [{el_type}]: {count}")

        return "\n".join(lines)

    def _draw_box(
        self,
        canvas: list[list[str]],
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        el_type: str,
    ) -> None:
        """Draw a box on the ASCII canvas.

        Args:
            canvas: 2D character array
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            el_type: Element type label
        """
        height = len(canvas)
        width = len(canvas[0]) if canvas else 0

        # Clamp coordinates
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))

        if x2 <= x1 or y2 <= y1:
            return

        # Draw corners
        canvas[y1][x1] = "┌"
        canvas[y1][x2] = "┐"
        canvas[y2][x1] = "└"
        canvas[y2][x2] = "┘"

        # Draw horizontal lines
        for x in range(x1 + 1, x2):
            if canvas[y1][x] == " ":
                canvas[y1][x] = "─"
            if canvas[y2][x] == " ":
                canvas[y2][x] = "─"

        # Draw vertical lines
        for y in range(y1 + 1, y2):
            if canvas[y][x1] == " ":
                canvas[y][x1] = "│"
            if canvas[y][x2] == " ":
                canvas[y][x2] = "│"

        # Add type label
        label = f"[{el_type}]"
        if len(label) < x2 - x1 - 1 and y1 + 1 < y2:
            for i, c in enumerate(label):
                if x1 + 1 + i < x2:
                    canvas[y1 + 1][x1 + 1 + i] = c
