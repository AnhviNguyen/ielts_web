"""Predict one learner's next-week IELTS bands.

Ported from ``ielts_model/src/predict_next_week.py`` and adapted for in-process
inference inside the FastAPI backend. The trained RandomForest pipeline lives at
``settings.NEXT_WEEK_MODEL_PATH`` (a joblib artifact built by
``ielts_model/src/train_baseline_random_forest.py``).

The model is loaded lazily and cached as a process-level singleton so the heavy
joblib file is only deserialized once per worker.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SKILLS = ["listening", "reading", "writing", "speaking"]
TARGET_NAMES = ["overall_band", *[f"{skill}_band" for skill in SKILLS]]
CATEGORICAL_FEATURES = ["learner_archetype"]
NUMERIC_FEATURES = [
    "week",
    "days_elapsed",
    "weekly_study_hours",
    "accumulated_study_hours",
    "weeks_elapsed",
    "avg_weekly_hours",
    "target_band",
    "ceiling_band",
    "start_overall_band",
    "current_overall_band",
    "overall_band",
    "study_consistency",
    "learning_rate",
    "motivation",
    "noise_level",
    "distance_to_ceiling",
    "distance_to_target",
    "is_high_band",
    "start_listening_band",
    "start_reading_band",
    "start_writing_band",
    "start_speaking_band",
    "listening_band",
    "reading_band",
    "writing_band",
    "speaking_band",
    "mock_overall",
    "mock_listening",
    "mock_reading",
    "mock_writing",
    "mock_speaking",
    "mock_overall_rolling3_mean",
    "mock_overall_rolling3_std",
    "overall_band_trend4",
    "mock_listening_rolling3_mean",
    "mock_listening_rolling3_std",
    "listening_band_trend4",
    "mock_reading_rolling3_mean",
    "mock_reading_rolling3_std",
    "reading_band_trend4",
    "mock_writing_rolling3_mean",
    "mock_writing_rolling3_std",
    "writing_band_trend4",
    "mock_speaking_rolling3_mean",
    "mock_speaking_rolling3_std",
    "speaking_band_trend4",
]

DEFAULTS = {
    "learner_archetype": "steady",
    "target_band": 7.0,
    "study_consistency": 0.7,
    "learning_rate": 1.0,
    "motivation": 0.7,
    "noise_level": 0.22,
}


def round_to_half_band(value: float) -> float:
    return float(np.clip(np.round(value * 2) / 2, 0.0, 9.0))


def _overall_from_skills(row: dict[str, Any], prefix: str = "") -> float:
    if prefix:
        values = [float(row[f"{prefix}{skill}"]) for skill in SKILLS]
    else:
        values = [float(row[f"{skill}_band"]) for skill in SKILLS]
    return round_to_half_band(float(np.mean(values)))


def _normalize_history(payload: dict[str, Any]) -> pd.DataFrame:
    history = payload.get("history")
    if not isinstance(history, list) or not history:
        raise ValueError("Input must contain a non-empty 'history' list.")

    rows: list[dict[str, Any]] = []
    accumulated_hours = 0.0
    for index, item in enumerate(history):
        row = dict(item)
        row["week"] = int(row.get("week", index))
        row["weekly_study_hours"] = float(row.get("weekly_study_hours", 0.0))
        accumulated_hours += row["weekly_study_hours"]
        row["accumulated_study_hours"] = float(
            row.get("accumulated_study_hours", accumulated_hours)
        )

        missing = [skill for skill in SKILLS if f"{skill}_band" not in row]
        if missing:
            missing_list = ", ".join(f"{skill}_band" for skill in missing)
            raise ValueError(f"History row {index} is missing skill bands: {missing_list}")

        for skill in SKILLS:
            row[f"{skill}_band"] = round_to_half_band(float(row[f"{skill}_band"]))
            row[f"mock_{skill}"] = round_to_half_band(
                float(row.get(f"mock_{skill}", row[f"{skill}_band"]))
            )

        row["overall_band"] = round_to_half_band(
            float(row.get("overall_band", _overall_from_skills(row)))
        )
        row["current_overall_band"] = row["overall_band"]
        row["mock_overall"] = round_to_half_band(
            float(row.get("mock_overall", _overall_from_skills(row, "mock_")))
        )
        rows.append(row)

    return pd.DataFrame(rows).sort_values("week").reset_index(drop=True)


def build_feature_row(payload: dict[str, Any]) -> pd.DataFrame:
    """Build the single feature row consumed by the trained pipeline."""
    history = _normalize_history(payload)
    latest = history.iloc[-1].to_dict()
    first = history.iloc[0].to_dict()

    target_band = float(payload.get("target_band", DEFAULTS["target_band"]))
    ceiling_band = float(
        payload.get(
            "ceiling_band",
            min(9.0, max(target_band + 0.5, latest["overall_band"] + 1.0)),
        )
    )
    week = int(latest["week"])
    accumulated_hours = float(latest["accumulated_study_hours"])

    features: dict[str, Any] = {
        "learner_archetype": payload.get("learner_archetype", DEFAULTS["learner_archetype"]),
        "week": week,
        "days_elapsed": int(latest.get("days_elapsed", week * 7)),
        "weekly_study_hours": float(latest["weekly_study_hours"]),
        "accumulated_study_hours": accumulated_hours,
        "weeks_elapsed": week,
        "avg_weekly_hours": accumulated_hours / week if week > 0 else 0.0,
        "target_band": target_band,
        "ceiling_band": ceiling_band,
        "start_overall_band": float(payload.get("start_overall_band", first["overall_band"])),
        "current_overall_band": float(latest["overall_band"]),
        "overall_band": float(latest["overall_band"]),
        "study_consistency": float(payload.get("study_consistency", DEFAULTS["study_consistency"])),
        "learning_rate": float(payload.get("learning_rate", DEFAULTS["learning_rate"])),
        "motivation": float(payload.get("motivation", DEFAULTS["motivation"])),
        "noise_level": float(payload.get("noise_level", DEFAULTS["noise_level"])),
    }

    features["distance_to_ceiling"] = ceiling_band - features["overall_band"]
    features["distance_to_target"] = target_band - features["overall_band"]
    features["is_high_band"] = int(features["overall_band"] >= 7.5)

    for skill in SKILLS:
        features[f"start_{skill}_band"] = float(
            payload.get(f"start_{skill}_band", first[f"{skill}_band"])
        )
        features[f"{skill}_band"] = float(latest[f"{skill}_band"])
        features[f"mock_{skill}"] = float(latest[f"mock_{skill}"])
    features["mock_overall"] = float(latest["mock_overall"])

    for skill in ["overall", *SKILLS]:
        mock_col = f"mock_{skill}" if skill != "overall" else "mock_overall"
        band_col = f"{skill}_band" if skill != "overall" else "overall_band"

        mock_values = history[mock_col].tail(3)
        features[f"{mock_col}_rolling3_mean"] = float(mock_values.mean())
        features[f"{mock_col}_rolling3_std"] = (
            float(mock_values.std(ddof=1)) if len(mock_values) >= 2 else 0.0
        )

        if len(history) >= 5:
            previous_band = float(history.iloc[-5][band_col])
        else:
            previous_band = float(history.iloc[0][band_col])
        features[f"{band_col}_trend4"] = float(latest[band_col]) - previous_band

    missing = set(CATEGORICAL_FEATURES + NUMERIC_FEATURES) - set(features)
    if missing:
        raise ValueError(f"Feature builder missed columns: {sorted(missing)}")

    return pd.DataFrame([features])[CATEGORICAL_FEATURES + NUMERIC_FEATURES]


class NextWeekPredictor:
    """Lazy-loading wrapper around the trained next-week RandomForest pipeline."""

    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path
        self._model: Any = None
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        """True when the model can be loaded (locally or from HF Hub)."""
        try:
            from app.core.model_downloader import resolve_model
            resolve_model("next_week_ielts.joblib", str(self._model_path))
            return True
        except FileNotFoundError:
            return False

    def _ensure_loaded(self) -> Any:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                from app.core.model_downloader import resolve_model
                import joblib  # local import keeps cold-start cheap

                resolved = resolve_model("next_week_ielts.joblib", str(self._model_path))
                logger.info("Loading next-week model from %s", resolved)
                self._model = joblib.load(resolved)
        return self._model

    def predict(self, payload: dict[str, Any]) -> dict[str, float]:
        """Return rounded next-week band predictions keyed by target name."""
        model = self._ensure_loaded()
        features = build_feature_row(payload)
        raw = model.predict(features)[0]
        return {
            name: round_to_half_band(float(value))
            for name, value in zip(TARGET_NAMES, raw, strict=True)
        }


_PREDICTOR: NextWeekPredictor | None = None
_PREDICTOR_LOCK = threading.Lock()


def get_predictor() -> NextWeekPredictor:
    """Return the process-wide predictor singleton (resolved from settings)."""
    global _PREDICTOR
    if _PREDICTOR is None:
        with _PREDICTOR_LOCK:
            if _PREDICTOR is None:
                from app.core.config import settings

                _PREDICTOR = NextWeekPredictor(Path(settings.NEXT_WEEK_MODEL_PATH))
    return _PREDICTOR
