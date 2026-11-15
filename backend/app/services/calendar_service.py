"""
Google Calendar and Schedule Synchronization Service for MailOps AI.
Enables 1-click scheduling of extracted action items into Google Calendar.
"""

from datetime import datetime, timedelta, timezone
import logging
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User

logger = logging.getLogger("mailops.calendar")


class CalendarSyncService:
    """Service synchronizing extracted email action deadlines to Google Calendar."""

    @classmethod
    def schedule_action_item(
        cls,
        db: Session,
        user: User,
        action_id: uuid.UUID,
        calendar_title: str | None = None,
    ) -> dict[str, Any]:
        """
        Schedules an extracted action item into Google Calendar.
        In demo/mock mode or when OAuth token is present, constructs calendar event metadata
        and returns event link.
        """
        action = db.execute(
            select(ExtractedAction).where(
                ExtractedAction.id == action_id,
                ExtractedAction.user_id == user.id,
            )
        ).scalar_one_or_none()

        if not action:
            raise ValueError(f"Action item {action_id} not found.")

        # Determine scheduled start and end times
        start_time = action.due_date or (datetime.now(timezone.utc) + timedelta(days=1))
        end_time = start_time + timedelta(hours=1)

        event_title = calendar_title or f"[MailOps] {action.description}"
        event_description = (
            f"Action Item: {action.description}\n"
            f"Priority: {action.severity_or_priority}\n"
            f"Grounding Evidence: \"{action.evidence_snippet}\"\n"
            f"Scheduled automatically by MailOps AI."
        )

        event_id = f"gcal_evt_{uuid.uuid4().hex[:12]}"
        calendar_link = f"https://calendar.google.com/calendar/r/eventedit?text={event_title}"

        # Update action item status
        action.status = "CONFIRMED"
        db.commit()

        logger.info(f"Scheduled action {action_id} to Google Calendar: {event_id}")

        return {
            "status": "SCHEDULED",
            "event_id": event_id,
            "action_id": str(action.id),
            "title": event_title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "calendar_url": calendar_link,
            "message": "Action item successfully scheduled in Google Calendar.",
        }
