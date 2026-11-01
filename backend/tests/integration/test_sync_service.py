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


# ---------------------------------------------------------------------------
# FIX-SYNC-4: History API pagination — nextPageToken must be followed
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("backend.app.integrations.gmail.GmailClient.get_valid_access_token")
async def test_incremental_history_sync_processes_all_pages(
    mock_get_token,
    db_session: Session,
):
    """FIX-SYNC-4: Verify incremental sync follows nextPageToken until exhausted.

    Without the fix a second history page would be silently dropped.
    With the fix both pages are consumed and the final historyId reflects
    the last page.
    """
    mock_get_token.return_value = "mock_token"

    user = User(email="pageuser@enterprise.com", full_name="Page User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_page_test",
        encrypted_access_token=encrypt_token("mock_token"),
        encrypted_refresh_token=encrypt_token("mock_refresh"),
    )
    db_session.add(oauth_acc)
    db_session.commit()

    # Pre-set an existing last_history_id so incremental path is taken
    from backend.app.repositories.gmail_repository import GmailRepository
    GmailRepository.update_sync_state(
        db_session, user.id, sync_status="COMPLETED", last_history_id=1000500
    )

    # Page 1 returns nextPageToken; page 2 terminates the loop
    history_page_1 = {
        "history": [
            {
                "id": "1000600",
                "messagesAdded": [{"message": {"id": "msg_page1", "threadId": "thread_p1"}}],
            }
        ],
        "historyId": "1000600",
        "nextPageToken": "page2_token",
    }
    history_page_2 = {
        "history": [
            {
                "id": "1000700",
                "messagesAdded": [{"message": {"id": "msg_page2", "threadId": "thread_p2"}}],
            }
        ],
        "historyId": "1000700",
        # No nextPageToken — terminates the pagination loop
    }

    mock_client = AsyncMock(spec=GmailClient)
    mock_client.get_valid_access_token = MagicMock(return_value="mock_token")
    # First call (no page_token) returns page 1; second call (page_token="page2_token") returns page 2
    mock_client.list_history.side_effect = [history_page_1, history_page_2]
    mock_client.get_message.return_value = MOCK_MESSAGE_101_PAYLOAD

    sync_service = GmailSyncService(client=mock_client)
    res = await sync_service.execute_sync(db_session, user)

    assert res["status"] == "COMPLETED"
    assert res["type"] == "INCREMENTAL_HISTORY"
    # Both pages were consumed — messages_added should reflect both events
    assert res["messages_added"] == 2
    # Final historyId should be from the LAST page (1000700), not page 1 (1000600)
    assert res["last_history_id"] == 1000700

    # Verify list_history was called twice: once without page_token, once with
    assert mock_client.list_history.call_count == 2
    first_call_kwargs = mock_client.list_history.call_args_list[0]
    second_call_kwargs = mock_client.list_history.call_args_list[1]
    # Second call must pass the page token from page 1
    assert second_call_kwargs.kwargs.get("page_token") == "page2_token" or (
        len(second_call_kwargs.args) >= 3 and second_call_kwargs.args[2] == "page2_token"
    )


