#!/bin/bash
# Test Runner Script

set -e

echo "🧪 Majiscope Backend Test Runner"
echo "================================"

# Load environment
if [ -f .env.test ]; then
    export $(cat .env.test | grep -v '#' | xargs)
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run different test suites
case "${1:-all}" in
    "all")
        echo "Running all tests..."
        pytest tests/ -v --cov=app --cov-report=html
        ;;
    "unit")
        echo "Running unit tests..."
        pytest tests/ -v -m "unit" --cov=app
        ;;
    "integration")
        echo "Running integration tests..."
        pytest tests/test_integration.py -v
        ;;
    "auth")
        echo "Running authentication tests..."
        pytest tests/test_auth.py -v
        ;;
    "users")
        echo "Running user tests..."
        pytest tests/test_users.py -v
        ;;
    "health")
        echo "Running health check tests..."
        pytest tests/test_health.py -v
        ;;
    "coverage")
        echo "Running tests with coverage report..."
        pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
        echo "✅ Coverage report generated in htmlcov/index.html"
        ;;
    "watch")
        echo "Running tests in watch mode..."
        pytest-watch tests/ -- -v
        ;;
    *)
        echo "Usage: ./run_tests.sh [all|unit|integration|auth|users|health|coverage|watch]"
        exit 1
        ;;
esac

echo "✅ Tests completed!"
