"""
Nidhi — Symmetric Token Encryption
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import get_settings

settings = get_settings()


def _get_fernet() -> Fernet:
    """Derive a 32-byte URL-safe base64 key from settings.secret_key."""
    key_hash = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    key_b64 = base64.urlsafe_b64encode(key_hash)
    return Fernet(key_b64)


def encrypt_token(token: str | None) -> str:
    """Encrypt a string token securely."""
    if not token:
        return ""
    f = _get_fernet()
    return f.encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str | None) -> str:
    """Decrypt a string token securely."""
    if not encrypted_token:
        return ""
    f = _get_fernet()
    return f.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
