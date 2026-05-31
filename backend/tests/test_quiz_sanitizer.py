from app.utils.quiz_sanitizer import sanitize_quiz_payload, strip_quiz_answers


def test_strip_quiz_answers_removes_keys():
    raw = {
        "id": 1,
        "parts": [
            {
                "question_sets": [
                    {
                        "questions": [
                            {
                                "id": 10,
                                "text": "Q1",
                                "correct_answer": "secret",
                                "correct_answers": ["A"],
                                "explain": "because",
                                "listen_from": "0:12",
                            }
                        ]
                    }
                ]
            }
        ],
    }
    out = strip_quiz_answers(raw)
    q = out["parts"][0]["question_sets"][0]["questions"][0]
    assert q["text"] == "Q1"
    assert "correct_answer" not in q
    assert "correct_answers" not in q
    assert "explain" not in q
    assert "listen_from" not in q


def test_sanitize_quiz_payload_wraps_data():
    raw = {"code": 0, "data": {"id": 2, "correct_answer": "x"}}
    out = sanitize_quiz_payload(raw)
    assert out["data"]["id"] == 2
    assert "correct_answer" not in out["data"]
