# Documentation Tests

This directory contains tests that validate documentation examples to prevent user-breaking issues.

## Purpose

These tests ensure that:
- Python code examples in documentation are syntactically valid
- Configuration YAML files have correct syntax
- CLI command examples are properly formatted
- Critical internal links work correctly
- User copy-paste examples function properly

## Test Categories

### Python Code Examples (`TestPythonCodeExamples`)
- Validates Python code blocks from documentation can be parsed
- Tests error handling patterns and API examples
- Ensures configuration validation scripts are correct

### YAML Configuration (`TestYAMLConfigurationExamples`)
- Tests `config.example.yml` syntax
- Validates configuration examples from documentation
- Ensures TDD configuration examples are correct
- Checks `mkdocs.yml` configuration integrity

### CLI Commands (`TestCLICommandExamples`)
- Validates CLI command syntax from quick-start guide
- Tests bash command examples for shell compatibility
- Ensures Python command examples are properly formatted

### Environment Variables (`TestEnvironmentVariableExamples`)
- Validates `.env` file format examples
- Tests environment variable syntax

### Documentation Integrity (`TestConfigurationTemplateIntegrity`, `TestDocumentationLinkIntegrity`)
- Ensures config templates match documented examples
- Validates critical internal documentation links
- Tests that documented commands follow proper naming conventions

## Running Tests

```bash
# Run all documentation tests
pytest tests/documentation/ -v

# Run specific test class
pytest tests/documentation/test_documentation_examples.py::TestPythonCodeExamples -v

# Run with coverage
pytest tests/documentation/ --cov=docs_src -v
```

## Design Principles

1. **Fast and Lightweight**: Tests focus on syntax validation, not execution
2. **User-Focused**: Tests target examples users actually copy-paste
3. **Critical Path Coverage**: Prioritizes getting-started and configuration examples
4. **No External Dependencies**: Tests don't require real API keys or external services

## Adding New Tests

When adding new documentation examples:
1. Add syntax validation tests for any code blocks
2. Test YAML configuration examples
3. Validate CLI commands are properly formatted
4. Check internal links for new documentation files

## Common Issues Caught

- Typos in CLI command flags
- Invalid YAML indentation in config examples
- Broken internal documentation links
- Python syntax errors in copy-paste examples
- Missing quotes in bash commands
- Invalid environment variable formats