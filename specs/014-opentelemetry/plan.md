# Implementation plan

1. Add pinned OpenTelemetry API, SDK, OTLP exporter, and framework instrumentation dependencies.
2. Add validated settings with telemetry disabled by default.
3. Centralize provider setup and idempotent client instrumentation in `app/observability/telemetry.py`.
4. Initialize telemetry from the FastAPI and Celery process entrypoints; instrument each runtime SQLAlchemy engine.
5. Add ingestion execution span attributes and terminal status.
6. Add unit tests for disabled behavior, exporter selection, idempotency, and all instrumentation helpers.
7. Document local console export and collector usage, then run the full quality gate.
