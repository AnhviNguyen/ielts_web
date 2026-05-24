from datetime import datetime, timedelta, timezone
from math import ceil

from fastapi import HTTPException, status

from app.db.models import History, User, UserProfile
from app.repositories.admin_repository import AdminRepository
from app.schemas import (
    AdminAnomalyItem,
    AdminBandBucket,
    AdminDailyActiveUsers,
    AdminDailyAttempts,
    AdminHistoryItem,
    AdminLeaderboardResponse,
    AdminOverviewResponse,
    AdminPracticeSummary,
    AdminRetentionBucket,
    AdminSkillAverage,
    AdminStreakBucket,
    AdminSystemVocabCopyResponse,
    AdminSystemVocabTopicCreate,
    AdminSystemVocabTopicDetail,
    AdminSystemVocabTopicResponse,
    AdminSystemVocabTopicUpdate,
    AdminSystemVocabWordCreate,
    AdminSystemVocabWordResponse,
    AdminSystemVocabWordUpdate,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
    ProgressResponse,
)


class AdminService:
    def __init__(self, repo: AdminRepository) -> None:
        self._repo = repo

    @staticmethod
    def _pages(total: int, page_size: int) -> int:
        return max(1, ceil(total / page_size)) if total else 1

    @staticmethod
    def _user_item(user: User, profile: UserProfile | None) -> AdminUserListItem:
        return AdminUserListItem(
            id=user.id,
            email=user.email,
            full_name=profile.full_name if profile else None,
            created_at=user.created_at,
            role=user.role,
            is_active=user.is_active,
            locked_at=user.locked_at,
            lock_reason=user.lock_reason,
            xp=profile.xp if profile else 0,
            streak=profile.streak if profile else 0,
            longest_streak=profile.longest_streak if profile else 0,
            target_band=profile.target_band if profile else None,
            is_leaderboard_hidden=profile.is_leaderboard_hidden if profile else False,
            leaderboard_flag_reason=profile.leaderboard_flag_reason if profile else None,
            leaderboard_hidden_at=profile.leaderboard_hidden_at if profile else None,
        )

    async def list_users(
        self,
        *,
        q: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        leaderboard_hidden: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "created_desc",
    ) -> AdminUserListResponse:
        total = await self._repo.count_users(
            q=q,
            role=role,
            is_active=is_active,
            leaderboard_hidden=leaderboard_hidden,
        )
        rows = await self._repo.list_users(
            q=q,
            role=role,
            is_active=is_active,
            leaderboard_hidden=leaderboard_hidden,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        return AdminUserListResponse(
            items=[self._user_item(user, profile) for user, profile in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=self._pages(total, page_size),
        )

    async def get_user_detail(self, user_id: int) -> AdminUserDetail:
        row = await self._repo.get_user_with_profile(user_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user, profile = row
        base = self._user_item(user, profile)

        progress = await self._repo.list_progress(user_id)
        recent_history = await self._repo.list_recent_history(user_id)
        session_counts = await self._repo.count_practice_sessions_by_status(user_id)
        total_sessions = sum(session_counts.values())

        return AdminUserDetail(
            **base.model_dump(),
            avatar_url=profile.avatar_url if profile else None,
            phone=profile.phone if profile else None,
            bio=profile.bio if profile else None,
            exam_date=profile.exam_date if profile else None,
            last_activity_date=profile.last_activity_date if profile else None,
            progress=[
                ProgressResponse(
                    id=row.id,
                    user_id=row.user_id,
                    subject=row.subject,
                    total_questions=row.total_questions,
                    completed_questions=row.completed_questions,
                    percentage=row.percentage,
                    band_score=row.band_score,
                    updated_at=row.updated_at,
                )
                for row in progress
            ],
            recent_history=[
                AdminHistoryItem(
                    id=h.id,
                    quiz_id=h.quiz_id,
                    subject=h.subject,
                    score=h.score,
                    total_questions=h.total_questions,
                    percentage=h.percentage,
                    band_score=h.band_score,
                    mode=h.mode,
                    completed_at=h.completed_at,
                )
                for h in recent_history
            ],
            practice_summary=AdminPracticeSummary(
                total=total_sessions,
                started=session_counts.get("started", 0),
                submitted=session_counts.get("submitted", 0),
            ),
            vocab_topic_count=await self._repo.count_vocab_topics(user_id),
            vocab_word_count=await self._repo.count_vocab_words(user_id),
            shadowing_video_count=await self._repo.count_shadowing_videos(user_id),
        )

    async def update_user_status(
        self,
        *,
        target_user_id: int,
        admin_user_id: int,
        is_active: bool,
        lock_reason: str | None,
    ) -> AdminUserDetail:
        row = await self._repo.get_user_with_profile(target_user_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user, _ = row
        if target_user_id == admin_user_id and not is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot lock themselves")

        user.is_active = is_active
        if is_active:
            user.locked_at = None
            user.lock_reason = None
        else:
            user.locked_at = datetime.now(timezone.utc)
            user.lock_reason = (lock_reason or "").strip() or None
        await self._repo.update_user(user)
        return await self.get_user_detail(target_user_id)

    async def reset_xp_streak(self, user_id: int, *, reset_xp: bool, reset_streak: bool) -> AdminUserDetail:
        row = await self._repo.get_user_with_profile(user_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        _, profile = row
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

        if reset_xp:
            profile.xp = 0
        if reset_streak:
            profile.streak = 0
            profile.longest_streak = 0
            profile.last_activity_date = None
        await self._repo.update_profile(profile)
        return await self.get_user_detail(user_id)

    async def update_leaderboard_visibility(
        self,
        user_id: int,
        *,
        is_hidden: bool,
        reason: str | None,
    ) -> AdminUserDetail:
        row = await self._repo.get_user_with_profile(user_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        _, profile = row
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

        profile.is_leaderboard_hidden = is_hidden
        profile.leaderboard_flag_reason = (reason or "").strip() or None if is_hidden else None
        profile.leaderboard_hidden_at = datetime.now(timezone.utc) if is_hidden else None
        await self._repo.update_profile(profile)
        return await self.get_user_detail(user_id)

    def _band_buckets(self, scores: list[float]) -> list[AdminBandBucket]:
        buckets = {"0-4.0": 0, "4.5-5.5": 0, "6.0-7.0": 0, "7.5-9.0": 0}
        for score in scores:
            if score <= 4:
                buckets["0-4.0"] += 1
            elif score <= 5.5:
                buckets["4.5-5.5"] += 1
            elif score <= 7:
                buckets["6.0-7.0"] += 1
            else:
                buckets["7.5-9.0"] += 1
        return [AdminBandBucket(label=label, count=count) for label, count in buckets.items()]

    @staticmethod
    def _streak_label(streak: int | None) -> str:
        value = int(streak or 0)
        if value <= 0:
            return "0"
        if value < 7:
            return "1-6"
        if value < 30:
            return "7-29"
        return "30+"

    async def _activity_user_ids_by_day(self, days: list) -> dict:
        if not days:
            return {}
        first_day = min(days)
        since = datetime.combine(first_day, datetime.min.time(), tzinfo=timezone.utc)
        activity: dict = {day: set() for day in days}

        for row in await self._repo.list_history_since(since):
            day = row.completed_at.date()
            if day in activity:
                activity[day].add(row.user_id)

        for row in await self._repo.list_practice_sessions_since(since):
            for value in (row.started_at, row.submitted_at):
                if not value:
                    continue
                day = value.date()
                if day in activity:
                    activity[day].add(row.user_id)

        for profile in await self._repo.list_profile_activity_since(first_day):
            day = profile.last_activity_date
            if day in activity:
                activity[day].add(profile.user_id)

        return activity

    async def _retention_by_streak(self, today, recent_active_ids: set[int], active_today_ids: set[int]) -> list[AdminRetentionBucket]:
        profiles = await self._repo.list_all_profiles()
        counts = {
            label: {"total": 0, "today": 0, "recent": 0}
            for label in ("0", "1-6", "7-29", "30+")
        }
        for profile in profiles:
            label = self._streak_label(profile.streak)
            counts[label]["total"] += 1
            if profile.user_id in active_today_ids or profile.last_activity_date == today:
                counts[label]["today"] += 1
            if profile.user_id in recent_active_ids:
                counts[label]["recent"] += 1

        return [
            AdminRetentionBucket(
                label=label,
                total_users=values["total"],
                active_today=values["today"],
                active_last_7_days=values["recent"],
                retention_rate=round((values["recent"] / values["total"]) * 100, 2) if values["total"] else 0.0,
            )
            for label, values in counts.items()
        ]

    async def _max_band_jump(self, user_id: int) -> float:
        rows = await self._repo.user_band_history(user_id)
        max_jump = 0.0
        previous_by_subject: dict[str, History] = {}
        for row in rows:
            subject = (row.subject or "").lower()
            if not subject:
                continue
            previous = previous_by_subject.get(subject)
            if previous and previous.band_score is not None and row.band_score is not None:
                max_jump = max(max_jump, float(row.band_score) - float(previous.band_score))
            previous_by_subject[subject] = row
        return round(max_jump, 2)

    async def _anomaly_items(self, *, limit: int = 10) -> list[AdminAnomalyItem]:
        rows = await self._repo.list_users(page=1, page_size=100, sort="xp_desc")
        attempts_24h = await self._repo.attempts_24h_by_user()
        items: list[AdminAnomalyItem] = []
        for user, profile in rows:
            if not profile:
                continue
            reasons: list[str] = []
            if (profile.xp or 0) >= 5000:
                reasons.append("XP very high")
            if (profile.streak or 0) >= 60:
                reasons.append("Long streak")
            if attempts_24h.get(user.id, 0) >= 20:
                reasons.append("Many attempts in 24h")
            max_jump = await self._max_band_jump(user.id)
            if max_jump >= 2.0:
                reasons.append("Band jump >= 2.0")
            if profile.is_leaderboard_hidden:
                reasons.append("Hidden from leaderboard")
            if not reasons:
                continue
            items.append(
                AdminAnomalyItem(
                    **self._user_item(user, profile).model_dump(),
                    attempts_24h=attempts_24h.get(user.id, 0),
                    max_band_jump=max_jump,
                    reasons=reasons,
                )
            )
            if len(items) >= limit:
                break
        return items

    async def get_overview(self) -> AdminOverviewResponse:
        now = datetime.now(timezone.utc)
        start_7 = now - timedelta(days=6)
        recent_history = await self._repo.list_history_since(start_7.replace(hour=0, minute=0, second=0, microsecond=0))
        daily_counts = {(now.date() - timedelta(days=i)): 0 for i in range(6, -1, -1)}
        for row in recent_history:
            key = row.completed_at.date()
            if key in daily_counts:
                daily_counts[key] += 1
        activity_by_day = await self._activity_user_ids_by_day(list(daily_counts.keys()))
        active_today_ids = activity_by_day.get(now.date(), set())
        recent_active_ids: set[int] = set()
        for ids in activity_by_day.values():
            recent_active_ids.update(ids)

        return AdminOverviewResponse(
            total_users=await self._repo.count_all_users(),
            active_users=await self._repo.count_active_users(),
            locked_users=await self._repo.count_locked_users(),
            attempts_today=daily_counts.get(now.date(), 0),
            attempts_last_7_days=[
                AdminDailyAttempts(date=day, attempts=count)
                for day, count in daily_counts.items()
            ],
            dau_today=len(active_today_ids),
            dau_last_7_days=[
                AdminDailyActiveUsers(date=day, active_users=len(activity_by_day.get(day, set())))
                for day in daily_counts
            ],
            average_band_by_skill=[
                AdminSkillAverage(subject=subject, average_band=round(avg, 2), attempts=count)
                for subject, avg, count in await self._repo.average_band_by_skill()
            ],
            band_distribution=self._band_buckets(await self._repo.list_band_scores()),
            streak_buckets=[
                AdminStreakBucket(label=label, count=count)
                for label, count in await self._repo.streak_bucket_counts()
            ],
            retention_by_streak=await self._retention_by_streak(now.date(), recent_active_ids, active_today_ids),
            top_suspicious_users=await self._anomaly_items(limit=8),
        )

    @staticmethod
    def _system_topic_response(topic, word_count: int = 0) -> AdminSystemVocabTopicResponse:
        return AdminSystemVocabTopicResponse(
            id=topic.id,
            name=topic.name,
            description=topic.description,
            level=topic.level,
            sort_order=topic.sort_order,
            is_active=topic.is_active,
            word_count=word_count,
            created_at=topic.created_at,
            updated_at=topic.updated_at,
        )

    @staticmethod
    def _system_word_response(word) -> AdminSystemVocabWordResponse:
        return AdminSystemVocabWordResponse(
            id=word.id,
            topic_id=word.topic_id,
            word=word.word,
            phonetic=word.phonetic,
            word_type=word.word_type,
            meaning_en=word.meaning_en,
            meaning_vi=word.meaning_vi,
            example=word.example,
            example_vi=word.example_vi,
            tags=word.tags or [],
            sort_order=word.sort_order,
            created_at=word.created_at,
            updated_at=word.updated_at,
        )

    async def list_system_vocab_topics(
        self,
        *,
        q: str | None = None,
        active: bool | None = None,
    ) -> list[AdminSystemVocabTopicResponse]:
        rows = await self._repo.list_system_vocab_topics(q=q, active=active)
        return [self._system_topic_response(topic, word_count) for topic, word_count in rows]

    async def create_system_vocab_topic(self, body: AdminSystemVocabTopicCreate) -> AdminSystemVocabTopicResponse:
        topic = await self._repo.create_system_vocab_topic(body.model_dump())
        return self._system_topic_response(topic, 0)

    async def get_system_vocab_topic_detail(self, topic_id: int) -> AdminSystemVocabTopicDetail:
        topic = await self._repo.get_system_vocab_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System vocab topic not found")
        words = await self._repo.list_system_vocab_words(topic_id)
        return AdminSystemVocabTopicDetail(
            topic=self._system_topic_response(topic, len(words)),
            words=[self._system_word_response(word) for word in words],
        )

    async def update_system_vocab_topic(self, topic_id: int, body: AdminSystemVocabTopicUpdate) -> AdminSystemVocabTopicResponse:
        topic = await self._repo.get_system_vocab_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System vocab topic not found")
        data = body.model_dump(exclude_unset=True)
        topic = await self._repo.update_system_vocab_topic(topic, data)
        words = await self._repo.list_system_vocab_words(topic_id)
        return self._system_topic_response(topic, len(words))

    async def delete_system_vocab_topic(self, topic_id: int) -> dict[str, str]:
        topic = await self._repo.get_system_vocab_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System vocab topic not found")
        await self._repo.delete_system_vocab_topic(topic)
        return {"message": "System vocab topic deleted"}

    async def list_system_vocab_words(self, topic_id: int) -> list[AdminSystemVocabWordResponse]:
        topic = await self._repo.get_system_vocab_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System vocab topic not found")
        return [self._system_word_response(word) for word in await self._repo.list_system_vocab_words(topic_id)]

    async def create_system_vocab_word(self, topic_id: int, body: AdminSystemVocabWordCreate) -> AdminSystemVocabWordResponse:
        topic = await self._repo.get_system_vocab_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System vocab topic not found")
        word = await self._repo.create_system_vocab_word(topic_id, body.model_dump())
        return self._system_word_response(word)

    async def update_system_vocab_word(self, topic_id: int, word_id: int, body: AdminSystemVocabWordUpdate) -> AdminSystemVocabWordResponse:
        word = await self._repo.get_system_vocab_word(topic_id, word_id)
        if not word:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System vocab word not found")
        word = await self._repo.update_system_vocab_word(word, body.model_dump(exclude_unset=True))
        return self._system_word_response(word)

    async def delete_system_vocab_word(self, topic_id: int, word_id: int) -> dict[str, str]:
        word = await self._repo.get_system_vocab_word(topic_id, word_id)
        if not word:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System vocab word not found")
        await self._repo.delete_system_vocab_word(word)
        return {"message": "System vocab word deleted"}

    async def copy_system_vocab_to_user(
        self,
        topic_id: int,
        *,
        user_id: int,
        target_topic_id: int | None,
        target_topic_name: str | None,
        word_ids: list[int],
    ) -> AdminSystemVocabCopyResponse:
        source_topic = await self._repo.get_system_vocab_topic(topic_id)
        if not source_topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System vocab topic not found")
        if not await self._repo.get_user_with_profile(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if target_topic_id:
            target_topic = await self._repo.get_user_vocab_topic(user_id, target_topic_id)
            if not target_topic:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user vocab topic not found")
        else:
            name = (target_topic_name or source_topic.name).strip() or source_topic.name
            target_topic = await self._repo.find_user_vocab_topic_by_name(user_id, name)
            if not target_topic:
                target_topic = await self._repo.create_user_vocab_topic(user_id, name)

        selected_ids = {int(x) for x in word_ids or []}
        source_words = await self._repo.list_system_vocab_words(topic_id)
        if selected_ids:
            source_words = [word for word in source_words if word.id in selected_ids]

        existing = {
            (word.word or "").strip().lower()
            for word in await self._repo.list_user_vocab_words(target_topic.id)
        }
        copied = 0
        skipped = 0
        for word in source_words:
            key = (word.word or "").strip().lower()
            if not key or key in existing:
                skipped += 1
                continue
            await self._repo.create_user_vocab_word(
                target_topic.id,
                {
                    "word": word.word,
                    "phonetic": word.phonetic,
                    "word_type": word.word_type,
                    "meaning_en": word.meaning_en,
                    "meaning_vi": word.meaning_vi,
                    "example": word.example,
                    "example_vi": word.example_vi,
                    "note": None,
                    "source_type": "system",
                    "source_quiz_id": f"system-topic-{topic_id}",
                },
            )
            existing.add(key)
            copied += 1

        return AdminSystemVocabCopyResponse(
            target_topic_id=target_topic.id,
            target_topic_name=target_topic.name,
            copied=copied,
            skipped_duplicates=skipped,
        )

    async def list_leaderboard(
        self,
        *,
        q: str | None = None,
        hidden: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminLeaderboardResponse:
        total = await self._repo.count_users(q=q, leaderboard_hidden=hidden)
        rows = await self._repo.list_users(
            q=q,
            leaderboard_hidden=hidden,
            page=page,
            page_size=page_size,
            sort="xp_desc",
        )
        attempts_24h = await self._repo.attempts_24h_by_user()
        items = []
        for user, profile in rows:
            max_jump = await self._max_band_jump(user.id)
            reasons: list[str] = []
            if profile and (profile.xp or 0) >= 5000:
                reasons.append("XP very high")
            if profile and (profile.streak or 0) >= 60:
                reasons.append("Long streak")
            if attempts_24h.get(user.id, 0) >= 20:
                reasons.append("Many attempts in 24h")
            if max_jump >= 2.0:
                reasons.append("Band jump >= 2.0")
            if profile and profile.is_leaderboard_hidden:
                reasons.append("Hidden from leaderboard")
            items.append(
                AdminAnomalyItem(
                    **self._user_item(user, profile).model_dump(),
                    attempts_24h=attempts_24h.get(user.id, 0),
                    max_band_jump=max_jump,
                    reasons=reasons,
                )
            )
        return AdminLeaderboardResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=self._pages(total, page_size),
        )

    async def list_anomalies(self) -> AdminLeaderboardResponse:
        items = await self._anomaly_items(limit=50)
        return AdminLeaderboardResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=len(items) or 1,
            total_pages=1,
        )
