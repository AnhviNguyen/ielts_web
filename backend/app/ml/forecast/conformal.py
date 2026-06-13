"""Conformal / IQR prediction intervals for forecast bands."""

from __future__ import annotations

import numpy as np


def iqr_intervals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    alpha: float = 0.1,
) -> float:
    """Return half-width q such that |y - yhat| <= q covers (1-alpha) of holdout."""
    residuals = np.abs(y_true.astype(float) - y_pred.astype(float))
    if residuals.size == 0:
        return 0.5
    return float(np.quantile(residuals, 1.0 - alpha))


def apply_interval(yhat: np.ndarray, half_width: float) -> tuple[np.ndarray, np.ndarray]:
    lo = np.clip(yhat - half_width, 0.0, 9.0)
    hi = np.clip(yhat + half_width, 0.0, 9.0)
    return lo, hi
