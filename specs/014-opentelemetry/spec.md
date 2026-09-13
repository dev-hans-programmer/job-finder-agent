# Spec 014 — OpenTelemetry instrumentation

## Goal

Instrument the API and background processes with optional OpenTelemetry tracing so requests, database queries, HTTP provider calls, Redis operations, and Celery tasks can be correlated in an external collector.

## Scope

- Configure a service name, environment, sampling ratio, and OTLP HTTP endpoint from environment settings.
- Keep telemetry disabled by default and use console span export when enabled without an endpoint for local verification.
- Instrument FastAPI, SQLAlchemy, HTTPX, Redis, and Celery.
- Add an explicit span around ingestion execution with source and run identifiers.
- Preserve application behavior when telemetry is disabled.

## Acceptance criteria

1. `OTEL_ENABLED=false` creates no exporters and does not instrument clients.
2. `OTEL_ENABLED=true` configures a tracer provider with the configured sample rate and service resource.
3. An OTLP endpoint uses OTLP HTTP export; an omitted endpoint uses console export.
4. API and worker processes initialize telemetry through their normal entrypoints.
5. Ingestion spans include `job.source_id`, `job.run_id`, and a terminal status.
6. Existing unit, integration, API, lint, and 100% branch-coverage checks pass.

There is no database schema change in this spec.
