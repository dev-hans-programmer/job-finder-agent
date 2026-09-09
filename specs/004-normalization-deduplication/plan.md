# Implementation plan

1. Define canonical `JobCandidate` and `CanonicalJob` types.
2. Add `jobs` and `job_source_records` tables and Alembic migration.
3. Implement deterministic field normalizers and evidence-bearing parsers.
4. Implement dedupe key generation and similarity decision service.
5. Add transactional upsert/merge repository methods.
6. Connect ingestion output to normalization service.
7. Add unit and PostgreSQL integration tests using source fixtures.

Fuzzy matching should be conservative in MVP and produce a reviewable merge reason.
