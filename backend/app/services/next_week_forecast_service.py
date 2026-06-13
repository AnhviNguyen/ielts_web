"""Next-week IELTS band prediction service.

Aggregates the per-day ``score_history`` time-series into weekly buckets, feeds
them to the RandomForest predictor (ported from ``ielts_model``), and reports
whether each skill is expected to improve, stay flat, or decline next week.

When the predicted overall band does not improve, an in-app notification is
created (at most once per ISO week) so the learner is warned proactively.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Notification
from app.ml.next_week.predictor import SKILLS, get_predictor, round_to_half_band
from app.repositories.profile_repository import ProfileRepository
from app.repositories.score_history_repository import ScoreHistoryRepository
from app.schemas import (
    NextWeekForecastResponse,
    NextWeekSkillForecast,
)

logger = logging.getLogger(__name__)

NOTIFICATION_TYPE = "score_forecast"
# Predicted overall must beat current by more than this to count as "improving".
IMPROVE_EPSILON = 0.01


def _status(delta: float) -> str:
    if delta > IMPROVE_EPSILON:
        return "improving"
    if delta < -IMPROVE_EPSILON:
        return "declining"
    return "flat"


class NextWeekForecastService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._history = ScoreHistoryRepository(db)
        self._profile = ProfileRepository(db)
        self._predictor = get_predictor()

    async def _build_weekly_history(self, user_id: int) -> list[dict]:
        """Collapse daily score_history into ordered weekly feature rows."""
        lookback_days = settings.NEXT_WEEK_LOOKBACK_WEEKS * 7
        series: dict[str, list] = {}
        all_dates: list[date] = []
        for skill in SKILLS:
            rows = await self._history.get_series(user_id, skill, lookback_days=lookback_days)
            series[skill] = rows
            all_dates.extend(r.ds for r in rows)

        if not all_dates:
            return []

        anchor = min(all_dates)

        def week_index(ds: date) -> int:
            return (ds - anchor).days // 7

        # Per (week, skill): accumulate band + minutes.
        weeks: dict[int, dict] = {}
        for skill in SKILLS:
            for row in series[skill]:
                wk = week_index(row.ds)
                bucket = weeks.setdefault(wk, {"bands": {}, "minutes": 0.0})
                bucket["bands"].setdefault(skill, []).append(float(row.y))
                bucket["minutes"] += float(row.session_min or 0.0)

        ordered_weeks = sorted(weeks)
        history: list[dict] = []
        last_known: dict[str, float] = {}
        for position, wk in enumerate(ordered_weeks):
            bucket = weeks[wk]
            row: dict = {
                "week": position + 1,
                "weekly_study_hours": round(bucket["minutes"] / 60.0, 2),
            }
            for skill in SKILLS:
                vals = bucket["bands"].get(skill)
                if vals:
                    band = round_to_half_band(sum(vals) / len(vals))
                    last_known[skill] = band
                elif skill in last_known:
                    band = last_known[skill]
                else:
                    band = None  # filled after we know the week's other skills
                row[f"{skill}_band"] = band
            # Backfill any skill with no prior data using this week's mean.
            present = [row[f"{s}_band"] for s in SKILLS if row[f"{s}_band"] is not None]
            fallback = round_to_half_band(sum(present) / len(present)) if present else 5.0
            for skill in SKILLS:
                if row[f"{skill}_band"] is None:
                    row[f"{skill}_band"] = fallback
                    last_known[skill] = fallback
            history.append(row)
        return history

    async def get_next_week_forecast(
        self, user_id: int, *, notify: bool = False
    ) -> NextWeekForecastResponse:
        profile = await self._profile.get_by_user_id(user_id)
        target = float(profile.target_band) if profile and profile.target_band else 7.0

        if not settings.NEXT_WEEK_ENABLED or not self._predictor.available:
            return NextWeekForecastResponse(
                user_id=user_id,
                enabled=False,
                cold_start=True,
                weeks_of_data=0,
                target_band=target,
                overall=None,
                skills=[],
                status="flat",
                improving=False,
                message="Tính năng dự đoán tuần tới chưa sẵn sàng.",
            )

        history = await self._build_weekly_history(user_id)
        weeks_of_data = len(history)

        if weeks_of_data < settings.NEXT_WEEK_MIN_WEEKS:
            return NextWeekForecastResponse(
                user_id=user_id,
                enabled=True,
                cold_start=True,
                weeks_of_data=weeks_of_data,
                target_band=target,
                overall=None,
                skills=[],
                status="flat",
                improving=False,
                message=(
                    f"Cần ít nhất {settings.NEXT_WEEK_MIN_WEEKS} tuần luyện tập để dự đoán "
                    f"(hiện có {weeks_of_data}). Hãy luyện thêm vài bài nhé!"
                ),
            )

        payload = {
            "history": history,
            "target_band": target,
        }
        try:
            predictions = self._predictor.predict(payload)
        except Exception as exc:  # noqa: BLE001 — degrade gracefully on inference error
            logger.warning("next-week predict failed user=%s: %s", user_id, exc)
            return NextWeekForecastResponse(
                user_id=user_id,
                enabled=True,
                cold_start=True,
                weeks_of_data=weeks_of_data,
                target_band=target,
                overall=None,
                skills=[],
                status="flat",
                improving=False,
                message="Không thể tạo dự đoán lúc này. Vui lòng thử lại sau.",
            )

        latest = history[-1]
        current_skills = {skill: float(latest[f"{skill}_band"]) for skill in SKILLS}
        current_overall = round_to_half_band(sum(current_skills.values()) / len(current_skills))

        skill_forecasts: list[NextWeekSkillForecast] = []
        for skill in SKILLS:
            cur = current_skills[skill]
            pred = float(predictions[f"{skill}_band"])
            delta = round(pred - cur, 2)
            skill_forecasts.append(
                NextWeekSkillForecast(
                    skill=skill,
                    current=cur,
                    predicted=pred,
                    delta=delta,
                    status=_status(delta),
                )
            )

        pred_overall = float(predictions["overall_band"])
        overall_delta = round(pred_overall - current_overall, 2)
        overall = NextWeekSkillForecast(
            skill="overall",
            current=current_overall,
            predicted=pred_overall,
            delta=overall_delta,
            status=_status(overall_delta),
        )

        improving = overall_delta > IMPROVE_EPSILON
        message = self._build_message(overall, skill_forecasts, target)

        response = NextWeekForecastResponse(
            user_id=user_id,
            enabled=True,
            cold_start=False,
            weeks_of_data=weeks_of_data,
            target_band=target,
            overall=overall,
            skills=skill_forecasts,
            status=overall.status,
            improving=improving,
            message=message,
        )

        if notify and not improving:
            await self._maybe_notify(user_id, overall, message)

        return response

    @staticmethod
    def _build_message(
        overall: NextWeekSkillForecast,
        skills: list[NextWeekSkillForecast],
        target: float,
    ) -> str:
        if overall.status == "improving":
            return (
                f"Tốt! Overall dự kiến tăng lên {overall.predicted:.1f} "
                f"(+{overall.delta:.1f}) trong tuần tới. Giữ vững nhịp độ!"
            )
        declining = [s for s in skills if s.status == "declining"]
        weakest = min(skills, key=lambda s: s.predicted) if skills else None
        if overall.status == "declining":
            head = (
                f"Cảnh báo: Overall có thể giảm xuống {overall.predicted:.1f} "
                f"({overall.delta:.1f}) trong tuần tới."
            )
        else:
            head = (
                f"Overall dự kiến chững lại ở {overall.predicted:.1f} trong tuần tới "
                f"(chưa đạt mục tiêu {target:.1f})."
            )
        if declining:
            names = ", ".join(s.skill for s in declining)
            head += f" Các kỹ năng cần chú ý: {names}."
        elif weakest:
            head += f" Hãy tập trung luyện {weakest.skill} (dự báo {weakest.predicted:.1f})."
        return head

    async def _maybe_notify(
        self, user_id: int, overall: NextWeekSkillForecast, message: str
    ) -> None:
        """Create a forecast notification at most once per ISO week."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        start_dt = datetime.combine(week_start, time.min, tzinfo=timezone.utc)
        existing = await self._db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.type == NOTIFICATION_TYPE,
                Notification.created_at >= start_dt,
            )
        )
        if int(existing.scalar_one() or 0) > 0:
            return

        from app.services.notification_service import NotificationService

        title = (
            "Điểm có thể giảm tuần tới"
            if overall.status == "declining"
            else "Điểm đang chững lại"
        )
        await NotificationService(self._db).create(
            user_id,
            type=NOTIFICATION_TYPE,
            title=title,
            body=message,
            link_path="/dashboard?tab=forecast",
        )
