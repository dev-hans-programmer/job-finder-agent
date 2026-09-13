# QA: Security hardening

## Local HTTP behavior

Run the API normally:

```bash
make services-up
make migrate
make app-up
```

```bash
curl -i http://localhost:8005/health/live
```

Expected headers include:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; frame-ancestors 'none'
```

The `/docs` and `/redoc` pages use a narrowly scoped documentation policy that
allows FastAPI's configured CDN assets and inline bootstrap script. This is why
Swagger can render while normal application responses retain the stricter
same-origin policy.

`Strict-Transport-Security` must not be present locally. HTTPS certificates are
not required for this setup.

## CORS

Set an explicit origin in `.env`:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000
CORS_ALLOW_CREDENTIALS=false
```

Restart the API and verify an OPTIONS request from that origin receives the
configured CORS response headers. An unlisted origin must not receive
`Access-Control-Allow-Origin`.

## JWT secret validation

For staging or production, configure a random secret of at least 32 characters:

```env
APP_ENV=staging
JWT_SECRET_KEY=<random-secret-at-least-32-characters>
```

The application must reject the development default or a shorter value at
startup. Local and testing environments remain usable without HTTPS and may use
test secrets.

## Refresh-token replay

1. Login and save the refresh token.
2. Refresh once successfully; the original token is rotated and revoked.
3. Submit the original refresh token again.
4. Expect HTTP `401` with `refresh token replay detected`.
5. Verify that the entire refresh-token family can no longer be used.

## CSRF

CSRF is disabled by default because the current API uses bearer tokens and sends
refresh tokens in the request body. If cookie authentication is introduced,
set `CSRF_ENABLED=true`; unsafe cookie-authenticated requests then require a
matching `X-CSRF-Token` and `csrf_token` cookie.

## Automated checks

```bash
make test-all
uv run pip-audit --strict
```

CI additionally builds the Docker image and scans it with Trivy for high and
critical vulnerabilities. The ASVS checklist is maintained alongside this
specification and should be reviewed before production releases.
