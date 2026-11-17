"""
Tier 1 — Feature 2: Older Email Loading (+50)
Specification: ORIGINAL_REQUEST.md §R1, PROJECT.md §Feature Inventory & Interface Contracts
Tests primary behavior for older email sync triggers, thread pagination, limits, and thread details.
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_helpers import create_test_email


def test_f2_1_sync_older_unauthenticated_returns_401(client: TestClient):
    """Verify POST /api/v1/gmail/sync-older returns HTTP 401 when unauthenticated."""
    response = client.post("/api/v1/gmail/sync-older?count=50")
    assert response.status_code == 401


def test_f2_2_sync_older_trigger_returns_202(
    client: TestClient,
    auth_user: dict,
):
    """Verify POST /api/v1/gmail/sync-older?count=50 triggers background retrieval with 202."""
    with patch("backend.app.api.v1.gmail._run_async_sync_older"):
        response = client.post(
            "/api/v1/gmail/sync-older?count=50",
            cookies=auth_user["cookies"],
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] in ["ACCEPTED", "IN_PROGRESS", "SYNCING"]
        assert "message" in data


def test_f2_3_threads_pagination_limit(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify GET /api/v1/gmail/threads?limit=3 respects the requested limit."""
    user = auth_user["user"]
    for i in range(5):
        create_test_email(
            db_session,
            user.id,
            subject=f"Thread Batch {i}",
            gmail_thread_id=f"thread_batch_{i}",
            gmail_message_id=f"msg_batch_{i}",
        )

    response = client.get(
        "/api/v1/gmail/threads?limit=3",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    threads = response.json()
    assert len(threads) <= 3


def test_f2_4_threads_pagination_pages(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify GET /api/v1/gmail/threads with page=1 vs page=2 returns distinct slices."""
    user = auth_user["user"]
    for i in range(4):
        create_test_email(
            db_session,
            user.id,
            subject=f"Paged Thread {i}",
            gmail_thread_id=f"thread_page_{i}",
            gmail_message_id=f"msg_page_{i}",
        )

    res_p1 = client.get(
        "/api/v1/gmail/threads?page=1&limit=2",
        cookies=auth_user["cookies"],
    )
    res_p2 = client.get(
        "/api/v1/gmail/threads?page=2&limit=2",
        cookies=auth_user["cookies"],
    )

    assert res_p1.status_code == 200
    assert res_p2.status_code == 200

    p1_ids = [t["id"] for t in res_p1.json()]
    p2_ids = [t["id"] for t in res_p2.json()]

    assert set(p1_ids).isdisjoint(set(p2_ids))


def test_f2_5_thread_details_with_messages(
    client: TestClient,
    auth_user: dict,
    test_email: dict,
):
    """Verify GET /api/v1/gmail/threads/{id} returns thread details including its messages."""
    thread = test_email["thread"]
    response = client.get(
        f"/api/v1/gmail/threads/{thread.id}",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(thread.id)
    assert "messages" in data
    assert len(data["messages"]) >= 1
    assert data["messages"][0]["subject"] == test_email["message"].subject
