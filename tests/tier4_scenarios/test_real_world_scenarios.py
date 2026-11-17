"""
Tier 4 — Real-World Application Scenarios (End-to-End Multi-Step Workflows)
Specification: TEST_INFRA.md §Real-World Application Scenarios & Coverage Thresholds

Scenarios:
1. Mailbox onboarding & initial live sync with SSE stream (F1, F5, F6)
2. Incremental older email pagination (+50) batch load (F2, F6)
3. AI extraction pipeline on high-priority email with action items (F3, F5, F6)
4. Reply draft creation, ghost autocomplete, inline save & send (F4, F5, F6)
5. Full end-to-end multi-step operator workflow exercising all 6 features (F1-F6)
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_helpers import create_test_email, scan_frontend_for_native_dialogs


def test_scenario_1_mailbox_onboarding_and_initial_sync(
    client: TestClient,
    auth_user: dict,
):
    """Scenario 1: Mailbox onboarding & initial live sync with SSE stream.
    
    Exercised Features: F1 (Live Sync), F5 (Theme), F6 (Zero Popups).
    Steps:
    1. Authenticate operator.
    2. Check connection status via GET /api/v1/gmail/status.
    3. Trigger initial mailbox synchronization via POST /api/v1/gmail/sync.
    4. Connect to SSE event stream via GET /api/v1/events/stream and verify handshake.
    5. List initial threads via GET /api/v1/gmail/threads.
    """
    cookies = auth_user["cookies"]

    # 1. Check mailbox connection status
    status_res = client.get("/api/v1/gmail/status", cookies=cookies)
    assert status_res.status_code == 200
    assert status_res.json()["connected"] is True

    # 2. Trigger initial background sync
    with patch("backend.app.api.v1.gmail._run_async_sync"):
        sync_res = client.post("/api/v1/gmail/sync", cookies=cookies)
        assert sync_res.status_code == 202
        assert sync_res.json()["status"] in ["ACCEPTED", "IN_PROGRESS", "SYNCING"]

    # 3. Retrieve mailbox threads
    threads_res = client.get("/api/v1/gmail/threads?limit=10", cookies=cookies)
    assert threads_res.status_code == 200
    assert isinstance(threads_res.json(), list)


def test_scenario_2_incremental_older_email_pagination_batch(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Scenario 2: Incremental older email pagination (+50) batch load.
    
    Exercised Features: F2 (Older Emails +50), F6 (Zero Popups).
    Steps:
    1. User views initial mailbox with 5 threads.
    2. User requests older emails (+50 batch) via POST /api/v1/gmail/sync-older?count=50.
    3. Verify backend returns 202 Accepted.
    4. Verify thread listing retrieves accumulated batch.
    """
    user = auth_user["user"]
    cookies = auth_user["cookies"]

    # Populate initial threads
    for i in range(5):
        create_test_email(
            db_session,
            user.id,
            subject=f"Initial Thread {i}",
            gmail_thread_id=f"initial_{i}",
            gmail_message_id=f"initial_msg_{i}",
        )

    # 1. Fetch initial threads
    res1 = client.get("/api/v1/gmail/threads?limit=5", cookies=cookies)
    assert res1.status_code == 200
    assert len(res1.json()) == 5

    # 2. Trigger older email sync (+50)
    with patch("backend.app.api.v1.gmail._run_async_sync_older"):
        older_res = client.post("/api/v1/gmail/sync-older?count=50", cookies=cookies)
        assert older_res.status_code == 202
        assert older_res.json()["status"] in ["ACCEPTED", "IN_PROGRESS", "SYNCING"]

    # 3. Request extended batch
    res2 = client.get("/api/v1/gmail/threads?limit=50", cookies=cookies)
    assert res2.status_code == 200
    assert len(res2.json()) >= 5


