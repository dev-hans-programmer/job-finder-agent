# QA — Observability, Security, and Deployment

## Prerequisites

Complete all previous specs. Run the CI-equivalent command locally and use a disposable PostgreSQL database for restore testing.

## Test 1: Logs and redaction

Run an ingestion and notification workflow. Inspect logs. Expected: request/run/source/job/profile IDs are present where applicable; passwords, API keys, bot tokens, and email secrets are absent or redacted.

## Test 2: Metrics and health

Trigger a successful run, a failed provider call, a match, and a notification. Inspect metrics and health endpoints. Expected: counters/latencies change for each event, live health remains process-only, and ready health reflects PostgreSQL/Redis state.

## Test 3: Configuration safety

Start using `.env.example` with placeholder values. Expected: no secret is embedded in the image or repository, and startup clearly reports missing required production credentials.

## Test 4: CI coverage gate

Run the documented CI command. Expected: migrations, unit tests, integration/API tests, linting, and branch coverage run; the build fails if coverage is below 100%.

## Test 5: Backup and restore

Create a disposable backup, destroy the disposable database, restore it, run `alembic current`, and query a known job/profile. Expected: schema and representative data are recoverable.

## Test 6: Deletion and retention

Create a test user, jobs, raw payloads, and notifications; invoke the documented deletion flow. Expected: user-owned data is removed or anonymized according to policy, deletion is audited, and unrelated users/data remain intact.

## Completion expectation

The service can be diagnosed, deployed without leaking secrets, tested with enforced quality gates, backed up/restored, and operated safely.
