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

from app.schemas import (
    AdminContentListResponse,
    AdminContentResponse,
    AdminContentWriteResponse,
    AdminImageUploadResponse,
    AdminReadingMockTestBuilderRequest,
    AdminReadingMockTestBuilderResponse,
)
from app.services.mock_data_service import MockDataService


class AdminContentService:
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
        content = await upload.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is empty")
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file must be 5MB or smaller")
        image_id = uuid.uuid4().hex
        image_dir = self._data_root / "assets" / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        path = image_dir / f"{image_id}{suffix}"
        path.write_bytes(content)
        return AdminImageUploadResponse(id=image_id, url=f"/images/{image_id}")

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
        items = MockDataService.default().list_writing_topics(task_type=task_type)
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
        raw = MockDataService.default().get_writing_topic_detail(topic_id)
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
        raw = MockDataService.default().get_writing_topic_detail(topic_id)
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing topic not found")
        item = self._data(raw)
        item["status"] = "archived"
        item["is_public"] = False
        return self.update_writing_topic(topic_id, raw)

    def _find_mock_path(self, kind: str, item_id: int) -> Path | None:
        prefixes = {
            "mock": [f"mock_test_{item_id}.json"],
            "quiz": [f"full_{item_id}.json", f"part_1_{item_id}.json", f"part_2_{item_id}.json", f"part_3_{item_id}.json"],
        }
        for path in self._data_root.rglob("*.json"):
            if path.name in prefixes[kind]:
                return path
        return None

    def list_mock_tests(self, skill_id: int | None = None, q: str | None = None) -> AdminContentListResponse:
        items = MockDataService.default().list_mock_tests(skill_id=skill_id)
        q_l = (q or "").strip().lower()
        if q_l:
            items = [item for item in items if q_l in str(item.get("title", "")).lower() or q_l in str(item.get("book_code", "")).lower()]
        return AdminContentListResponse(items=items, total=len(items))

    def _next_mock_test_id(self) -> int:
        existing = [int(x.get("id")) for x in MockDataService.default().list_mock_tests() if str(x.get("id", "")).isdigit()]
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
                if q_type == "GAP_FILLING":
                    expected_gaps = len(question_set.questions)
                    actual_gaps = len(re.findall(r"\{\{\s*gap\s*\}\}", question_set.content or ""))
                    if actual_gaps and actual_gaps != expected_gaps:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} gap count does not match questions")
                options_required = {
                    "SINGLE_CHOICE",
                    "SINGLE_SELECTION",
                    "MULTIPLE_CHOICE_ONE",
                    "MULTIPLE_CHOICE_MANY",
                    "MATCHING",
                    "MATCHING_FEATURES",
                    "MATCHING_INFO",
                    "MATCHING_HEADING",
                    "MATCHING_HEADINGS",
                    "MATCHING_ENDINGS",
                    "TABLE_SELECTION",
                }
                set_options = self._normalize_options(question_set.options)
                if q_type in options_required and q_type not in {"TRUE_FALSE", "YES_NO"} and not set_options:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} needs options")
                for question_idx, question in enumerate(question_set.questions, start=1):
                    answers = self._split_answers(question.correct_answers or question.correct_answer)
                    if q_type == "MULTIPLE_CHOICE_MANY":
                        answers = self._split_answers(question.correct_answers or question.correct_answer)
                    if not answers:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Passage {passage_idx} set {set_idx} question {question_idx} needs an answer")
                total_questions += len(question_set.questions)
        if total_questions != 40:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reading mock test must contain exactly 40 questions")

    def _build_reading_question_sets(
        self,
        *,
        builder: AdminReadingMockTestBuilderRequest,
        passage_index: int,
        quiz_id: int,
        mock_test_id: int,
        start_order: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        passage = builder.passages[passage_index - 1]
        generated_sets: list[dict[str, Any]] = []
        flat_questions: list[dict[str, Any]] = []
        order = start_order
        text_input_types = {"SHORT_ANSWER", "SENTENCE_COMPLETION", "SUMMARY_COMPLETION", "NOTE_COMPLETION", "MAP_DIAGRAM_LABEL"}
        matching_types = {"MATCHING", "MATCHING_FEATURES", "MATCHING_INFO", "MATCHING_HEADING", "MATCHING_HEADINGS", "MATCHING_ENDINGS", "TABLE_SELECTION"}

        for set_index, question_set in enumerate(passage.question_sets, start=1):
            q_type = self._normalize_question_type(question_set.question_type)
            set_id = mock_test_id * 1000 + passage_index * 100 + set_index
            set_options = self._normalize_options(question_set.options)
            if q_type == "TRUE_FALSE":
                set_type = "SINGLE_SELECTION"
                set_options = [{"option": "TRUE", "text": "TRUE"}, {"option": "FALSE", "text": "FALSE"}, {"option": "NOT GIVEN", "text": "NOT GIVEN"}]
                child_type = "TRUE_FALSE"
            elif q_type == "YES_NO":
                set_type = "SINGLE_SELECTION"
                set_options = [{"option": "YES", "text": "YES"}, {"option": "NO", "text": "NO"}, {"option": "NOT GIVEN", "text": "NOT GIVEN"}]
                child_type = "YES_NO"
            elif q_type in {"SINGLE_CHOICE", "SINGLE_SELECTION", "MULTIPLE_CHOICE_ONE"}:
                set_type = "SINGLE_CHOICE"
                child_type = "MULTIPLE_CHOICE_ONE"
            elif q_type == "MULTIPLE_CHOICE_MANY":
                set_type = "MULTIPLE_CHOICE_MANY"
                child_type = "MULTIPLE_CHOICE_MANY"
            elif q_type == "GAP_FILLING":
                set_type = "GAP_FILLING"
                child_type = "SUMMARY_COMPLETION"
            elif q_type in matching_types:
                set_type = q_type
                child_type = q_type
            elif q_type in text_input_types:
                set_type = q_type
                child_type = q_type
            else:
                set_type = q_type
                child_type = q_type

            questions: list[dict[str, Any]] = []
            for question_index, question in enumerate(question_set.questions, start=1):
                order += 1
                question_id = mock_test_id * 10000 + order
                answers = self._split_answers(question.correct_answers or question.correct_answer)
                correct_answer = answers[0] if answers else ""
                q_options = self._normalize_options(question.options) or set_options
                generated_question = {
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
                }
                if q_options:
                    generated_question["options"] = q_options
                if question.locate_paragraph:
                    paragraph = max(1, int(question.locate_paragraph))
                    generated_question["locate_info"] = {
                        "paragraph_ranges": [{"start": {"paragraph": paragraph}, "end": {"paragraph": paragraph}}]
                    }
                questions.append(generated_question)
                flat_questions.append(generated_question)

            generated_set = {
                "id": set_id,
                "quiz_id": quiz_id,
                "title": question_set.title,
                "description": question_set.description or "",
                "question_type": set_type,
                "sort": set_index,
                "status": "published",
                "options": set_options,
                "questions": questions,
            }
            if q_type == "GAP_FILLING":
                generated_set["content"] = self._gap_content(question_set.content, question_set.questions)
            elif question_set.content:
                generated_set["content"] = question_set.content
            if q_type == "MULTIPLE_CHOICE_MANY":
                generated_set["max_selections"] = question_set.max_selections or len(questions[0].get("correct_answers") or [])
            generated_sets.append(generated_set)

        return generated_sets, flat_questions, order

    def _build_reading_payloads(
        self,
        builder: AdminReadingMockTestBuilderRequest,
        *,
        mock_test_id: int,
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
        builder_data = builder.model_dump()
        full_quiz_id = mock_test_id * 100 + 1
        part_quiz_ids = [full_quiz_id + idx for idx in range(1, 4)]
        full_parts: list[dict[str, Any]] = []
        part_quizzes: list[dict[str, Any]] = []
        order = 0

        for passage_index, part_quiz_id in enumerate(part_quiz_ids, start=1):
            passage = builder.passages[passage_index - 1]
            question_sets, flat_questions, order = self._build_reading_question_sets(
                builder=builder,
                passage_index=passage_index,
                quiz_id=full_quiz_id,
                mock_test_id=mock_test_id,
                start_order=order,
            )
            part = {
                "id": part_quiz_id,
                "quiz_id": full_quiz_id,
                "title": passage.title or f"Passage {passage_index}",
                "passage": passage_index,
                "sort": passage_index,
                "status": "published",
                "vocabs": self._passage_to_vocabs(passage.passage_text, passage_index),
                "question_sets": question_sets,
                "questions": flat_questions,
            }
            full_parts.append(part)
            part_quiz = {
                "id": part_quiz_id,
                "title": f"{builder.title} - Passage {passage_index}",
                "type": 9,
                "skill_id": 1,
                "status": builder.status,
                "time": max(1, int(round(builder.time / 3))),
                "parts": [part],
                "admin_builder": builder_data,
            }
            part_quizzes.append(part_quiz)

        full_quiz = {
            "id": full_quiz_id,
            "title": builder.title,
            "type": 9,
            "skill_id": 1,
            "status": builder.status,
            "time": builder.time,
            "parts": full_parts,
            "admin_builder": builder_data,
        }
        mock_test = {
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
        }
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
        mock_test, full_quiz, part_quizzes, builder_data = self._build_reading_payloads(builder, mock_test_id=target_id)
        folder = self._data_root / "admin_generated" / "reading" / str(target_id)
        payloads: list[tuple[Path, dict[str, Any]]] = [
            (folder / f"mock_test_{target_id}.json", self._wrapper(mock_test)),
            (folder / f"full_{full_quiz['id']}.json", self._wrapper(full_quiz)),
        ]
        for index, quiz in enumerate(part_quizzes, start=1):
            payloads.append((folder / f"part_{index}_{quiz['id']}.json", self._wrapper(quiz)))
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
        builder = mock_test.get("admin_builder")
        if not isinstance(builder, dict):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This mock test was not created with Reading Builder")
        full_meta = (mock_test.get("quizzes") or {}).get("full") or {}
        full_quiz_id = int(full_meta.get("id") or 0)
        full_raw = MockDataService.default().get_quiz_raw(full_quiz_id) if full_quiz_id else None
        full_quiz = self._data(full_raw or {}) if full_raw else {}
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

    def get_mock_test(self, mock_test_id: int) -> AdminContentResponse:
        raw = MockDataService.default().get_mock_test_raw(mock_test_id)
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock test not found")
        return AdminContentResponse(item=self._data(raw), raw_json=raw)

    def write_mock_test(self, mock_test_id: int | None, raw_json: dict[str, Any]) -> AdminContentWriteResponse:
        raw = self._wrapper(raw_json)
        item = self._data(raw)
        if mock_test_id is not None:
            item["id"] = mock_test_id
        elif not item.get("id"):
            existing = [int(x.get("id")) for x in MockDataService.default().list_mock_tests() if str(x.get("id", "")).isdigit()]
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
        raw = MockDataService.default().get_quiz_raw(quiz_id)
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
