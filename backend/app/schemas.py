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
    role: str = "user"
    is_active: bool = True
    locked_at: Optional[datetime] = None
    lock_reason: Optional[str] = None
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


# ═══ Admin ═════════════════════════════════════════════════════════════════════
class AdminUserListItem(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    created_at: datetime
    role: str
    is_active: bool
    locked_at: Optional[datetime] = None
    lock_reason: Optional[str] = None
    xp: int = 0
    streak: int = 0
    longest_streak: int = 0
    target_band: Optional[float] = None
    is_leaderboard_hidden: bool = False
    leaderboard_flag_reason: Optional[str] = None
    leaderboard_hidden_at: Optional[datetime] = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminHistoryItem(BaseModel):
    id: int
    quiz_id: Optional[str] = None
    subject: Optional[str] = None
    score: Optional[int] = None
    total_questions: Optional[int] = None
    percentage: Optional[float] = None
    band_score: Optional[float] = None
    mode: Optional[str] = None
    completed_at: datetime


class AdminPracticeSummary(BaseModel):
    total: int = 0
    started: int = 0
    submitted: int = 0


class AdminUserDetail(AdminUserListItem):
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    exam_date: Optional[date] = None
    last_activity_date: Optional[date] = None
    progress: list[ProgressResponse] = Field(default_factory=list)
    recent_history: list[AdminHistoryItem] = Field(default_factory=list)
    practice_summary: AdminPracticeSummary = Field(default_factory=AdminPracticeSummary)
    vocab_topic_count: int = 0
    vocab_word_count: int = 0
    shadowing_video_count: int = 0


class AdminUserStatusUpdate(BaseModel):
    is_active: bool
    lock_reason: Optional[str] = None


class AdminResetXpStreakRequest(BaseModel):
    reset_xp: bool = True
    reset_streak: bool = True


class AdminLeaderboardUpdate(BaseModel):
    is_leaderboard_hidden: bool
    reason: Optional[str] = None


class AdminSkillAverage(BaseModel):
    subject: str
    average_band: float
    attempts: int


class AdminBandBucket(BaseModel):
    label: str
    count: int


class AdminStreakBucket(BaseModel):
    label: str
    count: int


class AdminDailyAttempts(BaseModel):
    date: date
    attempts: int


class AdminDailyActiveUsers(BaseModel):
    date: date
    active_users: int


class AdminRetentionBucket(BaseModel):
    label: str
    total_users: int
    active_today: int
    active_last_7_days: int
    retention_rate: float = 0.0


class AdminAnomalyItem(AdminUserListItem):
    attempts_24h: int = 0
    max_band_jump: float = 0.0
    reasons: list[str] = []


class AdminOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    locked_users: int
    attempts_today: int
    attempts_last_7_days: list[AdminDailyAttempts]
    dau_today: int = 0
    dau_last_7_days: list[AdminDailyActiveUsers] = Field(default_factory=list)
    average_band_by_skill: list[AdminSkillAverage]
    band_distribution: list[AdminBandBucket]
    streak_buckets: list[AdminStreakBucket]
    retention_by_streak: list[AdminRetentionBucket] = Field(default_factory=list)
    top_suspicious_users: list[AdminAnomalyItem]


class AdminLeaderboardResponse(BaseModel):
    items: list[AdminAnomalyItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminSystemVocabTopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    level: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class AdminSystemVocabTopicUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    level: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class AdminSystemVocabTopicResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    level: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    word_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class AdminSystemVocabWordCreate(BaseModel):
    word: str = Field(min_length=1, max_length=200)
    phonetic: Optional[str] = None
    word_type: Optional[str] = None
    meaning_en: Optional[str] = None
    meaning_vi: Optional[str] = None
    example: Optional[str] = None
    example_vi: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    sort_order: int = 0


class AdminSystemVocabWordUpdate(BaseModel):
    word: Optional[str] = Field(default=None, max_length=200)
    phonetic: Optional[str] = None
    word_type: Optional[str] = None
    meaning_en: Optional[str] = None
    meaning_vi: Optional[str] = None
    example: Optional[str] = None
    example_vi: Optional[str] = None
    tags: Optional[list[str]] = None
    sort_order: Optional[int] = None


class AdminSystemVocabWordResponse(BaseModel):
    id: int
    topic_id: int
    word: str
    phonetic: Optional[str] = None
    word_type: Optional[str] = None
    meaning_en: Optional[str] = None
    meaning_vi: Optional[str] = None
    example: Optional[str] = None
    example_vi: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    sort_order: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class AdminSystemVocabTopicDetail(BaseModel):
    topic: AdminSystemVocabTopicResponse
    words: list[AdminSystemVocabWordResponse]


class AdminSystemVocabCopyRequest(BaseModel):
    user_id: int
    target_topic_id: Optional[int] = None
    target_topic_name: Optional[str] = None
    word_ids: list[int] = Field(default_factory=list)


class AdminSystemVocabCopyResponse(BaseModel):
    target_topic_id: int
    target_topic_name: str
    copied: int
    skipped_duplicates: int


class AdminContentListResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int


class AdminContentRawRequest(BaseModel):
    raw_json: dict[str, Any]


class AdminContentResponse(BaseModel):
    item: dict[str, Any]
    raw_json: dict[str, Any]


class AdminContentWriteResponse(BaseModel):
    item: dict[str, Any]
    raw_json: dict[str, Any]
    backup_path: Optional[str] = None


class AdminImageUploadResponse(BaseModel):
    id: str
    url: str


class AdminReadingBuilderOption(BaseModel):
    option: str = Field(min_length=1, max_length=20)
    text: str = Field(default="", max_length=1000)


class AdminReadingBuilderQuestion(BaseModel):
    text: str = Field(default="", max_length=3000)
    correct_answer: Optional[str] = Field(default=None, max_length=1000)
    correct_answers: list[str] = Field(default_factory=list)
    options: list[AdminReadingBuilderOption] = Field(default_factory=list)
    explain: Optional[str] = None
    locate_paragraph: Optional[int] = None


class AdminReadingBuilderQuestionSet(BaseModel):
    title: str = Field(default="", max_length=500)
    question_type: str = Field(min_length=1, max_length=80)
    description: Optional[str] = None
    content: Optional[str] = None
    options: list[AdminReadingBuilderOption] = Field(default_factory=list)
    questions: list[AdminReadingBuilderQuestion] = Field(default_factory=list)
    max_selections: Optional[int] = None


class AdminReadingBuilderPassage(BaseModel):
    title: str = Field(default="", max_length=500)
    passage_text: str = Field(default="", max_length=60000)
    question_sets: list[AdminReadingBuilderQuestionSet] = Field(default_factory=list)


class AdminReadingMockTestBuilderRequest(BaseModel):
    id: Optional[int] = None
    title: str = Field(min_length=1, max_length=500)
    book_code: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="published", max_length=50)
    time: int = Field(default=60, ge=1, le=240)
    thumbnail: Optional[str] = Field(default=None, max_length=300)
    passages: list[AdminReadingBuilderPassage] = Field(default_factory=list)


class AdminReadingMockTestBuilderResponse(BaseModel):
    mock_test_id: int
    full_quiz_id: int
    part_quiz_ids: list[int]
    mock_test: dict[str, Any]
    full_quiz: dict[str, Any]
    raw_json: dict[str, Any]
    backup_paths: list[str] = Field(default_factory=list)
    builder: dict[str, Any]


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
