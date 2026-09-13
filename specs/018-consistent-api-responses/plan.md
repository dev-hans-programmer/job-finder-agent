# Implementation plan

1. Create generic `SuccessResponse[T]` and `ResponseMeta` schemas.
2. Create a shared response factory that copies request correlation metadata.
3. Update V1 and V2 application routes and response annotations.
4. Preserve infrastructure and no-content exceptions.
5. Update API/unit tests for the new contract and request metadata.
6. Document client migration from direct DTOs to `data` envelopes.
7. Run formatting, lint, tests, coverage, and OpenAPI validation.
