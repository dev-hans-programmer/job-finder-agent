# Spec 021: Load testing

## Goal

Provide repeatable performance tests for the API and ingestion trigger so
capacity, latency, and failure thresholds are measured before deployment.

## Requirements

- Use Locust with realistic authenticated read-heavy user behavior.
- Exercise registration/login, current-user, jobs, sources, health, and an
  optional source run when `LOADTEST_SOURCE_ID` is provided.
- Configure target URL, users, spawn rate, run duration, credentials, and wait
  times through environment variables or Make targets.
- Produce CSV statistics and an HTML report.
- Fail headless runs when aggregate failure percentage or p95 latency exceeds
  configured thresholds.
- Keep load tests isolated from the application runtime and database schema.

## Acceptance criteria

`make loadtest` opens the Locust UI, `make loadtest-headless` produces ignored
reports and enforces thresholds, and the scenario can authenticate against a
staging/local deployment without hardcoded credentials.
