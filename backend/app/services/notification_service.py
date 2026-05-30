"""In-app notifications + reminder settings + daily email digest."""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification, NotificationSettings, User, UserProfile
from app.schemas import (
    NotificationItem,
    NotificationListResponse,
    NotificationSettingsRequest,
    NotificationSettingsResponse,
)
from app.services.email_service import send_daily_study_reminder_email, smtp_configured

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_settings(self, user: User) -> NotificationSettingsResponse:
        row = await self._get_or_create_settings(user.id)
        return NotificationSettingsResponse.model_validate(row)

    async def update_settings(
        self, user: User, payload: NotificationSettingsRequest
    ) -> NotificationSettingsResponse:
        row = await self._get_or_create_settings(user.id)
        data = payload.model_dump(exclude_unset=True)
        for key, val in data.items():
            setattr(row, key, val)
        self._db.add(row)
        await self._db.flush()
        return NotificationSettingsResponse.model_validate(row)

    async def list_notifications(
        self, user: User, *, limit: int = 30, unread_only: bool = False
    ) -> NotificationListResponse:
        q = select(Notification).where(Notification.user_id == user.id)
        if unread_only:
            q = q.where(Notification.is_read.is_(False))
        q = q.order_by(Notification.created_at.desc()).limit(limit)
        rows = (await self._db.execute(q)).scalars().all()

        unread_rs = await self._db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
        )
        unread = int(unread_rs.scalar_one() or 0)
        items = [NotificationItem.model_validate(n) for n in rows]
        return NotificationListResponse(items=items, unread_count=unread)

    async def mark_read(self, user: User, notification_id: int) -> NotificationItem:
        result = await self._db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user.id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise ValueError("Notification not found")
        row.is_read = True
        self._db.add(row)
        await self._db.flush()
        return NotificationItem.model_validate(row)

    async def mark_all_read(self, user: User) -> int:
        result = await self._db.execute(
            update(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        return int(result.rowcount or 0)

    async def create(
        self,
        user_id: int,
        *,
        type: str,
        title: str,
        body: str,
        link_path: str | None = None,
    ) -> Notification:
        row = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            link_path=link_path,
        )
        self._db.add(row)
        await self._db.flush()
        return row

    async def maybe_streak_reminder(self, user: User) -> None:
        """Create in-app reminder if streak at risk (once per day)."""
        profile_rs = await self._db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_rs.scalar_one_or_none()
        if not profile or int(profile.streak or 0) < 1:
            return

        today = date.today()
        if profile.last_activity_date == today:
            return

        settings = await self._get_or_create_settings(user.id)
        if not settings.reminder_enabled:
            return

        start = datetime.combine(today, time.min, tzinfo=timezone.utc)
        existing = await self._db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user.id,
                Notification.type == "streak_reminder",
                Notification.created_at >= start,
            )
        )
        if int(existing.scalar_one() or 0) > 0:
            return

        await self.create(
            user.id,
            type="streak_reminder",
            title="Giữ streak hôm nay!",
            body=f"Bạn đang có {profile.streak} ngày streak. Làm ít nhất 1 bài để không mất.",
            link_path="/dashboard?tab=study",
        )

    async def notify_badge_unlocked(self, user_id: int, badge_title: str, badge_id: str) -> None:
        await self.create(
            user_id,
            type="badge",
            title="Huy hiệu mới!",
            body=f"Bạn vừa mở khóa: {badge_title}",
            link_path="/profile",
        )

    async def _get_or_create_settings(self, user_id: int) -> NotificationSettings:
        result = await self._db.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if row:
            return row
        row = NotificationSettings(user_id=user_id)
        self._db.add(row)
        await self._db.flush()
        return row


async def send_daily_reminders_for_all(db: AsyncSession) -> int:
    """Called from Celery beat — email digest for users with email_daily_digest."""
    if not smtp_configured():
        logger.info("SMTP not configured — skip daily reminder emails")
        return 0

    result = await db.execute(
        select(User, NotificationSettings, UserProfile)
        .join(NotificationSettings, NotificationSettings.user_id == User.id)
        .join(UserProfile, UserProfile.user_id == User.id)
        .where(
            NotificationSettings.reminder_enabled.is_(True),
            NotificationSettings.email_daily_digest.is_(True),
        )
    )
    sent = 0
    for user, settings, profile in result.all():
        try:
            await send_daily_study_reminder_email(
                to_email=user.email,
                full_name=profile.full_name or user.email,
                streak=int(profile.streak or 0),
            )
            sent += 1
        except Exception as exc:
            logger.warning("Daily reminder failed for user %s: %s", user.id, exc)
    return sent
