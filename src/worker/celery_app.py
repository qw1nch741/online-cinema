"""
Celery application configuration for background tasks.

Scheduled jobs (Celery Beat):
- cleanup-expired-tokens-every-30-minutes — removes expired activation,
  password-reset, and refresh tokens from the database.
"""

from celery import Celery

REDIS_URL = "redis://localhost:6379/0"

celery_app = Celery(
    "online_cinema_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.worker.tasks"],
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens-every-30-minutes": {
        "task": "src.worker.tasks.cleanup_expired_tokens",
        "schedule": 1800.0,
    },
}

celery_app.conf.timezone = "UTC"
