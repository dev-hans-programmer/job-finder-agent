# QA — Scheduling and End-to-End Workflows

## Prerequisites

Complete Specs 003–007. Start scheduler, worker, PostgreSQL, Redis, and provider fixtures.

## Test 1: Scheduled source run

Configure a source with a short test interval. Wait through one interval and inspect ingestion runs. Expected: one run starts at the configured cadence, acquires a lock, and produces jobs.

## Test 2: Full workflow

Use a fixture containing one new eligible job. Expected sequence: source run → normalized canonical job → dedupe → match result → one notification delivery. Confirm each record references the same job/run/profile context.

## Test 3: Rerun and unchanged job

Run the same fixture again. Expected: no duplicate canonical job, no duplicate notification, and no unnecessary embedding/LLM evaluation when the description hash and profile version are unchanged.

## Test 4: Changed job

Change the description or active profile version and rerun. Expected: a new match result is created and notification behavior follows the configured policy.

## Test 5: Failure isolation and resume

Make Source A fail while Source B succeeds. Expected: Source B completes, Source A is marked failed/partial, and a retry can resume without duplicating Source B's work.

## Completion expectation

The complete product flow is repeatable, resumable, idempotent, and isolated across sources and stages.
