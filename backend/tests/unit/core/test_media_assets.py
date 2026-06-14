"""
tests/unit/core/test_media_assets.py
──────────────────────────────────────
Unit tests mở rộng cho app/core/media_assets.py.

Kế thừa tests/test_media_assets.py (2 tests cũ).

Bao phủ:
  MA-01  resolve_audio → tìm thấy file .mp3 local
  MA-02  resolve_audio → tìm file với extension khác (.wav, .ogg, .m4a)
  MA-03  resolve_audio → file_id có extension trong tên → strip đúng (stem)
  MA-04  resolve_audio → không tìm thấy file nào → trả về None
  MA-05  resolve_image → tìm thấy file .png local
  MA-06  resolve_image → tìm thấy file .jpg, .jpeg, .webp
  MA-07  resolve_image → không tìm thấy → trả về None
  MA-08  resolve_audio (S3 mode) → kiểm tra storage.exists + trả về MediaAsset với source="s3"
  MA-09  resolve_image (S3 mode) → tìm theo thứ tự extension, trả về cái đầu tiên tồn tại
  MA-10  resolve_audio (S3 mode) → không tìm thấy trên S3 → fallback local → None (không crash)
  MA-11  content_type được set đúng cho từng extension
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.media_assets import (
    AUDIO_MEDIA,
    IMAGE_MEDIA,
    MediaAsset,
    resolve_audio,
    resolve_image,
)


# ---------------------------------------------------------------------------
# Fixtures: tạo thư mục audio/image giả (dùng tempfile.mkdtemp tránh WinError 5)
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_audio_dir(monkeypatch):
    d = tempfile.mkdtemp(prefix="pytest_ma_audio_")
    audio_dir = Path(d) / "audio"
    audio_dir.mkdir()
    monkeypatch.setattr("app.core.media_assets._AUDIO_DIR", audio_dir)
    monkeypatch.setattr("app.core.media_assets.settings", MagicMock(STORAGE_BACKEND="local"))
    yield audio_dir
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def fake_image_dir(monkeypatch):
    d = tempfile.mkdtemp(prefix="pytest_ma_image_")
    image_dir = Path(d) / "images"
    image_dir.mkdir()
    monkeypatch.setattr("app.core.media_assets._IMAGE_DIR", image_dir)
    monkeypatch.setattr("app.core.media_assets.settings", MagicMock(STORAGE_BACKEND="local"))
    yield image_dir
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# MA-01: resolve_audio tìm thấy .mp3
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma01_resolve_audio_finds_mp3(fake_audio_dir):
    (fake_audio_dir / "quiz001.mp3").write_bytes(b"fake-audio")
    asset = resolve_audio("quiz001")
    assert asset is not None
    assert asset.source == "local"
    assert asset.local_path.name == "quiz001.mp3"
    assert asset.content_type == "audio/mpeg"


# ---------------------------------------------------------------------------
# MA-02: resolve_audio với các extension khác
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("ext,expected_ct", [
    (".wav", "audio/wav"),
    (".ogg", "audio/ogg"),
    (".m4a", "audio/mp4"),
])
def test_ma02_resolve_audio_other_extensions(fake_audio_dir, ext, expected_ct):
    stem = "clip_test"
    (fake_audio_dir / f"{stem}{ext}").write_bytes(b"data")
    asset = resolve_audio(stem)
    assert asset is not None
    assert asset.content_type == expected_ct


# ---------------------------------------------------------------------------
# MA-03: file_id có chứa extension → stem() chỉ lấy phần trước dấu chấm đầu
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma03_file_id_with_extension_stripped(fake_audio_dir):
    (fake_audio_dir / "abc123.mp3").write_bytes(b"x")
    # Truyền vào "abc123.mp3" → stem = "abc123"
    asset = resolve_audio("abc123.mp3")
    assert asset is not None
    assert asset.local_path.name == "abc123.mp3"


# ---------------------------------------------------------------------------
# MA-04: resolve_audio không tìm thấy → None
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma04_resolve_audio_not_found_returns_none(fake_audio_dir):
    asset = resolve_audio("does-not-exist")
    assert asset is None


# ---------------------------------------------------------------------------
# MA-05: resolve_image tìm thấy .png
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma05_resolve_image_finds_png(fake_image_dir):
    (fake_image_dir / "thumb.png").write_bytes(b"png-data")
    asset = resolve_image("thumb")
    assert asset is not None
    assert asset.source == "local"
    assert asset.content_type == "image/png"


# ---------------------------------------------------------------------------
# MA-06: resolve_image với các extension ảnh khác
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("ext,expected_ct", [
    (".jpg", "image/jpeg"),
    (".jpeg", "image/jpeg"),
    (".webp", "image/webp"),
])
def test_ma06_resolve_image_other_extensions(fake_image_dir, ext, expected_ct):
    stem = "img_test"
    (fake_image_dir / f"{stem}{ext}").write_bytes(b"data")
    asset = resolve_image(stem)
    assert asset is not None
    assert asset.content_type == expected_ct


# ---------------------------------------------------------------------------
# MA-07: resolve_image không tìm thấy → None
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma07_resolve_image_not_found_returns_none(fake_image_dir):
    asset = resolve_image("ghost-image")
    assert asset is None


# ---------------------------------------------------------------------------
# MA-08: resolve_audio (S3 mode) → source="s3"
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma08_resolve_audio_s3_mode(monkeypatch):
    mock_settings = MagicMock()
    mock_settings.STORAGE_BACKEND = "s3"
    monkeypatch.setattr("app.core.media_assets.settings", mock_settings)

    mock_storage = MagicMock()
    mock_storage.exists.return_value = True
    mock_storage.public_url.return_value = "https://cdn.example.com/assets/audio/clip001.mp3"
    monkeypatch.setattr("app.core.media_assets.get_storage", lambda: mock_storage)

    asset = resolve_audio("clip001")
    assert asset is not None
    assert asset.source == "s3"
    assert asset.public_url == "https://cdn.example.com/assets/audio/clip001.mp3"
    assert asset.content_type == "audio/mpeg"


# ---------------------------------------------------------------------------
# MA-09: resolve_image (S3 mode) → tìm file đầu tiên tồn tại
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma09_resolve_image_s3_mode(monkeypatch):
    mock_settings = MagicMock()
    mock_settings.STORAGE_BACKEND = "s3"
    monkeypatch.setattr("app.core.media_assets.settings", mock_settings)

    mock_storage = MagicMock()
    # Giả sử chỉ có .webp
    def exists_side_effect(key: str) -> bool:
        return key.endswith(".webp")
    mock_storage.exists.side_effect = exists_side_effect
    mock_storage.public_url.return_value = "https://cdn.example.com/assets/images/img.webp"
    monkeypatch.setattr("app.core.media_assets.get_storage", lambda: mock_storage)

    asset = resolve_image("img")
    assert asset is not None
    assert asset.source == "s3"
    assert asset.content_type == "image/webp"


# ---------------------------------------------------------------------------
# MA-10: resolve_audio S3 mode, không tìm thấy trên S3, không có local → None
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma10_resolve_audio_s3_not_found_returns_none(monkeypatch):
    mock_settings = MagicMock()
    mock_settings.STORAGE_BACKEND = "s3"
    monkeypatch.setattr("app.core.media_assets.settings", mock_settings)

    # S3 không tìm thấy gì
    mock_storage = MagicMock()
    mock_storage.exists.return_value = False
    monkeypatch.setattr("app.core.media_assets.get_storage", lambda: mock_storage)

    # Local cũng không có — dùng tempfile.mkdtemp
    d = tempfile.mkdtemp(prefix="pytest_ma_empty_")
    try:
        empty_dir = Path(d) / "audio_empty"
        empty_dir.mkdir()
        monkeypatch.setattr("app.core.media_assets._AUDIO_DIR", empty_dir)
        asset = resolve_audio("nonexistent")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    assert asset is None


# ---------------------------------------------------------------------------
# MA-11: content_type constants đúng cho mọi extension
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ma11_audio_media_types_complete():
    assert AUDIO_MEDIA[".mp3"] == "audio/mpeg"
    assert AUDIO_MEDIA[".wav"] == "audio/wav"
    assert AUDIO_MEDIA[".ogg"] == "audio/ogg"
    assert AUDIO_MEDIA[".m4a"] == "audio/mp4"


@pytest.mark.unit
def test_ma11b_image_media_types_complete():
    assert IMAGE_MEDIA[".png"] == "image/png"
    assert IMAGE_MEDIA[".jpg"] == "image/jpeg"
    assert IMAGE_MEDIA[".jpeg"] == "image/jpeg"
    assert IMAGE_MEDIA[".webp"] == "image/webp"
