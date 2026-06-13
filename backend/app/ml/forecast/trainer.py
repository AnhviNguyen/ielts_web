"""Train and predict band scores with NeuralProphet (fallback: linear + weekly seasonality)."""

from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.forecast.conformal import apply_interval, iqr_intervals
from app.ml.forecast.paths import model_path

logger = logging.getLogger(__name__)

try:
    from neuralprophet import NeuralProphet  # type: ignore

    _HAS_NEURALPROPHET = True
except ImportError:
    NeuralProphet = None  # type: ignore
    _HAS_NEURALPROPHET = False


SKILL_SKILLS = ("reading", "listening", "writing", "speaking", "overall")


@dataclass
class TrainMetrics:
    trainer: str
    mae: float
    rmse: float
    sample_count: int
    interval_half_width: float


@dataclass
class ForecastPoint:
    ds: date
    yhat: float
    yhat_lower: float
    yhat_upper: float
    is_forecast: bool


def rows_to_frame(rows: list[Any]) -> pd.DataFrame:
    records = [
        {
            "ds": r.ds if isinstance(r.ds, date) else r["ds"],
            "y": float(r.y if hasattr(r, "y") else r["y"]),
            "session_min": float(r.session_min if hasattr(r, "session_min") else r["session_min"]),
            "correct_rate": float(
                r.correct_rate if hasattr(r, "correct_rate") else r["correct_rate"]
            ),
        }
        for r in rows
    ]
    if not records:
        return pd.DataFrame(columns=["ds", "y", "session_min", "correct_rate"])
    df = pd.DataFrame(records)
    df["ds"] = pd.to_datetime(df["ds"])
    return df.sort_values("ds").reset_index(drop=True)


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
    err = y_true.astype(float) - y_pred.astype(float)
    mae = float(np.mean(np.abs(err))) if err.size else 0.0
    rmse = float(np.sqrt(np.mean(err**2))) if err.size else 0.0
    return mae, rmse


def _future_regressors(df: pd.DataFrame, periods: int) -> pd.DataFrame:
    last = df.iloc[-1]["ds"]
    future_dates = pd.date_range(last + pd.Timedelta(days=1), periods=periods, freq="D")
    sm = float(df["session_min"].tail(7).mean() or 20.0)
    cr = float(df["correct_rate"].tail(7).mean() or 0.6)
    return pd.DataFrame(
        {
            "ds": future_dates,
            "session_min": [sm] * periods,
            "correct_rate": [cr] * periods,
        }
    )


class _LinearSeasonalModel:
    """Fallback when NeuralProphet is unavailable."""

    def __init__(self) -> None:
        self.coef_: np.ndarray | None = None
        self.origin_: pd.Timestamp | None = None

    def fit(self, df: pd.DataFrame) -> None:
        t0 = df["ds"].min()
        self.origin_ = t0
        day_idx = (df["ds"] - t0).dt.days.astype(float).values
        dow = df["ds"].dt.dayofweek.values
        dow_mat = np.column_stack([(dow == i).astype(float) for i in range(1, 7)])
        x = np.column_stack(
            [
                np.ones(len(df)),
                day_idx,
                dow_mat,
                df["session_min"].values,
                df["correct_rate"].values,
            ]
        )
        y = df["y"].values.astype(float)
        self.coef_, _, _, _ = np.linalg.lstsq(x, y, rcond=None)

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        if self.coef_ is None or self.origin_ is None:
            return np.full(len(frame), 5.5)
        day_idx = (frame["ds"] - self.origin_).dt.days.astype(float).values
        dow = frame["ds"].dt.dayofweek.values
        dow_mat = np.column_stack([(dow == i).astype(float) for i in range(1, 7)])
        x = np.column_stack(
            [
                np.ones(len(frame)),
                day_idx,
                dow_mat,
                frame["session_min"].values,
                frame["correct_rate"].values,
            ]
        )
        pred = x @ self.coef_
        return np.clip(pred, 0.0, 9.0)


