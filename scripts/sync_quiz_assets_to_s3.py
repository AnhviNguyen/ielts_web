#!/usr/bin/env python3
"""
Upload local quiz audio/images to S3/MinIO (assets/audio, assets/images).

Usage (from repo root):
  cd backend
  set STORAGE_BACKEND=s3
  set S3_ENDPOINT_URL=http://localhost:9000
  set S3_ACCESS_KEY=minioadmin
  set S3_SECRET_KEY=minioadmin
  set S3_BUCKET=linguaielts
  python ../scripts/sync_quiz_assets_to_s3.py
"""

from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
from app.core.storage import get_storage  # noqa: E402

AUDIO_DIR = BACKEND / "data" / "assets" / "audio"
IMAGE_DIR = BACKEND / "data" / "assets" / "images"


def upload_dir(local_dir: Path, prefix: str) -> int:
    if not local_dir.is_dir():
        print(f"Skip missing dir: {local_dir}")
        return 0
    storage = get_storage()
    count = 0
    for path in sorted(local_dir.iterdir()):
        if not path.is_file():
            continue
        key = f"{prefix}/{path.name}"
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        storage.put_bytes(key, path.read_bytes(), content_type)
        print(f"  uploaded {key}")
        count += 1
    return count


def main() -> None:
    if settings.STORAGE_BACKEND.lower() != "s3":
        print("Set STORAGE_BACKEND=s3 and S3_* env vars before running.")
        sys.exit(1)
    print(f"Syncing to bucket {settings.S3_BUCKET} @ {settings.S3_ENDPOINT_URL}")
    audio_n = upload_dir(AUDIO_DIR, "assets/audio")
    image_n = upload_dir(IMAGE_DIR, "assets/images")
    print(f"Done: {audio_n} audio, {image_n} images.")


if __name__ == "__main__":
    main()
