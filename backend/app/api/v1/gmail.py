import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.gmail_sync_state import GmailSyncState
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.app.repositories.gmail_repository import GmailRepository
from backend.app.schemas.gmail import (
    EmailMessageResponse,
    EmailThreadResponse,
    GmailSyncStateResponse,
    SyncTriggerResponse,
)
from backend.app.services.gmail_sync_service import GmailSyncService

router = APIRouter(prefix="/gmail", tags=["gmail"])


def _run_async_sync(user_id: uuid.UUID):
    """Background task runner executing sync in a new database session."""
    import asyncio
    from backend.app.db.session import SessionLocal

    async def _async_worker():
        db = SessionLocal()
        try:
            user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
            if user:
                sync_service = GmailSyncService()
                await sync_service.execute_sync(db, user)
        finally:
            db.close()

    asyncio.run(_async_worker())


@router.get("/status", response_model=dict)
def get_gmail_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve current user's Gmail OAuth connection status and synchronization state."""
    oauth_acc = db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.provider == "google",
        )
    ).scalar_one_or_none()

    sync_state = GmailRepository.get_or_create_sync_state(db, current_user.id)

    return {
        "connected": bool(oauth_acc and oauth_acc.encrypted_access_token),
        "email": oauth_acc.email if oauth_acc else current_user.email,
        "sync_state": GmailSyncStateResponse.model_validate(sync_state),
    }


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED, response_model=SyncTriggerResponse)
def trigger_gmail_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger background synchronization of user's Gmail mailbox."""
    oauth_acc = db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.provider == "google",
        )
    ).scalar_one_or_none()

    if not oauth_acc or not oauth_acc.encrypted_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No connected Google OAuth account found. Please login with Google first.",
        )

    # Update sync state to SYNCING
    GmailRepository.update_sync_state(db, current_user.id, sync_status="SYNCING")

    # Queue background sync task
    background_tasks.add_task(_run_async_sync, current_user.id)

    return SyncTriggerResponse(
        status="ACCEPTED",
        message="Gmail synchronization started in background.",
    )


@router.get("/threads", response_model=list[EmailThreadResponse])
def list_email_threads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List paginated email threads belonging to current user."""
    offset = (page - 1) * limit
    stmt = (
        select(EmailThread)
        .where(EmailThread.user_id == current_user.id)
        .options(selectinload(EmailThread.messages).selectinload(EmailMessage.attachments))
        .order_by(EmailThread.last_message_at.desc().nulls_last())
        .offset(offset)
        .limit(limit)
    )
    threads = db.execute(stmt).scalars().all()
    return threads


@router.get("/threads/{thread_id}", response_model=EmailThreadResponse)
def get_email_thread_detail(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single email thread detail with child messages for current user."""
    stmt = (
        select(EmailThread)
        .where(EmailThread.id == thread_id, EmailThread.user_id == current_user.id)
        .options(selectinload(EmailThread.messages).selectinload(EmailMessage.attachments))
    )
    thread = db.execute(stmt).scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found.")
    return thread


@router.get("/messages/{message_id}", response_model=EmailMessageResponse)
def get_email_message_detail(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single email message detail for current user."""
    stmt = (
        select(EmailMessage)
        .where(EmailMessage.id == message_id, EmailMessage.user_id == current_user.id)
        .options(selectinload(EmailMessage.attachments))
    )
    message = db.execute(stmt).scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    return message


@router.delete("/disconnect", status_code=status.HTTP_200_OK)
def disconnect_gmail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Gmail account and remove local synchronization data for current user."""
    oauth_acc = db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.provider == "google",
        )
    ).scalar_one_or_none()

    if oauth_acc:
        oauth_acc.encrypted_access_token = None
        db.add(oauth_acc)

    # Delete threads (cascades to messages and attachments)
    db.execute(select(EmailThread).where(EmailThread.user_id == current_user.id))
    
    GmailRepository.update_sync_state(
        db,
        current_user.id,
        sync_status="IDLE",
        last_history_id=None,
        synced_message_count=0,
    )
    db.commit()

    return {"status": "disconnected", "message": "Gmail account disconnected successfully."}
