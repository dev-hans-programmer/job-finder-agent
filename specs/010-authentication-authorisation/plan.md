# Plan

1. Add authentication dependencies and Argon2/JWT security helpers.
2. Add user password state, roles, user-role links, and refresh-token persistence models.
3. Add migration `20260913_007_auth`.
4. Implement the authentication repository and application service.
5. Add dependency providers for current-user lookup and role checks.
6. Add versioned auth and RBAC routes using injected services.
7. Add configurable initial-admin bootstrap and document local/production settings.
8. Add unit, PostgreSQL-backed integration, and HTTP API coverage plus manual QA.
