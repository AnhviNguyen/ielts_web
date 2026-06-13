from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ConversationSession,
    ConversationTopic,
    History,
    PracticeSession,
    Progress,
    ShadowingUserHistory,
    SystemVocabTopic,
    SystemVocabWord,
    TranslationAttempt,
    TranslationSentence,
    TranslationStep,
    TranslationTopic,
    User,
    UserProfile,
    VocabTopic,
    VocabWord,
)


class AdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _user_filters(
        self,
        *,
        q: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        leaderboard_hidden: bool | None = None,
    ) -> list:
        filters = []
        if q:
            like = f"%{q.strip()}%"
            filters.append(or_(User.email.ilike(like), UserProfile.full_name.ilike(like)))
        if role:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active == is_active)
        if leaderboard_hidden is not None:
            filters.append(UserProfile.is_leaderboard_hidden == leaderboard_hidden)
        return filters

    async def count_users(
        self,
        *,
        q: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        leaderboard_hidden: bool | None = None,
    ) -> int:
        stmt = (
            select(func.count(User.id))
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .where(*self._user_filters(q=q, role=role, is_active=is_active, leaderboard_hidden=leaderboard_hidden))
        )
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def list_users(
        self,
        *,
        q: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        leaderboard_hidden: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "created_desc",
    ) -> list[tuple[User, UserProfile | None]]:
        sort_map = {
            "created_asc": User.created_at.asc(),
            "created_desc": User.created_at.desc(),
            "xp_desc": desc(UserProfile.xp),
            "xp_asc": UserProfile.xp.asc(),
            "streak_desc": desc(UserProfile.streak),
            "streak_asc": UserProfile.streak.asc(),
        }
        order_by = sort_map.get(sort, User.created_at.desc())
        stmt = (
            select(User, UserProfile)
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .where(*self._user_filters(q=q, role=role, is_active=is_active, leaderboard_hidden=leaderboard_hidden))
            .order_by(order_by, User.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list((await self._db.execute(stmt)).all())

    async def get_user_with_profile(self, user_id: int) -> tuple[User, UserProfile | None] | None:
        stmt = (
            select(User, UserProfile)
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .where(User.id == user_id)
        )
        return (await self._db.execute(stmt)).first()

    async def list_progress(self, user_id: int) -> list[Progress]:
        result = await self._db.execute(select(Progress).where(Progress.user_id == user_id))
        return list(result.scalars().all())

    async def list_recent_history(self, user_id: int, limit: int = 10) -> list[History]:
        stmt = (
            select(History)
            .where(History.user_id == user_id)
            .order_by(History.completed_at.desc())
            .limit(limit)
        )
        return list((await self._db.execute(stmt)).scalars().all())

    async def count_practice_sessions_by_status(self, user_id: int) -> dict[str, int]:
        stmt = (
            select(PracticeSession.status, func.count(PracticeSession.id))
            .where(PracticeSession.user_id == user_id)
            .group_by(PracticeSession.status)
        )
        rows = (await self._db.execute(stmt)).all()
        return {str(status): int(count) for status, count in rows}

    async def count_vocab_topics(self, user_id: int) -> int:
        stmt = select(func.count(VocabTopic.id)).where(VocabTopic.user_id == user_id)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_vocab_words(self, user_id: int) -> int:
        stmt = (
            select(func.count(VocabWord.id))
            .join(VocabTopic, VocabTopic.id == VocabWord.topic_id)
            .where(VocabTopic.user_id == user_id)
        )
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_shadowing_videos(self, user_id: int) -> int:
        stmt = select(func.count(ShadowingUserHistory.id)).where(ShadowingUserHistory.user_id == user_id)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_all_users(self) -> int:
        return int((await self._db.execute(select(func.count(User.id)))).scalar_one() or 0)

    async def count_active_users(self) -> int:
        stmt = select(func.count(User.id)).where(User.is_active == True)  # noqa: E712
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_locked_users(self) -> int:
        stmt = select(func.count(User.id)).where(User.is_active == False)  # noqa: E712
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def list_history_since(self, since: datetime) -> list[History]:
        stmt = select(History).where(History.completed_at >= since)
        return list((await self._db.execute(stmt)).scalars().all())

    async def list_practice_sessions_since(self, since: datetime) -> list[PracticeSession]:
        stmt = select(PracticeSession).where(
            or_(
                PracticeSession.started_at >= since,
                PracticeSession.submitted_at >= since,
            )
        )
        return list((await self._db.execute(stmt)).scalars().all())

    async def list_profile_activity_since(self, since_date) -> list[UserProfile]:
        stmt = select(UserProfile).where(UserProfile.last_activity_date >= since_date)
        return list((await self._db.execute(stmt)).scalars().all())

    async def list_all_profiles(self) -> list[UserProfile]:
        return list((await self._db.execute(select(UserProfile))).scalars().all())

    async def average_band_by_skill(self) -> list[tuple[str, float, int]]:
        stmt = (
            select(History.subject, func.avg(History.band_score), func.count(History.id))
            .where(History.band_score.isnot(None), History.subject.isnot(None))
            .group_by(History.subject)
        )
        return [(str(subject), float(avg or 0), int(count)) for subject, avg, count in (await self._db.execute(stmt)).all()]

    async def list_band_scores(self) -> list[float]:
        stmt = select(History.band_score).where(History.band_score.isnot(None))
        return [float(x) for x in (await self._db.execute(stmt)).scalars().all()]

    async def streak_bucket_counts(self) -> list[tuple[Literal["0", "1-6", "7-29", "30+"], int]]:
        profiles = (await self._db.execute(select(UserProfile.streak))).scalars().all()
        counts = {"0": 0, "1-6": 0, "7-29": 0, "30+": 0}
        for streak in profiles:
            value = int(streak or 0)
            if value <= 0:
                counts["0"] += 1
            elif value < 7:
                counts["1-6"] += 1
            elif value < 30:
                counts["7-29"] += 1
            else:
                counts["30+"] += 1
        return [(k, counts[k]) for k in ("0", "1-6", "7-29", "30+")]

    async def update_user(self, user: User) -> None:
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)

    async def update_profile(self, profile: UserProfile) -> None:
        self._db.add(profile)
        await self._db.flush()
        await self._db.refresh(profile)

    async def attempts_24h_by_user(self) -> dict[int, int]:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        stmt = (
            select(History.user_id, func.count(History.id))
            .where(History.completed_at >= since)
            .group_by(History.user_id)
        )
        return {int(user_id): int(count) for user_id, count in (await self._db.execute(stmt)).all()}

    async def user_band_history(self, user_id: int) -> list[History]:
        stmt = (
            select(History)
            .where(History.user_id == user_id, History.band_score.isnot(None))
            .order_by(History.completed_at.asc())
        )
        return list((await self._db.execute(stmt)).scalars().all())

    async def list_system_vocab_topics(self, q: str | None = None, active: bool | None = None) -> list[tuple[SystemVocabTopic, int]]:
        filters = []
        if q:
            like = f"%{q.strip()}%"
            filters.append(or_(SystemVocabTopic.name.ilike(like), SystemVocabTopic.description.ilike(like)))
        if active is not None:
            filters.append(SystemVocabTopic.is_active == active)
        stmt = (
            select(SystemVocabTopic, func.count(SystemVocabWord.id))
            .outerjoin(SystemVocabWord, SystemVocabWord.topic_id == SystemVocabTopic.id)
            .where(*filters)
            .group_by(SystemVocabTopic.id)
            .order_by(SystemVocabTopic.sort_order.asc(), SystemVocabTopic.created_at.desc())
        )
        return list((await self._db.execute(stmt)).all())

    async def get_system_vocab_topic(self, topic_id: int) -> SystemVocabTopic | None:
        return await self._db.get(SystemVocabTopic, topic_id)

    async def create_system_vocab_topic(self, data: dict) -> SystemVocabTopic:
        topic = SystemVocabTopic(**data)
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def update_system_vocab_topic(self, topic: SystemVocabTopic, data: dict) -> SystemVocabTopic:
        for key, value in data.items():
            setattr(topic, key, value)
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def delete_system_vocab_topic(self, topic: SystemVocabTopic) -> None:
        await self._db.delete(topic)
        await self._db.flush()

    async def list_system_vocab_words(self, topic_id: int) -> list[SystemVocabWord]:
        stmt = (
            select(SystemVocabWord)
            .where(SystemVocabWord.topic_id == topic_id)
            .order_by(SystemVocabWord.sort_order.asc(), SystemVocabWord.created_at.asc())
        )
        return list((await self._db.execute(stmt)).scalars().all())

    async def get_system_vocab_word(self, topic_id: int, word_id: int) -> SystemVocabWord | None:
        stmt = select(SystemVocabWord).where(SystemVocabWord.topic_id == topic_id, SystemVocabWord.id == word_id)
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def create_system_vocab_word(self, topic_id: int, data: dict) -> SystemVocabWord:
        word = SystemVocabWord(topic_id=topic_id, **data)
        self._db.add(word)
        await self._db.flush()
        await self._db.refresh(word)
        return word

    async def update_system_vocab_word(self, word: SystemVocabWord, data: dict) -> SystemVocabWord:
        for key, value in data.items():
            setattr(word, key, value)
        self._db.add(word)
        await self._db.flush()
        await self._db.refresh(word)
        return word

    async def delete_system_vocab_word(self, word: SystemVocabWord) -> None:
        await self._db.delete(word)
        await self._db.flush()

    async def get_user_vocab_topic(self, user_id: int, topic_id: int) -> VocabTopic | None:
        stmt = select(VocabTopic).where(VocabTopic.user_id == user_id, VocabTopic.id == topic_id)
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def find_user_vocab_topic_by_name(self, user_id: int, name: str) -> VocabTopic | None:
        stmt = select(VocabTopic).where(VocabTopic.user_id == user_id, func.lower(VocabTopic.name) == name.lower())
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def create_user_vocab_topic(self, user_id: int, name: str) -> VocabTopic:
        topic = VocabTopic(user_id=user_id, name=name)
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def list_user_vocab_words(self, topic_id: int) -> list[VocabWord]:
        stmt = select(VocabWord).where(VocabWord.topic_id == topic_id)
        return list((await self._db.execute(stmt)).scalars().all())

    async def create_user_vocab_word(self, topic_id: int, data: dict) -> VocabWord:
        word = VocabWord(topic_id=topic_id, **data)
        self._db.add(word)
        await self._db.flush()
        await self._db.refresh(word)
        return word

    async def list_conversation_topics(
        self,
        *,
        q: str | None = None,
        level: str | None = None,
        active: bool | None = None,
    ) -> list[tuple[ConversationTopic, int]]:
        filters = []
        if q:
            like = f"%{q.strip()}%"
            filters.append(or_(ConversationTopic.title.ilike(like), ConversationTopic.description.ilike(like)))
        if level:
            filters.append(ConversationTopic.level == level)
        if active is not None:
            filters.append(ConversationTopic.is_active == active)
        stmt = (
            select(ConversationTopic, func.count(ConversationSession.id))
            .outerjoin(ConversationSession, ConversationSession.topic_id == ConversationTopic.id)
            .where(*filters)
            .group_by(ConversationTopic.id)
            .order_by(ConversationTopic.order.asc(), ConversationTopic.created_at.desc())
        )
        return list((await self._db.execute(stmt)).all())

    async def get_conversation_topic(self, topic_id: int) -> ConversationTopic | None:
        return await self._db.get(ConversationTopic, topic_id)

    async def count_conversation_sessions(self, topic_id: int) -> int:
        stmt = select(func.count(ConversationSession.id)).where(ConversationSession.topic_id == topic_id)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def create_conversation_topic(self, data: dict) -> ConversationTopic:
        topic = ConversationTopic(**data)
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def update_conversation_topic(self, topic: ConversationTopic, data: dict) -> ConversationTopic:
        for key, value in data.items():
            setattr(topic, key, value)
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def list_translation_steps(
        self, *, q: str | None = None, active: bool | None = None
    ) -> list[TranslationStep]:
        filters = []
        if q:
            like = f"%{q.strip()}%"
            filters.append(or_(TranslationStep.title.ilike(like), TranslationStep.description.ilike(like)))
        if active is not None:
            filters.append(TranslationStep.is_active == active)
        stmt = select(TranslationStep).where(*filters).order_by(TranslationStep.order.asc(), TranslationStep.id.asc())
        return list((await self._db.execute(stmt)).scalars().all())

    async def get_translation_step(self, step_id: int) -> TranslationStep | None:
        return await self._db.get(TranslationStep, step_id)

    async def create_translation_step(self, data: dict) -> TranslationStep:
        step = TranslationStep(**data)
        self._db.add(step)
        await self._db.flush()
        await self._db.refresh(step)
        return step

    async def update_translation_step(self, step: TranslationStep, data: dict) -> TranslationStep:
        for key, value in data.items():
            setattr(step, key, value)
        self._db.add(step)
        await self._db.flush()
        await self._db.refresh(step)
        return step

    async def list_translation_topics(
        self, step_id: int, *, active: bool | None = None
    ) -> list[TranslationTopic]:
        filters = [TranslationTopic.step_id == step_id]
        if active is not None:
            filters.append(TranslationTopic.is_active == active)
        stmt = select(TranslationTopic).where(*filters).order_by(TranslationTopic.order.asc(), TranslationTopic.id.asc())
        return list((await self._db.execute(stmt)).scalars().all())

    async def get_translation_topic(self, topic_id: int) -> TranslationTopic | None:
        return await self._db.get(TranslationTopic, topic_id)

    async def create_translation_topic(self, step_id: int, data: dict) -> TranslationTopic:
        topic = TranslationTopic(step_id=step_id, **data)
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def update_translation_topic(self, topic: TranslationTopic, data: dict) -> TranslationTopic:
        for key, value in data.items():
            setattr(topic, key, value)
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def list_translation_sentences(
        self, topic_id: int, *, active: bool | None = None
    ) -> list[TranslationSentence]:
        filters = [TranslationSentence.topic_id == topic_id]
        if active is not None:
            filters.append(TranslationSentence.is_active == active)
        stmt = select(TranslationSentence).where(*filters).order_by(TranslationSentence.order.asc(), TranslationSentence.id.asc())
        return list((await self._db.execute(stmt)).scalars().all())

    async def get_translation_sentence(self, sentence_id: int) -> TranslationSentence | None:
        return await self._db.get(TranslationSentence, sentence_id)

    async def create_translation_sentence(self, topic_id: int, data: dict) -> TranslationSentence:
        sentence = TranslationSentence(topic_id=topic_id, **data)
        self._db.add(sentence)
        await self._db.flush()
        await self._db.refresh(sentence)
        return sentence

    async def update_translation_sentence(self, sentence: TranslationSentence, data: dict) -> TranslationSentence:
        for key, value in data.items():
            setattr(sentence, key, value)
        self._db.add(sentence)
        await self._db.flush()
        await self._db.refresh(sentence)
        return sentence

    async def count_translation_topics(self, step_id: int, *, active: bool | None = None) -> int:
        filters = [TranslationTopic.step_id == step_id]
        if active is not None:
            filters.append(TranslationTopic.is_active == active)
        stmt = select(func.count(TranslationTopic.id)).where(*filters)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_translation_sentences_for_step(self, step_id: int, *, active: bool | None = None) -> int:
        filters = [TranslationTopic.step_id == step_id]
        if active is not None:
            filters.append(TranslationSentence.is_active == active)
        stmt = (
            select(func.count(TranslationSentence.id))
            .join(TranslationTopic, TranslationTopic.id == TranslationSentence.topic_id)
            .where(*filters)
        )
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_translation_sentences(self, topic_id: int, *, active: bool | None = None) -> int:
        filters = [TranslationSentence.topic_id == topic_id]
        if active is not None:
            filters.append(TranslationSentence.is_active == active)
        stmt = select(func.count(TranslationSentence.id)).where(*filters)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_translation_attempts(self, sentence_id: int) -> int:
        stmt = select(func.count(TranslationAttempt.id)).where(TranslationAttempt.sentence_id == sentence_id)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_total_attempts(self) -> int:
        return int((await self._db.execute(select(func.count(History.id)))).scalar_one() or 0)

    async def overall_average_band(self) -> float:
        stmt = select(func.avg(History.band_score)).where(History.band_score.isnot(None))
        value = (await self._db.execute(stmt)).scalar_one()
        return round(float(value or 0), 2)

    async def list_users_created_since(self, since: datetime) -> list[User]:
        stmt = select(User).where(User.created_at >= since)
        return list((await self._db.execute(stmt)).scalars().all())

    async def attempts_by_subject(self) -> list[tuple[str, int, float]]:
        stmt = (
            select(History.subject, func.count(History.id), func.avg(History.band_score))
            .where(History.subject.isnot(None))
            .group_by(History.subject)
            .order_by(func.count(History.id).desc())
        )
        return [
            (str(subject), int(count), round(float(avg or 0), 2))
            for subject, count, avg in (await self._db.execute(stmt)).all()
        ]

    async def count_system_vocab_topics(self, *, active: bool | None = True) -> int:
        filters = []
        if active is not None:
            filters.append(SystemVocabTopic.is_active == active)
        stmt = select(func.count(SystemVocabTopic.id))
        if filters:
            stmt = stmt.where(*filters)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_conversation_topics(self, *, active: bool | None = True) -> int:
        filters = []
        if active is not None:
            filters.append(ConversationTopic.is_active == active)
        stmt = select(func.count(ConversationTopic.id))
        if filters:
            stmt = stmt.where(*filters)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_translation_steps(self, *, active: bool | None = True) -> int:
        filters = []
        if active is not None:
            filters.append(TranslationStep.is_active == active)
        stmt = select(func.count(TranslationStep.id))
        if filters:
            stmt = stmt.where(*filters)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def count_translation_topics(self, *, active: bool | None = True) -> int:
        filters = []
        if active is not None:
            filters.append(TranslationTopic.is_active == active)
        stmt = select(func.count(TranslationTopic.id))
        if filters:
            stmt = stmt.where(*filters)
        return int((await self._db.execute(stmt)).scalar_one() or 0)

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def create_user_with_profile(
        self,
        *,
        email: str,
        password_hash: str,
        role: str,
        full_name: str | None,
        is_verified: bool,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            is_verified=is_verified,
            auth_provider="email",
        )
        self._db.add(user)
        await self._db.flush()
        profile = UserProfile(user_id=user.id, full_name=full_name or None)
        self._db.add(profile)
        await self._db.flush()
        await self._db.refresh(user)
        return user
