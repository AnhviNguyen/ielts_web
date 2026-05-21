"""XP rules shared across practice types (IELTS quizzes, vocabulary SRS, …)."""

XP_SECONDS_PER_POINT = 600  # 10 minutes → 1 XP


def xp_from_duration(duration_seconds: int) -> int:
    """1 XP per 10 minutes, minimum 1 XP when activity is recorded."""
    return max(1, int(duration_seconds or 0) // XP_SECONDS_PER_POINT)
