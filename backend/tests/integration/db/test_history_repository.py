"""
tests/integration/db/test_history_repository.py
─────────────────────────────────────────────────
Integration tests cho HistoryRepository.

Bao phủ:
  HIS-01  create() → History entry được persist với id
  HIS-02  get_paginated() → trả về đúng số lượng và tổng count
  HIS-03  get_paginated() với subject filter → chỉ trả về subject đó
  HIS-04  get_paginated() — phân trang đúng (page 2)
  HIS-05  get_paginated() — sắp xếp mới nhất trước (completed_at DESC)
  HIS-06  get_completed_quiz_ids() → danh sách quiz_id distinct
  HIS-07  get_completed_quiz_ids() với subject filter
  HIS-08  get_by_id_for_user() → tìm thấy đúng record của user
  HIS-09  get_by_id_for_user() của user khác → None (isolation)
  HIS-10  archive_completed_before() → rows được chuyển sang history_archive
  HIS-11  archive_completed_before() trả về số rows đã archive
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helper: tạo History entry nhanh
# ---------------------------------------------------------------------------

async def _create_history(history_repo, user_id: int, **kwargs):
    defaults = {
        "quiz_id": None,
        "subject": "Reading",
        "score": 8,
        "total_questions": 10,
        "percentage": 80.0,
        "answers": {"q1": "A"},
        "band_score": 6.5,
        "mode": "practice",
        "duration_seconds": 300,
    }
    defaults.update(kwargs)
    return await history_repo.create(user_id=user_id, **defaults)


# ---------------------------------------------------------------------------
# HIS-01: create() → entry persist với id
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his01_create_history_entry_persisted(make_user, history_repo):
    user = await make_user()
    entry = await _create_history(history_repo, user.id, quiz_id="quiz-001")

    assert entry.id is not None
    assert entry.user_id == user.id
    assert entry.quiz_id == "quiz-001"
    assert entry.subject == "Reading"
    assert entry.band_score == 6.5


# ---------------------------------------------------------------------------
# HIS-02: get_paginated() → đúng số lượng + total count
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his02_get_paginated_returns_correct_count(make_user, history_repo):
    user = await make_user()

    for i in range(5):
        await _create_history(history_repo, user.id, quiz_id=f"quiz-{i}")

    items, total = await history_repo.get_paginated(user.id, page=1, page_size=3)

    assert total == 5
    assert len(items) == 3


# ---------------------------------------------------------------------------
# HIS-03: get_paginated() với subject filter
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his03_get_paginated_subject_filter(make_user, history_repo):
    user = await make_user()

    await _create_history(history_repo, user.id, subject="Reading")
    await _create_history(history_repo, user.id, subject="Reading")
    await _create_history(history_repo, user.id, subject="Listening")

    items, total = await history_repo.get_paginated(
        user.id, page=1, page_size=10, subject="Reading"
    )

    assert total == 2
    assert all(h.subject == "Reading" for h in items)


# ---------------------------------------------------------------------------
# HIS-04: get_paginated() phân trang đúng (page 2)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his04_get_paginated_page_2(make_user, history_repo):
    user = await make_user()

    for i in range(7):
        await _create_history(history_repo, user.id, quiz_id=f"pg-{i}")

    page1, total = await history_repo.get_paginated(user.id, page=1, page_size=5)
    page2, _ = await history_repo.get_paginated(user.id, page=2, page_size=5)

    assert total == 7
    assert len(page1) == 5
    assert len(page2) == 2
    # Không có item trùng giữa 2 trang
    ids_p1 = {h.id for h in page1}
    ids_p2 = {h.id for h in page2}
    assert ids_p1.isdisjoint(ids_p2)


# ---------------------------------------------------------------------------
# HIS-05: get_paginated() — sắp xếp mới nhất trước
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his05_get_paginated_ordered_newest_first(make_user, history_repo, db_session):
    from app.db.models import History

    user = await make_user()
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    # Tạo 3 entries với completed_at khác nhau
    for i in range(3):
        entry = await _create_history(history_repo, user.id, quiz_id=f"ord-{i}")
        entry.completed_at = base_time + timedelta(hours=i)
        db_session.add(entry)
    await db_session.flush()

    items, _ = await history_repo.get_paginated(user.id, page=1, page_size=10)

    # Mới nhất trước: items[0].completed_at >= items[1].completed_at
    assert items[0].completed_at >= items[1].completed_at
    assert items[1].completed_at >= items[2].completed_at


# ---------------------------------------------------------------------------
# HIS-06: get_completed_quiz_ids() → distinct quiz_ids
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his06_get_completed_quiz_ids_distinct(make_user, history_repo):
    user = await make_user()

    # Cùng quiz_id làm 2 lần → chỉ xuất hiện 1 lần
    await _create_history(history_repo, user.id, quiz_id="q-001")
    await _create_history(history_repo, user.id, quiz_id="q-001")
    await _create_history(history_repo, user.id, quiz_id="q-002")

    ids = await history_repo.get_completed_quiz_ids(user.id)

    assert sorted(ids) == ["q-001", "q-002"]


# ---------------------------------------------------------------------------
# HIS-07: get_completed_quiz_ids() với subject filter
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his07_get_completed_quiz_ids_subject_filter(make_user, history_repo):
    user = await make_user()

    await _create_history(history_repo, user.id, quiz_id="r-001", subject="Reading")
    await _create_history(history_repo, user.id, quiz_id="l-001", subject="Listening")

    reading_ids = await history_repo.get_completed_quiz_ids(user.id, subject="Reading")

    assert "r-001" in reading_ids
    assert "l-001" not in reading_ids


# ---------------------------------------------------------------------------
# HIS-08: get_by_id_for_user() → đúng record của user
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his08_get_by_id_for_user_returns_record(make_user, history_repo):
    user = await make_user()
    entry = await _create_history(history_repo, user.id, quiz_id="mine")

    found = await history_repo.get_by_id_for_user(entry.id, user.id)

    assert found is not None
    assert found.id == entry.id
    assert found.quiz_id == "mine"


# ---------------------------------------------------------------------------
# HIS-09: get_by_id_for_user() của user khác → None (cross-user isolation)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his09_get_by_id_for_user_isolation(make_user, history_repo):
    user_a = await make_user()
    user_b = await make_user()
    entry = await _create_history(history_repo, user_a.id, quiz_id="user-a-only")

    # user_b cố lấy history của user_a → None
    result = await history_repo.get_by_id_for_user(entry.id, user_b.id)

    assert result is None


# ---------------------------------------------------------------------------
# HIS-10 + HIS-11: archive_completed_before() → rows chuyển sang archive
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_his10_archive_moves_rows_and_returns_count(make_user, history_repo, db_session):
    from sqlalchemy import select
    from app.db.models import HistoryArchive, History

    user = await make_user()
    cutoff = datetime(2026, 1, 15, tzinfo=timezone.utc)
    old_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    new_time = datetime(2026, 2, 1, tzinfo=timezone.utc)

    # Tạo 2 entries cũ (< cutoff) và 1 entry mới
    old1 = await _create_history(history_repo, user.id, quiz_id="old-1")
    old2 = await _create_history(history_repo, user.id, quiz_id="old-2")
    new1 = await _create_history(history_repo, user.id, quiz_id="new-1")

    # Gán completed_at bằng tay (DB default là now())
    old1.completed_at = old_time
    old2.completed_at = old_time
    new1.completed_at = new_time
    db_session.add_all([old1, old2, new1])
    await db_session.flush()

    archived_count = await history_repo.archive_completed_before(cutoff)

    assert archived_count == 2  # HIS-11: đúng số lượng

    # HIS-10: rows cũ không còn trong History
    remaining = await db_session.execute(
        select(History).where(History.user_id == user.id)
    )
    remaining_ids = {h.id for h in remaining.scalars().all()}
    assert old1.id not in remaining_ids
    assert old2.id not in remaining_ids
    assert new1.id in remaining_ids  # row mới vẫn còn

    # HIS-10: rows cũ xuất hiện trong HistoryArchive
    archive_res = await db_session.execute(
        select(HistoryArchive).where(HistoryArchive.user_id == user.id)
    )
    archived_ids = {h.id for h in archive_res.scalars().all()}
    assert old1.id in archived_ids
    assert old2.id in archived_ids
