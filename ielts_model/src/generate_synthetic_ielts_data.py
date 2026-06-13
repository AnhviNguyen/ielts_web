"""Generate synthetic weekly IELTS learning trajectories.

The synthetic world model uses an exponential saturation learning curve with
extra plateau pressure at high bands. It is intentionally transparent so that
future real learner data can replace or reweight each assumption.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


SKILLS = ["listening", "reading", "writing", "speaking"]
TARGET_COLUMNS = ["overall_band", *[f"{skill}_band" for skill in SKILLS]]


@dataclass(frozen=True)
class Archetype:
    name: str
    weekly_hours_mean: float
    weekly_hours_sd: float
    consistency_mean: float
    motivation_mean: float
    learning_rate_mean: float
    noise_mean: float


ARCHETYPES = [
    Archetype("casual", 5.0, 2.0, 0.55, 0.55, 0.88, 0.28),
    Archetype("steady", 9.0, 2.5, 0.72, 0.70, 1.00, 0.22),
    Archetype("intensive", 16.0, 4.0, 0.78, 0.78, 1.08, 0.24),
    Archetype("inconsistent", 8.0, 5.0, 0.42, 0.58, 0.92, 0.35),
]


def round_to_half_band(values: np.ndarray | float) -> np.ndarray | float:
    """Round to the nearest IELTS half-band and clip to the valid range."""
    return np.clip(np.round(np.asarray(values) * 2) / 2, 0.0, 9.0)


def ielts_overall(skill_bands: np.ndarray) -> float:
    """IELTS overall is the rounded average of four skills."""
    return float(round_to_half_band(np.mean(skill_bands)))


def plateau_factor(current_band: float) -> float:
    """Slow progress as the learner approaches high IELTS bands."""
    if current_band <= 6.5:
        return 1.0
    factor = 1.0 - ((current_band - 6.5) / 2.5) ** 2
    return float(np.clip(factor, 0.15, 1.0))


def sample_start_skill_bands(rng: np.random.Generator) -> np.ndarray:
    """Sample plausible initial skill bands with realistic within-learner spread."""
    start_overall = rng.triangular(3.0, 5.0, 7.0)
    offsets = rng.normal(0.0, 0.45, size=len(SKILLS))
    offsets -= offsets.mean()
    return np.clip(start_overall + offsets, 2.0, 8.0)


def build_weekly_timeseries(
    n_students: int = 1_000,
    min_weeks: int = 16,
    max_weeks: int = 52,
    seed: int = 42,
) -> pd.DataFrame:
    """Create one row per student-week with observed and latent learner state."""
    rng = np.random.default_rng(seed)
    rows: list[dict[str, float | int | str]] = []

    archetype_probs = np.array([0.22, 0.45, 0.20, 0.13])
    skill_difficulty = {
        "listening": 0.92,
        "reading": 0.96,
        "writing": 1.12,
        "speaking": 1.08,
    }

    for student_idx in range(n_students):
        student_id = f"S{student_idx + 1:04d}"
        archetype = rng.choice(ARCHETYPES, p=archetype_probs)
        n_weeks = int(rng.integers(min_weeks, max_weeks + 1))

        start_skills = sample_start_skill_bands(rng)
        ceiling = float(np.clip(rng.normal(8.25, 0.45), start_skills.max() + 0.75, 9.0))
        target_band = float(round_to_half_band(rng.uniform(max(6.0, start_skills.mean() + 0.5), 9.0)))
        learning_rate = float(np.clip(rng.normal(archetype.learning_rate_mean, 0.12), 0.6, 1.35))
        motivation = float(np.clip(rng.normal(archetype.motivation_mean, 0.10), 0.25, 1.0))
        noise_level = float(np.clip(rng.normal(archetype.noise_mean, 0.05), 0.10, 0.50))
        consistency = float(np.clip(rng.normal(archetype.consistency_mean, 0.10), 0.15, 0.98))

        latent_skills = start_skills.astype(float).copy()
        accumulated_hours = 0.0
        start_overall = ielts_overall(start_skills)

        for week in range(n_weeks + 1):
            observed_noise = rng.normal(0.0, noise_level, size=len(SKILLS))
            observed_skills = round_to_half_band(latent_skills + observed_noise)
            observed_overall = ielts_overall(observed_skills)

            mock_noise = rng.normal(0.0, noise_level * 0.8, size=len(SKILLS))
            mock_skills = round_to_half_band(latent_skills + mock_noise)
            mock_overall = ielts_overall(mock_skills)

            row: dict[str, float | int | str] = {
                "student_id": student_id,
                "learner_archetype": archetype.name,
                "week": week,
                "days_elapsed": week * 7,
                "weekly_study_hours": 0.0 if week == 0 else weekly_hours,
                "accumulated_study_hours": round(accumulated_hours, 2),
                "target_band": target_band,
                "ceiling_band": round(ceiling, 3),
                "start_overall_band": start_overall,
                "current_overall_band": observed_overall,
                "overall_band": observed_overall,
                "study_consistency": round(consistency, 3),
                "learning_rate": round(learning_rate, 3),
                "motivation": round(motivation, 3),
                "noise_level": round(noise_level, 3),
            }
            for skill, start_band, observed_band, mock_band, latent_band in zip(
                SKILLS,
                start_skills,
                observed_skills,
                mock_skills,
                latent_skills,
                strict=True,
            ):
                row[f"start_{skill}_band"] = float(round_to_half_band(start_band))
                row[f"{skill}_band"] = float(observed_band)
                row[f"mock_{skill}"] = float(mock_band)
                row[f"latent_{skill}_ability"] = round(float(latent_band), 4)
            row["mock_overall"] = mock_overall
            rows.append(row)

            if week == n_weeks:
                break

            attendance_shock = rng.beta(6 * consistency, 6 * (1 - consistency) + 0.5)
            weekly_hours = max(
                0.0,
                rng.normal(archetype.weekly_hours_mean, archetype.weekly_hours_sd) * attendance_shock,
            )
            weekly_hours = float(np.clip(weekly_hours, 0.0, 32.0))
            accumulated_hours += weekly_hours

            quality = np.clip(0.55 + 0.30 * motivation + 0.25 * consistency + rng.normal(0.0, 0.05), 0.45, 1.25)
            for skill_idx, skill in enumerate(SKILLS):
                current = float(latent_skills[skill_idx])
                remaining = max(0.0, ceiling - current)
                tau = 350.0 * skill_difficulty[skill] / learning_rate
                effective_hours = weekly_hours * quality
                saturation_gain = remaining * (1.0 - np.exp(-effective_hours / tau))
                gain = saturation_gain * plateau_factor(current)
                regression_noise = rng.normal(0.0, 0.018 + noise_level * 0.015)
                latent_skills[skill_idx] = np.clip(current + gain + regression_noise, 0.0, ceiling)

    weekly = pd.DataFrame(rows)
    return weekly.sort_values(["student_id", "week"]).reset_index(drop=True)


def add_feature_columns(group: pd.DataFrame) -> pd.DataFrame:
    """Build leakage-safe features and next-week targets for one student."""
    group = group.sort_values("week").copy()
    for skill in ["overall", *SKILLS]:
        mock_col = f"mock_{skill}" if skill != "overall" else "mock_overall"
        band_col = f"{skill}_band" if skill != "overall" else "overall_band"
        group[f"{mock_col}_rolling3_mean"] = group[mock_col].rolling(3, min_periods=1).mean()
        group[f"{mock_col}_rolling3_std"] = group[mock_col].rolling(3, min_periods=2).std().fillna(0.0)
        group[f"{band_col}_trend4"] = group[band_col] - group[band_col].shift(4)
        group[f"{band_col}_trend4"] = group[f"{band_col}_trend4"].fillna(group[band_col] - group[band_col].iloc[0])
        group[f"target_next_{band_col}"] = group[band_col].shift(-1)

    group["weeks_elapsed"] = group["week"]
    group["avg_weekly_hours"] = group["accumulated_study_hours"] / group["week"].replace(0, np.nan)
    group["avg_weekly_hours"] = group["avg_weekly_hours"].fillna(0.0)
    group["distance_to_ceiling"] = group["ceiling_band"] - group["overall_band"]
    group["distance_to_target"] = group["target_band"] - group["overall_band"]
    group["is_high_band"] = (group["overall_band"] >= 7.5).astype(int)
    return group


def build_training_rows(weekly: pd.DataFrame) -> pd.DataFrame:
    """Transform weekly time series into supervised next-week rows."""
    featured = pd.concat(
        [add_feature_columns(group) for _, group in weekly.groupby("student_id", sort=False)],
        ignore_index=True,
    )
    target_cols = ["target_next_overall_band", *[f"target_next_{skill}_band" for skill in SKILLS]]
    return featured.dropna(subset=target_cols).reset_index(drop=True)


def validate_synthetic_data(weekly: pd.DataFrame, training: pd.DataFrame, expected_students: int) -> dict[str, float | int]:
    """Run lightweight generation checks and return useful diagnostics."""
    band_columns = ["overall_band", "current_overall_band", *[f"{skill}_band" for skill in SKILLS]]
    n_students = weekly["student_id"].nunique()
    if n_students != expected_students:
        raise ValueError(f"Expected {expected_students} students, found {n_students}.")
    for column in band_columns:
        if not weekly[column].between(0.0, 9.0).all():
            raise ValueError(f"{column} has values outside [0, 9].")
        doubled = weekly[column] * 2
        if not np.allclose(doubled, np.round(doubled)):
            raise ValueError(f"{column} is not rounded to 0.5 band steps.")

    ordered = weekly.sort_values(["student_id", "week"])
    first = ordered.groupby("student_id").first()
    last = ordered.groupby("student_id").last()
    total_gain = last["overall_band"] - first["overall_band"]
    hours = last["accumulated_study_hours"].replace(0, np.nan)
    hours_per_band = (hours / total_gain.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)

    mid_band = training[(training["overall_band"] >= 4.0) & (training["overall_band"] <= 6.5)]
    high_band = training[training["overall_band"] >= 7.5]
    mid_weekly_gain = (mid_band["target_next_overall_band"] - mid_band["overall_band"]).mean()
    high_weekly_gain = (high_band["target_next_overall_band"] - high_band["overall_band"]).mean()

    return {
        "students": int(n_students),
        "weekly_rows": int(len(weekly)),
        "training_rows": int(len(training)),
        "median_hours_per_band_gain": round(float(hours_per_band.median()), 2),
        "mid_band_mean_next_week_gain": round(float(mid_weekly_gain), 4),
        "high_band_mean_next_week_gain": round(float(high_weekly_gain), 4) if not high_band.empty else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic IELTS time-series data.")
    parser.add_argument("--students", type=int, default=1_000)
    parser.add_argument("--min-weeks", type=int, default=16)
    parser.add_argument("--max-weeks", type=int, default=52)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)

    weekly = build_weekly_timeseries(
        n_students=args.students,
        min_weeks=args.min_weeks,
        max_weeks=args.max_weeks,
        seed=args.seed,
    )
    training = build_training_rows(weekly)
    diagnostics = validate_synthetic_data(weekly, training, expected_students=args.students)

    weekly_path = args.data_dir / "synthetic_weekly_timeseries.csv"
    training_path = args.data_dir / "synthetic_training_rows.csv"
    weekly.to_csv(weekly_path, index=False)
    training.to_csv(training_path, index=False)

    print(f"Wrote {weekly_path} ({len(weekly):,} rows)")
    print(f"Wrote {training_path} ({len(training):,} rows)")
    print("Diagnostics:")
    for key, value in diagnostics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
