"""
app/routers/vocabulary.py
─────────────────────────
Thin HTTP layer for Vocabulary and Reading Annotations.
All business logic lives in VocabService; all DB access in VocabRepository.
"""

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.vocab_lookup_service import stream_word_lookup

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import ReadingAnnotation, User
from app.repositories.vocab_repository import VocabRepository
from app.schemas import (
    AnnotationResponse,
    AnnotationSave,
    VocabBootstrapResponse,
    VocabReadingPassageRequest,
    VocabReadingPassageResponse,
    VocabReviewRequest,
    VocabSessionCompleteRequest,
    VocabSessionCompleteResponse,
    VocabStatsResponse,
    VocabStudyModesResponse,
    VocabStudyQueueResponse,
    VocabTopicCreate,
    VocabTopicDetailResponse,
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


@router.get("/study-modes", response_model=VocabStudyModesResponse)
async def list_study_modes() -> VocabStudyModesResponse:
    """Catalog of vocabulary study modes (flashcard, MCQ, reading, dictation)."""
    return VocabService.list_study_modes()


@router.post("/bootstrap", response_model=VocabBootstrapResponse)
async def bootstrap_vocabulary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VocabBootstrapResponse:
    """Create starter topics/words if the user has none."""
    return await _svc(db).bootstrap_starter_pack(current_user.id)


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

@router.get("/topics/{topic_id}/study-queue", response_model=VocabStudyQueueResponse)
async def get_study_queue(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VocabStudyQueueResponse:
    """SRS queue: words due for review in this topic."""
    return await _svc(db).get_study_queue(topic_id, current_user.id)


@router.post("/topics/{topic_id}/words/{word_id}/review", response_model=VocabWordResponse)
async def record_word_review(
    topic_id: int,
    word_id: int,
    body: VocabReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VocabWordResponse:
    """Apply SM-2 after a study card (quality 0–5)."""
    return await _svc(db).record_review(
        topic_id, word_id, current_user.id, body.quality
    )


@router.post(
    "/topics/{topic_id}/reading-passage",
    response_model=VocabReadingPassageResponse,
)
async def generate_reading_passage(
    topic_id: int,
    body: VocabReadingPassageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VocabReadingPassageResponse:
    """AI cloze passage (2 paragraphs, gaps + Vietnamese hints + answers)."""
    return await _svc(db).generate_reading_passage(
        topic_id, current_user.id, body.word_ids
    )


@router.get("/topics/{topic_id}/words/{word_id}/mcq")
async def get_word_mcq(
    topic_id: int,
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Multiple-choice options for trắc nghiệm mode."""
    return await _svc(db).build_mcq_options(topic_id, current_user.id, word_id)


@router.get("/topics/{topic_id}", response_model=VocabTopicDetailResponse)
async def get_topic_detail(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VocabTopicDetailResponse:
    """Topic + all words (EN, VI meaning, phonetic, example) for management and study."""
    return await _svc(db).get_topic_detail(topic_id, current_user.id)


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

@router.get("/lookup/stream")
async def lookup_word_stream(
    word: str = Query(..., min_length=1, max_length=80, description="English word to look up"),
    _user: User = Depends(get_current_user),
):
    """
    SSE stream: partial field patches while OpenRouter generates, then final result.
    Events: data: {"patch": {...}} | {"done": true, "result": {...}} | {"error": "..."}
    """
    async def event_generator():
        async for chunk in stream_word_lookup(word.strip()):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/words/search", response_model=list[VocabWordResponse])
async def search_words(
    q: str = Query(min_length=1, description="Search query (word or meaning)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search words across ALL topics for the current user."""
    return await _svc(db).search_words(current_user.id, q)


@router.post("/sessions/complete", response_model=VocabSessionCompleteResponse)
async def complete_vocab_session(
    body: VocabSessionCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VocabSessionCompleteResponse:
    """Lưu phiên ôn từ + cộng XP (10 phút = 1 XP, tối thiểu 1 XP)."""
    return await _svc(db).complete_study_session(
        current_user.id,
        body.topic_id,
        body.duration_seconds,
        body.words_reviewed,
    )


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


@annotations_router.get("/{session_id}")
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
        return {
            "session_id": session_id,
            "quiz_id": "",
            "highlights": [],
            "note": "",
        }
    return AnnotationResponse.model_validate(ann)


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
