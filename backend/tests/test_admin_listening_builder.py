from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile

from app.schemas import AdminListeningBuilderQuestion
from app.schemas import AdminListeningMockTestBuilderRequest
from app.services.admin_content_service import AdminContentService
from app.services.mock_data_service import MockDataService


@pytest.fixture()
def listening_service(tmp_path, monkeypatch):
    MockDataService._singleton = MockDataService(tmp_path)
    monkeypatch.setenv("MOCK_DATA_ROOT", str(tmp_path))
    return AdminContentService(data_root=tmp_path)


def listening_builder(**overrides):
    data = {
        "title": "Admin Listening Test",
        "book_code": "LISTEN-ADMIN",
        "status": "published",
        "time": 40,
        "thumbnail": "thumb-id",
        "parts": [
            {
                "title": f"Listening Part {idx}",
                "time": 10,
                "file_id": f"audio-{idx}",
                "transcript_text": f"Speaker 1: Transcript section {idx}",
                "listen_from": 0,
                "listen_to": 300,
                "question_sets": [
                    {
                        "title": f"Questions {(idx - 1) * 2 + 1}-{idx * 2}",
                        "template": "TEXT_COMPLETION",
                        "question_type": "SHORT_ANSWER",
                        "description": "Answer the questions.",
                        "questions": [
                            {"text": f"Question {idx}.1", "correct_answer": "alpha", "listen_from": 12},
                            {"text": f"Question {idx}.2", "correct_answer": "beta", "locate_paragraph": 1},
                        ],
                    }
                ],
            }
            for idx in range(1, 5)
        ],
    }
    data.update(overrides)
    return AdminListeningMockTestBuilderRequest(**data)


def test_create_listening_builder_writes_mock_and_quizzes(listening_service):
    result = listening_service.save_listening_mock_test_builder(listening_builder())

    assert result.mock_test["skill_id"] == 2
    assert result.full_quiz["type"] == 10
    assert result.full_quiz["skill_id"] == 2
    assert len(result.full_quiz["parts"]) == 4
    assert result.mock_test["quizzes"]["full"]["question_count"] == 8
    assert set(result.mock_test["quizzes"]) == {"full", "part_1", "part_2", "part_3", "part_4"}
    assert result.full_quiz["parts"][0]["file_id"] == "audio-1"
    assert result.full_quiz["parts"][0]["question_sets"][0]["question_type"] == "SHORT_ANSWER"
    assert result.full_quiz["parts"][0]["questions"][0]["listen_from"] == 12

    folder = Path(listening_service._data_root) / "admin_generated" / "listening" / str(result.mock_test_id)
    assert (folder / f"mock_test_{result.mock_test_id}.json").exists()
    assert (folder / f"full_{result.full_quiz_id}.json").exists()
    assert (folder / f"part_4_{result.part_quiz_ids[3]}.json").exists()


def test_get_listening_builder_round_trips_from_raw_json(listening_service):
    created = listening_service.save_listening_mock_test_builder(listening_builder())

    loaded = listening_service.get_listening_mock_test_builder(created.mock_test_id)

    assert loaded.builder["title"] == "Admin Listening Test"
    assert loaded.builder["parts"][0]["file_id"] == "audio-1"
    assert loaded.builder["parts"][0]["question_sets"][0]["questions"][0]["text"] == "Question 1.1"
    assert loaded.full_quiz_id == created.full_quiz_id


def test_update_listening_builder_keeps_ids_and_creates_backup(listening_service):
    created = listening_service.save_listening_mock_test_builder(listening_builder())
    first_question_id = created.full_quiz["parts"][0]["questions"][0]["id"]
    updated_builder = listening_builder(title="Updated Listening Test")
    updated_builder.parts[0].question_sets[0].questions[0].text = "Updated question"

    updated = listening_service.save_listening_mock_test_builder(updated_builder, mock_test_id=created.mock_test_id)

    assert updated.mock_test_id == created.mock_test_id
    assert updated.full_quiz_id == created.full_quiz_id
    assert updated.full_quiz["parts"][0]["questions"][0]["id"] == first_question_id
    assert updated.full_quiz["parts"][0]["questions"][0]["text"] == "Updated question"
    assert updated.backup_paths


def test_validate_listening_builder_rejects_missing_sets(listening_service):
    builder = listening_builder()
    builder.parts[0].question_sets = []

    with pytest.raises(HTTPException) as exc:
        listening_service.save_listening_mock_test_builder(builder)

    assert exc.value.status_code == 400
    assert "Part 1 needs at least one question set" in exc.value.detail


def test_listening_builder_allows_grouped_inline_gap_questions(listening_service):
    builder = listening_builder()
    builder.parts[0].question_sets[0].template = "INLINE_GAP_TEXT"
    builder.parts[0].question_sets[0].question_type = "GAP_FILLING"
    builder.parts[0].question_sets[0].content = "Write {{gap}}, {{gap}}, and {{gap}}."
    builder.parts[0].question_sets[0].questions = [
        AdminListeningBuilderQuestion(text="Questions 1-3", correct_answer="alpha|beta|gamma", listen_from=12),
    ]

    result = listening_service.save_listening_mock_test_builder(builder)

    first_set = result.full_quiz["parts"][0]["question_sets"][0]
    assert result.mock_test["quizzes"]["full"]["question_count"] == 7
    assert first_set["question_count"] == 1
    assert first_set["questions"][0]["correct_answers"] == ["alpha", "beta", "gamma"]
    assert first_set["content"].count("gap-placeholder") == 3


@pytest.mark.asyncio
async def test_upload_admin_audio_writes_local_asset(listening_service):
    upload = UploadFile(
        filename="section.mp3",
        file=BytesIO(b"fake-audio"),
        headers=Headers({"content-type": "audio/mpeg"}),
    )

    result = await listening_service.save_admin_audio(upload)

    assert result.id
    assert result.url == f"/audio/{result.id}"
    assert (Path(listening_service._data_root) / "assets" / "audio" / f"{result.id}.mp3").read_bytes() == b"fake-audio"


@pytest.mark.asyncio
async def test_upload_admin_audio_rejects_bad_type(listening_service):
    upload = UploadFile(
        filename="section.txt",
        file=BytesIO(b"fake-audio"),
        headers=Headers({"content-type": "text/plain"}),
    )

    with pytest.raises(HTTPException) as exc:
        await listening_service.save_admin_audio(upload)

    assert exc.value.status_code == 400
    assert "Only MP3" in exc.value.detail


@pytest.mark.asyncio
async def test_upload_admin_audio_rejects_empty_file(listening_service):
    upload = UploadFile(
        filename="section.wav",
        file=BytesIO(b""),
        headers=Headers({"content-type": "audio/wav"}),
    )

    with pytest.raises(HTTPException) as exc:
        await listening_service.save_admin_audio(upload)

    assert exc.value.status_code == 400
    assert "empty" in exc.value.detail
