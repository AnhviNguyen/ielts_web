"""Celery application — broker/backend from REDIS_URL."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "linguaielts",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.speaking_tasks",
        "app.tasks.shadowing_tasks",
        "app.tasks.leaderboard_tasks",
        "app.tasks.history_tasks",
        "app.tasks.notification_tasks",
    ],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_soft_time_limit=180,
    task_time_limit=300,
    beat_schedule={
        "rebuild-leaderboard-zset": {
            "task": "leaderboard.rebuild_zset",
            "schedule": 6 * 3600.0,
        },
        "archive-old-history": {
            "task": "history.archive_old",
            "schedule": 7 * 24 * 3600.0,
        },
        "daily-study-reminders": {
            "task": "notifications.daily_reminders",
            "schedule": 24 * 3600.0,
        },
    },
    task_routes={
        "app.tasks.speaking_tasks.*": {"queue": "speaking"},
        "app.tasks.shadowing_tasks.*": {"queue": "shadowing"},
    },
    task_default_queue="celery",
)
