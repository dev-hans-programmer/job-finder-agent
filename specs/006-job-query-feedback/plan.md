# Implementation plan

1. Add feedback table and lifecycle constraints through Alembic.
2. Implement query repository with safe allow-listed sorting and filters.
3. Implement job detail aggregation and latest-match lookup.
4. Implement feedback service and endpoint.
5. Add API pagination, authorization boundary, and integration tests.

Use keyset pagination later if volume requires it; MVP may use bounded offset pagination.
