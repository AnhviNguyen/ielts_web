"""Data access for shadowing videos and user watch history."""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ShadowingUserHistory, ShadowingVideo


class ShadowingRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_video_id(self, video_id: str) -> ShadowingVideo | None:
        r = await self._db.execute(
            select(ShadowingVideo).where(ShadowingVideo.video_id == video_id)
        )
        return r.scalar_one_or_none()

    async def upsert(
        self,
        *,
        video_id: str,
        title: str,
        level: str,
        language: str,
        source_url: str,
        transcript_source: str,
        segments: list,
        created_by: int | None,
    ) -> ShadowingVideo:
        row = await self.get_by_video_id(video_id)
        if row:
            row.title = title
            row.level = level
            row.language = language
            row.source_url = source_url
            row.transcript_source = transcript_source
            row.segments = segments
            return row

        row = ShadowingVideo(
            video_id=video_id,
            title=title,
            level=level,
            language=language,
            source_url=source_url,
            transcript_source=transcript_source,
            segments=segments,
            created_by=created_by,
        )
        self._db.add(row)
        await self._db.flush()
        await self._db.refresh(row)
        return row

    async def record_view(self, user_id: int, video_id: str) -> ShadowingUserHistory:
        r = await self._db.execute(
            select(ShadowingUserHistory).where(
                ShadowingUserHistory.user_id == user_id,
                ShadowingUserHistory.video_id == video_id,
            )
        )
        row = r.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if row:
            row.last_viewed_at = now
            return row
        row = ShadowingUserHistory(user_id=user_id, video_id=video_id, last_viewed_at=now)
        self._db.add(row)
        await self._db.flush()
        await self._db.refresh(row)
        return row

    async def list_history(self, user_id: int, *, limit: int = 30) -> list[tuple[ShadowingUserHistory, ShadowingVideo | None]]:
        r = await self._db.execute(
            select(ShadowingUserHistory, ShadowingVideo)
            .outerjoin(ShadowingVideo, ShadowingVideo.video_id == ShadowingUserHistory.video_id)
            .where(ShadowingUserHistory.user_id == user_id)
            .order_by(ShadowingUserHistory.last_viewed_at.desc())
            .limit(limit)
        )
        return list(r.all())

    async def get_history_entry(self, user_id: int, video_id: str) -> ShadowingUserHistory | None:
        r = await self._db.execute(
            select(ShadowingUserHistory).where(
                ShadowingUserHistory.user_id == user_id,
                ShadowingUserHistory.video_id == video_id,
            )
        )
        return r.scalar_one_or_none()

    async def update_history_display(
        self,
        user_id: int,
        video_id: str,
        *,
        display_title: str | None = None,
        display_level: str | None = None,
    ) -> ShadowingUserHistory | None:
        row = await self.get_history_entry(user_id, video_id)
        if not row:
            return None
        if display_title is not None:
            row.display_title = display_title.strip() or None
        if display_level is not None:
            row.display_level = display_level.strip() or None
        return row

    async def delete_history(self, user_id: int, video_id: str) -> bool:
        r = await self._db.execute(
            delete(ShadowingUserHistory).where(
                ShadowingUserHistory.user_id == user_id,
                ShadowingUserHistory.video_id == video_id,
            )
        )
        return (r.rowcount or 0) > 0
