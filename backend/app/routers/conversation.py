"""Conversation Practice router — /conversation/*"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.upload import ALLOWED_AUDIO_EXTENSIONS, MAX_AUDIO_UPLOAD_SIZE, read_upload_limited
from app.db.database import get_db
from app.db.models import User
from app.services.conversation_service import ConversationService
from app.services.speaking_audio_utils import convert_to_wav, run_whisper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversation", tags=["Conversation Practice"])


class StartRequest(BaseModel):
    topic_id: int = Field(gt=0)


class TurnRequest(BaseModel):
    session_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=2000)


class EndRequest(BaseModel):
    session_id: int = Field(gt=0)


class HintRequest(BaseModel):
    session_id: int = Field(gt=0)
    ai_message: str = Field(min_length=1, max_length=2000)


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


def _svc(db: AsyncSession = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


@router.get("/topics")
async def list_topics(
    level: str | None = None,
    svc: ConversationService = Depends(_svc),
) -> dict:
    topics = await svc.list_topics(level)
    return {"code": 0, "data": topics}


@limiter.limit("10/minute")
@router.post("/start")
async def start(
    request: Request,
    body: StartRequest,
    current_user: User = Depends(get_current_user),
    svc: ConversationService = Depends(_svc),
) -> dict:
    data = await svc.start_session(current_user.id, body.topic_id)
    return {"code": 0, "data": data}


@limiter.limit("30/minute")
@router.post("/turn")
async def turn(
    request: Request,
    body: TurnRequest,
    current_user: User = Depends(get_current_user),
    svc: ConversationService = Depends(_svc),
) -> dict:
    data = await svc.process_turn(current_user.id, body.session_id, body.message)
    return {"code": 0, "data": data}


async def _transcribe_uploaded_audio(audio: UploadFile) -> str:
    suffix = (Path(audio.filename or "audio.webm").suffix or ".webm").lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio file type")

    audio_bytes = await read_upload_limited(audio, MAX_AUDIO_UPLOAD_SIZE)
    tmp_path = ""
    wav_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        wav_path = convert_to_wav(tmp_path) if suffix != ".wav" else tmp_path

        whisper_result = run_whisper(wav_path)
        transcript = (whisper_result.get("transcript") or "").strip()
        if not transcript:
            raise HTTPException(status_code=400, detail="Không nhận được giọng nói, thử lại.")
        return transcript
    finally:
        for p in {tmp_path, wav_path}:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass


@limiter.limit("30/minute")
@router.post("/turn/transcribe")
async def transcribe_voice(
    request: Request,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict:
    transcript = await _transcribe_uploaded_audio(audio)
    return {"code": 0, "data": {"transcript": transcript}}


@limiter.limit("20/minute")
@router.post("/turn/voice")
async def turn_voice(
    request: Request,
    session_id: int = Form(...),
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    svc: ConversationService = Depends(_svc),
) -> dict:
    transcript = await _transcribe_uploaded_audio(audio)
    data = await svc.process_turn(current_user.id, session_id, transcript)
    data["transcript"] = transcript
    return {"code": 0, "data": data}


@limiter.limit("10/minute")
@router.post("/end")
async def end(
    request: Request,
    body: EndRequest,
    current_user: User = Depends(get_current_user),
    svc: ConversationService = Depends(_svc),
) -> dict:
    data = await svc.end_session(current_user, body.session_id)
    return {"code": 0, "data": data}


@limiter.limit("30/minute")
@router.post("/assist/hint")
async def reply_hint(
    request: Request,
    body: HintRequest,
    current_user: User = Depends(get_current_user),
    svc: ConversationService = Depends(_svc),
) -> dict:
    data = await svc.get_reply_hint(current_user.id, body.session_id, body.ai_message)
    return {"code": 0, "data": data}


@limiter.limit("60/minute")
@router.post("/assist/translate")
async def translate_message(
    request: Request,
    body: TranslateRequest,
    current_user: User = Depends(get_current_user),
    svc: ConversationService = Depends(_svc),
) -> dict:
    data = await svc.translate_message(body.text)
    return {"code": 0, "data": data}
