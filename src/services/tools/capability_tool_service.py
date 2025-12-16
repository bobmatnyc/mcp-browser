"""Capability detection tool service for MCP browser control."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CapabilityToolService:
    """MCP tool handler for capability detection and reporting."""

    def __init__(self, capability_detector=None):
        self.capability_detector = capability_detector

    async def handle_get_capabilities(self) -> Dict[str, Any]:
        """Get browser control capabilities.

        Returns:
            Dict with success status and formatted capability report
        """
        if not self.capability_detector:
            return {
                "success": False,
                "error": "Capability detection not available",
                "formatted_text": "Capability detection not available",
            }

        try:
            report = await self.capability_detector.get_capability_report()
            formatted_text = self._format_capability_report(report)

            return {
                "success": True,
                "report": report,
                "formatted_text": formatted_text,
            }

        except Exception as e:
            logger.exception("Failed to get capabilities")
            return {
                "success": False,
                "error": str(e),
                "formatted_text": f"Capability check failed: {str(e)}",
            }

    def _format_capability_report(self, report: Dict) -> str:
        """Format capability report for human-readable output.

        Args:
            report: Dict containing capability information with keys:
                - summary: Overall summary string
                - capabilities: List of available capability strings
                - methods: Dict of method_name -> {available, description}

        Returns:
            Formatted markdown string
        """
        lines = [
            "# Browser Control Capabilities",
            "",
            f"**Summary:** {report['summary']}",
            "",
            "## Available",
        ]

        for cap in report.get("capabilities", []):
            lines.append(f"- {cap}")

        lines.extend(["", "## Methods", ""])
        for method_name, method_info in report.get("methods", {}).items():
            status = "Available" if method_info["available"] else "Unavailable"
            lines.append(f"**{method_name.title()}**: {status}")
            lines.append(f"  {method_info['description']}")

        return "\n".join(lines)
