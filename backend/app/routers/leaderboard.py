"""
app/routers/leaderboard.py
──────────────────────────
Leaderboard HTTP layer: top 10 by XP + current user's rank.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_optional
from app.db.database import get_db
from app.db.models import User
from app.schemas import LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    top: int = Query(default=10, ge=1, le=50, description="Number of top users to return"),
    period: str = Query(
        default="all",
        description="all = lifetime XP; weekly | monthly = activity score from recent attempts",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> LeaderboardResponse:
    """
    Top N users by XP (default 10) and the authenticated user's global rank.
    Public endpoint; optional JWT marks the current user in the response.
    """
    return await LeaderboardService(db).get_leaderboard(
        top_n=top,
        current_user_id=current_user.id if current_user else None,
        period=period,
    )
