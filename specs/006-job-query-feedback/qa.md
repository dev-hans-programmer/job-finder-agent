# QA — Job Queries and User Feedback

## Prerequisites

Complete Specs 004–005 and have at least three jobs with different scores, statuses, locations, and companies.

## Test 1: List and filter

```bash
curl 'http://localhost:8000/api/v1/jobs?min_score=75&location=Mumbai&page=1&page_size=10'
```

Expected: only matching jobs are returned, pagination metadata is present, and sorting is stable across repeated requests.

## Test 2: Detail and match

```bash
curl http://localhost:8000/api/v1/jobs/<JOB_ID>
curl http://localhost:8000/api/v1/jobs/<JOB_ID>/match
```

Expected: detail includes canonical data, source provenance, latest match, notification state, and feedback. Match endpoint returns the active profile's latest result.

## Test 3: Feedback

```bash
curl -X POST http://localhost:8000/api/v1/jobs/<JOB_ID>/feedback \
  -H 'Content-Type: application/json' \
  -d '{"label":"saved","note":"Strong backend role"}'
```

Expected: feedback is persisted and visible in job detail. Repeat the same request and confirm the documented idempotent behavior.

## Test 4: Invalid and isolated access

Request a nonexistent job and an invalid sort field. Expected: standard `404` and `422` errors. If multiple users are enabled, confirm a user cannot query another user's job.

## Completion expectation

Users can reliably find, inspect, filter, and label jobs without unstable pagination or cross-user data exposure.
