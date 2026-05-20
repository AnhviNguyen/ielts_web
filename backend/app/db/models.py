"""
app/db/models.py — LinguaIELTS
SQLAlchemy ORM models. Schema cập nhật cho nền tảng IELTS:
- UserProfile: thêm target_band, exam_date, streak, xp
- Progress: thêm band_score
- History: thêm band_score, mode, duration_seconds
"""

from datetime import datetime, date
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile:  Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    progress: Mapped[list["Progress"]] = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    history:  Mapped[list["History"]]  = relationship("History",  back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    practice_sessions: Mapped[list["PracticeSession"]] = relationship(
        "PracticeSession", back_populates="user", cascade="all, delete-orphan"
    )
    study_plan_tasks: Mapped[list["StudyPlanTask"]] = relationship(
        "StudyPlanTask", back_populates="user", cascade="all, delete-orphan"
    )
    vocab_topics: Mapped[list["VocabTopic"]] = relationship(
        "VocabTopic", back_populates="user", cascade="all, delete-orphan"
    )
    reading_annotations: Mapped[list["ReadingAnnotation"]] = relationship(
        "ReadingAnnotation", back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

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


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("vocab_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    word: Mapped[str] = mapped_column(String(200), nullable=False)
    phonetic: Mapped[str | None] = mapped_column(String(200))
    word_type: Mapped[str | None] = mapped_column(String(100))        # noun, verb, adjective…
    meaning_vi: Mapped[str | None] = mapped_column(Text)               # Vietnamese meaning
    example: Mapped[str | None] = mapped_column(Text)                  # example sentence
    example_vi: Mapped[str | None] = mapped_column(Text)               # Vietnamese example
    note: Mapped[str | None] = mapped_column(Text)                     # user personal note
    mastery: Mapped[str] = mapped_column(String(20), default="new")    # new / learning / mastered
    # Provenance — where the word was saved from
    source_quiz_id: Mapped[str | None] = mapped_column(String(100))    # quiz_id it was saved from
    source_type: Mapped[str | None] = mapped_column(String(20))        # 'reading' | 'listening' | 'manual'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    topic: Mapped["VocabTopic"] = relationship("VocabTopic", back_populates="words")


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="study_plan_tasks")
