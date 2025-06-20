# Makefile for TDD Agent Workflow System
# Provides automation for testing, development, and deployment tasks

.PHONY: help install test test-unit test-integration test-performance test-security test-acceptance test-regression test-edge-cases test-e2e test-all test-quick test-ci clean lint format docs serve-docs build-docs validate check setup dev-setup run orchestrator

# Default target
help:
	@echo "Available targets:"
	@echo "  help               Show this help message"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  install            Install project dependencies"
	@echo "  setup              Complete project setup"
	@echo "  dev-setup          Setup development environment"
	@echo ""
	@echo "Testing:"
	@echo "  test               Run all tests"
	@echo "  test-unit          Run unit tests only"
	@echo "  test-integration   Run integration tests only"
	@echo "  test-performance   Run performance tests only"
	@echo "  test-security      Run security tests only"
	@echo "  test-acceptance    Run user acceptance tests only"
	@echo "  test-regression    Run regression tests only"
	@echo "  test-edge-cases    Run edge case tests only"
	@echo "  test-e2e           Run end-to-end tests only"
	@echo "  test-docs          Run documentation example validation tests"
	@echo "  test-all           Run comprehensive test suite"
	@echo "  test-quick         Run quick test suite (unit + integration)"
	@echo "  test-ci            Run CI/CD optimized test suite"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint               Run linting checks"
	@echo "  format             Format code with black and isort"
	@echo "  validate           Run comprehensive validation"
	@echo "  check              Quick code quality check"
	@echo ""
	@echo "Documentation:"
	@echo "  docs               Build documentation"
	@echo "  serve-docs         Serve documentation locally"
	@echo "  build-docs         Build static documentation"
	@echo "  docs-check         Run documentation quality checks"
	@echo "  docs-check-ci      Run CI-style documentation checks"
	@echo "  docs-fix           Auto-fix minor documentation issues"
	@echo "  docs-links         Check documentation links"
	@echo "  docs-install-hook  Install pre-commit hook for docs"
	@echo "  docs-health        Quick documentation health check"
	@echo "  docs-health-full   Full documentation health check"
	@echo "  docs-health-html   Generate HTML health report"
	@echo "  docs-health-ci     CI documentation health check"
	@echo ""
	@echo "Application:"
	@echo "  run                Run Discord bot with orchestrator"
	@echo "  orchestrator       Run orchestrator only"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean              Clean up temporary files and caches"

# Installation and Setup
install:
	@echo "Installing project dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-mock
	pip install black isort flake8 mypy
	pip install psutil GitPython

setup: install
	@echo "Setting up project..."
	python -c "import lib.project_storage; print('Project storage module verified')"
	python -c "import scripts.orchestrator; print('Orchestrator module verified')"
	@echo "Project setup complete!"

dev-setup: setup
	@echo "Setting up development environment..."
	pip install pre-commit
	mkdir -p tests/reports
	mkdir -p tests/htmlcov
	@echo "Development environment ready!"

# Testing Targets

# Unit Tests
test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/unit/ -v --tb=short -m "not slow"

# Integration Tests  
test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v --tb=short

# Performance Tests
test-performance:
	@echo "Running performance tests..."
	python tests/performance/test_tdd_performance.py

# Security Tests
test-security:
	@echo "Running security tests..."
	python tests/security/test_tdd_security.py

# User Acceptance Tests
test-acceptance:
	@echo "Running user acceptance tests..."
	python tests/acceptance/test_tdd_user_acceptance.py

# Regression Tests
test-regression:
	@echo "Running regression tests..."
	python tests/regression/test_tdd_regression.py

# Edge Case Tests
test-edge-cases:
	@echo "Running edge case tests..."
	python tests/edge_cases/test_tdd_edge_cases.py

# End-to-End Tests
test-e2e:
	@echo "Running end-to-end tests..."
	python test_tdd_e2e.py

# Documentation Tests
test-docs:
	@echo "Running documentation example validation tests..."
	python3 -m pytest tests/documentation/ -v --tb=short

# Comprehensive Test Suite
test-all:
	@echo "Running comprehensive test suite..."
	python tests/run_comprehensive_tests.py --save-report

# Quick Test Suite (for development)
test-quick:
	@echo "Running quick test suite..."
	python3 -m pytest tests/unit/ tests/documentation/ -v --tb=short
	python tests/run_comprehensive_tests.py --categories e2e regression

# CI/CD Optimized Test Suite
test-ci:
	@echo "Running CI/CD test suite..."
	python3 -m pytest tests/unit/ tests/integration/ tests/documentation/ -v --tb=short --durations=10
	python tests/run_comprehensive_tests.py --categories e2e security regression --save-report

# Standard test target (runs comprehensive suite)
test: test-all

# Code Quality Targets

