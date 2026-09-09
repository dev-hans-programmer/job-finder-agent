# QA — Normalization and Deduplication

## Prerequisites

Complete Spec 003 and use a source fixture that emits canonical and duplicate records.

## Test data

Create these records:

1. Same external ID and URL as an existing job.
2. Same job with URL tracking parameters changed.
3. Same company/title/location with a near-identical description.
4. Same company/title but a different city and responsibilities.
5. A job with no salary or experience information.

## Test 1: Canonical normalization

Run ingestion and inspect `GET /api/v1/jobs`. Expected: title, normalized company, locations, work mode, parsed salary/experience where available, description hash, and application URL are populated. Missing values show as unknown/null, not invented values.

## Test 2: Duplicate merge

Ingest records 1–3. Expected: one canonical job, all source records retained, duplicate count increased, and the most complete/latest representation displayed.

## Test 3: Distinct jobs remain separate

Ingest record 4. Expected: a second canonical job because location/responsibility evidence differs.

## Test 4: Changed listing

Modify the description of the first job and rerun ingestion. Expected: same canonical job ID, changed description hash, updated `last_seen_at`, and a flag/state indicating it requires re-matching.

## Completion expectation

Duplicate listings collapse safely without losing provenance, genuinely different jobs remain separate, and all parsed values can be traced back to source text.
