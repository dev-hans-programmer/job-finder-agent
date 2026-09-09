# Implementation plan

1. Define Pydantic request/domain schemas and normalization rules.
2. Add `users` and `preference_profiles` tables through Alembic.
3. Implement repository and profile service with transaction boundaries.
4. Add API routes and standard error handling.
5. Add PostgreSQL fixtures that always apply migrations.
6. Test concurrent activation and immutable version behavior.

The database must enforce uniqueness of `(user_id, version)` and one active profile per user, using a partial unique index where supported.

Verification: migration upgrade/downgrade test, repository integration tests, API tests, branch coverage at 100%.
