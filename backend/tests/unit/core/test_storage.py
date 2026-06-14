"""
tests/unit/core/test_storage.py
─────────────────────────────────
Unit tests mở rộng cho app/core/storage.py.

Kế thừa và bổ sung từ tests/test_storage.py (3 tests cũ).

Bao phủ:
  STG-01  LocalStorage: put_bytes → file tồn tại, URL đúng
  STG-02  LocalStorage: put_bytes tự tạo thư mục con nếu chưa có
  STG-03  LocalStorage: exists() → True khi file có, False khi không có
  STG-04  LocalStorage: get_bytes() → đọc lại đúng content
Ghi chú: Dùng tempfile.TemporaryDirectory thay vì pytest tmp_path để tránh
          WinError 5 (Access Denied) trên Windows.
  STG-05  LocalStorage: delete() → file bị xóa
  STG-06  LocalStorage: delete() với file không tồn tại → không raise
  STG-07  LocalStorage: public_url() trả về URL đúng format
  STG-08  LocalStorage: put_bytes ghi đè file cũ (overwrite)
  STG-09  avatar_key() tạo key đúng format "avatars/user-{id}-{filename}"
  STG-10  S3StorageBackend.public_url() normalize slash ở đầu key
  STG-11  s3_public_url_for_key() với base URL và key hợp lệ
  STG-12  s3_public_url_for_key() với S3_PUBLIC_BASE_URL rỗng → None
  STG-13  S3StorageBackend.put_bytes() gọi đúng boto3 client
  STG-14  S3StorageBackend.exists() trả về True khi head_object thành công
  STG-15  S3StorageBackend.exists() trả về False khi head_object raise
  STG-16  S3StorageBackend.delete() swallow exception (không raise)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.storage import (
    LocalStorageBackend,
    S3StorageBackend,
    avatar_key,
    s3_public_url_for_key,
)


# ---------------------------------------------------------------------------
# Context manager helper thay thế tmp_path (tránh WinError 5)
# ---------------------------------------------------------------------------

from contextlib import contextmanager

@contextmanager
def _tmpdir():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="pytest_storage_")
    try:
        yield Path(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# STG-01: put_bytes → file tồn tại, URL đúng
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg01_put_bytes_creates_file_and_returns_url():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        url = storage.put_bytes("avatars/test.jpg", b"image-data", "image/jpeg")
        assert url == "/uploads/avatars/test.jpg"
        assert (d / "avatars" / "test.jpg").read_bytes() == b"image-data"


# ---------------------------------------------------------------------------
# STG-02: put_bytes tự tạo nested directory
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg02_put_bytes_creates_parent_dirs():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        storage.put_bytes("deep/nested/dir/file.mp3", b"audio", "audio/mpeg")
        assert (d / "deep" / "nested" / "dir" / "file.mp3").exists()


# ---------------------------------------------------------------------------
# STG-03: exists() True/False
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg03_exists_true_and_false():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        assert storage.exists("nonexistent.txt") is False
        storage.put_bytes("exists.txt", b"hi", "text/plain")
        assert storage.exists("exists.txt") is True


# ---------------------------------------------------------------------------
# STG-04: get_bytes() → đọc lại đúng content
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg04_get_bytes_returns_correct_content():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        data = b"hello-storage-world"
        storage.put_bytes("hello.bin", data, "application/octet-stream")
        result = storage.get_bytes("hello.bin")
        assert result == data


# ---------------------------------------------------------------------------
# STG-05: get_bytes() khi file không tồn tại → None
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg05_get_bytes_nonexistent_returns_none():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        assert storage.get_bytes("does-not-exist.mp3") is None


# ---------------------------------------------------------------------------
# STG-06: delete() → file bị xóa, sau đó exists() = False
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg06_delete_removes_file():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        storage.put_bytes("to-delete.jpg", b"bye", "image/jpeg")
        assert storage.exists("to-delete.jpg") is True
        storage.delete("to-delete.jpg")
        assert storage.exists("to-delete.jpg") is False


# ---------------------------------------------------------------------------
# STG-07: delete() với file không tồn tại → không raise exception
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg07_delete_nonexistent_does_not_raise():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        storage.delete("totally-missing.png")   # không raise


# ---------------------------------------------------------------------------
# STG-08: public_url() trả về URL đúng format
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg08_public_url_format():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        url = storage.public_url("audio/quiz123.mp3")
        assert url == "/uploads/audio/quiz123.mp3"


# ---------------------------------------------------------------------------
# STG-09: put_bytes ghi đè khi file đã tồn tại
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg09_put_bytes_overwrites_existing_file():
    with _tmpdir() as d:
        storage = LocalStorageBackend(base_dir=str(d), url_prefix="/uploads")
        storage.put_bytes("ow.txt", b"first", "text/plain")
        storage.put_bytes("ow.txt", b"second", "text/plain")
        assert (d / "ow.txt").read_bytes() == b"second"


# ---------------------------------------------------------------------------
# STG-10: avatar_key() format
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg10_avatar_key_correct_format():
    assert avatar_key(5, "photo.jpg") == "avatars/user-5-photo.jpg"
    assert avatar_key(1000, "img.png") == "avatars/user-1000-img.png"


# ---------------------------------------------------------------------------
# STG-11: S3StorageBackend.public_url() normalize slash ở đầu key
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg11_s3_public_url_normalizes_leading_slash():
    storage = object.__new__(S3StorageBackend)
    storage._public_base = "https://cdn.example.com"
    url = storage.public_url("/assets/images/test.png")
    assert url == "https://cdn.example.com/assets/images/test.png"


# ---------------------------------------------------------------------------
# STG-12: s3_public_url_for_key() với base URL hợp lệ
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg12_s3_public_url_for_key_success(monkeypatch):
    from app.core import storage as storage_mod
    fake_settings = MagicMock()
    fake_settings.S3_PUBLIC_BASE_URL = "https://cdn.example.com"
    monkeypatch.setattr(storage_mod, "settings", fake_settings)

    url = s3_public_url_for_key("assets/audio/clip.mp3")
    assert url == "https://cdn.example.com/assets/audio/clip.mp3"


# ---------------------------------------------------------------------------
# STG-13: s3_public_url_for_key() với S3_PUBLIC_BASE_URL rỗng → None
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg13_s3_public_url_for_key_empty_base_returns_none(monkeypatch):
    from app.core import storage as storage_mod
    fake_settings = MagicMock()
    fake_settings.S3_PUBLIC_BASE_URL = ""
    monkeypatch.setattr(storage_mod, "settings", fake_settings)

    assert s3_public_url_for_key("some/key.png") is None


# ---------------------------------------------------------------------------
# STG-14: S3StorageBackend.put_bytes() gọi đúng boto3 put_object
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg14_s3_put_bytes_calls_boto3(monkeypatch):
    storage = object.__new__(S3StorageBackend)
    storage._bucket = "test-bucket"
    storage._public_base = "https://cdn.example.com"
    mock_client = MagicMock()
    storage._client = mock_client

    url = storage.put_bytes("assets/audio/test.mp3", b"audio-data", "audio/mpeg")

    mock_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="assets/audio/test.mp3",
        Body=b"audio-data",
        ContentType="audio/mpeg",
    )
    assert url == "https://cdn.example.com/assets/audio/test.mp3"


# ---------------------------------------------------------------------------
# STG-15: S3StorageBackend.exists() → True khi head_object thành công
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg15_s3_exists_returns_true_on_success():
    storage = object.__new__(S3StorageBackend)
    storage._bucket = "test-bucket"
    storage._client = MagicMock()  # head_object không raise = file tồn tại
    assert storage.exists("some/key.jpg") is True


# ---------------------------------------------------------------------------
# STG-16: S3StorageBackend.exists() → False khi head_object raise
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg16_s3_exists_returns_false_on_error():
    storage = object.__new__(S3StorageBackend)
    storage._bucket = "test-bucket"
    mock_client = MagicMock()
    mock_client.head_object.side_effect = Exception("Not Found")
    storage._client = mock_client
    assert storage.exists("missing/key.jpg") is False


# ---------------------------------------------------------------------------
# STG-17: S3StorageBackend.delete() swallow exception (không raise)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_stg17_s3_delete_swallows_exception():
    storage = object.__new__(S3StorageBackend)
    storage._bucket = "test-bucket"
    mock_client = MagicMock()
    mock_client.delete_object.side_effect = Exception("S3 error")
    storage._client = mock_client
    storage.delete("some/key.jpg")   # không raise
