import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, MultiFernet

from backend.app.core.config import settings


def _get_fernet_instance() -> MultiFernet:
    """Initialize Fernet encryption instance from application settings.
    
    Supports key rotation via comma-separated keys in ENCRYPTION_KEY environment variable.
    The first key is used for encryption; all keys are attempted for decryption.
    """
    key_str = settings.ENCRYPTION_KEY.strip() if settings.ENCRYPTION_KEY else ""
    if not key_str:
        key = Fernet.generate_key()
        return MultiFernet([Fernet(key)])

    keys = [k.strip() for k in key_str.split(",") if k.strip()]
    fernet_instances = []
    
    for k in keys:
        try:
            # Ensure valid base64 key
            decoded = base64.urlsafe_b64decode(k.encode("utf-8"))
            if len(decoded) != 32:
                digest = hashlib.sha256(k.encode("utf-8")).digest()
                valid_key = base64.urlsafe_b64encode(digest)
            else:
                valid_key = k.encode("utf-8")
            fernet_instances.append(Fernet(valid_key))
        except Exception:
            digest = hashlib.sha256(k.encode("utf-8")).digest()
            valid_key = base64.urlsafe_b64encode(digest)
            fernet_instances.append(Fernet(valid_key))

    return MultiFernet(fernet_instances)


_fernet = _get_fernet_instance()


def encrypt_token(token: Optional[str]) -> Optional[str]:
    """Encrypt a plaintext OAuth token for secure database persistence at rest.
    
    Args:
        token: Plaintext token string.
        
    Returns:
        Encrypted token ciphertext string, or None if token was None/empty.
    """
    if not token:
        return None
    encrypted_bytes = _fernet.encrypt(token.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_token(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt an encrypted OAuth token retrieved from the database boundary.
    
    Args:
        ciphertext: Encrypted token string.
        
    Returns:
        Decrypted plaintext token string, or None if input was None/empty.
    """
    if not ciphertext:
        return None
    try:
        decrypted_bytes = _fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt OAuth token: {e}") from e
