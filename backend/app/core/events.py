"""
Real-time In-Memory Event Streaming Bus for MailOps AI.
Provides async Server-Sent Events (SSE) broadcasting per user for:
- Gmail synchronization progress
- AI analysis completion
- Document OCR status
- New action items and alerts
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import AsyncGenerator
import uuid

logger = logging.getLogger(__name__)


class EventBus:
    """
    Per-user async Event Bus supporting Server-Sent Events (SSE).
    Each authenticated client connection subscribes to an asyncio.Queue.
    Provides cross-thread and cross-event-loop publishing safety.
    """

    def __init__(self):
        # Maps user_id -> set of active asyncio.Queue instances
        self._subscribers: dict[uuid.UUID, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
        self._main_loop: asyncio.AbstractEventLoop | None = None

    async def subscribe(self, user_id: uuid.UUID) -> asyncio.Queue:
        """Register a new queue listener for the given user."""
        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            if user_id not in self._subscribers:
                self._subscribers[user_id] = set()
            self._subscribers[user_id].add(queue)
            logger.debug(f"User {user_id} subscribed to EventBus (active listeners: {len(self._subscribers[user_id])})")
        return queue

    async def unsubscribe(self, user_id: uuid.UUID, queue: asyncio.Queue):
        """Remove a listener queue when client disconnects."""
        async with self._lock:
            if user_id in self._subscribers:
                self._subscribers[user_id].discard(queue)
                if not self._subscribers[user_id]:
                    del self._subscribers[user_id]
            logger.debug(f"User {user_id} unsubscribed from EventBus")

    async def publish(self, user_id: uuid.UUID, event_type: str, data: dict):
        """Broadcast an event payload to all active connections for a given user.
        
        Ensures thread-safety by routing through loop.call_soon_threadsafe
        when published from a worker thread or a different event loop.
        """
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            try:
                current_loop = asyncio.get_running_loop()
            except RuntimeError:
                current_loop = None

            if self._main_loop is None and current_loop is not None:
                self._main_loop = current_loop

            listeners = list(self._subscribers.get(user_id, set()))
            for queue in listeners:
                try:
                    if (
                        self._main_loop
                        and current_loop is not self._main_loop
                        and self._main_loop.is_running()
                    ):
                        self._main_loop.call_soon_threadsafe(queue.put_nowait, payload)
                    else:
                        queue.put_nowait(payload)
                except Exception as ex:
                    logger.debug(f"EventBus queue put failed: {ex}")
        except Exception as e:
            logger.debug(f"EventBus publish skipped: {e}")

    def publish_threadsafe(self, user_id: uuid.UUID, event_type: str, data: dict):
        """Thread-safe synchronous broadcast using loop.call_soon_threadsafe."""
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            listeners = list(self._subscribers.get(user_id, set()))
            for queue in listeners:
                try:
                    if self._main_loop and self._main_loop.is_running():
                        self._main_loop.call_soon_threadsafe(queue.put_nowait, payload)
                    else:
                        queue.put_nowait(payload)
                except Exception as ex:
                    logger.debug(f"EventBus publish_threadsafe queue put failed: {ex}")
        except Exception as e:
            logger.debug(f"EventBus publish_threadsafe skipped: {e}")

    async def broadcast_system(self, event_type: str, data: dict):
        """Broadcast to all connected users."""
        async with self._lock:
            all_users = list(self._subscribers.keys())
        for u_id in all_users:
            await self.publish(u_id, event_type, data)


# Global Singleton Event Bus
event_bus = EventBus()


async def event_generator(user_id: uuid.UUID, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """
    Asynchronous generator yielding SSE formatted text frames:
    data: {json}\n\n
    Includes periodic keep-alive pings to prevent proxy/firewall timeouts.
    """
    try:
        # Initial handshake event
        yield f"event: connected\ndata: {json.dumps({'message': 'Connected to MailOps Event Stream'})}\n\n"

        while True:
            try:
                # Wait for next event or send ping every 15 seconds
                event_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                event_type = event_data.get("event", "message")
                content = json.dumps(event_data.get("data", {}))
                yield f"event: {event_type}\ndata: {content}\n\n"
            except asyncio.TimeoutError:
                # SSE keep-alive ping
                yield ": ping\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        await event_bus.unsubscribe(user_id, queue)
