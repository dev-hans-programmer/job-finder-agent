# Spec 010 — Authentication and Authorisation

## Objective

Provide secure, testable identity and role-based access control for the Job Radar API.

## Scope

- Register users with Argon2 password hashes.
- Issue short-lived JWT access tokens and persisted, rotating refresh tokens.
- Support refresh-token reuse detection, family revocation, logout, disabled users, and `/me`.
- Provide configurable role creation and role assignment protected by the `admin` role.
- Support first-admin bootstrap through `INITIAL_ADMIN_EMAIL`.
- Keep the route → service → repository boundary.

## API contract

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Create a user and assign the configured default role |
| POST | `/api/v1/auth/login` | Validate credentials and issue tokens |
| POST | `/api/v1/auth/refresh` | Rotate a refresh token |
| POST | `/api/v1/auth/logout` | Revoke a refresh-token family |
| GET | `/api/v1/auth/me` | Return the authenticated user and roles |
| POST | `/api/v1/roles` | Create a role; admin only |
| POST | `/api/v1/users/{user_id}/roles/{role_name}` | Assign a role; admin only |

## Acceptance criteria

- Passwords are never persisted or logged in plaintext.
- Invalid credentials, malformed tokens, expired tokens, wrong token types, disabled users, and missing roles are rejected.
- Refresh rotation invalidates the previous token and reuse revokes the complete token family.
- Protected endpoints accept valid Bearer tokens and return 401 otherwise.
- Admin-only endpoints return 403 for non-admin users.
- PostgreSQL schema changes are delivered through Alembic.
- Unit, integration, and API tests pass with 100% statement and branch coverage.
