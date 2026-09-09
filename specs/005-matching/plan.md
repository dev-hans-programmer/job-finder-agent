# Implementation plan

1. Define matching domain types and versioned output schema.
2. Implement pure rule engine and weighted scorer first.
3. Add `match_results` and optional embedding-cache persistence/migration.
4. Implement embedding provider interface and hash-keyed cache.
5. Implement structured LLM adapter with timeout, budget, parser, and safe fallback.
6. Implement matching service and job/profile selection query.
7. Add golden fixtures and integration/API tests.

LLM and embeddings are disabled by default in local development; deterministic tests must not require network access.
