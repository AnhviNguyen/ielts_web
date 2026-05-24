"""Resolve quiz audio/image assets from S3 or local disk."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.core.config import settings
from app.core.storage import get_storage

_AUDIO_DIR = Path(__file__).resolve().parents[2] / "data" / "assets" / "audio"
_IMAGE_DIR = Path(__file__).resolve().parents[2] / "data" / "assets" / "images"

AUDIO_EXTENSIONS = (".mp3", ".m4a", ".ogg", ".wav")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

AUDIO_MEDIA = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
}
IMAGE_MEDIA = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


@dataclass(frozen=True)
class MediaAsset:
    source: Literal["s3", "local"]
    content_type: str
    key: str | None = None
    local_path: Path | None = None
    public_url: str | None = None


def _stem(file_id: str) -> str:
    return file_id.split(".")[0]


def resolve_audio(file_id: str) -> MediaAsset | None:
    stem = _stem(file_id)
    if settings.STORAGE_BACKEND.lower() == "s3":
        storage = get_storage()
        for ext in AUDIO_EXTENSIONS:
            key = f"assets/audio/{stem}{ext}"
            if storage.exists(key):
                return MediaAsset(
                    source="s3",
                    key=key,
                    content_type=AUDIO_MEDIA[ext],
                    public_url=storage.public_url(key),
                )
    for ext in AUDIO_EXTENSIONS:
        candidate = _AUDIO_DIR / f"{stem}{ext}"
        if candidate.is_file():
            return MediaAsset(
                source="local",
                local_path=candidate,
                content_type=AUDIO_MEDIA[ext],
            )
    return None


def resolve_image(file_id: str) -> MediaAsset | None:
    stem = _stem(file_id)
    if settings.STORAGE_BACKEND.lower() == "s3":
        storage = get_storage()
        for ext in IMAGE_EXTENSIONS:
            key = f"assets/images/{stem}{ext}"
            if storage.exists(key):
                return MediaAsset(
                    source="s3",
                    key=key,
                    content_type=IMAGE_MEDIA[ext],
                    public_url=storage.public_url(key),
                )
    for ext in IMAGE_EXTENSIONS:
        candidate = _IMAGE_DIR / f"{stem}{ext}"
        if candidate.is_file():
            return MediaAsset(
                source="local",
                local_path=candidate,
                content_type=IMAGE_MEDIA[ext],
            )
    return None
