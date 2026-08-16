from unittest.mock import patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.security import generate_oauth_state
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.user import User
from backend.app.schemas.auth import GoogleOIDCClaims, GoogleTokenResponse
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




def test_google_login_endpoint_redirects_and_sets_cookie():
    """Verify GET /api/v1/auth/google/login sets browser state cookie and redirects (307) to Google."""
    response = client.get("/api/v1/auth/google/login?return_to=/dashboard", follow_redirects=False)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "mailops_oauth_state" in response.cookies


def test_google_callback_invalid_state_redirects_with_error():
    """Verify callback with invalid state parameter redirects to login with error."""
    response = client.get(
        "/api/v1/auth/google/callback?code=mock_code&state=invalid_signed_state",
        cookies={"mailops_oauth_state": "mock_cookie_state"},
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "error=invalid_state" in response.headers["location"]


@patch("backend.app.api.v1.auth.exchange_code_for_tokens")
@patch("backend.app.api.v1.auth.validate_google_id_token")
def test_google_callback_success_creates_session_and_redirects(
    mock_validate_oidc,
    mock_exchange_tokens,
    db_session,
):
    """Verify successful Google callback creates User, OAuthAccount, DB session, sets cookie, and redirects."""
    # 1. Generate valid signed state & matching cookie
    signed_state, raw_state, nonce = generate_oauth_state(return_to="/dashboard")

    # 2. Mock token exchange & OIDC claims
    mock_exchange_tokens.return_value = GoogleTokenResponse(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        expires_in=3600,
        id_token="mock_id_token",
    )
    mock_validate_oidc.return_value = GoogleOIDCClaims(
        sub="google_sub_api_test",
        email="apitest@enterprise.com",
        email_verified=True,
        name="API Test User",
        picture="https://example.com/avatar.png",
        iss="https://accounts.google.com",
        aud=settings.GOOGLE_CLIENT_ID,
        exp=9999999999,
        nonce=nonce,
    )

    response = client.get(
        f"/api/v1/auth/google/callback?code=valid_code&state={signed_state}",
        cookies={"mailops_oauth_state": raw_state},
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "/dashboard" in response.headers["location"]

    # Verify session cookie set
    cookie_name = settings.SESSION_COOKIE_NAME
    session_cookie = response.cookies.get(cookie_name) or response.cookies.get("mailops_session")
    assert session_cookie is not None


def test_get_me_unauthenticated():
    """Verify GET /api/v1/auth/me returns 401 Unauthorized when session cookie is missing."""
    client.cookies.clear()
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]



def test_get_me_authenticated_and_logout(db_session):
    """Verify GET /api/v1/auth/me returns user profile with valid cookie and POST /auth/logout revokes session."""
    user = User(email="testme@enterprise.com", full_name="Test Me")
    db_session.add(user)
    db_session.commit()

    raw_token, _ = create_user_session(db_session, user)
    cookie_name = settings.SESSION_COOKIE_NAME

    # 1. Test GET /auth/me with valid session cookie
    me_resp = client.get("/api/v1/auth/me", cookies={cookie_name: raw_token})
    assert me_resp.status_code == status.HTTP_200_OK
    assert me_resp.json()["email"] == "testme@enterprise.com"

    # 2. Test POST /auth/logout
    logout_resp = client.post("/api/v1/auth/logout", cookies={cookie_name: raw_token})
    assert logout_resp.status_code == status.HTTP_200_OK
    assert logout_resp.json()["status"] == "logged_out"

    # 3. Test subsequent GET /auth/me returns 401
    me_resp_after = client.get("/api/v1/auth/me", cookies={cookie_name: raw_token})
    assert me_resp_after.status_code == status.HTTP_401_UNAUTHORIZED


@patch("backend.app.api.v1.auth.exchange_code_for_tokens")
@patch("backend.app.api.v1.auth.validate_google_id_token")
def test_session_id_regeneration_on_login(
    mock_validate_oidc,
    mock_exchange_tokens,
    db_session,
):
    """Verify authenticated session token is newly generated and pre-auth token is never reused."""
    signed_state, raw_state, nonce = generate_oauth_state(return_to="/dashboard")

    mock_exchange_tokens.return_value = GoogleTokenResponse(
        access_token="mock_access",
        expires_in=3600,
        id_token="mock_id",
    )
    mock_validate_oidc.return_value = GoogleOIDCClaims(
        sub="sub_regen_test",
        email="regen@enterprise.com",
        email_verified=True,
        name="Regen User",
        iss="https://accounts.google.com",
        aud=settings.GOOGLE_CLIENT_ID,
        exp=9999999999,
        nonce=nonce,
    )

    pre_auth_cookie = "pre_auth_unauthenticated_session_token_xyz"
    response = client.get(
        f"/api/v1/auth/google/callback?code=valid_code&state={signed_state}",
        cookies={
            "mailops_oauth_state": raw_state,
            settings.SESSION_COOKIE_NAME: pre_auth_cookie,
        },
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    cookie_name = settings.SESSION_COOKIE_NAME
    post_auth_cookie = response.cookies.get(cookie_name) or response.cookies.get("mailops_session")

    assert post_auth_cookie is not None
    assert post_auth_cookie != pre_auth_cookie


@patch("backend.app.api.v1.auth.exchange_code_for_tokens")
@patch("backend.app.api.v1.auth.validate_google_id_token")
def test_google_callback_oidc_nonce_mismatch_fails(
    mock_validate_oidc,
    mock_exchange_tokens,
    db_session,
):
    """Verify callback fails if OIDC ID Token validation fails due to nonce mismatch."""
    signed_state, raw_state, nonce = generate_oauth_state()

    mock_exchange_tokens.return_value = GoogleTokenResponse(
        access_token="mock_access",
        expires_in=3600,
        id_token="mock_id",
    )
    mock_validate_oidc.side_effect = ValueError("Google ID Token nonce mismatch or missing.")

    response = client.get(
        f"/api/v1/auth/google/callback?code=valid_code&state={signed_state}",
        cookies={"mailops_oauth_state": raw_state},
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "error=auth_failed" in response.headers["location"]

