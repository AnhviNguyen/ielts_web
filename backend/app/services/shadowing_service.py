"""
Shadowing pipeline: YouTube captions → normalize → optional translate → DB cache.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.repositories.shadowing_repository import ShadowingRepository
from app.core.config import settings
from app.services.shadowing_whisper_service import AudioTranscriptionError, transcribe_youtube_audio
from app.services.translate_service import translate_text
from app.services.youtube_transcript_service import (
    TranscriptNotFoundError,
    _is_bot_check_error,
    _youtube_proxy_config,
    fetch_youtube_transcript,
)
from app.utils.segment_utils import extract_youtube_video_id, normalize_segments

logger = logging.getLogger(__name__)


class ShadowingService:
    def __init__(self, repo: ShadowingRepository):
        self._repo = repo

    async def get_video(self, video_id: str) -> dict[str, Any] | None:
        row = await self._repo.get_by_video_id(video_id)
        if not row:
            return None
        return self._to_video_data(row)

    async def process_url(
        self,
        url: str,
        *,
        level: str = "Intermediate",
        translate: bool = True,
        user_id: int | None = None,
        force_refresh: bool = False,
        client_segments: list[dict[str, Any]] | None = None,
        client_language: str | None = None,
    ) -> dict[str, Any]:
        video_id = extract_youtube_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        if not force_refresh:
            cached = await self.get_video(video_id)
            if cached:
                return cached

        title = await self._fetch_video_title(video_id, url)
        raw: list[dict[str, Any]]
        language: str
        source: str

        if client_segments:
            raw = [
                {
                    "text": (seg.get("text") or "").strip(),
                    "start": float(seg.get("start", 0)),
                    "duration": max(0.1, float(seg.get("duration", 0.1))),
                }
                for seg in client_segments
                if (seg.get("text") or "").strip()
            ]
            if not raw:
                raise ValueError("Phụ đề từ trình duyệt trống — thử video khác có CC.")
            language = (client_language or "en").split("-")[0].lower()
            source = "client"
        else:
            try:
                raw, language = await asyncio.to_thread(fetch_youtube_transcript, video_id)
                source = "youtube"
            except TranscriptNotFoundError as e:
                logger.exception(
                    "Transcript failed | video=%s | error=%s",
                    video_id,
                    str(e),
                )
                err = str(e)
                if _is_bot_check_error(err):
                    if settings.ENVIRONMENT == "production" and _youtube_proxy_config() is None:
                        raise ValueError(
                            "Không lấy được phụ đề (IP server Oracle bị YouTube chặn). "
                            "Trang sẽ tự tải phụ đề từ trình duyệt — nếu vẫn lỗi, thêm proxy Webshare free "
                            "(YOUTUBE_WEBSHARE_USERNAME/PASSWORD trong .env) hoặc chọn video TED/BBC có CC EN."
                        ) from None
                    raise ValueError(
                        "YouTube chặn server khi lấy phụ đề. "
                        "Hãy chọn video có phụ đề EN (CC) — ví dụ TED Talk, BBC Learning English."
                    ) from None
                if settings.ENVIRONMENT == "production" and _youtube_proxy_config() is None:
                    raise ValueError(
                        "Video không có phụ đề hoặc server không truy cập được YouTube. "
                        "Thử video TED có CC EN; hoặc cấu hình Webshare proxy trên server."
                    ) from None
                if not settings.whisper_enabled:
                    raise ValueError(
                        "Video không có phụ đề YouTube. "
                        "Nhận dạng giọng nói (Whisper) chưa bật trên server — hãy chọn video có phụ đề EN."
                    ) from None
                logger.info("No YouTube captions for %s — Whisper fallback", video_id)
                try:
                    raw, language = await asyncio.to_thread(transcribe_youtube_audio, video_id)
                    source = "whisper"
                except AudioTranscriptionError as whisper_err:
                    if _is_bot_check_error(str(whisper_err)):
                        raise ValueError(
                            "Video không có phụ đề EN và Whisper bị YouTube chặn trên server. "
                            "Chọn video có phụ đề (CC) — bật CC trên YouTube trước khi dán link."
                        ) from whisper_err
                    raise ValueError(str(whisper_err)) from whisper_err

        segments = normalize_segments(raw, language=language)

        if translate and segments:
            segments = await self._translate_segments(segments, language)

        row = await self._repo.upsert(
            video_id=video_id,
            title=title,
            level=level or "Intermediate",
            language=language,
            source_url=url.strip(),
            transcript_source=source,
            segments=segments,
            created_by=user_id,
        )
        if user_id:
            await self._repo.record_view(user_id, video_id)
        return self._to_video_data(row)

    async def record_view(self, user_id: int, video_id: str) -> None:
        row = await self._repo.get_by_video_id(video_id)
        if not row:
            return
        await self._repo.record_view(user_id, video_id)

    async def list_history(self, user_id: int, *, limit: int = 30) -> list[dict[str, Any]]:
        rows = await self._repo.list_history(user_id, limit=limit)
        items: list[dict[str, Any]] = []
        for hist, video in rows:
            items.append(self._history_item_dict(hist, video))
        return items

    async def update_history_item(
        self,
        user_id: int,
        video_id: str,
        *,
        title: str | None = None,
        level: str | None = None,
    ) -> dict[str, Any] | None:
        row = await self._repo.update_history_display(
            user_id, video_id, display_title=title, display_level=level
        )
        if not row:
            return None
        video = await self._repo.get_by_video_id(video_id)
        return self._history_item_dict(row, video)

    async def delete_history_item(self, user_id: int, video_id: str) -> bool:
        return await self._repo.delete_history(user_id, video_id)

    @staticmethod
    def _thumbnail_url(video_id: str) -> str:
        return f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"

    def _history_item_dict(self, hist, video) -> dict[str, Any]:
        segs = (video.segments if video else None) or []
        base_title = (video.title if video else None) or hist.video_id
        base_level = (video.level if video else None) or "Intermediate"
        return {
            "video_id": hist.video_id,
            "title": hist.display_title or base_title,
            "level": hist.display_level or base_level,
            "language": (video.language if video else None) or "en",
            "transcript_source": video.transcript_source if video else None,
            "source_url": video.source_url if video else None,
            "segment_count": len(segs),
            "thumbnail_url": self._thumbnail_url(hist.video_id),
            "last_viewed_at": hist.last_viewed_at,
        }

    async def translate_one(self, text: str, from_lang: str = "en", to_lang: str = "vi") -> str:
        return await translate_text(text, from_lang, to_lang)

    async def _translate_segments(
        self,
        segments: list[dict[str, Any]],
        from_lang: str,
    ) -> list[dict[str, Any]]:
        # Skip translation for extremely long segments — they are not useful
        # for shadowing and would require hundreds of API calls.
        _MAX_TRANSLATABLE_CHARS = 2000

        async def _safe_translate(text: str) -> str:
            if len(text) > _MAX_TRANSLATABLE_CHARS:
                logger.warning(
                    "Segment too long for translation (%d chars) — skipping", len(text)
                )
                return ""
            try:
                return await translate_text(text, from_lang=from_lang, to_lang="vi")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Translation failed for segment: %s", exc)
                return ""

        # Translate concurrently with a semaphore to avoid flooding the API
        semaphore = asyncio.Semaphore(3)

        async def _bounded(seg: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                tr = await _safe_translate(seg["text"])
            return {**seg, "translation": tr}

        return list(await asyncio.gather(*[_bounded(s) for s in segments]))

    @staticmethod
    async def _fetch_video_title(video_id: str, fallback_url: str) -> str:
        oembed = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(oembed)
                if r.status_code == 200:
                    return r.json().get("title") or video_id
        except Exception:
            pass
        return fallback_url

    @staticmethod
    def _to_video_data(row) -> dict[str, Any]:
        segs = row.segments or []
        return {
            "video_id": row.video_id,
            "title": row.title or row.video_id,
            "level": row.level or "Intermediate",
            "language": row.language or "en",
            "transcript_source": row.transcript_source,
            "source_url": row.source_url,
            "segments": segs,
        }
