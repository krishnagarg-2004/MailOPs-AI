"""
Tier 1 — Feature 4: Reply Drafts (Generation/Editing/Sending)
Specification: ORIGINAL_REQUEST.md §R1, PROJECT.md §Feature Inventory & Interface Contracts
Tests primary behavior for AI reply draft generation, retrieval, manual editing, and discard.
"""

import pytest
from fastapi.testclient import TestClient


def test_f4_1_reply_draft_generate_unauthenticated_401(
    client: TestClient,
    test_email: dict,
):
    """Verify POST /api/v1/reply-drafts/generate returns 401 when unauthenticated."""
    payload = {
        "email_message_id": str(test_email["message"].id),
        "tone": "PROFESSIONAL",
    }
    response = client.post("/api/v1/reply-drafts/generate", json=payload)
    assert response.status_code == 401


def test_f4_2_reply_draft_generate_success_201(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify POST /api/v1/reply-drafts/generate returns 201 Created with structured draft."""
    payload = {
        "email_message_id": str(test_email["message"].id),
        "tone": "PROFESSIONAL",
        "intent": "REPLY_RESPONSE",
    }
    response = client.post(
        "/api/v1/reply-drafts/generate",
        json=payload,
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 201
    draft = response.json()
    assert "id" in draft
    assert draft["email_message_id"] == str(test_email["message"].id)
    assert draft["tone"] == "PROFESSIONAL"
    assert "body_text" in draft
    assert len(draft["body_text"]) > 0


def test_f4_3_reply_draft_get_by_id(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify GET /api/v1/reply-drafts/{draft_id} retrieves a specific draft."""
    gen_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(test_email["message"].id), "tone": "CONCISE"},
        cookies=auth_user["cookies"],
    )
    draft_id = gen_res.json()["id"]

    response = client.get(
        f"/api/v1/reply-drafts/{draft_id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    assert response.json()["id"] == draft_id
    assert response.json()["tone"] == "CONCISE"


def test_f4_4_reply_draft_update_edit(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify PUT /api/v1/reply-drafts/{draft_id} updates subject, body_text, and tone."""
    gen_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(test_email["message"].id)},
        cookies=auth_user["cookies"],
    )
    draft_id = gen_res.json()["id"]

    update_payload = {
        "subject": "Updated Subject: Payment Confirmed",
        "body_text": "Hi Alex,\n\nWe have verified the invoice and initiated transfer.\n\nBest regards,\nOperations",
        "tone": "URGENT",
    }
    put_res = client.put(
        f"/api/v1/reply-drafts/{draft_id}",
        json=update_payload,
        cookies=auth_user["cookies"],
    )
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["subject"] == update_payload["subject"]
    assert data["body_text"] == update_payload["body_text"]
    assert data["tone"] == "URGENT"


def test_f4_5_reply_draft_discard_soft_delete(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify DELETE /api/v1/reply-drafts/{draft_id} sets status to DISCARDED."""
    gen_res = client.post(
        "/api/v1/reply-drafts/generate",
        json={"email_message_id": str(test_email["message"].id)},
        cookies=auth_user["cookies"],
    )
    draft_id = gen_res.json()["id"]

    del_res = client.delete(
        f"/api/v1/reply-drafts/{draft_id}",
        cookies=auth_user["cookies"],
    )
    assert del_res.status_code == 200
    assert del_res.json()["status"].lower() == "discarded"
