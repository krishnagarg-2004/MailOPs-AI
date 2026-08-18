import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.api.v1.auth import get_current_user
from backend.app.db.session import get_db
from backend.app.models.reply_draft import ReplyDraft
from backend.app.models.user import User
from backend.app.schemas.reply_draft import (
    ReplyDraftCreateRequest,
    ReplyDraftRead,
    ReplyDraftUpdateRequest,
)
from backend.app.services.reply_draft_service import ReplyDraftService

router = APIRouter(prefix="/reply-drafts", tags=["Human-in-the-Loop Reply Drafting"])


@router.post("/generate", response_model=ReplyDraftRead, status_code=status.HTTP_201_CREATED)
async def generate_reply_draft(
    payload: ReplyDraftCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate context-aware AI email reply draft and persist locally in PostgreSQL.
    STRICT NO-AUTOMATIC-SENDING GUARANTEE: Does NOT send or sync to Gmail without explicit user action.
    """
    try:
        draft = await ReplyDraftService.generate_draft(
            db=db,
            user_id=current_user.id,
            message_id=payload.email_message_id,
            tone=payload.tone.value,
            intent=payload.intent,
        )
        return draft
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reply draft generation failed: {exc}",
        )


@router.get("/message/{message_id}", response_model=list[ReplyDraftRead])
async def list_message_reply_drafts(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch all reply drafts for a specific email message scoped to current user."""
    return (
        db.query(ReplyDraft)
        .filter(
            ReplyDraft.email_message_id == message_id,
            ReplyDraft.user_id == current_user.id,
        )
        .all()
    )


@router.get("/{draft_id}", response_model=ReplyDraftRead)
async def get_reply_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch a single reply draft strictly scoped to current user."""
    draft = db.query(ReplyDraft).filter(ReplyDraft.id == draft_id, ReplyDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply draft not found.")
    return draft


@router.put("/{draft_id}", response_model=ReplyDraftRead)
async def update_reply_draft(
    draft_id: uuid.UUID,
    payload: ReplyDraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save Human-in-the-Loop user manual edits (subject, body text, tone, status)."""
    try:
        draft = ReplyDraftService.update_draft(
            db=db,
            user_id=current_user.id,
            draft_id=draft_id,
            subject=payload.subject,
            body_text=payload.body_text,
            tone=payload.tone.value if payload.tone else None,
            intent=payload.intent,
            status=payload.status.value if payload.status else None,
        )
        return draft
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))


@router.post("/{draft_id}/sync-gmail", response_model=ReplyDraftRead)
async def sync_gmail_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Push draft to user's Gmail mailbox as a Gmail Draft.
    Requires explicit user action and verified gmail.compose OAuth scope.
    """
    try:
        draft = await ReplyDraftService.sync_gmail_draft(db, current_user.id, draft_id)
        return draft
    except PermissionError as perm_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_err))
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/{draft_id}/send", response_model=ReplyDraftRead)
async def send_reply_email(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send reply email directly via Gmail REST API.
    Requires explicit separate user action and verified gmail.compose OAuth scope.
    """
    try:
        draft = await ReplyDraftService.send_reply_email(db, current_user.id, draft_id)
        return draft
    except PermissionError as perm_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_err))
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/{draft_id}", status_code=status.HTTP_200_OK)
async def discard_reply_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Discard reply draft setting status to DISCARDED."""
    draft = db.query(ReplyDraft).filter(ReplyDraft.id == draft_id, ReplyDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply draft not found.")
    draft.status = "DISCARDED"
    db.add(draft)
    db.commit()
    return {"status": "discarded", "draft_id": str(draft_id)}
