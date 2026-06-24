.PHONY: help install dev test test-all test-unit test-integration test-coverage lint format clean run

# Default target
help:
	@echo "🚀 Majiscope Backend - Common Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make install        - Install dependencies"
	@echo "  make install-dev    - Install dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Run development server with auto-reload"
	@echo "  make run            - Run production server"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run code linter (flake8)"
	@echo "  make format         - Format code (black)"
	@echo "  make clean          - Clean up generated files"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make db-seed        - Seed database with test data"
	@echo ""

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 isort

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/test_integration.py -v

test-coverage:
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report generated in htmlcov/index.html"

lint:
	flake8 app tests --max-line-length=120 --exclude=__pycache__

format:
	black app tests --line-length=120
	isort app tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

migrate:
	alembic upgrade head

db-seed:
	python -m app.prisma.seed
