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
