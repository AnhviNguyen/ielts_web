"""
app/db/models.py — LinguaIELTS
SQLAlchemy ORM models. Schema cập nhật cho nền tảng IELTS:
- UserProfile: thêm target_band, exam_date, streak, xp
- Progress: thêm band_score
- History: thêm band_score, mode, duration_seconds
"""

from datetime import datetime, date, time
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lock_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # OAuth / email verification
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(20), default="email", nullable=False)

    profile:  Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    progress: Mapped[list["Progress"]] = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    history:  Mapped[list["History"]]  = relationship("History",  back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )
    practice_sessions: Mapped[list["PracticeSession"]] = relationship(
        "PracticeSession", back_populates="user", cascade="all, delete-orphan"
    )
    study_plan_tasks: Mapped[list["StudyPlanTask"]] = relationship(
        "StudyPlanTask", back_populates="user", cascade="all, delete-orphan"
    )
    shadowing_history: Mapped[list["ShadowingUserHistory"]] = relationship(
        "ShadowingUserHistory", back_populates="user", cascade="all, delete-orphan"
    )
    email_verifications: Mapped[list["EmailVerification"]] = relationship(
        "EmailVerification", back_populates="user", cascade="all, delete-orphan"
    )
    vocab_topics: Mapped[list["VocabTopic"]] = relationship(
        "VocabTopic", back_populates="user", cascade="all, delete-orphan"
    )
    reading_annotations: Mapped[list["ReadingAnnotation"]] = relationship(
        "ReadingAnnotation", back_populates="user", cascade="all, delete-orphan"
    )
    skill_adaptive_states: Mapped[list["SkillAdaptiveState"]] = relationship(
        "SkillAdaptiveState", back_populates="user", cascade="all, delete-orphan"
    )
    notification_settings: Mapped["NotificationSettings | None"] = relationship(
        "NotificationSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    conversation_sessions: Mapped[list["ConversationSession"]] = relationship(
        "ConversationSession", back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (Index("idx_user_profiles_xp", "xp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name:   Mapped[str | None] = mapped_column(String(255))
    avatar_url:  Mapped[str | None] = mapped_column(Text)
    phone:       Mapped[str | None] = mapped_column(String(20))
    bio:         Mapped[str | None] = mapped_column(Text)
    # IELTS-specific fields
    target_band: Mapped[float | None] = mapped_column(Float, default=7.0)
    exam_date:   Mapped[date | None]  = mapped_column(Date)
    streak:      Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    streak_freeze_count: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[date | None] = mapped_column(Date)
    xp:          Mapped[int] = mapped_column(Integer, default=0)
    daily_writing_used: Mapped[int] = mapped_column(Integer, default=0)
    daily_speaking_used: Mapped[int] = mapped_column(Integer, default=0)
    tutor_questions_used_month: Mapped[int] = mapped_column(Integer, default=0)
    is_leaderboard_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    leaderboard_flag_reason: Mapped[str | None] = mapped_column(Text)
    leaderboard_hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="profile")


class Progress(Base):
    """Tracks completion progress per user per IELTS skill."""
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "subject", name="uq_user_subject"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id:             Mapped[int]         = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject:             Mapped[str]         = mapped_column(String(100), nullable=False)  # Reading, Listening, etc.
    total_questions:     Mapped[int]         = mapped_column(Integer, default=0)
    completed_questions: Mapped[int]         = mapped_column(Integer, default=0)
    percentage:          Mapped[float]       = mapped_column(Float, default=0.0)
    band_score:          Mapped[float | None] = mapped_column(Float)  # IELTS band score 0–9
    updated_at:          Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="progress")


class History(Base):
    """Records each IELTS practice/exam attempt."""
    __tablename__ = "history"
    __table_args__ = (
        Index("idx_history_user_date", "user_id", "completed_at"),
        Index("idx_history_user_subject", "user_id", "subject"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id:          Mapped[int]        = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id:          Mapped[str | None] = mapped_column(String(100))
    practice_session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("practice_sessions.id", ondelete="SET NULL"), index=True
    )
    subject:          Mapped[str | None] = mapped_column(String(100))   # IELTS skill
    score:            Mapped[int | None] = mapped_column(Integer)
    total_questions:  Mapped[int | None] = mapped_column(Integer)
    percentage:       Mapped[float | None] = mapped_column(Float)
    band_score:       Mapped[float | None] = mapped_column(Float)        # Band score 0–9
    mode:             Mapped[str | None] = mapped_column(String(20))     # 'practice' | 'exam'
    duration_seconds: Mapped[int | None] = mapped_column(Integer)        # Time taken
    answers:          Mapped[Any | None] = mapped_column(JSON)
    completed_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="history")


class HistoryArchive(Base):
    """Cold storage for practice history older than HISTORY_ARCHIVE_AFTER_DAYS."""
    __tablename__ = "history_archive"
    __table_args__ = (
        Index("idx_history_archive_user_date", "user_id", "completed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quiz_id: Mapped[str | None] = mapped_column(String(100))
    practice_session_id: Mapped[int | None] = mapped_column(Integer)
    subject: Mapped[str | None] = mapped_column(String(100))
    score: Mapped[int | None] = mapped_column(Integer)
    total_questions: Mapped[int | None] = mapped_column(Integer)
    percentage: Mapped[float | None] = mapped_column(Float)
    band_score: Mapped[float | None] = mapped_column(Float)
    mode: Mapped[str | None] = mapped_column(String(20))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    answers: Mapped[Any | None] = mapped_column(JSON)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    __table_args__ = (Index("idx_practice_sessions_user", "user_id", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)  # reading/listening/writing/speaking
    quiz_id: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="started")  # started/submitted
    score: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="practice_sessions")


class VocabTopic(Base):
    """User-created vocabulary topic/set."""
    __tablename__ = "vocab_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="vocab_topics")
    words: Mapped[list["VocabWord"]] = relationship("VocabWord", back_populates="topic", cascade="all, delete-orphan")


class VocabWord(Base):
    """A saved vocabulary word inside a user topic."""
    __tablename__ = "vocab_words"
    __table_args__ = (
        Index("idx_vocab_words_topic_srs", "topic_id", "srs_next_review_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("vocab_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    word: Mapped[str] = mapped_column(String(200), nullable=False)
    phonetic: Mapped[str | None] = mapped_column(String(200))
    word_type: Mapped[str | None] = mapped_column(String(100))        # noun, verb, adjective…
    meaning_en: Mapped[str | None] = mapped_column(Text)               # English definition(s)
    meaning_vi: Mapped[str | None] = mapped_column(Text)               # Vietnamese meaning
    example: Mapped[str | None] = mapped_column(Text)                  # example sentence
    example_vi: Mapped[str | None] = mapped_column(Text)               # Vietnamese example
    note: Mapped[str | None] = mapped_column(Text)                     # user personal note
    mastery: Mapped[str] = mapped_column(String(20), default="new")    # new / learning / mastered
    # Spaced repetition (SM-2)
    srs_ease: Mapped[float] = mapped_column(Float, default=2.5)
    srs_interval_days: Mapped[int] = mapped_column(Integer, default=0)
    srs_repetitions: Mapped[int] = mapped_column(Integer, default=0)
    srs_next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    srs_last_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Provenance — where the word was saved from
    source_quiz_id: Mapped[str | None] = mapped_column(String(100))    # quiz_id it was saved from
    source_type: Mapped[str | None] = mapped_column(String(20))        # 'reading' | 'listening' | 'manual'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    topic: Mapped["VocabTopic"] = relationship("VocabTopic", back_populates="words")


class SystemVocabTopic(Base):
    """Admin-managed vocabulary topic template."""
    __tablename__ = "system_vocab_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    level: Mapped[str | None] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    words: Mapped[list["SystemVocabWord"]] = relationship(
        "SystemVocabWord",
        back_populates="topic",
        cascade="all, delete-orphan",
    )


class SystemVocabWord(Base):
    """Admin-managed vocabulary word template."""
    __tablename__ = "system_vocab_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("system_vocab_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    word: Mapped[str] = mapped_column(String(200), nullable=False)
    phonetic: Mapped[str | None] = mapped_column(String(200))
    word_type: Mapped[str | None] = mapped_column(String(100))
    meaning_en: Mapped[str | None] = mapped_column(Text)
    meaning_vi: Mapped[str | None] = mapped_column(Text)
    example: Mapped[str | None] = mapped_column(Text)
    example_vi: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[Any | None] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    topic: Mapped["SystemVocabTopic"] = relationship("SystemVocabTopic", back_populates="words")


class ReadingAnnotation(Base):
    """Stores per-session reading highlights and notes for a user."""
    __tablename__ = "reading_annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # local session UUID
    quiz_id: Mapped[str | None] = mapped_column(String(100), index=True)
    highlights: Mapped[Any | None] = mapped_column(JSON)    # [{id, text, color, paragraphIdx, charStart, charEnd}]
    note: Mapped[str | None] = mapped_column(Text)          # free-form note
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="reading_annotations")


class ShadowingVideo(Base):
    """Cached YouTube transcript for shadowing / dictation practice."""
    __tablename__ = "shadowing_videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    video_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    level: Mapped[str] = mapped_column(String(50), default="Intermediate")
    language: Mapped[str] = mapped_column(String(10), default="en")
    source_url: Mapped[str] = mapped_column(Text, default="")
    transcript_source: Mapped[str] = mapped_column(String(20), default="youtube")  # youtube | whisper
    segments: Mapped[Any] = mapped_column(JSON, default=list)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ShadowingUserHistory(Base):
    """Per-user shadowing watch history (last opened video)."""
    __tablename__ = "shadowing_user_history"
    __table_args__ = (UniqueConstraint("user_id", "video_id", name="uq_shadowing_user_video"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    display_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="shadowing_history")


class StudyPlanTask(Base):
    """A single to-do task inside a user's AI-generated study plan."""
    __tablename__ = "study_plan_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)          # 1-based day index
    plan_date: Mapped[date | None] = mapped_column(Date)                      # actual calendar date
    focus_skill: Mapped[str] = mapped_column(String(50), nullable=False)      # reading/listening/writing/speaking
    task_description: Mapped[str] = mapped_column(Text, nullable=False)       # what to do
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45)
    quiz_id: Mapped[str | None] = mapped_column(String(100))                  # optional link to a quiz
    route_path: Mapped[str | None] = mapped_column(String(200))               # frontend route e.g. /reading
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suggested_difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="study_plan_tasks")


class SkillAdaptiveState(Base):
    """Per-skill SRS-like state for adaptive study plan recommendations."""
    __tablename__ = "skill_adaptive_states"
    __table_args__ = (UniqueConstraint("user_id", "skill", name="uq_user_skill_adaptive"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill: Mapped[str] = mapped_column(String(30), nullable=False)
    srs_ease: Mapped[float] = mapped_column(Float, default=2.5)
    srs_interval_days: Mapped[int] = mapped_column(Integer, default=1)
    srs_repetitions: Mapped[int] = mapped_column(Integer, default=0)
    srs_next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    srs_last_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suggested_difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    avg_performance: Mapped[float] = mapped_column(Float, default=0.0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="skill_adaptive_states")


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_time: Mapped[time] = mapped_column(Time, default=time(9, 0))
    channel: Mapped[str] = mapped_column(String(20), default="in_app")
    email_daily_digest: Mapped[bool] = mapped_column(Boolean, default=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Ho_Chi_Minh")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notification_settings")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("idx_notifications_user_read", "user_id", "is_read", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    link_path: Mapped[str | None] = mapped_column(String(200))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")


# ── Translation Practice ──────────────────────────────────────────────────────

class TranslationStep(Base):
    """Learning step (Bước 1 – Cấu trúc cơ bản, etc.)"""
    __tablename__ = "translation_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    badge_label: Mapped[str | None] = mapped_column(String(30))
    badge_color: Mapped[str] = mapped_column(String(20), default="gray")
    icon_emoji: Mapped[str] = mapped_column(String(10), default="📝")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    topics: Mapped[list["TranslationTopic"]] = relationship(
        "TranslationTopic", back_populates="step", cascade="all, delete-orphan",
        order_by="TranslationTopic.order",
    )


class TranslationTopic(Base):
    """A sub-topic within a step (e.g., 'Simple Present')"""
    __tablename__ = "translation_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    step_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("translation_steps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    step: Mapped["TranslationStep"] = relationship("TranslationStep", back_populates="topics")
    sentences: Mapped[list["TranslationSentence"]] = relationship(
        "TranslationSentence", back_populates="topic", cascade="all, delete-orphan",
        order_by="TranslationSentence.order",
    )


class TranslationSentence(Base):
    """One Vietnamese sentence with its English model answer."""
    __tablename__ = "translation_sentences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("translation_topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vietnamese: Mapped[str] = mapped_column(Text, nullable=False)
    english: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    topic: Mapped["TranslationTopic"] = relationship("TranslationTopic", back_populates="sentences")
    attempts: Mapped[list["TranslationAttempt"]] = relationship(
        "TranslationAttempt", back_populates="sentence", cascade="all, delete-orphan"
    )


class TranslationAttempt(Base):
    """User's translation attempt with AI-graded score/feedback."""
    __tablename__ = "translation_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sentence_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("translation_sentences.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_translation: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float | None] = mapped_column(nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text)
    model_answer: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sentence: Mapped["TranslationSentence"] = relationship("TranslationSentence", back_populates="attempts")


# ── Email Verification ─────────────────────────────────────────────────────────

class EmailVerification(Base):
    """One-time 6-digit OTP for verifying a user's email address."""
    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="email_verifications")


# ── Conversation Practice ─────────────────────────────────────────────────────

class ConversationTopic(Base):
    """Role-play scenario for AI conversation practice."""
    __tablename__ = "conversation_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="beginner")
    icon_emoji: Mapped[str] = mapped_column(String(10), default="💬")
    ai_role: Mapped[str] = mapped_column(String(300), nullable=False)
    user_role: Mapped[str] = mapped_column(String(300), nullable=False)
    scenario: Mapped[str] = mapped_column(Text, nullable=False)
    opening_line: Mapped[str] = mapped_column(Text, nullable=False)
    vocabulary: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sessions: Mapped[list["ConversationSession"]] = relationship(
        "ConversationSession", back_populates="topic", cascade="all, delete-orphan"
    )


class ConversationSession(Base):
    """One user's role-play session with message history and feedback."""
    __tablename__ = "conversation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversation_topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    history: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="conversation_sessions")
    topic: Mapped["ConversationTopic"] = relationship("ConversationTopic", back_populates="sessions")
