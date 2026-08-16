from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GoogleTokenResponse(BaseModel):
    """Pydantic schema representing Google OAuth token exchange response."""

    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    token_type: str = "Bearer"
    id_token: str


class GoogleOIDCClaims(BaseModel):
    """Pydantic schema representing verified Google OIDC ID token claims."""

    sub: str = Field(description="Google stable provider subject ID")
    email: str
    email_verified: bool = False
    name: Optional[str] = None
    picture: Optional[str] = None
    iss: str
    aud: str
    exp: int
    nonce: Optional[str] = None


class LoginResponse(BaseModel):
    """Pydantic schema for login response metadata."""

    authorization_url: str
    state: str
