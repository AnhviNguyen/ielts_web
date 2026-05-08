from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.mock_data_service import MockDataService

router = APIRouter(prefix="", tags=["Mock Tests"])


@router.get("/mock-tests")
def list_mock_tests(skill_id: int | None = Query(default=None)) -> dict:
    service = MockDataService.default()
    data = service.list_mock_tests(skill_id=skill_id)
    return {"code": 0, "message": "", "data": data}


@router.get("/mock-tests/{mock_test_id}")
def get_mock_test(mock_test_id: int):
    service = MockDataService.default()
    raw = service.get_mock_test_raw(mock_test_id)
    if raw is None:
        return JSONResponse(status_code=404, content={"code": 404, "message": "Not found", "data": None})
    return raw


@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: int):
    service = MockDataService.default()
    raw = service.get_quiz_raw(quiz_id)
    if raw is None:
        return JSONResponse(status_code=404, content={"code": 404, "message": "Not found", "data": None})
    return raw

