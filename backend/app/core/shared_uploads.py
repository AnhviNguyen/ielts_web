"""Shared upload temp files visible to API and Celery workers (same volume mount)."""

from __future__ import annotations

import uuid
from pathlib import Path

UPLOAD_TMP_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads" / "tmp"


def ensure_upload_tmp_dir() -> Path:
    UPLOAD_TMP_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_TMP_DIR


def save_shared_upload(audio_bytes: bytes, suffix: str) -> str:
    """Write bytes under data/uploads/tmp and return absolute path."""
    ensure_upload_tmp_dir()
    ext = suffix if suffix.startswith(".") else f".{suffix}"
    path = UPLOAD_TMP_DIR / f"{uuid.uuid4().hex}{ext}"
    path.write_bytes(audio_bytes)
    return str(path)
