"""
tests/integration/services/test_admin_content.py
────────────────────────────────────────────────
Integration tests for AdminContentService uploads (AC-04 to AC-05).
"""

import io
import shutil
import pytest
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from starlette.datastructures import Headers

from unittest.mock import patch
from app.core.config import settings
from app.services.admin_content_service import AdminContentService

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def configure_settings():
    with patch.object(settings, "STORAGE_BACKEND", "local"):
        yield


@pytest.fixture
def temp_data_root():
    """Create a temporary data root inside the workspace."""
    data_dir = Path("tests/temp_admin_data")
    data_dir.mkdir(parents=True, exist_ok=True)
    yield data_dir
    if data_dir.exists():
        shutil.rmtree(data_dir, ignore_errors=True)


@pytest.fixture
def admin_service(temp_data_root):
    return AdminContentService(data_root=temp_data_root)


# ---------------------------------------------------------------------------
# AC-04: Upload image/audio file (Happy path)
# ---------------------------------------------------------------------------

async def test_ac04_upload_image_success(admin_service, temp_data_root):
    """
    AC-04: Upload image file -> saved to local disk assets/images/.
    """
    file_bytes = b"fake-png-content-bytes"
    upload = UploadFile(
        filename="thumbnail.png",
        file=io.BytesIO(file_bytes),
        headers=Headers({"content-type": "image/png"}),
    )

    resp = await admin_service.save_admin_image(upload)
    assert resp.id is not None
    assert resp.url == f"/images/{resp.id}"

    # Verify stored on disk
    expected_path = temp_data_root / "assets" / "images" / f"{resp.id}.png"
    assert expected_path.exists()
    assert expected_path.read_bytes() == file_bytes


async def test_ac04_upload_audio_success(admin_service, temp_data_root):
    """
    AC-04: Upload audio file -> saved to local disk assets/audio/.
    """
    file_bytes = b"fake-mp3-content-bytes"
    upload = UploadFile(
        filename="listening_passage.mp3",
        file=io.BytesIO(file_bytes),
        headers=Headers({"content-type": "audio/mp3"}),
    )

    resp = await admin_service.save_admin_audio(upload)
    assert resp.id is not None
    assert resp.url == f"/audio/{resp.id}"

    # Verify stored on disk
    expected_path = temp_data_root / "assets" / "audio" / f"{resp.id}.mp3"
    assert expected_path.exists()
    assert expected_path.read_bytes() == file_bytes


# ---------------------------------------------------------------------------
# AC-05: Upload invalid files (php, exe) -> raises 400 Bad Request
# ---------------------------------------------------------------------------

async def test_ac05_upload_image_invalid_extension(admin_service):
    """
    AC-05: Upload image file with malicious extension -> Raise 400.
    """
    upload = UploadFile(
        filename="shell.php",
        file=io.BytesIO(b"<?php phpinfo(); ?>"),
        headers=Headers({"content-type": "text/php"}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.save_admin_image(upload)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only PNG, JPG, JPEG, and WEBP images are supported" in exc_info.value.detail


async def test_ac05_upload_audio_invalid_extension(admin_service):
    """
    AC-05: Upload audio file with exe extension -> Raise 400.
    """
    upload = UploadFile(
        filename="malware.exe",
        file=io.BytesIO(b"exe-binary-payload"),
        headers=Headers({"content-type": "application/octet-stream"}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.save_admin_audio(upload)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only MP3, M4A, OGG, and WAV audio files are supported" in exc_info.value.detail
