"""Word-level pronunciation scoring (Wav2Vec2 + CMU phonemes)."""

from __future__ import annotations

import asyncio
import logging
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.upload import ALLOWED_AUDIO_EXTENSIONS, MAX_AUDIO_UPLOAD_SIZE, read_upload_limited
from app.db.models import User
from app.services.phoneme_scorer import get_expected_word_info, get_phoneme_scorer
from app.services.pronunciation_audio import audio_bytes_to_waveform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pronunciation", tags=["Pronunciation"])


def _clean_word(word: str) -> str:
    return re.sub(r"[^a-zA-Z'-]", "", (word or "").strip())


@router.get("/word/{word}/expected")
async def get_word_expected_phonemes(
    word: str,
    _user: User = Depends(get_current_user),
):
    """Return expected CMU phonemes/IPA for display before recording."""
    cleaned = _clean_word(word)
    if not cleaned:
        raise HTTPException(status_code=400, detail="word is required")
    info = get_expected_word_info(cleaned)
    if not info:
        raise HTTPException(
            status_code=422,
            detail=f"Từ '{cleaned}' không có trong CMU Pronouncing Dictionary.",
        )
    return info


@limiter.limit("20/minute")
@router.post("/word")
async def score_word_pronunciation(
    request: Request,
    word: str = Form(...),
    audio: UploadFile = File(...),
    _user: User = Depends(get_current_user),
):
    """Score single-word pronunciation from browser-recorded audio."""
    cleaned = _clean_word(word)
    if not cleaned:
        raise HTTPException(status_code=400, detail="word is required")

    if not get_expected_word_info(cleaned):
        raise HTTPException(
            status_code=422,
            detail=f"Từ '{cleaned}' không có trong CMU Pronouncing Dictionary.",
        )

    suffix = (audio.filename or "audio.webm").rsplit(".", 1)
    ext = f".{suffix[-1].lower()}" if len(suffix) > 1 else ".webm"
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio file type")

    audio_bytes = await read_upload_limited(audio, MAX_AUDIO_UPLOAD_SIZE)

    try:
        waveform, sample_rate = await asyncio.to_thread(
            audio_bytes_to_waveform,
            audio_bytes,
            audio.filename or "audio.webm",
        )
        result = await asyncio.to_thread(
            get_phoneme_scorer().score_word,
            waveform,
            sample_rate,
            cleaned,
        )
        return result.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("pronunciation/word failed for %s", cleaned)
        raise HTTPException(status_code=500, detail=f"Kiểm tra phát âm thất bại: {exc}") from exc
