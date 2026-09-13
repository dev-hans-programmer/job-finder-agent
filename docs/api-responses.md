# API response conventions

Application JSON success responses use a shared envelope:

```json
{
  "success": true,
  "data": {
    "id": "..."
  },
  "meta": {
    "request_id": "...",
    "api_version": "v1",
    "page": null,
    "page_size": null,
    "total": null
  }
}
```

Clients should read the resource from `data`, not from the top level. Collection endpoints put the list in `data` and pagination values in `meta`.

The request ID in `meta.request_id` matches the `X-Request-ID` response header and can be used to correlate API responses with logs and traces. V2 endpoints set `meta.api_version` to `v2`.

The following remain special by design:

- Health endpoints return simple readiness/liveness payloads for orchestrators.
- `/metrics` returns Prometheus exposition text.
- `204 No Content` endpoints return an empty body.
- Errors continue to use the existing `error` envelope.

Routes construct envelopes through `app/api/responses.py`; services and repositories remain unaware of HTTP formatting.
