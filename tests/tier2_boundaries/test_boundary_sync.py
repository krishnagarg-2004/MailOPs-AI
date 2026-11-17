"""
Tier 2 — Boundary & Corner Cases: Live Gmail Synchronization
Tests boundaries: rapid successive triggers, stale lock recovery, unauthorized token handling,
empty mailboxes, and event bus edge cases.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.events import EventBus
from backend.app.models.gmail_sync_state import GmailSyncState
from backend.app.repositories.gmail_repository import GmailRepository


def test_boundary_sync_rapid_successive_triggers(
    client: TestClient,
    auth_user: dict,
):
    """Verify rapid consecutive sync calls do not crash or return 409, returning 202."""
    with patch("backend.app.api.v1.gmail._run_async_sync"):
        resp1 = client.post("/api/v1/gmail/sync", cookies=auth_user["cookies"])
        resp2 = client.post("/api/v1/gmail/sync", cookies=auth_user["cookies"])
        resp3 = client.post("/api/v1/gmail/sync", cookies=auth_user["cookies"])

        assert resp1.status_code == 202
        assert resp2.status_code == 202
        assert resp3.status_code == 202

        assert resp2.json()["status"] in ["ACCEPTED", "IN_PROGRESS", "SYNCING"]
        assert resp3.json()["status"] in ["ACCEPTED", "IN_PROGRESS", "SYNCING"]


def test_boundary_sync_stale_lock_recovery(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify stale sync locks (>180 seconds old) are automatically cleared and allowed to re-sync."""
    user = auth_user["user"]
    sync_state = GmailRepository.get_or_create_sync_state(db_session, user.id)
    # Set stale lock from 4 minutes ago
    sync_state.sync_status = "SYNCING"
    sync_state.updated_at = datetime.now(timezone.utc) - timedelta(seconds=240)
    db_session.commit()

    with patch("backend.app.api.v1.gmail._run_async_sync"):
        response = client.post("/api/v1/gmail/sync", cookies=auth_user["cookies"])
        assert response.status_code == 202
        assert response.json()["status"] == "ACCEPTED"


def test_boundary_sync_missing_oauth_account(
    client: TestClient,
    db_session: Session,
):
    """Verify sync returns 400 Bad Request when user has no connected Google OAuth account."""
    from tests.test_helpers import create_test_auth_session
    user, cookies, _ = create_test_auth_session(db_session, email="no_oauth@test.com")
    
    from backend.app.models.oauth import OAuthAccount
    db_session.query(OAuthAccount).filter_by(user_id=user.id).delete()
    db_session.commit()

    response = client.post("/api/v1/gmail/sync", cookies=cookies)
    assert response.status_code == 400
    assert "detail" in response.json()


def test_boundary_sync_empty_mailbox_status(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify sync state on a brand-new user with 0 synced messages reports 0 without errors."""
    user = auth_user["user"]
    sync_state = GmailRepository.get_or_create_sync_state(db_session, user.id)
    sync_state.synced_message_count = 0
    sync_state.sync_status = "COMPLETED"
    db_session.commit()

    response = client.get("/api/v1/gmail/status", cookies=auth_user["cookies"])
    assert response.status_code == 200
    data = response.json()
    assert data["sync_state"]["synced_message_count"] == 0
    assert data["sync_state"]["sync_status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_boundary_sync_event_bus_empty_subscribers():
    """Verify EventBus gracefully handles publishing when no clients are subscribed."""
    bus = EventBus()
    non_existent_user = uuid.uuid4()
    await bus.publish(non_existent_user, "sync_progress", {"phase": "DONE"})
    assert non_existent_user not in bus._subscribers
