"""Storage service for persisting console logs."""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from ..models import ConsoleMessage

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Configuration for storage service."""

    base_path: Path = Path.home() / ".browserPYMCP" / "browser"
    max_file_size_mb: int = 50
    retention_days: int = 7
    rotation_check_interval: int = 300  # 5 minutes


class StorageService:
    """Service for storing and retrieving console logs."""

    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize storage service.

        Args:
            config: Optional storage configuration
        """
        self.config = config or StorageConfig()
        self._ensure_base_directory()
        self._rotation_task: Optional[asyncio.Task] = None
        self._file_locks: Dict[int, asyncio.Lock] = {}

    def _ensure_base_directory(self) -> None:
        """Ensure base storage directory exists."""
        self.config.base_path.mkdir(parents=True, exist_ok=True)

    def _get_port_directory(self, port: int) -> Path:
        """Get directory for a specific port.

        Args:
            port: Port number

        Returns:
            Path to port directory
        """
        port_dir = self.config.base_path / str(port)
        port_dir.mkdir(parents=True, exist_ok=True)
        return port_dir

    def _get_log_file_path(self, port: int, archived: bool = False) -> Path:
        """Get path to log file for a port.

        Args:
            port: Port number
            archived: Whether to get archived file path

        Returns:
            Path to log file
        """
        port_dir = self._get_port_directory(port)
        if archived:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return port_dir / f"console_{timestamp}.jsonl"
        return port_dir / "console.jsonl"

    async def _get_file_lock(self, port: int) -> asyncio.Lock:
        """Get or create a lock for a port's file.

        Args:
            port: Port number

        Returns:
            Lock for the port's file
        """
        if port not in self._file_locks:
            self._file_locks[port] = asyncio.Lock()
        return self._file_locks[port]

    async def store_message(self, message: ConsoleMessage) -> None:
        """Store a console message.

        Args:
            message: Console message to store
        """
        lock = await self._get_file_lock(message.port)
        async with lock:
            file_path = self._get_log_file_path(message.port)

            # Check if rotation is needed
            if await self._should_rotate(file_path):
                await self._rotate_log_file(message.port)

            # Append message to file
            async with aiofiles.open(file_path, "a") as f:
                await f.write(message.to_jsonl() + "\n")

    async def store_messages_batch(self, messages: List[ConsoleMessage]) -> None:
        """Store multiple console messages.

        Args:
            messages: List of console messages to store
        """
        # Group messages by port
        messages_by_port: Dict[int, List[ConsoleMessage]] = {}
        for msg in messages:
            if msg.port not in messages_by_port:
                messages_by_port[msg.port] = []
            messages_by_port[msg.port].append(msg)

        # Store messages for each port
        tasks = []
        for port, port_messages in messages_by_port.items():
            tasks.append(self._store_port_messages(port, port_messages))

        await asyncio.gather(*tasks)

    async def _store_port_messages(
        self, port: int, messages: List[ConsoleMessage]
    ) -> None:
        """Store messages for a specific port.

        Args:
            port: Port number
            messages: Messages to store
        """
        lock = await self._get_file_lock(port)
        async with lock:
            file_path = self._get_log_file_path(port)

            # Check if rotation is needed
            if await self._should_rotate(file_path):
                await self._rotate_log_file(port)

            # Append all messages
            async with aiofiles.open(file_path, "a") as f:
                for msg in messages:
                    await f.write(msg.to_jsonl() + "\n")

    async def query_messages(
        self,
        port: int,
        last_n: int = 100,
        level_filter: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ConsoleMessage]:
        """Query stored messages.

        Args:
            port: Port number
            last_n: Number of most recent messages to return
            level_filter: Optional filter by log levels
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of console messages
        """
        lock = await self._get_file_lock(port)
        async with lock:
            file_path = self._get_log_file_path(port)

            if not file_path.exists():
                return []

            messages = []
            async with aiofiles.open(file_path, "r") as f:
                async for line in f:
                    try:
                        msg = ConsoleMessage.from_jsonl(line.strip())

                        # Apply filters
                        if not msg.matches_filter(level_filter):
                            continue

                        if start_time and msg.timestamp < start_time:
                            continue

                        if end_time and msg.timestamp > end_time:
                            continue

                        messages.append(msg)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse log line: {e}")

            # Return last N messages
            return messages[-last_n:] if last_n else messages

    async def _should_rotate(self, file_path: Path) -> bool:
        """Check if log file should be rotated.

        Args:
            file_path: Path to log file

        Returns:
            True if rotation is needed
        """
        if not file_path.exists():
            return False

        size_mb = file_path.stat().st_size / (1024 * 1024)
        return size_mb >= self.config.max_file_size_mb

    async def _rotate_log_file(self, port: int) -> None:
        """Rotate log file for a port.

        Args:
            port: Port number
        """
        current_path = self._get_log_file_path(port)
        if current_path.exists():
            archived_path = self._get_log_file_path(port, archived=True)
            current_path.rename(archived_path)
            logger.info(f"Rotated log file for port {port} to {archived_path.name}")

    async def cleanup_old_files(self) -> None:
        """Clean up files older than retention period."""
        cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)

        for port_dir in self.config.base_path.iterdir():
            if not port_dir.is_dir():
                continue

            for file_path in port_dir.glob("console_*.jsonl"):
                # Parse timestamp from filename
                try:
                    timestamp_str = file_path.stem.replace("console_", "")
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if file_time < cutoff_time:
                        file_path.unlink()
                        logger.info(f"Deleted old log file: {file_path}")
                except (ValueError, OSError) as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")

    async def start_rotation_task(self) -> None:
        """Start background task for file rotation and cleanup."""
        if self._rotation_task and not self._rotation_task.done():
            return

        self._rotation_task = asyncio.create_task(self._rotation_loop())

    async def stop_rotation_task(self) -> None:
        """Stop the rotation background task."""
        if self._rotation_task and not self._rotation_task.done():
            self._rotation_task.cancel()
            try:
                await self._rotation_task
            except asyncio.CancelledError:
                pass

    async def _rotation_loop(self) -> None:
        """Background loop for file rotation and cleanup."""
        while True:
            try:
                await asyncio.sleep(self.config.rotation_check_interval)
                await self.cleanup_old_files()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rotation loop: {e}")

    async def _enumerate_async(self, async_iterable):
        """Async helper to enumerate an async iterable.

        Args:
            async_iterable: Async iterable to enumerate

        Yields:
            Tuple of (index, item)
        """
        i = 0
        async for item in async_iterable:
            yield i, item
            i += 1

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "base_path": str(self.config.base_path),
            "ports": [],
            "total_size_mb": 0,
            "total_messages": 0,
        }

        for port_dir in self.config.base_path.iterdir():
            if not port_dir.is_dir():
                continue

            port_stats = {
                "port": int(port_dir.name),
                "files": [],
                "size_mb": 0,
                "message_count": 0,
            }

            for file_path in port_dir.glob("*.jsonl"):
                size_mb = file_path.stat().st_size / (1024 * 1024)
                port_stats["files"].append(
                    {"name": file_path.name, "size_mb": round(size_mb, 2)}
                )
                port_stats["size_mb"] += size_mb

                # Count messages asynchronously with periodic yielding
                line_count = 0
                async with aiofiles.open(file_path, "r") as f:
                    async for i, _ in self._enumerate_async(f):
                        line_count += 1
                        # Yield control every 1000 lines to prevent blocking
                        if i % 1000 == 0:
                            await asyncio.sleep(0)
                port_stats["message_count"] += line_count

            stats["ports"].append(port_stats)
            stats["total_size_mb"] += port_stats["size_mb"]
            stats["total_messages"] += port_stats["message_count"]

        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats
