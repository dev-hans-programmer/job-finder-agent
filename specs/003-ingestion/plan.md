# Implementation plan

1. Define `SourceAdapter`, `RawJobRecord`, source configuration, and provider error types.
2. Add `sources` and `ingestion_runs` tables and migration.
3. Implement HTTP client policy with timeouts, retries, and rate limiting.
4. Implement Greenhouse and Lever adapters using fixture-driven contracts.
5. Implement ingestion service and run repository.
6. Add Redis source locks and manual-run API.
7. Add tests with mocked HTTP and real PostgreSQL/Redis.

Raw provider payload retention must be configurable and must not contain secrets.
