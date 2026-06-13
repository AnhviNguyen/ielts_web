"""Resolve quiz audio/image assets from Cloudinary, S3, or local disk."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.core.cloudinary_storage import cloudinary_public_url
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
    source: Literal["s3", "local", "cloudinary"]
    content_type: str
    key: str | None = None
    local_path: Path | None = None
    public_url: str | None = None


def _stem(file_id: str) -> str:
    return file_id.split(".")[0]


def _stem_variants(stem: str) -> list[str]:
    """Match local files saved with dashed UUIDs when JSON uses hex-only ids."""
    variants = [stem]
    if len(stem) == 32 and "-" not in stem:
        variants.append(f"{stem[:8]}-{stem[8:12]}-{stem[12:16]}-{stem[16:20]}-{stem[20:]}")
    elif stem.count("-") == 4:
        variants.append(stem.replace("-", ""))
    return variants


def _find_local_audio(stem: str) -> MediaAsset | None:
    for candidate_stem in _stem_variants(stem):
        for ext in AUDIO_EXTENSIONS:
            candidate = _AUDIO_DIR / f"{candidate_stem}{ext}"
            if candidate.is_file():
                return MediaAsset(
                    source="local",
                    local_path=candidate,
                    content_type=AUDIO_MEDIA[ext],
                )
    return None


def _find_local_image(stem: str) -> MediaAsset | None:
    for candidate_stem in _stem_variants(stem):
        for ext in IMAGE_EXTENSIONS:
            candidate = _IMAGE_DIR / f"{candidate_stem}{ext}"
            if candidate.is_file():
                return MediaAsset(
                    source="local",
                    local_path=candidate,
                    content_type=IMAGE_MEDIA[ext],
                )
    return None


def _resolve_cloudinary_audio(stem: str) -> MediaAsset | None:
    public_id = f"audio/{stem}"
    ext = ".mp3"
    return MediaAsset(
        source="cloudinary",
        key=public_id,
        content_type=AUDIO_MEDIA[ext],
        public_url=cloudinary_public_url(public_id, "video", ext),
    )


def _resolve_cloudinary_image(stem: str) -> MediaAsset | None:
    public_id = f"images/{stem}"
    ext = ".png"
    return MediaAsset(
        source="cloudinary",
        key=public_id,
        content_type=IMAGE_MEDIA[ext],
        public_url=cloudinary_public_url(public_id, "image", ext),
    )


def resolve_audio(file_id: str) -> MediaAsset | None:
    stem = _stem(file_id)
    backend = settings.STORAGE_BACKEND.lower()
    if backend == "cloudinary":
        return _resolve_cloudinary_audio(stem)
    if backend == "s3":
        storage = get_storage()
        for candidate_stem in _stem_variants(stem):
            for ext in AUDIO_EXTENSIONS:
                key = f"assets/audio/{candidate_stem}{ext}"
                if storage.exists(key):
                    return MediaAsset(
                        source="s3",
                        key=key,
                        content_type=AUDIO_MEDIA[ext],
                        public_url=storage.public_url(key),
                    )
    return _find_local_audio(stem)


def resolve_image(file_id: str) -> MediaAsset | None:
    stem = _stem(file_id)
    backend = settings.STORAGE_BACKEND.lower()
    if backend == "cloudinary":
        return _resolve_cloudinary_image(stem)
    if backend == "s3":
        storage = get_storage()
        for candidate_stem in _stem_variants(stem):
            for ext in IMAGE_EXTENSIONS:
                key = f"assets/images/{candidate_stem}{ext}"
                if storage.exists(key):
                    return MediaAsset(
                        source="s3",
                        key=key,
                        content_type=IMAGE_MEDIA[ext],
                        public_url=storage.public_url(key),
                    )
    return _find_local_image(stem)
