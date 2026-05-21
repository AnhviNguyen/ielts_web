"""
SM-2 spaced repetition helpers (shared by VocabService).
"""

from datetime import datetime, timedelta, timezone


def sm2_apply(
    *,
    quality: int,
    srs_ease: float,
    srs_interval_days: int,
    srs_repetitions: int,
) -> dict:
    """Return updated SRS fields + mastery after one review."""
    ease = float(srs_ease or 2.5)
    interval = int(srs_interval_days or 0)
    reps = int(srs_repetitions or 0)
    q = max(0, min(5, int(quality)))

    if q < 3:
        reps = 0
        interval = 1
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = max(1, round(interval * ease))
        reps += 1
        ease += 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        if ease < 1.3:
            ease = 1.3

    now = datetime.now(timezone.utc)
    next_at = now + timedelta(days=interval)

    mastery = "new"
    if reps >= 2 and interval >= 21:
        mastery = "mastered"
    elif reps >= 1:
        mastery = "learning"

    return {
        "srs_ease": round(ease, 2),
        "srs_interval_days": interval,
        "srs_repetitions": reps,
        "srs_next_review_at": next_at,
        "srs_last_review_at": now,
        "mastery": mastery,
    }
