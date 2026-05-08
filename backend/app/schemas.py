"""
app/schemas.py — LinguaIELTS
Pydantic schemas cập nhật cho IELTS platform.
"""

from datetime import datetime, date
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field


# ═══ Auth ════════════════════════════════════
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


# ═══ Profile ═════════════════════════════════
class ProfileUpdate(BaseModel):
    full_name:   Optional[str]   = None
    phone:       Optional[str]   = None
    bio:         Optional[str]   = None
    avatar_url:  Optional[str]   = None
    target_band: Optional[float] = None
    exam_date:   Optional[date]  = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name:   Optional[str]
    avatar_url:  Optional[str]
    phone:       Optional[str]
    bio:         Optional[str]
    target_band: Optional[float]
    exam_date:   Optional[date]
    streak:      int
    xp:          int
    updated_at:  datetime
    # Flattened user fields
    email:       str
    created_at:  datetime
    model_config = {"from_attributes": True}

class UserStatsResponse(BaseModel):
    """Dữ liệu topbar: streak, XP, band scores per skill."""
    streak: int
    xp:     int
    band_scores: dict[str, Optional[float]]  # {"Reading": 7.0, "Listening": 6.5, ...}
    days_to_exam: Optional[int]


class AuthRefreshRequest(BaseModel):
    refresh_token: str


class AuthLogoutRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)


# ═══ Progress ════════════════════════════════
class ProgressResponse(BaseModel):
    id: int
    user_id:             int
    subject:             str
    total_questions:     int
    completed_questions: int
    percentage:          float
    band_score:          Optional[float]
    updated_at:          datetime
    model_config = {"from_attributes": True}

class ProgressUpdateRequest(BaseModel):
    subject:             str
    total_questions:     int
    completed_questions: int
    band_score:          Optional[float] = None


# ═══ History ═════════════════════════════════
class HistorySave(BaseModel):
    quiz_id:          str
    subject:          str            # IELTS skill
    score:            int
    total_questions:  int
    percentage:       float
    band_score:       Optional[float] = None
    mode:             str = "practice"  # practice | exam
    duration_seconds: Optional[int]  = None
    answers:          Optional[Any]  = None

class HistoryResponse(BaseModel):
    id: int
    user_id:          int
    quiz_id:          Optional[str]
    subject:          Optional[str]
    score:            Optional[int]
    total_questions:  Optional[int]
    percentage:       Optional[float]
    band_score:       Optional[float]
    mode:             Optional[str]
    duration_seconds: Optional[int]
    answers:          Optional[Any]
    completed_at:     datetime
    model_config = {"from_attributes": True}

class PaginatedHistory(BaseModel):
    items:       list[HistoryResponse]
    total:       int
    page:        int
    page_size:   int
    total_pages: int


# ═══ Generic ═════════════════════════════════
class MessageResponse(BaseModel):
    message: str


class UserMeResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    full_name: Optional[str]
    avatar_url: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    target_band: Optional[float]
    exam_date: Optional[date]
    streak: int
    longest_streak: int
    streak_freeze_count: int
    last_activity_date: Optional[date]
    xp: int
    daily_writing_used: int
    daily_speaking_used: int
    tutor_questions_used_month: int
    model_config = {"from_attributes": True}


class UserMeUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    target_band: Optional[float] = None
    exam_date: Optional[date] = None


class PracticeSessionResponse(BaseModel):
    session_id: int
    subject: str
    quiz: dict[str, Any]


class PracticeSubmitRequest(BaseModel):
    session_id: int
    answers: dict[str, Any] = Field(default_factory=dict)


class PracticeSubmitResponse(BaseModel):
    session_id: int
    subject: str
    quiz_id: str | None
    score: int
    total_questions: int
    percentage: float
    estimated_band: float
    details: list[dict[str, Any]]
