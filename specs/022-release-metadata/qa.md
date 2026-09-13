# QA: Release notes and deployment metadata

## Automated verification

Run `make test-all`. This validates the version endpoint, metadata model,
release-note categorization, formatting, linting, and the existing 100% branch
coverage requirement.

## Version endpoint

Start the application and run:

```bash
curl -s http://localhost:8000/api/v1/version | jq
```

The response must contain `success: true` and `data` fields for `application`,
`version`, `commit_sha`, `build_timestamp`, and `environment`. In a CI-built
image, `commit_sha` must identify the deployed Git commit rather than
`unknown`.

## Release notes

Generate notes for the current repository:

```bash
make release-notes APP_VERSION=0.1.0 RELEASE_OUTPUT=/tmp/release-notes.md
cat /tmp/release-notes.md
```

Commits such as `feat: add job export`, `fix: handle provider timeout`, and
`perf: optimize job query` should appear under Features, Fixes, and Performance
respectively. Unknown prefixes should appear under Other.

For a release range:

```bash
make release-notes FROM_REF=v0.1.0 TO_REF=HEAD APP_VERSION=0.2.0
```

## Expected result

The running service can be traced to its exact image/commit, telemetry carries
the same identity, and release notes are reproducible from the selected Git
range.
