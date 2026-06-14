"""
tests/integration/db/test_profile_repository.py
─────────────────────────────────────────────────
Integration tests cho ProfileRepository + streak/XP logic.

Bao phủ:
  PRF-01  create_empty() → profile được tạo với user_id đúng, defaults OK
  PRF-02  get_by_user_id() → tìm thấy profile
  PRF-03  get_by_user_id() user không có profile → None
  PRF-04  update() → các field được cập nhật, None fields bị bỏ qua
  PRF-05  update_streak_and_xp() — last_activity=null → streak=1, last_activity=today
  PRF-06  update_streak_and_xp() — last_activity=today → streak không tăng
  PRF-07  update_streak_and_xp() — xp_to_add > 0 → XP được cộng
  PRF-08  update_streak_and_xp() — last_activity > 1 ngày trước → streak reset = 1
  PRF-09  ensure_speaking_eval_allowed() — dưới giới hạn → pass
  PRF-10  ensure_speaking_eval_allowed() — chạm giới hạn → HTTP 429
  PRF-11  increment_speaking_eval() → daily_speaking_used tăng lên 1
  PRF-12  ensure_tutor_chat_allowed() — chạm giới hạn tháng → HTTP 429
  PRF-13  update() chỉ thay đổi field được pass (None = không thay đổi)
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import HTTPException

from app.core.limits import DAILY_SPEAKING_EVAL_MAX, MONTHLY_TUTOR_QUESTIONS_MAX


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# PRF-01: create_empty() → profile được tạo với defaults
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf01_create_empty_profile_defaults(make_user, make_profile):
    user = await make_user()
    profile = await make_profile(user.id)

    assert profile.id is not None
    assert profile.user_id == user.id
    assert profile.streak == 0
    assert profile.xp == 0
    assert profile.full_name is None
    assert profile.placement_status == "pending"


# ---------------------------------------------------------------------------
# PRF-02: get_by_user_id() → tìm thấy profile
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf02_get_by_user_id_returns_profile(make_user, make_profile, profile_repo):
    user = await make_user()
    await make_profile(user.id, full_name="Nguyen Van A")

    found = await profile_repo.get_by_user_id(user.id)

    assert found is not None
    assert found.user_id == user.id
    assert found.full_name == "Nguyen Van A"


# ---------------------------------------------------------------------------
# PRF-03: get_by_user_id() user không có profile → None
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf03_get_by_user_id_no_profile_returns_none(profile_repo):
    result = await profile_repo.get_by_user_id(99999999)
    assert result is None


# ---------------------------------------------------------------------------
# PRF-04: update() → các field được cập nhật
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf04_update_profile_fields(make_user, make_profile, profile_repo):
    user = await make_user()
    profile = await make_profile(user.id, full_name="Old Name")

    updated = await profile_repo.update(
        profile,
        full_name="New Name",
        phone="0912345678",
        bio="IELTS learner",
        avatar_url="https://example.com/avatar.jpg",
        target_band=7.5,
        exam_date=date(2026, 12, 1),
    )

    assert updated.full_name == "New Name"
    assert updated.phone == "0912345678"
    assert updated.bio == "IELTS learner"
    assert updated.target_band == 7.5
    assert updated.exam_date == date(2026, 12, 1)


# ---------------------------------------------------------------------------
# PRF-05: update_streak_and_xp() — lần đầu → streak=1, last_activity=today
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf05_streak_starts_at_1_on_first_activity(make_user, make_profile, profile_repo):
    user = await make_user()
    await make_profile(user.id)

    # Đảm bảo last_activity_date là None (default)
    profile = await profile_repo.get_by_user_id(user.id)
    assert profile.last_activity_date is None

    updated = await profile_repo.update_streak_and_xp(user.id)

    assert updated.streak == 1
    assert updated.last_activity_date == date.today()


# ---------------------------------------------------------------------------
# PRF-06: update_streak_and_xp() — active hôm nay → streak không tăng
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf06_streak_does_not_double_count_same_day(make_user, make_profile, profile_repo):
    user = await make_user()
    await make_profile(user.id)

    # Lần 1: streak = 1
    await profile_repo.update_streak_and_xp(user.id)
    # Lần 2 cùng ngày: streak vẫn = 1
    updated = await profile_repo.update_streak_and_xp(user.id)

    assert updated.streak == 1


# ---------------------------------------------------------------------------
# PRF-07: update_streak_and_xp() — xp_to_add > 0 → XP được cộng
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf07_xp_added_correctly(make_user, make_profile, profile_repo):
    user = await make_user()
    await make_profile(user.id)

    updated = await profile_repo.update_streak_and_xp(user.id, xp_to_add=50)
    assert updated.xp == 50

    # Cộng thêm lần 2 cùng ngày
    updated2 = await profile_repo.update_streak_and_xp(user.id, xp_to_add=30)
    assert updated2.xp == 80


# ---------------------------------------------------------------------------
# PRF-08: update_streak_and_xp() — bỏ ngày → streak reset = 1
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf08_streak_resets_when_day_skipped(make_user, make_profile, profile_repo, db_session):
    from app.db.models import UserProfile
    from sqlalchemy import select

    user = await make_user()
    await make_profile(user.id)

    # Giả lập last_activity_date = 3 ngày trước (streak bị gián đoạn)
    profile = await profile_repo.get_by_user_id(user.id)
    profile.streak = 5
    profile.last_activity_date = date.today() - timedelta(days=3)
    db_session.add(profile)
    await db_session.flush()

    updated = await profile_repo.update_streak_and_xp(user.id)

    assert updated.streak == 1   # reset về 1


# ---------------------------------------------------------------------------
# PRF-09: ensure_speaking_eval_allowed() — dưới giới hạn → pass (không raise)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf09_speaking_eval_allowed_under_limit(make_user, make_profile, profile_repo):
    user = await make_user()
    await make_profile(user.id)

    # Không raise
    profile = await profile_repo.ensure_speaking_eval_allowed(user.id)
    assert profile is not None


# ---------------------------------------------------------------------------
# PRF-10: ensure_speaking_eval_allowed() — chạm giới hạn → HTTP 429
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf10_speaking_eval_blocked_at_limit(make_user, make_profile, profile_repo, db_session):
    user = await make_user()
    await make_profile(user.id)

    # Set daily_speaking_used = MAX và last_activity = today (tránh reset)
    profile = await profile_repo.get_by_user_id(user.id)
    profile.daily_speaking_used = DAILY_SPEAKING_EVAL_MAX
    profile.last_activity_date = date.today()
    db_session.add(profile)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        await profile_repo.ensure_speaking_eval_allowed(user.id)

    assert exc.value.status_code == 429
    assert str(DAILY_SPEAKING_EVAL_MAX) in exc.value.detail


# ---------------------------------------------------------------------------
# PRF-11: increment_speaking_eval() → daily_speaking_used tăng lên 1
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf11_increment_speaking_eval_increments_counter(make_user, make_profile, profile_repo):
    user = await make_user()
    await make_profile(user.id)

    await profile_repo.increment_speaking_eval(user.id)

    profile = await profile_repo.get_by_user_id(user.id)
    assert profile.daily_speaking_used == 1


# ---------------------------------------------------------------------------
# PRF-12: ensure_tutor_chat_allowed() — chạm giới hạn tháng → HTTP 429
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf12_tutor_chat_blocked_at_monthly_limit(make_user, make_profile, profile_repo, db_session):
    user = await make_user()
    await make_profile(user.id)

    profile = await profile_repo.get_by_user_id(user.id)
    profile.tutor_questions_used_month = MONTHLY_TUTOR_QUESTIONS_MAX
    profile.last_activity_date = date.today()
    db_session.add(profile)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        await profile_repo.ensure_tutor_chat_allowed(user.id)

    assert exc.value.status_code == 429


# ---------------------------------------------------------------------------
# PRF-13: update() với None fields → không ghi đè field cũ
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prf13_update_none_fields_not_overwritten(make_user, make_profile, profile_repo):
    user = await make_user()
    profile = await make_profile(user.id, full_name="Keep This Name")

    # full_name=None → không thay đổi
    updated = await profile_repo.update(
        profile,
        full_name=None,
        phone=None,
        bio="New bio only",
        avatar_url=None,
    )

    assert updated.full_name == "Keep This Name"   # giữ nguyên
    assert updated.bio == "New bio only"           # chỉ bio thay đổi
