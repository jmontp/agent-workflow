# Diagram Validation Tools

This directory contains tools for validating and maintaining consistency of Mermaid diagrams in the documentation.

## Mermaid Diagram Validator

The `diagram_validator.py` script provides comprehensive validation for Mermaid diagrams including:

### Features

- **Syntax Validation**: Checks for common Mermaid syntax errors
- **Theme Consistency**: Ensures all diagrams use the dark theme
- **State Machine Validation**: Validates state diagrams against known state machine states
- **Auto-Fix Capability**: Automatically fixes common issues where possible
- **Multiple Output Formats**: Human-readable reports or JSON for CI integration

### Usage

#### Basic Validation
```bash
# Validate all diagrams in docs_src/
python3 tools/validation/diagram_validator.py

# Verbose output
python3 tools/validation/diagram_validator.py --verbose

# Custom documentation path
python3 tools/validation/diagram_validator.py --docs-path custom_docs/
```

#### Auto-Fix Common Issues
```bash
# Fix issues automatically (missing themes, incorrect themes)
python3 tools/validation/diagram_validator.py --fix --verbose
```

#### CI/CD Integration
```bash
# JSON output for programmatic processing
python3 tools/validation/diagram_validator.py --json

# Exit with error code if issues found (useful for CI)
python3 tools/validation/diagram_validator.py --exit-code
```

### Validation Rules

#### Theme Consistency
- All diagrams must include: `%%{init: {'theme': 'dark'}}%%`
- Enforces consistent dark theme across all documentation

#### Syntax Validation
- Checks for unmatched brackets and parentheses
- Validates diagram type declarations
- Identifies common syntax patterns

#### State Machine Validation
- Validates state names against known states:
  - `IDLE`, `BACKLOG_READY`, `SPRINT_PLANNED`, `SPRINT_ACTIVE`
  - `SPRINT_PAUSED`, `SPRINT_REVIEW`, `BLOCKED`
- Checks command references in transitions
- Identifies primary workflow diagrams vs TDD sub-diagrams

#### Content Validation
- Flags unknown states that may indicate inconsistencies
- Suggests corrections for unrecognized commands
- Identifies missing critical states in primary workflows

### Example Output

```
# Mermaid Diagram Validation Report

**Summary:** 0 errors, 15 warnings, 3 info

## ⚠️ Warnings (Should Fix)

**state-machine.md:48** - No theme configuration found
  💡 *Suggestion: Add: %%{init: {'theme': 'dark'}}%%*

**overview.md:25** - Unknown states found: CUSTOM_STATE
  💡 *Suggestion: Valid states: BACKLOG_READY, BLOCKED, IDLE, ...*

## ℹ️ Information (Optional)

**workflow.md:102** - Command '/custom_command' not in recognized command list
  💡 *Suggestion: Valid commands: /epic, /approve, /sprint start, ...*
```

### Integration with Development Workflow

#### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python3 tools/validation/diagram_validator.py --exit-code
if [ $? -ne 0 ]; then
    echo "Mermaid diagram validation failed. Run with --fix to auto-fix common issues."
    exit 1
fi
```

#### Makefile Integration
```makefile
validate-diagrams:
	python3 tools/validation/diagram_validator.py --verbose

fix-diagrams:
	python3 tools/validation/diagram_validator.py --fix --verbose

docs-check: validate-diagrams
	@echo "Documentation validation complete"
```

#### CI/CD Pipeline
```yaml
- name: Validate Mermaid Diagrams
  run: python3 tools/validation/diagram_validator.py --json --exit-code
```

### Validation Categories

#### Errors (Must Fix)
- Syntax errors that break diagram rendering
- Unmatched brackets/parentheses
- Incorrect theme configurations

#### Warnings (Should Fix)
- Missing theme configurations
- Unknown states in state diagrams
- Missing diagram type declarations

#### Info (Optional)
- Unrecognized commands in transitions
- Missing optional states in primary workflows
- Style suggestions and improvements

### Extending the Validator

To add new validation rules:

1. Add new methods to `MermaidDiagramValidator` class
2. Call from `_validate_diagram_block()` method
3. Use `_add_issue()` to report problems
4. Add auto-fix logic to `_fix_file_issues()` if applicable

### Known Limitations

- Regex-based validation (not full Mermaid parser)
- Cannot validate complex diagram semantics
- Auto-fix limited to simple text replacements
- Does not validate diagram rendering output

This tool helps maintain visual consistency and prevents state machine diagram inconsistencies that could confuse users or lead to documentation drift.