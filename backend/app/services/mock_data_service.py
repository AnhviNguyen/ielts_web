from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

    def __init__(self, data_root: Path):
        self._data_root = data_root
        self._index: MockDataIndex | None = None
        self._writing_cache: list[dict[str, Any]] | None = None

    @classmethod
    def default(cls) -> "MockDataService":
        # backend/app/services -> backend/app -> backend
        backend_root = Path(__file__).resolve().parents[2]
        data_root = backend_root / "data"
        # allow overriding for deployments
        data_root = Path(os.getenv("MOCK_DATA_ROOT", str(data_root)))
        return cls(data_root=data_root)

    def _build_index(self) -> MockDataIndex:
        mock_tests_by_id: dict[int, Path] = {}
        quizzes_by_id: dict[int, Path] = {}
        mock_test_list: list[dict[str, Any]] = []

        for p in self._data_root.rglob("*.json"):
            name = p.name
            if name.startswith("mock_test_") and name.endswith(".json"):
                try:
                    id_ = int(name.removeprefix("mock_test_").removesuffix(".json"))
                except ValueError:
                    continue
                mock_tests_by_id[id_] = p
                continue

            # quiz files: full_6354.json, part_1_6427.json, ...
            if name.startswith("full_") and name.endswith(".json"):
                try:
                    id_ = int(name.removeprefix("full_").removesuffix(".json"))
                except ValueError:
                    continue
                quizzes_by_id[id_] = p
                continue

            if name.startswith("part_") and name.endswith(".json"):
                # part_1_6427.json -> quizId=6427
                try:
                    id_ = int(name.split("_")[-1].removesuffix(".json"))
                except ValueError:
                    continue
                quizzes_by_id[id_] = p

        # list = read all mock_test_*.json (lightweight enough)
        for _id, file_path in mock_tests_by_id.items():
            try:
                raw = file_path.read_text(encoding="utf-8")
                obj = json.loads(raw)
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
        idx = self._ensure_index()
        p = idx.quizzes_by_id.get(quiz_id)
        if not p:
            return None
        return json.loads(p.read_text(encoding="utf-8"))

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

