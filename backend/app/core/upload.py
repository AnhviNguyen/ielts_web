"""Validated image uploads (avatar, etc.)."""

import uuid

from fastapi import HTTPException, UploadFile

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
MAX_ADMIN_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_AUDIO_UPLOAD_SIZE = 15 * 1024 * 1024  # 15MB
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".webm", ".m4a", ".mp3", ".ogg"}
EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def read_upload_limited(file: UploadFile, max_size: int) -> bytes:
    """Read an UploadFile without allowing unbounded memory growth."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {max_size // (1024 * 1024)}MB.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def validate_and_read_image(file: UploadFile) -> tuple[bytes, str]:
    """Validate upload. Returns (content_bytes, safe_filename)."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Chỉ chấp nhận JPEG, PNG, WebP. Nhận: {file.content_type}",
        )
    content = await read_upload_limited(file, MAX_AVATAR_SIZE)
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File tối đa 2MB. File của bạn: {len(content) // 1024}KB",
        )
    ext = EXTENSION_MAP[file.content_type]
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    return content, safe_filename