# Linting
lint:
	@echo "Running linting checks..."
	flake8 lib/ scripts/ tests/ --max-line-length=120 --ignore=E203,W503
	mypy lib/ scripts/ --ignore-missing-imports --no-strict-optional

# Code Formatting
format:
	@echo "Formatting code..."
	black lib/ scripts/ tests/ --line-length=120
	isort lib/ scripts/ tests/ --profile=black

# Comprehensive Validation
validate: lint test-unit test-integration
	@echo "Running comprehensive validation..."
	python -c "import sys; sys.path.insert(0, 'lib'); import tdd_models, tdd_state_machine; print('TDD modules validated')"
	python validate_tdd.py
	@echo "Validation complete!"

# Quick Code Quality Check
check:
	@echo "Running quick code quality check..."
	python -m pytest tests/unit/ -x --tb=short
	flake8 lib/ scripts/ --max-line-length=120 --ignore=E203,W503 --select=E9,F63,F7,F82

# Documentation Targets

# Build and serve documentation
docs: serve-docs

serve-docs:
	@echo "Serving documentation locally..."
	mkdocs serve

build-docs:
	@echo "Building static documentation..."
	mkdocs build

# Documentation health checks
docs-health:
	@echo "Running documentation health check..."
	python3 tools/documentation/health_check.py --quick

docs-health-full:
	@echo "Running full documentation health check..."
	python3 tools/documentation/health_check.py

docs-health-html:
	@echo "Generating HTML documentation health report..."
	python3 tools/documentation/health_check.py --format html --output docs_health_report.html
	@echo "✅ HTML report generated: docs_health_report.html"

docs-health-ci:
	@echo "Running CI documentation health check..."
	python3 tools/documentation/ci_health_check.py

# Documentation Quality & CI Targets

docs-check:
	@echo "Running documentation quality checks..."
	python3 tools/check_docs_quality.py --verbose

docs-check-ci:
	@echo "Running CI-style documentation checks..."
	python3 tools/test_docs_ci.py

docs-fix:
	@echo "Auto-fixing minor documentation issues..."
	python3 tools/check_docs_quality.py --fix-minor --verbose

docs-links:
	@echo "Checking documentation links..."
	python3 tools/audit_links.py

docs-install-hook:
	@echo "Installing pre-commit hook for documentation..."
	python3 tools/setup_pre_commit_hook.py --install

# Application Targets

# Run Discord bot
run:
	@echo "Make sure to set DISCORD_BOT_TOKEN environment variable"
	@echo "Claude Code integration available for enhanced AI capabilities"
	python lib/discord_bot.py

# Run orchestrator only
orchestrator:
	python scripts/orchestrator.py

# Maintenance Targets

clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf tests/htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf site/
	rm -rf build/
	rm -rf dist/
	@echo "Cleanup complete!"

# TDD Workflow Validation
validate-tdd:
	@echo "Validating TDD implementation..."
	python validate_tdd.py
	python validate_enhanced_tdd.py

# Enhanced TDD Validation
validate-enhanced-tdd:
	@echo "Validating enhanced TDD features..."
	python validate_enhanced_tdd.py

# Complete System Validation
validate-system: validate validate-tdd validate-enhanced-tdd
	@echo "Complete system validation passed!"

# Development Workflow Shortcuts

# Pre-commit hook simulation
pre-commit: format lint test-unit
	@echo "Pre-commit checks passed!"

# Full development validation
dev-validate: clean format lint test-quick
	@echo "Development validation complete!"

# Release preparation
prepare-release: clean format lint validate-system test-all build-docs
	@echo "Release preparation complete!"

# Performance benchmarking
benchmark:
	@echo "Running performance benchmarks..."
	python tests/performance/test_tdd_performance.py

# Security audit
security-audit:
	@echo "Running security audit..."
	python tests/security/test_tdd_security.py

# Continuous Integration Simulation
ci-simulation: clean install test-ci
	@echo "CI simulation complete!"

# Production Readiness Check
production-check: validate-system test-all security-audit benchmark
	@echo "Production readiness check complete!"
	@echo "Review test reports before deployment!"

# Emergency Quick Check (minimal validation)
quick-check:
	@echo "Running emergency quick check..."
	python -c "import lib.orchestrator; print('Orchestrator imports OK')"
	python -c "import lib.tdd_state_machine; print('TDD state machine imports OK')"
	python -m pytest tests/unit/test_tdd_models.py -v
	@echo "Quick check passed!"

# Help for development workflow
dev-help:
	@echo "Development Workflow:"
	@echo "1. make dev-setup     # One-time setup"
	@echo "2. make check         # Quick validation during development"
	@echo "3. make test-quick    # Test your changes"
	@echo "4. make pre-commit    # Before committing"
	@echo "5. make test-all      # Before pushing"
	@echo ""
	@echo "Release Workflow:"
	@echo "1. make prepare-release"
	@echo "2. Review all test reports"
	@echo "3. Deploy if all checks pass"