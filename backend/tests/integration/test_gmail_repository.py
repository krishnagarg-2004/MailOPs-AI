from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.repositories.gmail_repository import GmailRepository
from backend.tests.integration.test_database import db_session, test_engine


def test_gmail_thread_and_message_upsert_idempotency(db_session: Session):
    """Verify upserting identical Gmail thread and message IDs updates existing records without duplication."""
    user = User(email="upsertuser@enterprise.com", full_name="Upsert User")
    db_session.add(user)
    db_session.commit()

    # 1. First upsert thread
    thread1 = GmailRepository.upsert_thread(
        db_session,
        user_id=user.id,
        gmail_thread_id="thread_id_100",
        snippet="Original snippet",
        history_id=1001,
        last_message_at=datetime.now(timezone.utc),
    )
    assert thread1 is not None

    # 2. Re-upsert same thread with updated snippet
    thread2 = GmailRepository.upsert_thread(
        db_session,
        user_id=user.id,
        gmail_thread_id="thread_id_100",
        snippet="Updated snippet",
        history_id=1002,
        last_message_at=datetime.now(timezone.utc),
    )
    assert thread1.id == thread2.id
    assert thread2.snippet == "Updated snippet"
    assert thread2.history_id == 1002

    # 3. First upsert message
    msg1 = GmailRepository.upsert_message(
        db_session,
        user_id=user.id,
        thread_id=thread1.id,
        gmail_message_id="msg_id_500",
        gmail_thread_id="thread_id_100",
        sender="alice@vendor.com",
        subject="Invoice #1",
        snippet="Original message snippet",
        body_plain="Original body",
        labels=["INBOX", "UNREAD"],
    )
    assert msg1 is not None

    # 4. Re-upsert same message with new labels and updated body
    msg2 = GmailRepository.upsert_message(
        db_session,
        user_id=user.id,
        thread_id=thread1.id,
        gmail_message_id="msg_id_500",
        gmail_thread_id="thread_id_100",
        sender="alice@vendor.com",
        subject="Invoice #1",
        snippet="Updated message snippet",
        body_plain="Updated body",
        labels=["INBOX", "IMPORTANT"],
    )
    assert msg1.id == msg2.id
    assert msg2.snippet == "Updated message snippet"
    assert "IMPORTANT" in msg2.labels


def test_attachment_persistence_and_sync_state(db_session: Session):
    """Verify Attachment metadata persistence and GmailSyncState status updates."""
    user = User(email="attuser@enterprise.com", full_name="Attachment User")
    db_session.add(user)
    db_session.commit()

    thread = GmailRepository.upsert_thread(db_session, user.id, "thread_att_1")
    msg = GmailRepository.upsert_message(
        db_session,
        user.id,
        thread.id,
        "msg_att_1",
        "thread_att_1",
        has_attachments=True,
    )

    attachment = GmailRepository.create_or_update_attachment(
        db_session,
        user_id=user.id,
        message_id=msg.id,
        filename="contract.pdf",
        mime_type="application/pdf",
        size_bytes=2048,
        gmail_attachment_id="att_id_999",
        storage_path="storage/attachments/test/contract.dat",
        is_downloaded=True,
    )

    assert attachment.id is not None
    assert attachment.filename == "contract.pdf"
    assert attachment.is_downloaded is True

    # Test GmailSyncState updates
    state = GmailRepository.update_sync_state(
        db_session,
        user.id,
        sync_status="COMPLETED",
        last_history_id=9999,
        synced_message_count=10,
    )

    assert state.sync_status == "COMPLETED"
    assert state.last_history_id == 9999
    assert state.synced_message_count == 10
    assert state.last_synced_at is not None
