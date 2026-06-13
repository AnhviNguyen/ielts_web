"""Shadowing pronunciation check — wav2vec2 CTC + GOP."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from app.services.gop_pronunciation_service import load_audio_16k, score_gop
from app.services.speaking_audio_utils import convert_to_wav, has_speech

logger = logging.getLogger(__name__)


async def check_pronunciation_from_bytes(
    audio_bytes: bytes,
    filename: str,
    target_text: str,
) -> dict:
    """Score shadowing recording with wav2vec2 forced alignment + GOP."""
    suffix = Path(filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    wav_path = tmp_path
    try:
        if suffix.lower() != ".wav":
            try:
                wav_path = convert_to_wav(tmp_path)
            except Exception as exc:
                logger.warning("wav convert failed: %s", exc)

        audio_16k = await asyncio.to_thread(load_audio_16k, wav_path)
        if not has_speech(audio_16k):
            raise ValueError(
                "Không phát hiện giọng nói trong bản ghi. Hãy nói to hơn hoặc kiểm tra micro."
            )

        return await asyncio.to_thread(score_gop, audio_16k, target_text)
    finally:
        for p in {tmp_path, wav_path}:
            try:
                Path(p).unlink(missing_ok=True)
            except OSError:
                pass
