from datetime import datetime, timezone
import logging
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
from backend.app.core.events import event_bus
from backend.app.services.gmail_sync_service import GmailSyncService

router = APIRouter(prefix="/gmail", tags=["gmail"])

logger = logging.getLogger(__name__)


async def _run_async_sync(user_id: uuid.UUID):
    """Background task runner executing sync in a new database session on the main asyncio loop."""
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user:
            sync_service = GmailSyncService()
            await sync_service.execute_sync(db, user)
        else:
            logger.warning(
                "Background sync: user_id=%s not found. Marking sync FAILED.",
                user_id,
            )
            GmailRepository.update_sync_state(
                db,
                user_id,
                sync_status="FAILED",
                error_message="User account not found during background sync.",
            )
            await event_bus.publish(
                user_id,
                "sync_completed",
                {
                    "status": "FAILED",
                    "error": "User account not found during background sync.",
                },
            )
    except Exception as exc:
        logger.error(
            "Background sync unhandled exception: user_id=%s error=%s",
            user_id,
            type(exc).__name__,
        )
        msg_count = 0
        try:
            from backend.app.models.email_message import EmailMessage
            msg_count = db.query(EmailMessage).filter(EmailMessage.user_id == user_id).count()
            if msg_count > 0:
                GmailRepository.update_sync_state(
                    db,
                    user_id,
                    sync_status="COMPLETED",
                    synced_message_count=msg_count,
                    error_message=f"Synced {msg_count} messages (interrupted: {type(exc).__name__})",
                )
            else:
                GmailRepository.update_sync_state(
                    db,
                    user_id,
                    sync_status="FAILED",
                    error_message=f"Background sync terminated unexpectedly: {type(exc).__name__}",
                )
        except Exception as db_exc:
            logger.critical(
                "Could not reset SYNCING state to FAILED after background sync failure: %s",
                db_exc,
            )
        try:
            await event_bus.publish(
                user_id,
                "sync_completed",
                {
                    "status": "COMPLETED" if msg_count > 0 else "FAILED",
                    "synced_count": msg_count,
                    "error": str(exc),
                },
            )
        except Exception as pub_exc:
            logger.critical("Could not publish sync_completed event on error: %s", pub_exc)
    finally:
        db.close()


async def _run_async_sync_older(user_id: uuid.UUID, count: int = 50):
    """Background task runner executing older historical emails sync."""
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user:
            sync_service = GmailSyncService()
            await sync_service.sync_older_messages(db, user, count=count)
        else:
            logger.warning(
                "Background older sync: user_id=%s not found. Marking sync FAILED.",
                user_id,
            )
            GmailRepository.update_sync_state(
                db,
                user_id,
                sync_status="FAILED",
                error_message="User account not found during background older sync.",
            )
            await event_bus.publish(
                user_id,
                "sync_completed",
                {
                    "status": "FAILED",
                    "error": "User account not found during background older sync.",
                },
            )
    except Exception as exc:
        logger.error(
            "Background older sync error: user_id=%s error=%s",
            user_id,
            type(exc).__name__,
            exc_info=True,
        )
        msg_count = 0
        try:
            from backend.app.models.email_message import EmailMessage
            msg_count = db.query(EmailMessage).filter(EmailMessage.user_id == user_id).count()
            GmailRepository.update_sync_state(
                db,
                user_id,
                sync_status="COMPLETED" if msg_count > 0 else "FAILED",
                synced_message_count=msg_count,
                error_message=f"Sync interrupted: {str(exc)}",
            )
        except Exception as db_exc:
            logger.critical("Could not reset SYNCING state: %s", db_exc)
        try:
            await event_bus.publish(
                user_id,
                "sync_completed",
                {
                    "status": "COMPLETED" if msg_count > 0 else "FAILED",
                    "synced_count": msg_count,
                    "error": str(exc),
                },
            )
        except Exception as pub_exc:
            logger.critical("Could not publish sync_completed on older error: %s", pub_exc)
    finally:
        db.close()


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

    # FIX-SYNC-3: Prevent concurrent syncs for the same user. A sync already
    # in progress would produce conflicting DB sessions and duplicate work.
    sync_state = GmailRepository.get_or_create_sync_state(db, current_user.id)
    if sync_state.sync_status == "SYNCING":
        now_utc = datetime.now(timezone.utc)
        is_stale = False
        if sync_state.updated_at:
            updated_dt = sync_state.updated_at if sync_state.updated_at.tzinfo else sync_state.updated_at.replace(tzinfo=timezone.utc)
            if (now_utc - updated_dt).total_seconds() > 180:
                is_stale = True

        if not is_stale:
            return SyncTriggerResponse(
                status="IN_PROGRESS",
                message="A Gmail synchronization is already in progress.",
            )
        logger.warning("Auto-clearing stale sync lock (>3m) for user %s", current_user.id)

    # Update sync state to SYNCING (acts as an optimistic lock against second concurrent trigger)
    GmailRepository.update_sync_state(db, current_user.id, sync_status="SYNCING", error_message=None)

    # Queue background sync task
    background_tasks.add_task(_run_async_sync, current_user.id)

    return SyncTriggerResponse(
        status="ACCEPTED",
        message="Gmail synchronization started in background.",
    )


@router.post("/sync-older", status_code=status.HTTP_202_ACCEPTED, response_model=SyncTriggerResponse)
def trigger_gmail_sync_older(
    background_tasks: BackgroundTasks,
    count: int = Query(50, ge=10, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger background synchronization of older historical emails."""
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

    sync_state = GmailRepository.get_or_create_sync_state(db, current_user.id)
    if sync_state.sync_status == "SYNCING":
        now_utc = datetime.now(timezone.utc)
        is_stale = False
        if sync_state.updated_at:
            updated_dt = sync_state.updated_at if sync_state.updated_at.tzinfo else sync_state.updated_at.replace(tzinfo=timezone.utc)
            if (now_utc - updated_dt).total_seconds() > 180:
                is_stale = True

        if not is_stale:
            return SyncTriggerResponse(
                status="IN_PROGRESS",
                message="A Gmail synchronization is already in progress.",
            )
        logger.warning("Auto-clearing stale older sync lock (>3m) for user %s", current_user.id)

    GmailRepository.update_sync_state(db, current_user.id, sync_status="SYNCING", error_message=None)
    background_tasks.add_task(_run_async_sync_older, current_user.id, count)

    return SyncTriggerResponse(
        status="ACCEPTED",
        message=f"Retrieval of up to {count} older emails started in background.",
    )


@router.get("/threads", response_model=list[EmailThreadResponse])
def list_email_threads(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
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
