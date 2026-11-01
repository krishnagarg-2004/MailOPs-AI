from datetime import datetime, timezone
import json
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from backend.app.models.attachment import Attachment
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.gmail_sync_state import GmailSyncState


class GmailRepository:
    """Repository encapsulating database operations for Gmail threads, messages, attachments, and sync states."""

    @staticmethod
    def get_or_create_sync_state(db: Session, user_id: uuid.UUID) -> GmailSyncState:
        """Fetch existing GmailSyncState for user or initialize a new record."""
        state = db.execute(
            select(GmailSyncState).where(GmailSyncState.user_id == user_id)
        ).scalar_one_or_none()

        if not state:
            state = GmailSyncState(
                user_id=user_id,
                sync_status="IDLE",
                synced_message_count=0,
            )
            db.add(state)
            db.commit()
            db.refresh(state)

        return state

    @staticmethod
    def update_sync_state(
        db: Session,
        user_id: uuid.UUID,
        sync_status: str | None = None,
        last_history_id: int | None = None,
        synced_message_count: int | None = None,
        error_message: str | None = None,
    ) -> GmailSyncState:
        """Update fields on user's GmailSyncState record."""
        state = GmailRepository.get_or_create_sync_state(db, user_id)

        if sync_status is not None:
            state.sync_status = sync_status
        if last_history_id is not None:
            state.last_history_id = last_history_id
        if synced_message_count is not None:
            state.synced_message_count = synced_message_count
        if sync_status == "COMPLETED":
            state.last_synced_at = datetime.now(timezone.utc)
            # Only auto-clear error_message on a clean COMPLETED (no partial failure note).
            # If an explicit error_message is provided alongside COMPLETED, preserve it
            # so partial-success states are visible in the DB.
            if error_message is None:
                state.error_message = None
        if error_message is not None:
            state.error_message = error_message

        db.add(state)
        db.commit()
        db.refresh(state)
        return state

    @staticmethod
    def upsert_thread(
        db: Session,
        user_id: uuid.UUID,
        gmail_thread_id: str,
        snippet: str | None = None,
        history_id: int | None = None,
        last_message_at: datetime | None = None,
    ) -> EmailThread:
        """Idempotently insert or update EmailThread record."""
        stmt = pg_insert(EmailThread).values(
            id=uuid.uuid4(),
            user_id=user_id,
            gmail_thread_id=gmail_thread_id,
            snippet=snippet,
            history_id=history_id,
            last_message_at=last_message_at,
        )

        update_dict: dict[str, Any] = {
            "snippet": stmt.excluded.snippet,
            "updated_at": datetime.now(timezone.utc),
        }
        if history_id is not None:
            update_dict["history_id"] = stmt.excluded.history_id
        if last_message_at is not None:
            update_dict["last_message_at"] = stmt.excluded.last_message_at

        stmt = stmt.on_conflict_do_update(
            constraint="uq_user_gmail_thread",
            set_=update_dict,
        )

        db.execute(stmt)
        db.commit()

        # Retrieve and return updated thread object
        thread = db.execute(
            select(EmailThread).where(
                EmailThread.user_id == user_id,
                EmailThread.gmail_thread_id == gmail_thread_id,
            )
        ).scalar_one()
        return thread

    @staticmethod
    def upsert_message(
        db: Session,
        user_id: uuid.UUID,
        thread_id: uuid.UUID,
        gmail_message_id: str,
        gmail_thread_id: str,
        sender: str | None = None,
        recipients: str | None = None,
        subject: str | None = None,
        snippet: str | None = None,
        body_plain: str | None = None,
        body_html: str | None = None,
        sent_at: datetime | None = None,
        received_at: datetime | None = None,
        labels: list[str] | None = None,
        has_attachments: bool = False,
        history_id: int | None = None,
    ) -> EmailMessage:
        """Idempotently insert or update EmailMessage record."""
        labels_json = json.dumps(labels or [])

        stmt = pg_insert(EmailMessage).values(
            id=uuid.uuid4(),
            user_id=user_id,
            thread_id=thread_id,
            gmail_message_id=gmail_message_id,
            gmail_thread_id=gmail_thread_id,
            history_id=history_id,
            sender=sender,
            recipients=recipients,
            subject=subject,
            snippet=snippet,
            body_plain=body_plain,
            body_html=body_html,
            sent_at=sent_at,
            received_at=received_at,
            labels=labels_json,
            has_attachments=has_attachments,
        )

        update_dict: dict[str, Any] = {
            "snippet": stmt.excluded.snippet,
            "body_plain": stmt.excluded.body_plain,
            "body_html": stmt.excluded.body_html,
            "labels": stmt.excluded.labels,
            "has_attachments": stmt.excluded.has_attachments,
            "updated_at": datetime.now(timezone.utc),
        }
        if history_id is not None:
            update_dict["history_id"] = stmt.excluded.history_id
        if sender is not None:
            update_dict["sender"] = stmt.excluded.sender
        if subject is not None:
            update_dict["subject"] = stmt.excluded.subject

        stmt = stmt.on_conflict_do_update(
            constraint="uq_user_gmail_message",
            set_=update_dict,
        )

        db.execute(stmt)
        db.commit()

        message = db.execute(
            select(EmailMessage).where(
                EmailMessage.user_id == user_id,
                EmailMessage.gmail_message_id == gmail_message_id,
            )
        ).scalar_one()
        return message

    @staticmethod
    def create_or_update_attachment(
        db: Session,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
        filename: str,
        mime_type: str | None = None,
        size_bytes: int = 0,
        gmail_attachment_id: str | None = None,
        storage_path: str | None = None,
        is_downloaded: bool = False,
    ) -> Attachment:
        """Create or update Attachment record for a message."""
        existing = db.execute(
            select(Attachment).where(
                Attachment.user_id == user_id,
                Attachment.message_id == message_id,
                Attachment.filename == filename,
            )
        ).scalar_one_or_none()

        if existing:
            if storage_path:
                existing.storage_path = storage_path
                existing.is_downloaded = is_downloaded
            if gmail_attachment_id:
                existing.gmail_attachment_id = gmail_attachment_id
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        attachment = Attachment(
            user_id=user_id,
            message_id=message_id,
            gmail_attachment_id=gmail_attachment_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            is_downloaded=is_downloaded,
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment

    @staticmethod
    def update_message_labels(
        db: Session,
        user_id: uuid.UUID,
        gmail_message_id: str,
        labels: list[str],
    ) -> EmailMessage | None:
        """Update Gmail labels on an existing email message."""
        message = db.execute(
            select(EmailMessage).where(
                EmailMessage.user_id == user_id,
                EmailMessage.gmail_message_id == gmail_message_id,
            )
        ).scalar_one_or_none()

        if message:
            message.labels = json.dumps(labels)
            db.add(message)
            db.commit()
            db.refresh(message)

        return message

    @staticmethod
    def delete_message_by_gmail_id(db: Session, user_id: uuid.UUID, gmail_message_id: str) -> bool:
        """Delete an email message by gmail_message_id for a user."""
        message = db.execute(
            select(EmailMessage).where(
                EmailMessage.user_id == user_id,
                EmailMessage.gmail_message_id == gmail_message_id,
            )
        ).scalar_one_or_none()

        if message:
            db.delete(message)
            db.commit()
            return True
        return False
