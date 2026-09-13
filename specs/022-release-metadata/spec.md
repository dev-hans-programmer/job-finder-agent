# Spec 022: Release notes and deployment metadata

## Goal

Make every build and deployment identifiable and generate readable release
notes from Git history.

## Requirements

- Expose application version, commit SHA, build timestamp, and environment at
  `GET /api/v1/version` using the standard success envelope.
- Include version and commit attributes in OpenTelemetry resources.
- Generate categorized Markdown notes from conventional commit prefixes.
- Support optional commit ranges and custom output paths.
- Inject build metadata into staging and production container images.
- Keep this mechanism independent of business data and PostgreSQL migrations.

## Acceptance criteria

The version endpoint identifies the running build, CI images contain immutable
commit metadata, and `make release-notes` creates a categorized Markdown file.
