from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "flowplane",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.scanner_tasks", "app.tasks.analysis_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "scan-markets": {
        "task": "app.tasks.scanner_tasks.scan_all_markets",
        "schedule": settings.SCAN_INTERVAL_MINUTES * 60,  # Convert to seconds
        "options": {"queue": "scanner"}
    },
    "update-correlations": {
        "task": "app.tasks.analysis_tasks.update_portfolio_correlations",
        "schedule": 15 * 60,  # Every 15 minutes
        "options": {"queue": "analysis"}
    },
}