from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import History, Progress, User, UserProfile
from app.schemas import MessageResponse, UserMeResponse, UserMeUpdateRequest
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


@router.get("/me/study-plan")
async def get_study_plan() -> dict:
    return {"days": [], "message": "No study plan generated yet"}


@router.post("/me/study-plan/generate")
async def generate_study_plan() -> dict:
    return {
        "days": [
            {"day": 1, "focus": "Reading", "minutes": 45},
            {"day": 2, "focus": "Listening", "minutes": 45},
            {"day": 3, "focus": "Writing", "minutes": 60},
            {"day": 4, "focus": "Speaking", "minutes": 45},
        ],
        "message": "Study plan generated (mock)",
    }


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
