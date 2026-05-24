"""
Object storage abstraction — local filesystem or S3-compatible (MinIO/AWS).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


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
        base = (settings.S3_PUBLIC_BASE_URL or "/media").rstrip("/")
        self._public_base = base

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
        return f"{self._public_base}/{key}"


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND.lower() == "s3":
        return S3StorageBackend()
    return LocalStorageBackend(base_dir="uploads", url_prefix="/uploads")


def avatar_key(user_id: int, filename: str) -> str:
    return f"avatars/user-{user_id}-{filename}"
