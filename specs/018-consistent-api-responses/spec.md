# Spec 018 — Consistent API success responses

## Goal

Standardize JSON success responses across application endpoints while preserving the existing structured error contract and infrastructure-specific response formats.

## Contract

A successful JSON response has this shape:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "...",
    "api_version": "v1",
    "page": null,
    "page_size": null,
    "total": null
  }
}
```

Collection endpoints put the collection in `data` and pagination values in `meta`.

## Scope

- Shared generic success and metadata schemas.
- Shared response factory using the request ID middleware value.
- V1 and V2 JSON application endpoints use the envelope and declare it in OpenAPI.
- Health probes remain simple probe responses.
- Prometheus metrics remain Prometheus text responses.
- `204 No Content` operations remain empty responses.
- Existing structured error responses remain unchanged.

## Acceptance criteria

1. Every in-scope successful JSON endpoint contains `success`, `data`, and `meta`.
2. `meta.request_id` matches the `X-Request-ID` response header.
3. V2 responses identify `api_version: v2` in metadata.
4. Collection pagination is represented in metadata.
5. Health, metrics, and 204 contracts are not incorrectly wrapped.
6. Swagger shows the shared response envelope.
7. Unit, API, integration, lint, and 100% branch-coverage checks pass.

There is no database schema change in this spec.
