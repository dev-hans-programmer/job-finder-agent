"""Celery application configuration and task registration."""

from celery import Celery

from app.config import get_settings
from app.observability.telemetry import configure_telemetry, instrument_clients

settings = get_settings()
configure_telemetry(settings)
instrument_clients(settings)
celery_app = Celery(
    "job_radar",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks.ingestion"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
)
