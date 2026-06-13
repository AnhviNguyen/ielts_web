"""
app/schemas.py — LinguaIELTS
Pydantic schemas cập nhật cho IELTS platform.
"""

from datetime import datetime, date, time
from typing import Any, Literal, Optional
from pydantic import BaseModel, EmailStr, Field


# ═══ Auth ════════════════════════════════════
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


# ═══ Profile ═════════════════════════════════
class UserStatsResponse(BaseModel):
    """Dữ liệu topbar: streak, XP, band scores per skill."""
    streak: int
    xp:     int
    band_scores: dict[str, Optional[float]]  # {"Reading": 7.0, "Listening": 6.5, ...}
    days_to_exam: Optional[int]


class AuthRefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class AuthLogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class RegisterResponse(BaseModel):
    """Returned after email registration — directs user to verify inbox."""
    needs_verification: bool = True
    email: str
    message: str = "Mã xác minh đã được gửi đến email của bạn."


class GoogleAuthRequest(BaseModel):
    """Frontend sends the authorization code received from Google."""
    code: str
    redirect_uri: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)


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
    placement_status: str = "pending"
    initial_band_source: Optional[str] = None
    initial_reading_band: Optional[float] = None
    initial_listening_band: Optional[float] = None
    initial_writing_band: Optional[float] = None
    initial_speaking_band: Optional[float] = None
    initial_overall_band: Optional[float] = None
    placement_completed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class UserMeUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    target_band: Optional[float] = None
    exam_date: Optional[date] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class WritingSubmitRequest(BaseModel):
    topic_id: int
    task_type: int = Field(ge=1, le=2)
    essay_text: str = Field(min_length=10, max_length=50_000)
    word_count: int = Field(ge=0)
    duration_seconds: int = Field(default=0, ge=0)
    prompt_text: Optional[str] = None


class BadgeItem(BaseModel):
    id: str
    title: str
    description: str
    hint: str = ""
    icon: str
    unlocked: bool


class BadgesResponse(BaseModel):
    items: list[BadgeItem]
    unlocked_count: int
    total_count: int


class WritingSubmitResponse(BaseModel):
    history_id: int
    band_score: float
    xp_earned: int
    evaluation: dict
    message: str
    new_badges: list[BadgeItem] = Field(default_factory=list)


class PracticeSessionResponse(BaseModel):
    session_id: int
    subject: str
    quiz: dict[str, Any]


class PracticeSubmitRequest(BaseModel):
    session_id: int
    answers: dict[str, Any] = Field(default_factory=dict)
    duration_seconds: int = Field(default=0, ge=0)


class PracticeSubmitResponse(BaseModel):
    session_id: int
    subject: str
    quiz_id: str | None
    score: int
    total_questions: int
    percentage: float
    estimated_band: float
    details: list[dict[str, Any]]
    new_badges: list[BadgeItem] = Field(default_factory=list)


class PracticeCheckAnswerRequest(BaseModel):
    session_id: int = Field(gt=0)
    question_id: int | str
    user_answer: Any = None


class PracticeCheckAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str | None = None
    correct_answers: list[str] = Field(default_factory=list)
    explain: str = ""
    listen_from: str | None = None
    user_answer: Any = None


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
    suggested_difficulty: Optional[str] = None
    priority_score: float = 0.0
    created_at: datetime
    model_config = {"from_attributes": True}


class StudyPlanNextTaskResponse(BaseModel):
    source: str
    task: Optional[StudyPlanTaskResponse] = None
    focus_skill: str
    suggested_difficulty: str
    difficulty_label: str
    reason: str
    route_path: str
    synthetic_description: Optional[str] = None
    duration_minutes: Optional[int] = None


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


class VocabComprehensionOption(BaseModel):
    id: str
    text: str


class VocabComprehensionQuestion(BaseModel):
    id: str
    stem: str
    options: list[VocabComprehensionOption]
    correct_id: str


