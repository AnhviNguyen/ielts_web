"""Compute user badges from profile + history (computed on read; no badges table)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ConversationSession, ConversationTopic, History, ShadowingUserHistory, StudyPlanTask, User, UserProfile
from app.schemas import BadgeItem, BadgesResponse


@dataclass
class _BadgeStats:
    total_attempts: int
    reading_count: int
    listening_count: int
    writing_count: int
    speaking_count: int
    vocab_count: int
    shadowing_count: int
    full_exam_count: int
    study_plan_done: int
    conversation_count: int
    conversation_topics: int
    conversation_max_turns: int
    conversation_advanced_count: int
    streak: int
    longest_streak: int
    xp: int
    max_band: float
    perfect_or_strong: int
    perfect_scores: int
    core_skills_used: int


# (id, title, short description, hint how to unlock, stroke icon key, checker)
def _badge_defs() -> list[tuple[str, str, str, str, str, str]]:
    return [
        ("first_step", "Bước đầu", "Hoàn thành bài luyện đầu tiên",
         "Nộp bất kỳ bài Reading, Listening, Writing, Speaking hoặc phiên từ vựng.",
         "flag", "first_step"),
        ("reading_3", "Mắt đại bàng", "3 bài Reading",
         "Hoàn thành 3 bài Reading (mock hoặc practice).",
         "book-open", "reading_3"),
        ("reading_10", "Bookworm", "10 bài Reading",
         "Hoàn thành 10 bài Reading trong lịch sử.",
         "library", "reading_10"),
        ("reading_perfect", "Điểm 10", "100% một bài Reading",
         "Đạt 100% đúng trong một bài Reading có ít nhất 10 câu.",
         "check-circle", "reading_perfect"),
        ("listening_3", "Tai thính", "3 bài Listening",
         "Hoàn thành 3 bài Listening.",
         "headphones", "listening_3"),
        ("listening_10", "Podcast pro", "10 bài Listening",
         "Hoàn thành 10 bài Listening.",
         "radio", "listening_10"),
        ("writer", "Nhà văn", "3 bài Writing",
         "Nộp 3 bài Writing đã chấm AI.",
         "pen-line", "writer"),
        ("writer_pro", "Văn sĩ", "10 bài Writing",
         "Nộp 10 bài Writing.",
         "feather", "writer_pro"),
        ("speaker", "Orator", "5 bài Speaking",
         "Hoàn thành 5 bài Speaking.",
         "mic", "speaker"),
        ("speaker_star", "MC IELTS", "15 bài Speaking",
         "Hoàn thành 15 bài Speaking.",
         "mic-2", "speaker_star"),
        ("word_hunter", "Thợ săn từ", "5 phiên từ vựng",
         "Kết thúc 5 phiên ôn từ (SRS) với ít nhất 1 từ đã ôn.",
         "bookmark", "word_hunter"),
        ("word_master", "Từ điển sống", "20 phiên từ vựng",
         "Hoàn thành 20 phiên từ vựng.",
         "book-marked", "word_master"),
        ("shadowing_3", "Shadow fan", "3 video shadowing",
         "Xem/luyện 3 video Shadowing khác nhau.",
         "play-circle", "shadowing_3"),
        ("shadowing_1", "Echo đầu tiên", "1 video shadowing",
         "Mở và luyện shadowing lần đầu tiên.",
         "repeat", "shadowing_1"),
        ("shadowing_10", "Shadow master", "10 video shadowing",
         "Luyện shadowing trên 10 video khác nhau.",
         "video", "shadowing_10"),
        ("shadowing_20", "Giọng native", "20 video shadowing",
         "Hoàn thành luyện tập trên 20 video shadowing.",
         "headphones", "shadowing_20"),
        ("conversation_1", "Xin chào!", "1 hội thoại",
         "Hoàn thành 1 buổi Conversation Practice (nhấn Kết thúc).",
         "message-circle", "conversation_1"),
        ("conversation_5", "Người bạn mới", "5 hội thoại",
         "Hoàn thành 5 buổi role-play với AI.",
         "messages", "conversation_5"),
        ("conversation_10", "Small talk pro", "10 hội thoại",
         "Hoàn thành 10 buổi Conversation Practice.",
         "message-circle", "conversation_10"),
        ("conversation_topics_3", "Đa tình huống", "3 chủ đề",
         "Kết thúc role-play ở 3 chủ đề/tình huống khác nhau.",
         "users", "conversation_topics_3"),
        ("conversation_deep", "Trò chuyện sâu", "≥5 lượt nói",
         "Trong một buổi, trả lời AI ít nhất 5 lượt rồi kết thúc.",
         "mic", "conversation_deep"),
        ("conversation_advanced", "Thượng thừa", "Chủ đề Advanced",
         "Hoàn thành 1 buổi hội thoại ở cấp Advanced.",
         "zap", "conversation_advanced"),
        ("full_mock_1", "Thi thử", "1 Full Mock",
         "Hoàn thành ít nhất 1 Full Mock Exam.",
         "clipboard-list", "full_mock_1"),
        ("plan_5", "Theo kế hoạch", "5 task study plan",
         "Đánh dấu hoàn thành 5 nhiệm vụ trong Study Plan.",
         "calendar-check", "plan_5"),
        ("streak_3", "Kiên trì 3 ngày", "Streak 3 ngày",
         "Luyện ít nhất 1 ngày liên tiếp trong 3 ngày (streak ≥ 3).",
         "flame", "streak_3"),
        ("streak_7", "Tuần lửa", "Streak 7 ngày",
         "Giữ streak 7 ngày (hoặc kỷ lục longest ≥ 7).",
         "flame", "streak_7"),
        ("streak_14", "Hai tuần vàng", "Streak 14 ngày",
         "Streak hiện tại hoặc kỷ lục ≥ 14 ngày.",
         "zap", "streak_14"),
        ("streak_30", "Bất bại", "Streak 30 ngày",
         "Đạt longest streak ≥ 30 ngày.",
         "crown", "streak_30"),
        ("xp_50", "Khởi động", "50 XP",
         "Tích lũy 50 XP (10 phút luyện ≈ 1 XP).",
         "sparkles", "xp_50"),
        ("xp_100", "Tích lũy", "100 XP",
         "Đạt 100 XP trên hồ sơ.",
         "star", "xp_100"),
        ("xp_500", "Cao thủ", "500 XP",
         "Đạt 500 XP.",
         "sparkle", "xp_500"),
        ("xp_1000", "Huyền thoại", "1000 XP",
         "Đạt 1000 XP.",
         "trophy", "xp_1000"),
        ("marathon", "Marathon", "20 bài đã làm",
         "Tổng cộng 20 lượt luyện trong lịch sử.",
         "footprints", "marathon"),
        ("century", "Century", "100 bài đã làm",
         "Hoàn thành 100 lượt luyện.",
         "hash", "century"),
        ("sharpshooter", "Xạ thủ", "≥80% bài dài",
         "Đạt ≥80% trong một bài có ít nhất 10 câu.",
         "crosshair", "sharpshooter"),
        ("band_6", "Band 6.0", "Band 6.0+",
         "Đạt band 6.0 trở lên trong ít nhất một bài có chấm band.",
         "badge-6", "band_6"),
        ("band_7", "Band 7.0", "Band 7.0+",
         "Đạt band 7.0 trở lên trong một bài.",
         "badge-7", "band_7"),
        ("band_8", "Band 8.0", "Band 8.0+",
         "Đạt band 8.0 trở lên.",
         "badge-8", "band_8"),
        ("all_rounder", "Đa năng", "4 kỹ năng chính",
         "Luyện ít nhất 1 bài mỗi kỹ năng: Reading, Listening, Writing, Speaking.",
         "layers", "all_rounder"),
        ("balanced", "Cân bằng", "Mọi kỹ năng",
         "Luyện cả 5 nhóm: Reading, Listening, Writing, Speaking và Vocabulary.",
         "compass", "balanced"),
        ("dedicated", "Chăm chỉ", "XP + streak",
         "Đạt ≥200 XP và streak ≥ 5 ngày cùng lúc.",
         "award", "dedicated"),
    ]


def _check(stats: _BadgeStats, key: str) -> bool:
    checks: dict[str, bool] = {
        "first_step": stats.total_attempts >= 1,
        "reading_3": stats.reading_count >= 3,
        "reading_10": stats.reading_count >= 10,
        "reading_perfect": stats.perfect_scores >= 1,
        "listening_3": stats.listening_count >= 3,
        "listening_10": stats.listening_count >= 10,
        "writer": stats.writing_count >= 3,
        "writer_pro": stats.writing_count >= 10,
        "speaker": stats.speaking_count >= 5,
        "speaker_star": stats.speaking_count >= 15,
        "word_hunter": stats.vocab_count >= 5,
        "word_master": stats.vocab_count >= 20,
        "shadowing_3": stats.shadowing_count >= 3,
        "shadowing_1": stats.shadowing_count >= 1,
        "shadowing_10": stats.shadowing_count >= 10,
        "shadowing_20": stats.shadowing_count >= 20,
        "conversation_1": stats.conversation_count >= 1,
        "conversation_5": stats.conversation_count >= 5,
        "conversation_10": stats.conversation_count >= 10,
        "conversation_topics_3": stats.conversation_topics >= 3,
        "conversation_deep": stats.conversation_max_turns >= 5,
        "conversation_advanced": stats.conversation_advanced_count >= 1,
        "full_mock_1": stats.full_exam_count >= 1,
        "plan_5": stats.study_plan_done >= 5,
        "streak_3": stats.streak >= 3,
        "streak_7": stats.streak >= 7 or stats.longest_streak >= 7,
        "streak_14": stats.streak >= 14 or stats.longest_streak >= 14,
        "streak_30": stats.longest_streak >= 30,
        "xp_50": stats.xp >= 50,
        "xp_100": stats.xp >= 100,
        "xp_500": stats.xp >= 500,
        "xp_1000": stats.xp >= 1000,
        "marathon": stats.total_attempts >= 20,
        "century": stats.total_attempts >= 100,
        "sharpshooter": stats.perfect_or_strong >= 1,
        "band_6": stats.max_band >= 6.0,
        "band_7": stats.max_band >= 7.0,
        "band_8": stats.max_band >= 8.0,
        "all_rounder": stats.core_skills_used >= 4,
        "balanced": stats.core_skills_used >= 4 and stats.vocab_count >= 1,
        "dedicated": stats.xp >= 200 and stats.streak >= 5,
    }
    return checks.get(key, False)


class BadgeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _gather_stats(self, user_id: int) -> _BadgeStats:
        profile_rs = await self._db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_rs.scalar_one_or_none()

        async def _count_subject(subject: str) -> int:
            rs = await self._db.execute(
                select(func.count())
                .select_from(History)
                .where(History.user_id == user_id, History.subject == subject)
            )
            return int(rs.scalar_one() or 0)

        total_rs = await self._db.execute(
            select(func.count()).select_from(History).where(History.user_id == user_id)
        )
        max_band_rs = await self._db.execute(
            select(func.max(History.band_score)).where(
                History.user_id == user_id, History.band_score.isnot(None)
            )
        )
        strong_rs = await self._db.execute(
            select(func.count())
            .select_from(History)
            .where(
                History.user_id == user_id,
                History.percentage >= 80,
                History.total_questions >= 10,
            )
        )
        perfect_rs = await self._db.execute(
            select(func.count())
            .select_from(History)
            .where(
                History.user_id == user_id,
                History.subject == "Reading",
                History.percentage >= 100,
                History.total_questions >= 10,
            )
        )
        full_mock_rs = await self._db.execute(
            select(func.count())
            .select_from(History)
            .where(History.user_id == user_id, History.mode == "full_exam")
        )
        shadow_rs = await self._db.execute(
            select(func.count())
            .select_from(ShadowingUserHistory)
            .where(ShadowingUserHistory.user_id == user_id)
        )
        plan_rs = await self._db.execute(
            select(func.count())
            .select_from(StudyPlanTask)
            .where(StudyPlanTask.user_id == user_id, StudyPlanTask.is_completed.is_(True))
        )
        conv_count_rs = await self._db.execute(
            select(func.count())
            .select_from(ConversationSession)
            .where(ConversationSession.user_id == user_id, ConversationSession.status == "completed")
        )
        conv_topics_rs = await self._db.execute(
            select(func.count(func.distinct(ConversationSession.topic_id)))
            .select_from(ConversationSession)
            .where(ConversationSession.user_id == user_id, ConversationSession.status == "completed")
        )
        conv_advanced_rs = await self._db.execute(
            select(func.count())
            .select_from(ConversationSession)
            .join(ConversationTopic, ConversationSession.topic_id == ConversationTopic.id)
            .where(
                ConversationSession.user_id == user_id,
                ConversationSession.status == "completed",
                ConversationTopic.level == "advanced",
            )
        )
        conv_feedback_rs = await self._db.execute(
            select(ConversationSession.feedback).where(
                ConversationSession.user_id == user_id,
                ConversationSession.status == "completed",
            )
        )
        conversation_max_turns = 0
        for (feedback,) in conv_feedback_rs.all():
            if isinstance(feedback, dict):
                try:
                    conversation_max_turns = max(conversation_max_turns, int(feedback.get("turn_count") or 0))
                except (TypeError, ValueError):
                    pass

        reading = await _count_subject("Reading")
        listening = await _count_subject("Listening")
        writing = await _count_subject("Writing")
        speaking = await _count_subject("Speaking")
        core_used = sum(1 for n in (reading, listening, writing, speaking) if n >= 1)

        return _BadgeStats(
            total_attempts=int(total_rs.scalar_one() or 0),
            reading_count=reading,
            listening_count=listening,
            writing_count=writing,
            speaking_count=speaking,
            vocab_count=await _count_subject("Vocabulary"),
            shadowing_count=int(shadow_rs.scalar_one() or 0),
            full_exam_count=int(full_mock_rs.scalar_one() or 0),
            study_plan_done=int(plan_rs.scalar_one() or 0),
            conversation_count=int(conv_count_rs.scalar_one() or 0),
            conversation_topics=int(conv_topics_rs.scalar_one() or 0),
            conversation_max_turns=conversation_max_turns,
            conversation_advanced_count=int(conv_advanced_rs.scalar_one() or 0),
            streak=profile.streak if profile else 0,
            longest_streak=profile.longest_streak if profile else 0,
            xp=profile.xp if profile else 0,
            max_band=float(max_band_rs.scalar_one() or 0),
            perfect_or_strong=int(strong_rs.scalar_one() or 0),
            perfect_scores=int(perfect_rs.scalar_one() or 0),
            core_skills_used=core_used,
        )

    def _build_items(self, stats: _BadgeStats) -> list[BadgeItem]:
        items: list[BadgeItem] = []
        for bid, title, desc, hint, icon, checker in _badge_defs():
            items.append(
                BadgeItem(
                    id=bid,
                    title=title,
                    description=desc,
                    hint=hint,
                    icon=icon,
                    unlocked=_check(stats, checker),
                )
            )
        return items

    async def get_badges(self, user: User) -> BadgesResponse:
        stats = await self._gather_stats(user.id)
        items = self._build_items(stats)
        return BadgesResponse(
            items=items,
            unlocked_count=sum(1 for i in items if i.unlocked),
            total_count=len(items),
        )

    async def get_unlocked_ids(self, user: User) -> set[str]:
        stats = await self._gather_stats(user.id)
        return {i.id for i in self._build_items(stats) if i.unlocked}

    async def detect_new_badges(self, user: User, before_unlocked: set[str]) -> list[BadgeItem]:
        stats = await self._gather_stats(user.id)
        return [
            item
            for item in self._build_items(stats)
            if item.unlocked and item.id not in before_unlocked
        ]


async def detect_new_badges_for_user(db: AsyncSession, user: User, before_unlocked: set[str]) -> list[BadgeItem]:
    return await BadgeService(db).detect_new_badges(user, before_unlocked)
