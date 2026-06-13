"""Filesystem paths for per-user forecast model artifacts."""

from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def forecast_model_dir() -> Path:
    root = Path(settings.FORECAST_MODEL_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def model_path(user_id: int, skill: str) -> Path:
    safe_skill = skill.replace("/", "_").lower()
    return forecast_model_dir() / f"{user_id}_{safe_skill}.pkl"