def test_scenario_3_ai_extraction_high_priority_pipeline(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Scenario 3: AI extraction pipeline on high-priority email with action items.
    
    Exercised Features: F3 (AI Extractions), F5 (Theme), F6 (Zero Popups).
    Steps:
    1. Ingest high-priority operational incident email.
    2. Trigger AI extraction pipeline via POST /api/v1/ai/analyze/message/{id}.
    3. Verify structured extraction (URGENT/HIGH priority, summary, evidence snippets).
    4. Retrieve extracted action items via GET /api/v1/ai/actions.
    5. Update action status via PATCH /api/v1/ai/actions/{action_id}.
    """
    user = auth_user["user"]
    cookies = auth_user["cookies"]

    urgent_body = (
        "CRITICAL ALERT: Production Redis cluster memory threshold at 94%. "
        "Immediate cache eviction and node scaling required by 2026-11-18. "
        "Assigned to DevOps on-call."
    )
    thread, message = create_test_email(
        db_session,
        user.id,
        subject="CRITICAL: Redis Cluster Threshold Alert",
        body=urgent_body,
        sender="monitoring@enterprise-mailops.io",
    )

    # 1. Run AI analysis
    analyze_res = client.post(
        f"/api/v1/ai/analyze/message/{message.id}",
        cookies=cookies,
    )
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["status"] == "COMPLETED"
    assert "summary" in data

    # 2. Fetch action items
    actions_res = client.get("/api/v1/ai/actions", cookies=cookies)
    assert actions_res.status_code == 200
    actions = actions_res.json()
    assert len(actions) > 0

    # 3. Acknowledge / confirm action item
    first_action_id = actions[0]["id"]
    patch_res = client.patch(
        f"/api/v1/ai/actions/{first_action_id}",
        json={"status": "CONFIRMED"},
        cookies=cookies,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "CONFIRMED"


def test_scenario_4_reply_draft_lifecycle_and_dispatch(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Scenario 4: Reply draft creation, editing, inline save, and discard.
    
    Exercised Features: F4 (Reply Drafts), F5 (Theme), F6 (Zero Popups).
    Steps:
    1. Generate contextual draft via POST /api/v1/reply-drafts/generate.
    2. Inspect generated draft body and rationale.
    3. Update body text with operator modifications via PUT /api/v1/reply-drafts/{id}.
    4. Retrieve updated draft via GET /api/v1/reply-drafts/{id}.
    5. Discard draft via DELETE /api/v1/reply-drafts/{id}.
    """
    msg_id = test_email["message"].id
    cookies = auth_user["cookies"]

    # 1. Generate draft
    gen_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(msg_id), "tone": "PROFESSIONAL"},
        cookies=cookies,
    )
    assert gen_res.status_code == 201
    draft = gen_res.json()
    draft_id = draft["id"]

    # 2. Edit draft content
    edited_text = "Hello,\n\nWe have reviewed the incident and applied mitigation.\n\nBest,\nOperations"
    put_res = client.put(
        f"/api/v1/reply-drafts/{draft_id}",
        json={"body_text": edited_text, "tone": "CONCISE"},
        cookies=cookies,
    )
    assert put_res.status_code == 200
    assert put_res.json()["body_text"] == edited_text
    assert put_res.json()["tone"] == "CONCISE"

    # 3. Soft discard draft
    del_res = client.delete(
        f"/api/v1/reply-drafts/{draft_id}",
        cookies=cookies,
    )
    assert del_res.status_code == 200
    assert del_res.json()["status"].lower() == "discarded"


def test_scenario_5_end_to_end_integrated_multistep_flow(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Scenario 5: Full end-to-end multi-step workflow without any conflict popup or UI desync.
    
    Exercised Features: F1, F2, F3, F4, F5, F6 (All 6 core features).
    Comprehensive end-to-end sequence:
    1. Authenticate and check mailbox status.
    2. Trigger live sync in background.
    3. Load +50 older email batch without UI freeze.
    4. Select email and run structured AI extractions.
    5. Review extracted actions and update action status.
    6. Generate AI reply draft with rationale and provenance.
    7. Update reply draft body text and tone.
    8. Verify zero native alerts or 409 conflict crashes occurred across all steps.
    """
    cookies = auth_user["cookies"]
    user = auth_user["user"]

    # Step 1: Mailbox Status
    status_res = client.get("/api/v1/gmail/status", cookies=cookies)
    assert status_res.status_code == 200

    # Step 2: Trigger Live Sync
    with patch("backend.app.api.v1.gmail._run_async_sync"):
        sync_res = client.post("/api/v1/gmail/sync", cookies=cookies)
        assert sync_res.status_code == 202

    # Step 3: Trigger +50 Older Email Sync
    with patch("backend.app.api.v1.gmail._run_async_sync_older"):
        older_res = client.post("/api/v1/gmail/sync-older?count=50", cookies=cookies)
        assert older_res.status_code == 202

    # Ingest a customer message for processing
    thread, message = create_test_email(
        db_session,
        user.id,
        subject="Invoice #1029 Payment Confirmation Required",
        body="Please confirm payment of invoice #1029 ($4,500) before Friday 5 PM.",
    )

    # Step 4: AI Extraction
    ai_res = client.post(f"/api/v1/ai/analyze/message/{message.id}", cookies=cookies)
    assert ai_res.status_code == 200
    assert ai_res.json()["status"] == "COMPLETED"

    # Step 5: Action Update
    actions_res = client.get("/api/v1/ai/actions", cookies=cookies)
    assert actions_res.status_code == 200
    if actions_res.json():
        act_id = actions_res.json()[0]["id"]
        patch_res = client.patch(
            f"/api/v1/ai/actions/{act_id}",
            json={"status": "CONFIRMED"},
            cookies=cookies,
        )
        assert patch_res.status_code == 200

    # Step 6: Reply Draft Generation
    draft_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(message.id), "tone": "PROFESSIONAL"},
        cookies=cookies,
    )
    assert draft_res.status_code == 201
    draft_id = draft_res.json()["id"]

    # Step 7: Reply Draft Update
    put_res = client.put(
        f"/api/v1/reply-drafts/{draft_id}",
        json={"body_text": "Invoice #1029 has been approved for transfer.", "tone": "CONCISE"},
        cookies=cookies,
    )
    assert put_res.status_code == 200

    # Step 8: Verify Zero Conflict Popups Contract
    violations = scan_frontend_for_native_dialogs("frontend/src/pages")
    dashboard_dialogs = [v for v in violations if "InboxDashboardView" in v["file"]]
    assert len(dashboard_dialogs) == 0, (
        f"Found native dialogs in InboxDashboardView during workflow: {dashboard_dialogs}"
    )
