#!/bin/bash

echo "========================================="
echo "FlexRadio 6400 Control - Test Suite"
echo "========================================="
echo ""

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing test dependencies..."
pip install -r requirements-test.txt

echo ""
echo "========================================="
echo "Running all tests..."
echo "========================================="
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

echo ""
echo "========================================="
echo "Running unit tests..."
echo "========================================="
pytest tests/unit/ -v

echo ""
echo "========================================="
echo "Running integration tests..."
echo "========================================="
pytest tests/integration/ -v -m integration

echo ""
echo "========================================="
echo "Running fast tests (excluding slow tests)..."
echo "========================================="
pytest tests/ -v -m "not slow"

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Test coverage report generated: htmlcov/index.html"
echo "Open in browser: open htmlcov/index.html"
echo ""

deactivate