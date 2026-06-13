"""
Shadowing API — YouTube transcript pipeline for dictation & shadowing.
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.upload import ALLOWED_AUDIO_EXTENSIONS, MAX_AUDIO_UPLOAD_SIZE, read_upload_limited
from app.db.database import get_db
from app.db.models import User
from app.repositories.shadowing_repository import ShadowingRepository
from app.services.badge_service import BadgeService
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


@router.post("/video/process")
@limiter.limit("3/minute")
async def process_video(
    request: Request,
    body: ShadowingProcessVideoRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Extract transcript (captions or Whisper), store in DB, return VideoData."""
    if settings.CELERY_ENABLED:
        from app.tasks.shadowing_tasks import process_video_task

        task = process_video_task.delay(
            body.url,
            body.level,
            body.translate,
            user.id,
        )
        from app.core.task_ownership import register_task_owner

        register_task_owner(task.id, user.id)
        return {"task_id": task.id, "status": "processing"}

    svc = _svc(db)
    try:
        data = await svc.process_url(
            body.url,
            level=body.level,
            translate=body.translate,
            user_id=user.id,
            force_refresh=body.force_refresh,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return data


@router.get("/video/process/result/{task_id}")
async def get_process_video_result(
    task_id: str,
    user: User = Depends(get_current_user),
):
    from app.core.celery_app import celery_app
    from app.core.task_ownership import verify_task_owner

    if not verify_task_owner(task_id, user.id):
        raise HTTPException(status_code=403, detail="Không có quyền truy cập task này")

    task = celery_app.AsyncResult(task_id)
    state_map = {"PENDING": 0, "STARTED": 30, "RETRY": 20}
    if task.state == "SUCCESS":
        return {"status": "done", "result": task.result}
    if task.state == "FAILURE":
        return {"status": "error", "detail": "Xử lý video thất bại, vui lòng thử lại"}
    return {"status": "processing", "progress": state_map.get(task.state, 10)}


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
    badge_svc = BadgeService(db)
    before_unlocked = await badge_svc.get_unlocked_ids(user)
    await svc.record_view(user.id, video_id)
    new_badges = await badge_svc.detect_new_badges(user, before_unlocked)
    return {
        "ok": True,
        "new_badges": [b.model_dump() for b in new_badges],
    }


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
@limiter.limit("10/minute")
async def check_pronunciation(
    request: Request,
    file: UploadFile = File(...),
    target_text: str = Form(...),
    _user: User = Depends(get_current_user),
):
    """wav2vec2 CTC forced alignment + GOP vs target sentence."""
    if not (target_text or "").strip():
        raise HTTPException(status_code=400, detail="target_text is required")
    if len(target_text) > 1000:
        raise HTTPException(status_code=400, detail="target_text is too long")
    suffix = (file.filename or "audio.webm").rsplit(".", 1)
    ext = f".{suffix[-1].lower()}" if len(suffix) > 1 else ".webm"
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio file type")
    audio_bytes = await read_upload_limited(file, MAX_AUDIO_UPLOAD_SIZE)
    if len(audio_bytes) < 512:
        raise HTTPException(status_code=422, detail="File ghi âm quá ngắn hoặc rỗng.")
    try:
        data = await check_pronunciation_from_bytes(
            audio_bytes,
            file.filename or "audio.webm",
            target_text.strip(),
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("pronunciation check failed")
        raise HTTPException(status_code=500, detail=f"Kiểm tra phát âm thất bại: {e}") from e
