"""Full mock exam catalog API."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user
from app.db.models import User
from app.services.full_exam_service import FullExamService

router = APIRouter(prefix="/mock-exams", tags=["Mock Exams"])


@router.get("/sets")
async def list_full_exam_sets(
    limit: int = 30,
    _: User = Depends(get_current_user),
):
    """List bundled Reading+Listening+Writing+Speaking mock exam sets."""
    sets = FullExamService().list_sets(limit=limit)
    return {"items": sets, "total": len(sets)}


@router.get("/sets/{set_id}")
async def get_full_exam_set(
    set_id: str,
    _: User = Depends(get_current_user),
):
    item = FullExamService().get_set(set_id)
    if not item:
        raise HTTPException(status_code=404, detail="Mock exam set not found")
    return item
