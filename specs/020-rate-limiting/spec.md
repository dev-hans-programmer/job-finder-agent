# Spec 020: Rate limiting

## Goal

Protect the API from accidental or hostile request bursts with a Redis-backed,
configurable fixed-window rate limiter.

## Requirements

- Apply limits to API requests while exempting health checks, metrics, and API documentation.
- Use a lower, independent limit for registration, login, and refresh endpoints.
- Identify unauthenticated callers by client IP and bearer-token callers by a one-way token hash.
- Honor `X-Forwarded-For` only when the direct peer is configured in `TRUSTED_PROXY_IPS`.
- Return HTTP 429 with structured error data and `Retry-After`, limit, remaining, and reset headers.
- Fail open for general traffic by default when Redis is unavailable; fail closed for auth traffic.
- Keep the policy independent of routes and persist no new database data.

## Acceptance criteria

The limiter is enabled in production defaults, configurable through environment
variables, covered by unit/API/integration tests, and documented for operators.
