"""Async request/response service for WebSocket communication with timeouts."""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AsyncRequestResponseService:
    """Generic async request/response pattern with UUID tracking and timeouts.

    This service manages async request/response communication over WebSockets:
    1. Generate unique request ID
    2. Create asyncio Future to wait for response
    3. Track pending requests with timestamps
    4. Send WebSocket message with request ID
    5. Wait for response with timeout
    6. Clean up completed/expired requests

    Cleanup Strategy:
    - Immediate cleanup on success/failure (finally block)
    - Background cleanup task runs every 30 seconds
    - Removes requests older than 120 seconds
    - Cancels futures for expired requests
    """

    def __init__(
        self, cleanup_interval: float = 30.0, request_timeout: float = 120.0
    ):
        """Initialize async request/response service.

        Args:
            cleanup_interval: Seconds between cleanup task runs (default: 30s)
            request_timeout: Max age for pending requests in seconds (default: 120s)
        """
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = cleanup_interval
        self._request_timeout = request_timeout

    async def send_request(
        self,
        websocket: Any,  # WebSocket type varies by implementation
        message_type: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0,
        tab_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send request and wait for response with timeout.

        Args:
            websocket: WebSocket connection to send on
            message_type: Type of message (e.g., 'extract_content', 'capture_screenshot')
            payload: Optional additional message payload
            timeout: Timeout in seconds for waiting for response
            tab_id: Optional tab ID to target specific browser tab

        Returns:
            Response data dict or None on timeout/error

        Raises:
            Exception: If WebSocket send fails
        """
        request_id = str(uuid.uuid4())
        response_future = asyncio.get_event_loop().create_future()

        # Track pending request with creation timestamp
        self._pending_requests[request_id] = {
            "future": response_future,
            "created_at": datetime.now(),
            "type": message_type,
        }

        # Build message with request ID
        message: Dict[str, Any] = {
            "type": message_type,
            "requestId": request_id,
            "timestamp": datetime.now().isoformat(),
        }

        # Merge in additional payload
        if payload:
            message.update(payload)

        # Add tab ID if specified
        if tab_id is not None:
            message["tabId"] = tab_id

        try:
            # Send WebSocket message
            await websocket.send(json.dumps(message))
            logger.debug(f"Sent {message_type} request {request_id}")

            # Wait for response with timeout
            try:
                result: Any = await asyncio.wait_for(response_future, timeout=timeout)
                logger.debug(f"Received response for request {request_id}")
                return result  # type: ignore[return-value]
            except asyncio.TimeoutError:
                logger.warning(
                    f"Request {request_id} ({message_type}) timed out after {timeout}s"
                )
                return None

        except Exception as e:
            logger.error(f"Request {request_id} ({message_type}) failed: {e}")
            raise
        finally:
            # Clean up pending request (immediate cleanup)
            self._pending_requests.pop(request_id, None)

    async def handle_response(
        self, request_id: str, response_data: Dict[str, Any]
    ) -> bool:
        """Complete pending request with response data.

        Args:
            request_id: UUID of the pending request
            response_data: Response data to set as future result

        Returns:
            True if request was found and completed, False otherwise
        """
        pending = self._pending_requests.get(request_id)

        if pending:
            future = pending["future"]
            if not future.done():
                future.set_result(response_data)
                logger.debug(
                    f"Completed request {request_id} (type: {pending['type']})"
                )
                return True
            else:
                logger.warning(f"Request {request_id} future already done")
                return False
        else:
            logger.warning(f"Received response for unknown request: {request_id}")
            return False

    async def start_cleanup_task(self) -> None:
        """Start background task to cleanup expired requests.

        Only starts if cleanup task is not already running.
        Runs cleanup every _cleanup_interval seconds.
        """
        if self._cleanup_task and not self._cleanup_task.done():
            logger.debug("Cleanup task already running")
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            f"Started request cleanup task (interval: {self._cleanup_interval}s, "
            f"timeout: {self._request_timeout}s)"
        )

    async def _cleanup_loop(self) -> None:
        """Background loop to periodically clean up expired requests."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self.cleanup_expired_requests()
            except asyncio.CancelledError:
                # Final cleanup before cancellation
                await self.cleanup_expired_requests()
                logger.info("Cleanup task cancelled, final cleanup complete")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def cleanup_expired_requests(self) -> None:
        """Remove requests older than _request_timeout seconds.

        Removes:
        - Completed futures that weren't cleaned up immediately
        - Expired requests (older than _request_timeout)

        Cancels futures for expired requests.
        """
        now = datetime.now()
        to_remove = []

        for request_id, request_data in self._pending_requests.items():
            future = request_data["future"]
            created_at = request_data["created_at"]
            age = (now - created_at).total_seconds()

            # Remove if completed
            if future.done():
                to_remove.append(request_id)
                logger.debug(f"Cleaning up completed request {request_id}")

            # Remove if expired (and cancel future)
            elif age > self._request_timeout:
                to_remove.append(request_id)
                if not future.done():
                    future.cancel()
                logger.warning(
                    f"Cleaning up expired request {request_id} "
                    f"(type: {request_data['type']}, age: {age:.1f}s)"
                )

        # Remove stale requests
        for request_id in to_remove:
            self._pending_requests.pop(request_id, None)

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} expired/completed requests")

    async def shutdown(self) -> None:
        """Stop cleanup task and cancel all pending requests.

        Cancels:
        - Background cleanup task
        - All pending request futures
        """
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Cleanup task cancelled")

        # Cancel all pending futures
        for request_id, request_data in list(self._pending_requests.items()):
            future = request_data["future"]
            if not future.done():
                future.cancel()
                logger.debug(f"Cancelled pending request {request_id}")

        # Clear pending requests
        self._pending_requests.clear()
        logger.info("AsyncRequestResponseService shutdown complete")

    def get_pending_count(self) -> int:
        """Get count of currently pending requests.

        Returns:
            Number of pending requests
        """
        return len(self._pending_requests)

    def get_pending_requests_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about pending requests.

        Returns:
            Dict mapping request_id to {type, age_seconds}
        """
        now = datetime.now()
        info = {}

        for request_id, request_data in self._pending_requests.items():
            age = (now - request_data["created_at"]).total_seconds()
            info[request_id] = {
                "type": request_data["type"],
                "age_seconds": age,
                "done": request_data["future"].done(),
            }

        return info
