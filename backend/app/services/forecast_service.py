"""Band score forecasting — train, predict, alerts."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.ml.forecast.trainer import ForecastTrainer, ForecastPoint
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.score_history_repository import ScoreHistoryRepository
from app.schemas import (
    ForecastAlert,
    ForecastAlertsResponse,
    ForecastPointSchema,
    ForecastResponse,
    ForecastSkillSummary,
    ScoreIngestRequest,
)

logger = logging.getLogger(__name__)


class ForecastService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._history = ScoreHistoryRepository(db)
        self._meta = ForecastModelRepository(db)
        self._profile = ProfileRepository(db)
        self._trainer = ForecastTrainer()

    async def ingest_score(self, user_id: int, payload: ScoreIngestRequest) -> None:
        from app.services.score_snapshot_service import ScoreSnapshotService

        await ScoreSnapshotService(self._db).ingest_from_practice(
            user_id,
            subject=payload.skill,
            band_score=payload.y,
            percentage=payload.correct_rate * 100 if payload.correct_rate <= 1 else payload.correct_rate,
            duration_seconds=int(payload.session_min * 60),
        )

    async def train_skill(self, user_id: int, skill: str, *, force: bool = False) -> bool:
        if not settings.FORECAST_ENABLED:
            return False

        rows = await self._history.get_series(
            user_id, skill, lookback_days=max(settings.FORECAST_LOOKBACK_DAYS, 60)
        )
        if len(rows) < settings.FORECAST_MIN_DAYS:
            return False

        old_metrics = None if force else self._trainer.evaluate_existing(user_id, skill, rows)
        metrics = self._trainer.train(user_id, skill, rows)
        if not metrics:
            return False

        if old_metrics and not force:
            old_mae, _ = old_metrics
            if metrics.mae > old_mae * 1.05:
                logger.info(
                    "Skip model overwrite user=%s skill=%s new_mae=%.3f old_mae=%.3f",
                    user_id,
                    skill,
                    metrics.mae,
                    old_mae,
                )
                return False

        from app.ml.forecast.paths import model_path

        await self._meta.upsert(
            user_id,
            skill,
            trainer=metrics.trainer,
            mae=metrics.mae,
            rmse=metrics.rmse,
            sample_count=metrics.sample_count,
            model_path=str(model_path(user_id, skill)),
        )
        return True

    async def get_forecast(self, user_id: int, skill: str) -> ForecastResponse:
        lookback = settings.FORECAST_LOOKBACK_DAYS
        rows = await self._history.get_series(user_id, skill, lookback_days=lookback)
        day_count = await self._history.count_days(user_id, skill)
        meta = await self._meta.get(user_id, skill)

        if day_count >= settings.FORECAST_MIN_DAYS:
            await self.train_skill(user_id, skill)

        points = self._trainer.predict(user_id, skill, rows)
        obs_map = {r.ds: r.y for r in rows}
        history_pts = [p for p in points if not p.is_forecast]
        forecast_pts = [p for p in points if p.is_forecast]

        return ForecastResponse(
            user_id=user_id,
            skill=skill,
            lookback_days=lookback,
            horizon_days=settings.FORECAST_HORIZON_DAYS,
            sample_days=day_count,
            trainer=meta.trainer if meta else "cold_start",
            mae=meta.mae if meta else None,
            rmse=meta.rmse if meta else None,
            history=[self._point_schema(p, obs_map.get(p.ds)) for p in history_pts],
            forecast=[self._point_schema(p) for p in forecast_pts],
            cold_start=day_count < settings.FORECAST_MIN_DAYS,
        )

    async def list_skills(self, user_id: int) -> list[ForecastSkillSummary]:
        skills = await self._history.list_skills(user_id)
        if not skills:
            skills = ["overall"]
        out: list[ForecastSkillSummary] = []
        for skill in skills:
            day_count = await self._history.count_days(user_id, skill)
            meta = await self._meta.get(user_id, skill)
            out.append(
                ForecastSkillSummary(
                    skill=skill,
                    sample_days=day_count,
                    trainer=meta.trainer if meta else None,
                    mae=meta.mae if meta else None,
                    trained_at=meta.trained_at if meta else None,
                )
            )
        return out

    async def get_alerts(self, user_id: int) -> ForecastAlertsResponse:
        profile = await self._profile.get_by_user_id(user_id)
        target = float(profile.target_band) if profile and profile.target_band else 7.0
        alerts: list[ForecastAlert] = []

        skills = await self._history.list_skills(user_id)
        if not skills:
            skills = ["overall"]

        for skill in skills:
            try:
                fc = await self.get_forecast(user_id, skill)
            except Exception as exc:
                logger.warning("forecast alert skip user=%s skill=%s: %s", user_id, skill, exc)
                continue

            if fc.cold_start:
                alerts.append(
                    ForecastAlert(
                        skill=skill,
                        severity="info",
                        code="cold_start",
                        message=f"Chưa đủ dữ liệu ({fc.sample_days}/{settings.FORECAST_MIN_DAYS} ngày) để dự báo chính xác cho {skill}.",
                    )
                )
                continue

            if not fc.forecast:
                continue

            min_pred = min(p.yhat_lower for p in fc.forecast)
            max_pred = max(p.yhat_upper for p in fc.forecast)
            end_pred = fc.forecast[-1]

            if min_pred < target - 0.5:
                alerts.append(
                    ForecastAlert(
                        skill=skill,
                        severity="warning",
                        code="below_target",
                        message=(
                            f"Dự báo {skill} có thể xuống dưới mục tiêu {target:.1f} "
                            f"(khoảng {min_pred:.1f}–{max_pred:.1f}) trong 14 ngày tới."
                        ),
                    )
                )

            width = end_pred.yhat_upper - end_pred.yhat_lower
            if width >= 1.2:
                alerts.append(
                    ForecastAlert(
                        skill=skill,
                        severity="info",
                        code="high_uncertainty",
                        message=f"Độ không chắc chắn cao cho {skill} (±{width / 2:.1f} band). Luyện tập đều đặn sẽ cải thiện dự báo.",
                    )
                )

            hist_vals = [p.yhat for p in fc.history[-7:]]
            if len(hist_vals) >= 5:
                spread = max(hist_vals) - min(hist_vals)
                if spread < 0.15 and end_pred.yhat <= hist_vals[-1] + 0.1:
                    alerts.append(
                        ForecastAlert(
                            skill=skill,
                            severity="info",
                            code="stagnation",
                            message=f"Điểm {skill} đang trì trệ. Thử đổi chủ đề hoặc tăng thời gian luyện tập.",
                        )
                    )

        return ForecastAlertsResponse(alerts=alerts, target_band=target)

    @staticmethod
    def _point_schema(p: ForecastPoint, observed_y: float | None = None) -> ForecastPointSchema:
        return ForecastPointSchema(
            ds=p.ds,
            y=observed_y,
            yhat=p.yhat,
            yhat_lower=p.yhat_lower,
            yhat_upper=p.yhat_upper,
            is_forecast=p.is_forecast,
        )
