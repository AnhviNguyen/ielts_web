"""
app/services/leaderboard_service.py
────────────────────────────────────
Leaderboard: all-time XP, weekly/monthly activity score from History.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.leaderboard_redis import (
    get_rank as redis_rank,
    get_top as redis_top,
    is_ready as redis_leaderboard_ready,
    rebuild_from_db as rebuild_leaderboard_zset,
)
from app.db.models import History, User, UserProfile
from app.schemas import LeaderboardEntry, LeaderboardResponse


class LeaderboardService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _display_name(profile: UserProfile, email: str) -> str:
        return profile.full_name or email.split("@")[0]

    def _entry(
        self,
        rank: int,
        profile: UserProfile,
        email: str,
        *,
        is_current: bool,
    ) -> LeaderboardEntry:
        return LeaderboardEntry(
            rank=rank,
            user_id=profile.user_id,
            display_name=self._display_name(profile, email),
            avatar_url=profile.avatar_url,
            xp=profile.xp or 0,
            streak=profile.streak or 0,
            longest_streak=profile.longest_streak or 0,
            is_current_user=is_current,
        )

    async def get_leaderboard(
        self,
        *,
        top_n: int = 10,
        current_user_id: int | None = None,
        period: str = "all",
    ) -> LeaderboardResponse:
        period = (period or "all").lower()
        if period in ("weekly", "monthly"):
            return await self._get_period_leaderboard(
                period=period,
                top_n=top_n,
                current_user_id=current_user_id,
            )

        redis_response = await self._get_all_time_from_redis(
            top_n=top_n,
            current_user_id=current_user_id,
        )
        if redis_response is not None:
            return redis_response

        cache_key = f"leaderboard:top{top_n}"
        if current_user_id is None:
            cached = cache.get(cache_key)
            if cached:
                return LeaderboardResponse(**cached)

        order = (
            desc(UserProfile.xp),
            desc(UserProfile.streak),
            asc(UserProfile.user_id),
        )

        top_stmt = (
            select(UserProfile, User.email)
            .join(User, User.id == UserProfile.user_id)
            .where(
                User.is_active == True,  # noqa: E712
                UserProfile.is_leaderboard_hidden == False,  # noqa: E712
            )
            .order_by(*order)
            .limit(top_n)
        )
        top_rows = (await self._db.execute(top_stmt)).all()

        top: list[LeaderboardEntry] = []
        current_in_top = False
        for rank, (profile, email) in enumerate(top_rows, start=1):
            is_me = profile.user_id == current_user_id
            if is_me:
                current_in_top = True
            top.append(self._entry(rank, profile, email, is_current=is_me))

        current_user_rank: int | None = None
        current_user_entry: LeaderboardEntry | None = None

        if current_user_id is not None:
            xp_stmt = (
                select(UserProfile.xp)
                .join(User, User.id == UserProfile.user_id)
                .where(
                    UserProfile.user_id == current_user_id,
                    User.is_active == True,  # noqa: E712
                    UserProfile.is_leaderboard_hidden == False,  # noqa: E712
                )
            )
            xp_result = await self._db.execute(xp_stmt)
            my_xp = xp_result.scalar_one_or_none()

            if my_xp is not None:
                rank_stmt = (
                    select(func.count())
                    .select_from(UserProfile)
                    .join(User, User.id == UserProfile.user_id)
                    .where(
                        UserProfile.xp > my_xp,
                        User.is_active == True,  # noqa: E712
                        UserProfile.is_leaderboard_hidden == False,  # noqa: E712
                    )
                )
                rank_result = await self._db.execute(rank_stmt)
                current_user_rank = int(rank_result.scalar_one()) + 1

            if my_xp is not None and not current_in_top:
                me_stmt = (
                    select(UserProfile, User.email)
                    .join(User, User.id == UserProfile.user_id)
                    .where(
                        UserProfile.user_id == current_user_id,
                        User.is_active == True,  # noqa: E712
                        UserProfile.is_leaderboard_hidden == False,  # noqa: E712
                    )
                )
                me_row = (await self._db.execute(me_stmt)).first()
                if me_row:
                    profile, email = me_row
                    current_user_entry = self._entry(
                        current_user_rank,
                        profile,
                        email,
                        is_current=True,
                    )

        response = LeaderboardResponse(
            top=top,
            current_user_rank=current_user_rank,
            current_user=current_user_entry,
            period="all",
        )
        if current_user_id is None:
            cache.set(cache_key, response.model_dump(), ttl=300)
        return response

    async def _get_all_time_from_redis(
        self,
        *,
        top_n: int,
        current_user_id: int | None,
    ) -> LeaderboardResponse | None:
        """All-time board via Redis ZSET; None → caller uses PostgreSQL."""
        if not cache.ping():
            return None

        if not redis_leaderboard_ready():
            await rebuild_leaderboard_zset(self._db)
        if not redis_leaderboard_ready():
            return None

        top_pairs = redis_top(top_n)
        if not top_pairs:
            return None

        user_ids = [uid for uid, _ in top_pairs]
        if current_user_id is not None and current_user_id not in user_ids:
            user_ids.append(current_user_id)

        profile_map = await self._fetch_profiles_by_user_ids(user_ids)

        top: list[LeaderboardEntry] = []
        current_in_top = False
        for rank, (uid, xp) in enumerate(top_pairs, start=1):
            row = profile_map.get(uid)
            if not row:
                continue
            profile, email = row
            is_me = uid == current_user_id
            if is_me:
                current_in_top = True
            top.append(
                LeaderboardEntry(
                    rank=rank,
                    user_id=uid,
                    display_name=self._display_name(profile, email),
                    avatar_url=profile.avatar_url,
                    xp=int(xp),
                    streak=profile.streak or 0,
                    longest_streak=profile.longest_streak or 0,
                    is_current_user=is_me,
                )
            )

        current_user_rank: int | None = None
        current_user_entry: LeaderboardEntry | None = None

        if current_user_id is not None:
            current_user_rank = redis_rank(current_user_id)
            if not current_in_top and current_user_rank is not None:
                row = profile_map.get(current_user_id)
                if row:
                    profile, email = row
                    current_user_entry = self._entry(
                        current_user_rank,
                        profile,
                        email,
                        is_current=True,
                    )

        return LeaderboardResponse(
            top=top,
            current_user_rank=current_user_rank,
            current_user=current_user_entry,
            period="all",
        )

    async def _fetch_profiles_by_user_ids(
        self,
        user_ids: list[int],
    ) -> dict[int, tuple[UserProfile, str]]:
        if not user_ids:
            return {}
        stmt = (
            select(UserProfile, User.email)
            .join(User, User.id == UserProfile.user_id)
            .where(UserProfile.user_id.in_(user_ids))
        )
        rows = (await self._db.execute(stmt)).all()
        return {profile.user_id: (profile, email) for profile, email in rows}

    async def _get_period_leaderboard(
        self,
        *,
        period: str,
        top_n: int,
        current_user_id: int | None,
    ) -> LeaderboardResponse:
        """Rank by activity in period: attempts * 10 + avg band * 10 (shown as xp field)."""
        days = 7 if period == "weekly" else 30
        since = datetime.now(timezone.utc) - timedelta(days=days)

        agg = (
            select(
                History.user_id.label("user_id"),
                func.count(History.id).label("attempts"),
                func.coalesce(func.avg(History.band_score), 0.0).label("avg_band"),
            )
            .where(History.completed_at >= since)
            .group_by(History.user_id)
            .subquery()
        )

        score_expr = (agg.c.attempts * 10 + agg.c.avg_band * 10).label("activity_score")

        top_stmt = (
            select(UserProfile, User.email, score_expr)
            .join(agg, UserProfile.user_id == agg.c.user_id)
            .join(User, User.id == UserProfile.user_id)
            .order_by(desc(score_expr), asc(UserProfile.user_id))
            .limit(top_n)
        )
        top_rows = (await self._db.execute(top_stmt)).all()

        top: list[LeaderboardEntry] = []
        current_in_top = False
        for rank, (profile, email, activity_score) in enumerate(top_rows, start=1):
            uid = profile.user_id
            is_me = uid == current_user_id
            if is_me:
                current_in_top = True
            top.append(
                LeaderboardEntry(
                    rank=rank,
                    user_id=profile.user_id,
                    display_name=self._display_name(profile, email),
                    avatar_url=profile.avatar_url,
                    xp=int(activity_score or 0),
                    streak=profile.streak or 0,
                    longest_streak=profile.longest_streak or 0,
                    is_current_user=is_me,
                )
            )

        current_user_rank = None
        current_user_entry = None

        if current_user_id is not None:
            all_stmt = (
                select(agg.c.user_id, score_expr)
                .order_by(desc(score_expr), asc(agg.c.user_id))
            )
            all_rows = (await self._db.execute(all_stmt)).all()
            for rank, (uid, score) in enumerate(all_rows, start=1):
                if uid == current_user_id:
                    current_user_rank = rank
                    if not current_in_top:
                        me_stmt = (
                            select(UserProfile, User.email)
                            .join(User, User.id == UserProfile.user_id)
                            .where(UserProfile.user_id == current_user_id)
                        )
                        me_row = (await self._db.execute(me_stmt)).first()
                        if me_row:
                            profile, email = me_row
                            current_user_entry = LeaderboardEntry(
                                rank=rank,
                                user_id=current_user_id,
                                display_name=self._display_name(profile, email),
                                avatar_url=profile.avatar_url,
                                xp=int(score or 0),
                                streak=profile.streak or 0,
                                longest_streak=profile.longest_streak or 0,
                                is_current_user=True,
                            )
                    break

        return LeaderboardResponse(
            top=top,
            current_user_rank=current_user_rank,
            current_user=current_user_entry,
            period=period,
        )
