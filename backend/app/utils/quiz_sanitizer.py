"""Strip answer keys from quiz JSON before sending to the client."""
from __future__ import annotations

import copy
from typing import Any

# Fields that must never be sent to the browser before submit/review.
_STRIP_KEYS = frozenset({
    "correct_answer",
    "correct_answers",
    "explain",
    "locate_info",
    "locate_paragraph",
    "listen_from",
})


def strip_quiz_answers(data: Any) -> Any:
    """Deep-copy and remove answer/explanation fields from quiz payloads."""
    if isinstance(data, dict):
        return {
            k: strip_quiz_answers(v)
            for k, v in data.items()
            if k not in _STRIP_KEYS
        }
    if isinstance(data, list):
        return [strip_quiz_answers(item) for item in data]
    return data


def sanitize_quiz_payload(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize mock/quiz API shape and strip answers from the quiz body."""
    if raw is None:
        return None
    payload = copy.deepcopy(raw)
    if "data" in payload and isinstance(payload["data"], dict):
        payload["data"] = strip_quiz_answers(payload["data"])
    else:
        payload = strip_quiz_answers(payload)
    return payload
