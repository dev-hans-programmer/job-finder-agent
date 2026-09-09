SHELL := /bin/sh

UV ?= uv
PYTEST := $(UV) run pytest
COMPOSE := docker compose

.PHONY: help install install-hooks pre-commit services-up services-down services-logs migrate migration
.PHONY: run test test-unit test-integration test-api coverage lint format check qa clean

help:
	@printf '%s\n' \
	  'install            Install/sync project dependencies' \
	  'install-hooks      Install the pre-commit git hook' \
	  'pre-commit         Run all pre-commit hooks on the repository' \
	  'services-up        Start PostgreSQL and Redis' \
	  'services-down      Stop PostgreSQL and Redis' \
	  'services-logs      Follow PostgreSQL/Redis logs' \
	  'migrate            Apply Alembic migrations' \
	  'migration          Create a new Alembic migration (MSG="...")' \
	  'run                Run the FastAPI development server' \
	  'test               Run all tests' \
	  'test-unit          Run unit tests' \
	  'test-integration   Run integration tests' \
	  'test-api           Run API tests' \
	  'coverage           Run tests with 100%% branch coverage requirement' \
	  'lint               Run Ruff checks' \
	  'format             Format Python files with Ruff' \
	  'check              Run format check, lint, and tests' \
	  'qa                 Start services, migrate, then run full checks' \
	  'clean              Remove local Python/test caches'

install:
	$(UV) sync

install-hooks: install
	$(UV) run pre-commit install

pre-commit:
	$(UV) run pre-commit run --all-files

services-up:
	$(COMPOSE) up -d

services-down:
	$(COMPOSE) down

services-logs:
	$(COMPOSE) logs -f postgres redis

migrate:
	$(UV) run alembic upgrade head

migration:
	@test -n "$(MSG)" || (echo 'Usage: make migration MSG="describe the change"' && exit 1)
	$(UV) run alembic revision -m "$(MSG)"

run:
	$(UV) run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(PYTEST) tests/unit tests/integration tests/api -q

test-unit:
	$(PYTEST) tests/unit -q

test-integration:
	$(PYTEST) tests/integration -q

test-api:
	$(PYTEST) tests/api -q

coverage:
	$(PYTEST) tests/unit tests/integration tests/api --cov=app --cov-branch --cov-report=term-missing

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

check:
	$(UV) run ruff format --check .
	$(UV) run ruff check .
	$(MAKE) coverage

qa: services-up migrate check

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '.coverage' \) -delete
