from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.crypto import encrypt_token
from backend.app.core.security import generate_session_token, hash_session_token
from backend.app.models.oauth import OAuthAccount
from backend.app.models.session import UserSession
from backend.app.models.user import User
from backend.app.schemas.auth import GoogleOIDCClaims, GoogleTokenResponse


def authenticate_google_user(
    db: Session,
    claims: GoogleOIDCClaims,
    token_resp: GoogleTokenResponse,
) -> User:
    """Authenticate or register a User via verified Google OIDC claims.
    
    ACCOUNT LINKING POLICY:
    1. Primary Lookup: Match existing `OAuthAccount` by `(provider='google', provider_account_id=claims.sub)`.
    2. Email Lookup (Strict Verification): If no OAuthAccount matches, query existing `User` by `email`
       ONLY IF `claims.email_verified == True`. If matched, link a new `OAuthAccount` to the existing `User`.
    3. New User Registration: If neither matches (and `email_verified == True`), create a new `User` entity
       and link a new `OAuthAccount` entity in a single atomic database transaction.
    """
    now = datetime.now(timezone.utc)
    token_expires_at = now + timedelta(seconds=token_resp.expires_in)

    # 1. Primary Lookup: provider + sub
    existing_oauth = db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == "google",
            OAuthAccount.provider_account_id == claims.sub,
        )
    ).scalar_one_or_none()

    if existing_oauth:
        # Update existing OAuth credentials
        existing_oauth.email = claims.email
        existing_oauth.encrypted_access_token = encrypt_token(token_resp.access_token)
        if token_resp.refresh_token:
            existing_oauth.encrypted_refresh_token = encrypt_token(token_resp.refresh_token)
        existing_oauth.token_expires_at = token_expires_at
        existing_oauth.scopes = token_resp.scope

        user = existing_oauth.user
        if claims.name and user.full_name != claims.name:
            user.full_name = claims.name
        if claims.picture and user.avatar_url != claims.picture:
            user.avatar_url = claims.picture

        db.commit()
        db.refresh(user)
        return user

    # 2. Strict Email Verification Requirement
    if not claims.email_verified:
        raise ValueError("Cannot link or create account with unverified Google email address.")

    # Secondary Lookup: match User by email
    existing_user = db.execute(
        select(User).where(User.email == claims.email)
    ).scalar_one_or_none()

    if existing_user:
        user = existing_user
    else:
        # 3. Register New User
        user = User(
            email=claims.email,
            full_name=claims.name,
            avatar_url=claims.picture,
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.flush()  # assign user.id

    # Create new linked OAuthAccount
    # FIX-AUTH-2: Guard against missing refresh_token — Google does not always
    # return a refresh token (e.g., when consent was previously granted without
    # prompt=consent). Never call encrypt_token(None).
    encrypted_refresh = (
        encrypt_token(token_resp.refresh_token)
        if token_resp.refresh_token
        else None
    )
    new_oauth = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id=claims.sub,
        email=claims.email,
        encrypted_access_token=encrypt_token(token_resp.access_token),
        encrypted_refresh_token=encrypted_refresh,
        token_expires_at=token_expires_at,
        scopes=token_resp.scope,
    )
    db.add(new_oauth)
    db.commit()
    db.refresh(user)
    return user


def create_user_session(
    db: Session,
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[str, UserSession]:
    """Generate a brand-new 256-bit session token and create a database session record.
    
    SECURITY RULE: Always generates a brand-new unguessable session token upon login.
    Only the SHA-256 hash of the session token is stored in PostgreSQL.
    """
    raw_session_token = generate_session_token()
    token_hash = hash_session_token(raw_session_token)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.SESSION_EXPIRE_HOURS)

    session_record = UserSession(
        session_token_hash=token_hash,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at,
        last_accessed_at=now,
        revoked_at=None,
    )
    db.add(session_record)
    db.commit()
    db.refresh(session_record)
    return raw_session_token, session_record


def validate_session(db: Session, raw_session_token: str) -> Tuple[UserSession, User]:
    """Validate raw session token against PostgreSQL database records.
    
    Args:
        db: Database session.
        raw_session_token: Raw session token from HttpOnly cookie.
        
    Returns:
        Tuple of (UserSession, User).
        
    Raises:
        ValueError: If session is invalid, expired, revoked, or user inactive.
    """
    if not raw_session_token:
        raise ValueError("Missing session token.")

    token_hash = hash_session_token(raw_session_token)
    now = datetime.now(timezone.utc)

    session_record = db.execute(
        select(UserSession).where(
            UserSession.session_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    ).scalar_one_or_none()

    if not session_record:
        raise ValueError("Invalid or expired session.")

    user = session_record.user
    if not user or not user.is_active:
        raise ValueError("User account is inactive or disabled.")

    # Touch last_accessed_at timestamp
    session_record.last_accessed_at = now
    db.commit()

    return session_record, user


def revoke_session(db: Session, raw_session_token: str) -> bool:
    """Revoke an active database session by setting revoked_at timestamp."""
    if not raw_session_token:
        return False

    token_hash = hash_session_token(raw_session_token)
    session_record = db.execute(
        select(UserSession).where(
            UserSession.session_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
        )
    ).scalar_one_or_none()

    if session_record:
        session_record.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return True
    return False
