# Dependency System Integration Guide for Claude

## Overview

The dependency tracking system automatically identifies relationships between files and suggests updates when changes occur. This guide helps Claude understand how to work with the system.

## When Making Changes

### 1. Code Changes
When modifying code files in `lib/` or `agent_workflow/`:
- The system will identify affected test files
- Claude should update tests to maintain coverage
- Use existing test patterns and conventions

### 2. Test Changes
When modifying test files:
- Ensure tests still accurately test the implementation
- Update test documentation if behavior changes
- Maintain coverage levels (95%+ for critical modules)

### 3. Documentation Changes
When updating documentation:
- Verify all code references are accurate
- Update examples to match current implementation
- Check that file paths are correct after reorganization

## Update Patterns

### Automatic Detection
The system detects these relationships:
- `lib/module.py` → `tests/unit/test_module.py`
- `lib/agents/agent.py` → `tests/unit/test_agents_agent.py`
- `lib/module.py` → `docs_src/api/module.md`
- CLAUDE.md files → all files in the same directory

### Manual Mappings
Some relationships require manual configuration in `dependencies.yaml`:
- Cross-module dependencies
- Integration test relationships
- Documentation to multiple modules

## Best Practices

1. **Incremental Updates**: Update files incrementally rather than wholesale rewrites
2. **Test-First**: Update tests before implementation when possible
3. **Coverage Maintenance**: Ensure updates don't reduce test coverage
4. **Documentation Sync**: Keep docs synchronized with code changes

## Common Scenarios

### New Feature Implementation
1. Create/update design docs
2. Write failing tests (TDD approach)
3. Implement feature
4. Update documentation
5. System tracks all relationships

### Bug Fixes
1. Write test that reproduces bug
2. Fix implementation
3. Update any affected documentation
4. System ensures consistency

### Refactoring
1. Ensure tests pass before refactoring
2. Make incremental changes
3. Run tests after each change
4. Update documentation if interfaces change

## Integration with TDD Workflow

The dependency system integrates with the TDD state machine:
- DESIGN phase: Documentation relationships
- TEST_RED phase: Test file creation/updates
- CODE_GREEN phase: Implementation updates
- REFACTOR phase: Maintain all relationships
- COMMIT phase: Validate all dependencies

## Validation

Before committing, the system validates:
- All dependencies are satisfied
- No orphaned test files
- Documentation references are valid
- Coverage thresholds are met

Use `python tools/dependencies/tracker.py --validate` to check manually.
