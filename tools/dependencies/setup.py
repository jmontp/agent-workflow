#!/usr/bin/env python3
"""
Dependency System Setup - Initialize dependency tracking

Sets up the dependency tracking system including:
- Initial dependency scan and mapping
- Pre-commit hook installation
- GitHub Actions workflow setup
- Configuration file generation
"""

import os
import sys
import subprocess
from pathlib import Path
import yaml
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.dependencies.tracker import DependencyTracker


def create_dependencies_yaml(project_root: Path) -> None:
    """Generate initial dependencies.yaml file"""
    print("Scanning project for dependencies...")
    
    tracker = DependencyTracker(project_root)
    tracker.scan_project()
    
    # Export dependencies
    output_path = project_root / 'dependencies.yaml'
    tracker.export_dependencies(output_path)
    
    print(f"✓ Created {output_path}")
    print(f"  - Found {len(tracker.file_nodes)} files")
    print(f"  - Mapped {len(tracker.dependencies)} dependencies")


def create_pre_commit_hook(project_root: Path) -> None:
    """Create pre-commit hook for dependency validation"""
    hooks_dir = project_root / '.git' / 'hooks'
    if not hooks_dir.exists():
        print("⚠ .git/hooks directory not found. Skipping pre-commit hook.")
        return
    
    hook_path = hooks_dir / 'pre-commit'
    
    hook_content = '''#!/bin/bash
# Pre-commit hook for dependency validation

echo "Validating dependencies..."

# Check if dependency tracking is available
if [ -f "tools/dependencies/tracker.py" ]; then
    # Run dependency validation
    python3 tools/dependencies/tracker.py --file dependencies.yaml --validate
    
    if [ $? -ne 0 ]; then
        echo "❌ Dependency validation failed!"
        echo "Please update dependencies.yaml or fix dependency issues."
        exit 1
    fi
fi

echo "✓ Dependencies validated"
'''
    
    with open(hook_path, 'w') as f:
        f.write(hook_content)
    
    # Make executable
    hook_path.chmod(0o755)
    
    print(f"✓ Created pre-commit hook: {hook_path}")


def create_github_workflow(project_root: Path) -> None:
    """Create GitHub Actions workflow for dependency checking"""
    workflows_dir = project_root / '.github' / 'workflows'
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_path = workflows_dir / 'dependency-check.yml'
    
    workflow_content = '''name: Dependency Check

on:
  pull_request:
    paths:
      - '**.py'
      - '**.md'
      - 'dependencies.yaml'
  push:
    branches: [main, develop]

jobs:
  check-dependencies:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyyaml watchdog
    
    - name: Validate dependencies
      run: |
        python tools/dependencies/tracker.py --validate
    
    - name: Check for missing tests
      run: |
        python tools/dependencies/tracker.py --check-missing-tests
    
    - name: Generate dependency report
      if: always()
      run: |
        python tools/dependencies/tracker.py --export-graph
        
    - name: Upload dependency graph
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: dependency-graph
        path: dependency_graph.json
'''
    
    with open(workflow_path, 'w') as f:
        f.write(workflow_content)
    
    print(f"✓ Created GitHub workflow: {workflow_path}")


