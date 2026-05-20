"""
app/routers/vocabulary.py
─────────────────────────
Thin HTTP layer for Vocabulary and Reading Annotations.
All business logic lives in VocabService; all DB access in VocabRepository.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import ReadingAnnotation, User
from app.repositories.vocab_repository import VocabRepository
from app.schemas import (
    AnnotationResponse,
    AnnotationSave,
    VocabStatsResponse,
    VocabTopicCreate,
    VocabTopicResponse,
    VocabTopicUpdate,
    VocabWordCreate,
    VocabWordResponse,
    VocabWordUpdate,
)
from app.services.vocab_service import VocabService

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary"])


def _svc(db: AsyncSession) -> VocabService:
    """Dependency factory — wires Repository → Service."""
    return VocabService(VocabRepository(db))


# ═══ Topics ═══════════════════════════════════════════════════════════════════

@router.get("/topics", response_model=list[VocabTopicResponse])
async def list_topics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_topics(current_user.id)


@router.post("/topics", response_model=VocabTopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    body: VocabTopicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).create_topic(current_user.id, body.name)


@router.patch("/topics/{topic_id}", response_model=VocabTopicResponse)
async def update_topic(
    topic_id: int,
    body: VocabTopicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).update_topic(topic_id, current_user.id, body.name, body.sort_order)


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _svc(db).delete_topic(topic_id, current_user.id)


# ═══ Words ════════════════════════════════════════════════════════════════════

@router.get("/topics/{topic_id}/words", response_model=list[VocabWordResponse])
async def list_words(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_words(topic_id, current_user.id)


@router.post(
    "/topics/{topic_id}/words",
    response_model=VocabWordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_word(
    topic_id: int,
    body: VocabWordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).create_word(topic_id, current_user.id, body)


@router.patch("/topics/{topic_id}/words/{word_id}", response_model=VocabWordResponse)
async def update_word(
    topic_id: int,
    word_id: int,
    body: VocabWordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).update_word(topic_id, word_id, current_user.id, body)


@router.delete("/topics/{topic_id}/words/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_word(
    topic_id: int,
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _svc(db).delete_word(topic_id, word_id, current_user.id)


# ═══ Search & Stats ═══════════════════════════════════════════════════════════

@router.get("/words/search", response_model=list[VocabWordResponse])
async def search_words(
    q: str = Query(min_length=1, description="Search query (word or meaning)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search words across ALL topics for the current user."""
    return await _svc(db).search_words(current_user.id, q)


@router.get("/stats", response_model=VocabStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return total/mastered/learning/new counts across all topics."""
    stats = await _svc(db).get_stats(current_user.id)
    return VocabStatsResponse(**stats)


# ═══ Reading Annotations ══════════════════════════════════════════════════════

annotations_router = APIRouter(prefix="/annotations", tags=["Annotations"])


@annotations_router.get("/{session_id}", response_model=AnnotationResponse)
async def get_annotation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReadingAnnotation).where(
            ReadingAnnotation.user_id == current_user.id,
            ReadingAnnotation.session_id == session_id,
        )
    )
    ann = result.scalar_one_or_none()
    if not ann:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Annotation not found")
    return ann


@annotations_router.put("/{session_id}", response_model=AnnotationResponse)
async def save_annotation(
    session_id: str,
    body: AnnotationSave,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReadingAnnotation).where(
            ReadingAnnotation.user_id == current_user.id,
            ReadingAnnotation.session_id == session_id,
        )
    )
    ann = result.scalar_one_or_none()
    if ann:
        ann.highlights = body.highlights
        ann.note = body.note
        if body.quiz_id:
            ann.quiz_id = body.quiz_id
    else:
        ann = ReadingAnnotation(
            user_id=current_user.id,
            session_id=session_id,
            quiz_id=body.quiz_id,
            highlights=body.highlights,
            note=body.note,
        )
        db.add(ann)
    # get_db auto-commits after request completes
    await db.flush()
    await db.refresh(ann)
    return ann
