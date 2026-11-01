import logging

from fastapi import APIRouter, Depends, Request, Response, status
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


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

OAUTH_STATE_COOKIE = "mailops_oauth_state"


@router.get(
    "/google/login",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def google_login(return_to: str | None = None):
    """Initiate Google OAuth 2.0 flow with standard read-only scopes."""

    signed_state, raw_state, nonce = generate_oauth_state(
        return_to=return_to
    )

    auth_url = get_google_authorization_url(
        state=signed_state,
        nonce=nonce,
        include_compose=False,
    )

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
        max_age=600,
        path="/",
    )

    return response


@router.get(
    "/google/authorize-compose",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def google_authorize_compose(
    return_to: str | None = None,
):
    """Initiate Google OAuth flow requesting gmail.compose scope."""

    signed_state, raw_state, nonce = generate_oauth_state(
        return_to=return_to
    )

    auth_url = get_google_authorization_url(
        state=signed_state,
        nonce=nonce,
        include_compose=True,
    )

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
        max_age=600,
        path="/",
    )

    return response


@router.get(
    "/google/callback",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Process Google OAuth callback.

    1. Handle OAuth errors.
    2. Verify OAuth state.
    3. Exchange authorization code for tokens.
    4. Validate Google ID token.
    5. Authenticate or create the user.
    6. Create an application session.
    7. Set the session cookie.
    8. Redirect to the frontend dashboard.
    """

    fallback_redirect = f"{settings.FRONTEND_URL}/login"

    # Google OAuth returned an error
    if error:
        return RedirectResponse(
            url=f"{fallback_redirect}?error={error}",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    # Missing required OAuth parameters
    if not code or not state:
        return RedirectResponse(
            url=f"{fallback_redirect}?error=missing_code_or_state",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    # Get browser-bound OAuth state cookie
    browser_state_cookie = request.cookies.get(
        OAUTH_STATE_COOKIE
    )

    # Verify OAuth state
    try:
        return_to, expected_nonce = verify_oauth_state(
            signed_state_param=state,
            expected_raw_state=browser_state_cookie,
            max_age=600,
        )

    except ValueError as e:
        # FIX-AUTH-3: Structured logging — no sensitive data logged.
        logger.warning(
            "OAuth state validation failed: %s: %s",
            type(e).__name__,
            e,
        )

        return RedirectResponse(
            url=f"{fallback_redirect}?error=invalid_state",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    # Process Google authentication
    try:
        # Exchange authorization code for OAuth tokens
        token_resp = await exchange_code_for_tokens(
            code
        )

        # Validate Google OIDC ID token
        claims = validate_google_id_token(
            id_token_str=token_resp.id_token,
            expected_nonce=expected_nonce,
        )

        # Authenticate existing user or create a new one
        user = authenticate_google_user(
            db,
            claims,
            token_resp,
        )

        # Get request information
        ip_addr = (
            request.client.host
            if request.client
            else None
        )

        user_agent = request.headers.get(
            "user-agent"
        )

        # Create application session
        raw_session_token, _ = create_user_session(
            db=db,
            user=user,
            ip_address=ip_addr,
            user_agent=user_agent,
        )

    except Exception as e:
        # FIX-AUTH-3: Structured logging — exception type only, no tokens or codes.
        logger.warning(
            "Google authentication failed: %s: %s",
            type(e).__name__,
            e,
        )

        return RedirectResponse(
            url=f"{fallback_redirect}?error=auth_failed",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    # Determine where the frontend should redirect
    target_url = (
        f"{settings.FRONTEND_URL}{return_to}"
        if return_to
        else f"{settings.FRONTEND_URL}/dashboard"
    )

    # Create redirect response
    response = RedirectResponse(
        url=target_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )

    # Remove temporary OAuth state cookie
    response.delete_cookie(
        key=OAUTH_STATE_COOKIE,
        path="/",
    )

    # Set authenticated session cookie
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


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Return currently authenticated user profile."""

    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Revoke active session and clear authentication cookies."""

    cookie_name = settings.SESSION_COOKIE_NAME

    session_token = request.cookies.get(
        cookie_name
    )

    # Backward compatibility with the old cookie name
    if (
        not session_token
        and cookie_name != "mailops_session"
    ):
        session_token = request.cookies.get(
            "mailops_session"
        )

    if session_token:
        revoke_session(
            db,
            session_token,
        )

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
    )

    response.delete_cookie(
        key="mailops_session",
        path="/",
    )

    return {
        "status": "logged_out"
    }