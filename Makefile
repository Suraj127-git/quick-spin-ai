.PHONY: help install dev test lint format run docker-build docker-up docker-down clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies with uv
	uv sync --all-extras

dev: ## Install development dependencies
	uv sync --all-extras --dev

test: ## Run tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term

lint: ## Run linters
	uv run ruff check app/ tests/
	uv run mypy app/

format: ## Format code
	uv run black app/ tests/
	uv run ruff check --fix app/ tests/

run: ## Run development server
	uv run python -m app.main

run-cli: ## Run CLI (interactive chat)
	uv run python -m app.cli chat --token $(TOKEN)

docker-build: ## Build Docker image
	docker build -t quickspin-ai:latest .

docker-up: ## Start Docker Compose services
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f quickspin-ai

clean: ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -f .coverage
