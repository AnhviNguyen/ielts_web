"""
Object storage abstraction — local filesystem or S3-compatible (MinIO/AWS).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def s3_public_url_for_key(key: str) -> str | None:
    base = (settings.S3_PUBLIC_BASE_URL or "").strip().rstrip("/")
    if not base:
        return None
    clean_key = key.strip().lstrip("/")
    if not clean_key:
        return None
    return f"{base}/{clean_key}"


class StorageBackend(ABC):
    @abstractmethod
    def put_bytes(self, key: str, data: bytes, content_type: str) -> str:
        """Store object; return public URL path or absolute URL for clients."""

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def get_bytes(self, key: str) -> bytes | None:
        pass

    @abstractmethod
    def public_url(self, key: str) -> str:
        pass


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str, url_prefix: str) -> None:
        self._base = Path(base_dir)
        self._url_prefix = url_prefix.rstrip("/")

    def _path(self, key: str) -> Path:
        return self._base.joinpath(*key.split("/"))

    def put_bytes(self, key: str, data: bytes, content_type: str) -> str:
        dest = self._path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return self.public_url(key)

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.is_file():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def get_bytes(self, key: str) -> bytes | None:
        path = self._path(key)
        if not path.is_file():
            return None
        return path.read_bytes()

    def public_url(self, key: str) -> str:
        return f"{self._url_prefix}/{key.replace(chr(92), '/')}"


class S3StorageBackend(StorageBackend):
    def __init__(self) -> None:
        import boto3
        from botocore.client import Config

        self._bucket = settings.S3_BUCKET
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )
        self._public_base = (settings.S3_PUBLIC_BASE_URL or "/media").strip().rstrip("/")

    def put_bytes(self, key: str, data: bytes, content_type: str) -> str:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return self.public_url(key)

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as exc:
            logger.debug("S3 delete skipped key=%s: %s", key, exc)

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    def get_bytes(self, key: str) -> bytes | None:
        try:
            obj = self._client.get_object(Bucket=self._bucket, Key=key)
            return obj["Body"].read()
        except Exception:
            return None

    def public_url(self, key: str) -> str:
        clean_key = key.strip().lstrip("/")
        return f"{self._public_base}/{clean_key}"


class CloudinaryStorageBackend(StorageBackend):
    """Upload/delete via Cloudinary API; public URLs for delivery."""

    def put_bytes(self, key: str, data: bytes, content_type: str) -> str:
        from app.core.cloudinary_storage import cloudinary_public_url, ensure_cloudinary_configured

        if not ensure_cloudinary_configured():
            raise RuntimeError("Cloudinary is not configured")
        import cloudinary.uploader

        public_id = key.strip("/").rsplit(".", 1)[0]
        resource_type = "video" if key.startswith("audio/") or content_type.startswith("audio/") else "image"
        cloudinary.uploader.upload(
            data,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=True,
        )
        ext = "." + key.rsplit(".", 1)[-1] if "." in key else (".mp3" if resource_type == "video" else ".png")
        return cloudinary_public_url(public_id, resource_type, ext)

    def delete(self, key: str) -> None:
        from app.core.cloudinary_storage import ensure_cloudinary_configured

        if not ensure_cloudinary_configured():
            return
        try:
            import cloudinary.uploader

            public_id = key.strip("/").rsplit(".", 1)[0]
            resource_type = "video" if key.startswith("audio/") else "image"
            cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        except Exception as exc:
            logger.debug("Cloudinary delete skipped key=%s: %s", key, exc)

    def exists(self, key: str) -> bool:
        from app.core.cloudinary_storage import cloudinary_resource_exists

        public_id = key.strip("/").rsplit(".", 1)[0]
        resource_type = "video" if key.startswith("audio/") else "image"
        return cloudinary_resource_exists(public_id, resource_type)

    def get_bytes(self, key: str) -> bytes | None:
        return None

    def public_url(self, key: str) -> str:
        from app.core.cloudinary_storage import cloudinary_public_url

        public_id = key.strip("/").rsplit(".", 1)[0]
        ext = "." + key.rsplit(".", 1)[-1] if "." in key else ""
        resource_type = "video" if key.startswith("audio/") else "image"
        if not ext:
            ext = ".mp3" if resource_type == "video" else ".png"
        return cloudinary_public_url(public_id, resource_type, ext)


def get_storage() -> StorageBackend:
    backend = settings.STORAGE_BACKEND.lower()
    if backend == "s3":
        return S3StorageBackend()
    if backend == "cloudinary":
        return CloudinaryStorageBackend()
    return LocalStorageBackend(base_dir="uploads", url_prefix="/uploads")


def avatar_key(user_id: int, filename: str) -> str:
    return f"avatars/user-{user_id}-{filename}"