class VocabReadingPassageResponse(BaseModel):
    paragraphs: list[VocabReadingParagraph]
    answers: dict[str, str]
    source: str = "ai"
    word_ids: list[int] = []
    comprehension_questions: list[VocabComprehensionQuestion] = []


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
    new_badges: list[BadgeItem] = Field(default_factory=list)


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
    period: str = "all"  # all | weekly | monthly


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


class AdminUserRoleUpdate(BaseModel):
    role: Literal["admin", "user"]


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: Optional[str] = None
    role: Literal["admin", "user"] = "user"
    is_verified: bool = True


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


class AdminSubjectStats(BaseModel):
    subject: str
    attempts: int
    average_band: float


class AdminContentCounts(BaseModel):
    system_vocab_topics: int = 0
    conversation_topics: int = 0
    translation_steps: int = 0
    translation_topics: int = 0


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
    total_attempts: int = 0
    overall_average_band: float = 0.0
    new_users_last_7_days: list[AdminDailyAttempts] = Field(default_factory=list)
    attempts_by_subject: list[AdminSubjectStats] = Field(default_factory=list)
    activity_heatmap: list[AdminDailyAttempts] = Field(default_factory=list)
    content_counts: AdminContentCounts = Field(default_factory=AdminContentCounts)


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


class AdminConversationTopicCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    level: str = Field(min_length=1, max_length=20)
    icon_emoji: Optional[str] = Field(default="💬", max_length=10)
    ai_role: str = Field(min_length=1, max_length=300)
    user_role: str = Field(min_length=1, max_length=300)
    scenario: str = Field(min_length=1)
    opening_line: str = Field(min_length=1)
    vocabulary: list[str] = Field(default_factory=list)
    order: int = 0
    is_active: bool = True


class AdminConversationTopicUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    level: Optional[str] = Field(default=None, max_length=20)
    icon_emoji: Optional[str] = Field(default=None, max_length=10)
    ai_role: Optional[str] = Field(default=None, max_length=300)
    user_role: Optional[str] = Field(default=None, max_length=300)
    scenario: Optional[str] = None
    opening_line: Optional[str] = None
    vocabulary: Optional[list[str]] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class AdminConversationTopicResponse(BaseModel):
    id: int
    order: int
    title: str
    description: str
    level: str
    icon_emoji: Optional[str] = None
    ai_role: str
    user_role: str
    scenario: str
    opening_line: str
    vocabulary: list[str] = Field(default_factory=list)
    is_active: bool
    session_count: int = 0
    created_at: datetime
    model_config = {"from_attributes": True}


class AdminTranslationStepCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    badge_label: Optional[str] = Field(default=None, max_length=30)
    badge_color: str = Field(default="gray", max_length=20)
    icon_emoji: str = Field(default="📝", max_length=10)
    order: int = 0
    is_active: bool = True


class AdminTranslationStepUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    badge_label: Optional[str] = Field(default=None, max_length=30)
    badge_color: Optional[str] = Field(default=None, max_length=20)
    icon_emoji: Optional[str] = Field(default=None, max_length=10)
    order: Optional[int] = None
    is_active: Optional[bool] = None


class AdminTranslationStepResponse(BaseModel):
    id: int
    order: int
    title: str
    description: str
    badge_label: Optional[str] = None
    badge_color: str
    icon_emoji: str
    is_active: bool
    topic_count: int = 0
    sentence_count: int = 0
    model_config = {"from_attributes": True}


class AdminTranslationTopicCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    order: int = 0
    is_active: bool = True


class AdminTranslationTopicUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class AdminTranslationTopicResponse(BaseModel):
    id: int
    step_id: int
    order: int
    title: str
    description: str
    is_active: bool
    sentence_count: int = 0
    model_config = {"from_attributes": True}


class AdminTranslationSentenceCreate(BaseModel):
    vietnamese: str = Field(min_length=1)
    english: str = Field(min_length=1)
    explanation: Optional[str] = None
    order: int = 0
    is_active: bool = True


class AdminTranslationSentenceUpdate(BaseModel):
    vietnamese: Optional[str] = None
    english: Optional[str] = None
    explanation: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class AdminTranslationSentenceResponse(BaseModel):
    id: int
    topic_id: int
    order: int
    vietnamese: str
    english: str
    explanation: Optional[str] = None
    is_active: bool
    attempt_count: int = 0
    model_config = {"from_attributes": True}


