from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import History, User
from app.repositories.history_repository import HistoryRepository
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.core.cache import invalidate_leaderboard_cache
from app.core.xp import xp_from_duration
from app.services.mock_data_service import MockDataService
from app.utils.quiz_sanitizer import strip_quiz_answers


class PracticeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._mock = MockDataService.default()
        self._session_repo = PracticeSessionRepository(db)
        self._history_repo = HistoryRepository(db)
        self._progress_repo = ProgressRepository(db)
        self._profile_repo = ProfileRepository(db)

    async def create_session(self, user: User, subject: str, quiz_id: int | None = None) -> dict[str, Any]:
        quiz_raw = self._mock.get_quiz_raw(quiz_id) if quiz_id else self._mock.get_random_quiz_raw(subject=subject)
        if not quiz_raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No quiz data found")

        quiz_data = quiz_raw.get("data", quiz_raw)
        session = await self._session_repo.create(
            user_id=user.id,
            session_type=subject,
            quiz_id=str(quiz_data.get("id")) if quiz_data.get("id") is not None else None,
        )
        return {"session_id": session.id, "subject": subject, "quiz": strip_quiz_answers(quiz_data)}

    async def check_answer(
        self,
        user: User,
        session_id: int,
        question_id: int | str,
        user_answer: Any,
    ) -> dict[str, Any]:
        """Practice mode: reveal correctness + model answer for one question (server-side only)."""
        session = await self._session_repo.get_by_id_for_user(session_id=session_id, user_id=user.id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice session not found")
        if session.status == "submitted":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already submitted")
        if not session.quiz_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session has no quiz assigned")

        quiz_raw = self._mock.get_quiz_raw(int(session.quiz_id))
        if not quiz_raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz data not found")
        quiz_data = quiz_raw.get("data", quiz_raw)

        for item in self._flatten_questions(quiz_data):
            q = item.get("question") or {}
            if str(q.get("id")) != str(question_id):
                continue
            is_ok = self._is_correct(q, user_answer)
            correct_answers = q.get("correct_answers") if isinstance(q.get("correct_answers"), list) else []
            return {
                "is_correct": is_ok,
                "correct_answer": q.get("correct_answer"),
                "correct_answers": [str(a) for a in correct_answers],
                "explain": q.get("explain") or "",
                "listen_from": q.get("listen_from"),
                "user_answer": user_answer,
            }

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in this quiz")

    async def submit(
        self,
        user: User,
        subject: str,
        session_id: int,
        answers: dict[str, Any],
        duration_seconds: int = 0,
    ) -> dict[str, Any]:
        session = await self._session_repo.get_by_id_for_user(session_id=session_id, user_id=user.id)
        if not session or session.session_type != subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice session not found")
        if session.status == "submitted":
            result = await self._result_for_submitted_session(user, session, subject)
            result["new_badges"] = []
            return result

        from app.services.badge_service import BadgeService

        badge_svc = BadgeService(self._db)
        before_unlocked = await badge_svc.get_unlocked_ids(user)

        if not session.quiz_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session has no quiz assigned")

        quiz_raw = self._mock.get_quiz_raw(int(session.quiz_id))
        if not quiz_raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz data not found")
        quiz_data = quiz_raw.get("data", quiz_raw)
        flat = self._flatten_questions(quiz_data)
        total = len(flat)
        correct = 0
        details: list[dict[str, Any]] = []

        for item in flat:
            q = item.get("question") or {}
            part = item.get("part") or {}
            qid = str(q.get("id"))
            user_answer = answers.get(qid)
            is_ok = self._is_correct(q, user_answer)
            if is_ok:
                correct += 1
            details.append(
                {
                    "question_id": q.get("id"),
                    "order": q.get("order"),
                    "part_index": part.get("order", 0),  # 0-based part index for grouping
                    "part_title": part.get("title") or f"Part {part.get('order', 1)}",
                    "user_answer": user_answer,
                    "correct_answer": q.get("correct_answer"),
                    "correct_answers": q.get("correct_answers"),
                    "explanation": q.get("explanation") or q.get("explain"),
                    "listen_from": q.get("listen_from"),
                    "locate_info": q.get("locate_info"),
                    "is_correct": is_ok,
                }
            )

        pct = round((correct / max(total, 1)) * 100, 2)
        band = self._estimate_band(raw_score=correct, quiz_type=str(quiz_data.get("type", "")))

        await self._session_repo.mark_submitted(session, score=float(correct))
        await self._history_repo.create(
            user_id=user.id,
            quiz_id=str(session.quiz_id),
            practice_session_id=session.id,
            subject=subject.capitalize(),
            score=correct,
            total_questions=total,
            percentage=pct,
            answers=answers,
            band_score=band,
            mode="practice",
            duration_seconds=max(0, int(duration_seconds or 0)),
        )

        existing = await self._progress_repo.get_by_subject(user.id, subject.capitalize())
        if existing:
            new_total = max(existing.total_questions, total)
            new_completed = min(existing.completed_questions + correct, new_total)
        else:
            new_total = total
            new_completed = correct
        new_pct = round((new_completed / max(new_total, 1)) * 100, 2)
        await self._progress_repo.upsert(
            user_id=user.id,
            subject=subject.capitalize(),
            total_questions=new_total,
            completed_questions=new_completed,
            percentage=new_pct,
        )

        xp_earned = xp_from_duration(duration_seconds)
        await self._profile_repo.update_streak_and_xp(user.id, xp_to_add=xp_earned)
        invalidate_leaderboard_cache()

        from app.services.adaptive_study_service import AdaptiveStudyService

        await AdaptiveStudyService(self._db).record_activity(
            user.id,
            subject=subject.capitalize(),
            percentage=pct,
            band_score=band,
        )

        new_badges = await badge_svc.detect_new_badges(user, before_unlocked)

        return {
            "session_id": session.id,
            "subject": subject,
            "quiz_id": session.quiz_id,
            "score": correct,
            "total_questions": total,
            "percentage": pct,
            "estimated_band": band,
            "details": details,
            "new_badges": new_badges,
        }

    async def _result_for_submitted_session(
        self, user: User, session: Any, subject: str
    ) -> dict[str, Any]:
        """Idempotent submit — return prior result without re-scoring."""
        result = await self._db.execute(
            select(History)
            .where(
                History.user_id == user.id,
                History.practice_session_id == session.id,
            )
            .order_by(History.completed_at.desc())
        )
        history = result.scalars().first()
        if not history:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session already submitted",
            )
        quiz_raw = self._mock.get_quiz_raw(int(session.quiz_id))
        quiz_data = (quiz_raw or {}).get("data", quiz_raw) if quiz_raw else {}
        details = self._build_details_from_answers(quiz_data, history.answers or {})
        return {
            "session_id": session.id,
            "subject": subject,
            "quiz_id": session.quiz_id,
            "score": history.score,
            "total_questions": history.total_questions,
            "percentage": history.percentage,
            "estimated_band": history.band_score or 0.0,
            "details": details,
        }

    async def get_session_result(self, user: User, session_id: int) -> dict[str, Any]:
        session = await self._session_repo.get_by_id_for_user(session_id=session_id, user_id=user.id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice session not found")
        if not session.quiz_id:
            return {"session_id": session_id, "history": None}

        result = await self._db.execute(
            select(History)
            .where(
                History.user_id == user.id,
                History.quiz_id == str(session.quiz_id),
                History.subject == session.session_type.capitalize(),
            )
            .order_by(History.completed_at.desc())
        )
        history = result.scalars().first()
        if not history:
            return {"session_id": session_id, "history": None}

        quiz_raw = self._mock.get_quiz_raw(int(session.quiz_id))
        quiz_data = (quiz_raw or {}).get("data", quiz_raw) if quiz_raw else {}
        details = self._build_details_from_answers(quiz_data, history.answers or {})

        return {
            "session_id": session_id,
            "history": {
                "id": history.id,
                "quiz_id": history.quiz_id,
                "subject": history.subject,
                "score": history.score,
                "total_questions": history.total_questions,
                "percentage": history.percentage,
                "answers": history.answers,
                "details": details,
                "completed_at": history.completed_at,
            },
        }

    async def get_latest_history_by_quiz(self, user: User, quiz_id: int) -> dict[str, Any]:
        """Latest practice attempt for a quiz — used by History → Review (no session id)."""
        result = await self._db.execute(
            select(History)
            .where(History.user_id == user.id, History.quiz_id == str(quiz_id))
            .order_by(History.completed_at.desc())
        )
        history = result.scalars().first()
        if not history:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No history for this quiz")

        quiz_raw = self._mock.get_quiz_raw(quiz_id)
        quiz_data = (quiz_raw or {}).get("data", quiz_raw) if quiz_raw else {}
        details = self._build_details_from_answers(quiz_data, history.answers or {})

        return {
            "session_id": history.practice_session_id,
            "history": {
                "id": history.id,
                "quiz_id": history.quiz_id,
                "subject": history.subject,
                "score": history.score,
                "total_questions": history.total_questions,
                "percentage": history.percentage,
                "answers": history.answers,
                "details": details,
                "completed_at": history.completed_at,
            },
        }

    def _build_details_from_answers(
        self, quiz_data: dict[str, Any], answers: dict[str, Any]
    ) -> list[dict[str, Any]]:
        flat = self._flatten_questions(quiz_data)
        details: list[dict[str, Any]] = []
        for item in flat:
            q = item.get("question") or {}
            part = item.get("part") or {}
            qid = str(q.get("id"))
            user_answer = answers.get(qid)
            is_ok = self._is_correct(q, user_answer)
            details.append(
                {
                    "question_id": q.get("id"),
                    "order": q.get("order"),
                    "part_index": part.get("order", 0),
                    "part_title": part.get("title") or f"Part {part.get('order', 1)}",
                    "user_answer": user_answer,
                    "correct_answer": q.get("correct_answer"),
                    "correct_answers": q.get("correct_answers"),
                    "explanation": q.get("explanation") or q.get("explain"),
                    "listen_from": q.get("listen_from"),
                    "locate_info": q.get("locate_info"),
                    "is_correct": is_ok,
                }
            )
        return details

    @staticmethod
    def _normalize_text(value: Any) -> str:
        return str(value or "").strip().lower()

    def _is_correct(self, question: dict[str, Any], user_answer: Any) -> bool:
        if isinstance(question.get("correct_answers"), list) and question["correct_answers"]:
            if isinstance(user_answer, list):
                ua = sorted(self._normalize_text(v) for v in user_answer)
                ca = sorted(self._normalize_text(v) for v in question["correct_answers"])
                return ua == ca
            ua = self._normalize_text(user_answer)
            return any(self._normalize_text(v) == ua for v in question["correct_answers"])

        correct_answer = question.get("correct_answer")
        if correct_answer is not None and str(correct_answer).strip() != "":
            return self._normalize_text(user_answer) == self._normalize_text(correct_answer)
        return False

    @classmethod
    def score_from_quiz_answers(cls, quiz_data: dict[str, Any], answers: dict[str, Any]) -> tuple[int, int, float, float]:
        """Server-side score for history validation (reading/listening)."""
        flat = cls._flatten_questions(quiz_data)
        total = len(flat)
        scorer = cls.__new__(cls)
        correct = 0
        for item in flat:
            q = item.get("question") or {}
            qid = str(q.get("id"))
            if scorer._is_correct(q, answers.get(qid)):
                correct += 1
        pct = round((correct / max(total, 1)) * 100, 2)
        band = cls._estimate_band(correct, str(quiz_data.get("type", "")))
        return correct, total, pct, band

    @staticmethod
    def _flatten_questions(quiz_data: dict[str, Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for part in quiz_data.get("parts", []):
            for qset in part.get("question_sets", []):
                for q in qset.get("questions", []):
                    out.append({"part": part, "question_set": qset, "question": q})
        out.sort(key=lambda x: x.get("question", {}).get("order") or 0)
        return out

    @staticmethod
    def _estimate_band(raw_score: int, quiz_type: str) -> float:
        is_listening = quiz_type == "10"
        table = (
            [(39, 9), (37, 8.5), (35, 8), (32, 7.5), (30, 7), (26, 6.5), (23, 6), (18, 5.5), (16, 5), (13, 4.5), (11, 4), (8, 3.5), (6, 3), (4, 2.5), (0, 2)]
            if is_listening
            else [(39, 9), (37, 8.5), (35, 8), (33, 7.5), (30, 7), (27, 6.5), (23, 6), (19, 5.5), (15, 5), (13, 4.5), (10, 4), (8, 3.5), (6, 3), (4, 2.5), (0, 2)]
        )
        for min_score, band in table:
            if raw_score >= min_score:
                return float(band)
        return 0.0
