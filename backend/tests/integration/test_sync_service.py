from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.orm import Session

from backend.app.core.crypto import encrypt_token
from backend.app.integrations.gmail import GmailAPIError, GmailClient
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.app.repositories.gmail_repository import GmailRepository
from backend.app.services.gmail_sync_service import GmailSyncService
from backend.tests.fixtures.gmail_fixtures import (
    MOCK_GMAIL_HISTORY_INCREMENTAL,
    MOCK_GMAIL_PROFILE,
    MOCK_MESSAGE_101_PAYLOAD,
    MOCK_MESSAGE_102_PAYLOAD,
)
from backend.tests.integration.test_database import db_session, test_engine


@pytest.mark.anyio
@patch("backend.app.integrations.gmail.GmailClient.get_valid_access_token")
async def test_initial_sync_baseline_history_id_capture_invariant(
    mock_get_token,
    db_session: Session,
):
    """Verify initial synchronization captures baseline historyId BEFORE message ingestion."""
    mock_get_token.return_value = "mock_access_token_123"

    user = User(email="syncuser@enterprise.com", full_name="Sync User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_sync_test",
        encrypted_access_token=encrypt_token("mock_access_token_123"),
        encrypted_refresh_token=encrypt_token("mock_refresh_token_123"),
    )
    db_session.add(oauth_acc)
    db_session.commit()

    mock_client = AsyncMock(spec=GmailClient)
    mock_client.get_valid_access_token = MagicMock(return_value="mock_access_token_123")
    mock_client.get_profile.return_value = MOCK_GMAIL_PROFILE
    mock_client.list_messages.return_value = {
        "messages": [
            {"id": "msg_101", "threadId": "thread_001"},
            {"id": "msg_102", "threadId": "thread_001"},
        ]
    }
    mock_client.get_message.side_effect = lambda token, msg_id: (
        MOCK_MESSAGE_101_PAYLOAD if msg_id == "msg_101" else MOCK_MESSAGE_102_PAYLOAD
    )

    sync_service = GmailSyncService(client=mock_client)
    res = await sync_service.execute_sync(db_session, user)

    assert res["status"] == "COMPLETED"
    assert res["type"] == "INITIAL_BASELINE"
    assert res["messages_synced"] == 2
    assert res["last_history_id"] == 1000500

    # Verify state saved in PostgreSQL
    state = GmailRepository.get_or_create_sync_state(db_session, user.id)
    assert state.sync_status == "COMPLETED"
    assert state.last_history_id == 1000500
    assert state.synced_message_count == 2


@pytest.mark.anyio
@patch("backend.app.integrations.gmail.GmailClient.get_valid_access_token")
async def test_incremental_history_sync_and_404_fallback(
    mock_get_token,
    db_session: Session,
):
    """Verify incremental History API sync and automatic fallback to full sync on HTTP 404."""
    mock_get_token.return_value = "mock_access_token_123"

    user = User(email="histuser@enterprise.com", full_name="Hist User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_hist_test",
        encrypted_access_token=encrypt_token("mock_access_token_123"),
        encrypted_refresh_token=encrypt_token("mock_refresh_token_123"),
    )
    db_session.add(oauth_acc)
    db_session.commit()

    # Pre-populate sync state with existing last_history_id
    GmailRepository.update_sync_state(
        db_session,
        user.id,
        sync_status="COMPLETED",
        last_history_id=1000500,
        synced_message_count=2,
    )

    # 1. Test successful incremental history sync
    mock_client = AsyncMock(spec=GmailClient)
    mock_client.get_valid_access_token = MagicMock(return_value="mock_access_token_123")
    mock_client.list_history.return_value = MOCK_GMAIL_HISTORY_INCREMENTAL
    mock_client.get_message.return_value = MOCK_MESSAGE_101_PAYLOAD

    sync_service = GmailSyncService(client=mock_client)
    res = await sync_service.execute_sync(db_session, user)

    assert res["status"] == "COMPLETED"
    assert res["type"] == "INCREMENTAL_HISTORY"
    assert res["last_history_id"] == 1000602

    # 2. Test HTTP 404 historyIdNotFound triggering full sync fallback
    mock_client_404 = AsyncMock(spec=GmailClient)
    mock_client_404.get_valid_access_token = MagicMock(return_value="mock_access_token_123")
    mock_client_404.list_history.side_effect = GmailAPIError(404, "historyIdNotFound: Requested historyId is invalid or expired.")
    mock_client_404.get_profile.return_value = MOCK_GMAIL_PROFILE
    mock_client_404.list_messages.return_value = {"messages": [{"id": "msg_101", "threadId": "thread_001"}]}
    mock_client_404.get_message.return_value = MOCK_MESSAGE_101_PAYLOAD

    sync_service_404 = GmailSyncService(client=mock_client_404)
    res_fallback = await sync_service_404.execute_sync(db_session, user)

    assert res_fallback["status"] == "COMPLETED"
    assert res_fallback["type"] == "INITIAL_BASELINE"
    assert res_fallback["last_history_id"] == 1000500
