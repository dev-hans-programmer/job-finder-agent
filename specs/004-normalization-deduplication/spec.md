# Spec 004 — Normalization and Deduplication

## Objective

Convert heterogeneous source records into canonical jobs and merge repeated listings without losing provenance.

## Scope

Implement canonical job extraction, title/company/location/work-mode/experience/salary parsing, description hashing, deterministic deduplication, fuzzy fallback, and source provenance.

## Rules

Deduplication order: source ID, normalized application URL, external ATS identity, then company + title + location + description similarity. Every merge retains all source records and timestamps.

Unknown values remain unknown. Parsers must return evidence or confidence for extracted fields.

## Acceptance criteria

- Equivalent source records produce one canonical job.
- Material description changes update the canonical job and mark it for re-matching.
- Distinct roles with same company/title remain separate when location or description evidence differs.
- Salary and experience parsing supports absent and ambiguous values without false values.
- Migration creates all required job/source-record indexes.
- Unit, fixture, repository, and API integration tests achieve 100% branch coverage for this scope.

## Required tests

Unit: normalization aliases, parsing, hash generation, every dedupe strategy, confidence thresholds.

Integration: upsert/merge behavior, provenance retention, changed-job detection, transaction rollback, migration.