def create_watcher_config(project_root: Path) -> None:
    """Create configuration file for the dependency watcher"""
    config_path = project_root / '.dependency-config.yaml'
    
    config = {
        'watcher': {
            'watch_patterns': ['**/*.py', '**/*.md', '**/*.yaml'],
            'ignore_patterns': [
                '__pycache__', '.git', '.pytest_cache', 'venv',
                'env', 'build', 'dist', '*.egg-info', 'htmlcov'
            ],
            'debounce_seconds': 2.0,
            'max_concurrent_updates': 3
        },
        'updater': {
            'auto_update': {
                'tests': False,  # Start with manual mode
                'docs': False,
                'dependent_code': False
            },
            'update_modes': {
                'tests': 'suggest',
                'docs': 'suggest',
                'code': 'manual'
            },
            'validation': {
                'run_tests': True,
                'check_coverage': True,
                'lint_code': True
            }
        },
        'claude_integration': {
            'enabled': True,
            'model': 'claude-3-opus-20240229',
            'max_tokens': 4096,
            'instructions': {
                'test_creation': 'Create comprehensive unit tests following existing patterns',
                'test_update': 'Update tests to cover changes, maintain existing test style',
                'doc_update': 'Update documentation to reflect changes, keep examples current'
            }
        },
        'rules': {
            'test_file_pattern': 'tests/unit/test_{module}.py',
            'doc_file_pattern': 'docs_src/api/{module}.md',
            'coverage_threshold': 0.95,
            'require_tests_for_new_code': True
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Created configuration: {config_path}")


def create_claude_integration(project_root: Path) -> None:
    """Create CLAUDE.md for dependency system"""
    claude_path = project_root / 'tools' / 'dependencies' / 'CLAUDE.md'
    
    content = '''# Dependency System Integration Guide for Claude

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
'''
    
    with open(claude_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Created Claude integration guide: {claude_path}")


def setup_vscode_integration(project_root: Path) -> None:
    """Create VS Code tasks for dependency management"""
    vscode_dir = project_root / '.vscode'
    vscode_dir.mkdir(exist_ok=True)
    
    tasks_path = vscode_dir / 'tasks.json'
    
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Check Dependencies",
                "type": "shell",
                "command": "python",
                "args": [
                    "tools/dependencies/tracker.py",
                    "--file",
                    "${file}",
                    "--related"
                ],
                "group": "test",
                "presentation": {
                    "reveal": "always",
                    "panel": "dedicated"
                },
                "problemMatcher": []
            },
            {
                "label": "Update Dependencies",
                "type": "shell",
                "command": "python",
                "args": [
                    "tools/dependencies/updater.py",
                    "${file}",
                    "--dry-run"
                ],
                "group": "build",
                "presentation": {
                    "reveal": "always",
                    "panel": "dedicated"
                },
                "problemMatcher": []
            },
            {
                "label": "Watch Dependencies",
                "type": "shell",
                "command": "python",
                "args": [
                    "tools/dependencies/watcher.py"
                ],
                "isBackground": true,
                "presentation": {
                    "reveal": "always",
                    "panel": "dedicated"
                },
                "problemMatcher": []
            }
        ]
    }
    
    # Merge with existing tasks if file exists
    if tasks_path.exists():
        with open(tasks_path, 'r') as f:
            existing = json.load(f)
            existing['tasks'].extend(tasks['tasks'])
            tasks = existing
    
    with open(tasks_path, 'w') as f:
        json.dump(tasks, f, indent=2)
    
    print(f"✓ Created VS Code tasks: {tasks_path}")


def main():
    """Main setup function"""
    project_root = Path.cwd()
    
    print("Setting up dependency tracking system...")
    print(f"Project root: {project_root}")
    print()
    
    # Check if this is a git repository
    if not (project_root / '.git').exists():
        print("⚠ Warning: Not a git repository. Some features will be skipped.")
        print()
    
    # Create components
    steps = [
        ("Creating dependencies.yaml", lambda: create_dependencies_yaml(project_root)),
        ("Setting up pre-commit hook", lambda: create_pre_commit_hook(project_root)),
        ("Creating GitHub workflow", lambda: create_github_workflow(project_root)),
        ("Creating watcher configuration", lambda: create_watcher_config(project_root)),
        ("Creating Claude integration guide", lambda: create_claude_integration(project_root)),
        ("Setting up VS Code integration", lambda: setup_vscode_integration(project_root))
    ]
    
    for description, func in steps:
        try:
            print(f"\n{description}...")
            func()
        except Exception as e:
            print(f"❌ Error: {e}")
            print("  Continuing with setup...")
    
    print("\n✅ Dependency tracking setup complete!")
    print("\nNext steps:")
    print("1. Review dependencies.yaml for accuracy")
    print("2. Customize .dependency-config.yaml as needed")
    print("3. Test the watcher: python tools/dependencies/watcher.py")
    print("4. Configure your editor to use the dependency tools")
    
    print("\nUseful commands:")
    print("  python tools/dependencies/tracker.py --file <file> --related")
    print("  python tools/dependencies/updater.py <file> --dry-run")
    print("  python tools/dependencies/watcher.py")


if __name__ == '__main__':
    main()