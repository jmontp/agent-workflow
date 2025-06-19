# Dependency Tracking System

An intelligent file dependency tracking and update system for maintaining consistency across code, tests, and documentation in the AI Agent TDD-Scrum workflow system.

## Overview

The dependency tracking system automatically:
- Maps relationships between code, tests, and documentation
- Monitors file changes in real-time
- Suggests or applies updates to dependent files
- Integrates with Claude Code for intelligent updates
- Validates dependencies before commits

## Components

### 1. **Dependency Tracker** (`tracker.py`)
Scans the codebase to build a comprehensive dependency map.

**Features:**
- AST-based Python import analysis
- Convention-based test/doc mapping
- Markdown reference extraction
- Bidirectional dependency graphs
- YAML export/import

**Usage:**
```bash
# Scan and export dependencies
python tracker.py

# Check dependencies for a specific file
python tracker.py --file lib/agents/code_agent.py --related

# Export dependency graph
python tracker.py --export-graph
```

### 2. **File Watcher** (`watcher.py`)
Monitors file changes and triggers dependency updates.

**Features:**
- Real-time file monitoring with watchdog
- Debounced update processing
- Concurrent update execution
- Integration with update handlers

**Usage:**
```bash
# Start watching (runs continuously)
python watcher.py

# Watch with custom config
python watcher.py --config .dependency-config.yaml
```

### 3. **Automatic Updater** (`updater.py`)
Handles intelligent updates of dependent files.

**Features:**
- Strategy-based update logic
- Claude Code integration
- Test/doc generation
- Validation and linting
- Dry-run mode

**Usage:**
```bash
# Check what would be updated
python updater.py lib/some_module.py --dry-run

# Auto-execute updates
python updater.py lib/some_module.py --auto

# Specify change type
python updater.py lib/new_module.py --change-type created
```

### 4. **Setup Script** (`setup.py`)
Initialize the dependency tracking system.

**Features:**
- Generate initial dependencies.yaml
- Install pre-commit hooks
- Create GitHub Actions workflow
- Configure VS Code integration

**Usage:**
```bash
# Run initial setup
python setup.py
```

## Dependency Mapping

### Automatic Conventions

The system automatically detects these patterns:

1. **Test Files:**
   - `lib/module.py` → `tests/unit/test_module.py`
   - `lib/agents/agent.py` → `tests/unit/test_agents_agent.py`
   - `lib/module.py` → `tests/integration/test_module.py`

2. **Documentation:**
   - `lib/module.py` → `docs_src/api/module.md`
   - `*/CLAUDE.md` → All files in the same directory

3. **Import Dependencies:**
   - Python imports create explicit dependencies
   - Relative imports are resolved to absolute paths

### Manual Configuration

Additional mappings can be defined in `dependencies.yaml`:

```yaml
version: '1.0'
generated: tracker.py
mappings:
  lib/orchestrator.py:
    type: code
    dependencies:
      - lib/state_machine.py
      - lib/agents/base_agent.py
    dependents:
      - tests/unit/test_orchestrator.py
    related:
      tests:
        - tests/unit/test_orchestrator.py
        - tests/integration/test_orchestrator_workflow.py
      docs:
        - docs_src/api/orchestrator.md
        - docs_src/architecture/orchestration.md
```

## Configuration

### Watcher Configuration (`.dependency-config.yaml`)

```yaml
watcher:
  watch_patterns: ['**/*.py', '**/*.md', '**/*.yaml']
  ignore_patterns: ['__pycache__', '.git', 'venv']
  debounce_seconds: 2.0
  max_concurrent_updates: 3

updater:
  auto_update:
    tests: false      # Start with manual mode
    docs: false
    dependent_code: false
  update_modes:
    tests: suggest    # 'auto', 'suggest', 'manual'
    docs: suggest
    code: manual
  validation:
    run_tests: true
    check_coverage: true
    lint_code: true

claude_integration:
  enabled: true
  model: claude-3-opus-20240229
  instructions:
    test_creation: Create comprehensive unit tests
    test_update: Update tests to cover changes
    doc_update: Update documentation and examples
```

