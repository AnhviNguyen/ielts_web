"""Tests for local media asset resolution."""

from pathlib import Path
from unittest.mock import patch

from app.core.media_assets import resolve_audio, resolve_image


@patch("app.core.media_assets.settings")
def test_resolve_audio_local(mock_settings, tmp_path, monkeypatch):
    mock_settings.STORAGE_BACKEND = "local"
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "abc123.mp3").write_bytes(b"fake")
    monkeypatch.setattr("app.core.media_assets._AUDIO_DIR", audio_dir)

    asset = resolve_audio("abc123")
    assert asset is not None
    assert asset.source == "local"
    assert asset.local_path.name == "abc123.mp3"


@patch("app.core.media_assets.settings")
def test_resolve_image_local(mock_settings, tmp_path, monkeypatch):
    mock_settings.STORAGE_BACKEND = "local"
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "thumb.png").write_bytes(b"png")
    monkeypatch.setattr("app.core.media_assets._IMAGE_DIR", image_dir)

    asset = resolve_image("thumb.png")
    assert asset is not None
    assert asset.source == "local"


@patch("app.core.cloudinary_storage.settings")
@patch("app.core.media_assets.settings")
def test_resolve_audio_cloudinary(mock_media_settings, mock_cld_settings):
    mock_media_settings.STORAGE_BACKEND = "cloudinary"
    mock_cld_settings.CLOUDINARY_CLOUD_NAME = "dq955rfxi"

    asset = resolve_audio("abc123.mp3")
    assert asset is not None
    assert asset.source == "cloudinary"
    assert asset.public_url == "https://res.cloudinary.com/dq955rfxi/video/upload/audio/abc123.mp3"
    assert asset.local_path is None


@patch("app.core.media_assets.settings")
def test_resolve_audio_hex_id_matches_dashed_local_file(mock_settings, tmp_path, monkeypatch):
    mock_settings.STORAGE_BACKEND = "local"
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "63aa72d7-778f-4622-adbb-4f794fd474a6.mp3").write_bytes(b"mp3")
    monkeypatch.setattr("app.core.media_assets._AUDIO_DIR", audio_dir)

    asset = resolve_audio("63aa72d7778f4622adbb4f794fd474a6.mp3")
    assert asset is not None
    assert asset.source == "local"


@patch("app.core.cloudinary_storage.settings")
@patch("app.core.media_assets.settings")
def test_resolve_image_cloudinary(mock_media_settings, mock_cld_settings):
    mock_media_settings.STORAGE_BACKEND = "cloudinary"
    mock_cld_settings.CLOUDINARY_CLOUD_NAME = "dq955rfxi"

    asset = resolve_image("e6be86ba-7962-42a6-8565-475f3e5220f5")
    assert asset is not None
    assert asset.source == "cloudinary"
    assert asset.public_url == (
        "https://res.cloudinary.com/dq955rfxi/image/upload/"
        "images/e6be86ba-7962-42a6-8565-475f3e5220f5.png"
    )
