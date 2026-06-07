"""Tests for local object storage backend."""

import tempfile
from pathlib import Path

from app.core.storage import LocalStorageBackend, S3StorageBackend, avatar_key


def test_local_storage_put_and_url():
    with tempfile.TemporaryDirectory() as tmp:
        storage = LocalStorageBackend(base_dir=tmp, url_prefix="/uploads")
        url = storage.put_bytes("avatars/test.jpg", b"data", "image/jpeg")
        assert url == "/uploads/avatars/test.jpg"
        assert storage.public_url("avatars/test.jpg") == "/uploads/avatars/test.jpg"
        assert (Path(tmp) / "avatars" / "test.jpg").read_bytes() == b"data"


def test_avatar_key_format():
    assert avatar_key(5, "abc.jpg") == "avatars/user-5-abc.jpg"


def test_s3_public_url_normalizes_key_slashes():
    storage = object.__new__(S3StorageBackend)
    storage._public_base = "https://cdn.example.com"
    assert storage.public_url("/assets/images/test.png") == "https://cdn.example.com/assets/images/test.png"
