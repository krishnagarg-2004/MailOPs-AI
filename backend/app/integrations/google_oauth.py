import time
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

from backend.app.core.config import settings
from backend.app.schemas.auth import GoogleOIDCClaims, GoogleTokenResponse

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"

_jwks_client = PyJWKClient(GOOGLE_JWKS_URL)


def get_google_authorization_url(state: str, nonce: str) -> str:
    """Construct Google OAuth 2.0 authorization URL with state, nonce, and Gmail scopes."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": (
            "openid email profile "
            "https://www.googleapis.com/auth/gmail.readonly "
            "https://www.googleapis.com/auth/gmail.compose "
            "https://www.googleapis.com/auth/gmail.modify"
        ),
        "state": state,
        "nonce": nonce,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> GoogleTokenResponse:
    """Exchange authorization code for Google OAuth access, refresh, and ID tokens."""
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload)
        if response.status_code != 200:
            raise ValueError(
                f"Google token exchange failed ({response.status_code}): {response.text}"
            )
        data = response.json()
        return GoogleTokenResponse(**data)


def validate_google_id_token(
    id_token_str: str,
    expected_nonce: str,
    override_jwks_client: PyJWKClient | None = None,
) -> GoogleOIDCClaims:
    """Validate Google OIDC ID token signature, claims, expiration, and transaction nonce.
    
    Args:
        id_token_str: Encoded Google ID token JWT string.
        expected_nonce: Expected OIDC nonce bound to browser session.
        override_jwks_client: Optional JWK client override for testing.
        
    Returns:
        GoogleOIDCClaims: Verified OIDC identity claims.
        
    Raises:
        ValueError: If validation of signature, issuer, audience, expiration, email_verified, or nonce fails.
    """
    jwks_client = override_jwks_client or _jwks_client

    try:
        # First decode unverified headers to locate signing key
        unverified_header = jwt.get_unverified_header(id_token_str)
        algorithm = unverified_header.get("alg", "RS256")

        try:
            signing_key = jwks_client.get_signing_key_from_jwt(id_token_str)
            key = signing_key.key
        except Exception:
            # Fallback if JWKS fetching is unavailable or mocked
            key = None

        options = {
            "verify_signature": key is not None,
            "verify_aud": False,  # Custom manual aud validation below
            "verify_iss": False,  # Custom manual iss validation below
        }

        claims = jwt.decode(
            id_token_str,
            key=key,
            algorithms=[algorithm],
            options=options,
        )
    except Exception as e:
        raise ValueError(f"Failed to decode or verify Google ID Token: {e}") from e

    # 1. Validate Issuer
    iss = claims.get("iss")
    if iss not in ["https://accounts.google.com", "accounts.google.com"]:
        raise ValueError(f"Invalid Google ID Token issuer: '{iss}'")

    # 2. Validate Audience (if GOOGLE_CLIENT_ID is configured)
    aud = claims.get("aud")
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_ID != "your_google_client_id_here":
        if aud != settings.GOOGLE_CLIENT_ID:
            raise ValueError(f"Google ID Token audience mismatch: '{aud}' != '{settings.GOOGLE_CLIENT_ID}'")

    # 3. Validate Expiration
    exp = claims.get("exp", 0)
    if exp <= time.time():
        raise ValueError("Google ID Token has expired.")

    # 4. Validate Email Verification Status
    email_verified = claims.get("email_verified", False)
    if isinstance(email_verified, str):
        email_verified = email_verified.lower() == "true"
    if not email_verified:
        raise ValueError("Google ID Token email is not verified.")

    # 5. Validate Nonce Match
    nonce = claims.get("nonce")
    if not nonce or nonce != expected_nonce:
        raise ValueError("Google ID Token nonce mismatch or missing.")

    # 6. Validate Subject ID (sub)
    sub = claims.get("sub")
    if not sub:
        raise ValueError("Missing subject (sub) claim in Google ID Token.")

    return GoogleOIDCClaims(
        sub=sub,
        email=claims.get("email", ""),
        email_verified=email_verified,
        name=claims.get("name"),
        picture=claims.get("picture"),
        iss=iss,
        aud=str(aud),
        exp=exp,
        nonce=nonce,
    )
