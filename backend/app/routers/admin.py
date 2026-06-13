from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin_user
from app.db.database import get_db
from app.db.models import User
from app.repositories.admin_repository import AdminRepository
from app.schemas import (
    AdminLeaderboardResponse,
    AdminLeaderboardUpdate,
    AdminContentListResponse,
    AdminContentRawRequest,
    AdminContentResponse,
    AdminContentWriteResponse,
    AdminConversationTopicCreate,
    AdminConversationTopicResponse,
    AdminConversationTopicUpdate,
    AdminImageUploadResponse,
    AdminListeningMockTestBuilderRequest,
    AdminListeningMockTestBuilderResponse,
    AdminOverviewResponse,
    AdminReadingMockTestBuilderRequest,
    AdminReadingMockTestBuilderResponse,
    AdminResetXpStreakRequest,
    AdminSpeakingMockTestBuilderRequest,
    AdminSpeakingMockTestBuilderResponse,
    AdminSystemVocabCopyRequest,
    AdminSystemVocabCopyResponse,
    AdminSystemVocabTopicCreate,
    AdminSystemVocabTopicDetail,
    AdminSystemVocabTopicResponse,
    AdminSystemVocabTopicUpdate,
    AdminSystemVocabWordCreate,
    AdminSystemVocabWordResponse,
    AdminSystemVocabWordUpdate,
    AdminTranslationSentenceCreate,
    AdminTranslationSentenceResponse,
    AdminTranslationSentenceUpdate,
    AdminTranslationStepCreate,
    AdminTranslationStepDetail,
    AdminTranslationStepResponse,
    AdminTranslationStepUpdate,
    AdminTranslationTopicCreate,
    AdminTranslationTopicDetail,
    AdminTranslationTopicResponse,
    AdminTranslationTopicUpdate,
    AdminUserCreate,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
    MessageResponse,
)
from app.services.admin_service import AdminService
from app.services.admin_content_service import AdminContentService

router = APIRouter(prefix="/admin", tags=["Admin"])


def _svc(db: AsyncSession) -> AdminService:
    return AdminService(AdminRepository(db))


def _content_svc() -> AdminContentService:
    return AdminContentService()


@router.post("/assets/images", response_model=AdminImageUploadResponse)
async def upload_admin_image(
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin_user),
) -> AdminImageUploadResponse:
    return await _content_svc().save_admin_image(file)


@router.post("/assets/audio", response_model=AdminImageUploadResponse)
async def upload_admin_audio(
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin_user),
) -> AdminImageUploadResponse:
    return await _content_svc().save_admin_audio(file)


@router.get("/overview", response_model=AdminOverviewResponse)
async def get_overview(
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminOverviewResponse:
    return await _svc(db).get_overview()


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    q: str | None = Query(default=None, max_length=100),
    role: str | None = Query(default=None, pattern="^(admin|user)$"),
    is_active: bool | None = Query(default=None),
    leaderboard_hidden: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="created_desc"),
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListResponse:
    return await _svc(db).list_users(
        q=q,
        role=role,
        is_active=is_active,
        leaderboard_hidden=leaderboard_hidden,
        page=page,
        page_size=page_size,
        sort=sort,
    )


