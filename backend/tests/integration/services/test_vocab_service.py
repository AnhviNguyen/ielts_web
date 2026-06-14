"""
tests/integration/services/test_vocab_service.py
─────────────────────────────────────────────────
Integration tests for VocabService and VocabLookupService.
Covers dictionary lookup (mocked), CRUD for topics and words, SRS SM-2 transitions,
and cascade delete behaviors.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from sqlalchemy import select

from app.db.models import User, VocabTopic, VocabWord
from app.repositories.vocab_repository import VocabRepository
from app.services.vocab_service import VocabService
from app.services.vocab_lookup_service import lookup_word
from app.schemas import VocabWordCreate, VocabWordUpdate

pytestmark = pytest.mark.integration


@pytest.fixture
def vocab_repo(db_session):
    return VocabRepository(db_session)


@pytest.fixture
def vocab_service(vocab_repo):
    return VocabService(vocab_repo)


# ---------------------------------------------------------------------------
# VS-01: Vocab Lookup Service (API mocked)
# ---------------------------------------------------------------------------

@patch("httpx.AsyncClient.get")
async def test_vs01_vocab_lookup_success(mock_get):
    """
    VS-01: Tra cứu từ vựng mới -> Gọi API từ điển + dịch nghĩa.
    """
    # Mock responses for Dictionary API and MyMemory API
    mock_dict_resp = MagicMock()
    mock_dict_resp.status_code = 200
    mock_dict_resp.is_success = True
    mock_dict_resp.json.return_value = [
        {
            "word": "hello",
            "phonetic": "həˈləʊ",
            "meanings": [
                {
                    "partOfSpeech": "noun",
                    "definitions": [{"definition": "An expression of greeting"}]
                }
            ],
            "phonetics": [{"text": "həˈləʊ", "audio": "//audio.url"}]
        }
    ]

    mock_mymemory_resp = MagicMock()
    mock_mymemory_resp.status_code = 200
    mock_mymemory_resp.is_success = True
    mock_mymemory_resp.json.return_value = {
        "responseData": {"translatedText": "xin chào"}
    }

    # Side effect for HTTP GET calls
    def get_side_effect(url, *args, **kwargs):
        if "dictionaryapi.dev" in url:
            return mock_dict_resp
        elif "mymemory" in url:
            return mock_mymemory_resp
        return MagicMock(status_code=404)

    mock_get.side_effect = get_side_effect

    result = await lookup_word("hello")
    assert result["word"] == "hello"
    assert result["phonetic"] == "həˈləʊ"
    assert result["meaning_en"] == "(noun) An expression of greeting"
    assert result["meaning_vi"] == "xin chào"
    assert result["audio"] == "https://audio.url"


# ---------------------------------------------------------------------------
# VS-02: Save word to topic (Topic & Word CRUD)
# ---------------------------------------------------------------------------

async def test_vs02_topic_and_word_crud(vocab_service, db_session, make_user):
    """
    VS-02: Lưu từ vào topic -> Tạo topic, tạo word và kiểm tra CRUD.
    """
    user = await make_user(email="vocab_student@example.com")

    # 1. Create Topic
    topic_resp = await vocab_service.create_topic(user_id=user.id, name="IELTS Essentials")
    assert topic_resp.name == "IELTS Essentials"

    # Verify topic in DB
    stmt_topic = select(VocabTopic).where(VocabTopic.id == topic_resp.id)
    res_topic = await db_session.execute(stmt_topic)
    assert res_topic.scalar_one_or_none() is not None

    # 2. Add Word to Topic
    word_payload = VocabWordCreate(
        word="ubiquitous",
        phonetic="juːˈbɪkwɪtəs",
        word_type="adjective",
        meaning_en="Present, appearing, or found everywhere.",
        meaning_vi="phổ biến, đầy rẫy",
        example="Computers are now ubiquitous.",
        example_vi="Máy tính ngày nay xuất hiện ở khắp mọi nơi.",
    )
    word_resp = await vocab_service.create_word(topic_id=topic_resp.id, user_id=user.id, data=word_payload)
    assert word_resp.word == "ubiquitous"
    assert word_resp.mastery == "new"

    # Verify word in DB
    stmt_word = select(VocabWord).where(VocabWord.id == word_resp.id)
    res_word = await db_session.execute(stmt_word)
    word_row = res_word.scalar_one_or_none()
    assert word_row is not None
    assert word_row.topic_id == topic_resp.id


# ---------------------------------------------------------------------------
# VS-03 & VS-04: SRS review (correct & incorrect)
# ---------------------------------------------------------------------------

async def test_vs03_srs_review_correct_increases_interval(vocab_service, db_session, make_user):
    """
    VS-03: SRS review trả lời đúng -> interval tăng theo SM-2.
    """
    user = await make_user(email="srs_good@example.com")
    topic = await vocab_service.create_topic(user_id=user.id, name="SRS Topic")
    
    word_payload = VocabWordCreate(word="meticulous", meaning_vi="tỉ mỉ")
    word = await vocab_service.create_word(topic_id=topic.id, user_id=user.id, data=word_payload)

    # First review correct (quality=5)
    updated = await vocab_service.record_review(
        topic_id=topic.id, word_id=word.id, user_id=user.id, quality=5
    )
    assert updated.srs_repetitions == 1
    assert updated.srs_interval_days == 1
    assert updated.mastery == "learning"

    # Second review correct (quality=4)
    updated2 = await vocab_service.record_review(
        topic_id=topic.id, word_id=word.id, user_id=user.id, quality=4
    )
    assert updated2.srs_repetitions == 2
    assert updated2.srs_interval_days == 6


async def test_vs04_srs_review_incorrect_resets_interval(vocab_service, db_session, make_user):
    """
    VS-04: SRS review trả lời sai -> reset interval về 1.
    """
    user = await make_user(email="srs_bad@example.com")
    topic = await vocab_service.create_topic(user_id=user.id, name="SRS Topic")
    
    word_payload = VocabWordCreate(word="obsolete", meaning_vi="cổ xưa")
    word = await vocab_service.create_word(topic_id=topic.id, user_id=user.id, data=word_payload)

    # Advance the word to some learned state manually or via mock
    stmt = select(VocabWord).where(VocabWord.id == word.id)
    res = await db_session.execute(stmt)
    row = res.scalar_one()
    row.srs_repetitions = 3
    row.srs_interval_days = 15
    row.srs_ease = 2.4
    await db_session.flush()

    # Review incorrect (quality=1)
    updated = await vocab_service.record_review(
        topic_id=topic.id, word_id=word.id, user_id=user.id, quality=1
    )
    assert updated.srs_repetitions == 0
    assert updated.srs_interval_days == 1
    assert updated.mastery == "new"


# ---------------------------------------------------------------------------
# VS-05: Delete topic cascades words
# ---------------------------------------------------------------------------

async def test_vs05_delete_topic_cascades_words(vocab_service, db_session, make_user):
    """
    VS-05: Xóa topic -> cascade xóa tất cả words trong topic.
    """
    user = await make_user(email="vocab_cascade@example.com")
    topic = await vocab_service.create_topic(user_id=user.id, name="Delete Me")
    
    word_payload = VocabWordCreate(word="transient", meaning_vi="ngắn ngủi")
    word = await vocab_service.create_word(topic_id=topic.id, user_id=user.id, data=word_payload)

    # Verify both exist
    assert (await db_session.get(VocabTopic, topic.id)) is not None
    assert (await db_session.get(VocabWord, word.id)) is not None

    # Delete topic
    await vocab_service.delete_topic(topic_id=topic.id, user_id=user.id)
    await db_session.flush()

    # Verify both are deleted
    assert (await db_session.get(VocabTopic, topic.id)) is None
    assert (await db_session.get(VocabWord, word.id)) is None
