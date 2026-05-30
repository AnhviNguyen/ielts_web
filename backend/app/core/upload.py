"""Validated image uploads (avatar, etc.)."""

import uuid

from fastapi import HTTPException, UploadFile

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def validate_and_read_image(file: UploadFile) -> tuple[bytes, str]:
    """Validate upload. Returns (content_bytes, safe_filename)."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Chỉ chấp nhận JPEG, PNG, WebP. Nhận: {file.content_type}",
        )
    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File tối đa 2MB. File của bạn: {len(content) // 1024}KB",
        )
    ext = EXTENSION_MAP[file.content_type]
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    return content, safe_filename
