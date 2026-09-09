# QA — Preference Profiles

## Prerequisites

Complete Spec 001 and start the API with PostgreSQL. Use a test user ID supported by the MVP authentication setup.

## Test data: valid profile

Save as `valid-preferences.json`:

```json
{
  "titles": ["Senior Software Engineer", "Backend Engineer"],
  "skills": {"must_have": ["Python", "PostgreSQL"], "nice_to_have": ["AWS", "Redis"]},
  "locations": {"preferred": ["Mumbai", "Bangalore"]},
  "work_mode": ["remote", "hybrid"],
  "experience": {"min": 7, "max": 15},
  "salary": {"minimum_lpa": 40},
  "companies": {"preferred": ["Razorpay", "Stripe"]},
  "exclusions": ["frontend", "PHP"],
  "matching": {"minimum_score": 75}
}
```

## Test 1: Validate without persisting

```bash
curl -X POST http://localhost:8000/api/v1/preferences/validate \
  -H 'Content-Type: application/json' --data @valid-preferences.json
```

Expected: HTTP `200` with normalized preferences. Call `GET /api/v1/preferences` and confirm no new version was created.

## Test 2: Create a profile version

```bash
curl -X PUT http://localhost:8000/api/v1/preferences \
  -H 'Content-Type: application/json' --data @valid-preferences.json
```

Expected: HTTP `200` or `201`, version `1`, active status, and normalized arrays without duplicates. Repeat after changing the threshold; expect version `2` while version `1` remains unchanged.

## Test 3: Invalid profile

Change `minimum_score` to `150`, set `experience.min` above `experience.max`, and add an unsupported work mode. Expected: HTTP `422`, field-level details, and no additional database version.

## Completion expectation

A valid profile can be saved and retrieved, previous versions are immutable, exactly one version is active, and invalid input never partially persists.
