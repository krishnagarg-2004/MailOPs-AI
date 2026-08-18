import uuid
import pytest
from sqlalchemy.orm import Session
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.reply_draft import ReplyDraft
from backend.app.models.user import User
from backend.app.services.reply_draft_service import ReplyDraftService
from backend.tests.integration.test_database import db_session, test_engine


@pytest.mark.asyncio
async def test_no_automatic_send_guarantee(db_session: Session):
    """
    EXPLICIT SECURITY TEST:
    Verify AI draft generation ONLY persists locally in PostgreSQL with status DRAFTED,
    and NEVER sends or syncs email automatically.
    """
    user = User(email=f"nosend_{uuid.uuid4().hex[:8]}@test.com", full_name="No Send User", is_active=True)
    db_session.add(user)
    db_session.commit()

    thread = EmailThread(user_id=user.id, gmail_thread_id="th_nosend_123", snippet="No Send Thread")
    db_session.add(thread)
    db_session.commit()

    msg = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id="msg_nosend_123",
        gmail_thread_id=thread.gmail_thread_id,
        sender="client@corp.com",
        subject="Request Details",
        body_plain="Please send details.",
    )
    db_session.add(msg)
    db_session.commit()

    # Generate AI draft
    draft = await ReplyDraftService.generate_draft(db_session, user.id, msg.id, tone="PROFESSIONAL")

    assert draft.status == "DRAFTED"
    assert draft.gmail_draft_id is None
    assert "Re:" in draft.subject
    assert draft.user_id == user.id


def test_cross_user_reply_draft_isolation(db_session: Session):
    """
    EXPLICIT SECURITY TEST:
    Verify User B cannot read or update User A's reply drafts.
    """
    user_a = User(email=f"usera_{uuid.uuid4().hex[:8]}@test.com", full_name="User A", is_active=True)
    user_b = User(email=f"userb_{uuid.uuid4().hex[:8]}@test.com", full_name="User B", is_active=True)
    db_session.add_all([user_a, user_b])
    db_session.commit()

    thread_a = EmailThread(user_id=user_a.id, gmail_thread_id="th_a_123", snippet="Thread A")
    db_session.add(thread_a)
    db_session.commit()

    msg_a = EmailMessage(
        user_id=user_a.id,
        thread_id=thread_a.id,
        gmail_message_id="msg_a_123",
        gmail_thread_id=thread_a.gmail_thread_id,
        sender="boss@corp.com",
        subject="Confidential Task",
        body_plain="Confidential text.",
    )
    db_session.add(msg_a)
    db_session.commit()

    draft_a = ReplyDraft(
        user_id=user_a.id,
        email_thread_id=thread_a.id,
        email_message_id=msg_a.id,
        subject="Re: Confidential Task",
        body_text="Confidential draft body.",
        recipient_email="boss@corp.com",
        status="DRAFTED",
    )
    db_session.add(draft_a)
    db_session.commit()

    # User B attempts to update User A's draft -> MUST raise ValueError
    with pytest.raises(ValueError) as exc_info:
        ReplyDraftService.update_draft(db_session, user_b.id, draft_a.id, body_text="Hacked body text")
    assert "not found for user" in str(exc_info.value)
