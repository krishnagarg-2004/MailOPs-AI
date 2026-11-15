"""
Unit tests for Real-time Event Streaming Bus and SSE endpoints.
"""

import asyncio
import uuid
import pytest

from backend.app.core.events import EventBus, event_generator


@pytest.mark.asyncio
async def test_event_bus_subscribe_publish_unsubscribe():
    """Verify EventBus registers subscribers, queues events, and unregisters properly."""
    bus = EventBus()
    user_id = uuid.uuid4()

    queue = await bus.subscribe(user_id)
    assert user_id in bus._subscribers
    assert queue in bus._subscribers[user_id]

    # Publish an event
    test_payload = {"status": "SYNCING", "processed": 5}
    await bus.publish(user_id, "sync_progress", test_payload)

    # Receive item from queue
    event = await queue.get()
    assert event["event"] == "sync_progress"
    assert event["data"] == test_payload
    assert "timestamp" in event

    # Unsubscribe
    await bus.unsubscribe(user_id, queue)
    assert user_id not in bus._subscribers


@pytest.mark.asyncio
async def test_event_generator_sse_formatting():
    """Verify event_generator produces valid Server-Sent Events (SSE) format frames."""
    queue = asyncio.Queue()
    user_id = uuid.uuid4()

    # Put a mock event
    await queue.put({"event": "sync_started", "data": {"status": "SYNCING"}})

    gen = event_generator(user_id, queue)

    # First chunk is the handshake
    handshake = await gen.__anext__()
    assert handshake.startswith("event: connected\ndata:")

    # Second chunk is the queued event
    first_event = await gen.__anext__()
    assert "event: sync_started\n" in first_event
    assert '"status": "SYNCING"' in first_event
    assert first_event.endswith("\n\n")

    # Clean up
    await gen.aclose()
