import hashlib
import re
import secrets
from typing import Optional, Tuple

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.app.core.config import settings

_state_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="mailops_oauth_state")

# Allowed return_to paths to prevent open redirect vulnerabilities
_SAFE_RETURN_TO_REGEX = re.compile(r"^/[a-zA-Z0-9_\-/]*$")


def generate_session_token() -> str:
    """Generate a cryptographically unguessable 256-bit URL-safe session token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Compute SHA-256 digest of a session token for indexed database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_nonce() -> str:
    """Generate a cryptographically random 256-bit URL-safe OIDC nonce."""
    return secrets.token_urlsafe(32)


def validate_return_to(return_to: Optional[str]) -> Optional[str]:
    """Validate and sanitize return_to path to prevent open redirect vulnerabilities."""
    if not return_to:
        return None
    cleaned = return_to.strip()
    if _SAFE_RETURN_TO_REGEX.match(cleaned) and not cleaned.startswith("//"):
        return cleaned
    return None


def generate_oauth_state(
    return_to: Optional[str] = None,
    nonce: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Generate a browser-bound, signed OAuth state parameter and OIDC nonce.
    
    Args:
        return_to: Optional sanitized return path after login.
        nonce: Optional OIDC nonce (generated if not provided).
        
    Returns:
        Tuple of (signed_state_param, raw_state_token, nonce).
    """
    raw_state = secrets.token_urlsafe(32)
    oidc_nonce = nonce if nonce else generate_nonce()
    safe_return_to = validate_return_to(return_to)

    payload = {
        "s": raw_state,
        "n": oidc_nonce,
        "r": safe_return_to,
    }
    signed_state = _state_serializer.dumps(payload)
    return signed_state, raw_state, oidc_nonce


def verify_oauth_state(
    signed_state_param: str,
    expected_raw_state: Optional[str],
    max_age: int = 600,
) -> Tuple[Optional[str], str]:
    """Verify signed OAuth state parameter against browser-bound state cookie.
    
    Args:
        signed_state_param: The `state` query parameter received in callback.
        expected_raw_state: The `mailops_oauth_state` browser cookie value.
        max_age: Maximum allowed age in seconds (default 600 = 10 minutes).
        
    Returns:
        Tuple of (sanitized_return_to, oidc_nonce).
        
    Raises:
        ValueError: If state signature is invalid, expired, or fails browser-binding match.
    """
    if not signed_state_param or not expected_raw_state:
        raise ValueError("Missing OAuth state parameter or browser state cookie.")

    try:
        payload = _state_serializer.loads(signed_state_param, max_age=max_age)
    except SignatureExpired as e:
        raise ValueError("OAuth state token has expired.") from e
    except BadSignature as e:
        raise ValueError("Invalid OAuth state token signature.") from e

    raw_state = payload.get("s")
    if not raw_state or not secrets.compare_digest(raw_state, expected_raw_state):
        raise ValueError("OAuth state browser-binding mismatch.")

    nonce = payload.get("n")
    if not nonce:
        raise ValueError("Missing OIDC nonce in state payload.")

    return payload.get("r"), nonce
