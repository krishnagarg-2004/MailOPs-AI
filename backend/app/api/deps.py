from typing import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.auth_service import validate_session


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to extract and validate current authenticated user from session cookie.
    
    Reads session token from HttpOnly cookie (mailops_session / __Host-mailops_session)
    and validates session against PostgreSQL database records.
    
    Raises:
        HTTPException 401: If session cookie is missing, invalid, expired, or revoked.
    """
    cookie_name = settings.SESSION_COOKIE_NAME
    session_token = request.cookies.get(cookie_name)

    # Fallback to dev cookie name if main cookie name not found
    if not session_token and cookie_name != "mailops_session":
        session_token = request.cookies.get("mailops_session")

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing session cookie.",
        )

    try:
        _, user = validate_session(db, session_token)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired session: {e}",
        ) from e
