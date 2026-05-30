"""Tests for HistoryService payload validation."""

from app.schemas import HistorySave
from app.services.history_service import HistoryService


class _MockData:
    def get_quiz_raw(self, quiz_id: int):
        if quiz_id != 99:
            return None
        return {
            "data": {
                "type": "9",
                "parts": [
                    {
                        "order": 1,
                        "question_sets": [
                            {
                                "questions": [
                                    {"id": 10, "order": 1, "correct_answer": "yes"},
                                ]
                            }
                        ],
                    }
                ],
            }
        }


def test_validated_payload_recalculates_reading_score():
    svc = HistoryService.__new__(HistoryService)
    svc._mock = _MockData()
    payload = HistorySave(
        quiz_id="99",
        subject="Reading",
        score=999,
        total_questions=1,
        percentage=99.9,
        answers={"10": "yes"},
    )
    out = svc._validated_payload(payload)
    assert out.score == 1
    assert out.total_questions == 1
    assert out.percentage == 100.0


def test_validated_payload_clamps_band_and_duration():
    svc = HistoryService.__new__(HistoryService)
    svc._mock = _MockData()
    payload = HistorySave(
        quiz_id="vocab:1",
        subject="Vocabulary",
        score=5,
        total_questions=3,
        percentage=200.0,
        band_score=15.0,
        duration_seconds=999_999,
    )
    out = svc._validated_payload(payload)
    assert out.score == 3
    assert out.band_score == 9.0
    assert out.duration_seconds == 86_400
