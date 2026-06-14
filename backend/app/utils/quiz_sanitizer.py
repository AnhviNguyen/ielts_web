"""Strip answer keys from quiz JSON before sending to the client."""
from __future__ import annotations

import copy
from typing import Any

from app.core.media_assets import public_audio_url, public_image_url

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


def attach_quiz_media_urls(data: Any) -> Any:
    """Add audio_url / image URLs for listening parts and quiz assets."""
    if isinstance(data, dict):
        out = {k: attach_quiz_media_urls(v) for k, v in data.items()}
        file_id = out.get("file_id")
        if isinstance(file_id, str) and file_id.strip():
            out["audio_url"] = public_audio_url(file_id)
        audio_url = out.get("audio_url")
        if isinstance(audio_url, str) and audio_url.strip() and not audio_url.startswith(("http://", "https://")):
            out["audio_url"] = public_audio_url(audio_url)
        thumb = out.get("thumbnail")
        if isinstance(thumb, str) and thumb.strip() and not thumb.startswith(("http://", "https://", "/")):
            out["thumbnail_url"] = public_image_url(thumb)
        graph_id = out.get("writing_graph_image")
        if isinstance(graph_id, str) and graph_id.strip():
            out["chart_image_url"] = public_image_url(graph_id)
        return out
    if isinstance(data, list):
        return [attach_quiz_media_urls(item) for item in data]
    return data


def sanitize_quiz_payload(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize mock/quiz API shape, strip answers, attach CDN media URLs."""
    if raw is None:
        return None
    payload = copy.deepcopy(raw)
    if "data" in payload and isinstance(payload["data"], dict):
        payload["data"] = attach_quiz_media_urls(strip_quiz_answers(payload["data"]))
    else:
        payload = attach_quiz_media_urls(strip_quiz_answers(payload))
    return payload