class AdminTranslationStepDetail(BaseModel):
    step: AdminTranslationStepResponse
    topics: list[AdminTranslationTopicResponse]


class AdminTranslationTopicDetail(BaseModel):
    topic: AdminTranslationTopicResponse
    sentences: list[AdminTranslationSentenceResponse]


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
    template: Optional[str] = Field(default=None, max_length=80)
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


class AdminSpeakingBuilderQuestion(BaseModel):
    title: str = Field(default="", max_length=1000)
    description: Optional[str] = None
    time_to_think: int = Field(default=0, ge=0, le=600)
    time_limit: int = Field(default=30, ge=1, le=600)
    audio_url: Optional[str] = Field(default="", max_length=2000)


class AdminSpeakingBuilderPart(BaseModel):
    title: str = Field(default="", max_length=500)
    time: int = Field(default=5, ge=1, le=60)
    instruction_html: Optional[str] = None
    questions: list[AdminSpeakingBuilderQuestion] = Field(default_factory=list)


class AdminSpeakingMockTestBuilderRequest(BaseModel):
    id: Optional[int] = None
    title: str = Field(min_length=1, max_length=500)
    book_code: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="published", max_length=50)
    time: int = Field(default=13, ge=1, le=240)
    thumbnail: Optional[str] = Field(default=None, max_length=300)
    parts: list[AdminSpeakingBuilderPart] = Field(default_factory=list)


class AdminSpeakingMockTestBuilderResponse(BaseModel):
    mock_test_id: int
    full_quiz_id: int
    part_quiz_ids: list[int]
    mock_test: dict[str, Any]
    full_quiz: dict[str, Any]
    raw_json: dict[str, Any]
    backup_paths: list[str] = Field(default_factory=list)
    builder: dict[str, Any]


class AdminListeningBuilderQuestion(BaseModel):
    text: str = Field(default="", max_length=3000)
    correct_answer: Optional[str] = Field(default=None, max_length=1000)
    correct_answers: list[str] = Field(default_factory=list)
    options: list[AdminReadingBuilderOption] = Field(default_factory=list)
    explain: Optional[str] = None
    locate_paragraph: Optional[int] = None
    listen_from: Optional[float] = None


class AdminListeningBuilderQuestionSet(BaseModel):
    title: str = Field(default="", max_length=500)
    template: Optional[str] = Field(default=None, max_length=80)
    question_type: str = Field(min_length=1, max_length=80)
    description: Optional[str] = None
    content: Optional[str] = None
    options: list[AdminReadingBuilderOption] = Field(default_factory=list)
    questions: list[AdminListeningBuilderQuestion] = Field(default_factory=list)
    max_selections: Optional[int] = None


class AdminListeningBuilderPart(BaseModel):
    title: str = Field(default="", max_length=500)
    time: int = Field(default=8, ge=1, le=60)
    file_id: Optional[str] = Field(default="", max_length=500)
    transcript_text: str = Field(default="", max_length=120000)
    listen_from: Optional[float] = None
    listen_to: Optional[float] = None
    question_sets: list[AdminListeningBuilderQuestionSet] = Field(default_factory=list)


class AdminListeningMockTestBuilderRequest(BaseModel):
    id: Optional[int] = None
    title: str = Field(min_length=1, max_length=500)
    book_code: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="published", max_length=50)
    time: int = Field(default=40, ge=1, le=240)
    thumbnail: Optional[str] = Field(default=None, max_length=300)
    parts: list[AdminListeningBuilderPart] = Field(default_factory=list)


class AdminListeningMockTestBuilderResponse(BaseModel):
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
    force_refresh: bool = Field(default=False)


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


# ═══ Notifications ════════════════════════════
class NotificationSettingsRequest(BaseModel):
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[time] = None
    channel: Optional[str] = Field(None, pattern="^(in_app|email|both)$")
    email_daily_digest: Optional[bool] = None
    push_enabled: Optional[bool] = None
    timezone: Optional[str] = Field(None, max_length=64)


