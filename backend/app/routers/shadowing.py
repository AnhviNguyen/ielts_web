"""
Shadowing API — YouTube transcript pipeline for dictation & shadowing.
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.repositories.shadowing_repository import ShadowingRepository
from app.schemas import (
    ShadowingHistoryItemOut,
    ShadowingHistoryListOut,
    ShadowingHistoryUpdateRequest,
    ShadowingProcessVideoRequest,
    ShadowingTranslateRequest,
    ShadowingTranslateResponse,
    ShadowingVideoDataOut,
)
from app.services.shadowing_service import ShadowingService
from app.services.shadowing_pronunciation_service import check_pronunciation_from_bytes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shadowing", tags=["Shadowing"])


def _svc(db: AsyncSession) -> ShadowingService:
    return ShadowingService(ShadowingRepository(db))


@router.post("/video/process", response_model=ShadowingVideoDataOut)
async def process_video(
    body: ShadowingProcessVideoRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Extract transcript (captions or Whisper), store in DB, return VideoData."""
    svc = _svc(db)
    try:
        data = await svc.process_url(
            body.url,
            level=body.level,
            translate=body.translate,
            user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return data


@router.get("/video/{video_id}", response_model=ShadowingVideoDataOut)
async def get_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = _svc(db)
    data = await svc.get_video(video_id)
    if not data:
        raise HTTPException(status_code=404, detail="Video not found. Process it first via POST /shadowing/video/process")
    await svc.record_view(user.id, video_id)
    return data


@router.get("/history", response_model=ShadowingHistoryListOut)
async def list_history(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = _svc(db)
    items = await svc.list_history(user.id, limit=min(max(limit, 1), 50))
    return ShadowingHistoryListOut(items=items)


@router.post("/history/{video_id}/touch")
async def touch_history(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = _svc(db)
    await svc.record_view(user.id, video_id)
    return {"ok": True}


@router.patch("/history/{video_id}", response_model=ShadowingHistoryItemOut)
async def update_history_item(
    video_id: str,
    body: ShadowingHistoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.title is None and body.level is None:
        raise HTTPException(status_code=400, detail="Provide title and/or level to update")
    svc = _svc(db)
    item = await svc.update_history_item(
        user.id, video_id, title=body.title, level=body.level
    )
    if not item:
        raise HTTPException(status_code=404, detail="History entry not found")
    return item


@router.delete("/history/{video_id}")
async def delete_history_item(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = _svc(db)
    ok = await svc.delete_history_item(user.id, video_id)
    if not ok:
        raise HTTPException(status_code=404, detail="History entry not found")
    return {"ok": True}


@router.post("/translate", response_model=ShadowingTranslateResponse)
async def translate_segment(
    body: ShadowingTranslateRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = _svc(db)
    translation = await svc.translate_one(body.text, body.from_lang, body.to_lang)
    return ShadowingTranslateResponse(translation=translation)


@router.post("/pronunciation/check")
async def check_pronunciation(
    file: UploadFile = File(...),
    target_text: str = Form(...),
    _user: User = Depends(get_current_user),
):
    """Whisper transcript + pron_scorer model vs target sentence."""
    if not (target_text or "").strip():
        raise HTTPException(status_code=400, detail="target_text is required")
    try:
        data = await check_pronunciation_from_bytes(
            await file.read(),
            file.filename or "audio.webm",
            target_text.strip(),
        )
        return data
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("pronunciation check failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
