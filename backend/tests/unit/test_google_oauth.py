"""Unit tests for backend.app.integrations.google_oauth — validate_google_id_token security.

Tests focus on:
- FIX-AUTH-1: JWKS unavailability must fail closed (never bypass signature verification)
- FIX-AUTH-4: Expiration validated by jwt.decode with leeway=60 (no inconsistent manual check)
- Nonce mismatch / issuer mismatch / unverified email rejection
- Source-level assertion that verify_signature=False is never present
"""
import time
from unittest.mock import MagicMock, patch

import pytest

from backend.app.integrations.google_oauth import validate_google_id_token


# A minimal valid JWT-format string (three base64url segments separated by dots).
# The actual content doesn't matter here because we mock jwt.get_unverified_header
# and jwt.decode entirely in the claims tests. For JWKS tests we let get_unverified_header
# run on a real (but invalid) token; the JWKS error should happen BEFORE that in the
# code flow — but jwt.get_unverified_header runs FIRST in validate_google_id_token.
# We use a valid-format mock token to ensure get_unverified_header succeeds.
import base64, json

def _make_mock_jwt(header=None, payload=None) -> str:
    """Create a JWT-format string with real base64url-encoded parts."""
    h = header or {"alg": "RS256", "kid": "test-kid"}
    p = payload or {"sub": "12345", "exp": int(time.time()) + 3600}
    def b64url(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    return f"{b64url(h)}.{b64url(p)}.mock-signature"


class TestJWKSFailsClosedOnUnavailability:
    """FIX-AUTH-1: JWKS failure must always raise ValueError — never bypass signature."""

    def test_jwks_network_failure_raises_value_error(self):
        """If JWKS client raises any exception, validate_google_id_token must raise ValueError."""
        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.side_effect = Exception("Network unreachable")

        with pytest.raises(ValueError, match="Failed to fetch Google JWKS signing key"):
            validate_google_id_token(
                id_token_str=_make_mock_jwt(),
                expected_nonce="any_nonce",
                override_jwks_client=mock_jwks_client,
            )

    def test_jwks_timeout_raises_value_error(self):
        """A timeout fetching JWKS must fail closed, not silently skip verification."""
        import httpx

        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.side_effect = Exception(
            "JWKS connect timed out"
        )

        with pytest.raises(ValueError, match="Failed to fetch Google JWKS signing key"):
            validate_google_id_token(
                id_token_str=_make_mock_jwt(),
                expected_nonce="any_nonce",
                override_jwks_client=mock_jwks_client,
            )

    def test_jwks_ssl_error_raises_value_error(self):
        """An SSL error fetching JWKS must fail closed."""
        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.side_effect = Exception(
            "SSL certificate verify failed"
        )

        with pytest.raises(ValueError, match="Failed to fetch Google JWKS signing key"):
            validate_google_id_token(
                id_token_str=_make_mock_jwt(),
                expected_nonce="any_nonce",
                override_jwks_client=mock_jwks_client,
            )

    def test_no_silent_fallback_to_unverified(self):
        """Verify that when JWKS fails, a ValueError is raised (never silently skips).
        This test does NOT check verify_signature=False — it checks that ValueError propagates."""
        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.side_effect = RuntimeError("DNS failure")

        # The function must raise — not return a claims object without verifying
        with pytest.raises(ValueError):
            validate_google_id_token(
                id_token_str=_make_mock_jwt(),
                expected_nonce="any_nonce",
                override_jwks_client=mock_jwks_client,
            )


class TestValidateGoogleIdTokenClaims:
    """Tests for claim validation: issuer, nonce, email_verified, sub.

    These tests mock both jwt.get_unverified_header and jwt.decode so we can
    control what claims are returned without needing a real RS256 key pair.
    """

    def _mock_jwks_client(self):
        mock_jwks_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = "test-secret-key-long-enough"
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
        return mock_jwks_client

    def _valid_claims(self, overrides=None) -> dict:
        claims = {
            "iss": "https://accounts.google.com",
            # Use empty string so audience validation is skipped (GOOGLE_CLIENT_ID must be falsy
            # or match; we patch settings.GOOGLE_CLIENT_ID below in each test)
            "aud": "test-client-id",
            "sub": "12345",
            "email": "test@example.com",
            "email_verified": True,
            "nonce": "test_nonce",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        if overrides:
            claims.update(overrides)
        return claims

    def test_invalid_issuer_raises(self):
        """Token with issuer other than accounts.google.com must be rejected."""
        claims = self._valid_claims({"iss": "https://evil.com"})
        with patch("backend.app.integrations.google_oauth.jwt") as mock_jwt, \
             patch("backend.app.integrations.google_oauth.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
            mock_jwt.get_unverified_header.return_value = {"alg": "HS256"}
            mock_jwt.decode.return_value = claims
            with pytest.raises(ValueError, match="Invalid Google ID Token issuer"):
                validate_google_id_token(
                    id_token_str=_make_mock_jwt(),
                    expected_nonce="test_nonce",
                    override_jwks_client=self._mock_jwks_client(),
                )

    def test_unverified_email_raises(self):
        """Token with email_verified=False must be rejected."""
        claims = self._valid_claims({"email_verified": False})
        with patch("backend.app.integrations.google_oauth.jwt") as mock_jwt, \
             patch("backend.app.integrations.google_oauth.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
            mock_jwt.get_unverified_header.return_value = {"alg": "HS256"}
            mock_jwt.decode.return_value = claims
            with pytest.raises(ValueError, match="email is not verified"):
                validate_google_id_token(
                    id_token_str=_make_mock_jwt(),
                    expected_nonce="test_nonce",
                    override_jwks_client=self._mock_jwks_client(),
                )

    def test_nonce_mismatch_raises(self):
        """Token nonce not matching expected_nonce must be rejected."""
        claims = self._valid_claims({"nonce": "correct_nonce"})
        with patch("backend.app.integrations.google_oauth.jwt") as mock_jwt, \
             patch("backend.app.integrations.google_oauth.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
            mock_jwt.get_unverified_header.return_value = {"alg": "HS256"}
            mock_jwt.decode.return_value = claims
            with pytest.raises(ValueError, match="nonce mismatch"):
                validate_google_id_token(
                    id_token_str=_make_mock_jwt(),
                    expected_nonce="wrong_nonce",
                    override_jwks_client=self._mock_jwks_client(),
                )

    def test_missing_sub_raises(self):
        """Token with missing sub claim must be rejected."""
        claims = self._valid_claims()
        del claims["sub"]
        with patch("backend.app.integrations.google_oauth.jwt") as mock_jwt, \
             patch("backend.app.integrations.google_oauth.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
            mock_jwt.get_unverified_header.return_value = {"alg": "HS256"}
            mock_jwt.decode.return_value = claims
            with pytest.raises(ValueError, match="Missing subject"):
                validate_google_id_token(
                    id_token_str=_make_mock_jwt(),
                    expected_nonce="test_nonce",
                    override_jwks_client=self._mock_jwks_client(),
                )

    def test_jwt_decode_called_with_leeway_60(self):
        """FIX-AUTH-4: jwt.decode is called with leeway=60 for clock-skew tolerance."""
        claims = self._valid_claims()
        with patch("backend.app.integrations.google_oauth.jwt") as mock_jwt, \
             patch("backend.app.integrations.google_oauth.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
            mock_jwt.get_unverified_header.return_value = {"alg": "HS256"}
            mock_jwt.decode.return_value = claims

            validate_google_id_token(
                id_token_str=_make_mock_jwt(),
                expected_nonce="test_nonce",
                override_jwks_client=self._mock_jwks_client(),
            )

            call_kwargs = mock_jwt.decode.call_args
            assert call_kwargs.kwargs.get("leeway") == 60, (
                f"jwt.decode must be called with leeway=60. Got: {call_kwargs}"
            )


class TestJWKSSignatureNeverSkipped:
    """Regression: verify_signature=False must never appear in the source."""

    def test_options_never_contains_verify_signature_false(self):
        """Inspect source — verify_signature=False must not be present anywhere."""
        import inspect
        from backend.app.integrations import google_oauth

        source = inspect.getsource(google_oauth)
        assert '"verify_signature": False' not in source
        assert "'verify_signature': False" not in source
        assert "verify_signature=False" not in source
