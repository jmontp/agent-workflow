# Documentation Tools

This directory contains tools for maintaining and monitoring documentation health.

## Tools Overview

### 📋 health_check.py
Comprehensive documentation health monitoring system that provides:

- **Navigation Coverage**: Identifies files missing from navigation
- **Content Quality**: Detects empty files, stub content, and incomplete markers
- **Link Validation**: Checks for broken internal links and missing images
- **Consistency Analysis**: Identifies naming conventions and formatting issues
- **Actionable Recommendations**: Prioritized suggestions for improvement

**Usage:**
```bash
# Quick console summary
python tools/documentation/health_check.py --quick

# Full check with link validation
python tools/documentation/health_check.py

# Generate HTML report
python tools/documentation/health_check.py --format html --output health_report.html

# Generate JSON report for automation
python tools/documentation/health_check.py --format json --output health_report.json
```

**Output Formats:**
- **Console**: Developer-friendly summary with immediate actions
- **JSON**: Machine-readable format for CI/CD integration
- **HTML**: Visual report with progress bars and detailed analysis

### 🔧 ci_health_check.py
Lightweight CI/CD-focused health check designed for automated workflows:

- **Fast execution**: Skips expensive operations for quick feedback
- **Exit codes**: Proper exit codes for build pipeline integration
- **Configurable thresholds**: Fail on high-severity or medium-severity issues
- **Quiet mode**: Minimal output for automated environments

**Usage:**
```bash
# Basic CI check (fails on high-severity issues)
python tools/documentation/ci_health_check.py

# Strict mode (fails on medium-severity issues too)
python tools/documentation/ci_health_check.py --fail-on-medium

# Report-only mode (never fails, useful for reporting)
python tools/documentation/ci_health_check.py --report-only --output report.json

# Quiet mode for automation
python tools/documentation/ci_health_check.py --quiet
```

**Exit Codes:**
- `0`: No critical issues found
- `1`: High-severity issues found (or medium-severity with `--fail-on-medium`)
- `2`: Build-breaking issues found (configuration/structure problems)

### 🔧 generate_api_docs.py
Automated API documentation generator that extracts information from source code.

**Usage:**
```bash
# Generate markdown API docs
python tools/documentation/generate_api_docs.py --format markdown

# Generate OpenAPI specification
python tools/documentation/generate_api_docs.py --format openapi

# Include private methods and attributes
python tools/documentation/generate_api_docs.py --include-private
```

## Health Check Features

### 📊 Coverage Analysis
- **Navigation Coverage**: Percentage of files included in MkDocs navigation
- **Content Coverage**: Percentage of files with substantial content
- **Quality Score**: Overall documentation health score (0-100)
- **Health Grade**: Letter grade (A-F) based on overall quality

### 🔍 Issue Detection
The health check identifies several types of issues:

**High Severity (Build-breaking):**
- Missing or corrupted configuration files
- Empty documentation files
- Broken internal links to critical pages

**Medium Severity (User-impacting):**
- Files missing from navigation
- Broken internal links
- Missing images
- Very short content files

**Low Severity (Quality improvements):**
- Inconsistent naming conventions
- Missing alt text for images
- Incomplete content markers (TODO, FIXME)
- Poor heading structure

### 💡 Recommendations
The system provides actionable recommendations prioritized by impact:

1. **Fix Critical Issues**: Address build-breaking problems first
2. **Improve Navigation Coverage**: Add important files to navigation
3. **Enhance Content Quality**: Expand stub files and add examples
4. **Maintain Consistency**: Standardize naming and formatting

## Integration Examples

### GitHub Actions
```yaml
- name: Check Documentation Health
  run: |
    python tools/documentation/ci_health_check.py --fail-on-medium
    python tools/documentation/health_check.py --format json --output health-report.json
    
- name: Upload Health Report
  uses: actions/upload-artifact@v3
  with:
    name: documentation-health-report
    path: health-report.json
```

### Make Target
```makefile
docs-health:
	python tools/documentation/health_check.py --format html --output docs/health-report.html

docs-health-ci:
	python tools/documentation/ci_health_check.py --fail-on-medium

.PHONY: docs-health docs-health-ci
```

### Pre-commit Hook
```yaml
- repo: local
  hooks:
    - id: docs-health-check
      name: Documentation Health Check
      entry: python tools/documentation/ci_health_check.py
      language: system
      files: ^docs_src/.*\.md$
```

## Configuration

The health check automatically detects:
- **Documentation root**: `docs_src/` directory
- **MkDocs config**: `mkdocs.yml` file
- **Special files**: Files that don't need navigation (README.md, CLAUDE.md, etc.)
- **Archive files**: Files in archive/ or compliance/ directories

## Best Practices

1. **Regular monitoring**: Run health checks regularly to catch issues early
2. **CI/CD integration**: Use the CI version in your build pipeline
3. **Fix high-severity issues first**: Address build-breaking problems immediately
4. **Monitor trends**: Track health scores over time to measure improvement
5. **Use HTML reports**: Generate visual reports for stakeholder communication

## Performance

- **Quick mode**: ~2-3 seconds for 100+ files (skips link validation)
- **Full mode**: ~10-15 seconds for 100+ files (includes link validation)
- **CI mode**: ~1-2 seconds (optimized for automation)

## Dependencies

- Python 3.8+
- PyYAML (for MkDocs configuration parsing)
- No external dependencies for basic functionality