class NotificationSettingsResponse(BaseModel):
    reminder_enabled: bool
    reminder_time: time
    channel: str
    email_daily_digest: bool
    push_enabled: bool
    timezone: str
    model_config = {"from_attributes": True}


class NotificationItem(BaseModel):
    id: int
    type: str
    title: str
    body: str
    link_path: Optional[str] = None
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    unread_count: int


# ═══ Score forecast ════════════════════════════
class ScoreIngestRequest(BaseModel):
    skill: str
    y: float = Field(ge=0, le=9)
    session_min: float = Field(ge=0, default=0)
    correct_rate: float = Field(ge=0, le=1, default=0.5)


class ForecastPointSchema(BaseModel):
    ds: date
    y: Optional[float] = None
    yhat: float
    yhat_lower: float
    yhat_upper: float
    is_forecast: bool = False


class ForecastResponse(BaseModel):
    user_id: int
    skill: str
    lookback_days: int
    horizon_days: int
    sample_days: int
    trainer: str
    mae: Optional[float] = None
    rmse: Optional[float] = None
    history: list[ForecastPointSchema]
    forecast: list[ForecastPointSchema]
    cold_start: bool = False


class ForecastSkillSummary(BaseModel):
    skill: str
    sample_days: int
    trainer: Optional[str] = None
    mae: Optional[float] = None
    trained_at: Optional[datetime] = None


class ForecastSkillListResponse(BaseModel):
    skills: list[ForecastSkillSummary]


class ForecastAlert(BaseModel):
    skill: str
    severity: str  # info | warning | critical
    code: str
    message: str


class ForecastAlertsResponse(BaseModel):
    alerts: list[ForecastAlert]
    target_band: float


# ═══ Next-week band prediction (RandomForest) ════
class NextWeekSkillForecast(BaseModel):
    skill: str
    current: float
    predicted: float
    delta: float
    status: str  # improving | flat | declining


class NextWeekForecastResponse(BaseModel):
    user_id: int
    enabled: bool
    cold_start: bool
    weeks_of_data: int
    target_band: float
    overall: Optional[NextWeekSkillForecast] = None
    skills: list[NextWeekSkillForecast] = []
    status: str = "flat"  # overall status: improving | flat | declining
    improving: bool = False
    message: str = ""


class PlacementBands(BaseModel):
    reading: float = Field(ge=0, le=9)
    listening: float = Field(ge=0, le=9)
    writing: float = Field(ge=0, le=9)
    speaking: float = Field(ge=0, le=9)
    overall: Optional[float] = Field(None, ge=0, le=9)


class PlacementStatusResponse(BaseModel):
    placement_status: str
    initial_band_source: Optional[str] = None
    bands: Optional[PlacementBands] = None
    placement_completed_at: Optional[datetime] = None
    active_session_id: Optional[int] = None


class PlacementManualRequest(BaseModel):
    reading: float = Field(ge=0, le=9)
    listening: float = Field(ge=0, le=9)
    writing: float = Field(ge=0, le=9)
    speaking: float = Field(ge=0, le=9)


class PlacementFullExamFinalizeRequest(PlacementManualRequest):
    set_id: Optional[str] = None
    session_id: Optional[str] = None
    results: dict[str, Any] = Field(default_factory=dict)


class PlacementSessionResponse(BaseModel):
    id: int
    status: str
    current_stage: str
    results: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    completed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class PlacementStageResponse(BaseModel):
    session: PlacementSessionResponse
    stage: str
    payload: dict[str, Any]


class PlacementStageSubmitRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)
    essay_text: Optional[str] = Field(None, max_length=50_000)
    transcript_text: Optional[str] = Field(None, max_length=20_000)
    duration_seconds: int = Field(default=0, ge=0)


class PlacementStageSubmitResponse(BaseModel):
    session: PlacementSessionResponse
    stage: str
    result: dict[str, Any]


class PlacementFinalizeResponse(BaseModel):
    placement_status: str
    bands: PlacementBands
