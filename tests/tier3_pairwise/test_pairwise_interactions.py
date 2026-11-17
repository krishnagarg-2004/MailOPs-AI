"""
Tier 3 — Cross-Feature Combinations (Pairwise Interactions)
Specification: TEST_INFRA.md §Feature Inventory & Coverage Thresholds
Tests pairwise combinations across all 6 core features:
- Pair 1: F1 (Sync) + F4 (Reply Drafts)
- Pair 2: F2 (Older Emails) + F6 (Zero Popups)
- Pair 3: F3 (AI Extractions) + F5 (Theme Compliance)
- Pair 4: F1 (Sync) + F2 (Older Emails Concurrency)
- Pair 5: F3 (AI Extractions) + F4 (Reply Drafts Provenance)
- Pair 6: F4 (Reply Drafts) + F6 (Zero Popups & Inline Action)
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.reply_draft import ReplyDraft
from backend.app.repositories.gmail_repository import GmailRepository
from tests.test_helpers import create_test_email, scan_frontend_for_forbidden_colors, scan_frontend_for_native_dialogs


def test_pairwise_sync_and_reply_draft_selection_isolation(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
    db_session: Session,
):
    """Pairwise F1 + F4: Verify draft state remains untouched when live sync completes in background."""
    msg_id = test_email["message"].id

    # 1. User generates and edits a reply draft
    gen_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(msg_id), "tone": "PROFESSIONAL"},
        cookies=auth_user["cookies"],
    )
    draft_id = gen_res.json()["id"]

    client.put(
        f"/api/v1/reply-drafts/{draft_id}",
        json={"body_text": "Custom operator draft message."},
        cookies=auth_user["cookies"],
    )

    # 2. Trigger background sync while draft is active
    with patch("backend.app.api.v1.gmail._run_async_sync"):
        sync_res = client.post("/api/v1/gmail/sync", cookies=auth_user["cookies"])
        assert sync_res.status_code == 202

    # 3. Verify draft content was not mutated or overwritten by sync
    get_res = client.get(
        f"/api/v1/reply-drafts/{draft_id}",
        cookies=auth_user["cookies"],
    )
    assert get_res.status_code == 200
    assert get_res.json()["body_text"] == "Custom operator draft message."


def test_pairwise_older_emails_and_zero_popups_error_handling(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Pairwise F2 + F6: Verify older email load failures return structured responses without 409 or popups."""
    user = auth_user["user"]
    GmailRepository.get_or_create_sync_state(db_session, user.id)
    GmailRepository.update_sync_state(db_session, user.id, sync_status="SYNCING")

    res = client.post(
        "/api/v1/gmail/sync-older?count=50",
        cookies=auth_user["cookies"],
    )
    assert res.status_code != 409
    assert res.status_code in [200, 202]
    assert res.json()["status"] in ["IN_PROGRESS", "ACCEPTED", "SYNCING"]


def test_pairwise_ai_extraction_and_theme_compliance():
    """Pairwise F3 + F5: Verify AI extraction card uses strictly Black/Gray/Red theme tokens."""
    violations = scan_frontend_for_forbidden_colors(
        "frontend/src/components",
        target_components=["EmailAnalysisCard.tsx"],
    )
    assert len(violations) == 0, (
        f"EmailAnalysisCard contains non-compliant theme tokens: {violations}"
    )


def test_pairwise_live_sync_and_older_emails_concurrency(
    client: TestClient,
    auth_user: dict,
):
    """Pairwise F1 + F2: Verify concurrent trigger of /sync and /sync-older handles lock safely."""
    with patch("backend.app.api.v1.gmail._run_async_sync"), patch(
        "backend.app.api.v1.gmail._run_async_sync_older"
    ):
        res_sync = client.post("/api/v1/gmail/sync", cookies=auth_user["cookies"])
        assert res_sync.status_code == 202

        res_older = client.post("/api/v1/gmail/sync-older?count=50", cookies=auth_user["cookies"])
        assert res_older.status_code == 202
        assert res_older.json()["status"] in ["ACCEPTED", "IN_PROGRESS", "SYNCING"]


def test_pairwise_ai_extractions_and_reply_draft_provenance(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Pairwise F3 + F4: Verify AI extraction results feed into reply draft context cleanly."""
    msg_id = test_email["message"].id

    analyze_res = client.post(
        f"/api/v1/ai/analyze/message/{msg_id}",
        cookies=auth_user["cookies"],
    )
    assert analyze_res.status_code == 200

    draft_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(msg_id), "tone": "PROFESSIONAL"},
        cookies=auth_user["cookies"],
    )
    assert draft_res.status_code == 201
    draft_data = draft_res.json()
    assert "rationale_and_provenance" in draft_data


def test_pairwise_reply_draft_send_and_zero_popups_inline_confirm():
    """Pairwise F4 + F6: Verify reply draft sending does not invoke window.confirm() or alert()."""
    violations = scan_frontend_for_native_dialogs("frontend/src/components")
    draft_violations = [
        v for v in violations
        if "ReplyDraftWidget" in v["file"]
    ]
    assert len(draft_violations) == 0, (
        f"ReplyDraftWidget contains native dialog calls: {draft_violations}"
    )
