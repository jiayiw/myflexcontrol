.PHONY: format lint test clean help

help:
	@echo "Available commands:"
	@echo "  make format    - Format code with black and isort"
	@echo "  make lint      - Check code quality with flake8, pylint, and mypy"
	@echo "  make test      - Run tests with pytest"
	@echo "  make clean     - Remove cache and temporary files"

format:
	black .
	isort .

lint:
	flake8 .
	pylint *.py
	mypy .

test:
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	@echo "Cleanup complete"