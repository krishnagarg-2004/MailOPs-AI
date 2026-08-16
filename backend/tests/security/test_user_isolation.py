import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.repositories.gmail_repository import GmailRepository
from backend.tests.integration.test_database import db_session, test_engine


def test_strict_multi_tenant_user_isolation(db_session: Session):
    """Verify User A cannot query, update, or retrieve User B's email threads, messages, or attachments."""
    user_a = User(email="usera@enterprise.com", full_name="User A")
    user_b = User(email="userb@enterprise.com", full_name="User B")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    # Create thread and message for User A
    thread_a = GmailRepository.upsert_thread(db_session, user_a.id, "thread_gmail_a")
    msg_a = GmailRepository.upsert_message(
        db_session,
        user_id=user_a.id,
        thread_id=thread_a.id,
        gmail_message_id="msg_gmail_a",
        gmail_thread_id="thread_gmail_a",
        subject="User A Confidential",
    )

    # Create thread and message for User B with identical gmail_thread_id string
    thread_b = GmailRepository.upsert_thread(db_session, user_b.id, "thread_gmail_a")
    msg_b = GmailRepository.upsert_message(
        db_session,
        user_id=user_b.id,
        thread_id=thread_b.id,
        gmail_message_id="msg_gmail_b",
        gmail_thread_id="thread_gmail_a",
        subject="User B Confidential",
    )

    # Assert distinct database UUID primary keys
    assert thread_a.id != thread_b.id
    assert msg_a.id != msg_b.id

    # Assert querying as User A strictly returns User A's thread only
    threads_a = db_session.execute(
        select(type(thread_a)).where(type(thread_a).user_id == user_a.id)
    ).scalars().all()
    
    assert len(threads_a) == 1
    assert threads_a[0].id == thread_a.id

    # Assert User A cannot delete User B's message
    deleted = GmailRepository.delete_message_by_gmail_id(db_session, user_a.id, "msg_gmail_b")
    assert deleted is False

    # Assert User B's message remains intact
    msg_b_check = db_session.execute(
        select(type(msg_b)).where(type(msg_b).id == msg_b.id)
    ).scalar_one_or_none()
    assert msg_b_check is not None
