"""Compare tabular baselines for next-week IELTS band prediction."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor


SKILLS = ["listening", "reading", "writing", "speaking"]
TARGET_COLUMNS = ["target_next_overall_band", *[f"target_next_{skill}_band" for skill in SKILLS]]
CURRENT_TARGET_COLUMNS = ["overall_band", *[f"{skill}_band" for skill in SKILLS]]
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


def split_by_student(data: pd.DataFrame, test_size: float, random_state: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(data, groups=data["student_id"]))
    return data.iloc[train_idx].copy(), data.iloc[test_idx].copy()


def make_preprocessor(scale_numeric: bool = False) -> ColumnTransformer:
    numeric_step: str | StandardScaler = StandardScaler() if scale_numeric else "passthrough"
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", numeric_step, NUMERIC_FEATURES),
        ],
        remainder="drop",
    )


def build_models(seed: int, n_jobs: int) -> dict[str, Pipeline]:
    return {
        "ridge": Pipeline(
            steps=[
                ("preprocess", make_preprocessor(scale_numeric=True)),
                ("model", Ridge(alpha=1.0)),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocess", make_preprocessor()),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=300,
                        min_samples_leaf=3,
                        random_state=seed,
                        n_jobs=n_jobs,
                    ),
                ),
            ]
        ),
        "xgboost": Pipeline(
            steps=[
                ("preprocess", make_preprocessor()),
                (
                    "model",
                    MultiOutputRegressor(
                        XGBRegressor(
                            n_estimators=350,
                            max_depth=4,
                            learning_rate=0.045,
                            subsample=0.9,
                            colsample_bytree=0.9,
                            objective="reg:squarederror",
                            tree_method="hist",
                            random_state=seed,
                            n_jobs=n_jobs,
                        ),
                        n_jobs=1,
                    ),
                ),
            ]
        ),
        "lightgbm": Pipeline(
            steps=[
                ("preprocess", make_preprocessor()),
                (
                    "model",
                    MultiOutputRegressor(
                        LGBMRegressor(
                            n_estimators=450,
                            learning_rate=0.035,
                            num_leaves=31,
                            min_child_samples=30,
                            subsample=0.9,
                            colsample_bytree=0.9,
                            random_state=seed,
                            n_jobs=n_jobs,
                            verbose=-1,
                        ),
                        n_jobs=1,
                    ),
                ),
            ]
        ),
    }


def rounded_band_predictions(model: Pipeline, x_test: pd.DataFrame) -> np.ndarray:
    predictions = model.predict(x_test)
    return np.clip(np.round(predictions * 2) / 2, 0.0, 9.0)


def evaluate_predictions(y_true: pd.DataFrame, predictions: np.ndarray) -> dict[str, float]:
    per_target = {}
    for idx, target_name in enumerate(TARGET_NAMES):
        per_target[f"mae_{target_name}"] = round(
            float(mean_absolute_error(y_true[TARGET_COLUMNS[idx]], predictions[:, idx])),
            4,
        )
    per_target["macro_mae"] = round(float(np.mean(list(per_target.values()))), 4)
    return per_target


def evaluate_naive(test_data: pd.DataFrame) -> dict[str, float]:
    per_target = {}
    for idx, target_name in enumerate(TARGET_NAMES):
        per_target[f"mae_{target_name}"] = round(
            float(mean_absolute_error(test_data[TARGET_COLUMNS[idx]], test_data[CURRENT_TARGET_COLUMNS[idx]])),
            4,
        )
    per_target["macro_mae"] = round(float(np.mean(list(per_target.values()))), 4)
    return per_target


def stability_score(metrics: dict[str, float]) -> float:
    target_maes = [metrics[f"mae_{target_name}"] for target_name in TARGET_NAMES]
    return round(float(np.std(target_maes)), 4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare IELTS prediction models.")
    parser.add_argument("--training-data", type=Path, default=Path("data/synthetic_training_rows.csv"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=-1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    args.model_dir.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(args.training_data)
    train_data, test_data = split_by_student(data, test_size=args.test_size, random_state=args.seed)

    x_train = train_data[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y_train = train_data[TARGET_COLUMNS]
    x_test = test_data[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y_test = test_data[TARGET_COLUMNS]

    rows: list[dict[str, Any]] = []
    trained_models: dict[str, Pipeline] = {}

    naive_metrics = evaluate_naive(test_data)
    rows.append(
        {
            "model": "naive_current_band",
            "fit_seconds": 0.0,
            "stability_mae_std": stability_score(naive_metrics),
            **naive_metrics,
        }
    )

    for model_name, model in build_models(seed=args.seed, n_jobs=args.n_jobs).items():
        start = time.perf_counter()
        model.fit(x_train, y_train)
        fit_seconds = time.perf_counter() - start
        predictions = rounded_band_predictions(model, x_test)
        metrics = evaluate_predictions(y_test, predictions)
        rows.append(
            {
                "model": model_name,
                "fit_seconds": round(fit_seconds, 2),
                "stability_mae_std": stability_score(metrics),
                **metrics,
            }
        )
        trained_models[model_name] = model

    results = pd.DataFrame(rows).sort_values(["macro_mae", "stability_mae_std", "fit_seconds"])
    best_model_name = str(results.iloc[0]["model"])

    csv_path = args.reports_dir / "model_comparison.csv"
    json_path = args.reports_dir / "model_comparison.json"
    results.to_csv(csv_path, index=False)
    json_path.write_text(
        json.dumps(
            {
                "best_model": best_model_name,
                "selection_rule": "lowest macro_mae, then lowest target MAE std, then fastest fit time",
                "train_rows": int(len(train_data)),
                "test_rows": int(len(test_data)),
                "train_students": int(train_data["student_id"].nunique()),
                "test_students": int(test_data["student_id"].nunique()),
                "results": results.to_dict(orient="records"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if best_model_name in trained_models:
        best_model_path = args.model_dir / "ielts_best_model.joblib"
        joblib.dump(trained_models[best_model_name], best_model_path)
        print(f"Saved best model: {best_model_path}")
    else:
        print("Best result is the naive baseline; no trained model was saved as best.")

    print(f"Saved comparison CSV: {csv_path}")
    print(f"Saved comparison JSON: {json_path}")
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
