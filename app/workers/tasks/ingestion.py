"""Celery task for ingestion execution."""

import asyncio
import uuid

from opentelemetry import trace

from app.config import get_settings
from app.db import RuntimeResources
from app.dependencies.sources import build_ingestion_service
from app.workers.celery_app import celery_app
from app.workers.ingestion import execute_ingestion_run

tracer = trace.get_tracer("job-radar.ingestion")


@celery_app.task(
    bind=True,
    name="job_radar.ingestion",
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def run_ingestion(self, source_id: str, run_id: str) -> dict:
    """Execute one ingestion run and expose a monitorable Celery task."""
    return asyncio.run(_run_ingestion(source_id, run_id))


async def _run_ingestion(source_id: str, run_id: str) -> dict:
    with tracer.start_as_current_span("ingestion.execute") as span:
        span.set_attribute("job.source_id", source_id)
        span.set_attribute("job.run_id", run_id)
        resources = RuntimeResources(get_settings())
        try:
            async with resources.session_factory() as session:
                service = build_ingestion_service(resources.redis)
                source = await service.repository.get(session, uuid.UUID(source_id))
                if source is None:
                    span.set_attribute("job.status", "skipped")
                    return {"status": "skipped", "reason": "source not found"}
                await execute_ingestion_run(
                    resources, session, service, source, uuid.UUID(run_id), uuid.UUID(source_id)
                )
                span.set_attribute("job.status", "completed")
                return {"status": "completed", "run_id": run_id}
        finally:
            await resources.close()
