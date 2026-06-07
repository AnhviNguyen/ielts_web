"""Full IELTS mock exam set catalog (4 skills bundled)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.services.mock_data_service import MockDataService

# IELTS computer-delivered approximate section times (minutes)
DEFAULT_TIMERS = {
    "reading_minutes": 60,
    "listening_minutes": 30,
    "writing_task1_minutes": 20,
    "writing_task2_minutes": 40,
    "speaking_minutes": 15,
}


class FullExamService:
    _sets_cache: dict[int, list[dict[str, Any]]] = {}

    def __init__(self, mock: MockDataService | None = None) -> None:
        self._mock = mock or MockDataService.default()

    def list_sets(self, limit: int = 30) -> list[dict[str, Any]]:
        if limit in self._sets_cache:
            return self._sets_cache[limit]
        idx = self._mock._ensure_index()
        reading_map: dict[tuple[str, str], dict] = {}
        listening_map: dict[tuple[str, str], dict] = {}

        for _mt_id, path in idx.mock_tests_by_id.items():
            try:
                import json

                raw = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            data = raw.get("data") or {}
            skill_id = data.get("skill_id")
            title = str(data.get("title") or "")
            m = re.search(r"Test\s+(\d+)", title, re.I)
            if not m:
                continue
            test_num = m.group(1)
            book_raw = self._book_from_path(path)
            if not book_raw:
                continue
            book = self._normalize_book_label(book_raw)
            key = (book, test_num)
            full = (data.get("quizzes") or {}).get("full") or {}
            meta_seo = full.get("meta_seo") or {}
            thumbnail = data.get("thumbnail") or meta_seo.get("image")
            entry = {
                "mock_test_id": data.get("id"),
                "quiz_id": full.get("id"),
                "time_minutes": full.get("time"),
                "question_count": full.get("question_count"),
                "title": title,
                "thumbnail": thumbnail,
                "book_code": data.get("book_code"),
            }
            if skill_id == 1 and entry.get("quiz_id"):
                reading_map[key] = entry
            elif skill_id == 2 and entry.get("quiz_id"):
                listening_map[key] = entry

        writing_t1 = self._mock.list_writing_topics(task_type=1)
        writing_t2 = self._mock.list_writing_topics(task_type=2)
        speaking_pool = self._list_speaking(idx)

        sets: list[dict[str, Any]] = []
        for key in sorted(reading_map.keys(), reverse=True):
            if key not in listening_map:
                continue
            book, test_num = key
            r, l = reading_map[key], listening_map[key]
            set_id = f"{book.lower().replace(' ', '-')}-test-{test_num}"
            w1, w2 = self._pick_writing_topics(writing_t1, writing_t2, set_id)
            speaking = self._pick_speaking(speaking_pool, set_id)
            sets.append(
                {
                    "id": set_id,
                    "title": f"{book} — Full Mock Test {test_num}",
                    "book": book,
                    "test_number": int(test_num),
                    "thumbnail": r.get("thumbnail") or l.get("thumbnail"),
                    "book_code": r.get("book_code") or l.get("book_code"),
                    "reading_quiz_id": r["quiz_id"],
                    "listening_quiz_id": l["quiz_id"],
                    "writing_task1_topic_id": w1,
                    "writing_task2_topic_id": w2,
                    "speaking_quiz_id": speaking.get("quiz_id"),
                    "timers": {
                        **DEFAULT_TIMERS,
                        "reading_minutes": r.get("time_minutes") or DEFAULT_TIMERS["reading_minutes"],
                        "listening_minutes": l.get("time_minutes") or DEFAULT_TIMERS["listening_minutes"],
                        "speaking_minutes": speaking.get("time_minutes") or DEFAULT_TIMERS["speaking_minutes"],
                    },
                    "total_minutes": (
                        (r.get("time_minutes") or 60)
                        + (l.get("time_minutes") or 30)
                        + DEFAULT_TIMERS["writing_task1_minutes"]
                        + DEFAULT_TIMERS["writing_task2_minutes"]
                        + (speaking.get("time_minutes") or 15)
                    ),
                }
            )
            if len(sets) >= limit:
                break
        self._sets_cache[limit] = sets
        return sets

    def get_set(self, set_id: str) -> dict[str, Any] | None:
        for item in self.list_sets(limit=200):
            if item["id"] == set_id:
                return item
        return None

    @staticmethod
    def _book_from_path(path: Path) -> str | None:
        for part in path.parts:
            if part.startswith("Orange Test"):
                return part
        return None

    @staticmethod
    def _normalize_book_label(raw: str) -> str:
        """Orange Test 15 (Đã có YouPass Builder) 🔥🔥 → Orange Test 15"""
        m = re.match(r"(Orange Test\s+\d+)", raw, re.I)
        if m:
            return m.group(1).strip()
        cleaned = re.sub(r"\s*\([^)]*\)\s*", " ", raw)
        cleaned = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]+", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def _stable_index(seed: str, size: int) -> int:
        if size <= 0:
            return 0
        return sum(ord(c) for c in seed) % size

    @classmethod
    def _pick_writing_topics(
        cls,
        t1: list[dict[str, Any]],
        t2: list[dict[str, Any]],
        set_id: str,
    ) -> tuple[int | None, int | None]:
        w1 = t1[cls._stable_index(set_id + ":t1", len(t1))]["id"] if t1 else None
        w2 = t2[cls._stable_index(set_id + ":t2", len(t2))]["id"] if t2 else None
        return w1, w2

    @staticmethod
    def _list_speaking(idx) -> list[dict[str, Any]]:
        import json

        out: list[dict[str, Any]] = []
        for _mt_id, path in idx.mock_tests_by_id.items():
            if "speaking" not in str(path).lower():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8")).get("data") or {}
            except Exception:
                continue
            if data.get("skill_id") != 8:
                continue
            full = (data.get("quizzes") or {}).get("full") or {}
            if full.get("id"):
                out.append(
                    {
                        "mock_test_id": data.get("id"),
                        "quiz_id": full.get("id"),
                        "time_minutes": full.get("time"),
                        "title": data.get("title"),
                    }
                )
        return out

    @classmethod
    def _pick_speaking(cls, pool: list[dict[str, Any]], set_id: str) -> dict[str, Any]:
        if not pool:
            return {}
        return pool[cls._stable_index(set_id + ":sp", len(pool))]
