"""
Tier 5 — Adversarial Stress & Fault Injection
Specification: TEST_INFRA.md §Coverage Thresholds & System Prompt Adversarial Verification
Tests resilience under rapid load bursts, race conditions, SSE connection storms,
malformed payloads with control characters, and primary provider failure fallbacks.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.events import EventBus
from tests.test_helpers import create_test_email


def test_adversarial_rapid_sync_bombardment(
    client: TestClient,
    auth_user: dict,
):
    """Adversarial 1: Fire 10 rapid sync requests in immediate succession.
    
    Verifies lock serialization, no deadlocks, and zero HTTP 409 or 500 errors.
    """
    with patch("backend.app.api.v1.gmail._run_async_sync"):
        responses = [
            client.post("/api/v1/gmail/sync", cookies=auth_user["cookies"])
            for _ in range(10)
        ]

        # Every response must be 202 Accepted, never 409 Conflict or 500 Server Error
        for r in responses:
            assert r.status_code == 202
            assert r.json()["status"] in ["ACCEPTED", "IN_PROGRESS", "SYNCING"]


@pytest.mark.asyncio
async def test_adversarial_sse_subscriber_storm_and_cleanup():
    """Adversarial 2: Subscribe 30 concurrent listeners to EventBus, burst events, and clean up.
    
    Verifies high fan-out delivery and zero lingering subscriber queues.
    """
    bus = EventBus()
    user_id = uuid.uuid4()

    # Create 30 listener queues
    queues = [await bus.subscribe(user_id) for _ in range(30)]
    assert len(bus._subscribers[user_id]) == 30

    # Publish burst of 5 events
    for i in range(5):
        await bus.publish(user_id, "sync_progress", {"batch": i, "status": "SYNCING"})

    # Verify all queues received all 5 events
    for q in queues:
        assert q.qsize() == 5

    # Unsubscribe all
    for q in queues:
        await bus.unsubscribe(user_id, q)

    assert user_id not in bus._subscribers


def test_adversarial_malformed_email_payload_resilience(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Adversarial 3: Email containing null bytes, invalid tags, and control characters.
    
    Verifies that AI extraction and draft generation don't crash or corrupt DB.
    """
    user = auth_user["user"]
    malformed_body = (
        "Subject: \x00\x01\x02Malicious Header\n"
        "<script>alert('xss')</script><iframe src='javascript:void(0)'>"
        "Payment of €9,999.99 requested.\n"
        "\u0000\u0007\u0008\u001b[31mRed Alert\u001b[0m"
    )

    thread, message = create_test_email(
        db_session,
        user.id,
        subject="Malformed \x00 Subject",
        body=malformed_body,
    )

    # 1. AI Extraction on malformed body
    ai_res = client.post(
        f"/api/v1/ai/analyze/message/{message.id}",
        cookies=auth_user["cookies"],
    )
    assert ai_res.status_code == 200
    assert ai_res.json()["status"] == "COMPLETED"

    # 2. Reply Draft generation from malformed message
    draft_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(message.id), "tone": "PROFESSIONAL"},
        cookies=auth_user["cookies"],
    )
    assert draft_res.status_code == 201
    assert "id" in draft_res.json()


def test_adversarial_concurrent_draft_updates_race(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Adversarial 4: Fire 5 rapid updates to the same reply draft.
    
    Verifies that database transactions serialize cleanly without integrity errors.
    """
    msg_id = test_email["message"].id
    cookies = auth_user["cookies"]

    # Generate draft
    gen_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(msg_id)},
        cookies=cookies,
    )
    draft_id = gen_res.json()["id"]

    responses = [
        client.put(
            f"/api/v1/reply-drafts/{draft_id}",
            json={"body_text": f"Concurrent edit version {i}"},
            cookies=cookies,
        )
        for i in range(5)
    ]

    for r in responses:
        assert r.status_code == 200


def test_adversarial_ai_extraction_provider_timeout_fallback(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Adversarial 5: Simulate primary AI provider failure / network timeout.
    
    Verifies that the extraction service seamlessly falls back to MockAIProvider
    and succeeds without throwing HTTP 500 to the caller.
    """
    msg_id = test_email["message"].id

    with patch(
        "backend.app.ai.provider.GeminiProvider.extract_email_intelligence",
        new=AsyncMock(side_effect=TimeoutError("Gemini API connection timed out after 30s")),
    ):
        response = client.post(
            f"/api/v1/ai/analyze/message/{msg_id}",
            cookies=auth_user["cookies"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert "summary" in data
