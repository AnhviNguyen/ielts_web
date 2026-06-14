"""
tests/integration/services/test_forecast_service.py
────────────────────────────────────────────────────
Integration tests for ForecastService and NextWeekForecastService.
Verifies daily forecasting models, alerts, weekly bucketing, and next-week forecasts.
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

from app.core.config import settings
from app.db.models import ScoreHistory, Notification, UserProfile
from app.services.forecast_service import ForecastService
from app.services.next_week_forecast_service import NextWeekForecastService

pytestmark = pytest.mark.integration


import shutil
from pathlib import Path

@pytest.fixture(autouse=True)
def setup_forecast_test():
    """Override FORECAST_MODEL_DIR to use a temporary directory inside the workspace."""
    temp_dir = Path("tests/temp_models")
    temp_dir.mkdir(parents=True, exist_ok=True)
    with patch.object(settings, "FORECAST_MODEL_DIR", str(temp_dir)):
        with patch.object(settings, "FORECAST_MIN_DAYS", 14):
            with patch.object(settings, "FORECAST_LOOKBACK_DAYS", 30):
                yield
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def forecast_service(db_session):
    return ForecastService(db_session)


@pytest.fixture
def next_week_service(db_session):
    return NextWeekForecastService(db_session)


# Helper to populate score history daily for a user
async def populate_history(db_session, user_id: int, skill: str, num_days: int, start_score: float, step: float = 0.1):
    today = date.today()
    for d in range(num_days):
        ds = today - timedelta(days=num_days - d - 1)
        sh = ScoreHistory(
            user_id=user_id,
            skill=skill,
            ds=ds,
            y=min(9.0, max(0.0, start_score + d * step)),
            session_min=20.0,
            correct_rate=0.7,
            attempt_count=1
        )
        db_session.add(sh)
    await db_session.flush()


# ---------------------------------------------------------------------------
# FC-01 to FC-04: Daily Forecasting & Alerts
# ---------------------------------------------------------------------------

async def test_fc01_train_skill_insufficient_data(forecast_service, make_user):
    """
    FC-01: Train model with < 14 data points -> returns False.
    """
    user = await make_user(email="insufficient@example.com")
    success = await forecast_service.train_skill(user.id, "Reading")
    assert success is False


async def test_fc02_train_and_predict_sufficient_data(forecast_service, db_session, make_user):
    """
    FC-02 & FC-03: Train and predict daily forecast using linear_seasonal fallback.
    """
    user = await make_user(email="sufficient@example.com")
    await populate_history(db_session, user.id, "Reading", 15, 6.0, 0.05)

    # Train model
    success = await forecast_service.train_skill(user.id, "Reading")
    assert success is True

    # Retrieve forecast
    resp = await forecast_service.get_forecast(user.id, "Reading")
    assert resp.cold_start is False
    assert resp.trainer == "linear_seasonal"
    assert len(resp.history) == 15
    assert len(resp.forecast) == settings.FORECAST_HORIZON_DAYS


async def test_fc04_get_alerts(forecast_service, db_session, make_user):
    """
    FC-04: Verify alerts generation (cold_start first, then below_target or stagnation).
    """
    user = await make_user(email="alerts@example.com")

    # 1. Cold start alert when no history exists
    resp = await forecast_service.get_alerts(user.id)
    assert len(resp.alerts) == 1
    assert resp.alerts[0].code == "cold_start"

    # 2. Add history, set high target to trigger warning
    profile = await db_session.get(UserProfile, user.id)
    if profile:
        profile.target_band = 8.5
        await db_session.flush()

    await populate_history(db_session, user.id, "Reading", 15, 5.5, 0.0)
    await forecast_service.train_skill(user.id, "Reading")

    resp2 = await forecast_service.get_alerts(user.id)
    alert_codes = [a.code for a in resp2.alerts]
    # Should flag "below_target" because 5.5 is way below 8.5
    assert "below_target" in alert_codes


# ---------------------------------------------------------------------------
# NW-01 to NW-03: Next-Week Forecasting
# ---------------------------------------------------------------------------

async def test_nw01_next_week_forecast_success(next_week_service, db_session, make_user):
    """
    NW-01: Predict next week forecast with sufficient data -> calculates status and alerts.
    """
    user = await make_user(email="nextweek@example.com")

    # We need 2+ weeks of daily data (e.g. 15 days) to pass the MIN_WEEKS requirement
    # We populate history for all skills: listening, reading, writing, speaking
    for skill in ["listening", "reading", "writing", "speaking"]:
        await populate_history(db_session, user.id, skill, 15, 6.0, 0.05)

    # Mock the RandomForest next-week predictor
    mock_predictor = MagicMock()
    mock_predictor.available = True
    mock_predictor.predict.return_value = {
        "overall_band": 7.0,
        "listening_band": 7.0,
        "reading_band": 7.0,
        "writing_band": 6.5,
        "speaking_band": 6.5,
    }

    with patch.object(settings, "NEXT_WEEK_ENABLED", True):
        with patch.object(settings, "NEXT_WEEK_MIN_WEEKS", 2):
            with patch.object(next_week_service, "_predictor", mock_predictor):
                resp = await next_week_service.get_next_week_forecast(user.id, notify=True)

                assert resp.cold_start is False
                assert resp.overall.predicted == 7.0
                assert resp.overall.current == 6.5  # overall average from daily 6.0 to 6.7 in history
                assert resp.overall.status == "improving"

                # Since it was improving, no notification should be generated
                stmt_notify = select(Notification).where(Notification.user_id == user.id)
                res_notify = await db_session.execute(stmt_notify)
                assert len(res_notify.scalars().all()) == 0


async def test_nw02_next_week_forecast_declining_sends_notification(next_week_service, db_session, make_user):
    """
    NW-01/NW-02: Predict next week forecast declining -> dispatches notification.
    """
    user = await make_user(email="declining@example.com")

    for skill in ["listening", "reading", "writing", "speaking"]:
        await populate_history(db_session, user.id, skill, 15, 7.5, -0.05)  # declining score trend

    mock_predictor = MagicMock()
    mock_predictor.available = True
    mock_predictor.predict.return_value = {
        "overall_band": 6.5,
        "listening_band": 6.5,
        "reading_band": 6.5,
        "writing_band": 6.5,
        "speaking_band": 6.5,
    }

    with patch.object(settings, "NEXT_WEEK_ENABLED", True):
        with patch.object(settings, "NEXT_WEEK_MIN_WEEKS", 2):
            with patch.object(next_week_service, "_predictor", mock_predictor):
                resp = await next_week_service.get_next_week_forecast(user.id, notify=True)

                assert resp.cold_start is False
                assert resp.overall.status == "declining"

                # Assert in-app notification created
                stmt_notify = select(Notification).where(Notification.user_id == user.id)
                res_notify = await db_session.execute(stmt_notify)
                notifs = res_notify.scalars().all()
                assert len(notifs) == 1
                assert notifs[0].type == "score_forecast"
                assert "Cảnh báo" in notifs[0].body


async def test_nw03_next_week_forecast_insufficient_data(next_week_service, db_session, make_user):
    """
    NW-02: Predict with insufficient weeks of data -> returns cold_start=True.
    """
    user = await make_user(email="insufficient_weeks@example.com")
    # Only 5 days of data (less than 2 weeks)
    for skill in ["listening", "reading", "writing", "speaking"]:
        await populate_history(db_session, user.id, skill, 5, 6.0, 0.0)

    mock_predictor = MagicMock()
    mock_predictor.available = True

    with patch.object(settings, "NEXT_WEEK_ENABLED", True):
        with patch.object(settings, "NEXT_WEEK_MIN_WEEKS", 2):
            with patch.object(next_week_service, "_predictor", mock_predictor):
                resp = await next_week_service.get_next_week_forecast(user.id)
                assert resp.cold_start is True
                assert "Hãy luyện thêm vài bài nhé" in resp.message


async def test_nw03_next_week_forecast_model_not_found(next_week_service, db_session, make_user):
    """
    NW-03: Model file not found (available = False) -> handles gracefully, returns cold_start=True.
    """
    user = await make_user(email="no_model@example.com")
    for skill in ["listening", "reading", "writing", "speaking"]:
        await populate_history(db_session, user.id, skill, 15, 6.0, 0.0)

    # Predictor model doesn't exist
    mock_predictor = MagicMock()
    mock_predictor.available = False

    with patch.object(settings, "NEXT_WEEK_ENABLED", True):
        with patch.object(next_week_service, "_predictor", mock_predictor):
            resp = await next_week_service.get_next_week_forecast(user.id)
            assert resp.enabled is False
            assert resp.cold_start is True
            assert "chưa sẵn sàng" in resp.message
