# QA — Consistent API responses

## Success envelope

Call any JSON application endpoint, for example:

```bash
curl -i http://localhost:8000/api/v1/sources
```

Expected response body:

```json
{
  "success": true,
  "data": [],
  "meta": {
    "request_id": "...",
    "api_version": "v1",
    "page": null,
    "page_size": null,
    "total": null
  }
}
```

The `meta.request_id` value must match the `X-Request-ID` response header.

## Pagination

```bash
curl 'http://localhost:8000/api/v1/jobs?page=1&page_size=10'
```

Expected: jobs are in `data`, while `page`, `page_size`, and `total` are in `meta`.

## V2 metadata

```bash
curl http://localhost:8000/api/v2/health/live
```

The health probe remains intentionally simple. Use the V2 preferences endpoint for the application envelope and verify:

```json
"meta": {
  "api_version": "v2"
}
```

## Exceptions

Verify these remain unchanged:

- `GET /health/live` returns the probe payload directly.
- `GET /metrics` returns Prometheus text.
- Delete/logout/role assignment `204` responses have no body.
- Errors retain the `error` object and request ID.

## Automated verification

```bash
make check
```

Expected: all tests pass and total branch coverage is 100%.

## Sign-off

- [ ] JSON success responses are enveloped.
- [ ] Request IDs correlate between body and header.
- [ ] Pagination metadata is correct.
- [ ] V2 metadata is correct.
- [ ] Infrastructure exceptions remain compatible.
- [ ] Swagger documents the envelope.
