from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.dependencies import get_current_user
from app.db.models import User
from app.services.mock_data_service import MockDataService
from app.utils.quiz_sanitizer import sanitize_quiz_payload, strip_quiz_answers

router = APIRouter(prefix="", tags=["Mock Tests"])


@router.get("/mock-tests")
def list_mock_tests(
    skill_id: int | None = Query(default=None),
    _user: User = Depends(get_current_user),
) -> dict:
    """List mock tests (metadata only). Requires login."""
    service = MockDataService.default()
    data = service.list_mock_tests(skill_id=skill_id)
    return {"code": 0, "message": "", "data": data}


@router.get("/mock-tests/{mock_test_id}")
def get_mock_test(
    mock_test_id: int,
    _user: User = Depends(get_current_user),
):
    """Mock test detail without embedded answer keys. Requires login."""
    service = MockDataService.default()
    raw = service.get_mock_test_raw(mock_test_id)
    if raw is None:
        return JSONResponse(status_code=404, content={"code": 404, "message": "Not found", "data": None})
    if isinstance(raw, dict) and "data" in raw:
        return sanitize_quiz_payload(raw)
    return strip_quiz_answers(raw)


@router.get("/quizzes/{quiz_id}")
def get_quiz(
    quiz_id: int,
    _user: User = Depends(get_current_user),
):
    """Quiz content for exam UI — answers stripped; grading is server-side only."""
    service = MockDataService.default()
    raw = service.get_quiz_raw(quiz_id)
    if raw is None:
        return JSONResponse(status_code=404, content={"code": 404, "message": "Not found", "data": None})
    body = raw.get("data", raw) if isinstance(raw, dict) else raw
    safe = strip_quiz_answers(body)
    return {"code": 0, "message": "", "data": safe}