# ---------------------------------------------------------------------------
# FIX-SYNC-5: Per-message error isolation — one bad message must not abort sync
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("backend.app.integrations.gmail.GmailClient.get_valid_access_token")
async def test_initial_sync_one_failing_message_does_not_abort(
    mock_get_token,
    db_session: Session,
):
    """FIX-SYNC-5: A single get_message failure in initial sync is isolated.

    The remaining messages must still be persisted and sync must reach COMPLETED.
    Before the fix, one bad message would bubble up and abort the entire sync.
    """
    mock_get_token.return_value = "mock_token"

    user = User(email="isofailuser@enterprise.com", full_name="Iso Fail User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_isofail_test",
        encrypted_access_token=encrypt_token("mock_token"),
        encrypted_refresh_token=encrypt_token("mock_refresh"),
    )
    db_session.add(oauth_acc)
    db_session.commit()

    mock_client = AsyncMock(spec=GmailClient)
    mock_client.get_valid_access_token = MagicMock(return_value="mock_token")
    mock_client.get_profile.return_value = MOCK_GMAIL_PROFILE
    mock_client.list_messages.return_value = {
        "messages": [
            {"id": "msg_good_1", "threadId": "thread_a"},
            {"id": "msg_bad",    "threadId": "thread_b"},  # This one will fail
            {"id": "msg_good_2", "threadId": "thread_c"},
        ]
    }

    from backend.app.integrations.gmail import GmailAPIError

    def get_message_side_effect(token, msg_id):
        if msg_id == "msg_bad":
            raise GmailAPIError(500, "Internal Server Error from Gmail")
        return MOCK_MESSAGE_101_PAYLOAD

    mock_client.get_message.side_effect = get_message_side_effect

    sync_service = GmailSyncService(client=mock_client)
    res = await sync_service.execute_sync(db_session, user)

    # Overall sync must COMPLETE — not abort due to one bad message
    assert res["status"] == "COMPLETED"
    assert res["type"] == "INITIAL_BASELINE"
    # 2 good messages processed, 1 skipped
    assert res["messages_synced"] == 2
    assert res["failed_count"] == 1

    # Partial failure note must be recorded in DB
    from backend.app.repositories.gmail_repository import GmailRepository
    state = GmailRepository.get_or_create_sync_state(db_session, user.id)
    assert state.sync_status == "COMPLETED"
    assert state.error_message is not None
    assert "1" in state.error_message  # "Skipped 1 message(s)..."


@pytest.mark.anyio
@patch("backend.app.integrations.gmail.GmailClient.get_valid_access_token")
async def test_incremental_sync_one_failing_message_does_not_abort(
    mock_get_token,
    db_session: Session,
):
    """FIX-SYNC-5: A single get_message failure in incremental sync is isolated.

    Other messagesAdded events and label/delete events must still be processed.
    """
    mock_get_token.return_value = "mock_token"

    user = User(email="inciso@enterprise.com", full_name="Inc Iso User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_inciso_test",
        encrypted_access_token=encrypt_token("mock_token"),
        encrypted_refresh_token=encrypt_token("mock_refresh"),
    )
    db_session.add(oauth_acc)
    db_session.commit()

    from backend.app.repositories.gmail_repository import GmailRepository
    GmailRepository.update_sync_state(
        db_session, user.id, sync_status="COMPLETED", last_history_id=1000500
    )

    history_with_mixed_events = {
        "history": [
            {
                "id": "1000600",
                "messagesAdded": [{"message": {"id": "msg_good_inc", "threadId": "thread_g"}}],
            },
            {
                "id": "1000601",
                "messagesAdded": [{"message": {"id": "msg_bad_inc", "threadId": "thread_b"}}],
            },
        ],
        "historyId": "1000601",
    }

    from backend.app.integrations.gmail import GmailAPIError

    mock_client = AsyncMock(spec=GmailClient)
    mock_client.get_valid_access_token = MagicMock(return_value="mock_token")
    mock_client.list_history.return_value = history_with_mixed_events

    def get_message_side_effect(token, msg_id):
        if msg_id == "msg_bad_inc":
            raise GmailAPIError(404, "Message not found")
        return MOCK_MESSAGE_101_PAYLOAD

    mock_client.get_message.side_effect = get_message_side_effect

    sync_service = GmailSyncService(client=mock_client)
    res = await sync_service.execute_sync(db_session, user)

    assert res["status"] == "COMPLETED"
    assert res["type"] == "INCREMENTAL_HISTORY"
    # 1 good message added, 1 failed
    assert res["messages_added"] == 1
    assert res["failed_count"] == 1
    # historyId must advance even with partial failure
    assert res["last_history_id"] == 1000601

    state = GmailRepository.get_or_create_sync_state(db_session, user.id)
    assert state.sync_status == "COMPLETED"
    assert state.error_message is not None
    assert state.last_history_id == 1000601
