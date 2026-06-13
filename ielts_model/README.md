# IELTS Band Prediction Baseline

Synthetic-data baseline for predicting a learner's next-week IELTS overall band
and skill bands from weekly study progress.

## What This Project Does

- Generates weekly synthetic IELTS learning trajectories for 1,000 students.
- Uses an exponential saturation learning curve with high-band plateau pressure.
- Builds leakage-safe tabular features from each learner's historical rows.
- Trains a multi-output `RandomForestRegressor` to predict next-week:
  - `overall_band`
  - `listening_band`
  - `reading_band`
  - `writing_band`
  - `speaking_band`
- Compares the model against a naive baseline that predicts next week equals the
  current band.

## Learning Curve

The generator models latent skill ability with:

```text
band(t) = start_band + max_gain * (1 - exp(-effective_hours / tau))
```

Weekly gains are then reduced near high IELTS bands:

```text
weekly_gain *= max(0.15, 1 - ((current_band - 6.5) / 2.5)^2)
```

This makes the synthetic data useful for cold-start experiments without assuming
linear progress.

## Run

```bash
python src/generate_synthetic_ielts_data.py
python src/train_baseline_random_forest.py
python src/model_comparison.py
python src/predict_next_week.py --input data/sample_student_input.json
```

Generated files:

- `data/synthetic_weekly_timeseries.csv`
- `data/synthetic_training_rows.csv`
- `models/ielts_random_forest_baseline.joblib`
- `models/ielts_best_model.joblib`
- `reports/baseline_metrics.json`
- `reports/model_comparison.csv`
- `reports/model_comparison.json`

## Predict One Learner

`src/predict_next_week.py` loads `models/ielts_random_forest_baseline.joblib`
by default and returns next-week predictions for overall plus four skills.

Input JSON should contain learner-level fields and a weekly `history` list. At
minimum, each history row needs:

- `weekly_study_hours`
- `listening_band`
- `reading_band`
- `writing_band`
- `speaking_band`

Mock scores are optional; when omitted, the script uses the current skill bands
as mock scores. Example:

```bash
python src/predict_next_week.py --input data/sample_student_input.json
```

## Notes

Synthetic data is a controllable starting point, not ground truth about IELTS
learning. Once real learner data exists, retraining should weight real rows more
heavily and gradually retire synthetic rows.

`src/model_comparison.py` selects the best model by lowest macro MAE, then lower
MAE variance across targets, then faster fit time. On the default synthetic
dataset, Ridge can perform very well because the generated learning curve is
smooth after feature engineering; tree/boosting models become more useful as
real data adds messier nonlinear behavior.
