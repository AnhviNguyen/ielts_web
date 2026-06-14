from pathlib import Path

import pytest
from fastapi import HTTPException

from app.schemas import AdminSpeakingMockTestBuilderRequest
from app.services.admin_content_service import AdminContentService
from app.services.mock_data_service import MockDataService


@pytest.fixture()
def speaking_service(tmp_path, monkeypatch):
    MockDataService._singleton = MockDataService(tmp_path)
    monkeypatch.setenv("MOCK_DATA_ROOT", str(tmp_path))
    return AdminContentService(data_root=tmp_path)


def speaking_builder(**overrides):
    data = {
        "title": "Admin Speaking Test",
        "book_code": "SP-ADMIN",
        "status": "published",
        "time": 13,
        "thumbnail": "thumb-id",
        "parts": [
            {
                "title": "Speaking Part 1",
                "time": 5,
                "instruction_html": "<p>Part 1 instruction</p>",
                "questions": [
                    {"title": "Do you work or study?", "time_to_think": 0, "time_limit": 30, "audio_url": ""}
                ],
            },
            {
                "title": "Speaking Part 2",
                "time": 3,
                "instruction_html": "<p>Part 2 instruction</p>",
                "questions": [
                    {
                        "title": "Describe a useful object",
                        "description": "<ul><li>what it is</li></ul>",
                        "time_to_think": 60,
                        "time_limit": 120,
                        "audio_url": "https://example.com/q.mp3",
                    }
                ],
            },
            {
                "title": "Speaking Part 3",
                "time": 5,
                "instruction_html": "<p>Part 3 instruction</p>",
                "questions": [
                    {"title": "Why do people keep old things?", "time_to_think": 0, "time_limit": 45, "audio_url": ""}
                ],
            },
        ],
    }
    data.update(overrides)
    return AdminSpeakingMockTestBuilderRequest(**data)


def test_create_speaking_builder_writes_mock_and_quizzes(speaking_service):
    result = speaking_service.save_speaking_mock_test_builder(speaking_builder())

    assert result.mock_test["skill_id"] == 8
    assert result.full_quiz["type"] == 8
    assert result.full_quiz["skill_id"] == 8
    assert len(result.full_quiz["parts"]) == 3
    assert result.mock_test["quizzes"]["full"]["question_count"] == 3
    assert set(result.mock_test["quizzes"]) == {"full", "part_1", "part_2", "part_2&3", "part_3"}
    assert result.full_quiz["parts"][1]["questions"][0]["description"] == "<ul><li>what it is</li></ul>"
    assert result.full_quiz["parts"][1]["questions"][0]["time_to_think"] == 60
    assert result.full_quiz["parts"][1]["question_sets"][0]["question_type"] == "SPEAKING"

    folder = Path(speaking_service._data_root) / "admin_generated" / "speaking" / str(result.mock_test_id)
    assert (folder / f"mock_test_{result.mock_test_id}.json").exists()
    assert (folder / f"full_{result.full_quiz_id}.json").exists()
    assert (folder / f"part_2&3_{result.part_quiz_ids[2]}.json").exists()


def test_get_speaking_builder_round_trips_from_raw_json(speaking_service):
    created = speaking_service.save_speaking_mock_test_builder(speaking_builder())

    loaded = speaking_service.get_speaking_mock_test_builder(created.mock_test_id)

    assert loaded.builder["title"] == "Admin Speaking Test"
    assert loaded.builder["parts"][0]["questions"][0]["title"] == "Do you work or study?"
    assert loaded.builder["parts"][1]["questions"][0]["audio_url"] == "https://example.com/q.mp3"
    assert loaded.full_quiz_id == created.full_quiz_id


def test_update_speaking_builder_keeps_ids_and_creates_backup(speaking_service):
    created = speaking_service.save_speaking_mock_test_builder(speaking_builder())
    first_question_id = created.full_quiz["parts"][0]["questions"][0]["id"]
    updated_builder = speaking_builder(title="Updated Speaking Test")
    updated_builder.parts[0].questions[0].title = "Are you a student?"

    updated = speaking_service.save_speaking_mock_test_builder(updated_builder, mock_test_id=created.mock_test_id)

    assert updated.mock_test_id == created.mock_test_id
    assert updated.full_quiz_id == created.full_quiz_id
    assert updated.full_quiz["parts"][0]["questions"][0]["id"] == first_question_id
    assert updated.full_quiz["parts"][0]["questions"][0]["title"] == "Are you a student?"
    assert updated.backup_paths


def test_validate_speaking_builder_rejects_missing_questions(speaking_service):
    builder = speaking_builder()
    builder.parts[2].questions = []

    with pytest.raises(HTTPException) as exc:
        speaking_service.save_speaking_mock_test_builder(builder)

    assert exc.value.status_code == 400
    assert "Part 3 needs at least one question" in exc.value.detail
