"""
Tier 2 — Boundary & Corner Cases: AI Intelligence Extractions
Tests boundaries: empty message body, ultra-large payloads, Unicode/emojis,
hallucinated evidence detection, and non-existent message IDs.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.utils.evidence_validator import EvidenceValidator
from tests.test_helpers import create_test_email


def test_boundary_ai_empty_message_body(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify extracting intelligence from an email with empty body/snippet does not crash."""
    user = auth_user["user"]
    thread, message = create_test_email(
        db_session,
        user.id,
        subject="Blank Email",
        body="",
    )

    response = client.post(
        f"/api/v1/ai/analyze/message/{message.id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "confidence_score" in data


def test_boundary_ai_large_payload(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify processing an email with a 30KB+ body text completes successfully."""
    user = auth_user["user"]
    long_body = "Quarterly system performance report.\n" + ("Database connection latency steady at 12ms. " * 600)
    thread, message = create_test_email(
        db_session,
        user.id,
        subject="Large Report",
        body=long_body,
    )

    response = client.post(
        f"/api/v1/ai/analyze/message/{message.id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


def test_boundary_ai_unicode_and_emojis(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify email containing Unicode, emojis, and non-ASCII chars produces clean output."""
    user = auth_user["user"]
    unicode_body = "🚨 Urgent: Payment authorization requested for 1,500€ 支付确认 ⚡. Please confirm."
    thread, message = create_test_email(
        db_session,
        user.id,
        subject="Payment Alert 💳",
        body=unicode_body,
    )

    response = client.post(
        f"/api/v1/ai/analyze/message/{message.id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"


def test_boundary_ai_hallucinated_evidence_detection():
    """Verify EvidenceValidator flags hallucinated snippets not found in source text."""
    source_email = "The deployment is scheduled for Friday at 6 PM EST. Team leads must sign off."
    
    # Valid snippet
    assert EvidenceValidator.validate_snippet(
        "deployment is scheduled for Friday",
        source_email,
    ) is True

    # Hallucinated snippet (not in email)
    assert EvidenceValidator.validate_snippet(
        "Authorize immediate wire transfer of $50,000",
        source_email,
    ) is False


def test_boundary_ai_nonexistent_message_returns_404(
    client: TestClient,
    auth_user: dict,
):
    """Verify POST /api/v1/ai/analyze/message/{fake_uuid} returns HTTP 404."""
    fake_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/ai/analyze/message/{fake_id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 404
