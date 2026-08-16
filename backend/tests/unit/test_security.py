import pytest
from backend.app.core.security import (
    generate_nonce,
    generate_oauth_state,
    generate_session_token,
    hash_session_token,
    validate_return_to,
    verify_oauth_state,
)


def test_session_token_generation_and_hashing():
    """Verify session tokens are unguessable and produce consistent SHA-256 digests."""
    token1 = generate_session_token()
    token2 = generate_session_token()

    assert len(token1) >= 40
    assert token1 != token2

    hash1 = hash_session_token(token1)
    hash1_repeat = hash_session_token(token1)
    hash2 = hash_session_token(token2)

    assert len(hash1) == 64  # SHA-256 hex string length
    assert hash1 == hash1_repeat
    assert hash1 != hash2


def test_generate_nonce():
    """Verify OIDC nonce generation produces unguessable tokens."""
    n1 = generate_nonce()
    n2 = generate_nonce()
    assert len(n1) >= 40
    assert n1 != n2


def test_oauth_state_generation_and_browser_binding():
    """Verify signed OAuth state generation and browser-binding verification."""
    signed_state, raw_state, nonce = generate_oauth_state(return_to="/dashboard", nonce="test_nonce_123")

    assert signed_state is not None
    assert raw_state is not None
    assert nonce == "test_nonce_123"

    # Successful verification matching browser cookie
    return_to, verified_nonce = verify_oauth_state(
        signed_state_param=signed_state,
        expected_raw_state=raw_state,
    )
    assert return_to == "/dashboard"
    assert verified_nonce == "test_nonce_123"


def test_oauth_state_mismatch_raises_value_error():
    """Verify state verification fails if browser cookie state does not match."""
    signed_state, raw_state, nonce = generate_oauth_state(return_to="/dashboard")

    with pytest.raises(ValueError, match="OAuth state browser-binding mismatch"):
        verify_oauth_state(
            signed_state_param=signed_state,
            expected_raw_state="differing_raw_state_cookie",
        )


def test_open_redirect_prevention():
    """Verify validate_return_to blocks external malicious return_to URLs."""
    assert validate_return_to("/dashboard") == "/dashboard"
    assert validate_return_to("/settings/profile") == "/settings/profile"
    assert validate_return_to("https://evil.com") is None
    assert validate_return_to("//evil.com") is None
    assert validate_return_to("javascript:alert(1)") is None
