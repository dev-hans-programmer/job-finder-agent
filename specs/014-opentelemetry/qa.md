# QA — OpenTelemetry

## Automated checks

From the repository root:

```bash
make check
```

Expected: formatting, lint, API/integration/unit tests, and branch coverage pass at 100%.

## Local console-span verification

1. Copy `.env.example` to `.env` and set `OTEL_ENABLED=true`.
2. Leave `OTEL_EXPORTER_OTLP_ENDPOINT` empty.
3. Start dependencies and apply migrations: `make services-up && make migrate`.
4. Start the API with `make run`.
5. Call `curl http://localhost:8000/health/live`.
6. Inspect the API terminal.

Expected: the request succeeds and a completed OpenTelemetry span is printed by the console exporter. The response remains the normal health response.

## OTLP collector verification

1. Set `OTEL_ENABLED=true` and `OTEL_EXPORTER_OTLP_ENDPOINT` to an OTLP/HTTP collector endpoint, for example `http://localhost:4318/v1/traces`.
2. Start the API and invoke a health endpoint, a protected API endpoint, and an ingestion run.
3. Inspect the configured collector.

Expected: spans use service name `OTEL_SERVICE_NAME`, include HTTP/database/client activity where applicable, and ingestion spans contain `job.source_id`, `job.run_id`, and a terminal `job.status`.

## Disabled behavior

1. Set `OTEL_ENABLED=false`.
2. Restart the API and worker.
3. Invoke the same endpoints.

Expected: all endpoints and workers continue to work, no exporter output is produced, and no collector is required.

## Sign-off

- [ ] Automated quality gate passes.
- [ ] Console spans verified locally, or OTLP spans verified in a collector.
- [ ] Disabled mode verified.
