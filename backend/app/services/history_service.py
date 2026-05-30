"""
app/services/history_service.py
─────────────────────────────────
Business logic for saving practice results and updating progress.
Orchestrates HistoryRepository + ProgressRepository in a single transaction.
"""

import logging
import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.history_repository import HistoryRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.schemas import HistoryListItem, HistoryResponse, HistorySave, PaginatedHistory
from app.core.xp import xp_from_duration
from app.services.mock_data_service import MockDataService
from app.services.practice_service import PracticeService

logger = logging.getLogger(__name__)


class HistoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._history_repo = HistoryRepository(db)
        self._progress_repo = ProgressRepository(db)
        self._profile_repo = ProfileRepository(db)
        self._mock = MockDataService.default()

    @staticmethod
    def _skill_from_subject(subject: str | None) -> str:
        return (subject or "reading").strip().lower()

    def _resolve_title(
        self,
        quiz_id: str | None,
        subject: str | None,
        *,
        load_quiz: bool = False,
    ) -> str:
        if quiz_id and str(quiz_id).startswith("vocab:"):
            return "Ôn từ vựng (SRS)"
        if load_quiz and quiz_id:
            try:
                raw = self._mock.get_quiz_raw(int(quiz_id))
                if raw:
                    data = raw.get("data", raw)
                    title = data.get("title")
                    if title:
                        return str(title)
            except (ValueError, TypeError):
                pass
        subj = (subject or "IELTS").strip()
        return f"{subj} practice"

    def _to_list_item(self, entry) -> HistoryListItem:
        skill = self._skill_from_subject(entry.subject)
        return HistoryListItem(
            id=entry.id,
            user_id=entry.user_id,
            quiz_id=entry.quiz_id,
            session_id=entry.practice_session_id,
            subject=entry.subject,
            skill=skill,
            title=self._resolve_title(entry.quiz_id, entry.subject, load_quiz=False),
            score=entry.score,
            total_questions=entry.total_questions,
            percentage=entry.percentage,
            band_score=entry.band_score,
            mode=entry.mode,
            duration_seconds=entry.duration_seconds,
            completed_at=entry.completed_at,
        )

    def _validated_payload(self, payload: HistorySave) -> HistorySave:
        """Clamp client fields; recalculate score for reading/listening when answers provided."""
        subject = (payload.subject or "Reading").strip().capitalize()
        subject_lower = subject.lower()
        total = max(int(payload.total_questions or 0), 1)
        score = max(0, min(int(payload.score or 0), total))
        band = payload.band_score
        if band is not None:
            band = max(0.0, min(9.0, float(band)))
        duration = payload.duration_seconds
        if duration is not None:
            duration = max(0, min(int(duration), 86_400))
        answers = payload.answers
        percentage = round((score / total) * 100, 2)

        if subject_lower in ("reading", "listening") and payload.quiz_id and isinstance(answers, dict) and answers:
            try:
                qid = int(str(payload.quiz_id).strip())
                quiz_raw = self._mock.get_quiz_raw(qid)
                if quiz_raw:
                    quiz_data = quiz_raw.get("data", quiz_raw)
                    score, total, percentage, band = PracticeService.score_from_quiz_answers(
                        quiz_data, answers
                    )
            except (ValueError, TypeError):
                pass

        return HistorySave(
            quiz_id=payload.quiz_id,
            subject=subject,
            score=score,
            total_questions=total,
            percentage=percentage,
            band_score=band,
            mode=payload.mode or "practice",
            duration_seconds=duration,
            answers=answers,
        )

    async def save_practice_result(self, user: User, payload: HistorySave) -> HistoryResponse:
        """
        Persist a practice attempt and atomically update the subject progress,
        streak, and XP:
        1. Insert history record
        2. Fetch existing progress (if any) for this subject
        3. Increment completed_questions by attempt score (capped at total)
        4. Upsert progress with recalculated percentage
        5. Update streak + add XP (10 min = 1 XP, min 1 XP)
        """
        payload = self._validated_payload(payload)
        # 1. Save history entry
        entry = await self._history_repo.create(
            user_id=user.id,
            quiz_id=payload.quiz_id,
            subject=payload.subject,
            score=payload.score,
            total_questions=payload.total_questions,
            percentage=payload.percentage,
            answers=payload.answers,
            band_score=payload.band_score,
            mode=payload.mode,
            duration_seconds=payload.duration_seconds,
        )

        # 2. Update subject progress
        existing = await self._progress_repo.get_by_subject(user.id, payload.subject)

        if existing:
            new_total = max(existing.total_questions, payload.total_questions)
            new_completed = min(existing.completed_questions + payload.score, new_total)
        else:
            new_total = payload.total_questions
            new_completed = payload.score

        new_pct = round((new_completed / max(new_total, 1)) * 100, 2)
        new_pct = min(new_pct, 100.0)

        await self._progress_repo.upsert(
            user_id=user.id,
            subject=payload.subject,
            total_questions=new_total,
            completed_questions=new_completed,
            percentage=new_pct,
        )

        # 5. Update streak + XP (1 XP per 10 minutes, minimum 1 XP)
        duration_secs = payload.duration_seconds or 0
        xp_earned = xp_from_duration(duration_secs)
        await self._profile_repo.update_streak_and_xp(user.id, xp_to_add=xp_earned)
        from app.core.cache import invalidate_leaderboard_cache

        invalidate_leaderboard_cache()

        from app.services.adaptive_study_service import AdaptiveStudyService

        await AdaptiveStudyService(self._history_repo._db).record_activity(
            user.id,
            subject=payload.subject,
            percentage=payload.percentage,
            band_score=payload.band_score,
        )

        logger.info(
            "Practice attempt saved: user_id=%s subject=%s score=%s/%s pct=%.1f%% xp_earned=%d",
            user.id,
            payload.subject,
            payload.score,
            payload.total_questions,
            payload.percentage,
            xp_earned,
        )

        return HistoryResponse.model_validate(entry)

    async def get_history(
        self,
        user: User,
        page: int,
        page_size: int,
        subject: str | None = None,
    ) -> PaginatedHistory:
        """Return a paginated list of the user's practice attempts."""
        items, total = await self._history_repo.get_paginated(
            user.id, page, page_size, subject=subject
        )
        total_pages = math.ceil(total / page_size) if total else 1

        return PaginatedHistory(
            items=[self._to_list_item(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
