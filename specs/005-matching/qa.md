# QA — Explainable Matching

## Prerequisites

Complete Specs 002 and 004. Disable external LLM/embedding calls for deterministic manual testing, or configure the documented provider sandbox.

## Test data

Use the active profile with Python/PostgreSQL, preferred backend titles, Mumbai/Bangalore, remote/hybrid, 7–15 years, minimum 40 LPA, and exclusions frontend/PHP.

Create these jobs:

- **Job A:** Senior Backend Engineer; Python, Django, PostgreSQL, AWS; Mumbai; hybrid; 8 years; 45–55 LPA; FinTech.
- **Job B:** Frontend Engineer; React, PHP; Mumbai; hybrid; 8 years; 45 LPA.
- **Job C:** Backend Engineer; Python; Bangalore; remote; salary unknown; experience unknown.

## Test 1: Strong semantic match

Run matching for Job A and retrieve `GET /api/v1/jobs/<JOB_ID>/match`.

Expected: score above the configured threshold, decision `notify`, Python/PostgreSQL/AWS/FinTech in matched criteria, FastAPI possibly in missing criteria, and reasoning that Django is related backend experience rather than an automatic rejection.

## Test 2: Hard exclusion

Match Job B. Expected: decision `reject` regardless of any otherwise positive score, with the exclusion term and evidence in concerns/reasons.

## Test 3: Unknown fields

Match Job C. Expected: missing salary/experience are represented as unknown; the job is not rejected solely because those fields are absent; confidence reflects uncertainty.

## Test 4: Provider failure

Force embedding or LLM provider failure. Expected: deterministic rule score is retained, result is persisted, confidence is reduced if applicable, and the API remains available.

## Completion expectation

Scores are explainable and reproducible, exclusions are absolute, semantic similarity prevents brittle keyword rejection, and provider failures degrade safely.
