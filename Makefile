# AI Agent TDD-Scrum Workflow Makefile

.PHONY: install test lint run clean help docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run test suite"
	@echo "  lint        - Run code linting"
	@echo "  run         - Run Discord bot with orchestrator"
	@echo "  orchestrator - Run orchestrator only"
	@echo "  docs        - Serve documentation locally"
	@echo "  docs-build  - Build documentation"
	@echo "  clean       - Clean up generated files"
	@echo "  help        - Show this help message"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-coverage:
	pytest tests/ -v --cov=lib --cov=scripts --cov-report=html

# Run only unit tests
test-unit:
	pytest tests/unit/ -v

# Run only integration tests
test-integration:
	pytest tests/integration/ -v

# Run linting
lint:
	python -m flake8 lib/ scripts/ --max-line-length=120 --ignore=E501,W503
	python -m black --check lib/ scripts/

# Format code
format:
	python -m black lib/ scripts/

# Run Discord bot
run:
	python lib/discord_bot.py

# Run orchestrator only
orchestrator:
	python scripts/orchestrator.py

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# Development setup
dev-setup: install
	pip install black flake8
	@echo "Development environment ready!"

# Documentation
docs:
	mkdocs serve

docs-build:
	mkdocs build

# Run with environment variables
run-dev:
	@echo "Make sure to set DISCORD_BOT_TOKEN environment variable"
	@echo "Claude Code integration available for enhanced AI capabilities"
	python lib/discord_bot.py