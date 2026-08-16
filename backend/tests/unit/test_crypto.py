import pytest
from backend.app.core.crypto import decrypt_token, encrypt_token


def test_encrypt_decrypt_token_roundtrip():
    """Verify Fernet encryption and decryption roundtrip for plaintext tokens."""
    plaintext = "ya29.a0Axoo87654321_sample_google_access_token_xyz"
    encrypted = encrypt_token(plaintext)

    assert encrypted is not None
    assert encrypted != plaintext

    decrypted = decrypt_token(encrypted)
    assert decrypted == plaintext


def test_encrypt_decrypt_none_or_empty():
    """Verify encrypt and decrypt return None when input is None or empty."""
    assert encrypt_token(None) is None
    assert encrypt_token("") is None
    assert decrypt_token(None) is None
    assert decrypt_token("") is None


def test_decrypt_invalid_ciphertext_raises_value_error():
    """Verify attempting to decrypt invalid ciphertext raises ValueError."""
    with pytest.raises(ValueError, match="Failed to decrypt OAuth token"):
        decrypt_token("invalid_ciphertext_payload_123")
