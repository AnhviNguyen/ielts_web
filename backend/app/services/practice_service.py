from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import History, User
from app.repositories.history_repository import HistoryRepository
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.progress_repository import ProgressRepository
from app.services.mock_data_service import MockDataService


class PracticeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._mock = MockDataService.default()
        self._session_repo = PracticeSessionRepository(db)
        self._history_repo = HistoryRepository(db)
        self._progress_repo = ProgressRepository(db)

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
        return {"session_id": session.id, "subject": subject, "quiz": quiz_data}

    async def submit(self, user: User, subject: str, session_id: int, answers: dict[str, Any]) -> dict[str, Any]:
        session = await self._session_repo.get_by_id_for_user(session_id=session_id, user_id=user.id)
        if not session or session.session_type != subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice session not found")
        if session.status == "submitted":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already submitted")

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
            qid = str(q.get("id"))
            user_answer = answers.get(qid)
            is_ok = self._is_correct(q, user_answer)
            if is_ok:
                correct += 1
            details.append(
                {
                    "question_id": q.get("id"),
                    "order": q.get("order"),
                    "user_answer": user_answer,
                    "correct_answer": q.get("correct_answer"),
                    "correct_answers": q.get("correct_answers"),
                    "is_correct": is_ok,
                }
            )

        pct = round((correct / max(total, 1)) * 100, 2)
        band = self._estimate_band(raw_score=correct, quiz_type=str(quiz_data.get("type", "")))

        await self._session_repo.mark_submitted(session, score=float(correct))
        await self._history_repo.create(
            user_id=user.id,
            quiz_id=str(session.quiz_id),
            subject=subject.capitalize(),
            score=correct,
            total_questions=total,
            percentage=pct,
            answers=answers,
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

        return {
            "session_id": session.id,
            "subject": subject,
            "quiz_id": session.quiz_id,
            "score": correct,
            "total_questions": total,
            "percentage": pct,
            "estimated_band": band,
            "details": details,
        }

    async def get_history(self, user: User, page: int, page_size: int) -> dict[str, Any]:
        offset = (page - 1) * page_size
        result = await self._db.execute(
            select(History)
            .where(History.user_id == user.id, History.subject.in_(["Reading", "Listening"]))
            .order_by(History.completed_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = result.scalars().all()
        count_result = await self._db.execute(
            select(History.id).where(History.user_id == user.id, History.subject.in_(["Reading", "Listening"]))
        )
        total = len(count_result.scalars().all())
        return {
            "items": [
                {
                    "id": i.id,
                    "quiz_id": i.quiz_id,
                    "subject": i.subject,
                    "score": i.score,
                    "total_questions": i.total_questions,
                    "percentage": i.percentage,
                    "completed_at": i.completed_at,
                }
                for i in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
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
                "completed_at": history.completed_at,
            },
        }

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
