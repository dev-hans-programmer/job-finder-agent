# Spec 005 — Explainable Matching

## Objective

Score canonical jobs from 0–100 using deterministic rules, semantic similarity, and optional structured LLM reasoning.

## Scope

Implement hard exclusions, component scoring, configurable weights, embedding cache/provider interface, LLM adapter/schema validation, match persistence, threshold decisions, and evidence-based explanations.

## Invariants

- Hard exclusions cannot be overridden by embeddings or the LLM.
- Missing data is not automatically negative unless configured.
- Scores are clamped to 0–100 and component weights total 100.
- Every inference records matcher/model/prompt versions.
- LLM output is untrusted input and must pass schema validation.

## Acceptance criteria

- Django can be semantically related to a FastAPI backend preference without automatic rejection.
- A configured strict must-have can reject a job when absent.
- Excluded frontend/support/PHP roles are not notified.
- Match output contains component scores, confidence, matched, missing, concerns, and reasoning.
- Embedding/LLM failure falls back safely and lowers confidence where appropriate.
- Match results are reproducible against stored profile and description hash.
- Unit, provider contract, PostgreSQL integration, and API tests achieve 100% branch coverage.

## Required tests

Golden unit tests for score math and exclusions; embedding cache hit/miss; LLM malformed/unsafe/valid responses; repository persistence; API match retrieval; end-to-end fixture matching.
