from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy.orm import Session

from backend.app.core.crypto import encrypt_token, decrypt_token
from backend.app.integrations.gmail import GmailClient
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.tests.integration.test_database import db_session, test_engine


def test_get_valid_access_token_returns_existing_unexpired_token(db_session: Session):
    """Verify get_valid_access_token returns unexpired access token without network call."""
    user = User(email="tokenuser@enterprise.com", full_name="Token User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_token_test",
        encrypted_access_token=encrypt_token("valid_access_token_123"),
        encrypted_refresh_token=encrypt_token("valid_refresh_token_123"),
        token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(oauth_acc)
    db_session.commit()

    token = GmailClient.get_valid_access_token(db_session, oauth_acc)
    assert token == "valid_access_token_123"


@patch("httpx.Client.post")
def test_get_valid_access_token_refreshes_expired_token(mock_post, db_session: Session):
    """Verify expired access token triggers Google OAuth token endpoint refresh."""
    user = User(email="refreshuser@enterprise.com", full_name="Refresh User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_refresh_test",
        encrypted_access_token=encrypt_token("old_access_token"),
        encrypted_refresh_token=encrypt_token("valid_refresh_token_123"),
        token_expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),  # Expired
    )
    db_session.add(oauth_acc)
    db_session.commit()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "new_refreshed_access_token_999",
        "expires_in": 3600,
    }
    mock_post.return_value = mock_resp

    new_token = GmailClient.get_valid_access_token(db_session, oauth_acc)
    assert new_token == "new_refreshed_access_token_999"

    # Verify updated token in database is encrypted
    db_session.refresh(oauth_acc)
    assert oauth_acc.encrypted_access_token != "new_refreshed_access_token_999"
    assert decrypt_token(oauth_acc.encrypted_access_token) == "new_refreshed_access_token_999"


@patch("httpx.Client.post")
def test_get_valid_access_token_invalid_grant_revocation_clears_tokens(mock_post, db_session: Session):
    """Verify invalid_grant response clears encrypted access token and raises ValueError."""
    user = User(email="revokeduser@enterprise.com", full_name="Revoked User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="sub_revoked_test",
        encrypted_access_token=encrypt_token("old_access_token"),
        encrypted_refresh_token=encrypt_token("revoked_refresh_token"),
        token_expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    db_session.add(oauth_acc)
    db_session.commit()

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"error": "invalid_grant"}
    mock_post.return_value = mock_resp

    with pytest.raises(ValueError, match="Google authorization revoked or expired"):
        GmailClient.get_valid_access_token(db_session, oauth_acc)

    db_session.refresh(oauth_acc)
    assert oauth_acc.encrypted_access_token is None
