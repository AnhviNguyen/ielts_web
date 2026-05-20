"""
app/routers/leaderboard.py — LinguaIELTS
Leaderboard endpoint: xếp hạng người dùng theo XP.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_optional
from app.db.database import get_db
from app.db.models import User, UserProfile

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("")
async def get_leaderboard(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    """
    Trả về top N người dùng xếp hạng theo XP.
    Public endpoint — không yêu cầu đăng nhập, nhưng nếu đăng nhập sẽ đánh dấu rank của mình.
    """
    stmt = (
        select(UserProfile, User.email)
        .join(User, User.id == UserProfile.user_id)
        .order_by(desc(UserProfile.xp), desc(UserProfile.streak), asc(UserProfile.user_id))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    current_user_id = current_user.id if current_user else None

    items = []
    for rank, (profile, email) in enumerate(rows, start=1):
        # Privacy: chỉ hiển thị phần trước @ của email nếu không có full_name
        display_name = profile.full_name or email.split("@")[0]
        items.append({
            "rank": rank,
            "user_id": profile.user_id,
            "display_name": display_name,
            "avatar_url": profile.avatar_url,
            "xp": profile.xp or 0,
            "streak": profile.streak or 0,
            "longest_streak": profile.longest_streak or 0,
            "is_current_user": profile.user_id == current_user_id,
        })

    # Nếu current_user không nằm trong top N, thêm rank của họ vào cuối
    current_user_rank = None
    if current_user_id and not any(i["is_current_user"] for i in items):
        rank_stmt = (
            select(UserProfile)
            .where(UserProfile.xp > (
                select(UserProfile.xp).where(UserProfile.user_id == current_user_id).scalar_subquery()
            ))
        )
        rank_result = await db.execute(rank_stmt)
        above_count = len(rank_result.scalars().all())
        current_user_rank = above_count + 1

        current_profile_stmt = select(UserProfile, User.email).join(User).where(UserProfile.user_id == current_user_id)
        cp_result = await db.execute(current_profile_stmt)
        cp_row = cp_result.first()
        if cp_row:
            cp, cp_email = cp_row
            items.append({
                "rank": current_user_rank,
                "user_id": cp.user_id,
                "display_name": cp.full_name or cp_email.split("@")[0],
                "avatar_url": cp.avatar_url,
                "xp": cp.xp or 0,
                "streak": cp.streak or 0,
                "longest_streak": cp.longest_streak or 0,
                "is_current_user": True,
            })

    return {
        "items": items,
        "current_user_rank": current_user_rank,
    }