## Integration

### Pre-commit Hook

Automatically validates dependencies before commits:

```bash
#!/bin/bash
# .git/hooks/pre-commit
python tools/dependencies/tracker.py --validate
```

### GitHub Actions

Validates dependencies in CI/CD:

```yaml
# .github/workflows/dependency-check.yml
- name: Validate dependencies
  run: python tools/dependencies/tracker.py --validate
```

### VS Code Tasks

Quick access to dependency tools:
- **Check Dependencies**: Analyze current file
- **Update Dependencies**: Preview updates
- **Watch Dependencies**: Start monitoring

### Claude Code Integration

When Claude makes changes:
1. System detects modified files
2. Identifies affected tests/docs
3. Claude receives update instructions
4. Updates maintain consistency

## Workflows

### 1. Adding New Code

```bash
# 1. Create new module
echo "# New module" > lib/new_feature.py

# 2. System detects creation
python updater.py lib/new_feature.py --change-type created

# 3. Creates test template
# → tests/unit/test_new_feature.py (generated)

# 4. Update documentation
# → Suggests creating docs_src/api/new_feature.md
```

### 2. Modifying Existing Code

```bash
# 1. Edit existing module
vim lib/agents/code_agent.py

# 2. Check affected files
python tracker.py --file lib/agents/code_agent.py --related

# 3. Preview updates
python updater.py lib/agents/code_agent.py --dry-run

# 4. Apply updates
python updater.py lib/agents/code_agent.py --auto
```

### 3. Continuous Monitoring

```bash
# Start watcher in background
python watcher.py &

# Make changes - watcher detects and logs
# Updates are suggested/applied based on config
```

### 4. Validation Before Commit

```bash
# Manual validation
python tracker.py --validate

# Automatic via pre-commit hook
git commit -m "Update feature"
# → Hook runs validation
# → Commit blocked if issues found
```

## Best Practices

### 1. Incremental Updates
- Make small, focused changes
- Update dependencies after each change
- Maintain test coverage

### 2. Test-First Development
- Update/create tests before implementation
- Use dependency system to ensure test coverage
- Validate all tests pass

### 3. Documentation Sync
- Update docs when changing public APIs
- Keep examples current
- Verify all file references

### 4. Review Generated Content
- Always review auto-generated tests
- Customize templates as needed
- Maintain code quality standards

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install watchdog pyyaml
   ```

2. **Import Errors**
   ```bash
   # Run from project root
   cd /path/to/agent-workflow
   python tools/dependencies/tracker.py
   ```

3. **Permission Errors**
   ```bash
   # Make scripts executable
   chmod +x tools/dependencies/*.py
   ```

4. **Watcher Not Detecting Changes**
   - Check ignore patterns in config
   - Verify file extensions are watched
   - Check file system events are supported

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python watcher.py

# Verbose output
python tracker.py --verbose
```

## Performance Considerations

- Initial scan may take time for large projects
- Watcher uses minimal resources
- Updates are debounced to avoid thrashing
- Concurrent updates improve performance

## Future Enhancements

1. **Machine Learning Integration**
   - Learn update patterns from history
   - Predict required changes
   - Suggest refactoring opportunities

2. **Advanced Claude Integration**
   - Multi-file update orchestration
   - Context-aware update generation
   - Test quality validation

3. **IDE Plugins**
   - Real-time dependency visualization
   - Inline update suggestions
   - Refactoring support

4. **Metrics and Analytics**
   - Dependency complexity metrics
   - Update frequency analysis
   - Code health monitoring

## Contributing

To improve the dependency tracking system:

1. **Add New Patterns**: Update `naming_conventions` in tracker.py
2. **Create Strategies**: Implement new UpdateStrategy subclasses
3. **Enhance Detection**: Improve AST analysis or add new file types
4. **Integration**: Add support for new tools or IDEs

## License

Part of the AI Agent TDD-Scrum workflow system. See main project license.