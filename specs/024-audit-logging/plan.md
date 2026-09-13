# Implementation plan

1. Add the `AuditEvent` SQLAlchemy model and reversible Alembic migration.
2. Add the audit repository and domain service.
3. Add an injectable audit-service dependency.
4. Record authentication and account-security events at the route boundary.
5. Add unit tests for event construction and persistence.
6. Add API/integration coverage for request metadata and success/failure events.
7. Document manual verification with PostgreSQL queries.
