SHELL := /bin/sh

UV ?= uv
PYTEST := $(UV) run pytest
COMPOSE := docker compose

.PHONY: help install install-hooks pre-commit services-up services-down services-logs app-up app-down app-logs
.PHONY: migrate migration run run-api run-worker run-scheduler run-flower backup backup-verify restore run-all test test-unit test-integration test-api coverage lint format check qa clean

help:
	@printf '%s\n' \
	  'install            Install/sync project dependencies' \
	  'install-hooks      Install the pre-commit git hook' \
	  'pre-commit         Run all pre-commit hooks on the repository' \
	  'services-up        Start PostgreSQL and Redis' \
	  'services-down      Stop PostgreSQL and Redis' \
	  'services-logs      Follow PostgreSQL/Redis logs' \
	  'app-up             Start API, worker, and scheduler containers' \
	  'app-down           Stop API, worker, and scheduler containers' \
	  'app-logs           Follow API/worker/scheduler logs' \
	  'migrate            Apply Alembic migrations' \
	  'migration          Create a new Alembic migration (MSG="...")' \
	  'run                Run the FastAPI development server' \
	  'run-api            Run the API process' \
	  'run-worker         Run the worker process' \
	  'run-scheduler      Run the scheduler process' \
	  'run-flower         Run the Celery monitoring dashboard' \
	  'backup             Create a PostgreSQL backup' \
	  'backup-verify      Verify a PostgreSQL backup' \
	  'restore            Restore a backup into the configured database' \
	  'run-all            Start all application processes in Docker' \
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
	$(COMPOSE) up -d postgres redis

services-down:
	$(COMPOSE) down

services-logs:
	$(COMPOSE) logs -f postgres redis

app-up:
	$(COMPOSE) up -d --build api worker scheduler flower backup

app-down:
	$(COMPOSE) stop api worker scheduler flower backup

app-logs:
	$(COMPOSE) logs -f api worker scheduler flower

migrate:
	$(UV) run alembic upgrade head

migration:
	@test -n "$(MSG)" || (echo 'Usage: make migration MSG="describe the change"' && exit 1)
	$(UV) run alembic revision -m "$(MSG)"

run:
	$(MAKE) run-api

run-api:
	$(UV) run uvicorn app.main:app --reload --host 127.0.0.1 --port 8005

run-worker:
	$(UV) run python -m app.processes.worker

run-scheduler:
	$(UV) run python -m app.processes.scheduler

run-flower:
	$(UV) run celery -A app.workers.celery_app flower --port=5555

backup:
	$(COMPOSE) run --rm backup python -m app.backup.cli backup

backup-verify:
	@test -n "$(BACKUP)" || (echo 'Usage: make backup-verify BACKUP=backups/file.dump' && exit 1)
	$(COMPOSE) run --rm backup python -m app.backup.cli verify "/backups/$$(basename "$(BACKUP)")"

restore:
	@test -n "$(BACKUP)" || (echo 'Usage: make restore BACKUP=backups/file.dump' && exit 1)
	$(COMPOSE) run --rm backup python -m app.backup.cli restore "/backups/$$(basename "$(BACKUP)")"

run-all: app-up

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
