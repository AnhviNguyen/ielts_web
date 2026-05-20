from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import History, Progress, User, UserProfile
from app.repositories.profile_repository import ProfileRepository
from app.schemas import (
    MessageResponse,
    SkillRadarResponse,
    StudyPlanResponse,
    StudyPlanTaskResponse,
    UserMeResponse,
    UserMeUpdateRequest,
)
from app.services.study_plan_service import StudyPlanService
from app.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["Users"])

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_OPENROUTER_MODEL = "anthropic/claude-3-haiku"


class DashboardChatMessage(BaseModel):
    role: str
    content: str


class DashboardChatRequest(BaseModel):
    user_message: str
    history: list[DashboardChatMessage] = []


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserMeResponse:
    return await UsersService(db).get_me(current_user)


@router.patch("/me", response_model=UserMeResponse)
async def patch_me(
    payload: UserMeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserMeResponse:
    return await UsersService(db).update_me(current_user, payload)


@router.put("/me/avatar", response_model=MessageResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    suffix = Path(file.filename or "").suffix.lower() or ".bin"
    upload_dir = Path(settings.AVATAR_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"user-{current_user.id}-{uuid4().hex}{suffix}"
    file_path = upload_dir / filename
    data = await file.read()
    file_path.write_bytes(data)

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if profile:
        profile.avatar_url = f"/uploads/avatars/{filename}"
        db.add(profile)
        await db.flush()

    return MessageResponse(message="Avatar uploaded successfully")


@router.post("/me/activity-ping")
async def activity_ping(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Gọi khi user mở app/trang — cập nhật streak nếu chưa active hôm nay.
    Không cộng XP (chỉ đánh dấu hoạt động).
    """
    profile_repo = ProfileRepository(db)
    profile = await profile_repo.update_streak_and_xp(current_user.id, xp_to_add=0)
    return {
        "streak": profile.streak if profile else 0,
        "last_activity_date": profile.last_activity_date.isoformat() if profile and profile.last_activity_date else None,
    }


@router.get("/me/streak")
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"streak": 0, "longest_streak": 0, "last_activity_date": None}
    return {
        "streak": profile.streak,
        "longest_streak": profile.longest_streak,
        "last_activity_date": profile.last_activity_date,
    }


@router.get("/me/progress")
async def get_me_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Progress).where(Progress.user_id == current_user.id))
    rows = result.scalars().all()
    return {
        "items": [
            {
                "subject": row.subject,
                "percentage": row.percentage,
                "band_score": row.band_score,
            }
            for row in rows
        ]
    }


@router.get("/me/badges")
async def get_badges() -> dict:
    return {"items": []}


@router.get("/me/skill-radar", response_model=SkillRadarResponse)
async def get_skill_radar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillRadarResponse:
    """
    Return average band scores computed from the user's FIRST attempt per quiz per skill.
    Uses a subquery: for each (quiz_id, subject) pair find MIN(completed_at),
    then averages the band_score of those first attempts grouped by skill.
    """
    # Subquery: first completed_at per (quiz_id, subject) for this user
    sub = (
        select(
            History.quiz_id,
            History.subject,
            func.min(History.completed_at).label("first_at"),
        )
        .where(
            History.user_id == current_user.id,
            History.quiz_id.isnot(None),
            History.band_score.isnot(None),
        )
        .group_by(History.quiz_id, History.subject)
        .subquery()
    )

    # Join back to get band_score of those first attempts
    stmt = (
        select(
            History.subject,
            func.avg(History.band_score).label("avg_band"),
            func.count(History.id).label("cnt"),
        )
        .join(
            sub,
            (History.quiz_id == sub.c.quiz_id)
            & (History.subject == sub.c.subject)
            & (History.completed_at == sub.c.first_at)
            & (History.user_id == current_user.id),
        )
        .group_by(History.subject)
    )

    result = await db.execute(stmt)
    rows = result.all()

    scores: dict[str, float] = {}
    attempts: dict[str, int] = {}
    for row in rows:
        skill = (row.subject or "").lower()
        if skill in ("reading", "listening", "writing", "speaking"):
            scores[skill] = round(float(row.avg_band), 2)
            attempts[skill] = int(row.cnt)

    return SkillRadarResponse(
        reading=scores.get("reading", 0.0),
        listening=scores.get("listening", 0.0),
        writing=scores.get("writing", 0.0),
        speaking=scores.get("speaking", 0.0),
        attempts=attempts,
    )


@router.get("/me/study-plan", response_model=StudyPlanResponse)
async def get_study_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudyPlanResponse:
    return await StudyPlanService(db).get_plan(current_user)


@router.post(
    "/me/study-plan/generate",
    response_model=StudyPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_study_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudyPlanResponse:
    """Generate a fresh 5-day AI study plan (replaces existing plan)."""
    return await StudyPlanService(db).generate_plan(current_user)


@router.post("/me/study-plan/extend", response_model=StudyPlanResponse)
async def extend_study_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudyPlanResponse:
    """Append 5 more days to the existing study plan."""
    return await StudyPlanService(db).extend_plan(current_user)


@router.patch(
    "/me/study-plan/{task_id}/complete",
    response_model=StudyPlanTaskResponse,
)
async def toggle_task_complete(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudyPlanTaskResponse:
    """Toggle is_completed for a study plan task."""
    try:
        return await StudyPlanService(db).toggle_complete(current_user, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/me/chat")
async def dashboard_chat(
    body: DashboardChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Dashboard chatbot with user-specific learning context (progress/history).
    """
    if not settings.OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY is missing in backend environment."}

    profile_rs = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = profile_rs.scalar_one_or_none()

    progress_rs = await db.execute(select(Progress).where(Progress.user_id == current_user.id))
    progress_rows = progress_rs.scalars().all()

    history_rs = await db.execute(
        select(History)
        .where(History.user_id == current_user.id)
        .order_by(History.completed_at.desc())
        .limit(12)
    )
    history_rows = history_rs.scalars().all()

    progress_context = [
        f"{row.subject}: {row.percentage or 0:.0f}% (band {row.band_score if row.band_score is not None else 'N/A'})"
        for row in progress_rows
    ]
    recent_context = [
        f"{h.subject or 'unknown'} | score {h.score or 0}/{h.total_questions or 0} | band {h.band_score if h.band_score is not None else 'N/A'} | mode {h.mode or 'practice'}"
        for h in history_rows[:8]
    ]

    system_prompt = (
        "You are Catbot, an IELTS dashboard coach. "
        "Your job is to answer with practical, personalized IELTS advice based on provided user context. "
        "Always be directly relevant to the user's question. "
        "If user asks a study plan question, provide concrete plan for today/this week. "
        "If user asks score improvement, explain what to focus first and why. "
        "Keep answer concise but useful (5-10 sentences). "
        "Use English unless user clearly asks for Vietnamese."
    )

    context_prompt = (
        f"User profile: target_band={profile.target_band if profile else 'N/A'}, "
        f"streak={profile.streak if profile else 0}, xp={profile.xp if profile else 0}, "
        f"exam_date={profile.exam_date.isoformat() if profile and profile.exam_date else 'N/A'}\n"
        f"Progress: {', '.join(progress_context) if progress_context else 'No progress rows'}\n"
        f"Recent attempts: {'; '.join(recent_context) if recent_context else 'No recent attempts'}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": context_prompt},
    ]
    for m in body.history[-8:]:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": body.user_message})

    payload = {
        "model": _OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 700,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "LinguaIELTS Dashboard Coach",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
            resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"]
        return {"reply": reply}
    except Exception as exc:
        return {"error": f"Dashboard coach unavailable: {exc}"}
