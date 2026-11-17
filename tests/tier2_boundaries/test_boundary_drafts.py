"""
Tier 2 — Boundary & Corner Cases: Reply Drafts (Generation/Editing/Sending)
Tests boundaries: rationale_and_provenance schema flexibility (strings vs dicts),
user isolation, RFC 2822 MIME compiling, and nonexistent draft lookups.
"""

from datetime import datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.reply_draft import ReplyDraft
from backend.app.services.reply_draft_service import build_raw_reply_mime
from tests.test_helpers import create_test_auth_session, create_test_email


def test_boundary_draft_schema_list_of_strings_rationale(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
    db_session: Session,
):
    """Verify GET /api/v1/reply-drafts/message/{id} handles list of strings in rationale without HTTP 500.
    
    This directly verifies the fix for the HTTP 500 bug discovered in survey 3.
    """
    user = auth_user["user"]
    msg = test_email["message"]

    # Insert draft with string rationale (like the demo seed)
    draft = ReplyDraft(
        user_id=user.id,
        email_thread_id=msg.thread_id,
        email_message_id=msg.id,
        subject="Re: Payment Status",
        body_text="Payment has been confirmed.",
        recipient_email="vendor@company.com",
        intent="REPLY_RESPONSE",
        tone="PROFESSIONAL",
        status="DRAFTED",
        rationale_and_provenance=[
            "Drafted to de-escalate payment cluster rate limits and confirm threshold stabilization."
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(draft)
    db_session.commit()

    response = client.get(
        f"/api/v1/reply-drafts/message/{msg.id}",
        cookies=auth_user["cookies"],
    )
    # Must NOT be 500 Internal Server Error
    assert response.status_code == 200, (
        f"Expected 200 OK but got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert len(data) >= 1
    assert data[0]["id"] == str(draft.id)


def test_boundary_draft_schema_list_of_dicts_rationale(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
    db_session: Session,
):
    """Verify GET /api/v1/reply-drafts/message/{id} handles structured dictionary provenance items."""
    user = auth_user["user"]
    msg = test_email["message"]

    draft = ReplyDraft(
        user_id=user.id,
        email_thread_id=msg.thread_id,
        email_message_id=msg.id,
        subject="Re: Payment Status",
        body_text="Payment has been confirmed.",
        recipient_email="vendor@company.com",
        intent="REPLY_RESPONSE",
        tone="PROFESSIONAL",
        status="DRAFTED",
        rationale_and_provenance=[
            {
                "source_type": "ACTION_ITEM",
                "source_id": "act_123",
                "description": "Authorize payment settlement",
                "verbatim_text": "Invoice #404 due",
            }
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(draft)
    db_session.commit()

    response = client.get(
        f"/api/v1/reply-drafts/message/{msg.id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_boundary_draft_user_isolation(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
    db_session: Session,
):
    """Verify User B cannot access User A's reply draft (returns 404)."""
    user_b, cookies_b, _ = create_test_auth_session(db_session, email="user_b@enterprise.com")

    gen_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(test_email["message"].id)},
        cookies=auth_user["cookies"],
    )
    draft_id = gen_res.json()["id"]

    res_b = client.get(
        f"/api/v1/reply-drafts/{draft_id}",
        cookies=cookies_b,
    )
    assert res_b.status_code == 404


def test_boundary_draft_mime_compilation_special_chars():
    """Verify build_raw_reply_mime safely encodes UTF-8 and special MIME characters."""
    encoded_mime = build_raw_reply_mime(
        sender="Alex Morgan <alex.morgan@enterprise-mailops.io>",
        recipient="Partner Support <partner-support@vendor.co.jp>",
        subject="Re: システムアップデート & 請求書 #9090",
        body_text="Hello,\n\nWe have verified the Japanese billing statement (¥50,000).\n\n\"Thank you!\"",
        in_reply_to_msg_id="<msg-9090-abc@vendor.co.jp>",
        references="<msg-9090-abc@vendor.co.jp>",
    )
    assert isinstance(encoded_mime, str)
    assert len(encoded_mime) > 0


def test_boundary_draft_nonexistent_draft_update_404(
    client: TestClient,
    auth_user: dict,
):
    """Verify updating a non-existent draft ID returns HTTP 404."""
    fake_id = uuid.uuid4()
    response = client.put(
        f"/api/v1/reply-drafts/{fake_id}",
        json={"body_text": "New body"},
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 404
