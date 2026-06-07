from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.core.openrouter_client import chat_completion, has_openrouter_keys
from app.core.rate_limit import limiter
from app.core.storage import s3_public_url_for_key
from app.core.usage_counters import check_and_increment_writing_chat
from app.db.database import get_db
from app.db.models import User
from app.schemas import WritingSubmitRequest, WritingSubmitResponse
from app.services.mock_data_service import MockDataService
from app.services.writing_service import WritingService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="", tags=["Writing"])

_WRITING_SYSTEM = (
    "You are Catbot, an expert IELTS Writing coach with 10+ years of experience. "
    "You help students improve their Task 1 and Task 2 writing skills. "
    "Give concise, practical, actionable advice. "
    "You may respond in the same language the user writes in (Vietnamese or English). "
    "When given a writing task/prompt, refer to it when answering."
)


class _ChatMsg(BaseModel):
    role: str
    content: str


class _WritingChatReq(BaseModel):
    prompt_text: str = ""
    user_message: str
    history: list[_ChatMsg] = []


@limiter.limit("30/minute")
@router.post("/writing/chat")
async def writing_chat(
    request: Request,
    body: _WritingChatReq,
    current_user: User = Depends(get_current_user),
):
    """Proxy chat to OpenRouter for writing coaching, with topic context (JWT required)."""
    check_and_increment_writing_chat(current_user.id)
    if not has_openrouter_keys():
        return JSONResponse(status_code=503, content={"error": "AI service unavailable: OPENROUTER_API_KEY is missing"})

    messages: list[dict] = [{"role": "system", "content": _WRITING_SYSTEM}]
    if body.prompt_text:
        messages.append({
            "role": "system",
            "content": f'Current IELTS Writing task the student is working on: "{body.prompt_text}"',
        })
    for m in body.history[-10:]:
        role = m.role if m.role in {"user", "assistant"} else "user"
        messages.append({"role": role, "content": m.content})
    messages.append({"role": "user", "content": body.user_message})

    try:
        reply, _model = await chat_completion(
            messages,
            max_tokens=800,
            temperature=0.6,
            timeout=15.0,
            title="Writing Coach",
        )
        return {"reply": reply}
    except Exception as exc:
        return JSONResponse(status_code=502, content={"error": f"AI service unavailable: {exc}"})


def _attach_media_urls(payload: dict) -> dict:
    """Expose chart/thumbnail URLs for Task 1 graphs (UUID → GET /images/{id})."""
    if payload.get("code") != 0:
        return payload
    data = payload.get("data")
    if not isinstance(data, dict):
        return payload
    thumb = data.get("thumbnail")
    if thumb:
        data["thumbnail_url"] = _image_url(thumb)
    for q in data.get("questions") or []:
        if not isinstance(q, dict):
            continue
        graph_id = q.get("writing_graph_image")
        if graph_id:
            q["chart_image_url"] = _image_url(graph_id)
    return payload


def _image_url(image_id: str) -> str:
    image_id = str(image_id or "").strip()
    if not image_id:
        return ""
    if image_id.startswith(("http://", "https://", "/")):
        return image_id
    if "." in image_id.rsplit("/", 1)[-1]:
        return s3_public_url_for_key(f"assets/images/{image_id}") or f"/images/{image_id}"
    return f"/images/{image_id}"


@router.get("/writing/topics/{topic_id}")
def get_writing_topic(topic_id: int) -> dict:
    service = MockDataService.default()
    raw = service.get_writing_topic_detail(topic_id)
    if raw is None:
        return JSONResponse(status_code=404, content={"code": 404, "message": "Not found", "data": None})
    return _attach_media_urls(raw)


@router.post("/writing/submit", response_model=WritingSubmitResponse, status_code=201)
@limiter.limit("10/minute")
async def submit_writing(
    request: Request,
    body: WritingSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WritingSubmitResponse:
    """Save essay, AI band evaluation, history + progress."""
    return await WritingService(db).submit(current_user, body)


@router.get("/writing/topics")
def list_writing_topics(
    task_type: int | None = Query(default=None, ge=1, le=2),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> dict:
    service = MockDataService.default()
    items = service.list_writing_topics(task_type=task_type)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "code": 0,
        "message": "",
        "data": {
            "items": items[start:end],
            "total": len(items),
            "page": page,
            "page_size": page_size,
        },
    }
