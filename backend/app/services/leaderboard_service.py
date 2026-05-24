"""
app/services/leaderboard_service.py
────────────────────────────────────
Leaderboard business logic: top N by XP and current user's global rank.
"""

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserProfile
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
    ) -> LeaderboardResponse:
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

        return LeaderboardResponse(
            top=top,
            current_user_rank=current_user_rank,
            current_user=current_user_entry,
        )
