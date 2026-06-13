from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.utils.content_visibility import is_public_content

from functools import lru_cache

# Parsed quiz JSON kept in-process (avoid Redis round-trips on 300KB+ payloads).
_MAX_QUIZ_CACHE = int(os.getenv("MOCK_QUIZ_CACHE_SIZE", "128"))
_WARM_QUIZ_COUNT = int(os.getenv("MOCK_QUIZ_WARM_COUNT", "24"))


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
        self.warmup_popular_quizzes()
        return len(idx.mock_test_list)

    def warmup_popular_quizzes(self, limit: int = _WARM_QUIZ_COUNT) -> int:
        """Preload quiz JSON for the first visible mock tests into process memory."""
        if limit <= 0:
            return 0
        warmed = 0
        seen: set[int] = set()
        for item in self._ensure_index().mock_test_list:
            quizzes = item.get("quizzes") or {}
            for meta in quizzes.values():
                if not isinstance(meta, dict):
                    continue
                quiz_id = meta.get("id")
                if not isinstance(quiz_id, int) or quiz_id in seen:
                    continue
                seen.add(quiz_id)
                if self.get_quiz_raw(quiz_id) is not None:
                    warmed += 1
                if warmed >= limit:
                    return warmed
        return warmed

    def invalidate_cache(self) -> None:
        """Drop file-backed caches so admin-written content is visible immediately."""
        self._index = None
        self._writing_cache = None
        self._quiz_raw_cache.clear()
        clear_quiz_option_caches()
        from app.services.full_exam_service import FullExamService
        FullExamService.invalidate_sets_cache()

    def _ensure_index(self) -> MockDataIndex:
        if self._index is None:
            self._index = self._build_index()
        return self._index

    def list_mock_tests(self, skill_id: int | None = None, *, visible_only: bool = True) -> list[dict[str, Any]]:
        idx = self._ensure_index()
        items = idx.mock_test_list
        if skill_id is not None:
            items = [x for x in items if str(x.get("skill_id")) == str(skill_id)]
        if visible_only:
            items = [x for x in items if is_public_content(x)]
        return items

    def list_mock_test_cards(self, skill_id: int | None = None, *, visible_only: bool = True) -> list[dict[str, Any]]:
        items = self.list_mock_tests(skill_id=skill_id, visible_only=visible_only)
        return [_mock_test_list_item(x) for x in items]

    def get_mock_test_raw(self, mock_test_id: int, *, visible_only: bool = True) -> dict[str, Any] | None:
        idx = self._ensure_index()
        p = idx.mock_tests_by_id.get(mock_test_id)
        if not p:
            return None
        raw = json.loads(p.read_text(encoding="utf-8"))
        if visible_only:
            data = raw.get("data") if isinstance(raw, dict) else None
            if isinstance(data, dict) and not is_public_content(data):
                return None
        return raw

    def get_quiz_raw(self, quiz_id: int, *, visible_only: bool = True) -> dict[str, Any] | None:
        if quiz_id in self._quiz_raw_cache:
            data = self._quiz_raw_cache[quiz_id]
            if visible_only:
                inner = data.get("data", data) if isinstance(data, dict) else {}
                if isinstance(inner, dict) and not is_public_content(inner):
                    return None
            return data
        idx = self._ensure_index()
        p = idx.quizzes_by_id.get(quiz_id)
        if not p:
            return None
        data = _load_quiz_json_file(str(p))
        data = _enrich_quiz_options_from_backup(data, p)
        if len(self._quiz_raw_cache) >= _MAX_QUIZ_CACHE:
            self._quiz_raw_cache.pop(next(iter(self._quiz_raw_cache)))
        self._quiz_raw_cache[quiz_id] = data
        if visible_only:
            inner = data.get("data", data) if isinstance(data, dict) else {}
            if isinstance(inner, dict) and not is_public_content(inner):
                return None
        return data

    def get_random_quiz_raw(self, subject: str) -> dict[str, Any] | None:
        idx = self._ensure_index()
        subject_l = subject.lower()
        candidates: list[int] = []
        for qid in idx.quizzes_by_id:
            raw = self.get_quiz_raw(qid, visible_only=True)
            title = str((raw or {}).get("data", {}).get("title", "")).lower()
            if subject_l in title:
                candidates.append(qid)
        if not candidates:
            return None
        return self.get_quiz_raw(random.choice(candidates), visible_only=True)

    def get_writing_topic_detail(self, topic_id: int, *, visible_only: bool = True) -> dict[str, Any] | None:
        """Return full detail for a writing topic from task_type_1/ or task_type_2/ folder."""
        for sub in ("task_type_1", "task_type_2"):
            candidate = self._data_root / "writing" / sub / f"{topic_id}.json"
            if candidate.exists():
                raw = json.loads(candidate.read_text(encoding="utf-8"))
                if visible_only:
                    data = raw.get("data") if isinstance(raw, dict) else None
                    if isinstance(data, dict) and not is_public_content(data):
                        return None
                return raw
        return None

    def _writing_list_files(self) -> list[Path]:
        """All writing *list* files (root + per-task-type pages), excluding per-topic detail files."""
        files: list[Path] = []
        root_file = self._data_root / "writing.json"
        if root_file.exists():
            files.append(root_file)
        for sub in ("task_type_1", "task_type_2"):
            sub_dir = self._data_root / "writing" / sub
            if sub_dir.is_dir():
                files.extend(sorted(sub_dir.glob("writing_task_*.json")))
        return files

    def list_writing_topics(self, task_type: int | None = None, *, visible_only: bool = True) -> list[dict[str, Any]]:
        if self._writing_cache is None:
            normalized: list[dict[str, Any]] = []
            seen_ids: set[Any] = set()
            for list_file in self._writing_list_files():
                try:
                    payload = json.loads(list_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                items = ((payload or {}).get("data") or {}).get("items") or []
                for item in items:
                    topic_id = item.get("id")
                    if topic_id in seen_ids:
                        continue
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
                            "id": topic_id,
                            "title": item.get("title"),
                            "writing_task_type": inferred_task_type,
                            "tags": tag_titles,
                            "prompt_html": first_question.get("content_writing") or "",
                            "prompt_text": first_question.get("title") or "",
                            "status": item.get("status", "published"),
                            "is_public": item.get("is_public", True),
                        }
                    )
                    seen_ids.add(topic_id)
            self._writing_cache = normalized
        result = self._writing_cache
        if visible_only:
            result = [x for x in result if is_public_content(x)]
        if task_type is not None:
            result = [x for x in result if x.get("writing_task_type") == task_type]
        return result

    def list_writing_sets(self) -> list[dict[str, Any]]:
        """Pair Task 1 + Task 2 topics into practice sets (same index, sorted by id)."""
        t1 = sorted(self.list_writing_topics(task_type=1), key=lambda x: int(x.get("id") or 0))
        t2 = sorted(self.list_writing_topics(task_type=2), key=lambda x: int(x.get("id") or 0))
        n = min(len(t1), len(t2))
        sets: list[dict[str, Any]] = []
        for i in range(n):
            a, b = t1[i], t2[i]
            sets.append(
                {
                    "id": i + 1,
                    "title": f"Bộ đề Writing #{i + 1}",
                    "task1_topic_id": a.get("id"),
                    "task2_topic_id": b.get("id"),
                    "task1_title": a.get("title") or "",
                    "task2_title": b.get("title") or "",
                    "task1_tags": a.get("tags") or [],
                    "task2_tags": b.get("tags") or [],
                }
            )
        return sets

    def find_writing_set_for_topic(self, topic_id: int) -> dict[str, Any] | None:
        for item in self.list_writing_sets():
            if topic_id == item.get("task1_topic_id"):
                return {**item, "start_step": 1}
            if topic_id == item.get("task2_topic_id"):
                return {**item, "start_step": 2}
        return None


