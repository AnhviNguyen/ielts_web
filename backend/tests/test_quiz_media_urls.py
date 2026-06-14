"""Tests for quiz media URL attachment."""

from unittest.mock import patch

from app.core.media_assets import public_audio_url
from app.utils.quiz_sanitizer import attach_quiz_media_urls


@patch("app.utils.quiz_sanitizer.public_audio_url")
def test_attach_audio_url_on_listening_part(mock_audio_url):
    mock_audio_url.return_value = "https://res.cloudinary.com/test/video/upload/audio/uuid.mp3"
    data = {
        "parts": [
            {"title": "Part 1", "file_id": "63aa72d7-778f-4622-adbb-4f794fd474a6"},
        ],
    }
    out = attach_quiz_media_urls(data)
    assert out["parts"][0]["audio_url"] == "https://res.cloudinary.com/test/video/upload/audio/uuid.mp3"
    mock_audio_url.assert_called_once_with("63aa72d7-778f-4622-adbb-4f794fd474a6")


@patch("app.utils.quiz_sanitizer.public_audio_url")
def test_attach_keeps_existing_http_audio_url(mock_audio_url):
    url = "https://example.com/q.mp3"
    data = {"audio_url": url}
    out = attach_quiz_media_urls(data)
    assert out["audio_url"] == url
    mock_audio_url.assert_not_called()


@patch("app.core.cloudinary_storage.settings")
@patch("app.core.media_assets.settings")
def test_public_audio_url_cloudinary(mock_media_settings, mock_cld_settings):
    mock_media_settings.STORAGE_BACKEND = "cloudinary"
    mock_cld_settings.CLOUDINARY_CLOUD_NAME = "dq955rfxi"

    url = public_audio_url("63aa72d7-778f-4622-adbb-4f794fd474a6")
    assert url == "https://res.cloudinary.com/dq955rfxi/video/upload/audio/63aa72d7-778f-4622-adbb-4f794fd474a6.mp3"
