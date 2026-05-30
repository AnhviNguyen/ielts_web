from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from functools import lru_cache

# Parsed quiz JSON kept in-process (avoid Redis round-trips on 300KB+ payloads).
_MAX_QUIZ_CACHE = 48


@dataclass(frozen=True)
class MockDataIndex:
    mock_tests_by_id: dict[int, Path]
    quizzes_by_id: dict[int, Path]
    mock_test_list: list[dict[str, Any]]


class MockDataService:
    """
    Read-only service that loads quiz/mock-test JSON files from backend/data.
    Returns raw JSON objects using original field names from the data.
    """

    _singleton: "MockDataService | None" = None

    def __init__(self, data_root: Path):
        self._data_root = data_root
        self._index: MockDataIndex | None = None
        self._writing_cache: list[dict[str, Any]] | None = None
        self._quiz_raw_cache: dict[int, dict[str, Any]] = {}

    @classmethod
    def default(cls) -> "MockDataService":
        if cls._singleton is not None:
            return cls._singleton
        backend_root = Path(__file__).resolve().parents[2]
        data_root = backend_root / "data"
        data_root = Path(os.getenv("MOCK_DATA_ROOT", str(data_root)))
        cls._singleton = cls(data_root=data_root)
        return cls._singleton

    def _build_index(self) -> MockDataIndex:
        mock_tests_by_id: dict[int, Path] = {}
        quizzes_by_id: dict[int, Path] = {}
        mock_test_list: list[dict[str, Any]] = []

        # Targeted globs — avoid scanning every JSON under data/ (1400+ files).
        mock_paths = list(self._data_root.glob("**/mock_test_*.json"))
        full_paths = list(self._data_root.glob("**/full_*.json"))
        part_paths = list(self._data_root.glob("**/part_*_*.json"))

        for p in mock_paths:
            name = p.name
            try:
                id_ = int(name.removeprefix("mock_test_").removesuffix(".json"))
            except ValueError:
                continue
            mock_tests_by_id[id_] = p

        for p in full_paths:
            name = p.name
            try:
                id_ = int(name.removeprefix("full_").removesuffix(".json"))
            except ValueError:
                continue
            quizzes_by_id[id_] = p

        for p in part_paths:
            name = p.name
            if not name.startswith("part_"):
                continue
            try:
                id_ = int(name.split("_")[-1].removesuffix(".json"))
            except ValueError:
                continue
            quizzes_by_id[id_] = p

        for _id, file_path in mock_tests_by_id.items():
            try:
                obj = json.loads(file_path.read_text(encoding="utf-8"))
                data = obj.get("data")
                if isinstance(data, dict):
                    mock_test_list.append(data)
            except Exception:
                continue

        mock_test_list.sort(key=lambda x: int(x.get("id", 0) or 0), reverse=True)
        return MockDataIndex(
            mock_tests_by_id=mock_tests_by_id,
            quizzes_by_id=quizzes_by_id,
            mock_test_list=mock_test_list,
        )

    def warmup_index(self) -> int:
        """Build in-memory index (call from startup thread). Returns mock test count."""
        idx = self._ensure_index()
        return len(idx.mock_test_list)

    def invalidate_cache(self) -> None:
        """Drop file-backed caches so admin-written content is visible immediately."""
        self._index = None
        self._writing_cache = None
        self._quiz_raw_cache.clear()
        _load_quiz_json_file.cache_clear()

    def _ensure_index(self) -> MockDataIndex:
        if self._index is None:
            self._index = self._build_index()
        return self._index

    def list_mock_tests(self, skill_id: int | None = None) -> list[dict[str, Any]]:
        idx = self._ensure_index()
        if skill_id is None:
            return idx.mock_test_list
        return [x for x in idx.mock_test_list if str(x.get("skill_id")) == str(skill_id)]

    def get_mock_test_raw(self, mock_test_id: int) -> dict[str, Any] | None:
        idx = self._ensure_index()
        p = idx.mock_tests_by_id.get(mock_test_id)
        if not p:
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def get_quiz_raw(self, quiz_id: int) -> dict[str, Any] | None:
        if quiz_id in self._quiz_raw_cache:
            return self._quiz_raw_cache[quiz_id]
        idx = self._ensure_index()
        p = idx.quizzes_by_id.get(quiz_id)
        if not p:
            return None
        data = _load_quiz_json_file(str(p))
        if len(self._quiz_raw_cache) >= _MAX_QUIZ_CACHE:
            self._quiz_raw_cache.pop(next(iter(self._quiz_raw_cache)))
        self._quiz_raw_cache[quiz_id] = data
        return data

    def get_random_quiz_raw(self, subject: str) -> dict[str, Any] | None:
        idx = self._ensure_index()
        subject_l = subject.lower()
        candidates: list[int] = []
        for qid in idx.quizzes_by_id:
            raw = self.get_quiz_raw(qid)
            title = str((raw or {}).get("data", {}).get("title", "")).lower()
            if subject_l in title:
                candidates.append(qid)
        if not candidates:
            return None
        return self.get_quiz_raw(random.choice(candidates))

    def get_writing_topic_detail(self, topic_id: int) -> dict[str, Any] | None:
        """Return full detail for a writing topic from task_type_1/ or task_type_2/ folder."""
        for sub in ("task_type_1", "task_type_2"):
            candidate = self._data_root / "writing" / sub / f"{topic_id}.json"
            if candidate.exists():
                raw = json.loads(candidate.read_text(encoding="utf-8"))
                return raw
        return None

    def list_writing_topics(self, task_type: int | None = None) -> list[dict[str, Any]]:
        if self._writing_cache is None:
            writing_file = self._data_root / "writing.json"
            if not writing_file.exists():
                self._writing_cache = []
            else:
                payload = json.loads(writing_file.read_text(encoding="utf-8"))
                items = ((payload or {}).get("data") or {}).get("items") or []
                normalized: list[dict[str, Any]] = []
                for item in items:
                    tags = item.get("tags") or []
                    tag_titles = [t.get("title") for t in tags if isinstance(t, dict) and t.get("title")]
                    inferred_task_type = item.get("writing_task_type")
                    tags_text = " ".join(tag_titles).lower()
                    if "task 2" in tags_text:
                        inferred_task_type = 2
                    elif "task 1" in tags_text and inferred_task_type not in (1, 2):
                        inferred_task_type = 1
                    first_question = (item.get("questions") or [{}])[0] or {}
                    normalized.append(
                        {
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "writing_task_type": inferred_task_type,
                            "tags": tag_titles,
                            "prompt_html": first_question.get("content_writing") or "",
                            "prompt_text": first_question.get("title") or "",
                        }
                    )
                self._writing_cache = normalized
        if task_type is None:
            return self._writing_cache
        return [x for x in self._writing_cache if x.get("writing_task_type") == task_type]


@lru_cache(maxsize=64)
def _load_quiz_json_file(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

