"""
Tier 1 — Feature 3: AI Intelligence Extractions
Specification: ORIGINAL_REQUEST.md §R1, PROJECT.md §Feature Inventory & Interface Contracts
Tests primary behavior for AI analysis pipeline, structured intelligence fields,
action item retrieval, and human-in-the-loop status updates.
"""

import pytest
from fastapi.testclient import TestClient


def test_f3_1_ai_analyze_unauthenticated_returns_401(client: TestClient, test_email: dict):
    """Verify POST /api/v1/ai/analyze/message/{id} returns 401 when unauthenticated."""
    msg_id = test_email["message"].id
    response = client.post(f"/api/v1/ai/analyze/message/{msg_id}")
    assert response.status_code == 401


def test_f3_2_ai_analyze_message_success(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify AI analysis produces structured intelligence (intent, priority, summary, actions)."""
    msg_id = test_email["message"].id
    response = client.post(
        f"/api/v1/ai/analyze/message/{msg_id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email_message_id"] == str(msg_id)
    assert "intent" in data
    assert "priority" in data
    assert "summary" in data
    assert "confidence_score" in data
    assert isinstance(data.get("extracted_items"), list)
    assert len(data["extracted_items"]) > 0


def test_f3_3_ai_get_analysis(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify GET /api/v1/ai/analysis/message/{id} retrieves previously generated analysis."""
    msg_id = test_email["message"].id
    # First generate analysis
    client.post(
        f"/api/v1/ai/analyze/message/{msg_id}",
        cookies=auth_user["cookies"],
    )

    # Then retrieve it
    response = client.get(
        f"/api/v1/ai/analysis/message/{msg_id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email_message_id"] == str(msg_id)
    assert data["status"] == "COMPLETED"


def test_f3_4_ai_actions_listing(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify GET /api/v1/ai/actions returns list of actionable items for current user."""
    msg_id = test_email["message"].id
    client.post(
        f"/api/v1/ai/analyze/message/{msg_id}",
        cookies=auth_user["cookies"],
    )

    response = client.get(
        "/api/v1/ai/actions",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    actions = response.json()
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert "description" in actions[0]
    assert "status" in actions[0]


def test_f3_5_ai_action_status_patch(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify PATCH /api/v1/ai/actions/{action_id} allows human-in-the-loop status transitions."""
    msg_id = test_email["message"].id
    client.post(
        f"/api/v1/ai/analyze/message/{msg_id}",
        cookies=auth_user["cookies"],
    )
    actions_res = client.get(
        "/api/v1/ai/actions",
        cookies=auth_user["cookies"],
    )
    action_id = actions_res.json()[0]["id"]

    patch_res = client.patch(
        f"/api/v1/ai/actions/{action_id}",
        json={"status": "CONFIRMED"},
        cookies=auth_user["cookies"],
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "CONFIRMED"
