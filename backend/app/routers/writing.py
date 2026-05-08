from __future__ import annotations

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings
from app.services.mock_data_service import MockDataService

router = APIRouter(prefix="", tags=["Writing"])

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

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


@router.post("/writing/chat")
async def writing_chat(body: _WritingChatReq):
    """Proxy chat to OpenRouter for writing coaching, with topic context."""
    messages: list[dict] = [{"role": "system", "content": _WRITING_SYSTEM}]
    if body.prompt_text:
        messages.append({
            "role": "system",
            "content": f'Current IELTS Writing task the student is working on: "{body.prompt_text}"',
        })
    for m in body.history[-10:]:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": body.user_message})

    payload = {
        "model":       "anthropic/claude-3-haiku",
        "messages":    messages,
        "max_tokens":  800,
        "temperature": 0.6,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://cathoven-clone.local",
        "X-Title":       "Writing Coach",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
            resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"]
        return {"reply": reply}
    except Exception as exc:
        return JSONResponse(status_code=502, content={"error": f"AI service unavailable: {exc}"})


@router.get("/writing/topics/{topic_id}")
def get_writing_topic(topic_id: int) -> dict:
    service = MockDataService.default()
    raw = service.get_writing_topic_detail(topic_id)
    if raw is None:
        return JSONResponse(status_code=404, content={"code": 404, "message": "Not found", "data": None})
    return raw


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
