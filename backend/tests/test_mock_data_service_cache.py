import json
from pathlib import Path

from app.services.mock_data_service import MockDataService


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"code": 0, "message": "", "data": data}), encoding="utf-8")


def test_invalidate_cache_exposes_new_mock_tests(tmp_path):
    service = MockDataService(tmp_path)
    _write_json(tmp_path / "mock_test_1.json", {"id": 1, "title": "Old", "skill_id": 1})

    assert [item["id"] for item in service.list_mock_tests(skill_id=1)] == [1]

    _write_json(tmp_path / "admin_generated" / "reading" / "2" / "mock_test_2.json", {"id": 2, "title": "New", "skill_id": 1})
    assert [item["id"] for item in service.list_mock_tests(skill_id=1)] == [1]

    service.invalidate_cache()

    assert [item["id"] for item in service.list_mock_tests(skill_id=1)] == [2, 1]


def test_invalidate_cache_refreshes_cached_quiz_file(tmp_path):
    service = MockDataService(tmp_path)
    quiz_path = tmp_path / "admin_generated" / "reading" / "2" / "full_201.json"
    _write_json(quiz_path, {"id": 201, "title": "Before", "parts": []})

    assert service.get_quiz_raw(201)["data"]["title"] == "Before"

    _write_json(quiz_path, {"id": 201, "title": "After", "parts": []})
    assert service.get_quiz_raw(201)["data"]["title"] == "Before"

    service.invalidate_cache()

    assert service.get_quiz_raw(201)["data"]["title"] == "After"


def test_list_mock_test_cards_returns_compact_quiz_metadata(tmp_path):
    service = MockDataService(tmp_path)
    _write_json(
        tmp_path / "mock_test_1.json",
        {
            "id": 1,
            "title": "Reading Test",
            "skill_id": 1,
            "book_code": "OT15",
            "thumbnail": "thumb-id",
            "heavy_field": "not-needed",
            "quizzes": {
                "full": {"id": 101, "title": "Full", "time": 60, "question_count": 40, "answers": [1]},
                "part_1": {"id": 102, "time": 20, "question_count": 13, "answers": [2]},
            },
        },
    )

    card = service.list_mock_test_cards(skill_id=1)[0]

    assert card["id"] == 1
    assert card["quizzes"]["full"] == {"id": 101, "title": "Full", "time": 60, "question_count": 40}
    assert "heavy_field" not in card
    assert "answers" not in card["quizzes"]["part_1"]
