"""Shared upload temp files visible to API and Celery workers (same volume mount)."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path


def _default_upload_tmp_dir() -> Path:
    """Prefer appuser cache (writable on Docker); fall back to system temp."""
    home_cache = Path.home() / ".cache" / "linguaielts-uploads" / "tmp"
    if home_cache.parent.parent.exists():
        return home_cache
    return Path(tempfile.gettempdir()) / "linguaielts-uploads" / "tmp"


def upload_tmp_dir() -> Path:
    override = (os.environ.get("UPLOAD_TMP_DIR") or "").strip()
    if override:
        return Path(override)
    return _default_upload_tmp_dir()


def ensure_upload_tmp_dir() -> Path:
    path = upload_tmp_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_shared_upload(audio_bytes: bytes, suffix: str) -> str:
    """Write bytes to a writable temp dir and return absolute path."""
    ensure_upload_tmp_dir()
    ext = suffix if suffix.startswith(".") else f".{suffix}"
    path = upload_tmp_dir() / f"{uuid.uuid4().hex}{ext}"
    path.write_bytes(audio_bytes)
    return str(path)
