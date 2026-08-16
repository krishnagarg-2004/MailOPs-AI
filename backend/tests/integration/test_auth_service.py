from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from backend.app.core.crypto import decrypt_token
from backend.app.models.user import User
from backend.app.schemas.auth import GoogleOIDCClaims, GoogleTokenResponse
from backend.app.services.auth_service import (
    authenticate_google_user,
    create_user_session,
    revoke_session,
    validate_session,
)

# Test helper engine imports from integration setup
from backend.tests.integration.test_database import db_session, test_engine


def test_authenticate_google_user_new_registration(db_session: Session):
    """Verify new user registration via Google OIDC claims and encrypted token storage."""
    claims = GoogleOIDCClaims(
        sub="google_sub_1001",
        email="newuser@enterprise.com",
        email_verified=True,
        name="New User",
        picture="https://example.com/pic.jpg",
        iss="https://accounts.google.com",
        aud="test_client_id",
        exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        nonce="nonce_1001",
    )
    token_resp = GoogleTokenResponse(
        access_token="plain_access_token_1001",
        refresh_token="plain_refresh_token_1001",
        expires_in=3600,
        scope="openid email profile",
        id_token="mock_id_token",
    )

    user = authenticate_google_user(db_session, claims, token_resp)

    assert user is not None
    assert user.email == "newuser@enterprise.com"
    assert user.full_name == "New User"
    assert len(user.oauth_accounts) == 1

    oauth_acc = user.oauth_accounts[0]
    assert oauth_acc.provider == "google"
    assert oauth_acc.provider_account_id == "google_sub_1001"

    # Verify tokens are encrypted at rest
    assert oauth_acc.encrypted_access_token != "plain_access_token_1001"
    assert decrypt_token(oauth_acc.encrypted_access_token) == "plain_access_token_1001"
    assert decrypt_token(oauth_acc.encrypted_refresh_token) == "plain_refresh_token_1001"


def test_authenticate_google_user_unverified_email_raises_error(db_session: Session):
    """Verify registration or linking fails if email_verified is False."""
    claims = GoogleOIDCClaims(
        sub="google_sub_unverified",
        email="unverified@enterprise.com",
        email_verified=False,  # Unverified
        name="Unverified User",
        iss="https://accounts.google.com",
        aud="test_client_id",
        exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
    )
    token_resp = GoogleTokenResponse(
        access_token="access_123",
        expires_in=3600,
        id_token="mock_id_token",
    )

    with pytest.raises(ValueError, match="unverified Google email"):
        authenticate_google_user(db_session, claims, token_resp)


def test_user_session_lifecycle(db_session: Session):
    """Verify session creation, lookup, token hashing, and revocation."""
    user = User(email="sessionuser@enterprise.com", full_name="Session User")
    db_session.add(user)
    db_session.commit()

    # Create session
    raw_token, session_record = create_user_session(db_session, user, ip_address="127.0.0.1")

    assert raw_token is not None
    assert session_record.session_token_hash is not None
    assert session_record.session_token_hash != raw_token
    assert session_record.user_id == user.id
    assert session_record.revoked_at is None

    # Validate session
    valid_session, valid_user = validate_session(db_session, raw_token)
    assert valid_session.id == session_record.id
    assert valid_user.id == user.id

    # Revoke session
    revocation_success = revoke_session(db_session, raw_token)
    assert revocation_success is True

    # Validate revoked session raises error
    with pytest.raises(ValueError, match="Invalid or expired session"):
        validate_session(db_session, raw_token)
