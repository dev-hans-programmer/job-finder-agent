# Spec 008 — Scheduling and End-to-End Workflows

## Objective

Run ingestion, normalization, matching, and notification as resilient scheduled workflows.

## Scope

Implement scheduler configuration, source cadence, workflow orchestration, worker boundaries, run status, retries/dead-letter handling, and manual workflow triggering.

## Acceptance criteria

- Enabled sources run on their configured cadence.
- A failed source does not stop other sources.
- Workflow stages are resumable and idempotent.
- Changed descriptions are re-matched; unchanged jobs reuse valid results.
- A complete fixture run produces one canonical job, one match, and at most one notification.
- Partial/failure status and counters are persisted and queryable.
- Unit, Redis/PostgreSQL integration, API, and end-to-end tests achieve 100% branch coverage.
