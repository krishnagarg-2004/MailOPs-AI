"""
Tier 1 — Feature 1: Live Gmail Synchronization
Specification: ORIGINAL_REQUEST.md §R1, PROJECT.md §Feature Inventory & Interface Contracts
Tests primary behavior (happy paths) for mailbox connection, background sync trigger,
EventBus SSE broadcasting, and disconnection.
"""

from unittest.mock import patch
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.events import EventBus
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User


def test_f1_1_sync_unauthenticated_returns_401(client: TestClient):
    """Verify POST /api/v1/gmail/sync returns HTTP 401 when unauthenticated."""
    response = client.post("/api/v1/gmail/sync")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_f1_2_sync_trigger_authenticated_returns_202(
    client: TestClient,
    auth_user: dict,
):
    """Verify POST /api/v1/gmail/sync returns HTTP 202 Accepted with valid status."""
    with patch("backend.app.api.v1.gmail._run_async_sync"):
        response = client.post(
            "/api/v1/gmail/sync",
            cookies=auth_user["cookies"],
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] in ["ACCEPTED", "IN_PROGRESS", "SYNCING"]
        assert "message" in data


def test_f1_3_sync_status_endpoint(
    client: TestClient,
    auth_user: dict,
):
    """Verify GET /api/v1/gmail/status returns connected state and sync state object."""
    response = client.get(
        "/api/v1/gmail/status",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["email"] == auth_user["user"].email
    assert "sync_state" in data


@pytest.mark.asyncio
async def test_f1_4_event_bus_lifecycle_and_sse():
    """Verify EventBus subscribes queues, routes events by user_id, and delivers payloads."""
    bus = EventBus()
    user_id = uuid.uuid4()

    queue = await bus.subscribe(user_id)
    assert user_id in bus._subscribers

    test_payload = {"phase": "FETCHING_MESSAGES", "synced": 12, "total": 50}
    await bus.publish(user_id, "sync_progress", test_payload)

    event = await queue.get()
    assert event["event"] == "sync_progress"
    assert event["data"] == test_payload
    assert "timestamp" in event

    await bus.unsubscribe(user_id, queue)
    assert user_id not in bus._subscribers


def test_f1_5_disconnect_endpoint(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify DELETE /api/v1/gmail/disconnect revokes tokens and sets disconnected status."""
    response = client.delete(
        "/api/v1/gmail/disconnect",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disconnected"

    # Verify encrypted tokens were cleared in database
    oauth_acc = db_session.query(OAuthAccount).filter_by(user_id=auth_user["user"].id).first()
    assert oauth_acc.encrypted_access_token is None
