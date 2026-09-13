# QA: Rate limiting

## Automated verification

Run `make test-all`. It starts the isolated PostgreSQL/Redis services, applies
migrations, runs unit/integration/API tests with 100% branch coverage, and
stops the test services afterward.

## Manual verification

1. Copy `.env.example` to `.env`, keep `RATE_LIMIT_ENABLED=true`, and start the
   stack with `make services-up`, `make migrate`, and `make app-up`.
2. Confirm normal traffic receives rate-limit headers:

   ```bash
   curl -i http://localhost:8000/health/live
   curl -i http://localhost:8000/api/v1/jobs
   ```

   Health should not have rate-limit headers. An API endpoint should have
   `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
3. Temporarily set `RATE_LIMIT_GENERAL_REQUESTS=2`, restart the API, and call
   `/api/v1/jobs` three times from the same client. The third response should be
   `429`, contain error code `RATE_LIMIT_EXCEEDED`, and include `Retry-After`.
4. Set `RATE_LIMIT_AUTH_REQUESTS=2` and repeat against
   `/api/v1/auth/login`; auth traffic must use the auth limit independently.
5. Verify `/health/live`, `/health/ready`, `/metrics`, `/docs`, and
   `/openapi.json` remain available even after the API limit is exhausted.
6. To verify proxy handling, set `TRUSTED_PROXY_IPS` to the API's actual direct
   proxy address and send different `X-Forwarded-For` values. Without a trusted
   peer, those headers must not change the caller identity.

## Expected result

Allowed responses carry current quota headers; exhausted responses are
structured 429s; auth limits are stricter; observability endpoints remain
usable; and no rate-limit rows appear in PostgreSQL.
