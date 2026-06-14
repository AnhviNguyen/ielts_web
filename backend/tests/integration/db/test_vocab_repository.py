"""
tests/integration/db/test_vocab_repository.py
───────────────────────────────────────────────
Integration tests cho VocabRepository — Topics và Words CRUD, SRS queue.

Bao phủ:
  VCB-01  create_topic() → topic persist với user_id
  VCB-02  get_topic() → tìm thấy topic đúng user, không thấy của user khác
  VCB-03  list_topics_with_counts() → trả về danh sách + word count đúng
  VCB-04  update_topic() → name/sort_order được cập nhật
  VCB-05  delete_topic() → topic bị xóa, words cascade
  VCB-06  create_word() → word persist trong topic
  VCB-07  create_words_bulk() → nhiều words được tạo cùng lúc
  VCB-08  list_words() → trả về đúng words trong topic, sort DESC created_at
  VCB-09  get_word() → tìm thấy word theo id + topic_id
  VCB-10  get_word() sai topic_id → None (isolation giữa topics)
  VCB-11  update_word() → fields được cập nhật
  VCB-12  delete_word() → word bị xóa
  VCB-13  search_words() → tìm theo word text
  VCB-14  search_words() → tìm theo meaning_vi
  VCB-15  list_study_queue() → chỉ trả về words null/quá hạn SRS
  VCB-16  get_user_stats() → đếm đúng mastery groups
  VCB-17  count_topics() → đúng số lượng topics của user
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# VCB-01: create_topic() → persist với user_id
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb01_create_topic_persisted(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "Business English", sort_order=1)

    assert topic.id is not None
    assert topic.user_id == user.id
    assert topic.name == "Business English"
    assert topic.sort_order == 1


# ---------------------------------------------------------------------------
# VCB-02: get_topic() — tìm của user mình, không thấy của user khác
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb02_get_topic_user_isolation(make_user, vocab_repo):
    user_a = await make_user()
    user_b = await make_user()
    topic = await vocab_repo.create_topic(user_a.id, "Topic A")

    # user_a tìm thấy
    found = await vocab_repo.get_topic(topic.id, user_a.id)
    assert found is not None
    assert found.name == "Topic A"

    # user_b không tìm thấy (isolation)
    not_found = await vocab_repo.get_topic(topic.id, user_b.id)
    assert not_found is None


# ---------------------------------------------------------------------------
# VCB-03: list_topics_with_counts() → danh sách + word count
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb03_list_topics_with_word_counts(make_user, vocab_repo):
    user = await make_user()
    topic1 = await vocab_repo.create_topic(user.id, "Topic 1")
    topic2 = await vocab_repo.create_topic(user.id, "Topic 2")

    # Thêm 2 words vào topic1, 0 vào topic2
    await vocab_repo.create_words_bulk(topic1.id, [
        {"word": "hello", "meaning_vi": "xin chào"},
        {"word": "world", "meaning_vi": "thế giới"},
    ])

    result = await vocab_repo.list_topics_with_counts(user.id)

    # Kết quả phải có 2 topics
    assert len(result) == 2
    counts = {t.name: cnt for t, cnt in result}
    assert counts["Topic 1"] == 2
    assert counts["Topic 2"] == 0


# ---------------------------------------------------------------------------
# VCB-04: update_topic() → name và sort_order được cập nhật
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb04_update_topic_fields(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "Old Name", sort_order=0)

    updated = await vocab_repo.update_topic(topic, name="New Name", sort_order=5)

    assert updated.name == "New Name"
    assert updated.sort_order == 5


# ---------------------------------------------------------------------------
# VCB-05: delete_topic() → topic bị xóa
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb05_delete_topic_removes_it(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "To Delete")

    await vocab_repo.delete_topic(topic)

    found = await vocab_repo.get_topic(topic.id, user.id)
    assert found is None


# ---------------------------------------------------------------------------
# VCB-06: create_word() → word persist trong topic
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb06_create_word_persisted(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "Words")

    word = await vocab_repo.create_word(topic.id, {
        "word": "tenacious",
        "meaning_vi": "kiên trì",
        "example": "She is tenacious in her studies.",
        "mastery": "new",
    })

    assert word.id is not None
    assert word.topic_id == topic.id
    assert word.word == "tenacious"
    assert word.mastery == "new"


# ---------------------------------------------------------------------------
# VCB-07: create_words_bulk() → nhiều words cùng lúc
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb07_create_words_bulk(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "Bulk Topic")

    words = await vocab_repo.create_words_bulk(topic.id, [
        {"word": "apple", "meaning_vi": "táo"},
        {"word": "banana", "meaning_vi": "chuối"},
        {"word": "cherry", "meaning_vi": "anh đào"},
    ])

    assert len(words) == 3
    assert {w.word for w in words} == {"apple", "banana", "cherry"}


# ---------------------------------------------------------------------------
# VCB-08: list_words() → đúng words trong topic
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb08_list_words_returns_topic_words(make_user, vocab_repo):
    user = await make_user()
    topic1 = await vocab_repo.create_topic(user.id, "T1")
    topic2 = await vocab_repo.create_topic(user.id, "T2")

    await vocab_repo.create_word(topic1.id, {"word": "t1-word"})
    await vocab_repo.create_word(topic2.id, {"word": "t2-word"})

    words = await vocab_repo.list_words(topic1.id)

    assert len(words) == 1
    assert words[0].word == "t1-word"


# ---------------------------------------------------------------------------
# VCB-09: get_word() → tìm đúng theo id + topic_id
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb09_get_word_found(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "T")
    word = await vocab_repo.create_word(topic.id, {"word": "ephemeral"})

    found = await vocab_repo.get_word(word.id, topic.id)

    assert found is not None
    assert found.word == "ephemeral"


# ---------------------------------------------------------------------------
# VCB-10: get_word() sai topic_id → None
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb10_get_word_wrong_topic_returns_none(make_user, vocab_repo):
    user = await make_user()
    topic1 = await vocab_repo.create_topic(user.id, "T1")
    topic2 = await vocab_repo.create_topic(user.id, "T2")
    word = await vocab_repo.create_word(topic1.id, {"word": "isolated"})

    # Thử lấy word của topic1 bằng topic2.id → None
    result = await vocab_repo.get_word(word.id, topic2.id)
    assert result is None


# ---------------------------------------------------------------------------
# VCB-11: update_word() → fields được cập nhật
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb11_update_word_fields(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "T")
    word = await vocab_repo.create_word(topic.id, {
        "word": "resilient",
        "mastery": "new",
    })

    updated = await vocab_repo.update_word(word, {
        "mastery": "learning",
        "meaning_vi": "kiên cường",
    })

    assert updated.mastery == "learning"
    assert updated.meaning_vi == "kiên cường"


# ---------------------------------------------------------------------------
# VCB-12: delete_word() → word bị xóa
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb12_delete_word_removes_it(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "T")
    word = await vocab_repo.create_word(topic.id, {"word": "transient"})

    await vocab_repo.delete_word(word)

    found = await vocab_repo.get_word(word.id, topic.id)
    assert found is None


# ---------------------------------------------------------------------------
# VCB-13 + VCB-14: search_words() — tìm theo word text và meaning_vi
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb13_search_words_by_word_text(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "Search")
    await vocab_repo.create_words_bulk(topic.id, [
        {"word": "eloquent", "meaning_vi": "hùng biện"},
        {"word": "eloquence", "meaning_vi": "tài hùng biện"},
        {"word": "persistent", "meaning_vi": "kiên trì"},
    ])

    results = await vocab_repo.search_words(user.id, "eloqu")

    assert len(results) == 2
    assert all("eloqu" in w.word.lower() for w in results)


@pytest.mark.asyncio
async def test_vcb14_search_words_by_meaning_vi(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "Search VI")
    await vocab_repo.create_words_bulk(topic.id, [
        {"word": "brave", "meaning_vi": "dũng cảm"},
        {"word": "bold", "meaning_vi": "táo bạo, dũng cảm"},
        {"word": "timid", "meaning_vi": "nhút nhát"},
    ])

    results = await vocab_repo.search_words(user.id, "dũng cảm")

    assert len(results) == 2


# ---------------------------------------------------------------------------
# VCB-15: list_study_queue() → chỉ words null/quá hạn SRS
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb15_list_study_queue_srs_filter(make_user, vocab_repo, db_session):
    from app.db.models import VocabWord

    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "SRS")

    # Word 1: srs_next_review_at = None (new word → due)
    w1 = await vocab_repo.create_word(topic.id, {"word": "new-word"})

    # Word 2: srs_next_review_at quá hạn (trong quá khứ → due)
    w2 = await vocab_repo.create_word(topic.id, {"word": "overdue-word"})
    w2.srs_next_review_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.add(w2)

    # Word 3: srs_next_review_at trong tương lai (chưa đến hạn → NOT due)
    w3 = await vocab_repo.create_word(topic.id, {"word": "future-word"})
    w3.srs_next_review_at = datetime.now(timezone.utc) + timedelta(days=1)
    db_session.add(w3)
    await db_session.flush()

    queue = await vocab_repo.list_study_queue(topic.id)

    word_texts = {w.word for w in queue}
    assert "new-word" in word_texts
    assert "overdue-word" in word_texts
    assert "future-word" not in word_texts


# ---------------------------------------------------------------------------
# VCB-16: get_user_stats() → đếm đúng mastery groups
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb16_get_user_stats_mastery_counts(make_user, vocab_repo):
    user = await make_user()
    topic = await vocab_repo.create_topic(user.id, "Stats")

    await vocab_repo.create_words_bulk(topic.id, [
        {"word": "w1", "mastery": "new"},
        {"word": "w2", "mastery": "new"},
        {"word": "w3", "mastery": "learning"},
        {"word": "w4", "mastery": "mastered"},
        {"word": "w5", "mastery": "mastered"},
        {"word": "w6", "mastery": "mastered"},
    ])

    stats = await vocab_repo.get_user_stats(user.id)

    assert stats["total"] == 6
    assert stats["new"] == 2
    assert stats["learning"] == 1
    assert stats["mastered"] == 3


# ---------------------------------------------------------------------------
# VCB-17: count_topics() → đúng số lượng topics của user
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vcb17_count_topics_per_user(make_user, vocab_repo):
    user_a = await make_user()
    user_b = await make_user()

    await vocab_repo.create_topic(user_a.id, "A1")
    await vocab_repo.create_topic(user_a.id, "A2")
    await vocab_repo.create_topic(user_b.id, "B1")

    count_a = await vocab_repo.count_topics(user_a.id)
    count_b = await vocab_repo.count_topics(user_b.id)

    assert count_a == 2
    assert count_b == 1
