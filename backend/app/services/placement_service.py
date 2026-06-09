"""Placement onboarding: manual bands and compact 4-skill diagnostic."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import PlacementSession, User, UserProfile
from app.repositories.history_repository import HistoryRepository
from app.repositories.progress_repository import ProgressRepository
from app.schemas import (
    PlacementBands,
    PlacementFinalizeResponse,
    PlacementFullExamFinalizeRequest,
    PlacementManualRequest,
    PlacementSessionResponse,
    PlacementStageResponse,
    PlacementStageSubmitRequest,
    PlacementStageSubmitResponse,
    PlacementStatusResponse,
)
from app.services.adaptive_study_service import AdaptiveStudyService
from app.services.full_exam_service import FullExamService
from app.services.mock_data_service import MockDataService
from app.services.practice_service import PracticeService
from app.services.writing_service import WritingService
from app.utils.quiz_sanitizer import strip_quiz_answers

_STAGES = ("reading", "listening", "writing", "speaking")


class PlacementService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._mock = MockDataService.default()
        self._history = HistoryRepository(db)
        self._progress = ProgressRepository(db)

    async def status(self, user: User) -> PlacementStatusResponse:
        profile = await self._profile(user.id)
        active = await self._active_session(user.id)
        placement_status = profile.placement_status or "pending"
        initial_source = profile.initial_band_source
        completed_at = profile.placement_completed_at
        if placement_status != "completed" and not self._requires_placement(user):
            placement_status = "completed"
            initial_source = initial_source or "legacy"
            completed_at = completed_at or user.created_at
        bands = None
        if profile.initial_overall_band is not None:
            bands = PlacementBands(
                reading=float(profile.initial_reading_band or 0),
                listening=float(profile.initial_listening_band or 0),
                writing=float(profile.initial_writing_band or 0),
                speaking=float(profile.initial_speaking_band or 0),
                overall=float(profile.initial_overall_band or 0),
            )
        return PlacementStatusResponse(
            placement_status=placement_status,
            initial_band_source=initial_source,
            bands=bands,
            placement_completed_at=completed_at,
            active_session_id=active.id if active else None,
        )

    async def submit_manual(self, user: User, payload: PlacementManualRequest) -> PlacementFinalizeResponse:
        bands = {
            "reading": self._valid_band(payload.reading, strict=True),
            "listening": self._valid_band(payload.listening, strict=True),
            "writing": self._valid_band(payload.writing, strict=True),
            "speaking": self._valid_band(payload.speaking, strict=True),
        }
        overall = self._overall(bands.values())
        await self._complete_profile(user.id, source="manual", bands={**bands, "overall": overall})
        await self._persist_baseline(user.id, source="manual", bands=bands)
        return PlacementFinalizeResponse(
            placement_status="completed",
            bands=PlacementBands(**bands, overall=overall),
        )

    async def finalize_full_exam(
        self,
        user: User,
        payload: PlacementFullExamFinalizeRequest,
    ) -> PlacementFinalizeResponse:
        bands = {
            "reading": self._valid_band(payload.reading),
            "listening": self._valid_band(payload.listening),
            "writing": self._valid_band(payload.writing),
            "speaking": self._valid_band(payload.speaking),
        }
        overall = self._overall(bands.values())
        results = payload.results or {}
        metadata = {
            "set_id": payload.set_id,
            "session_id": payload.session_id,
            "results": results,
        }
        await self._complete_profile(user.id, source="full_exam", bands={**bands, "overall": overall})
        await self._persist_baseline(
            user.id,
            source="full_exam",
            bands=bands,
            results_override={
                "reading": {"band": bands["reading"], "result": results.get("reading"), "metadata": metadata},
                "listening": {"band": bands["listening"], "result": results.get("listening"), "metadata": metadata},
                "writing": {"band": bands["writing"], "result": results.get("writing"), "metadata": metadata},
                "speaking": {"band": bands["speaking"], "result": results.get("speaking"), "metadata": metadata},
            },
        )
        return PlacementFinalizeResponse(
            placement_status="completed",
            bands=PlacementBands(**bands, overall=overall),
        )

    async def create_session(self, user: User) -> PlacementSessionResponse:
        profile = await self._profile(user.id)
        if profile.placement_status == "completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Placement already completed")

        active = await self._active_session(user.id)
        if active:
            return PlacementSessionResponse.model_validate(active)

        ids = self._pick_content_ids()
        row = PlacementSession(
            user_id=user.id,
            current_stage="reading",
            reading_quiz_id=ids.get("reading"),
            listening_quiz_id=ids.get("listening"),
            writing_topic_id=ids.get("writing"),
            speaking_quiz_id=ids.get("speaking"),
            results={},
        )
        self._db.add(row)
        await self._db.flush()
        await self._db.refresh(row)
        return PlacementSessionResponse.model_validate(row)

    async def current_session(self, user: User) -> PlacementSessionResponse | None:
        active = await self._active_session(user.id)
        return PlacementSessionResponse.model_validate(active) if active else None

    async def get_stage(self, user: User, session_id: int, stage: str) -> PlacementStageResponse:
        stage = self._normalize_stage(stage)
        session = await self._session_for_user(user.id, session_id)
        payload = await self._stage_payload(session, stage)
        return PlacementStageResponse(
            session=PlacementSessionResponse.model_validate(session),
            stage=stage,
            payload=payload,
        )

    async def submit_stage(
        self,
        user: User,
        session_id: int,
        stage: str,
        payload: PlacementStageSubmitRequest,
    ) -> PlacementStageSubmitResponse:
        stage = self._normalize_stage(stage)
        session = await self._session_for_user(user.id, session_id)
        if session.status == "completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Placement session already completed")

        if stage in ("reading", "listening"):
            result = await self._score_objective_stage(session, stage, payload.answers)
        elif stage == "writing":
            result = await self._score_writing_stage(session, payload)
        else:
            result = self._score_speaking_stage(payload)

        results = dict(session.results or {})
        results[stage] = result
        session.results = results
        session.current_stage = self._next_stage(stage)
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)
        return PlacementStageSubmitResponse(
            session=PlacementSessionResponse.model_validate(session),
            stage=stage,
            result=result,
        )

    async def finalize(self, user: User, session_id: int) -> PlacementFinalizeResponse:
        session = await self._session_for_user(user.id, session_id)
        results = session.results or {}
        missing = [stage for stage in _STAGES if stage not in results]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing placement stages: {', '.join(missing)}",
            )

        bands = {stage: self._valid_band(float(results[stage].get("band") or 0)) for stage in _STAGES}
        overall = self._overall(bands.values())
        await self._complete_profile(user.id, source="diagnostic", bands={**bands, "overall": overall})
        await self._persist_baseline(user.id, source="diagnostic", bands=bands, session=session)

        session.status = "completed"
        session.current_stage = "done"
        session.completed_at = datetime.now(timezone.utc)
        self._db.add(session)
        await self._db.flush()

        return PlacementFinalizeResponse(
            placement_status="completed",
            bands=PlacementBands(**bands, overall=overall),
        )

    async def _profile(self, user_id: int) -> UserProfile:
        rs = await self._db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = rs.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return profile

    async def _active_session(self, user_id: int) -> PlacementSession | None:
        rs = await self._db.execute(
            select(PlacementSession)
            .where(PlacementSession.user_id == user_id, PlacementSession.status == "started")
            .order_by(PlacementSession.started_at.desc())
        )
        return rs.scalars().first()

    async def _session_for_user(self, user_id: int, session_id: int) -> PlacementSession:
        rs = await self._db.execute(
            select(PlacementSession).where(
                PlacementSession.id == session_id,
                PlacementSession.user_id == user_id,
            )
        )
        session = rs.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement session not found")
        return session

    def _pick_content_ids(self) -> dict[str, str | None]:
        sets = FullExamService(self._mock).list_sets(limit=1)
        if sets:
            item = sets[0]
            return {
                "reading": str(item.get("reading_quiz_id") or ""),
                "listening": str(item.get("listening_quiz_id") or ""),
                "writing": str(item.get("writing_task2_topic_id") or ""),
                "speaking": str(item.get("speaking_quiz_id") or ""),
            }
        reading = (self._mock.list_mock_tests(skill_id=1) or [{}])[0]
        listening = (self._mock.list_mock_tests(skill_id=2) or [{}])[0]
        writing = (self._mock.list_writing_topics(task_type=2) or [{}])[0]
        return {
            "reading": str(((reading.get("quizzes") or {}).get("full") or {}).get("id") or ""),
            "listening": str(((listening.get("quizzes") or {}).get("full") or {}).get("id") or ""),
            "writing": str(writing.get("id") or ""),
            "speaking": None,
        }

    async def _stage_payload(self, session: PlacementSession, stage: str) -> dict[str, Any]:
        if stage in ("reading", "listening"):
            quiz = self._compact_quiz(getattr(session, f"{stage}_quiz_id"), stage)
            return {"quiz": strip_quiz_answers(quiz), "instructions": "Complete this short diagnostic section."}
        if stage == "writing":
            detail = self._writing_detail(session.writing_topic_id)
            return {"topic": detail, "instructions": "Write a short IELTS-style response for diagnostic scoring."}
        return {"question": self._speaking_prompt(session.speaking_quiz_id)}

    async def _score_objective_stage(
        self,
        session: PlacementSession,
        stage: str,
        answers: dict[str, Any],
    ) -> dict[str, Any]:
        quiz = self._compact_quiz(getattr(session, f"{stage}_quiz_id"), stage)
        score, total, pct, _band = PracticeService.score_from_quiz_answers(quiz, answers)
        band = self._valid_band((pct / 100) * 9)
        return {
            "score": score,
            "total_questions": total,
            "percentage": pct,
            "band": band,
            "quiz_id": getattr(session, f"{stage}_quiz_id"),
        }

    async def _score_writing_stage(
        self,
        session: PlacementSession,
        payload: PlacementStageSubmitRequest,
    ) -> dict[str, Any]:
        essay = (payload.essay_text or "").strip()
        if len(essay.split()) < 20:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Writing answer is too short.")
        topic = self._writing_detail(session.writing_topic_id)
        prompt = topic.get("prompt_text") or topic.get("title") or ""
        evaluation = await WritingService(self._db)._evaluate_essay(
            task_type=int(topic.get("task_type") or 2),
            prompt_text=prompt,
            essay_text=essay,
            word_count=len(essay.split()),
        )
        band = self._valid_band(float(evaluation.get("overall_band") or 0))
        return {
            "band": band,
            "evaluation": evaluation,
            "topic_id": session.writing_topic_id,
            "duration_seconds": payload.duration_seconds,
        }

    def _score_speaking_stage(self, payload: PlacementStageSubmitRequest) -> dict[str, Any]:
        text = (payload.transcript_text or "").strip()
        if len(text.split()) < 15:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Speaking transcript is too short.")
        words = len(text.split())
        unique_ratio = len({w.lower().strip(".,!?;:") for w in text.split()}) / max(words, 1)
        raw = 3.5 + min(words, 120) / 35 + min(unique_ratio, 0.85) * 1.4
        band = self._valid_band(min(8.0, raw))
        return {
            "band": band,
            "word_count": words,
            "feedback": "Diagnostic speaking estimate from transcript length and lexical range.",
            "duration_seconds": payload.duration_seconds,
        }

    def _compact_quiz(self, quiz_id: str | None, stage: str) -> dict[str, Any]:
        if not quiz_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No {stage} diagnostic quiz configured")
        raw = self._mock.get_quiz_raw(int(quiz_id))
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{stage.title()} quiz not found")
        data = copy.deepcopy(raw.get("data", raw))
        parts = data.get("parts") or []
        if parts:
            data["parts"] = [parts[0]]
        total = len(PracticeService._flatten_questions(data))
        data["question_count"] = total
        return data

    def _writing_detail(self, topic_id: str | None) -> dict[str, Any]:
        if not topic_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No writing diagnostic topic configured")
        raw = self._mock.get_writing_topic_detail(int(topic_id))
        data = (raw or {}).get("data") or {}
        question = (data.get("questions") or [{}])[0]
        return {
            "id": data.get("id") or topic_id,
            "title": data.get("title") or question.get("title") or "IELTS Writing Diagnostic",
            "task_type": data.get("task_type") or question.get("task_type") or 2,
            "prompt_text": question.get("content_writing") or question.get("title") or data.get("title") or "",
        }

    def _speaking_prompt(self, quiz_id: str | None) -> dict[str, Any]:
        default = {
            "question_text": "Describe a goal you want to achieve in your IELTS study. You should explain why it matters and how you plan to reach it.",
            "time_limit_seconds": 90,
        }
        if not quiz_id:
            return default
        try:
            raw = self._mock.get_quiz_raw(int(quiz_id))
            data = (raw or {}).get("data", raw) if raw else {}
            flat = PracticeService._flatten_questions(data)
            question = (flat[0].get("question") if flat else {}) or {}
            return {
                "quiz_id": quiz_id,
                "question_id": question.get("id"),
                "question_text": question.get("title") or question.get("question") or default["question_text"],
                "description": question.get("description") or "",
                "time_limit_seconds": int(question.get("time_limit") or 90),
            }
        except Exception:
            return default

    async def _complete_profile(self, user_id: int, *, source: str, bands: dict[str, float]) -> None:
        profile = await self._profile(user_id)
        profile.placement_status = "completed"
        profile.initial_band_source = source
        profile.initial_reading_band = bands["reading"]
        profile.initial_listening_band = bands["listening"]
        profile.initial_writing_band = bands["writing"]
        profile.initial_speaking_band = bands["speaking"]
        profile.initial_overall_band = bands["overall"]
        profile.placement_completed_at = datetime.now(timezone.utc)
        self._db.add(profile)
        await self._db.flush()

    async def _persist_baseline(
        self,
        user_id: int,
        *,
        source: str,
        bands: dict[str, float],
        session: PlacementSession | None = None,
        results_override: dict[str, Any] | None = None,
    ) -> None:
        results = results_override if results_override is not None else (
            session.results if session and isinstance(session.results, dict) else {}
        )
        for stage, band in bands.items():
            subject = stage.capitalize()
            score = int(round((band / 9) * 40))
            total = 40
            pct = round((band / 9) * 100, 2)
            detail = results.get(stage, {}) if isinstance(results, dict) else {}
            await self._history.create(
                user_id=user_id,
                quiz_id=str(detail.get("quiz_id") or f"placement:{stage}"),
                subject=subject,
                score=score,
                total_questions=total,
                percentage=pct,
                band_score=band,
                mode="placement",
                duration_seconds=int(detail.get("duration_seconds") or 0),
                answers={"source": source, "placement_session_id": session.id if session else None, "result": detail},
            )
            await self._progress.upsert(
                user_id=user_id,
                subject=subject,
                total_questions=total,
                completed_questions=score,
                percentage=pct,
                band_score=band,
            )
            await AdaptiveStudyService(self._db).record_activity(
                user_id,
                subject=subject,
                percentage=pct,
                band_score=band,
            )

    @staticmethod
    def _valid_band(value: float, *, strict: bool = False) -> float:
        band = max(0.0, min(9.0, round(float(value) * 2) / 2))
        if strict and abs((float(value) * 2) - round(float(value) * 2)) > 1e-6:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bands must use 0.5 increments")
        return band

    @staticmethod
    def _overall(values) -> float:
        return max(0.0, min(9.0, round((sum(values) / 4) * 2) / 2))

    @staticmethod
    def _requires_placement(user: User) -> bool:
        cutoff_raw = (settings.PLACEMENT_REQUIRED_AFTER or "").strip()
        if not cutoff_raw or not user.created_at:
            return True
        try:
            cutoff = datetime.fromisoformat(cutoff_raw.replace("Z", "+00:00"))
        except ValueError:
            return True
        created_at = user.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)
        return created_at >= cutoff

    @staticmethod
    def _normalize_stage(stage: str) -> str:
        key = (stage or "").strip().lower()
        if key not in _STAGES:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown placement stage")
        return key

    @staticmethod
    def _next_stage(stage: str) -> str:
        idx = _STAGES.index(stage)
        return _STAGES[idx + 1] if idx < len(_STAGES) - 1 else "review"
