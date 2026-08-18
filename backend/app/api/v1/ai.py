import uuid
from typing import Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.api.v1.auth import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.ai_repository import AIRepository
from backend.app.schemas.ai import (
    AIAnalysisRead,
    ActionStatusEnum,
    ActionStatusUpdate,
    ExtractedActionRead,
    PriorityEnum,
)
from backend.app.services.ai_extraction_service import AIExtractionService

router = APIRouter(prefix="/ai", tags=["AI Engine"])


@router.post("/analyze/message/{message_id}", response_model=AIAnalysisRead)
async def analyze_email_message(
    message_id: uuid.UUID,
    force: bool = Query(default=False, description="Force re-analysis even if completed analysis exists"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger AI extraction analysis for a single synced email message."""
    service = AIExtractionService()
    try:
        analysis = await service.analyze_message(
            db=db,
            user_id=current_user.id,
            message_id=message_id,
            force_reanalyze=force,
        )
        return analysis
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Analysis failed: {exc}",
        )


@router.post("/analyze/thread/{thread_id}", response_model=list[AIAnalysisRead])
async def analyze_email_thread(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger AI extraction analysis across all messages in an email thread."""
    service = AIExtractionService()
    try:
        analyses = await service.analyze_thread(
            db=db,
            user_id=current_user.id,
            thread_id=thread_id,
        )
        return analyses
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Thread Analysis failed: {exc}",
        )


@router.get("/analysis/message/{message_id}", response_model=AIAnalysisRead)
async def get_message_analysis(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve existing AI analysis for a message."""
    analysis = AIRepository.get_latest_analysis_by_message(
        db=db,
        user_id=current_user.id,
        email_message_id=message_id,
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI Analysis found for message {message_id}",
        )
    return analysis


@router.get("/actions", response_model=list[ExtractedActionRead])
async def get_user_actions(
    status_filter: ActionStatusEnum | None = Query(default=None, alias="status"),
    priority_filter: PriorityEnum | None = Query(default=None, alias="priority"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all extracted action items for the current user."""
    status_val = status_filter.value if status_filter else None
    priority_val = priority_filter.value if priority_filter else None

    actions = AIRepository.get_actions_for_user(
        db=db,
        user_id=current_user.id,
        status_filter=status_val,
        priority_filter=priority_val,
    )
    return actions


@router.patch("/actions/{action_id}", response_model=ExtractedActionRead)
async def update_action_status(
    action_id: uuid.UUID,
    body: ActionStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Human-in-the-Loop endpoint to confirm, edit, or dismiss an action item."""
    updated = AIRepository.update_action_status(
        db=db,
        user_id=current_user.id,
        action_id=action_id,
        new_status=body.status.value,
        assignee=body.assignee,
        due_date=body.due_date,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item {action_id} not found",
        )
    return updated
