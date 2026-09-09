# Test layout

Tests are organized by implementation spec:

```text
tests/
  unit/
    test_*.py     # pure functions, schemas, and domain services
  integration/
    test_*.py     # PostgreSQL, Redis, filesystem, and provider-boundary tests
  api/
    test_*.py     # FastAPI endpoint and HTTP contract tests
  conftest.py     # global test configuration/fixtures
```

Each spec owns its tests and fixtures. A spec's tests must pass independently:

```bash
uv run pytest tests/unit tests/integration tests/api -q
uv run pytest tests/unit tests/integration tests/api --cov=app --cov-branch --cov-report=term-missing
```

The preferred project-level commands are available through the root `Makefile`:

```bash
make install
make services-up
make migrate
make run
```

In another terminal, use `make check` for formatting, linting, and the complete test/coverage gate.

Install the git hook once with `make install-hooks`. It runs file hygiene checks, Ruff, and the full 100%% coverage test gate before each commit. Run the same checks manually with `make pre-commit`.

When later specs are implemented, their tests should be added directly to the applicable test-type folder. Use descriptive filenames and pytest markers if a test needs to be associated with a particular spec.
