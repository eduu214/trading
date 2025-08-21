from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "alphastrat",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.scanner_tasks", "app.tasks.analysis_tasks", "app.tasks.portfolio_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes (default)
    task_soft_time_limit=25 * 60,  # 25 minutes (default)
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Portfolio-specific task routing
    task_routes={
        'app.tasks.portfolio_tasks.optimize_portfolio': {'queue': 'portfolio'},
        'app.tasks.portfolio_tasks.calculate_correlation_matrix': {'queue': 'portfolio'},
        'app.tasks.portfolio_tasks.detect_rebalancing_opportunity': {'queue': 'portfolio'},
        'app.tasks.scanner_tasks.*': {'queue': 'scanner'},
        'app.tasks.analysis_tasks.*': {'queue': 'analysis'},
    },
    
    # Queue-specific configurations
    task_annotations={
        'app.tasks.portfolio_tasks.optimize_portfolio': {
            'rate_limit': '10/m',  # Max 10 optimizations per minute
            'time_limit': 30,      # 30 second hard limit
            'soft_time_limit': 25, # 25 second soft limit
        },
        'app.tasks.portfolio_tasks.calculate_correlation_matrix': {
            'rate_limit': '5/m',   # Max 5 correlation calculations per minute
            'time_limit': 30,
            'soft_time_limit': 25,
        },
        'app.tasks.portfolio_tasks.detect_rebalancing_opportunity': {
            'rate_limit': '20/m',  # Max 20 rebalancing checks per minute
            'time_limit': 20,      # 20 second limit for lighter task
            'soft_time_limit': 15,
        },
    }
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
    # Portfolio optimization tasks
    "calculate-correlations-30d": {
        "task": "app.tasks.portfolio_tasks.calculate_correlation_matrix",
        "schedule": 30 * 60,  # Every 30 minutes
        "args": ["main", 30],
        "options": {"queue": "portfolio"}
    },
    "calculate-correlations-90d": {
        "task": "app.tasks.portfolio_tasks.calculate_correlation_matrix",
        "schedule": 2 * 60 * 60,  # Every 2 hours
        "args": ["main", 90],
        "options": {"queue": "portfolio"}
    },
    "detect-rebalancing-opportunities": {
        "task": "app.tasks.portfolio_tasks.detect_rebalancing_opportunity",
        "schedule": 5 * 60,  # Every 5 minutes
        "args": ["main"],
        "options": {"queue": "portfolio"}
    },
}