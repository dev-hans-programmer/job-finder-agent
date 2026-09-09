# QA — Source Ingestion

## Prerequisites

Complete Specs 001–002. Configure a test Greenhouse or Lever source using a fixture/sandbox endpoint and a source-specific external ID.

## Test 1: Create and run a source

Create an enabled source through the configured source-management API or seed it through the documented fixture command. Then run:

```bash
curl -i -X POST http://localhost:8000/api/v1/sources/<SOURCE_ID>/run
```

Expected: HTTP `202` and a `run_id`. Poll the run status endpoint until it is `succeeded` or `partial`, with fetched and normalized counters.

## Test 2: Pagination

Use a fixture with at least two pages. Expected: all records are fetched exactly once, the next-page token/URL is followed, and the run counter equals the total records.

## Test 3: Malformed record

Add one record without a title or application URL. Expected: valid records complete, malformed record is counted as an error, and the run becomes `partial` rather than crashing.

## Test 4: Provider failure and duplicate trigger

Configure a fixture returning HTTP `500` or `429`. Expected: retries occur, `Retry-After` is respected where present, and the final run is failed with a safe error summary. Trigger the same source while it is running; expected: the existing run ID is returned and a second run is not created.

## Completion expectation

A permitted source can be run repeatedly, pagination and retries work, bad records are isolated, and run status/counters provide enough information to diagnose a failure.
