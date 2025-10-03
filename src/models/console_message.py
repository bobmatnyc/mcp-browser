"""Console message data model."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ConsoleLevel(Enum):
    """Console log levels."""

    DEBUG = "debug"
    INFO = "info"
    LOG = "log"
    WARN = "warn"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ConsoleMessage:
    """Represents a console message from the browser."""

    timestamp: datetime
    level: ConsoleLevel
    message: str
    port: int
    url: Optional[str] = None
    stack_trace: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    source_file: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_websocket_data(cls, data: Dict[str, Any], port: int) -> "ConsoleMessage":
        """Create a ConsoleMessage from WebSocket data.

        Args:
            data: Raw data from WebSocket
            port: Port number of the connection

        Returns:
            ConsoleMessage instance
        """
        # Parse timestamp
        timestamp = datetime.fromisoformat(
            data.get("timestamp", datetime.now().isoformat())
        )

        # Parse level
        level_str = data.get("level", "log").lower()
        try:
            level = ConsoleLevel(level_str)
        except ValueError:
            level = ConsoleLevel.LOG

        # Extract message
        message = data.get("message", "")
        if isinstance(data.get("args"), list):
            # Join multiple arguments
            message = " ".join(str(arg) for arg in data["args"])

        return cls(
            timestamp=timestamp,
            level=level,
            message=message,
            port=port,
            url=data.get("url"),
            stack_trace=data.get("stackTrace"),
            line_number=data.get("lineNumber"),
            column_number=data.get("columnNumber"),
            source_file=data.get("sourceFile"),
            metadata=data.get("metadata", {}),
        )

    def to_jsonl(self) -> str:
        """Convert to JSONL format for storage.

        Returns:
            JSON string representation
        """
        data = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "port": self.port,
            "url": self.url,
            "stackTrace": self.stack_trace,
            "lineNumber": self.line_number,
            "columnNumber": self.column_number,
            "sourceFile": self.source_file,
            "metadata": self.metadata,
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data)

    @classmethod
    def from_jsonl(cls, line: str) -> "ConsoleMessage":
        """Create a ConsoleMessage from JSONL line.

        Args:
            line: JSONL string

        Returns:
            ConsoleMessage instance
        """
        data = json.loads(line)
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            level=ConsoleLevel(data["level"]),
            message=data["message"],
            port=data["port"],
            url=data.get("url"),
            stack_trace=data.get("stackTrace"),
            line_number=data.get("lineNumber"),
            column_number=data.get("columnNumber"),
            source_file=data.get("sourceFile"),
            metadata=data.get("metadata", {}),
        )

    def matches_filter(self, level_filter: Optional[List[str]] = None) -> bool:
        """Check if message matches filter criteria.

        Args:
            level_filter: Optional list of levels to include

        Returns:
            True if message matches filter
        """
        if level_filter:
            return self.level.value in level_filter
        return True
