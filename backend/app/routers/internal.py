from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.post("/cron/push-reminders")
async def run_push_reminders_cron(
    x_cron_secret: str | None = Header(default=None, alias="X-Cron-Secret"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not settings.CRON_SECRET or x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret",
        )
    sent = await NotificationService(db).send_due_push_reminders()
    return {"message": "Push reminders processed.", "sent": sent}
