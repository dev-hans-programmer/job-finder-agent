# Implementation plan

1. Add validated rate-limit settings and local environment examples.
2. Implement a Redis fixed-window service and HTTP middleware.
3. Register the middleware after request-ID setup so rejected responses retain request IDs.
4. Add unit, API, and Redis integration coverage for allowed, rejected, exempt, and unavailable paths.
5. Run the full isolated test lifecycle and lint/format checks.

No Alembic migration is required because rate-limit state is ephemeral Redis data.
