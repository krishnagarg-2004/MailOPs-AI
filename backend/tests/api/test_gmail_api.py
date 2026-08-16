from unittest.mock import patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.crypto import encrypt_token
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.app.repositories.gmail_repository import GmailRepository
from backend.app.services.auth_service import create_user_session
from backend.tests.integration.test_database import db_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db_tables():
    """Ensure clean schema tables exist for all API tests."""
    client.cookies.clear()
    Base.metadata.create_all(bind=test_engine)
    yield
    client.cookies.clear()
    Base.metadata.drop_all(bind=test_engine)
    with test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        conn.commit()


def test_gmail_api_unauthenticated_returns_401():
    """Verify Gmail API endpoints return 401 Unauthorized when session cookie is missing."""
    client.cookies.clear()
    resp = client.get("/api/v1/gmail/status")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    resp_sync = client.post("/api/v1/gmail/sync")
    assert resp_sync.status_code == status.HTTP_401_UNAUTHORIZED


def test_gmail_status_and_sync_trigger(db_session):
    """Verify GET /api/v1/gmail/status returns connection status and POST /api/v1/gmail/sync returns 202 Accepted."""
    user = User(email="apigmailuser@enterprise.com", full_name="API Gmail User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_api_gmail",
        email="apigmailuser@enterprise.com",
        encrypted_access_token=encrypt_token("access_token_123"),
        encrypted_refresh_token=encrypt_token("refresh_token_123"),
    )

    db_session.add(oauth_acc)
    db_session.commit()

    raw_token, _ = create_user_session(db_session, user)
    cookie_name = settings.SESSION_COOKIE_NAME

    # 1. Check status
    status_resp = client.get("/api/v1/gmail/status", cookies={cookie_name: raw_token})
    assert status_resp.status_code == status.HTTP_200_OK
    data = status_resp.json()
    assert data["connected"] is True
    assert data["email"] == "apigmailuser@enterprise.com"

    # 2. Trigger sync
    with patch("backend.app.api.v1.gmail._run_async_sync"):
        sync_resp = client.post("/api/v1/gmail/sync", cookies={cookie_name: raw_token})
        assert sync_resp.status_code == status.HTTP_202_ACCEPTED
        assert sync_resp.json()["status"] == "ACCEPTED"


def test_gmail_threads_and_messages_endpoints(db_session):
    """Verify GET /api/v1/gmail/threads and /api/v1/gmail/threads/{id} endpoints."""
    user = User(email="threadapiuser@enterprise.com", full_name="Thread User")
    db_session.add(user)
    db_session.commit()

    thread = GmailRepository.upsert_thread(db_session, user.id, "thread_api_1", snippet="API thread snippet")
    msg = GmailRepository.upsert_message(
        db_session,
        user.id,
        thread.id,
        "msg_api_1",
        "thread_api_1",
        subject="API Subject",
        snippet="API message snippet",
        labels=["INBOX"],
    )

    raw_token, _ = create_user_session(db_session, user)
    cookie_name = settings.SESSION_COOKIE_NAME

    # 1. List threads
    threads_resp = client.get("/api/v1/gmail/threads", cookies={cookie_name: raw_token})
    assert threads_resp.status_code == status.HTTP_200_OK
    threads_data = threads_resp.json()
    assert len(threads_data) == 1
    assert threads_data[0]["gmail_thread_id"] == "thread_api_1"

    # 2. Get thread detail
    detail_resp = client.get(f"/api/v1/gmail/threads/{thread.id}", cookies={cookie_name: raw_token})
    assert detail_resp.status_code == status.HTTP_200_OK
    detail_data = detail_resp.json()
    assert detail_data["id"] == str(thread.id)
    assert len(detail_data["messages"]) == 1
    assert detail_data["messages"][0]["subject"] == "API Subject"

    # 3. Get message detail
    msg_resp = client.get(f"/api/v1/gmail/messages/{msg.id}", cookies={cookie_name: raw_token})
    assert msg_resp.status_code == status.HTTP_200_OK
    assert msg_resp.json()["id"] == str(msg.id)


def test_gmail_disconnect_endpoint(db_session):
    """Verify DELETE /api/v1/gmail/disconnect clears tokens and sync state."""
    user = User(email="disconnectuser@enterprise.com", full_name="Disconnect User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_disc_test",
        encrypted_access_token=encrypt_token("access_token_123"),
        encrypted_refresh_token=encrypt_token("refresh_token_123"),
    )
    db_session.add(oauth_acc)
    db_session.commit()

    raw_token, _ = create_user_session(db_session, user)
    cookie_name = settings.SESSION_COOKIE_NAME

    disc_resp = client.delete("/api/v1/gmail/disconnect", cookies={cookie_name: raw_token})
    assert disc_resp.status_code == status.HTTP_200_OK
    assert disc_resp.json()["status"] == "disconnected"

    db_session.refresh(oauth_acc)
    assert oauth_acc.encrypted_access_token is None
