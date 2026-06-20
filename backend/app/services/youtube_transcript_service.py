"""
Fetch YouTube captions via youtube-transcript-api (v1+ instance API).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TranscriptNotFoundError(Exception):
    pass


def _raw_from_fetched(fetched: Any) -> list[dict[str, Any]]:
    if hasattr(fetched, "to_raw_data"):
        return fetched.to_raw_data()
    raw: list[dict[str, Any]] = []
    for item in fetched:
        if isinstance(item, dict):
            raw.append({
                "text": item.get("text", ""),
                "start": float(item.get("start", 0)),
                "duration": float(item.get("duration", 0.1)),
            })
        else:
            raw.append({
                "text": getattr(item, "text", ""),
                "start": float(getattr(item, "start", 0)),
                "duration": float(getattr(item, "duration", 0.1)),
            })
    return raw


def _language_from_fetched(fetched: Any, fallback: str = "en") -> str:
    code = getattr(fetched, "language_code", None) or getattr(fetched, "language", None) or fallback
    return str(code).split("-")[0].lower()


def fetch_youtube_transcript(video_id: str, preferred_langs: list[str] | None = None) -> tuple[list[dict[str, Any]], str]:
    """
    Returns (raw_entries, language_code).
    Each entry: { text, start, duration }
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
    )

    api = YouTubeTranscriptApi()
    langs = preferred_langs or ["en", "en-US", "en-GB", "vi", "vi-VN"]

    try:
        fetched = api.fetch(video_id, languages=langs)
        raw = _raw_from_fetched(fetched)
        language = _language_from_fetched(fetched)
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as e:
        raise TranscriptNotFoundError(str(e)) from e
    except Exception as e:

        logger.exception(
            "api.fetch() failed | type=%s | error=%s",
            type(e).__name__,
            str(e),
        )

        try:
            transcript_list = api.list(video_id)
            transcript = None
            for lang in langs:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except Exception:
                    continue
            if transcript is None:
                try:
                    transcript = transcript_list.find_generated_transcript(["en"])
                except Exception:
                    transcript = transcript_list.find_manually_created_transcript(["en"])
            if transcript is None:
                raise TranscriptNotFoundError("No captions available")
            fetched = transcript.fetch()
            raw = _raw_from_fetched(fetched)
            language = _language_from_fetched(
                fetched,
                getattr(transcript, "language_code", "en") or "en",
            )
        except TranscriptNotFoundError:
            raise
        except Exception as e:

            logger.exception(
                "api.list() failed | type=%s | error=%s",
                type(e).__name__,
                str(e),
            )

            raise TranscriptNotFoundError(str(e)) from e

    if not raw:
        raise TranscriptNotFoundError("Empty transcript")

    logger.info("YouTube transcript fetched: video=%s lang=%s lines=%d", video_id, language, len(raw))
    return raw, language
