"""
Translation Practice router — /translation/*
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.db.models import User
from app.services.translation_service import TranslationService

router = APIRouter(prefix="/translation", tags=["Translation Practice"])


class TranslationCheckRequest(BaseModel):
    sentence_id: int = Field(gt=0)
    user_translation: str = Field(min_length=1, max_length=2000)


def _svc(db: AsyncSession = Depends(get_db)) -> TranslationService:
    return TranslationService(db)


@router.get("/steps")
async def list_steps(svc: TranslationService = Depends(_svc)) -> dict:
    """List all learning steps with topic and sentence counts."""
    steps = await svc.list_steps_with_counts()
    return {"code": 0, "data": steps}


@router.get("/steps/{step_id}/topics")
async def list_topics(
    step_id: int,
    current_user: User = Depends(get_current_user),
    svc: TranslationService = Depends(_svc),
) -> dict:
    """List all topics within a step, with user progress."""
    topics = await svc.list_topics_for_step(step_id, current_user.id)
    return {"code": 0, "data": topics}


@router.get("/topics/{topic_id}/sentences")
async def list_sentences(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    svc: TranslationService = Depends(_svc),
) -> dict:
    """List all sentences in a topic with hint words and previous attempt info."""
    sentences = await svc.list_sentences_for_topic(topic_id, current_user.id)
    return {"code": 0, "data": sentences}


@limiter.limit("20/minute")
@router.post("/check")
async def check_translation(
    request: Request,
    body: TranslationCheckRequest,
    current_user: User = Depends(get_current_user),
    svc: TranslationService = Depends(_svc),
) -> dict:
    """Grade user's translation with AI. Returns score, feedback, model_answer."""
    result = await svc.check_translation(
        user_id=current_user.id,
        sentence_id=body.sentence_id,
        user_translation=body.user_translation,
    )
    return {"code": 0, "data": result}
