"""Tests for content visibility helper and MockDataService filtering."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-32chars")
os.environ.setdefault("AUTH_HTTPONLY_REFRESH", "false")
os.environ.setdefault("ENVIRONMENT", "development")

from app.utils.content_visibility import is_public_content


# ── is_public_content unit tests ────────────────────────────────────────

class TestIsPublicContent:
    """Verify helper handles all legacy status variants."""

    def test_published_string(self):
        assert is_public_content({"status": "published"}) is True

    def test_draft_visible(self):
        """Draft items remain visible to users (by design)."""
        assert is_public_content({"status": "draft"}) is True

    def test_status_int_1(self):
        assert is_public_content({"status": 1}) is True

    def test_no_status_field(self):
        assert is_public_content({}) is True

    def test_none_status(self):
        assert is_public_content({"status": None}) is True

    def test_archived_string(self):
        assert is_public_content({"status": "archived"}) is False

    def test_archived_mixed_case(self):
        assert is_public_content({"status": "Archived"}) is False

    def test_status_zero_int(self):
        assert is_public_content({"status": 0}) is False

    def test_status_zero_string(self):
        assert is_public_content({"status": "0"}) is False

    def test_status_false(self):
        assert is_public_content({"status": False}) is False

    def test_is_public_false(self):
        assert is_public_content({"status": "published", "is_public": False}) is False

    def test_is_public_true(self):
        assert is_public_content({"status": "published", "is_public": True}) is True

    def test_is_public_false_overrides_published(self):
        assert is_public_content({"status": "published", "is_public": False}) is False


# ── MockDataService integration tests ──────────────────────────────────

@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    """Create a minimal data directory with one published and one archived mock test."""
    # Published mock test
    published = {
        "code": 0,
        "data": {
            "id": 1,
            "title": "Published Reading Test 1",
            "skill_id": 1,
            "status": "published",
            "book_code": "Test",
            "quizzes": {"full": {"id": 100, "time": 60, "question_count": 40}},
        },
    }
    # Archived mock test
    archived = {
        "code": 0,
        "data": {
            "id": 2,
            "title": "Archived Reading Test 2",
            "skill_id": 1,
            "status": "archived",
            "book_code": "Test",
            "quizzes": {"full": {"id": 200, "time": 60, "question_count": 40}},
        },
    }
    # Status 0 mock test (legacy int)
    legacy = {
        "code": 0,
        "data": {
            "id": 3,
            "title": "Legacy Hidden Test 3",
            "skill_id": 1,
            "status": 0,
            "book_code": "Test",
            "quizzes": {"full": {"id": 300, "time": 60, "question_count": 40}},
        },
    }

    for name, payload in [
        ("mock_test_1.json", published),
        ("mock_test_2.json", archived),
        ("mock_test_3.json", legacy),
    ]:
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")

    # Published quiz
    quiz_pub = {"data": {"id": 100, "title": "Quiz 100", "status": "published", "parts": []}}
    (tmp_path / "full_100.json").write_text(json.dumps(quiz_pub), encoding="utf-8")

    # Archived quiz
    quiz_arch = {"data": {"id": 200, "title": "Quiz 200", "status": "archived", "parts": []}}
    (tmp_path / "full_200.json").write_text(json.dumps(quiz_arch), encoding="utf-8")

    # Writing topic list
    writing_list = {
        "code": 0,
        "data": {
            "total": 2,
            "items": [
                {"id": 10, "title": "Public Topic", "status": "published", "is_public": True, "writing_task_type": 1, "tags": [], "questions": [{}]},
                {"id": 11, "title": "Hidden Topic", "status": "archived", "is_public": False, "writing_task_type": 1, "tags": [], "questions": [{}]},
            ],
        },
    }
    (tmp_path / "writing.json").write_text(json.dumps(writing_list), encoding="utf-8")

    # Detail files
    detail_dir = tmp_path / "writing" / "task_type_1"
    detail_dir.mkdir(parents=True, exist_ok=True)

    topic_10 = {"code": 0, "data": {"id": 10, "title": "Public Topic", "status": "published", "is_public": True, "writing_task_type": 1}}
    topic_11 = {"code": 0, "data": {"id": 11, "title": "Hidden Topic", "status": "archived", "is_public": False, "writing_task_type": 1}}

    (detail_dir / "10.json").write_text(json.dumps(topic_10), encoding="utf-8")
    (detail_dir / "11.json").write_text(json.dumps(topic_11), encoding="utf-8")

    return tmp_path


@pytest.fixture()
def mock_svc(data_dir: Path):
    from app.services.mock_data_service import MockDataService

    svc = MockDataService(data_root=data_dir)
    return svc


class TestMockDataServiceVisibility:
    def test_list_mock_tests_visible_only_true(self, mock_svc):
        items = mock_svc.list_mock_tests(visible_only=True)
        ids = [x["id"] for x in items]
        assert 1 in ids
        assert 2 not in ids  # archived
        assert 3 not in ids  # status=0

    def test_list_mock_tests_visible_only_false(self, mock_svc):
        items = mock_svc.list_mock_tests(visible_only=False)
        ids = [x["id"] for x in items]
        assert 1 in ids
        assert 2 in ids  # admin sees archived
        assert 3 in ids  # admin sees status=0

    def test_get_mock_test_raw_archived_hidden(self, mock_svc):
        assert mock_svc.get_mock_test_raw(2, visible_only=True) is None

    def test_get_mock_test_raw_archived_admin(self, mock_svc):
        raw = mock_svc.get_mock_test_raw(2, visible_only=False)
        assert raw is not None
        assert raw["data"]["id"] == 2

    def test_get_quiz_raw_archived_hidden(self, mock_svc):
        assert mock_svc.get_quiz_raw(200, visible_only=True) is None

    def test_get_quiz_raw_published_visible(self, mock_svc):
        raw = mock_svc.get_quiz_raw(100, visible_only=True)
        assert raw is not None

    def test_get_quiz_raw_archived_admin(self, mock_svc):
        raw = mock_svc.get_quiz_raw(200, visible_only=False)
        assert raw is not None

    def test_list_writing_topics_visible_only(self, mock_svc):
        items = mock_svc.list_writing_topics(visible_only=True)
        ids = [x["id"] for x in items]
        assert 10 in ids
        assert 11 not in ids  # archived + is_public=false

    def test_list_writing_topics_admin(self, mock_svc):
        items = mock_svc.list_writing_topics(visible_only=False)
        ids = [x["id"] for x in items]
        assert 10 in ids
        assert 11 in ids  # admin sees hidden topics

    def test_list_mock_test_cards_default_filters(self, mock_svc):
        """Default call (no visible_only arg) should filter archived."""
        cards = mock_svc.list_mock_test_cards()
        ids = [x["id"] for x in cards]
        assert 1 in ids
        assert 2 not in ids


@pytest.fixture()
def admin_svc(data_dir: Path, monkeypatch, mock_svc):
    from app.services.admin_content_service import AdminContentService
    from app.services.mock_data_service import MockDataService
    monkeypatch.setattr(MockDataService, "default", lambda: mock_svc)

    svc = AdminContentService()
    svc._data_root = data_dir
    return svc


class TestAdminContentServiceArchiveRestore:
    """Verify archive and restore flows across AdminContentService."""

    def test_archive_and_restore_mock_test(self, admin_svc, mock_svc):
        # Initial check
        assert mock_svc.get_mock_test_raw(1, visible_only=True) is not None
        assert mock_svc.get_quiz_raw(100, visible_only=True) is not None

        # Archive
        admin_svc.archive_mock_test(1)
        assert mock_svc.get_mock_test_raw(1, visible_only=True) is None
        assert mock_svc.get_quiz_raw(100, visible_only=True) is None

        # Restore
        admin_svc.restore_mock_test(1)
        assert mock_svc.get_mock_test_raw(1, visible_only=True) is not None
        assert mock_svc.get_quiz_raw(100, visible_only=True) is not None

    def test_archive_and_restore_quiz(self, admin_svc, mock_svc):
        # Initial
        assert mock_svc.get_quiz_raw(100, visible_only=True) is not None

        # Archive
        admin_svc.archive_quiz(100)
        assert mock_svc.get_quiz_raw(100, visible_only=True) is None

        # Restore
        admin_svc.restore_quiz(100)
        assert mock_svc.get_quiz_raw(100, visible_only=True) is not None

    def test_archive_and_restore_writing_topic(self, admin_svc, mock_svc):
        # Initial
        assert mock_svc.get_writing_topic_detail(10, visible_only=True) is not None

        # Archive
        admin_svc.archive_writing_topic(10)
        assert mock_svc.get_writing_topic_detail(10, visible_only=True) is None

        # Restore
        admin_svc.restore_writing_topic(10)
        assert mock_svc.get_writing_topic_detail(10, visible_only=True) is not None

