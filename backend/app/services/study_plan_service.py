"""
app/services/study_plan_service.py
────────────────────────────────────
Service layer for AI-generated study plans.
Responsibilities (SRP):
  - Build user context from DB (history + progress)
  - Call OpenRouter to generate a structured plan
  - Persist / extend / complete tasks in study_plan_tasks
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import History, Progress, StudyPlanTask, User, UserProfile
from app.schemas import StudyPlanDayGroup, StudyPlanResponse, StudyPlanTaskResponse

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_OPENROUTER_MODEL = "anthropic/claude-3-haiku"

_SKILL_ROUTES = {
    "reading": "/reading",
    "listening": "/listening",
    "writing": "/writing",
    "speaking": "/speaking",
    "vocabulary": "/vocabulary",
}


class StudyPlanService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────

    async def get_plan(self, user: User) -> StudyPlanResponse:
        result = await self._db.execute(
            select(StudyPlanTask)
            .where(StudyPlanTask.user_id == user.id)
            .order_by(StudyPlanTask.day_number, StudyPlanTask.id)
        )
        tasks = result.scalars().all()
        return self._group_by_day(tasks)

    async def generate_plan(self, user: User) -> StudyPlanResponse:
        """Delete existing plan and generate a fresh 5-day plan via AI."""
        await self._db.execute(
            delete(StudyPlanTask).where(StudyPlanTask.user_id == user.id)
        )
        await self._db.flush()
        tasks = await self._ai_generate(user, start_day=1, num_days=5)
        self._db.add_all(tasks)
        await self._db.flush()
        return self._group_by_day(tasks)

    async def extend_plan(self, user: User) -> StudyPlanResponse:
        """Append 5 more days to the existing plan."""
        result = await self._db.execute(
            select(func.max(StudyPlanTask.day_number)).where(
                StudyPlanTask.user_id == user.id
            )
        )
        max_day = result.scalar_one_or_none() or 0
        tasks = await self._ai_generate(user, start_day=max_day + 1, num_days=5)
        self._db.add_all(tasks)
        await self._db.flush()
        all_result = await self._db.execute(
            select(StudyPlanTask)
            .where(StudyPlanTask.user_id == user.id)
            .order_by(StudyPlanTask.day_number, StudyPlanTask.id)
        )
        return self._group_by_day(all_result.scalars().all())

    async def toggle_complete(
        self, user: User, task_id: int
    ) -> StudyPlanTaskResponse:
        result = await self._db.execute(
            select(StudyPlanTask).where(
                StudyPlanTask.id == task_id,
                StudyPlanTask.user_id == user.id,
            )
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        task.is_completed = not task.is_completed
        task.completed_at = (
            datetime.now(tz=timezone.utc) if task.is_completed else None
        )
        self._db.add(task)
        await self._db.flush()
        return StudyPlanTaskResponse.model_validate(task)

    # ─────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────

    async def _build_context(self, user: User) -> dict:
        """Fetch user profile, progress, and recent history for prompt context."""
        profile_res = await self._db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_res.scalar_one_or_none()

        progress_res = await self._db.execute(
            select(Progress).where(Progress.user_id == user.id)
        )
        progress_rows = progress_res.scalars().all()

        history_res = await self._db.execute(
            select(History)
            .where(History.user_id == user.id)
            .order_by(History.completed_at.desc())
            .limit(30)
        )
        history_rows = history_res.scalars().all()

        done_quiz_ids = {h.quiz_id for h in history_rows if h.quiz_id}

        return {
            "target_band": profile.target_band if profile else 6.5,
            "exam_date": (
                profile.exam_date.isoformat() if profile and profile.exam_date else None
            ),
            "progress": [
                {
                    "skill": r.subject,
                    "band": r.band_score,
                    "pct": r.percentage,
                }
                for r in progress_rows
            ],
            "recent_history": [
                {
                    "skill": h.subject,
                    "quiz_id": h.quiz_id,
                    "band": h.band_score,
                    "score": h.score,
                }
                for h in history_rows[:15]
            ],
            "done_quiz_ids": list(done_quiz_ids),
        }

    async def _ai_generate(
        self, user: User, start_day: int, num_days: int
    ) -> list[StudyPlanTask]:
        """Call OpenRouter and parse the JSON plan into ORM objects."""
        ctx = await self._build_context(user)

        today = date.today()

        system_prompt = (
            "You are an expert IELTS coach. "
            "Generate a structured study plan in JSON format. "
            "Output ONLY a valid JSON array (no markdown, no extra text). "
            "Each element represents ONE task with keys: "
            "day_number (int), focus_skill (one of: reading, listening, writing, speaking, vocabulary), "
            "task_description (string, concise action in English), "
            "duration_minutes (int 30-90). "
            "Prioritise weaker skills (lower band score). "
            "Vary the tasks: include mock tests, targeted exercises, and review sessions. "
            "Do NOT repeat the same quiz the user has already done."
        )

        user_prompt = (
            f"Target band: {ctx['target_band']}. "
            f"Exam date: {ctx['exam_date'] or 'not set'}. "
            f"Current progress: {json.dumps(ctx['progress'])}. "
            f"Recent attempts: {json.dumps(ctx['recent_history'])}. "
            f"Already done quiz_ids: {ctx['done_quiz_ids'][:20]}. "
            f"Generate exactly {num_days} tasks starting from day {start_day}."
        )

        fallback = self._fallback_plan(user.id, today, start_day, num_days)

        if not settings.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY not set – using fallback plan")
            return fallback

        payload = {
            "model": _OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.6,
            "max_tokens": 1200,
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "LinguaIELTS StudyPlan",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
                resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            items = json.loads(raw)
            return self._parse_ai_items(user.id, today, start_day, items)
        except Exception as exc:
            logger.warning("AI plan generation failed (%s) – using fallback", exc)
            return fallback

    @staticmethod
    def _parse_ai_items(
        user_id: int, today: date, start_day: int, items: list
    ) -> list[StudyPlanTask]:
        tasks = []
        for item in items:
            day_num = int(item.get("day_number", start_day))
            skill = str(item.get("focus_skill", "reading")).lower()
            if skill not in _SKILL_ROUTES:
                skill = "reading"
            plan_date = today + timedelta(days=day_num - 1)
            tasks.append(
                StudyPlanTask(
                    user_id=user_id,
                    day_number=day_num,
                    plan_date=plan_date,
                    focus_skill=skill,
                    task_description=str(item.get("task_description", "Practice session")),
                    duration_minutes=int(item.get("duration_minutes", 45)),
                    route_path=_SKILL_ROUTES.get(skill, "/reading"),
                )
            )
        return tasks

    @staticmethod
    def _fallback_plan(
        user_id: int, today: date, start_day: int, num_days: int
    ) -> list[StudyPlanTask]:
        """Simple round-robin fallback when AI is unavailable."""
        rotation = [
            ("reading", "Complete a Reading practice test (Parts 1–3)", 60),
            ("listening", "Complete a Listening practice test (Sections 1–4)", 60),
            ("writing", "Write a Task 2 essay and review model answers", 75),
            ("speaking", "Record yourself doing Part 2 topic and review feedback", 45),
            ("vocabulary", "Review due vocabulary with SRS flashcards (≥10 min)", 30),
            ("reading", "Focus on True/False/Not Given and matching headings", 45),
        ]
        tasks = []
        for i in range(num_days):
            skill, desc, mins = rotation[(start_day - 1 + i) % len(rotation)]
            day_num = start_day + i
            tasks.append(
                StudyPlanTask(
                    user_id=user_id,
                    day_number=day_num,
                    plan_date=today + timedelta(days=day_num - 1),
                    focus_skill=skill,
                    task_description=desc,
                    duration_minutes=mins,
                    route_path=_SKILL_ROUTES[skill],
                )
            )
        return tasks

    @staticmethod
    def _group_by_day(tasks: list[StudyPlanTask]) -> StudyPlanResponse:
        days_map: dict[int, StudyPlanDayGroup] = {}
        for task in tasks:
            if task.day_number not in days_map:
                days_map[task.day_number] = StudyPlanDayGroup(
                    day_number=task.day_number,
                    plan_date=task.plan_date,
                    tasks=[],
                )
            days_map[task.day_number].tasks.append(
                StudyPlanTaskResponse.model_validate(task)
            )
        sorted_days = sorted(days_map.values(), key=lambda d: d.day_number)
        total = sum(len(d.tasks) for d in sorted_days)
        completed = sum(
            1 for d in sorted_days for t in d.tasks if t.is_completed
        )
        return StudyPlanResponse(
            days=sorted_days, total_tasks=total, completed_tasks=completed
        )
