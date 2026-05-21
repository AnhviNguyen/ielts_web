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

class HistoryListItem(BaseModel):
    """History row enriched for UI (title from quiz JSON when available)."""
    id: int
    user_id: int
    quiz_id: Optional[str] = None
    session_id: Optional[int] = None
    subject: Optional[str] = None
    skill: Optional[str] = None
    title: str = "Bài luyện IELTS"
    score: Optional[int] = None
    total_questions: Optional[int] = None
    percentage: Optional[float] = None
    band_score: Optional[float] = None
    mode: Optional[str] = None
    duration_seconds: Optional[int] = None
    completed_at: datetime
    model_config = {"from_attributes": True}


class PaginatedHistory(BaseModel):
    items:       list[HistoryListItem]
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


# ═══ Study Plan ═══════════════════════════════
class StudyPlanTaskResponse(BaseModel):
    id: int
    user_id: int
    day_number: int
    plan_date: Optional[date]
    focus_skill: str
    task_description: str
    duration_minutes: int
    quiz_id: Optional[str]
    route_path: Optional[str]
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class StudyPlanDayGroup(BaseModel):
    day_number: int
    plan_date: Optional[date]
    tasks: list[StudyPlanTaskResponse]


class StudyPlanResponse(BaseModel):
    days: list[StudyPlanDayGroup]
    total_tasks: int
    completed_tasks: int


# ═══ Skill Radar ══════════════════════════════
class SkillRadarResponse(BaseModel):
    reading: float
    listening: float
    writing: float
    speaking: float
    attempts: dict[str, int]  # number of first-attempt quizzes per skill


# ═══ Vocabulary ════════════════════════════════
class VocabWordCreate(BaseModel):
    word: str
    phonetic: Optional[str] = None
    word_type: Optional[str] = None
    meaning_en: Optional[str] = None
    meaning_vi: Optional[str] = None
    example: Optional[str] = None
    example_vi: Optional[str] = None
    note: Optional[str] = None
    # Provenance — where word was saved from
    source_quiz_id: Optional[str] = None   # quiz_id if saved from reading/listening
    source_type: Optional[str] = None      # 'reading' | 'listening' | 'manual'

class VocabWordUpdate(BaseModel):
    word: Optional[str] = None
    phonetic: Optional[str] = None
    word_type: Optional[str] = None
    meaning_en: Optional[str] = None
    meaning_vi: Optional[str] = None
    example: Optional[str] = None
    example_vi: Optional[str] = None
    note: Optional[str] = None
    mastery: Optional[str] = None

class VocabWordResponse(BaseModel):
    id: int
    topic_id: int
    word: str
    phonetic: Optional[str] = None
    word_type: Optional[str] = None
    meaning_en: Optional[str] = None
    meaning_vi: Optional[str] = None
    example: Optional[str] = None
    example_vi: Optional[str] = None
    note: Optional[str] = None
    mastery: str
    source_quiz_id: Optional[str] = None
    source_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    srs_ease: float = 2.5
    srs_interval_days: int = 0
    srs_repetitions: int = 0
    srs_next_review_at: Optional[datetime] = None
    srs_last_review_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class VocabReviewRequest(BaseModel):
    quality: int = Field(ge=0, le=5, description="SM-2 quality 0–5")


class VocabTopicCreate(BaseModel):
    name: str

class VocabTopicUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None

class VocabTopicResponse(BaseModel):
    id: int
    user_id: int
    name: str
    sort_order: int
    created_at: datetime
    word_count: int = 0
    model_config = {"from_attributes": True}


class VocabStudyQueueResponse(BaseModel):
    topic: VocabTopicResponse
    due_count: int
    words: list[VocabWordResponse]


class VocabStatsResponse(BaseModel):
    total: int = 0
    new: int = 0
    learning: int = 0
    mastered: int = 0


class VocabStudyModeInfo(BaseModel):
    id: str
    label: str
    description: str


class VocabStudyModesResponse(BaseModel):
    modes: list[VocabStudyModeInfo]


class VocabReadingPassageRequest(BaseModel):
    word_ids: list[int] = Field(min_length=1, max_length=8)


class VocabReadingGapPart(BaseModel):
    type: str  # text | gap
    content: Optional[str] = None
    id: Optional[str] = None
    hint_vi: Optional[str] = None


class VocabReadingParagraph(BaseModel):
    parts: list[VocabReadingGapPart]


class VocabReadingPassageResponse(BaseModel):
    paragraphs: list[VocabReadingParagraph]
    answers: dict[str, str]
    source: str = "ai"
    word_ids: list[int] = []


class VocabTopicDetailResponse(BaseModel):
    """Topic metadata + all words for study session."""
    topic: VocabTopicResponse
    words: list[VocabWordResponse]


class VocabBootstrapResponse(BaseModel):
    created: bool
    topics_created: int
    words_created: int
    message: str


class VocabSessionCompleteRequest(BaseModel):
    topic_id: int
    duration_seconds: int = Field(ge=0, default=0)
    words_reviewed: int = Field(ge=0, default=0)


class VocabSessionCompleteResponse(BaseModel):
    xp_earned: int
    total_xp: int
    words_reviewed: int
    duration_seconds: int


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    avatar_url: Optional[str] = None
    xp: int = 0
    streak: int = 0
    longest_streak: int = 0
    is_current_user: bool = False


class LeaderboardResponse(BaseModel):
    top: list[LeaderboardEntry]
    current_user_rank: Optional[int] = None
    current_user: Optional[LeaderboardEntry] = None


# ═══ Reading Annotations ═══════════════════════
class AnnotationSave(BaseModel):
    session_id: str
    quiz_id: Optional[str] = None
    highlights: Optional[Any] = None
    note: Optional[str] = None

class AnnotationResponse(BaseModel):
    id: int
    session_id: str
    quiz_id: Optional[str]
    highlights: Optional[Any]
    note: Optional[str]
    updated_at: datetime
    model_config = {"from_attributes": True}


# ═══ Shadowing ═════════════════════════════════
class ShadowingSegmentOut(BaseModel):
    id: int
    text: str
    start: float
    duration: float
    translation: Optional[str] = None
    language: Optional[str] = None
    flagged: bool = False


class ShadowingVideoDataOut(BaseModel):
    video_id: str
    title: str
    level: str
    language: str
    segments: list[ShadowingSegmentOut]
    transcript_source: Optional[str] = None
    source_url: Optional[str] = None


class ShadowingProcessVideoRequest(BaseModel):
    url: str = Field(..., min_length=8)
    level: str = Field(default="Intermediate", max_length=50)
    translate: bool = Field(default=True)


class ShadowingTranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    from_lang: str = Field(default="en", max_length=10)
    to_lang: str = Field(default="vi", max_length=10)


class ShadowingTranslateResponse(BaseModel):
    translation: str


class ShadowingHistoryItemOut(BaseModel):
    video_id: str
    title: str
    level: str
    language: str
    segment_count: int = 0
    transcript_source: Optional[str] = None
    source_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    last_viewed_at: datetime


class ShadowingHistoryListOut(BaseModel):
    items: list[ShadowingHistoryItemOut]


class ShadowingHistoryUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    level: Optional[str] = Field(None, max_length=50)
