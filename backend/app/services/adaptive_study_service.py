"""
SRS-inspired adaptive difficulty per skill + next-task recommendation for study plan.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import History, SkillAdaptiveState, StudyPlanTask, User
from app.schemas import StudyPlanNextTaskResponse, StudyPlanTaskResponse
from app.services.vocab_srs import sm2_apply

logger = logging.getLogger(__name__)

SKILLS = ("reading", "listening", "writing", "speaking", "vocabulary")

SUBJECT_TO_SKILL: dict[str, str] = {
    "reading": "reading",
    "listening": "listening",
    "writing": "writing",
    "speaking": "speaking",
    "vocabulary": "vocabulary",
}

_SKILL_ROUTES = {
    "reading": "/reading",
    "listening": "/listening",
    "writing": "/writing",
    "speaking": "/speaking",
    "vocabulary": "/vocabulary",
}

_DIFFICULTY_LABELS = {
    "easy": "Dễ — ôn lại nền tảng",
    "medium": "Trung bình — duy trì nhịp luyện",
    "hard": "Khó — thử thách band cao hơn",
    "challenge": "Thử thách — mock / đề khó",
}


def subject_to_skill(subject: str | None) -> str | None:
    key = (subject or "").strip().lower()
    return SUBJECT_TO_SKILL.get(key)


def performance_to_quality(
    *,
    percentage: float | None = None,
    band_score: float | None = None,
) -> int:
    """Map attempt result to SM-2 quality 0–5."""
    if band_score is not None:
        b = float(band_score)
        if b >= 8.0:
            return 5
        if b >= 7.0:
            return 4
        if b >= 6.0:
            return 3
        if b >= 5.0:
            return 2
        return 1
    pct = float(percentage or 0)
    if pct >= 90:
        return 5
    if pct >= 80:
        return 4
    if pct >= 65:
        return 3
    if pct >= 50:
        return 2
    return 1


def _suggested_difficulty_from_state(state: SkillAdaptiveState, quality: int) -> str:
    reps = int(state.srs_repetitions or 0)
    ease = float(state.srs_ease or 2.5)
    if quality < 3 or reps <= 1:
        return "easy"
    if quality >= 5 and reps >= 4 and ease >= 2.6:
        return "challenge"
    if quality >= 4 and reps >= 2:
        return "hard"
    if reps >= 2:
        return "medium"
    return "easy"


class AdaptiveStudyService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def record_activity(
        self,
        user_id: int,
        *,
        subject: str,
        percentage: float | None = None,
        band_score: float | None = None,
    ) -> None:
        skill = subject_to_skill(subject)
        if not skill:
            return

        quality = performance_to_quality(percentage=percentage, band_score=band_score)
        state = await self._get_or_create_state(user_id, skill)

        patch = sm2_apply(
            quality=quality,
            srs_ease=state.srs_ease,
            srs_interval_days=state.srs_interval_days,
            srs_repetitions=state.srs_repetitions,
        )
        perf = float(percentage or 0)
        if band_score is not None:
            perf = max(perf, (float(band_score) / 9.0) * 100)

        n = int(state.attempt_count or 0)
        new_avg = ((state.avg_performance or 0) * n + perf) / (n + 1)

        state.srs_ease = patch["srs_ease"]
        state.srs_interval_days = patch["srs_interval_days"]
        state.srs_repetitions = patch["srs_repetitions"]
        state.srs_next_review_at = patch["srs_next_review_at"]
        state.srs_last_review_at = patch["srs_last_review_at"]
        state.avg_performance = round(new_avg, 2)
        state.attempt_count = n + 1
        state.suggested_difficulty = _suggested_difficulty_from_state(state, quality)
        self._db.add(state)
        await self._db.flush()

        await self.refresh_plan_priorities(user_id)

    async def refresh_plan_priorities(self, user_id: int) -> None:
        states = await self._all_states(user_id)
        state_map = {s.skill: s for s in states}
        now = datetime.now(timezone.utc)
        today = date.today()

        result = await self._db.execute(
            select(StudyPlanTask).where(
                StudyPlanTask.user_id == user_id,
                StudyPlanTask.is_completed.is_(False),
            )
        )
        tasks = result.scalars().all()
        for task in tasks:
            skill = (task.focus_skill or "reading").lower()
            st = state_map.get(skill)
            due_bonus = 0.0
            weakness_bonus = 0.0
            today_bonus = 0.0
            if st:
                if st.srs_next_review_at and st.srs_next_review_at <= now:
                    due_bonus = 40.0
                weakness_bonus = max(0.0, (100.0 - float(st.avg_performance or 0)) * 0.35)
                task.suggested_difficulty = st.suggested_difficulty
            if task.plan_date and task.plan_date <= today:
                today_bonus = 25.0
            task.priority_score = round(due_bonus + weakness_bonus + today_bonus, 2)
            self._db.add(task)
        await self._db.flush()

    async def get_next_task(self, user: User) -> StudyPlanNextTaskResponse:
        await self.refresh_plan_priorities(user.id)
        states = await self._all_states(user_id=user.id)
        now = datetime.now(timezone.utc)
        today = date.today()

        result = await self._db.execute(
            select(StudyPlanTask)
            .where(
                StudyPlanTask.user_id == user.id,
                StudyPlanTask.is_completed.is_(False),
            )
            .order_by(StudyPlanTask.priority_score.desc(), StudyPlanTask.plan_date, StudyPlanTask.id)
        )
        tasks = result.scalars().all()

        if tasks:
            best = tasks[0]
            skill = (best.focus_skill or "reading").lower()
            st = next((s for s in states if s.skill == skill), None)
            diff = best.suggested_difficulty or (st.suggested_difficulty if st else "medium")
            reason = self._reason_for_task(best, st, now)
            return StudyPlanNextTaskResponse(
                source="study_plan",
                task=StudyPlanTaskResponse.model_validate(best),
                focus_skill=skill,
                suggested_difficulty=diff,
                difficulty_label=_DIFFICULTY_LABELS.get(diff, diff),
                reason=reason,
                route_path=best.route_path or _SKILL_ROUTES.get(skill, "/reading"),
            )

        skill = self._pick_weakest_due_skill(states, now)
        st = next((s for s in states if s.skill == skill), None)
        diff = st.suggested_difficulty if st else "medium"
        desc = self._synthetic_description(skill, diff)
        return StudyPlanNextTaskResponse(
            source="adaptive",
            task=None,
            focus_skill=skill,
            suggested_difficulty=diff,
            difficulty_label=_DIFFICULTY_LABELS.get(diff, diff),
            reason="Chưa có study plan — gợi ý theo kỹ năng cần ôn (SRS).",
            route_path=_SKILL_ROUTES[skill],
            synthetic_description=desc,
            duration_minutes=45 if skill != "vocabulary" else 25,
        )

    async def _get_or_create_state(self, user_id: int, skill: str) -> SkillAdaptiveState:
        result = await self._db.execute(
            select(SkillAdaptiveState).where(
                SkillAdaptiveState.user_id == user_id,
                SkillAdaptiveState.skill == skill,
            )
        )
        state = result.scalar_one_or_none()
        if state:
            return state
        now = datetime.now(timezone.utc)
        state = SkillAdaptiveState(
            user_id=user_id,
            skill=skill,
            srs_next_review_at=now,
            suggested_difficulty="medium",
        )
        self._db.add(state)
        await self._db.flush()
        return state

    async def _all_states(self, user_id: int) -> list[SkillAdaptiveState]:
        result = await self._db.execute(
            select(SkillAdaptiveState).where(SkillAdaptiveState.user_id == user_id)
        )
        existing = {s.skill: s for s in result.scalars().all()}
        out: list[SkillAdaptiveState] = []
        for skill in SKILLS:
            if skill in existing:
                out.append(existing[skill])
            else:
                out.append(await self._get_or_create_state(user_id, skill))
        return out

    @staticmethod
    def _pick_weakest_due_skill(states: list[SkillAdaptiveState], now: datetime) -> str:
        scored: list[tuple[float, str]] = []
        for st in states:
            due = 1.0 if (st.srs_next_review_at and st.srs_next_review_at <= now) else 0.2
            weakness = max(0.0, 100.0 - float(st.avg_performance or 0))
            scored.append((due * 50 + weakness, st.skill))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else "reading"

    @staticmethod
    def _reason_for_task(
        task: StudyPlanTask,
        state: SkillAdaptiveState | None,
        now: datetime,
    ) -> str:
        parts: list[str] = []
        if task.plan_date and task.plan_date <= date.today():
            parts.append("Nhiệm vụ hôm nay trong study plan")
        if state and state.srs_next_review_at and state.srs_next_review_at <= now:
            parts.append("Kỹ năng đến hạn ôn (SRS)")
        if state and float(state.avg_performance or 0) < 60:
            parts.append("Điểm gần đây thấp — ưu tiên cải thiện")
        if not parts:
            parts.append("Ưu tiên theo lịch sử luyện tập gần nhất")
        return " · ".join(parts)

    @staticmethod
    def _synthetic_description(skill: str, difficulty: str) -> str:
        templates = {
            "reading": {
                "easy": "Làm 1 bài Reading ngắn, tập trung tìm keyword",
                "medium": "Hoàn thành 1 bài Reading full (3 passages)",
                "hard": "Reading timed — mục tiêu ≥75%",
                "challenge": "Reading mock khó — phân tích lỗi chi tiết",
            },
            "listening": {
                "easy": "Nghe Section 1–2 và làm lại transcript",
                "medium": "1 bài Listening đầy đủ 4 sections",
                "hard": "Listening timed với distraction",
                "challenge": "Listening mock — không pause audio",
            },
            "writing": {
                "easy": "Viết outline Task 2 (15 phút)",
                "medium": "Hoàn thành Task 2 (~250 từ) + chấm AI",
                "hard": "Task 1 + Task 2 trong 60 phút",
                "challenge": "Writing mock — band mục tiêu +7",
            },
            "speaking": {
                "easy": "Luyện Part 1 — 5 câu trả lời ngắn",
                "medium": "Part 2 cue card 2 phút + Part 3",
                "hard": "Full speaking mock có ghi âm",
                "challenge": "Speaking mock timed + tự đánh giá band",
            },
            "vocabulary": {
                "easy": "Flashcard 10 từ due hôm nay",
                "medium": "SRS session ≥15 từ + reading cloze",
                "hard": "Mixed modes: typing + dictation",
                "challenge": "Ôn 25 từ + passage comprehension",
            },
        }
        return templates.get(skill, {}).get(difficulty, "Luyện tập theo kỹ năng")
