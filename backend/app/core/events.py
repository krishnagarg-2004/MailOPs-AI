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
    """

    def __init__(self):
        # Maps user_id -> set of active asyncio.Queue instances
        self._subscribers: dict[uuid.UUID, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, user_id: uuid.UUID) -> asyncio.Queue:
        """Register a new queue listener for the given user."""
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
        """Broadcast an event payload to all active connections for a given user."""
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            listeners = list(self._subscribers.get(user_id, set()))
            for queue in listeners:
                try:
                    queue.put_nowait(payload)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"EventBus publish skipped: {e}")

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
