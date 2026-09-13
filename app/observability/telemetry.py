"""Optional OpenTelemetry tracing configuration and instrumentation."""

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

_configured = False
_instrumented_redis = False
_instrumented_httpx = False
_instrumented_celery = False


def configure_telemetry(settings: Any) -> TracerProvider | None:
    global _configured
    if not getattr(settings, "otel_enabled", False):
        return None
    if _configured:
        provider = trace.get_tracer_provider()
        return provider if isinstance(provider, TracerProvider) else None
    resource = Resource.create(
        {
            SERVICE_NAME: settings.otel_service_name,
            "service.version": getattr(settings, "app_version", "unknown"),
            "service.commit_sha": getattr(settings, "git_sha", "unknown"),
            "deployment.environment": settings.app_env,
        }
    )
    provider = TracerProvider(
        resource=resource,
        sampler=TraceIdRatioBased(settings.otel_sample_rate),
    )
    exporter = (
        OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        if settings.otel_exporter_otlp_endpoint
        else ConsoleSpanExporter()
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _configured = True
    return provider


def instrument_app(app, settings: Any) -> None:
    if getattr(settings, "otel_enabled", False):
        FastAPIInstrumentor.instrument_app(app)


def instrument_engine(engine, settings: Any) -> None:
    if getattr(settings, "otel_enabled", False):
        # SQLAlchemy's event system attaches listeners to the synchronous
        # engine behind AsyncEngine, not to AsyncEngine itself.
        sync_engine = getattr(engine, "sync_engine", engine)
        SQLAlchemyInstrumentor().instrument(engine=sync_engine)


def instrument_clients(settings: Any) -> None:
    global _instrumented_redis, _instrumented_httpx, _instrumented_celery
    if not getattr(settings, "otel_enabled", False):
        return
    if not _instrumented_redis:
        RedisInstrumentor().instrument()
        _instrumented_redis = True
    if not _instrumented_httpx:
        HTTPXClientInstrumentor().instrument()
        _instrumented_httpx = True
    if not _instrumented_celery:
        CeleryInstrumentor().instrument()
        _instrumented_celery = True
