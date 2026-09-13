# Spec 015 — Prometheus, Grafana, Loki, and Tempo

## Goal

Provide a local, repeatable observability stack that collects application metrics, logs, and distributed traces and makes them searchable from Grafana.

## Scope

- Prometheus scraping the API `/metrics` endpoint.
- Grafana provisioning Prometheus, Loki, and Tempo datasources and an overview dashboard.
- Loki receiving Docker container logs through Grafana Alloy.
- Tempo receiving traces through the OpenTelemetry Collector.
- API request counters and 5xx counters in Prometheus format.
- Structured request logs containing route, status, duration, and request ID.
- Compose targets and operational documentation.

## Acceptance criteria

1. `make app-up` starts the application and observability services.
2. Prometheus reports the API target as healthy.
3. Grafana opens with all three datasources provisioned and the Job Radar dashboard present.
4. API requests appear as metrics and logs.
5. API and worker traces are queryable in Tempo.
6. Existing application behavior is preserved when the observability stack is stopped.
7. Unit, API, integration, lint, and 100% branch-coverage checks pass.

There is no database schema change in this spec.
