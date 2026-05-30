"""Tests for server-side quiz scoring."""

from app.services.practice_service import PracticeService

SAMPLE_QUIZ = {
    "type": "9",
    "parts": [
        {
            "order": 1,
            "question_sets": [
                {
                    "questions": [
                        {"id": 1, "order": 1, "correct_answer": "Paris"},
                        {"id": 2, "order": 2, "correct_answers": ["A", "B"]},
                    ]
                }
            ],
        }
    ],
}


def test_score_from_quiz_answers_all_correct():
    answers = {"1": "Paris", "2": ["A", "B"]}
    score, total, pct, band = PracticeService.score_from_quiz_answers(SAMPLE_QUIZ, answers)
    assert score == 2
    assert total == 2
    assert pct == 100.0
    assert band >= 0


def test_score_from_quiz_answers_client_cheat_rejected():
    answers = {"1": "wrong", "2": ["A", "B"]}
    score, total, pct, _band = PracticeService.score_from_quiz_answers(SAMPLE_QUIZ, answers)
    assert score == 1
    assert total == 2
    assert pct == 50.0
