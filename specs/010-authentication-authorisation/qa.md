# QA Guide

## Prerequisites

Start PostgreSQL and Redis, configure `.env`, and apply migrations:

```bash
make infra-up
make migrate
make run
```

For a protected local environment, set `AUTH_REQUIRE_TOKEN=true`. To bootstrap an administrator, set `INITIAL_ADMIN_EMAIL=admin@example.com` before registering that email. Restart the API after changing environment variables.

## Automated verification

```bash
make lint
make coverage
```

Expected: lint passes and all tests pass with `Required test coverage of 100.0% reached`.

## Manual happy path

Register a user:

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"correct horse battery staple"}'
```

Expected: `201`, an ID, the email, and role `user` (plus `admin` when `INITIAL_ADMIN_EMAIL` matches).

Login and save both returned tokens:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"correct horse battery staple"}'
```

Expected: `200` with `access_token` and `refresh_token`. Call `/me` with the access token:

```bash
curl -i http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

Expected: `200` with the same user and roles. Refresh once and verify a new refresh token is returned. Reuse the old refresh token and expect `401`; the token family is revoked. Logout with the current refresh token and expect `204`.

Open `http://localhost:8000/docs`. Expected: one `Authorize` button near the top, backed by an HTTP Bearer scheme. Protected operations show a lock and use that authorization; health and auth registration/login operations remain public.

## RBAC checks

With a non-admin token, call `POST /api/v1/roles` and expect `403`. With a bootstrapped admin token, create:

```json
{"name":"recruiter","description":"Recruiting operators"}
```

Expected: `201` with the role ID. Assign it using `POST /api/v1/users/{user_id}/roles/recruiter`; expected: `204`.

## Negative cases

- Duplicate registration → `409`.
- Wrong password or unknown email → `401`.
- Missing, malformed, expired, or refresh-token-as-access-token Bearer token → `401`.
- Disabled user → `401`.
- Unknown target user or role → `404`.

Inspect PostgreSQL only to verify behavior: `users.password_hash` must contain an Argon2 hash, `refresh_tokens.token_hash` must contain a hash rather than the raw token, and revoked tokens must have `revoked_at` set.
