from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "digital_library",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.notification_tasks",
    ],
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-notifications": {
        "task": "app.tasks.notification_tasks.cleanup_expired_notifications",
        "schedule": crontab(hour=0, minute=0),  # daily midnight
    },
}
