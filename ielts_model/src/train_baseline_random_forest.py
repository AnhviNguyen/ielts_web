"""Train a Random Forest baseline for next-week IELTS band prediction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


SKILLS = ["listening", "reading", "writing", "speaking"]
TARGET_COLUMNS = ["target_next_overall_band", *[f"target_next_{skill}_band" for skill in SKILLS]]
CURRENT_TARGET_COLUMNS = ["overall_band", *[f"{skill}_band" for skill in SKILLS]]


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
CATEGORICAL_FEATURES = ["learner_archetype"]


def load_training_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing = set(TARGET_COLUMNS + NUMERIC_FEATURES + CATEGORICAL_FEATURES) - set(data.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Training data is missing required columns: {missing_list}")
    return data


def build_pipeline(random_state: int, n_estimators: int, n_jobs: int) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ],
        remainder="drop",
    )
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        min_samples_leaf=3,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("model", model)])


def split_by_student(data: pd.DataFrame, test_size: float, random_state: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(data, groups=data["student_id"]))
    return data.iloc[train_idx].copy(), data.iloc[test_idx].copy()


def compute_metrics(y_true: pd.DataFrame, y_pred: np.ndarray, baseline_pred: pd.DataFrame) -> dict[str, object]:
    target_names = ["overall_band", *[f"{skill}_band" for skill in SKILLS]]
    per_target = {}
    baseline_per_target = {}
    for idx, name in enumerate(target_names):
        target_column = TARGET_COLUMNS[idx]
        per_target[name] = round(float(mean_absolute_error(y_true[target_column], y_pred[:, idx])), 4)
        baseline_per_target[name] = round(
            float(mean_absolute_error(y_true[target_column], baseline_pred[CURRENT_TARGET_COLUMNS[idx]])),
            4,
        )

    return {
        "model_mae": per_target,
        "naive_current_band_mae": baseline_per_target,
        "macro_model_mae": round(float(np.mean(list(per_target.values()))), 4),
        "macro_naive_mae": round(float(np.mean(list(baseline_per_target.values()))), 4),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train baseline Random Forest for IELTS prediction.")
    parser.add_argument("--training-data", type=Path, default=Path("data/synthetic_training_rows.csv"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--n-jobs", type=int, default=-1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.model_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    data = load_training_data(args.training_data)
    train_data, test_data = split_by_student(data, test_size=args.test_size, random_state=args.seed)

    x_train = train_data[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y_train = train_data[TARGET_COLUMNS]
    x_test = test_data[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y_test = test_data[TARGET_COLUMNS]

    pipeline = build_pipeline(
        random_state=args.seed,
        n_estimators=args.n_estimators,
        n_jobs=args.n_jobs,
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    predictions = np.clip(np.round(predictions * 2) / 2, 0.0, 9.0)

    metrics = compute_metrics(
        y_true=y_test,
        y_pred=predictions,
        baseline_pred=test_data[CURRENT_TARGET_COLUMNS],
    )
    metrics.update(
        {
            "train_rows": int(len(train_data)),
            "test_rows": int(len(test_data)),
            "train_students": int(train_data["student_id"].nunique()),
            "test_students": int(test_data["student_id"].nunique()),
            "features": CATEGORICAL_FEATURES + NUMERIC_FEATURES,
            "targets": TARGET_COLUMNS,
        }
    )

    model_path = args.model_dir / "ielts_random_forest_baseline.joblib"
    metrics_path = args.reports_dir / "baseline_metrics.json"
    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Saved model: {model_path}")
    print(f"Saved metrics: {metrics_path}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
