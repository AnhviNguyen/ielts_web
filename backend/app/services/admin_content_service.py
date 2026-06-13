from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.storage import get_storage
from app.core.upload import MAX_ADMIN_IMAGE_SIZE, read_upload_limited
from app.schemas import (
    AdminContentListResponse,
    AdminContentResponse,
    AdminContentWriteResponse,
    AdminImageUploadResponse,
    AdminListeningMockTestBuilderRequest,
    AdminListeningMockTestBuilderResponse,
    AdminReadingMockTestBuilderRequest,
    AdminReadingMockTestBuilderResponse,
    AdminSpeakingMockTestBuilderRequest,
    AdminSpeakingMockTestBuilderResponse,
)
from app.services.mock_data_service import MockDataService


class AdminContentService:
    TEMPLATE_INLINE_GAP = "INLINE_GAP_TEXT"
    TEMPLATE_TF_NG = "TF_NG"
    TEMPLATE_YN_NG = "YN_NG"
    TEMPLATE_SINGLE_CHOICE = "SINGLE_CHOICE"
    TEMPLATE_MULTI_CHOICE = "MULTIPLE_CHOICE_MANY"
    TEMPLATE_MATCHING = "MATCHING_SELECT"
    TEMPLATE_TEXT = "TEXT_COMPLETION"
    MATCHING_TYPES = {
        "MATCHING",
        "MATCHING_FEATURES",
        "MATCHING_INFO",
        "MATCHING_HEADING",
        "MATCHING_HEADINGS",
        "MATCHING_ENDINGS",
        "TABLE_SELECTION",
    }
    TEXT_INPUT_TYPES = {"SHORT_ANSWER", "SENTENCE_COMPLETION", "SUMMARY_COMPLETION", "NOTE_COMPLETION", "MAP_DIAGRAM_LABEL"}
    OPTION_BANK_START = "<!-- admin-option-bank:start -->"
    OPTION_BANK_END = "<!-- admin-option-bank:end -->"

    def __init__(self, data_root: Path | None = None) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        default_root = backend_root / "data"
        self._data_root = Path(data_root or os.getenv("MOCK_DATA_ROOT", str(default_root)))

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content file not found")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Invalid JSON file: {path.name}") from exc

    def _backup_and_write(self, path: Path, payload: dict[str, Any]) -> str | None:
        path.parent.mkdir(parents=True, exist_ok=True)
        backup_path: Path | None = None
        if path.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            backup_path = path.with_name(f"{path.name}.{stamp}.bak")
            shutil.copy2(path, backup_path)
        tmp_path = path.with_name(f"{path.name}.tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)
        MockDataService.default().invalidate_cache()
        return str(backup_path.relative_to(self._data_root)) if backup_path else None

    @staticmethod
    def _wrapper(data: dict[str, Any]) -> dict[str, Any]:
        if "data" in data and isinstance(data["data"], dict):
            return data
        return {"code": 0, "message": "", "data": data}

    @staticmethod
    def _data(raw: dict[str, Any]) -> dict[str, Any]:
        data = raw.get("data")
        return data if isinstance(data, dict) else raw

    async def save_admin_image(self, upload: UploadFile) -> AdminImageUploadResponse:
        suffix = Path(upload.filename or "").suffix.lower()
        content_type = (upload.content_type or "").lower()
        allowed_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
        allowed_types = {"image/png", "image/jpeg", "image/webp"}
        if suffix not in allowed_suffixes or content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PNG, JPG, JPEG, and WEBP images are supported",
            )
        content = await read_upload_limited(upload, MAX_ADMIN_IMAGE_SIZE)
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is empty")
        image_id = uuid.uuid4().hex
        backend = settings.STORAGE_BACKEND.lower()
        if backend == "cloudinary":
            key = f"images/{image_id}{suffix}"
            get_storage().put_bytes(key, content, content_type)
            return AdminImageUploadResponse(id=image_id, url=f"/images/{image_id}")
        if backend == "s3":
            key = f"assets/images/{image_id}{suffix}"
            get_storage().put_bytes(key, content, content_type)
            return AdminImageUploadResponse(id=image_id, url=f"/images/{image_id}")

        image_dir = self._data_root / "assets" / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        path = image_dir / f"{image_id}{suffix}"
        path.write_bytes(content)
        return AdminImageUploadResponse(id=image_id, url=f"/images/{image_id}")

    async def save_admin_audio(self, upload: UploadFile) -> AdminImageUploadResponse:
        suffix = Path(upload.filename or "").suffix.lower()
        content_type = (upload.content_type or "").lower()
        allowed_suffixes = {".mp3", ".m4a", ".ogg", ".wav"}
        allowed_types = {
            "audio/mpeg",
            "audio/mp3",
            "audio/mp4",
            "audio/x-m4a",
            "audio/ogg",
            "audio/wav",
            "audio/x-wav",
            "audio/wave",
        }
        if suffix not in allowed_suffixes or content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only MP3, M4A, OGG, and WAV audio files are supported",
            )
        content = await upload.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty")
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file must be 100MB or smaller")
        audio_id = uuid.uuid4().hex
        backend = settings.STORAGE_BACKEND.lower()
        if backend == "cloudinary":
            key = f"audio/{audio_id}{suffix}"
            get_storage().put_bytes(key, content, content_type)
            return AdminImageUploadResponse(id=audio_id, url=f"/audio/{audio_id}")
        if backend == "s3":
            key = f"assets/audio/{audio_id}{suffix}"
            get_storage().put_bytes(key, content, content_type)
            return AdminImageUploadResponse(id=audio_id, url=f"/audio/{audio_id}")

        audio_dir = self._data_root / "assets" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        path = audio_dir / f"{audio_id}{suffix}"
        path.write_bytes(content)
        return AdminImageUploadResponse(id=audio_id, url=f"/audio/{audio_id}")

    def _writing_file(self) -> Path:
        return self._data_root / "writing.json"

    def _writing_detail_path(self, topic_id: int, task_type: int | None) -> Path:
        folder = "task_type_2" if int(task_type or 1) == 2 else "task_type_1"
        return self._data_root / "writing" / folder / f"{topic_id}.json"

    def _writing_list_payload(self) -> dict[str, Any]:
        path = self._writing_file()
        if not path.exists():
            return {"code": 0, "message": "", "data": {"total": 0, "page": 1, "page_size": 300, "items": []}}
        return self._read_json(path)

    def list_writing_topics(
        self,
        *,
        task_type: int | None = None,
        status_filter: str | None = None,
        q: str | None = None,
    ) -> AdminContentListResponse:
        items = MockDataService.default().list_writing_topics(task_type=task_type, visible_only=False)
        raw_list = ((self._writing_list_payload().get("data") or {}).get("items") or [])
        status_by_id = {item.get("id"): item.get("status") for item in raw_list if isinstance(item, dict)}
        enriched = []
        q_l = (q or "").strip().lower()
        for item in items:
            row = dict(item)
            row["status"] = status_by_id.get(row.get("id"), "published")
            if status_filter and str(row.get("status")) != status_filter:
                continue
            if q_l and q_l not in str(row.get("title", "")).lower():
                continue
            enriched.append(row)
        return AdminContentListResponse(items=enriched, total=len(enriched))

    def get_writing_topic(self, topic_id: int) -> AdminContentResponse:
        raw = MockDataService.default().get_writing_topic_detail(topic_id, visible_only=False)
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing topic not found")
        return AdminContentResponse(item=self._data(raw), raw_json=raw)

    def _upsert_writing_list_item(self, item: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
        payload = self._writing_list_payload()
        data = payload.setdefault("data", {})
        items = data.setdefault("items", [])
        topic_id = item.get("id")
        for idx, existing in enumerate(items):
            if isinstance(existing, dict) and existing.get("id") == topic_id:
                existing.update({
                    "id": topic_id,
                    "title": item.get("title", existing.get("title")),
                    "status": item.get("status", existing.get("status", "published")),
                    "thumbnail": item.get("thumbnail", existing.get("thumbnail", "")),
                    "tags": item.get("tags", existing.get("tags", [])),
                    "questions": item.get("questions", existing.get("questions", [])),
                    "writing_task_type": item.get("writing_task_type", existing.get("writing_task_type")),
                    "is_public": item.get("is_public", existing.get("is_public", True)),
                })
                items[idx] = existing
                break
        else:
            items.insert(0, item)
        data["total"] = len(items)
        return payload, self._backup_and_write(self._writing_file(), payload)

    def create_writing_topic(self, raw_json: dict[str, Any]) -> AdminContentWriteResponse:
        raw = self._wrapper(raw_json)
        item = self._data(raw)
        payload = self._writing_list_payload()
        existing_ids = [int(x.get("id")) for x in (payload.get("data", {}).get("items") or []) if isinstance(x, dict) and str(x.get("id", "")).isdigit()]
        if not item.get("id"):
            item["id"] = (max(existing_ids) + 1) if existing_ids else 100000
            raw["data"] = item
        topic_id = int(item["id"])
        detail_path = self._writing_detail_path(topic_id, item.get("writing_task_type"))
        detail_backup = self._backup_and_write(detail_path, raw)
        list_payload, list_backup = self._upsert_writing_list_item(item)
        return AdminContentWriteResponse(item=item, raw_json=raw, backup_path=detail_backup or list_backup)

    def update_writing_topic(self, topic_id: int, raw_json: dict[str, Any]) -> AdminContentWriteResponse:
        raw = self._wrapper(raw_json)
        item = self._data(raw)
        item["id"] = topic_id
        raw["data"] = item
        detail_path = self._writing_detail_path(topic_id, item.get("writing_task_type"))
        detail_backup = self._backup_and_write(detail_path, raw)
        _, list_backup = self._upsert_writing_list_item(item)
        return AdminContentWriteResponse(item=item, raw_json=raw, backup_path=detail_backup or list_backup)

    def archive_writing_topic(self, topic_id: int) -> AdminContentWriteResponse:
        raw = MockDataService.default().get_writing_topic_detail(topic_id, visible_only=False)
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing topic not found")
        item = self._data(raw)
        item["status"] = "archived"
        item["is_public"] = False
        return self.update_writing_topic(topic_id, raw)

    def restore_writing_topic(self, topic_id: int) -> AdminContentWriteResponse:
        raw = MockDataService.default().get_writing_topic_detail(topic_id, visible_only=False)
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing topic not found")
        item = self._data(raw)
        item["status"] = "published" if isinstance(item.get("status"), str) else 1
        item["is_public"] = True
        return self.update_writing_topic(topic_id, raw)

    def _find_mock_path(self, kind: str, item_id: int) -> Path | None:
        prefixes = {
            "mock": [f"mock_test_{item_id}.json"],
            "quiz": [f"full_{item_id}.json", f"part_1_{item_id}.json", f"part_2_{item_id}.json", f"part_3_{item_id}.json"],
        }
        for path in self._data_root.rglob("*.json"):
            if path.name in prefixes[kind] or (kind == "quiz" and path.name.startswith("part_") and path.name.endswith(f"_{item_id}.json")):
                return path
        return None

    @staticmethod
    def _reading_part_quiz_metas(mock_test: dict[str, Any]) -> list[dict[str, Any]]:
        quizzes = mock_test.get("quizzes") or {}
        rows: list[tuple[int, dict[str, Any]]] = []
        for key, meta in quizzes.items():
            if not str(key).startswith("part_") or not isinstance(meta, dict):
                continue
            try:
                index = int(str(key).split("_")[-1])
            except ValueError:
                index = len(rows) + 1
            rows.append((index, meta))
        rows.sort(key=lambda item: item[0])
        return [meta for _, meta in rows]

    @staticmethod
    def _vocabs_to_passage_text(vocabs: list[dict[str, Any]] | None) -> str:
        paragraphs: list[str] = []
        for vocab in vocabs or []:
            children = vocab.get("children") if isinstance(vocab, dict) else None
            if not isinstance(children, list) or not children:
                continue
            text = " ".join(str(child.get("value") or "").strip() for child in children if isinstance(child, dict)).strip()
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)

    @staticmethod
    def _locate_paragraph(question: dict[str, Any]) -> int | None:
        locate_info = question.get("locate_info") if isinstance(question, dict) else None
        ranges = locate_info.get("paragraph_ranges") if isinstance(locate_info, dict) else None
        if not isinstance(ranges, list) or not ranges:
            return None
        first = ranges[0] if isinstance(ranges[0], dict) else {}
        start = first.get("start") if isinstance(first, dict) else {}
        paragraph = start.get("paragraph") if isinstance(start, dict) else None
        try:
            return int(paragraph) if paragraph is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _builder_set_type(question_set: dict[str, Any]) -> str:
        set_type = str(question_set.get("question_type") or "SHORT_ANSWER")
        questions = question_set.get("questions") or []
        first_question = questions[0] if questions and isinstance(questions[0], dict) else {}
        child_type = str(first_question.get("question_type") or "")
        if set_type.upper() == "SINGLE_SELECTION" and child_type.upper() in {"TRUE_FALSE", "YES_NO"}:
            return child_type
        if set_type.upper() == "SINGLE_CHOICE" and child_type.upper() == "MULTIPLE_CHOICE_ONE":
            return "SINGLE_CHOICE"
        return set_type

    @classmethod
    def _normalize_template(cls, template: Any, question_type: Any = None, question_set: dict[str, Any] | None = None) -> str:
        aliases = {
            "INLINE_GAP": cls.TEMPLATE_INLINE_GAP,
            "INLINE_GAP_TEXT": cls.TEMPLATE_INLINE_GAP,
            "GAP_FILLING": cls.TEMPLATE_INLINE_GAP,
            "GAP": cls.TEMPLATE_INLINE_GAP,
            "TF_NG": cls.TEMPLATE_TF_NG,
            "TRUE_FALSE": cls.TEMPLATE_TF_NG,
            "TFNG": cls.TEMPLATE_TF_NG,
            "YN_NG": cls.TEMPLATE_YN_NG,
            "YES_NO": cls.TEMPLATE_YN_NG,
            "YNNG": cls.TEMPLATE_YN_NG,
            "SINGLE_CHOICE": cls.TEMPLATE_SINGLE_CHOICE,
            "SINGLE": cls.TEMPLATE_SINGLE_CHOICE,
            "MULTIPLE_CHOICE_ONE": cls.TEMPLATE_SINGLE_CHOICE,
            "MULTIPLE_CHOICE_MANY": cls.TEMPLATE_MULTI_CHOICE,
            "MULTI": cls.TEMPLATE_MULTI_CHOICE,
            "MATCHING_SELECT": cls.TEMPLATE_MATCHING,
            "MATCHING": cls.TEMPLATE_MATCHING,
            "MATCHING_HEADING": cls.TEMPLATE_MATCHING,
            "MATCHING_HEADINGS": cls.TEMPLATE_MATCHING,
            "MATCHING_INFO": cls.TEMPLATE_MATCHING,
            "MATCHING_FEATURES": cls.TEMPLATE_MATCHING,
            "MATCHING_ENDINGS": cls.TEMPLATE_MATCHING,
            "TABLE_SELECTION": cls.TEMPLATE_MATCHING,
            "TEXT_COMPLETION": cls.TEMPLATE_TEXT,
            "SHORT_ANSWER": cls.TEMPLATE_TEXT,
            "SENTENCE_COMPLETION": cls.TEMPLATE_TEXT,
            "SUMMARY_COMPLETION": cls.TEMPLATE_TEXT,
            "NOTE_COMPLETION": cls.TEMPLATE_TEXT,
            "MAP_DIAGRAM_LABEL": cls.TEMPLATE_TEXT,
        }
        raw = re.sub(r"[^A-Z0-9]+", "_", str(template or "").upper()).strip("_")
        if raw in aliases:
            return aliases[raw]

        if question_set:
            content = str(question_set.get("content") or "")
            has_gap = "{{gap}}" in content or "gap-placeholder" in content
            has_options = bool(question_set.get("options"))
            questions = question_set.get("questions") if isinstance(question_set.get("questions"), list) else []
            first = questions[0] if questions and isinstance(questions[0], dict) else {}
            child_type = cls._normalize_question_type(first.get("question_type") or "")
            if has_gap and not has_options:
                return cls.TEMPLATE_INLINE_GAP
            if has_gap and has_options:
                return cls.TEMPLATE_MATCHING
            if child_type == "TRUE_FALSE":
                return cls.TEMPLATE_TF_NG
            if child_type == "YES_NO":
                return cls.TEMPLATE_YN_NG
            if child_type == "MULTIPLE_CHOICE_MANY":
                return cls.TEMPLATE_MULTI_CHOICE
            if child_type == "MULTIPLE_CHOICE_ONE":
                return cls.TEMPLATE_SINGLE_CHOICE

        q_type = cls._normalize_question_type(question_type or "")
        if q_type == "TRUE_FALSE":
            return cls.TEMPLATE_TF_NG
        if q_type == "YES_NO":
            return cls.TEMPLATE_YN_NG
        if q_type in {"SINGLE_CHOICE", "SINGLE_SELECTION", "MULTIPLE_CHOICE_ONE"}:
            return cls.TEMPLATE_SINGLE_CHOICE
        if q_type == "MULTIPLE_CHOICE_MANY":
            return cls.TEMPLATE_MULTI_CHOICE
        if q_type in cls.MATCHING_TYPES:
            return cls.TEMPLATE_MATCHING
        if q_type == "GAP_FILLING":
            return cls.TEMPLATE_INLINE_GAP
        return cls.TEMPLATE_TEXT

    @classmethod
    def _question_type_for_template(cls, template: str, question_type: Any = None) -> str:
        q_type = cls._normalize_question_type(question_type or "")
        if template == cls.TEMPLATE_INLINE_GAP:
            return "GAP_FILLING"
        if template == cls.TEMPLATE_TF_NG:
            return "TRUE_FALSE"
        if template == cls.TEMPLATE_YN_NG:
            return "YES_NO"
        if template == cls.TEMPLATE_SINGLE_CHOICE:
            return "SINGLE_CHOICE"
        if template == cls.TEMPLATE_MULTI_CHOICE:
            return "MULTIPLE_CHOICE_MANY"
        if template == cls.TEMPLATE_MATCHING:
            return q_type if q_type in cls.MATCHING_TYPES else "MATCHING"
        if template == cls.TEMPLATE_TEXT:
            return q_type if q_type in cls.TEXT_INPUT_TYPES else "SHORT_ANSWER"
        return q_type or "SHORT_ANSWER"

    @classmethod
    def _strip_admin_option_bank(cls, description: Any) -> str:
        text = str(description or "")
        pattern = re.escape(cls.OPTION_BANK_START) + r".*?" + re.escape(cls.OPTION_BANK_END)
        return re.sub(pattern, "", text, flags=re.DOTALL).strip()

    @classmethod
    def _option_bank_html(cls, options: list[dict[str, str]]) -> str:
        rows = []
        for option in options:
            key = str(option.get("option") or "").strip()
            text = str(option.get("text") or "").strip()
            if key:
                rows.append(f"<li><strong>{key}</strong> {text}</li>" if text else f"<li><strong>{key}</strong></li>")
        if not rows:
            return ""
        return (
            f"{cls.OPTION_BANK_START}"
            '<div class="admin-option-bank"><p><strong>Options</strong></p><ul>'
            + "".join(rows)
            + f"</ul></div>{cls.OPTION_BANK_END}"
        )

    @classmethod
    def _description_with_option_bank(cls, description: Any, options: list[dict[str, str]]) -> str:
        base = cls._strip_admin_option_bank(description)
        bank = cls._option_bank_html(options)
        if not bank:
            return base
        return f"{base}\n{bank}".strip()

    def _builder_from_reading_raw(
        self,
        *,
        mock_test: dict[str, Any],
        full_quiz: dict[str, Any],
    ) -> dict[str, Any]:
        passages: list[dict[str, Any]] = []
        for idx, part in enumerate(full_quiz.get("parts") or [], start=1):
            if not isinstance(part, dict):
                continue
            question_sets: list[dict[str, Any]] = []
            for question_set in part.get("question_sets") or []:
                if not isinstance(question_set, dict):
                    continue
                questions: list[dict[str, Any]] = []
                for question in question_set.get("questions") or []:
                    if not isinstance(question, dict):
                        continue
                    correct_answers = question.get("correct_answers") if isinstance(question.get("correct_answers"), list) else []
                    correct_answer = question.get("correct_answer") or "|".join(str(a) for a in correct_answers)
                    questions.append(
                        {
                            "text": question.get("text") or question.get("content") or question.get("title") or "",
                            "correct_answer": correct_answer,
                            "correct_answers": [str(a) for a in correct_answers],
                            "options": self._normalize_options(question.get("options") or []),
                            "explain": question.get("explain") or "",
                            "locate_paragraph": self._locate_paragraph(question),
                        }
                    )
                question_sets.append(
                    {
                        "title": question_set.get("title") or "",
                        "template": self._normalize_template(question_set.get("template"), self._builder_set_type(question_set), question_set),
                        "question_type": self._builder_set_type(question_set),
                        "description": self._strip_admin_option_bank(question_set.get("description") or ""),
                        "content": question_set.get("content") or "",
                        "options": self._normalize_options(question_set.get("options") or []),
                        "questions": questions,
                        "max_selections": question_set.get("max_selections") or None,
                    }
                )
            passages.append(
                {
                    "title": part.get("title") or f"Passage {idx}",
                    "passage_text": self._vocabs_to_passage_text(part.get("vocabs") or []),
                    "question_sets": question_sets,
                }
            )

        while len(passages) < 3:
            passages.append({"title": f"Passage {len(passages) + 1}", "passage_text": "", "question_sets": []})

        return {
            "id": mock_test.get("id"),
            "title": mock_test.get("title") or full_quiz.get("title") or "Reading Mock Test",
            "book_code": mock_test.get("book_code") or "Admin",
            "status": full_quiz.get("status") or ("archived" if mock_test.get("status") == 0 else "published"),
            "time": int((mock_test.get("quizzes") or {}).get("full", {}).get("time") or full_quiz.get("time") or 60),
            "thumbnail": mock_test.get("thumbnail") or "",
            "passages": passages[:3],
        }

    def list_mock_tests(self, skill_id: int | None = None, q: str | None = None) -> AdminContentListResponse:
        items = MockDataService.default().list_mock_tests(skill_id=skill_id, visible_only=False)
        q_l = (q or "").strip().lower()
        if q_l:
            items = [item for item in items if q_l in str(item.get("title", "")).lower() or q_l in str(item.get("book_code", "")).lower()]
        return AdminContentListResponse(items=items, total=len(items))

    def _next_mock_test_id(self) -> int:
        existing = [int(x.get("id")) for x in MockDataService.default().list_mock_tests(visible_only=False) if str(x.get("id", "")).isdigit()]
        return (max(existing) + 1) if existing else 100000

    @staticmethod
    def _normalize_question_type(question_type: str) -> str:
        aliases = {
            "GAP": "GAP_FILLING",
            "GAP_FILL": "GAP_FILLING",
            "TEXT_COMPLETION": "SENTENCE_COMPLETION",
            "TFNG": "TRUE_FALSE",
            "YNNG": "YES_NO",
            "SINGLE": "SINGLE_CHOICE",
            "MULTI": "MULTIPLE_CHOICE_MANY",
            "MULTIPLE_CHOICE": "MULTIPLE_CHOICE_ONE",
            "HEADINGS": "MATCHING_HEADINGS",
            "FEATURES": "MATCHING_FEATURES",
            "INFO": "MATCHING_INFO",
            "ENDINGS": "MATCHING_ENDINGS",
        }
        value = re.sub(r"[^A-Z0-9]+", "_", str(question_type or "").upper()).strip("_")
        return aliases.get(value, value or "SHORT_ANSWER")

    @staticmethod
    def _normalize_options(options: list[Any]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for idx, opt in enumerate(options or []):
            if isinstance(opt, dict):
                key = str(opt.get("option") or chr(65 + idx)).strip()
                text = str(opt.get("text") or "").strip()
            elif hasattr(opt, "option"):
                key = str(getattr(opt, "option", "") or chr(65 + idx)).strip()
                text = str(getattr(opt, "text", "") or "").strip()
            else:
                key = chr(65 + idx)
                text = str(opt).strip()
            if key:
                normalized.append({"option": key, "text": text})
        return normalized

    @staticmethod
    def _split_answers(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if value is None:
            return []
        return [part.strip() for part in re.split(r"[|,]", str(value)) if part.strip()]

    @staticmethod
    def _split_text_answers(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if value is None:
            return []
        return [part.strip() for part in str(value).split("|") if part.strip()]

    @classmethod
    def _answers_for_template(cls, template: str, value: Any) -> list[str]:
        if template in {cls.TEMPLATE_INLINE_GAP, cls.TEMPLATE_TEXT}:
            return cls._split_text_answers(value)
        return cls._split_answers(value)

    @staticmethod
    def _option_keys(options: list[dict[str, str]]) -> set[str]:
        return {str(option.get("option") or "").strip().upper() for option in options if str(option.get("option") or "").strip()}

    @classmethod
    def _count_builder_gaps(cls, content: str | None) -> int:
        raw = str(content or "")
        explicit = len(re.findall(r"\{\{\s*gap\s*\}\}", raw, flags=re.IGNORECASE))
        if explicit:
            return explicit
        question_ids = len(re.findall(r"data-question-id=[\"']gf_", raw, flags=re.IGNORECASE))
        if question_ids:
            return question_ids
        return len(re.findall(r"class=[\"'][^\"']*gap-placeholder", raw, flags=re.IGNORECASE))

    @staticmethod
    def _passage_to_vocabs(passage_text: str, passage_index: int) -> list[dict[str, Any]]:
        paragraphs = [line.strip() for line in str(passage_text or "").splitlines() if line.strip()]
        vocabs: list[dict[str, Any]] = []
        base = passage_index * 10000
        for idx, paragraph in enumerate(paragraphs, start=1):
            vocabs.append(
                {
                    "id": base + idx,
                    "level": 1,
                    "value": "",
                    "children": [{"id": base + idx * 10, "level": 2, "value": paragraph}],
                }
            )
        return vocabs

    @staticmethod
    def _gap_content(raw_content: str | None, questions: list[Any]) -> str:
        content = raw_content or ""
        if "{{gap}}" in content:
            counter = 0

            def replace_gap(_: re.Match[str]) -> str:
                nonlocal counter
                counter += 1
                return f'<span class="gap-placeholder" data-question-id="gf_{counter}">______</span>'

            return re.sub(r"\{\{\s*gap\s*\}\}", replace_gap, content)
        if "gap-placeholder" in content:
            return content
        lines = []
        for idx, question in enumerate(questions, start=1):
            text = getattr(question, "text", "") or f"Question {idx}"
            lines.append(f'{text} <span class="gap-placeholder" data-question-id="gf_{idx}">______</span>')
        return "<br/>".join(lines)

    def _validate_reading_builder(self, builder: AdminReadingMockTestBuilderRequest) -> None:
        if len(builder.passages) != 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reading mock test must have exactly 3 passages")
        total_questions = 0
        for passage_idx, passage in enumerate(builder.passages, start=1):
            if not passage.passage_text.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} text is required")
            if not passage.question_sets:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} needs at least one question set")
            for set_idx, question_set in enumerate(passage.question_sets, start=1):
                q_type = self._normalize_question_type(question_set.question_type)
                if not question_set.questions:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} has no questions")
                template = self._normalize_template(question_set.template, q_type)
                q_type = self._question_type_for_template(template, q_type)
                set_options = self._normalize_options(question_set.options)

                if template == self.TEMPLATE_INLINE_GAP:
                    actual_gaps = self._count_builder_gaps(question_set.content)
                    if actual_gaps != len(question_set.questions):
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} gap count must match questions")
                    if set_options:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} inline gap must not use options")

                if template in {self.TEMPLATE_MULTI_CHOICE, self.TEMPLATE_MATCHING} and not set_options:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} needs options")

                if template == self.TEMPLATE_SINGLE_CHOICE and not set_options:
                    has_question_options = any(self._normalize_options(question.options) for question in question_set.questions)
                    if not has_question_options:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} needs set or question options")

                set_option_keys = self._option_keys(set_options)
                allowed_fixed = {
                    self.TEMPLATE_TF_NG: {"TRUE", "FALSE", "NOT GIVEN"},
                    self.TEMPLATE_YN_NG: {"YES", "NO", "NOT GIVEN"},
                }
                for question_idx, question in enumerate(question_set.questions, start=1):
                    answers = self._answers_for_template(template, question.correct_answers or question.correct_answer)
                    if not answers:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} question {question_idx} needs an answer")
                    upper_answers = {answer.upper() for answer in answers}
                    if template in allowed_fixed and not upper_answers.issubset(allowed_fixed[template]):
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} question {question_idx} has invalid fixed-choice answer")
                    if template == self.TEMPLATE_SINGLE_CHOICE:
                        q_option_keys = self._option_keys(self._normalize_options(question.options)) or set_option_keys
                        if not q_option_keys:
                            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} question {question_idx} needs options")
                        if len(answers) != 1 or answers[0].upper() not in q_option_keys:
                            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} question {question_idx} answer must match its options")
                    if template == self.TEMPLATE_MULTI_CHOICE:
                        if not upper_answers.issubset(set_option_keys):
                            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} question {question_idx} answers must match options")
                        if question_set.max_selections and len(answers) > int(question_set.max_selections):
                            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} question {question_idx} exceeds max selections")
                    if template == self.TEMPLATE_MATCHING and (len(answers) != 1 or answers[0].upper() not in set_option_keys):
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} question {question_idx} answer must match option bank")
                total_questions += len(question_set.questions)
        if total_questions <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reading mock test must contain at least one question")

    def _build_reading_question_sets(
        self,
        *,
        builder: AdminReadingMockTestBuilderRequest,
        passage_index: int,
        quiz_id: int,
        mock_test_id: int,
        start_order: int,
        existing_part: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        passage = builder.passages[passage_index - 1]
        generated_sets: list[dict[str, Any]] = []
        flat_questions: list[dict[str, Any]] = []
        order = start_order
        existing_sets = existing_part.get("question_sets") if isinstance(existing_part, dict) else []
        existing_sets = existing_sets if isinstance(existing_sets, list) else []

        for set_index, question_set in enumerate(passage.question_sets, start=1):
            template = self._normalize_template(question_set.template, question_set.question_type)
            q_type = self._question_type_for_template(template, question_set.question_type)
            existing_set = existing_sets[set_index - 1] if set_index - 1 < len(existing_sets) and isinstance(existing_sets[set_index - 1], dict) else {}
            set_id = int(existing_set.get("id") or (mock_test_id * 1000 + passage_index * 100 + set_index))
            set_options = self._normalize_options(question_set.options)
            if template == self.TEMPLATE_TF_NG:
                set_type = "SINGLE_SELECTION"
                set_options = [{"option": "TRUE", "text": "TRUE"}, {"option": "FALSE", "text": "FALSE"}, {"option": "NOT GIVEN", "text": "NOT GIVEN"}]
                child_type = "TRUE_FALSE"
            elif template == self.TEMPLATE_YN_NG:
                set_type = "SINGLE_SELECTION"
                set_options = [{"option": "YES", "text": "YES"}, {"option": "NO", "text": "NO"}, {"option": "NOT GIVEN", "text": "NOT GIVEN"}]
                child_type = "YES_NO"
            elif template == self.TEMPLATE_SINGLE_CHOICE:
                set_type = "SINGLE_CHOICE"
                child_type = "MULTIPLE_CHOICE_ONE"
            elif template == self.TEMPLATE_MULTI_CHOICE:
                set_type = "MULTIPLE_CHOICE_MANY"
                child_type = "MULTIPLE_CHOICE_MANY"
            elif template == self.TEMPLATE_INLINE_GAP:
                set_type = "GAP_FILLING"
                child_type = "SUMMARY_COMPLETION"
                set_options = []
            elif template == self.TEMPLATE_MATCHING:
                set_type = q_type
                child_type = q_type
            elif template == self.TEMPLATE_TEXT:
                set_type = q_type
                child_type = q_type
            else:
                set_type = q_type
                child_type = q_type

            questions: list[dict[str, Any]] = []
            existing_questions = existing_set.get("questions") if isinstance(existing_set, dict) else []
            existing_questions = existing_questions if isinstance(existing_questions, list) else []
            for question_index, question in enumerate(question_set.questions, start=1):
                order += 1
                existing_question = existing_questions[question_index - 1] if question_index - 1 < len(existing_questions) and isinstance(existing_questions[question_index - 1], dict) else {}
                question_id = int(existing_question.get("id") or (mock_test_id * 10000 + order))
                answers = self._answers_for_template(template, question.correct_answers or question.correct_answer)
                correct_answer = answers[0] if answers else ""
                q_options = self._normalize_options(question.options)
                if q_options and not any(o.get("text") for o in q_options):
                    q_options = []
                q_options = q_options or ([] if template == self.TEMPLATE_INLINE_GAP else set_options)
                generated_question = dict(existing_question)
                generated_question.update({
                    "id": question_id,
                    "quiz_id": quiz_id,
                    "type": "",
                    "question_type": child_type,
                    "title": "",
                    "content": question.text,
                    "text": question.text,
                    "status": "published",
                    "sort": order,
                    "order": order,
                    "explain": question.explain or "",
                    "time_limit": 30,
                    "question_set_id": set_id,
                    "correct_answer": correct_answer,
                    "correct_answers": answers,
                })
                if q_options:
                    generated_question["options"] = q_options
                elif "options" in generated_question:
                    generated_question["options"] = []
                if question.locate_paragraph:
                    paragraph = max(1, int(question.locate_paragraph))
                    generated_question["locate_info"] = {
                        "paragraph_ranges": [{"start": {"paragraph": paragraph}, "end": {"paragraph": paragraph}}]
                    }
                elif "locate_info" in generated_question:
                    generated_question.pop("locate_info", None)
                questions.append(generated_question)
                flat_questions.append(generated_question)

            generated_set = dict(existing_set)
            description = question_set.description or ""
            if template == self.TEMPLATE_MATCHING:
                description = self._description_with_option_bank(description, set_options)
            generated_set.update({
                "id": set_id,
                "quiz_id": quiz_id,
                "title": question_set.title,
                "template": template,
                "description": description,
                "question_type": set_type,
                "sort": set_index,
                "status": "published",
                "options": set_options,
                "questions": questions,
            })
            if template == self.TEMPLATE_INLINE_GAP:
                generated_set["content"] = self._gap_content(question_set.content, question_set.questions)
            elif question_set.content:
                generated_set["content"] = question_set.content
            elif "content" in generated_set:
                generated_set["content"] = ""
            if template == self.TEMPLATE_MULTI_CHOICE:
                generated_set["max_selections"] = question_set.max_selections or len(questions[0].get("correct_answers") or [])
            elif "max_selections" in generated_set:
                generated_set.pop("max_selections", None)
            generated_sets.append(generated_set)

        return generated_sets, flat_questions, order

    def _build_reading_payloads(
        self,
        builder: AdminReadingMockTestBuilderRequest,
        *,
        mock_test_id: int,
        existing_mock: dict[str, Any] | None = None,
        existing_full_quiz: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
        builder_data = builder.model_dump()
        existing_quizzes = (existing_mock or {}).get("quizzes") or {}
        existing_full_meta = existing_quizzes.get("full") if isinstance(existing_quizzes.get("full"), dict) else {}
        full_quiz_id = int(existing_full_meta.get("id") or (mock_test_id * 100 + 1))
        existing_part_metas = self._reading_part_quiz_metas(existing_mock or {})
        part_quiz_ids = [
            int(existing_part_metas[idx].get("id")) if idx < len(existing_part_metas) and str(existing_part_metas[idx].get("id", "")).isdigit() else full_quiz_id + idx + 1
            for idx in range(3)
        ]
        existing_full_parts = (existing_full_quiz or {}).get("parts") or []
        existing_full_parts = existing_full_parts if isinstance(existing_full_parts, list) else []
        full_parts: list[dict[str, Any]] = []
        part_quizzes: list[dict[str, Any]] = []
        order = 0

        for passage_index, part_quiz_id in enumerate(part_quiz_ids, start=1):
            passage = builder.passages[passage_index - 1]
            existing_part = existing_full_parts[passage_index - 1] if passage_index - 1 < len(existing_full_parts) and isinstance(existing_full_parts[passage_index - 1], dict) else {}
            part_id = int(existing_part.get("id") or part_quiz_id)
            question_sets, flat_questions, order = self._build_reading_question_sets(
                builder=builder,
                passage_index=passage_index,
                quiz_id=full_quiz_id,
                mock_test_id=mock_test_id,
                start_order=order,
                existing_part=existing_part,
            )
            part = dict(existing_part)
            part.update({
                "id": part_id,
                "quiz_id": full_quiz_id,
                "title": passage.title or f"Passage {passage_index}",
                "passage": passage_index,
                "sort": passage_index,
                "status": "published",
                "vocabs": self._passage_to_vocabs(passage.passage_text, passage_index),
                "question_sets": question_sets,
                "questions": flat_questions,
            })
            full_parts.append(part)
            part_quiz = {
                "id": part_quiz_id,
                "title": f"{builder.title} - Passage {passage_index}",
                "type": 9,
                "mode": 0,
                "skill_id": 1,
                "status": builder.status,
                "time": int((existing_part_metas[passage_index - 1].get("time") if passage_index - 1 < len(existing_part_metas) else 0) or max(1, int(round(builder.time / 3)))),
                "quiz_code": "",
                "parts": [part],
                "admin_builder": builder_data,
            }
            part_quizzes.append(part_quiz)

        full_quiz = dict(existing_full_quiz or {})
        full_quiz.update({
            "id": full_quiz_id,
            "title": builder.title,
            "type": 9,
            "mode": int((existing_full_quiz or {}).get("mode") or 0),
            "skill_id": 1,
            "status": builder.status,
            "time": builder.time,
            "quiz_code": (existing_full_quiz or {}).get("quiz_code", ""),
            "parts": full_parts,
            "admin_builder": builder_data,
        })
        mock_test = dict(existing_mock or {})
        mock_test.update({
            "id": mock_test_id,
            "title": builder.title,
            "thumbnail": builder.thumbnail or "",
            "book_code": builder.book_code or "Admin",
            "skill_id": 1,
            "status": 1 if builder.status != "archived" else 0,
            "has_guided_retry": False,
            "quizzes": {
                "full": {"id": full_quiz_id, "type": 9, "mock_test_type": 1, "time": builder.time, "question_count": order},
                "part_1": {"id": part_quiz_ids[0], "type": 9, "mock_test_type": 2, "time": part_quizzes[0]["time"], "question_count": len(full_parts[0]["questions"])},
                "part_2": {"id": part_quiz_ids[1], "type": 9, "mock_test_type": 2, "time": part_quizzes[1]["time"], "question_count": len(full_parts[1]["questions"])},
                "part_3": {"id": part_quiz_ids[2], "type": 9, "mock_test_type": 2, "time": part_quizzes[2]["time"], "question_count": len(full_parts[2]["questions"])},
            },
            "admin_builder": builder_data,
        })
        return mock_test, full_quiz, part_quizzes, builder_data

    def save_reading_mock_test_builder(
        self,
        builder: AdminReadingMockTestBuilderRequest,
        *,
        mock_test_id: int | None = None,
    ) -> AdminReadingMockTestBuilderResponse:
        target_id = mock_test_id or builder.id or self._next_mock_test_id()
        builder.id = target_id
        self._validate_reading_builder(builder)
        existing_mock: dict[str, Any] | None = None
        existing_full_quiz: dict[str, Any] | None = None
        if mock_test_id is not None:
            existing_mock_raw = self.get_mock_test(target_id).raw_json
            existing_mock = self._data(existing_mock_raw)
            full_meta = (existing_mock.get("quizzes") or {}).get("full") or {}
            full_quiz_id = int(full_meta.get("id") or 0)
            existing_full_raw = MockDataService.default().get_quiz_raw(full_quiz_id) if full_quiz_id else None
            if not existing_full_raw:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Full quiz for this mock test was not found")
            existing_full_quiz = self._data(existing_full_raw)

        mock_test, full_quiz, part_quizzes, builder_data = self._build_reading_payloads(
            builder,
            mock_test_id=target_id,
            existing_mock=existing_mock,
            existing_full_quiz=existing_full_quiz,
        )
        folder = self._data_root / "admin_generated" / "reading" / str(target_id)
        mock_path = self._find_mock_path("mock", target_id) if mock_test_id is not None else None
        full_path = self._find_mock_path("quiz", int(full_quiz["id"])) if mock_test_id is not None else None
        payloads: list[tuple[Path, dict[str, Any]]] = [
            (mock_path or (folder / f"mock_test_{target_id}.json"), self._wrapper(mock_test)),
            (full_path or (folder / f"full_{full_quiz['id']}.json"), self._wrapper(full_quiz)),
        ]
        for index, quiz in enumerate(part_quizzes, start=1):
            part_path = self._find_mock_path("quiz", int(quiz["id"])) if mock_test_id is not None else None
            payloads.append((part_path or (folder / f"part_{index}_{quiz['id']}.json"), self._wrapper(quiz)))
        backup_paths: list[str] = []
        for path, payload in payloads:
            backup = self._backup_and_write(path, payload)
            if backup:
                backup_paths.append(backup)
        return AdminReadingMockTestBuilderResponse(
            mock_test_id=target_id,
            full_quiz_id=int(full_quiz["id"]),
            part_quiz_ids=[int(q["id"]) for q in part_quizzes],
            mock_test=mock_test,
            full_quiz=full_quiz,
            raw_json={"mock_test": self._wrapper(mock_test), "full_quiz": self._wrapper(full_quiz), "part_quizzes": [self._wrapper(q) for q in part_quizzes]},
            backup_paths=backup_paths,
            builder=builder_data,
        )

    def get_reading_mock_test_builder(self, mock_test_id: int) -> AdminReadingMockTestBuilderResponse:
        mock_raw = self.get_mock_test(mock_test_id).raw_json
        mock_test = self._data(mock_raw)
        full_meta = (mock_test.get("quizzes") or {}).get("full") or {}
        full_quiz_id = int(full_meta.get("id") or 0)
        full_raw = MockDataService.default().get_quiz_raw(full_quiz_id) if full_quiz_id else None
        if not full_raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Full quiz for this mock test was not found")
        full_quiz = self._data(full_raw)
        builder = self._builder_from_reading_raw(mock_test=mock_test, full_quiz=full_quiz)
        part_ids = [
            int(meta.get("id"))
            for key, meta in sorted((mock_test.get("quizzes") or {}).items())
            if key.startswith("part_") and isinstance(meta, dict) and str(meta.get("id", "")).isdigit()
        ]
        return AdminReadingMockTestBuilderResponse(
            mock_test_id=mock_test_id,
            full_quiz_id=full_quiz_id,
            part_quiz_ids=part_ids,
            mock_test=mock_test,
            full_quiz=full_quiz,
            raw_json={"mock_test": mock_raw, "full_quiz": full_raw or {}},
            backup_paths=[],
            builder=builder,
        )

    @staticmethod
    def _speaking_default_part(part_index: int) -> dict[str, Any]:
        defaults = {
            1: {
                "title": "Speaking Part 1",
                "time": 5,
                "instruction_html": "<ul><li>Part 1 will take about 4 to 5 minutes.</li><li>The examiner will ask you general questions about familiar topics.</li></ul>",
            },
            2: {
                "title": "Speaking Part 2",
                "time": 3,
                "instruction_html": "<ul><li>Part 2 will take about 3 to 4 minutes.</li><li>You will have 1 minute to prepare and 1 to 2 minutes to speak.</li></ul>",
            },
            3: {
                "title": "Speaking Part 3",
                "time": 5,
                "instruction_html": "<ul><li>Part 3 will take about 4 to 5 minutes.</li><li>You will discuss more abstract questions related to Part 2.</li></ul>",
            },
        }
        return defaults.get(part_index, defaults[1])

    @staticmethod
    def _speaking_question_defaults(part_index: int) -> dict[str, int]:
        if part_index == 2:
            return {"time_to_think": 60, "time_limit": 120}
        if part_index == 3:
            return {"time_to_think": 0, "time_limit": 45}
        return {"time_to_think": 0, "time_limit": 30}

    @staticmethod
    def _speaking_part_metas(mock_test: dict[str, Any]) -> dict[str, dict[str, Any]]:
        quizzes = mock_test.get("quizzes") or {}
        return {key: meta for key, meta in quizzes.items() if str(key).startswith("part_") and isinstance(meta, dict)}

    def _builder_from_speaking_raw(
        self,
        *,
        mock_test: dict[str, Any],
        full_quiz: dict[str, Any],
    ) -> dict[str, Any]:
        parts: list[dict[str, Any]] = []
        raw_parts = full_quiz.get("parts") if isinstance(full_quiz.get("parts"), list) else []
        sorted_parts = sorted(
            [part for part in raw_parts if isinstance(part, dict)],
            key=lambda part: int(part.get("sort") or part.get("passage") or 0),
        )
        for idx, part in enumerate(sorted_parts[:3], start=1):
            default_part = self._speaking_default_part(idx)
            questions = []
            raw_questions = part.get("questions") if isinstance(part.get("questions"), list) else []
            if not raw_questions:
                for question_set in part.get("question_sets") or []:
                    if isinstance(question_set, dict):
                        raw_questions.extend([q for q in question_set.get("questions") or [] if isinstance(q, dict)])
            for question in sorted(raw_questions, key=lambda q: int(q.get("sort") or q.get("order") or 0)):
                defaults = self._speaking_question_defaults(idx)
                questions.append(
                    {
                        "title": question.get("title") or question.get("text") or question.get("content") or "",
                        "description": question.get("description") or "",
                        "time_to_think": int(question.get("time_to_think") or defaults["time_to_think"]),
                        "time_limit": int(question.get("time_limit") or defaults["time_limit"]),
                        "audio_url": question.get("audio_url") or "",
                    }
                )
            instruction = part.get("instruction") if isinstance(part.get("instruction"), dict) else {}
            parts.append(
                {
                    "title": part.get("title") or default_part["title"],
                    "time": int(part.get("time") or default_part["time"]),
                    "instruction_html": instruction.get("content") or default_part["instruction_html"],
                    "questions": questions,
                }
            )

        while len(parts) < 3:
            idx = len(parts) + 1
            default_part = self._speaking_default_part(idx)
            parts.append({**default_part, "questions": []})

        return {
            "id": mock_test.get("id"),
            "title": mock_test.get("title") or full_quiz.get("title") or "Speaking Mock Test",
            "book_code": mock_test.get("book_code") or "Admin",
            "status": full_quiz.get("status") or ("archived" if mock_test.get("status") == 0 else "published"),
            "time": int((mock_test.get("quizzes") or {}).get("full", {}).get("time") or full_quiz.get("time") or 13),
            "thumbnail": mock_test.get("thumbnail") or "",
            "parts": parts[:3],
        }

    def _validate_speaking_builder(self, builder: AdminSpeakingMockTestBuilderRequest) -> None:
        if not builder.title.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Speaking test title is required")
        if len(builder.parts) != 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Speaking mock test must have exactly 3 parts")
        for part_idx, part in enumerate(builder.parts, start=1):
            if not part.questions:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} needs at least one question")
            for question_idx, question in enumerate(part.questions, start=1):
                if not question.title.strip():
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} question {question_idx} title is required")

    def _build_speaking_part(
        self,
        *,
        builder: AdminSpeakingMockTestBuilderRequest,
        part_index: int,
        quiz_id: int,
        mock_test_id: int,
        existing_part: dict[str, Any] | None = None,
        global_sort_offset: int = 0,
    ) -> tuple[dict[str, Any], int]:
        part_builder = builder.parts[part_index - 1]
        default_part = self._speaking_default_part(part_index)
        part_id = int((existing_part or {}).get("id") or (mock_test_id * 1000 + part_index))
        existing_sets = (existing_part or {}).get("question_sets") if isinstance((existing_part or {}).get("question_sets"), list) else []
        existing_set = existing_sets[0] if existing_sets and isinstance(existing_sets[0], dict) else {}
        set_id = int(existing_set.get("id") or (mock_test_id * 1000 + part_index * 10))
        existing_questions = existing_set.get("questions") if isinstance(existing_set.get("questions"), list) else []
        if not existing_questions:
            existing_questions = (existing_part or {}).get("questions") if isinstance((existing_part or {}).get("questions"), list) else []

        questions: list[dict[str, Any]] = []
        for question_index, question in enumerate(part_builder.questions, start=1):
            existing_question = existing_questions[question_index - 1] if question_index - 1 < len(existing_questions) and isinstance(existing_questions[question_index - 1], dict) else {}
            question_id = int(existing_question.get("id") or (mock_test_id * 10000 + global_sort_offset + question_index))
            defaults = self._speaking_question_defaults(part_index)
            generated_question = dict(existing_question)
            generated_question.update(
                {
                    "id": question_id,
                    "quiz_id": quiz_id,
                    "type": "speaking",
                    "question_type": "SPEAKING",
                    "title": question.title.strip(),
                    "description": question.description or "",
                    "status": "published",
                    "sort": global_sort_offset + question_index,
                    "order": question_index,
                    "time_to_think": int(question.time_to_think if question.time_to_think is not None else defaults["time_to_think"]),
                    "time_limit": int(question.time_limit or defaults["time_limit"]),
                    "audio_url": question.audio_url or "",
                    "question_set_id": set_id,
                }
            )
            questions.append(generated_question)

        question_set = dict(existing_set)
        question_set.update(
            {
                "id": set_id,
                "title": f"Speaking part {part_index}",
                "description": f"Part {part_index}",
                "part_id": part_id,
                "question_type": "SPEAKING",
                "question_count": len(questions),
                "content": f"Part {part_index}",
                "allow_reuse": False,
                "max_selections": 0,
                "sort": part_index,
                "status": "published",
                "questions": questions,
                "has_guided_retry": False,
            }
        )
        part = dict(existing_part or {})
        part.update(
            {
                "id": part_id,
                "quiz_id": quiz_id,
                "passage": part_index,
                "title": part_builder.title or default_part["title"],
                "sort": part_index,
                "time": int(part_builder.time or default_part["time"]),
                "status": "published",
                "questions": questions,
                "instruction": {
                    "id": mock_test_id * 100 + part_index,
                    "sort": 0,
                    "title": f"Speaking part {part_index}",
                    "status": "published",
                    "content": part_builder.instruction_html or default_part["instruction_html"],
                },
                "question_sets": [question_set],
            }
        )
        return part, global_sort_offset + len(questions)

    def _build_speaking_payloads(
        self,
        builder: AdminSpeakingMockTestBuilderRequest,
        *,
        mock_test_id: int,
        existing_mock: dict[str, Any] | None = None,
        existing_full_quiz: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], list[tuple[str, dict[str, Any]]], dict[str, Any]]:
        builder_data = builder.model_dump()
        existing_quizzes = (existing_mock or {}).get("quizzes") or {}
        full_meta = existing_quizzes.get("full") if isinstance(existing_quizzes.get("full"), dict) else {}
        full_quiz_id = int(full_meta.get("id") or (mock_test_id * 100 + 1))
        part_metas = self._speaking_part_metas(existing_mock or {})
        part_specs = [
            ("part_1", full_quiz_id + 1, [1], 5),
            ("part_2", full_quiz_id + 2, [2], 3),
            ("part_2&3", full_quiz_id + 3, [2, 3], 8),
            ("part_3", full_quiz_id + 4, [3], 5),
        ]
        part_quiz_ids = {
            key: int(part_metas.get(key, {}).get("id") or default_id)
            for key, default_id, _indices, _time in part_specs
        }
        existing_full_parts = (existing_full_quiz or {}).get("parts") if isinstance((existing_full_quiz or {}).get("parts"), list) else []
        full_parts: list[dict[str, Any]] = []
        order = 0
        for part_index in range(1, 4):
            existing_part = existing_full_parts[part_index - 1] if part_index - 1 < len(existing_full_parts) and isinstance(existing_full_parts[part_index - 1], dict) else {}
            part, order = self._build_speaking_part(
                builder=builder,
                part_index=part_index,
                quiz_id=full_quiz_id,
                mock_test_id=mock_test_id,
                existing_part=existing_part,
                global_sort_offset=order,
            )
            full_parts.append(part)

        full_quiz = dict(existing_full_quiz or {})
        full_quiz.update(
            {
                "id": full_quiz_id,
                "type": 8,
                "mode": int((existing_full_quiz or {}).get("mode") or 0),
                "title": f"{builder.title} - Full test",
                "status": builder.status,
                "sort": int((existing_full_quiz or {}).get("sort") or 1),
                "time": int(builder.time or 13),
                "is_test": True,
                "skill_id": 8,
                "parts": full_parts,
                "quiz_type": 4,
                "mock_test_id": mock_test_id,
                "mock_test_type": 1,
                "is_public": builder.status != "archived",
                "has_guided_retry": False,
                "admin_builder": builder_data,
            }
        )

        part_quizzes: list[tuple[str, dict[str, Any]]] = []
        for key, _default_id, indices, default_time in part_specs:
            parts = [full_parts[idx - 1] for idx in indices]
            question_count = sum(len(part.get("questions") or []) for part in parts)
            title_suffix = "Part 2 & 3" if key == "part_2&3" else f"Part {indices[0]}"
            quiz = {
                "id": part_quiz_ids[key],
                "type": 8,
                "mode": 0,
                "title": f"{builder.title} - {title_suffix}",
                "status": builder.status,
                "sort": 1,
                "time": int(part_metas.get(key, {}).get("time") or default_time),
                "is_test": True,
                "skill_id": 8,
                "parts": parts,
                "quiz_type": 4,
                "mock_test_id": mock_test_id,
                "mock_test_type": 2,
                "is_public": builder.status != "archived",
                "has_guided_retry": False,
                "admin_builder": builder_data,
                "speaking_part_type": indices[0] if len(indices) == 1 else 23,
            }
            part_quizzes.append((key, quiz))

        mock_test = dict(existing_mock or {})
        mock_test.update(
            {
                "id": mock_test_id,
                "title": builder.title,
                "thumbnail": builder.thumbnail or "",
                "book_code": builder.book_code or "Admin",
                "skill_id": 8,
                "status": 1 if builder.status != "archived" else 0,
                "has_guided_retry": False,
                "quizzes": {
                    "full": {"id": full_quiz_id, "type": 8, "mock_test_type": 1, "time": int(builder.time or 13), "question_count": order, "sort": 1},
                    **{
                        key: {
                            "id": quiz["id"],
                            "type": 8,
                            "mock_test_type": 2,
                            "time": quiz["time"],
                            "question_count": sum(len(part.get("questions") or []) for part in quiz["parts"]),
                            "sort": 1,
                        }
                        for key, quiz in part_quizzes
                    },
                },
                "admin_builder": builder_data,
            }
        )
        return mock_test, full_quiz, part_quizzes, builder_data

    def save_speaking_mock_test_builder(
        self,
        builder: AdminSpeakingMockTestBuilderRequest,
        *,
        mock_test_id: int | None = None,
    ) -> AdminSpeakingMockTestBuilderResponse:
        target_id = mock_test_id or builder.id or self._next_mock_test_id()
        builder.id = target_id
        self._validate_speaking_builder(builder)
        existing_mock: dict[str, Any] | None = None
        existing_full_quiz: dict[str, Any] | None = None
        if mock_test_id is not None:
            existing_mock_raw = self.get_mock_test(target_id).raw_json
            existing_mock = self._data(existing_mock_raw)
            full_quiz_id = int(((existing_mock.get("quizzes") or {}).get("full") or {}).get("id") or 0)
            existing_full_raw = MockDataService.default().get_quiz_raw(full_quiz_id) if full_quiz_id else None
            if not existing_full_raw:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Full quiz for this mock test was not found")
            existing_full_quiz = self._data(existing_full_raw)

        mock_test, full_quiz, part_quizzes, builder_data = self._build_speaking_payloads(
            builder,
            mock_test_id=target_id,
            existing_mock=existing_mock,
            existing_full_quiz=existing_full_quiz,
        )
        folder = self._data_root / "admin_generated" / "speaking" / str(target_id)
        mock_path = self._find_mock_path("mock", target_id) if mock_test_id is not None else None
        full_path = self._find_mock_path("quiz", int(full_quiz["id"])) if mock_test_id is not None else None
        payloads: list[tuple[Path, dict[str, Any]]] = [
            (mock_path or (folder / f"mock_test_{target_id}.json"), self._wrapper(mock_test)),
            (full_path or (folder / f"full_{full_quiz['id']}.json"), self._wrapper(full_quiz)),
        ]
        for key, quiz in part_quizzes:
            part_path = self._find_mock_path("quiz", int(quiz["id"])) if mock_test_id is not None else None
            payloads.append((part_path or (folder / f"{key}_{quiz['id']}.json"), self._wrapper(quiz)))
        backup_paths: list[str] = []
        for path, payload in payloads:
            backup = self._backup_and_write(path, payload)
            if backup:
                backup_paths.append(backup)
        return AdminSpeakingMockTestBuilderResponse(
            mock_test_id=target_id,
            full_quiz_id=int(full_quiz["id"]),
            part_quiz_ids=[int(quiz["id"]) for _key, quiz in part_quizzes],
            mock_test=mock_test,
            full_quiz=full_quiz,
            raw_json={"mock_test": self._wrapper(mock_test), "full_quiz": self._wrapper(full_quiz), "part_quizzes": [self._wrapper(q) for _key, q in part_quizzes]},
            backup_paths=backup_paths,
            builder=builder_data,
        )

    def get_speaking_mock_test_builder(self, mock_test_id: int) -> AdminSpeakingMockTestBuilderResponse:
        mock_raw = self.get_mock_test(mock_test_id).raw_json
        mock_test = self._data(mock_raw)
        full_meta = (mock_test.get("quizzes") or {}).get("full") or {}
        full_quiz_id = int(full_meta.get("id") or 0)
        full_raw = MockDataService.default().get_quiz_raw(full_quiz_id) if full_quiz_id else None
        if not full_raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Full quiz for this mock test was not found")
        full_quiz = self._data(full_raw)
        builder = self._builder_from_speaking_raw(mock_test=mock_test, full_quiz=full_quiz)
        part_ids = [
            int(meta.get("id"))
            for key, meta in (mock_test.get("quizzes") or {}).items()
            if key.startswith("part_") and isinstance(meta, dict) and str(meta.get("id", "")).isdigit()
        ]
        return AdminSpeakingMockTestBuilderResponse(
            mock_test_id=mock_test_id,
            full_quiz_id=full_quiz_id,
            part_quiz_ids=part_ids,
            mock_test=mock_test,
            full_quiz=full_quiz,
            raw_json={"mock_test": mock_raw, "full_quiz": full_raw or {}},
            backup_paths=[],
            builder=builder,
        )

    @staticmethod
    def _listening_part_quiz_metas(mock_test: dict[str, Any]) -> list[dict[str, Any]]:
        quizzes = mock_test.get("quizzes") or {}
        rows: list[tuple[int, dict[str, Any]]] = []
        for key, meta in quizzes.items():
            if not str(key).startswith("part_") or not isinstance(meta, dict):
                continue
            try:
                index = int(str(key).split("_")[-1])
            except ValueError:
                index = len(rows) + 1
            rows.append((index, meta))
        rows.sort(key=lambda item: item[0])
        return [meta for _, meta in rows]

    @staticmethod
    def _transcript_to_vocabs(transcript_text: str, part_index: int) -> list[dict[str, Any]]:
        lines = [line.strip() for line in str(transcript_text or "").splitlines() if line.strip()]
        vocabs: list[dict[str, Any]] = []
        base = part_index * 100000
        for idx, line in enumerate(lines, start=1):
            speaker = None
            text = line
            if ":" in line and len(line.split(":", 1)[0]) <= 40:
                speaker, text = [part.strip() for part in line.split(":", 1)]
            child = {"id": base + idx * 10, "level": 2, "value": text}
            if speaker:
                child["meta"] = {"speaker": speaker}
            vocabs.append({"id": base + idx, "level": 1, "value": text, "children": [child]})
        return vocabs

    @staticmethod
    def _vocabs_to_transcript_text(vocabs: list[dict[str, Any]] | None) -> str:
        lines: list[str] = []
        for vocab in vocabs or []:
            children = vocab.get("children") if isinstance(vocab, dict) else None
            if not isinstance(children, list) or not children:
                continue
            speaker = children[0].get("meta", {}).get("speaker") if isinstance(children[0], dict) else None
            text = " ".join(str(child.get("value") or "").strip() for child in children if isinstance(child, dict)).strip()
            if text:
                lines.append(f"{speaker}: {text}" if speaker else text)
        return "\n".join(lines)

    def _builder_from_listening_raw(
        self,
        *,
        mock_test: dict[str, Any],
        full_quiz: dict[str, Any],
    ) -> dict[str, Any]:
        parts: list[dict[str, Any]] = []
        raw_parts = [part for part in (full_quiz.get("parts") or []) if isinstance(part, dict)]
        raw_parts.sort(key=lambda part: int(part.get("sort") or part.get("passage") or 0))
        for idx, part in enumerate(raw_parts[:4], start=1):
            question_sets: list[dict[str, Any]] = []
            for question_set in part.get("question_sets") or []:
                if not isinstance(question_set, dict):
                    continue
                template = self._normalize_template(question_set.get("template") or question_set.get("question_type"), question_set.get("question_type"), question_set)
                questions = []
                for question in question_set.get("questions") or []:
                    if not isinstance(question, dict):
                        continue
                    correct_answers = question.get("correct_answers") if isinstance(question.get("correct_answers"), list) else []
                    questions.append(
                        {
                            "text": question.get("text") or question.get("content") or question.get("title") or "",
                            "correct_answer": question.get("correct_answer") or "|".join(str(a) for a in correct_answers),
                            "correct_answers": [str(a) for a in correct_answers],
                            "options": self._normalize_options(question.get("options") or []),
                            "explain": question.get("explain") or "",
                            "locate_paragraph": self._locate_paragraph(question),
                            "listen_from": question.get("listen_from"),
                        }
                    )
                question_sets.append(
                    {
                        "title": question_set.get("title") or "",
                        "template": template,
                        "question_type": self._question_type_for_template(template, question_set.get("question_type")),
                        "description": self._strip_admin_option_bank(question_set.get("description") or ""),
                        "content": question_set.get("content") or "",
                        "options": self._normalize_options(question_set.get("options") or []),
                        "questions": questions,
                        "max_selections": question_set.get("max_selections") or None,
                    }
                )
            parts.append(
                {
                    "title": part.get("title") or f"Listening Part {idx}",
                    "time": int(part.get("time") or 8),
                    "file_id": part.get("file_id") or "",
                    "transcript_text": self._vocabs_to_transcript_text(part.get("vocabs") or []),
                    "listen_from": part.get("listen_from"),
                    "listen_to": part.get("listen_to"),
                    "question_sets": question_sets,
                }
            )
        while len(parts) < 4:
            idx = len(parts) + 1
            parts.append({"title": f"Listening Part {idx}", "time": 8, "file_id": "", "transcript_text": "", "listen_from": None, "listen_to": None, "question_sets": []})
        return {
            "id": mock_test.get("id"),
            "title": mock_test.get("title") or full_quiz.get("title") or "Listening Mock Test",
            "book_code": mock_test.get("book_code") or "Admin",
            "status": full_quiz.get("status") or ("archived" if mock_test.get("status") == 0 else "published"),
            "time": int((mock_test.get("quizzes") or {}).get("full", {}).get("time") or full_quiz.get("time") or 40),
            "thumbnail": mock_test.get("thumbnail") or "",
            "parts": parts[:4],
        }

    def _validate_listening_builder(self, builder: AdminListeningMockTestBuilderRequest) -> None:
        if not builder.title.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listening test title is required")
        if len(builder.parts) != 4:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listening mock test must have exactly 4 parts")
        total_questions = 0
        for part_idx, part in enumerate(builder.parts, start=1):
            if not part.question_sets:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} needs at least one question set")
            for set_idx, question_set in enumerate(part.question_sets, start=1):
                if not question_set.questions:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} has no questions")
                template = self._normalize_template(question_set.template, question_set.question_type)
                set_options = self._normalize_options(question_set.options)
                if template in {self.TEMPLATE_MULTI_CHOICE, self.TEMPLATE_MATCHING} and not set_options:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} needs options")
                if template == self.TEMPLATE_SINGLE_CHOICE and not set_options:
                    has_question_options = any(self._normalize_options(question.options) for question in question_set.questions)
                    if not has_question_options:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} needs set or question options")
                set_option_keys = self._option_keys(set_options)
                allowed_fixed = {
                    self.TEMPLATE_TF_NG: {"TRUE", "FALSE", "NOT GIVEN"},
                    self.TEMPLATE_YN_NG: {"YES", "NO", "NOT GIVEN"},
                }
                for question_idx, question in enumerate(question_set.questions, start=1):
                    answers = self._answers_for_template(template, question.correct_answers or question.correct_answer)
                    if not answers:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} question {question_idx} needs an answer")
                    if template != self.TEMPLATE_INLINE_GAP and not question.text.strip():
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} question {question_idx} needs text")
                    upper_answers = {answer.upper() for answer in answers}
                    if template in allowed_fixed and not upper_answers.issubset(allowed_fixed[template]):
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} question {question_idx} has invalid fixed-choice answer")
                    if template == self.TEMPLATE_SINGLE_CHOICE:
                        q_option_keys = self._option_keys(self._normalize_options(question.options)) or set_option_keys
                        if len(answers) != 1 or answers[0].upper() not in q_option_keys:
                            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} question {question_idx} answer must match options")
                    if template == self.TEMPLATE_MULTI_CHOICE and not upper_answers.issubset(set_option_keys):
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} question {question_idx} answers must match options")
                    if template == self.TEMPLATE_MATCHING and (len(answers) != 1 or answers[0].upper() not in set_option_keys):
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Part {part_idx} set {set_idx} question {question_idx} answer must match option bank")
                total_questions += len(question_set.questions)
        if total_questions <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listening mock test must contain questions")

    def _build_listening_question_sets(
        self,
        *,
        part_builder: Any,
        part_index: int,
        quiz_id: int,
        mock_test_id: int,
        start_order: int,
        existing_part: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        generated_sets: list[dict[str, Any]] = []
        flat_questions: list[dict[str, Any]] = []
        order = start_order
        existing_sets = existing_part.get("question_sets") if isinstance(existing_part, dict) else []
        existing_sets = existing_sets if isinstance(existing_sets, list) else []
        for set_index, question_set in enumerate(part_builder.question_sets, start=1):
            template = self._normalize_template(question_set.template, question_set.question_type)
            q_type = self._question_type_for_template(template, question_set.question_type)
            existing_set = existing_sets[set_index - 1] if set_index - 1 < len(existing_sets) and isinstance(existing_sets[set_index - 1], dict) else {}
            set_id = int(existing_set.get("id") or (mock_test_id * 1000 + part_index * 100 + set_index))
            set_options = self._normalize_options(question_set.options)
            if template == self.TEMPLATE_SINGLE_CHOICE:
                set_type, child_type = "SINGLE_CHOICE", "MULTIPLE_CHOICE_ONE"
            elif template == self.TEMPLATE_MULTI_CHOICE:
                set_type = child_type = "MULTIPLE_CHOICE_MANY"
            elif template == self.TEMPLATE_TF_NG:
                set_type = "SINGLE_SELECTION"
                child_type = "TRUE_FALSE"
                set_options = [{"option": "TRUE", "text": "TRUE"}, {"option": "FALSE", "text": "FALSE"}, {"option": "NOT GIVEN", "text": "NOT GIVEN"}]
            elif template == self.TEMPLATE_YN_NG:
                set_type = "SINGLE_SELECTION"
                child_type = "YES_NO"
                set_options = [{"option": "YES", "text": "YES"}, {"option": "NO", "text": "NO"}, {"option": "NOT GIVEN", "text": "NOT GIVEN"}]
            elif template == self.TEMPLATE_INLINE_GAP:
                set_type, child_type, set_options = "GAP_FILLING", "SUMMARY_COMPLETION", []
            elif template == self.TEMPLATE_MATCHING:
                set_type = child_type = q_type
            else:
                set_type = child_type = q_type
            questions: list[dict[str, Any]] = []
            existing_questions = existing_set.get("questions") if isinstance(existing_set.get("questions"), list) else []
            for question_index, question in enumerate(question_set.questions, start=1):
                order += 1
                existing_question = existing_questions[question_index - 1] if question_index - 1 < len(existing_questions) and isinstance(existing_questions[question_index - 1], dict) else {}
                question_id = int(existing_question.get("id") or (mock_test_id * 10000 + order))
                answers = self._answers_for_template(template, question.correct_answers or question.correct_answer)
                q_options = self._normalize_options(question.options)
                if q_options and not any(o.get("text") for o in q_options):
                    q_options = []
                q_options = q_options or ([] if template == self.TEMPLATE_INLINE_GAP else set_options)
                generated_question = dict(existing_question)
                generated_question.update({
                    "id": question_id,
                    "quiz_id": quiz_id,
                    "type": "",
                    "question_type": child_type,
                    "title": "",
                    "status": "published",
                    "content": "",
                    "content_writing": "",
                    "sort": order,
                    "order": order,
                    "listen_from": question.listen_from if question.listen_from is not None else part_builder.listen_from,
                    "time_limit": 30,
                    "question_set_id": set_id,
                    "correct_answer": answers[0] if answers else "",
                    "correct_answers": answers,
                    "text": question.text,
                    "explain": question.explain or "",
                })
                if q_options:
                    generated_question["options"] = q_options
                elif "options" in generated_question:
                    generated_question["options"] = []
                if question.locate_paragraph:
                    paragraph = max(1, int(question.locate_paragraph))
                    generated_question["locate_info"] = {"paragraph_ranges": [{"start": {"paragraph": paragraph}, "end": {"paragraph": paragraph}}]}
                elif "locate_info" in generated_question:
                    generated_question.pop("locate_info", None)
                questions.append(generated_question)
                flat_questions.append(generated_question)
            description = question_set.description or ""
            if template == self.TEMPLATE_MATCHING:
                description = self._description_with_option_bank(description, set_options)
            generated_set = dict(existing_set)
            generated_set.update({
                "id": set_id,
                "title": question_set.title,
                "description": description,
                "part_id": int((existing_part or {}).get("id") or (mock_test_id * 1000 + part_index)),
                "question_type": set_type,
                "question_count": len(questions),
                "content": self._gap_content(question_set.content, question_set.questions) if template == self.TEMPLATE_INLINE_GAP else (question_set.content or ""),
                "option_title": "",
                "options": set_options,
                "allow_reuse": False,
                "max_selections": question_set.max_selections or (len(questions[0].get("correct_answers") or []) if template == self.TEMPLATE_MULTI_CHOICE and questions else 0),
                "sort": set_index,
                "questions": questions,
            })
            generated_sets.append(generated_set)
        return generated_sets, flat_questions, order

    def _build_listening_payloads(
        self,
        builder: AdminListeningMockTestBuilderRequest,
        *,
        mock_test_id: int,
        existing_mock: dict[str, Any] | None = None,
        existing_full_quiz: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
        builder_data = builder.model_dump()
        existing_quizzes = (existing_mock or {}).get("quizzes") or {}
        full_meta = existing_quizzes.get("full") if isinstance(existing_quizzes.get("full"), dict) else {}
        full_quiz_id = int(full_meta.get("id") or (mock_test_id * 100 + 1))
        existing_part_metas = self._listening_part_quiz_metas(existing_mock or {})
        part_quiz_ids = [
            int(existing_part_metas[idx].get("id")) if idx < len(existing_part_metas) and str(existing_part_metas[idx].get("id", "")).isdigit() else full_quiz_id + idx + 1
            for idx in range(4)
        ]
        existing_full_parts = (existing_full_quiz or {}).get("parts") if isinstance((existing_full_quiz or {}).get("parts"), list) else []
        full_parts: list[dict[str, Any]] = []
        part_quizzes: list[dict[str, Any]] = []
        order = 0
        for part_index, part_quiz_id in enumerate(part_quiz_ids, start=1):
            part_builder = builder.parts[part_index - 1]
            existing_part = existing_full_parts[part_index - 1] if part_index - 1 < len(existing_full_parts) and isinstance(existing_full_parts[part_index - 1], dict) else {}
            part_id = int(existing_part.get("id") or part_quiz_id)
            question_sets, flat_questions, order = self._build_listening_question_sets(
                part_builder=part_builder,
                part_index=part_index,
                quiz_id=full_quiz_id,
                mock_test_id=mock_test_id,
                start_order=order,
                existing_part=existing_part,
            )
            part = dict(existing_part)
            part.update({
                "id": part_id,
                "quiz_id": full_quiz_id,
                "passage": part_index,
                "title": part_builder.title or f"Listening Part {part_index}",
                "sort": part_index,
                "time": int(part_builder.time or 8),
                "content": "",
                "explanations": [],
                "questions": flat_questions,
                "vocabs": self._transcript_to_vocabs(part_builder.transcript_text, part_index),
                "listen_from": part_builder.listen_from,
                "listen_to": part_builder.listen_to,
                "question_sets": question_sets,
                "file_id": part_builder.file_id or "",
                "transcription": '""',
            })
            full_parts.append(part)
            part_quizzes.append({
                "id": part_quiz_id,
                "type": 10,
                "mode": 0,
                "title": f"{builder.title} - Part {part_index}",
                "status": builder.status,
                "time": int(part_builder.time or 8),
                "is_test": False,
                "skill_id": 2,
                "quiz_code": "",
                "parts": [part],
                "mock_test_id": mock_test_id,
                "mock_test_type": 2,
                "admin_builder": builder_data,
            })
        full_quiz = dict(existing_full_quiz or {})
        full_quiz.update({
            "id": full_quiz_id,
            "type": 10,
            "mode": int((existing_full_quiz or {}).get("mode") or 0),
            "title": builder.title,
            "status": builder.status,
            "time": int(builder.time or 40),
            "is_test": False,
            "skill_id": 2,
            "quiz_code": (existing_full_quiz or {}).get("quiz_code", ""),
            "parts": full_parts,
            "mock_test_id": mock_test_id,
            "mock_test_type": 1,
            "admin_builder": builder_data,
        })
        mock_test = dict(existing_mock or {})
        mock_test.update({
            "id": mock_test_id,
            "title": builder.title,
            "thumbnail": builder.thumbnail or "",
            "book_code": builder.book_code or "Admin",
            "skill_id": 2,
            "status": 1 if builder.status != "archived" else 0,
            "has_guided_retry": False,
            "quizzes": {
                "full": {"id": full_quiz_id, "type": 10, "mock_test_type": 1, "time": int(builder.time or 40), "question_count": order},
                **{
                    f"part_{idx}": {"id": quiz["id"], "type": 10, "mock_test_type": 2, "time": quiz["time"], "question_count": len(quiz["parts"][0]["questions"])}
                    for idx, quiz in enumerate(part_quizzes, start=1)
                },
            },
            "admin_builder": builder_data,
        })
        return mock_test, full_quiz, part_quizzes, builder_data

    def save_listening_mock_test_builder(
        self,
        builder: AdminListeningMockTestBuilderRequest,
        *,
        mock_test_id: int | None = None,
    ) -> AdminListeningMockTestBuilderResponse:
        target_id = mock_test_id or builder.id or self._next_mock_test_id()
        builder.id = target_id
        self._validate_listening_builder(builder)
        existing_mock: dict[str, Any] | None = None
        existing_full_quiz: dict[str, Any] | None = None
        if mock_test_id is not None:
            existing_mock_raw = self.get_mock_test(target_id).raw_json
            existing_mock = self._data(existing_mock_raw)
            full_quiz_id = int(((existing_mock.get("quizzes") or {}).get("full") or {}).get("id") or 0)
            existing_full_raw = MockDataService.default().get_quiz_raw(full_quiz_id) if full_quiz_id else None
            if not existing_full_raw:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Full quiz for this mock test was not found")
            existing_full_quiz = self._data(existing_full_raw)
        mock_test, full_quiz, part_quizzes, builder_data = self._build_listening_payloads(
            builder,
            mock_test_id=target_id,
            existing_mock=existing_mock,
            existing_full_quiz=existing_full_quiz,
        )
        folder = self._data_root / "admin_generated" / "listening" / str(target_id)
        mock_path = self._find_mock_path("mock", target_id) if mock_test_id is not None else None
        full_path = self._find_mock_path("quiz", int(full_quiz["id"])) if mock_test_id is not None else None
        payloads: list[tuple[Path, dict[str, Any]]] = [
            (mock_path or (folder / f"mock_test_{target_id}.json"), self._wrapper(mock_test)),
            (full_path or (folder / f"full_{full_quiz['id']}.json"), self._wrapper(full_quiz)),
        ]
        for index, quiz in enumerate(part_quizzes, start=1):
            part_path = self._find_mock_path("quiz", int(quiz["id"])) if mock_test_id is not None else None
            payloads.append((part_path or (folder / f"part_{index}_{quiz['id']}.json"), self._wrapper(quiz)))
        backup_paths: list[str] = []
        for path, payload in payloads:
            backup = self._backup_and_write(path, payload)
            if backup:
                backup_paths.append(backup)
        return AdminListeningMockTestBuilderResponse(
            mock_test_id=target_id,
            full_quiz_id=int(full_quiz["id"]),
            part_quiz_ids=[int(q["id"]) for q in part_quizzes],
            mock_test=mock_test,
            full_quiz=full_quiz,
            raw_json={"mock_test": self._wrapper(mock_test), "full_quiz": self._wrapper(full_quiz), "part_quizzes": [self._wrapper(q) for q in part_quizzes]},
            backup_paths=backup_paths,
            builder=builder_data,
        )

    def get_listening_mock_test_builder(self, mock_test_id: int) -> AdminListeningMockTestBuilderResponse:
        mock_raw = self.get_mock_test(mock_test_id).raw_json
        mock_test = self._data(mock_raw)
        full_quiz_id = int(((mock_test.get("quizzes") or {}).get("full") or {}).get("id") or 0)
        full_raw = MockDataService.default().get_quiz_raw(full_quiz_id) if full_quiz_id else None
        if not full_raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Full quiz for this mock test was not found")
        full_quiz = self._data(full_raw)
        builder = self._builder_from_listening_raw(mock_test=mock_test, full_quiz=full_quiz)
        part_ids = [
            int(meta.get("id"))
            for key, meta in sorted((mock_test.get("quizzes") or {}).items())
            if key.startswith("part_") and isinstance(meta, dict) and str(meta.get("id", "")).isdigit()
        ]
        return AdminListeningMockTestBuilderResponse(
            mock_test_id=mock_test_id,
            full_quiz_id=full_quiz_id,
            part_quiz_ids=part_ids,
            mock_test=mock_test,
            full_quiz=full_quiz,
            raw_json={"mock_test": mock_raw, "full_quiz": full_raw or {}},
            backup_paths=[],
            builder=builder,
        )

    def get_mock_test(self, mock_test_id: int) -> AdminContentResponse:
        raw = MockDataService.default().get_mock_test_raw(mock_test_id, visible_only=False)
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock test not found")
        return AdminContentResponse(item=self._data(raw), raw_json=raw)

    def write_mock_test(self, mock_test_id: int | None, raw_json: dict[str, Any]) -> AdminContentWriteResponse:
        raw = self._wrapper(raw_json)
        item = self._data(raw)
        if mock_test_id is not None:
            item["id"] = mock_test_id
        elif not item.get("id"):
            existing = [int(x.get("id")) for x in MockDataService.default().list_mock_tests(visible_only=False) if str(x.get("id", "")).isdigit()]
            item["id"] = (max(existing) + 1) if existing else 100000
        raw["data"] = item
        item_id = int(item["id"])
        path = self._find_mock_path("mock", item_id) or (self._data_root / "admin_generated" / f"mock_test_{item_id}.json")
        backup = self._backup_and_write(path, raw)
        return AdminContentWriteResponse(item=item, raw_json=raw, backup_path=backup)

    def archive_mock_test(self, mock_test_id: int) -> AdminContentWriteResponse:
        raw = self.get_mock_test(mock_test_id).raw_json
        item = self._data(raw)
        item["status"] = "archived" if isinstance(item.get("status"), str) else 0
        # Sync linked quiz files so get_quiz_raw(visible_only=True) blocks them
        quizzes = item.get("quizzes") or {}
        for _key, meta in quizzes.items():
            if not isinstance(meta, dict) or not meta.get("id"):
                continue
            quiz_id = int(meta["id"])
            quiz_path = self._find_mock_path("quiz", quiz_id)
            if quiz_path and quiz_path.exists():
                try:
                    quiz_raw = self._read_json(quiz_path)
                    quiz_data = self._data(quiz_raw)
                    quiz_data["status"] = "archived"
                    self._backup_and_write(quiz_path, quiz_raw)
                except Exception:
                    pass  # Best-effort: main mock test is still archived
        return self.write_mock_test(mock_test_id, raw)

    def restore_mock_test(self, mock_test_id: int) -> AdminContentWriteResponse:
        raw = self.get_mock_test(mock_test_id).raw_json
        item = self._data(raw)
        item["status"] = "published" if isinstance(item.get("status"), str) else 1
        # Sync linked quiz files so they become visible again
        quizzes = item.get("quizzes") or {}
        for _key, meta in quizzes.items():
            if not isinstance(meta, dict) or not meta.get("id"):
                continue
            quiz_id = int(meta["id"])
            quiz_path = self._find_mock_path("quiz", quiz_id)
            if quiz_path and quiz_path.exists():
                try:
                    quiz_raw = self._read_json(quiz_path)
                    quiz_data = self._data(quiz_raw)
                    quiz_data["status"] = "published" if isinstance(quiz_data.get("status"), str) else 1
                    self._backup_and_write(quiz_path, quiz_raw)
                except Exception:
                    pass
        return self.write_mock_test(mock_test_id, raw)

    def _scan_quizzes(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in self._data_root.rglob("*.json"):
            if not (path.name.startswith("full_") or path.name.startswith("part_")):
                continue
            try:
                raw = self._read_json(path)
                item = self._data(raw)
                rows.append({
                    "id": item.get("id"),
                    "title": item.get("title") or path.stem,
                    "status": item.get("status"),
                    "time": item.get("time"),
                    "parts": len(item.get("parts") or []),
                    "file": str(path.relative_to(self._data_root)),
                })
            except Exception:
                continue
        rows.sort(key=lambda x: int(x.get("id") or 0), reverse=True)
        return rows

    def list_quizzes(self, q: str | None = None) -> AdminContentListResponse:
        rows = self._scan_quizzes()
        q_l = (q or "").strip().lower()
        if q_l:
            rows = [row for row in rows if q_l in str(row.get("title", "")).lower() or q_l in str(row.get("id", "")).lower()]
        return AdminContentListResponse(items=rows, total=len(rows))

    def get_quiz(self, quiz_id: int) -> AdminContentResponse:
        raw = MockDataService.default().get_quiz_raw(quiz_id, visible_only=False)
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        return AdminContentResponse(item=self._data(raw), raw_json=raw)

    def write_quiz(self, quiz_id: int | None, raw_json: dict[str, Any]) -> AdminContentWriteResponse:
        raw = self._wrapper(raw_json)
        item = self._data(raw)
        if quiz_id is not None:
            item["id"] = quiz_id
        elif not item.get("id"):
            existing = [int(x.get("id")) for x in self._scan_quizzes() if str(x.get("id", "")).isdigit()]
            item["id"] = (max(existing) + 1) if existing else 100000
        raw["data"] = item
        item_id = int(item["id"])
        path = self._find_mock_path("quiz", item_id) or (self._data_root / "admin_generated" / f"full_{item_id}.json")
        backup = self._backup_and_write(path, raw)
        return AdminContentWriteResponse(item=item, raw_json=raw, backup_path=backup)

    def archive_quiz(self, quiz_id: int) -> AdminContentWriteResponse:
        raw = self.get_quiz(quiz_id).raw_json
        item = self._data(raw)
        item["status"] = "archived"
        return self.write_quiz(quiz_id, raw)

    def restore_quiz(self, quiz_id: int) -> AdminContentWriteResponse:
        raw = self.get_quiz(quiz_id).raw_json
        item = self._data(raw)
        item["status"] = "published" if isinstance(item.get("status"), str) else 1
        return self.write_quiz(quiz_id, raw)

    def update_quiz_part(self, quiz_id: int, part_id: int, patch: dict[str, Any]) -> AdminContentWriteResponse:
        raw = self.get_quiz(quiz_id).raw_json
        item = self._data(raw)
        for part in item.get("parts") or []:
            if isinstance(part, dict) and int(part.get("id") or 0) == part_id:
                part.update(patch)
                return self.write_quiz(quiz_id, raw)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz part not found")

    def update_quiz_question(self, quiz_id: int, question_id: int, patch: dict[str, Any]) -> AdminContentWriteResponse:
        raw = self.get_quiz(quiz_id).raw_json
        item = self._data(raw)
        for part in item.get("parts") or []:
            for question in part.get("questions") or []:
                if isinstance(question, dict) and int(question.get("id") or 0) == question_id:
                    question.update(patch)
                    return self.write_quiz(quiz_id, raw)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz question not found")
