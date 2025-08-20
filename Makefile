.PHONY: help install test lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies and set up development environment"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-integration-full - Run all integration tests including performance"
	@echo "  test-integration-performance - Run performance tests only"
	@echo "  test-integration-api - Run API integration tests only"
	@echo "  test-integration-pipeline - Run pipeline integration tests only"
	@echo "  test-coverage-integration - Run integration tests with coverage"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code with black"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  clean        - Clean up generated files"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start all services with Docker"
	@echo "  docker-down  - Stop all Docker services"
	@echo "  docker-db    - Start only database service"
	@echo "  docker-api   - Start API service"
	@echo "  docker-processor - Run data processor"
	@echo "  dev-api      - Start development API server"
	@echo "  demo-api     - Run API demo (requires API server running)"
	@echo "  demo-cli     - Run interactive CLI demo"
	@echo "  demo-cli-extract - Run CLI demo with number extraction"

# Development setup
install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pre-commit install

# Testing
test:
	pytest

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/

test-integration-full:
	python tests/integration/run_integration_tests.py --all

test-integration-performance:
	python tests/integration/run_integration_tests.py --performance

test-integration-api:
	python tests/integration/run_integration_tests.py --api

test-integration-pipeline:
	python tests/integration/run_integration_tests.py --pipeline

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term

test-coverage-integration:
	python tests/integration/run_integration_tests.py --coverage

# Code quality
lint:
	flake8 src/ tests/
	black --check src/ tests/

format:
	black src/ tests/

type-check:
	mypy src/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose --profile api --profile data-processing up -d

docker-down:
	docker-compose down -v

docker-db:
	docker-compose up database -d

docker-api:
	docker-compose --profile api up -d

docker-processor:
	docker-compose --profile data-processing up data-processor

# Development server
dev-api:
	python scripts/run_api.py

# API demos
demo-api:
	python scripts/demo_api.py

demo-cli:
	python scripts/cli_demo.py --interactive

demo-cli-extract:
	python scripts/cli_demo.py --extract 42

# Data processing
process-data:
	python -m src.data_processing.main

# Database management
init-db:
	python scripts/init_database.py

db-info:
	python -c "from src.database.manager import DatabaseManager; from src.database.connection import db_connection; dm = DatabaseManager(); info = dm.get_database_info(); print('Schemas:', info['schemas']); print('Tables:', sum(len(t) for t in info['tables'].values())); print('Views:', len(info['views'])); db_connection.close()"