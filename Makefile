.DEFAULT_GOAL := help
SHELL := /bin/bash

COMPOSE ?= docker compose
PYTHON ?= uv run python
PYTEST ?= uv run pytest

.PHONY: help install up down restart logs ps migrate migrate-create seed test test-unit test-integration test-adversarial test-load lint format type-check check clean smoke

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## install deps into local .venv (Python 3.12)
	uv sync --all-groups

up: ## start full stack (postgres, redis, qdrant, observability, all services)
	$(COMPOSE) up -d
	@echo "Stack up. Run 'make migrate' then 'make smoke' to verify."

down: ## stop and remove containers (keeps volumes)
	$(COMPOSE) down

destroy: ## stop containers AND remove volumes (destroys data)
	$(COMPOSE) down -v

restart: down up

logs: ## tail logs from all services
	$(COMPOSE) logs -f

ps: ## show running services
	$(COMPOSE) ps

migrate: ## apply database migrations
	uv run alembic upgrade head

migrate-create: ## create a new migration (make migrate-create name=add_foo)
	uv run alembic revision --autogenerate -m "$(name)"

seed: ## seed dev data
	$(PYTHON) scripts/seed.py

test: ## run all tests
	$(PYTEST)

test-unit:
	$(PYTEST) -m unit

test-integration:
	$(PYTEST) -m integration

test-adversarial:
	$(PYTEST) -m adversarial

lint: ## ruff lint
	uv run ruff check .

format: ## ruff format
	uv run ruff format .

type-check: ## mypy
	uv run mypy .

check: lint type-check test ## all quality gates

smoke: ## boot every service in-process and exercise the meta endpoints
	$(PYTEST) -m smoke -v --no-cov

test-load: ## run load tests (requires stack)
	$(PYTEST) -m load -v --no-cov

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

web-dev: ## run dashboard web in dev mode (port 3000)
	cd dashboard/web && npm run dev

web-build: ## build dashboard web for production
	cd dashboard/web && npm run build

web-test: ## run dashboard web vitest suite
	cd dashboard/web && npm run test

web-lint: ## typecheck + lint dashboard web
	cd dashboard/web && npm run typecheck && npm run lint
