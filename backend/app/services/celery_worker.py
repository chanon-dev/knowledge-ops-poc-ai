"""Celery worker for async document processing."""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "the_expert",
    broker=settings.REDIS_URL if hasattr(settings, "REDIS_URL") else "redis://localhost:6379/1",
    backend=settings.REDIS_URL if hasattr(settings, "REDIS_URL") else "redis://localhost:6379/2",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.services.tasks.*": {"queue": "ingestion"},
    },
)
