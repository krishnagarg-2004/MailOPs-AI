from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.core.security import generate_oauth_state, verify_oauth_state
from backend.app.db.session import get_db
from backend.app.integrations.google_oauth import (
    exchange_code_for_tokens,
    get_google_authorization_url,
    validate_google_id_token,
)
from backend.app.models.user import User
from backend.app.schemas.user import UserResponse
from backend.app.services.auth_service import (
    authenticate_google_user,
    create_user_session,
    revoke_session,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

OAUTH_STATE_COOKIE = "mailops_oauth_state"


@router.get("/google/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def google_login(return_to: str | None = None):
    """Initiate Google OAuth 2.0 flow with standard read-only scopes."""
    signed_state, raw_state, nonce = generate_oauth_state(return_to=return_to)
    auth_url = get_google_authorization_url(state=signed_state, nonce=nonce, include_compose=False)

    response = RedirectResponse(
        url=auth_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=raw_state,
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        max_age=600,  # 10 minutes
        path="/",
    )
    return response


@router.get("/google/authorize-compose", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def google_authorize_compose(return_to: str | None = None):
    """Initiate Google OAuth 2.0 flow requesting incremental `gmail.compose` scope."""
    signed_state, raw_state, nonce = generate_oauth_state(return_to=return_to)
    auth_url = get_google_authorization_url(state=signed_state, nonce=nonce, include_compose=True)

    response = RedirectResponse(
        url=auth_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=raw_state,
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        max_age=600,  # 10 minutes
        path="/",
    )
    return response



@router.get("/google/callback", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """Process Google OAuth 2.0 callback.
    
    1. Handles OAuth consent errors (access_denied).
    2. Verifies signed `state` parameter against browser-bound `mailops_oauth_state` cookie.
    3. Exchanges authorization `code` for Google OAuth tokens via HTTP POST.
    4. Validates OIDC ID Token signature, issuer, audience, expiration, email_verified, and nonce.
    5. Resolves/registers User & OAuthAccount in PostgreSQL with Fernet token encryption at rest.
    6. Generates a NEW 256-bit session token, stores SHA-256 hash in `sessions` table.
    7. Clears OAuth state cookie and sets `mailops_session` HttpOnly cookie.
    8. Issues HTTP 307 redirect to frontend dashboard.
    """
    fallback_redirect = f"{settings.FRONTEND_URL}/login"

    if error:
        return RedirectResponse(
            url=f"{fallback_redirect}?error={error}",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{fallback_redirect}?error=missing_code_or_state",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    browser_state_cookie = request.cookies.get(OAUTH_STATE_COOKIE)

    try:
        return_to, expected_nonce = verify_oauth_state(
            signed_state_param=state,
            expected_raw_state=browser_state_cookie,
            max_age=600,
        )
    except ValueError as e:
        return RedirectResponse(
            url=f"{fallback_redirect}?error=invalid_state",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    try:
        # Exchange authorization code for tokens
        token_resp = await exchange_code_for_tokens(code)

        # Validate Google OIDC ID Token claims & transaction nonce
        claims = validate_google_id_token(
            id_token_str=token_resp.id_token,
            expected_nonce=expected_nonce,
        )

        # Authenticate / link User & OAuthAccount
        user = authenticate_google_user(db, claims, token_resp)

        # Create NEW database session (Session ID Regeneration)
        ip_addr = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        raw_session_token, _ = create_user_session(
            db=db,
            user=user,
            ip_address=ip_addr,
            user_agent=user_agent,
        )

    except Exception:
        return RedirectResponse(
            url=f"{fallback_redirect}?error=auth_failed",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    target_url = f"{settings.FRONTEND_URL}{return_to}" if return_to else f"{settings.FRONTEND_URL}/dashboard"
    response = RedirectResponse(
        url=target_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )

    # Clear state cookie
    response.delete_cookie(key=OAUTH_STATE_COOKIE, path="/")

    # Set authenticated HttpOnly session cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_session_token,
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        path="/",
    )

    return response


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return currently authenticated user profile."""
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Revoke active database session and clear session cookie."""
    cookie_name = settings.SESSION_COOKIE_NAME
    session_token = request.cookies.get(cookie_name)
    if not session_token and cookie_name != "mailops_session":
        session_token = request.cookies.get("mailops_session")

    if session_token:
        revoke_session(db, session_token)

    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(key="mailops_session", path="/")
    return {"status": "logged_out"}