@router.post("/users", response_model=AdminUserDetail, status_code=201)
async def create_user(
    body: AdminUserCreate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    return await _svc(db).create_user(body)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(
    user_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    return await _svc(db).get_user_detail(user_id)


@router.patch("/users/{user_id}/status", response_model=AdminUserDetail)
async def update_user_status(
    user_id: int,
    body: AdminUserStatusUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    return await _svc(db).update_user_status(
        target_user_id=user_id,
        admin_user_id=admin.id,
        is_active=body.is_active,
        lock_reason=body.lock_reason,
    )


@router.patch("/users/{user_id}/role", response_model=AdminUserDetail)
async def update_user_role(
    user_id: int,
    body: AdminUserRoleUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    return await _svc(db).update_user_role(
        target_user_id=user_id,
        admin_user_id=admin.id,
        role=body.role,
    )


@router.post("/users/{user_id}/reset-xp-streak", response_model=AdminUserDetail)
async def reset_xp_streak(
    user_id: int,
    body: AdminResetXpStreakRequest,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    return await _svc(db).reset_xp_streak(
        user_id,
        reset_xp=body.reset_xp,
        reset_streak=body.reset_streak,
    )


@router.patch("/users/{user_id}/leaderboard", response_model=AdminUserDetail)
async def update_user_leaderboard(
    user_id: int,
    body: AdminLeaderboardUpdate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    return await _svc(db).update_leaderboard_visibility(
        user_id,
        is_hidden=body.is_leaderboard_hidden,
        reason=body.reason,
    )


@router.get("/leaderboard", response_model=AdminLeaderboardResponse)
async def list_leaderboard(
    q: str | None = Query(default=None, max_length=100),
    hidden: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminLeaderboardResponse:
    return await _svc(db).list_leaderboard(q=q, hidden=hidden, page=page, page_size=page_size)


@router.get("/leaderboard/anomalies", response_model=AdminLeaderboardResponse)
async def list_leaderboard_anomalies(
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminLeaderboardResponse:
    return await _svc(db).list_anomalies()


@router.get("/system-vocab/topics", response_model=list[AdminSystemVocabTopicResponse])
async def list_system_vocab_topics(
    q: str | None = Query(default=None, max_length=100),
    active: bool | None = Query(default=None),
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[AdminSystemVocabTopicResponse]:
    return await _svc(db).list_system_vocab_topics(q=q, active=active)


@router.post("/system-vocab/topics", response_model=AdminSystemVocabTopicResponse)
async def create_system_vocab_topic(
    body: AdminSystemVocabTopicCreate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemVocabTopicResponse:
    return await _svc(db).create_system_vocab_topic(body)


@router.get("/system-vocab/topics/{topic_id}", response_model=AdminSystemVocabTopicDetail)
async def get_system_vocab_topic(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemVocabTopicDetail:
    return await _svc(db).get_system_vocab_topic_detail(topic_id)


@router.patch("/system-vocab/topics/{topic_id}", response_model=AdminSystemVocabTopicResponse)
async def update_system_vocab_topic(
    topic_id: int,
    body: AdminSystemVocabTopicUpdate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemVocabTopicResponse:
    return await _svc(db).update_system_vocab_topic(topic_id, body)


@router.delete("/system-vocab/topics/{topic_id}", response_model=MessageResponse)
async def delete_system_vocab_topic(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    return await _svc(db).delete_system_vocab_topic(topic_id)


@router.get("/system-vocab/topics/{topic_id}/words", response_model=list[AdminSystemVocabWordResponse])
async def list_system_vocab_words(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[AdminSystemVocabWordResponse]:
    return await _svc(db).list_system_vocab_words(topic_id)


@router.post("/system-vocab/topics/{topic_id}/words", response_model=AdminSystemVocabWordResponse)
async def create_system_vocab_word(
    topic_id: int,
    body: AdminSystemVocabWordCreate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemVocabWordResponse:
    return await _svc(db).create_system_vocab_word(topic_id, body)


@router.patch("/system-vocab/topics/{topic_id}/words/{word_id}", response_model=AdminSystemVocabWordResponse)
async def update_system_vocab_word(
    topic_id: int,
    word_id: int,
    body: AdminSystemVocabWordUpdate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemVocabWordResponse:
    return await _svc(db).update_system_vocab_word(topic_id, word_id, body)


@router.delete("/system-vocab/topics/{topic_id}/words/{word_id}", response_model=MessageResponse)
async def delete_system_vocab_word(
    topic_id: int,
    word_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    return await _svc(db).delete_system_vocab_word(topic_id, word_id)


@router.post("/system-vocab/topics/{topic_id}/copy-to-user", response_model=AdminSystemVocabCopyResponse)
async def copy_system_vocab_to_user(
    topic_id: int,
    body: AdminSystemVocabCopyRequest,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemVocabCopyResponse:
    return await _svc(db).copy_system_vocab_to_user(
        topic_id,
        user_id=body.user_id,
        target_topic_id=body.target_topic_id,
        target_topic_name=body.target_topic_name,
        word_ids=body.word_ids,
    )


@router.get("/conversation/topics", response_model=list[AdminConversationTopicResponse])
async def list_admin_conversation_topics(
    q: str | None = Query(default=None, max_length=100),
    level: str | None = Query(default=None, max_length=20),
    active: bool | None = Query(default=None),
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[AdminConversationTopicResponse]:
    return await _svc(db).list_conversation_topics(q=q, level=level, active=active)


@router.post("/conversation/topics", response_model=AdminConversationTopicResponse)
async def create_admin_conversation_topic(
    body: AdminConversationTopicCreate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminConversationTopicResponse:
    return await _svc(db).create_conversation_topic(body)


@router.get("/conversation/topics/{topic_id}", response_model=AdminConversationTopicResponse)
async def get_admin_conversation_topic(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminConversationTopicResponse:
    return await _svc(db).get_conversation_topic(topic_id)


@router.patch("/conversation/topics/{topic_id}", response_model=AdminConversationTopicResponse)
async def update_admin_conversation_topic(
    topic_id: int,
    body: AdminConversationTopicUpdate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminConversationTopicResponse:
    return await _svc(db).update_conversation_topic(topic_id, body)


@router.delete("/conversation/topics/{topic_id}", response_model=MessageResponse)
async def archive_admin_conversation_topic(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    return await _svc(db).archive_conversation_topic(topic_id)


@router.get("/translation/steps", response_model=list[AdminTranslationStepResponse])
async def list_admin_translation_steps(
    q: str | None = Query(default=None, max_length=100),
    active: bool | None = Query(default=None),
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[AdminTranslationStepResponse]:
    return await _svc(db).list_translation_steps(q=q, active=active)


@router.post("/translation/steps", response_model=AdminTranslationStepResponse)
async def create_admin_translation_step(
    body: AdminTranslationStepCreate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTranslationStepResponse:
    return await _svc(db).create_translation_step(body)


@router.get("/translation/steps/{step_id}", response_model=AdminTranslationStepDetail)
async def get_admin_translation_step(
    step_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTranslationStepDetail:
    return await _svc(db).get_translation_step_detail(step_id)


@router.patch("/translation/steps/{step_id}", response_model=AdminTranslationStepResponse)
async def update_admin_translation_step(
    step_id: int,
    body: AdminTranslationStepUpdate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTranslationStepResponse:
    return await _svc(db).update_translation_step(step_id, body)


@router.delete("/translation/steps/{step_id}", response_model=MessageResponse)
async def archive_admin_translation_step(
    step_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    return await _svc(db).archive_translation_step(step_id)


@router.post("/translation/steps/{step_id}/topics", response_model=AdminTranslationTopicResponse)
async def create_admin_translation_topic(
    step_id: int,
    body: AdminTranslationTopicCreate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTranslationTopicResponse:
    return await _svc(db).create_translation_topic(step_id, body)


@router.get("/translation/topics/{topic_id}", response_model=AdminTranslationTopicDetail)
async def get_admin_translation_topic(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTranslationTopicDetail:
    return await _svc(db).get_translation_topic_detail(topic_id)


@router.patch("/translation/topics/{topic_id}", response_model=AdminTranslationTopicResponse)
async def update_admin_translation_topic(
    topic_id: int,
    body: AdminTranslationTopicUpdate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTranslationTopicResponse:
    return await _svc(db).update_translation_topic(topic_id, body)


@router.delete("/translation/topics/{topic_id}", response_model=MessageResponse)
async def archive_admin_translation_topic(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    return await _svc(db).archive_translation_topic(topic_id)


@router.post("/translation/topics/{topic_id}/sentences", response_model=AdminTranslationSentenceResponse)
async def create_admin_translation_sentence(
    topic_id: int,
    body: AdminTranslationSentenceCreate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTranslationSentenceResponse:
    return await _svc(db).create_translation_sentence(topic_id, body)


@router.patch("/translation/sentences/{sentence_id}", response_model=AdminTranslationSentenceResponse)
async def update_admin_translation_sentence(
    sentence_id: int,
    body: AdminTranslationSentenceUpdate,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTranslationSentenceResponse:
    return await _svc(db).update_translation_sentence(sentence_id, body)


@router.delete("/translation/sentences/{sentence_id}", response_model=MessageResponse)
async def archive_admin_translation_sentence(
    sentence_id: int,
    _admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    return await _svc(db).archive_translation_sentence(sentence_id)


@router.get("/content/writing-topics", response_model=AdminContentListResponse)
async def list_writing_topics(
    task_type: int | None = Query(default=None, ge=1, le=2),
    status: str | None = Query(default=None, max_length=50),
    q: str | None = Query(default=None, max_length=100),
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentListResponse:
    return _content_svc().list_writing_topics(task_type=task_type, status_filter=status, q=q)


@router.get("/content/writing-topics/{topic_id}", response_model=AdminContentResponse)
async def get_writing_topic(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentResponse:
    return _content_svc().get_writing_topic(topic_id)


@router.post("/content/writing-topics", response_model=AdminContentWriteResponse)
async def create_writing_topic(
    body: AdminContentRawRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().create_writing_topic(body.raw_json)


@router.patch("/content/writing-topics/{topic_id}", response_model=AdminContentWriteResponse)
async def update_writing_topic(
    topic_id: int,
    body: AdminContentRawRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().update_writing_topic(topic_id, body.raw_json)


@router.delete("/content/writing-topics/{topic_id}", response_model=AdminContentWriteResponse)
async def archive_writing_topic(
    topic_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().archive_writing_topic(topic_id)


@router.get("/content/mock-tests", response_model=AdminContentListResponse)
async def list_admin_mock_tests(
    skill_id: int | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentListResponse:
    return _content_svc().list_mock_tests(skill_id=skill_id, q=q)


@router.post("/content/mock-tests", response_model=AdminContentWriteResponse)
async def create_admin_mock_test(
    body: AdminContentRawRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().write_mock_test(None, body.raw_json)


@router.post("/content/reading-mock-tests", response_model=AdminReadingMockTestBuilderResponse)
async def create_admin_reading_mock_test(
    body: AdminReadingMockTestBuilderRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminReadingMockTestBuilderResponse:
    return _content_svc().save_reading_mock_test_builder(body)


@router.get("/content/reading-mock-tests/{mock_test_id}/builder", response_model=AdminReadingMockTestBuilderResponse)
async def get_admin_reading_mock_test_builder(
    mock_test_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminReadingMockTestBuilderResponse:
    return _content_svc().get_reading_mock_test_builder(mock_test_id)


@router.patch("/content/reading-mock-tests/{mock_test_id}", response_model=AdminReadingMockTestBuilderResponse)
async def update_admin_reading_mock_test(
    mock_test_id: int,
    body: AdminReadingMockTestBuilderRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminReadingMockTestBuilderResponse:
    return _content_svc().save_reading_mock_test_builder(body, mock_test_id=mock_test_id)


@router.post("/content/listening-mock-tests", response_model=AdminListeningMockTestBuilderResponse)
async def create_admin_listening_mock_test(
    body: AdminListeningMockTestBuilderRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminListeningMockTestBuilderResponse:
    return _content_svc().save_listening_mock_test_builder(body)


@router.get("/content/listening-mock-tests/{mock_test_id}/builder", response_model=AdminListeningMockTestBuilderResponse)
async def get_admin_listening_mock_test_builder(
    mock_test_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminListeningMockTestBuilderResponse:
    return _content_svc().get_listening_mock_test_builder(mock_test_id)


@router.patch("/content/listening-mock-tests/{mock_test_id}", response_model=AdminListeningMockTestBuilderResponse)
async def update_admin_listening_mock_test(
    mock_test_id: int,
    body: AdminListeningMockTestBuilderRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminListeningMockTestBuilderResponse:
    return _content_svc().save_listening_mock_test_builder(body, mock_test_id=mock_test_id)


@router.post("/content/speaking-mock-tests", response_model=AdminSpeakingMockTestBuilderResponse)
async def create_admin_speaking_mock_test(
    body: AdminSpeakingMockTestBuilderRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminSpeakingMockTestBuilderResponse:
    return _content_svc().save_speaking_mock_test_builder(body)


@router.get("/content/speaking-mock-tests/{mock_test_id}/builder", response_model=AdminSpeakingMockTestBuilderResponse)
async def get_admin_speaking_mock_test_builder(
    mock_test_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminSpeakingMockTestBuilderResponse:
    return _content_svc().get_speaking_mock_test_builder(mock_test_id)


@router.patch("/content/speaking-mock-tests/{mock_test_id}", response_model=AdminSpeakingMockTestBuilderResponse)
async def update_admin_speaking_mock_test(
    mock_test_id: int,
    body: AdminSpeakingMockTestBuilderRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminSpeakingMockTestBuilderResponse:
    return _content_svc().save_speaking_mock_test_builder(body, mock_test_id=mock_test_id)


@router.get("/content/mock-tests/{mock_test_id}", response_model=AdminContentResponse)
async def get_admin_mock_test(
    mock_test_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentResponse:
    return _content_svc().get_mock_test(mock_test_id)


@router.patch("/content/mock-tests/{mock_test_id}", response_model=AdminContentWriteResponse)
async def update_admin_mock_test(
    mock_test_id: int,
    body: AdminContentRawRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().write_mock_test(mock_test_id, body.raw_json)


@router.delete("/content/mock-tests/{mock_test_id}", response_model=AdminContentWriteResponse)
async def archive_admin_mock_test(
    mock_test_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().archive_mock_test(mock_test_id)


@router.get("/content/quizzes", response_model=AdminContentListResponse)
async def list_admin_quizzes(
    q: str | None = Query(default=None, max_length=100),
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentListResponse:
    return _content_svc().list_quizzes(q=q)


@router.post("/content/quizzes", response_model=AdminContentWriteResponse)
async def create_admin_quiz(
    body: AdminContentRawRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().write_quiz(None, body.raw_json)


@router.get("/content/quizzes/{quiz_id}", response_model=AdminContentResponse)
async def get_admin_quiz(
    quiz_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentResponse:
    return _content_svc().get_quiz(quiz_id)


@router.patch("/content/quizzes/{quiz_id}", response_model=AdminContentWriteResponse)
async def update_admin_quiz(
    quiz_id: int,
    body: AdminContentRawRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().write_quiz(quiz_id, body.raw_json)


@router.delete("/content/quizzes/{quiz_id}", response_model=AdminContentWriteResponse)
async def archive_admin_quiz(
    quiz_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().archive_quiz(quiz_id)


@router.get("/content/quizzes/{quiz_id}/parts/{part_id}", response_model=AdminContentResponse)
async def get_admin_quiz_part(
    quiz_id: int,
    part_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentResponse:
    quiz = _content_svc().get_quiz(quiz_id)
    for part in (quiz.item.get("parts") or []):
        if isinstance(part, dict) and int(part.get("id") or 0) == part_id:
            return AdminContentResponse(item=part, raw_json=part)
    from fastapi import HTTPException, status
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz part not found")


@router.patch("/content/quizzes/{quiz_id}/parts/{part_id}", response_model=AdminContentWriteResponse)
async def update_admin_quiz_part(
    quiz_id: int,
    part_id: int,
    body: AdminContentRawRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().update_quiz_part(quiz_id, part_id, body.raw_json)


@router.get("/content/quizzes/{quiz_id}/questions/{question_id}", response_model=AdminContentResponse)
async def get_admin_quiz_question(
    quiz_id: int,
    question_id: int,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentResponse:
    quiz = _content_svc().get_quiz(quiz_id)
    for part in (quiz.item.get("parts") or []):
        for question in part.get("questions") or []:
            if isinstance(question, dict) and int(question.get("id") or 0) == question_id:
                return AdminContentResponse(item=question, raw_json=question)
    from fastapi import HTTPException, status
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz question not found")


@router.patch("/content/quizzes/{quiz_id}/questions/{question_id}", response_model=AdminContentWriteResponse)
async def update_admin_quiz_question(
    quiz_id: int,
    question_id: int,
    body: AdminContentRawRequest,
    _admin: User = Depends(get_current_admin_user),
) -> AdminContentWriteResponse:
    return _content_svc().update_quiz_question(quiz_id, question_id, body.raw_json)
