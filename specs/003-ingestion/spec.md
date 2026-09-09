# Spec 003 — Source Ingestion

## Objective

Fetch job records from permitted sources through replaceable, idempotent adapters.

## Scope

Implement source configuration, adapter protocol, Greenhouse and Lever adapters, pagination, rate limits, retries, ingestion-run tracking, and manual run API. No browser automation or authenticated LinkedIn scraping is included.

## Contracts

- `POST /api/v1/sources/{source_id}/run` returns `202` and a run ID.
- Duplicate active run requests return the existing run ID.
- Adapter output is a typed `RawJobRecord`; malformed records are isolated and counted.
- Every run ends as `succeeded`, `partial`, or `failed` with counters and errors.
- Provider requests use bounded timeout, retry, and pagination behavior.

## Acceptance criteria

- A fixture-backed Greenhouse or Lever response produces typed records.
- Rate limits and `Retry-After` are respected.
- One bad record does not abort the run.
- Provider outage marks the run failed without affecting other sources.
- Source and run state are persisted through Alembic-managed tables.
- Unit, adapter contract, PostgreSQL integration, and API tests provide 100% branch coverage for changed code.

## Required tests

Unit: pagination, retry classification, backoff policy, record validation, adapter configuration.

Contract: representative Greenhouse/Lever fixtures, empty pages, malformed records, provider errors.

Integration/API: source CRUD if included, manual run, duplicate run lock, run status, database counters.
