# PlutosAI Development Makefile

.PHONY: help install dev-setup test lint type-check clean docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -e .

dev-setup: ## Install development dependencies
	pip install -e '.[dev]'

test: ## Run all tests
	pytest -v

test-unit: ## Run unit tests only
	pytest tests/ -k "not integration and not e2e" -v

test-integration: ## Run integration tests
	pytest tests/integration/ -v

lint: ## Run linter
	ruff check .

lint-fix: ## Run linter and auto-fix issues
	ruff check --fix .

type-check: ## Run type checker
	mypy shared/

format: ## Format code
	ruff format .

security-scan: ## Run security scanning
	bandit -r shared/ services/

test-all: lint type-check test ## Run all quality checks

clean: ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

docker-up: ## Start all services with Docker Compose
	cd infrastructure/docker && docker-compose up -d

docker-down: ## Stop all services
	cd infrastructure/docker && docker-compose down

docker-logs: ## Show logs from all services
	cd infrastructure/docker && docker-compose logs -f

run-client: ## Run client service locally
	cd services/client-service && uvicorn src.api:app --reload --host 0.0.0.0 --port 8001

run-gateway: ## Run gateway service locally
	cd services/gateway-service && uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

setup: ## Complete development setup
	@echo "Setting up PlutosAI development environment..."
	python3.11 -m venv .venv
	@echo "Created virtual environment. Run 'source .venv/bin/activate' to activate."
	@echo "Then run 'make dev-setup' to install dependencies."

migrate-db: ## Run database migrations
	@echo "Database migrations would be run here"
	# alembic upgrade head

create-migration: ## Create new database migration
	@echo "Create new migration here"
	# alembic revision --autogenerate -m "migration message"

seed-db: ## Seed database with test data
	@echo "Seeding database with test data..."
	# python scripts/seed_database.py

docs: ## Generate API documentation
	@echo "Generating API documentation..."
	# pdoc --html --output-dir docs/api shared/

coverage: ## Generate test coverage report
	pytest --cov=shared --cov=services --cov-report=html --cov-report=term-missing

security-audit: ## Run security audit on dependencies
	pip-audit
