"""Cloudinary helpers for quiz audio/images and optional StorageBackend."""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_CONFIGURED = False


def ensure_cloudinary_configured() -> bool:
    """Configure cloudinary SDK once; return False if credentials missing."""
    global _CONFIGURED
    if _CONFIGURED:
        return True
    cloud_name = (settings.CLOUDINARY_CLOUD_NAME or "").strip()
    api_key = (settings.CLOUDINARY_API_KEY or "").strip()
    api_secret = (settings.CLOUDINARY_API_SECRET or "").strip()
    if not cloud_name or not api_key or not api_secret:
        return False
    try:
        import cloudinary

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        _CONFIGURED = True
        return True
    except Exception as exc:
        logger.warning("Cloudinary configure failed: %s", exc)
        return False


def cloudinary_public_url(public_id: str, resource_type: str, ext: str) -> str:
    """Build delivery URL: .../video/upload/audio/{uuid}.mp3 or .../image/upload/images/{uuid}.png"""
    cloud_name = (settings.CLOUDINARY_CLOUD_NAME or "").strip()
    fmt = ext.lstrip(".")
    folder_id = public_id.strip("/")
    if resource_type == "video":
        return f"https://res.cloudinary.com/{cloud_name}/video/upload/{folder_id}.{fmt}"
    return f"https://res.cloudinary.com/{cloud_name}/image/upload/{folder_id}.{fmt}"


def cloudinary_resource_exists(public_id: str, resource_type: str) -> bool:
    if not ensure_cloudinary_configured():
        return False
    try:
        import cloudinary.api

        cloudinary.api.resource(public_id, resource_type=resource_type)
        return True
    except Exception:
        return False
