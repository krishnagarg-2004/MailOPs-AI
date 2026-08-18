import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.reply_draft import ReplyDraft
from backend.app.models.user import User
from backend.app.services.auth_service import create_user_session
from backend.tests.integration.test_database import db_session, test_engine

client = TestClient(app)


def test_reply_draft_api_unauthenticated_returns_401():
    response = client.get("/api/v1/reply-drafts/message/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 401


def test_reply_draft_api_generate_update_discard_flow(db_session: Session):
    user = User(
        email=f"reply_api_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Reply API User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    session_token, _ = create_user_session(db_session, user)

    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"thread_rapi_{uuid.uuid4().hex[:8]}",
        snippet="RAPI Thread",
    )
    db_session.add(thread)
    db_session.commit()

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_rapi_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="vendor@company.com",
        subject="Invoice #8892 Inquiry",
        body_plain="Please confirm payment status for Invoice #8892.",
        has_attachments=False,
    )
    db_session.add(message)
    db_session.commit()

    cookies = {"mailops_session": session_token}

    # 1. Test POST /api/v1/reply-drafts/generate
    gen_resp = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(message.id), "tone": "CONCISE", "intent": "REPLY_RESPONSE"},
        cookies=cookies,
    )
    assert gen_resp.status_code == 201
    draft_data = gen_resp.json()
    assert draft_data["status"] == "DRAFTED"
    assert draft_data["tone"] == "CONCISE"
    assert "Re:" in draft_data["subject"]
    draft_id = draft_data["id"]

    # 2. Test GET /api/v1/reply-drafts/message/{message_id}
    list_resp = client.get(f"/api/v1/reply-drafts/message/{message.id}", cookies=cookies)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 3. Test PUT /api/v1/reply-drafts/{draft_id} (Human-in-the-Loop edit)
    update_resp = client.put(
        f"/api/v1/reply-drafts/{draft_id}",
        json={"body_text": "Payment for Invoice #8892 has been scheduled for Friday.", "tone": "PROFESSIONAL"},
        cookies=cookies,
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["body_text"] == "Payment for Invoice #8892 has been scheduled for Friday."
    assert updated_data["status"] == "EDITED"

    # 4. Test DELETE /api/v1/reply-drafts/{draft_id}
    del_resp = client.delete(f"/api/v1/reply-drafts/{draft_id}", cookies=cookies)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "discarded"
