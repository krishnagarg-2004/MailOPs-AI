"""
Calendar & Scheduling API Router for MailOps AI.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.calendar_service import CalendarSyncService

router = APIRouter(prefix="/calendar", tags=["Calendar & Scheduling"])


class ScheduleActionRequest(BaseModel):
    action_id: uuid.UUID = Field(description="ID of the extracted action item to schedule")
    calendar_title: str | None = Field(default=None, description="Optional custom calendar event title")


class ScheduleActionResponse(BaseModel):
    status: str
    event_id: str
    action_id: str
    title: str
    start_time: str
    end_time: str
    calendar_url: str
    message: str


@router.post("/schedule", response_model=ScheduleActionResponse)
async def schedule_action(
    req: ScheduleActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Schedules an action item deadline into Google Calendar."""
    try:
        res = CalendarSyncService.schedule_action_item(
            db=db,
            user=current_user,
            action_id=req.action_id,
            calendar_title=req.calendar_title,
        )
        return ScheduleActionResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calendar scheduling failed: {exc}",
        )
