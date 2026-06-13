"""Encrypt/decrypt per-user AI API keys at rest."""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    digest = hashlib.sha256((settings.SECRET_KEY or "dev-secret").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_api_key(plain: str) -> str:
    return _fernet().encrypt(plain.strip().encode()).decode()


def decrypt_api_key(cipher: str) -> str:
    try:
        return _fernet().decrypt(cipher.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Invalid encrypted API key") from exc


def mask_api_key(key: str) -> str:
    key = (key or "").strip()
    if not key:
        return ""
    if len(key) <= 10:
        return "****"
    return f"{key[:4]}...{key[-4:]}"