class ForecastTrainer:
    def __init__(self) -> None:
        self.horizon = settings.FORECAST_HORIZON_DAYS

    def _train_neuralprophet(self, df: pd.DataFrame) -> tuple[Any, str, np.ndarray, np.ndarray]:
        assert NeuralProphet is not None
        m = NeuralProphet(
            weekly_seasonality=True,
            daily_seasonality=False,
            yearly_seasonality=False,
            n_changepoints=5,
            learning_rate=0.1,
            epochs=80,
        )
        m = m.add_future_regressor("session_min")
        m = m.add_future_regressor("correct_rate")
        m.fit(df, freq="D")
        hist = m.predict(df)
        y_pred = hist["yhat1"].values.astype(float)
        y_true = df["y"].values.astype(float)
        return m, "neuralprophet", y_true, y_pred

    def _train_fallback(self, df: pd.DataFrame) -> tuple[Any, str, np.ndarray, np.ndarray]:
        model = _LinearSeasonalModel()
        model.fit(df)
        y_pred = model.predict(df)
        y_true = df["y"].values.astype(float)
        return model, "linear_seasonal", y_true, y_pred

    def train(self, user_id: int, skill: str, rows: list[Any]) -> TrainMetrics | None:
        if len(rows) < settings.FORECAST_MIN_DAYS:
            return None

        df = rows_to_frame(rows)
        use_np = _HAS_NEURALPROPHET and len(df) >= settings.FORECAST_MIN_DAYS
        try:
            if use_np:
                model, trainer, y_true, y_pred = self._train_neuralprophet(df)
            else:
                model, trainer, y_true, y_pred = self._train_fallback(df)
        except Exception as exc:
            logger.warning("NeuralProphet failed for user=%s skill=%s: %s — fallback", user_id, skill, exc)
            model, trainer, y_true, y_pred = self._train_fallback(df)

        holdout = max(3, min(7, len(df) // 5))
        if len(df) > holdout + 5:
            eval_true = y_true[-holdout:]
            eval_pred = y_pred[-holdout:]
        else:
            eval_true, eval_pred = y_true, y_pred

        mae, rmse = _metrics(eval_true, eval_pred)
        half_w = iqr_intervals(eval_true, eval_pred)

        payload = {
            "trainer": trainer,
            "model": model,
            "training_df": df,
            "interval_half_width": half_w,
            "mae": mae,
            "rmse": rmse,
            "sample_count": len(df),
        }
        path = model_path(user_id, skill)
        with path.open("wb") as fh:
            pickle.dump(payload, fh)

        return TrainMetrics(
            trainer=trainer,
            mae=mae,
            rmse=rmse,
            sample_count=len(df),
            interval_half_width=half_w,
        )

    def _load(self, user_id: int, skill: str) -> dict | None:
        path = model_path(user_id, skill)
        if not path.exists():
            return None
        with path.open("rb") as fh:
            return pickle.load(fh)

    def predict(
        self,
        user_id: int,
        skill: str,
        rows: list[Any],
        *,
        periods: int | None = None,
    ) -> list[ForecastPoint]:
        periods = periods or self.horizon
        df = rows_to_frame(rows)
        if df.empty:
            return []

        artifact = self._load(user_id, skill)
        half_w = 0.5
        trainer = "cold_start"

        if artifact:
            half_w = float(artifact.get("interval_half_width", 0.5))
            trainer = artifact.get("trainer", "fallback")
            model = artifact["model"]
        else:
            metrics = self.train(user_id, skill, rows)
            if metrics is None:
                return self._cold_start_forecast(df, periods)
            artifact = self._load(user_id, skill)
            if not artifact:
                return self._cold_start_forecast(df, periods)
            half_w = float(artifact.get("interval_half_width", 0.5))
            trainer = artifact.get("trainer", "fallback")
            model = artifact["model"]

        future_reg = _future_regressors(df, periods)
        hist_reg = df[["ds", "session_min", "correct_rate"]]
        full_reg = pd.concat([hist_reg, future_reg], ignore_index=True)

        if trainer == "neuralprophet" and _HAS_NEURALPROPHET:
            future = model.make_future_dataframe(df, periods=periods, n_historic_predictions=len(df))
            future = future.merge(full_reg, on="ds", how="left")
            future["session_min"] = future["session_min"].ffill().fillna(20.0)
            future["correct_rate"] = future["correct_rate"].ffill().fillna(0.6)
            fc = model.predict(future)
            yhat = fc["yhat1"].values.astype(float)
            dates = fc["ds"].dt.date.tolist()
            hist_len = len(df)
        else:
            yhat = model.predict(full_reg)
            dates = full_reg["ds"].dt.date.tolist()
            hist_len = len(df)

        yhat = np.clip(yhat, 0.0, 9.0)
        lo, hi = apply_interval(yhat, half_w)

        out: list[ForecastPoint] = []
        for i, ds in enumerate(dates):
            out.append(
                ForecastPoint(
                    ds=ds,
                    yhat=round(float(yhat[i]), 2),
                    yhat_lower=round(float(lo[i]), 2),
                    yhat_upper=round(float(hi[i]), 2),
                    is_forecast=i >= hist_len,
                )
            )
        return out

    def _cold_start_forecast(self, df: pd.DataFrame, periods: int) -> list[ForecastPoint]:
        """Simple trend when insufficient history."""
        y = df["y"].values.astype(float)
        if len(y) >= 2:
            slope = (y[-1] - y[0]) / max(len(y) - 1, 1)
        else:
            slope = 0.0
        base = float(y[-1]) if len(y) else 5.5
        last_ds = df["ds"].max().date() if not df.empty else date.today()
        out: list[ForecastPoint] = []
        for i, row in df.iterrows():
            out.append(
                ForecastPoint(
                    ds=row["ds"].date(),
                    yhat=round(float(row["y"]), 2),
                    yhat_lower=round(float(row["y"]) - 0.5, 2),
                    yhat_upper=round(float(row["y"]) + 0.5, 2),
                    is_forecast=False,
                )
            )
        for p in range(1, periods + 1):
            ds = last_ds + timedelta(days=p)
            pred = np.clip(base + slope * p, 0.0, 9.0)
            out.append(
                ForecastPoint(
                    ds=ds,
                    yhat=round(float(pred), 2),
                    yhat_lower=round(float(pred) - 0.8, 2),
                    yhat_upper=round(float(pred) + 0.8, 2),
                    is_forecast=True,
                )
            )
        return out

    def evaluate_existing(self, user_id: int, skill: str, rows: list[Any]) -> tuple[float, float] | None:
        artifact = self._load(user_id, skill)
        if not artifact or len(rows) < 7:
            return None
        df = rows_to_frame(rows)
        model = artifact["model"]
        trainer = artifact.get("trainer", "fallback")
        if trainer == "neuralprophet" and _HAS_NEURALPROPHET:
            hist = model.predict(df)
            y_pred = hist["yhat1"].values.astype(float)
        else:
            y_pred = model.predict(df)
        y_true = df["y"].values.astype(float)
        return _metrics(y_true[-7:], y_pred[-7:])
