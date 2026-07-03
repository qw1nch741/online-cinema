from celery import Celery

# 1. Define your Redis connection string.
# 'redis://localhost:6379/0' means connecting to local machine, default port, database 0.
REDIS_URL = "redis://localhost:6379/0"

celery_app = Celery(
    "online_cinema_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.worker.tasks"]  # Crucial: Tells Celery to scan this file for tasks on startup
)

# 2. Configure the Celery Beat automated scheduler
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens-every-30-minutes": {
        "task": "src.worker.tasks.cleanup_expired_tokens",  # Must match your task path exactly!
        "schedule": 1800.0,  # Interval period tracked in seconds (1800s = 30 minutes)
    },
}

# 3. Ensure your background clocks sync cleanly with your database timestamps
celery_app.conf.timezone = "UTC"