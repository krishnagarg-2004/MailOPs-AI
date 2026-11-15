"""
Real-time Server-Sent Events (SSE) router.
Streams live synchronization progress, OCR events, and AI analysis alerts.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from backend.app.api.deps import get_current_user
from backend.app.core.events import event_bus, event_generator
from backend.app.models.user import User

router = APIRouter(prefix="/events", tags=["Real-time Events"])


@router.get("/stream")
async def stream_events(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Subscribes the authenticated browser client to live server-sent events (SSE).
    Streams sync progress, OCR status updates, and notifications.
    """
    queue = await event_bus.subscribe(current_user.id)

    return StreamingResponse(
        event_generator(current_user.id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disables proxy buffering in Nginx
        },
    )