_donor_options_cache: dict[str, list[dict[str, str]]] | None = None


def _get_donor_options_by_text() -> dict[str, list[dict[str, str]]]:
    global _donor_options_cache
    if _donor_options_cache is None:
        _donor_options_cache = _build_donor_options_by_text(_quiz_data_root())
    return _donor_options_cache


def clear_quiz_option_caches() -> None:
    global _donor_options_cache
    _donor_options_cache = None
    _load_quiz_json_file.cache_clear()


@lru_cache(maxsize=64)
def _load_quiz_json_file(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _option_text(opt: Any) -> str:
    if not isinstance(opt, dict):
        return ""
    return str(opt.get("text") or "").strip()


def _options_incomplete(options: Any) -> bool:
    if not isinstance(options, list) or not options:
        return True
    return any(not _option_text(opt) for opt in options if isinstance(opt, dict))


def _backup_options_usable(backup_opts: Any) -> bool:
    if not isinstance(backup_opts, list) or not backup_opts:
        return False
    return any(_option_text(opt) for opt in backup_opts if isinstance(opt, dict))


def _copy_options_with_text(source: list[Any]) -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    for opt in source:
        if not isinstance(opt, dict):
            continue
        key = str(opt.get("option") or "").strip()
        text = _option_text(opt)
        if key:
            copied.append({"option": key, "text": text})
    return copied


def _collect_questions_by_id(payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        return out
    for part in data.get("parts") or []:
        if not isinstance(part, dict):
            continue
        for q in part.get("questions") or []:
            if isinstance(q, dict) and isinstance(q.get("id"), int):
                out[q["id"]] = q
        for qs in part.get("question_sets") or []:
            if not isinstance(qs, dict):
                continue
            for q in qs.get("questions") or []:
                if isinstance(q, dict) and isinstance(q.get("id"), int):
                    out[q["id"]] = q
    return out


def _collect_questions_by_order_text(payload: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    out: dict[tuple[int, str], dict[str, Any]] = {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        return out
    for part in data.get("parts") or []:
        if not isinstance(part, dict):
            continue
        for q in part.get("questions") or []:
            if not isinstance(q, dict):
                continue
            order = q.get("order")
            text = str(q.get("text") or "").strip()
            if isinstance(order, int) and text:
                out[(order, text)] = q
        for qs in part.get("question_sets") or []:
            if not isinstance(qs, dict):
                continue
            for q in qs.get("questions") or []:
                if not isinstance(q, dict):
                    continue
                order = q.get("order")
                text = str(q.get("text") or "").strip()
                if isinstance(order, int) and text:
                    out[(order, text)] = q
    return out


def _resolve_backup_question(
    question: dict[str, Any],
    *,
    backup_by_id: dict[int, dict[str, Any]],
    backup_by_order_text: dict[tuple[int, str], dict[str, Any]],
) -> dict[str, Any] | None:
    qid = question.get("id")
    if isinstance(qid, int) and qid in backup_by_id:
        return backup_by_id[qid]
    order = question.get("order")
    text = str(question.get("text") or "").strip()
    if isinstance(order, int) and text:
        return backup_by_order_text.get((order, text))
    return None


def _build_donor_options_by_text(data_root: Path) -> dict[str, list[dict[str, str]]]:
    donors: dict[str, list[dict[str, str]]] = {}
    candidates = sorted(data_root.glob("**/part_*_*.json")) + sorted(data_root.glob("**/full_*.json"))
    for file_path in candidates:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if not isinstance(data, dict):
            continue
        for part in data.get("parts") or []:
            if not isinstance(part, dict):
                continue
            for qs in part.get("question_sets") or []:
                if not isinstance(qs, dict):
                    continue
                for q in qs.get("questions") or []:
                    if not isinstance(q, dict):
                        continue
                    text = str(q.get("text") or "").strip()
                    opts = q.get("options")
                    if not text or not _backup_options_usable(opts) or _options_incomplete(opts):
                        continue
                    donors[text] = _copy_options_with_text(opts)
    return donors


def _apply_backup_options(
    live: dict[str, Any],
    *,
    backup_by_id: dict[int, dict[str, Any]],
    backup_by_order_text: dict[tuple[int, str], dict[str, Any]],
    donor_by_text: dict[str, list[dict[str, str]]] | None = None,
) -> bool:
    changed = False
    data = live.get("data") if isinstance(live.get("data"), dict) else live
    if not isinstance(data, dict):
        return False

    def repair_question(question: dict[str, Any]) -> bool:
        if not isinstance(question, dict):
            return False
        if not _options_incomplete(question.get("options")):
            return False
        backup_q = _resolve_backup_question(
            question,
            backup_by_id=backup_by_id,
            backup_by_order_text=backup_by_order_text,
        )
        backup_opts = backup_q.get("options") if backup_q else None
        if not _backup_options_usable(backup_opts):
            text = str(question.get("text") or "").strip()
            backup_opts = (donor_by_text or {}).get(text)
        if not _backup_options_usable(backup_opts):
            return False
        question["options"] = _copy_options_with_text(backup_opts)
        return True

    for part in data.get("parts") or []:
        if not isinstance(part, dict):
            continue
        for q in part.get("questions") or []:
            if repair_question(q):
                changed = True
        for qs in part.get("question_sets") or []:
            if not isinstance(qs, dict):
                continue
            for q in qs.get("questions") or []:
                if repair_question(q):
                    changed = True
            if _options_incomplete(qs.get("options")):
                first_with_text = next(
                    (
                        q.get("options")
                        for q in qs.get("questions") or []
                        if isinstance(q, dict) and _backup_options_usable(q.get("options"))
                    ),
                    None,
                )
                if isinstance(first_with_text, list) and first_with_text:
                    qs["options"] = _copy_options_with_text(first_with_text)
                    changed = True
    return changed


def _quiz_data_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def _enrich_quiz_options_from_backup(payload: dict[str, Any], file_path: Path) -> dict[str, Any]:
    bak_files = sorted(file_path.parent.glob(f"{file_path.name}.*.bak"), reverse=True)
    backup_by_id: dict[int, dict[str, Any]] = {}
    backup_by_order_text: dict[tuple[int, str], dict[str, Any]] = {}
    if bak_files:
        try:
            backup = json.loads(bak_files[0].read_text(encoding="utf-8"))
            backup_by_id = _collect_questions_by_id(backup)
            backup_by_order_text = _collect_questions_by_order_text(backup)
        except (json.JSONDecodeError, OSError):
            pass
    donor_by_text = _get_donor_options_by_text()
    if not backup_by_id and not backup_by_order_text and not donor_by_text:
        return payload
    if not _apply_backup_options(
        payload,
        backup_by_id=backup_by_id,
        backup_by_order_text=backup_by_order_text,
        donor_by_text=donor_by_text,
    ):
        return payload
    return payload


def repair_quiz_options_from_backup_file(
    file_path: Path,
    *,
    donor_by_text: dict[str, list[dict[str, str]]] | None = None,
) -> bool:
    """Persist option text repairs from sibling .bak into a quiz JSON file."""
    if not file_path.exists():
        return False
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    bak_files = sorted(file_path.parent.glob(f"{file_path.name}.*.bak"), reverse=True)
    backup_by_id: dict[int, dict[str, Any]] = {}
    backup_by_order_text: dict[tuple[int, str], dict[str, Any]] = {}
    if bak_files:
        try:
            backup = json.loads(bak_files[0].read_text(encoding="utf-8"))
            backup_by_id = _collect_questions_by_id(backup)
            backup_by_order_text = _collect_questions_by_order_text(backup)
        except (json.JSONDecodeError, OSError):
            pass
    donors = donor_by_text if donor_by_text is not None else _build_donor_options_by_text(_quiz_data_root())
    if not _apply_backup_options(
        payload,
        backup_by_id=backup_by_id,
        backup_by_order_text=backup_by_order_text,
        donor_by_text=donors,
    ):
        return False
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    clear_quiz_option_caches()
    return True


def repair_all_quiz_options_from_backups(data_root: Path | None = None) -> int:
    root = data_root or _quiz_data_root()
    donor_by_text = _build_donor_options_by_text(root)
    repaired = 0
    candidates = sorted(root.glob("**/part_*_*.json")) + sorted(root.glob("**/full_*.json"))
    for file_path in candidates:
        if repair_quiz_options_from_backup_file(file_path, donor_by_text=donor_by_text):
            repaired += 1
    return repaired


def _quiz_meta(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    out = {
        "id": meta.get("id"),
        "title": meta.get("title"),
        "time": meta.get("time"),
        "question_count": meta.get("question_count"),
    }
    return {k: v for k, v in out.items() if v not in (None, "")}


def _mock_test_list_item(item: dict[str, Any]) -> dict[str, Any]:
    quizzes = item.get("quizzes") or {}
    compact_quizzes = {
        key: _quiz_meta(meta)
        for key, meta in quizzes.items()
        if key == "full" or str(key).startswith("part_")
    }
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "skill_id": item.get("skill_id"),
        "book_code": item.get("book_code"),
        "thumbnail": item.get("thumbnail"),
        "status": item.get("status"),
        "quizzes": compact_quizzes,
    }

