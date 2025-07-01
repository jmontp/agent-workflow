# agent_workflow/ Package Documentation

This document provides comprehensive documentation for the `agent_workflow` Python package - the main distribution unit for the AI Agent TDD-Scrum Orchestration Framework.

## Package Overview

The `agent_workflow` package is a professionally structured Python distribution that provides a comprehensive framework for coordinating AI agents in Test-Driven Development and Scrum workflows. It serves as the primary entry point for users installing the system via pip/PyPI and provides both programmatic APIs and command-line interfaces.

### Package Architecture

The package follows modern Python packaging standards with clear separation of concerns:

```
agent_workflow/
├── __init__.py                 # Package entry point with core exports
├── orchestrator.py             # Simple orchestrator runner
├── cli/                        # Command-line interface modules
├── core/                       # Core orchestration components
├── config/                     # Configuration management
├── security/                   # Security and access control
├── integrations/              # External service integrations
└── templates/                 # Project and configuration templates
```

## Module Organization

### CLI Module (`cli/`)

The CLI module provides the primary user interface through console commands accessible via `agent-orch` and `aw` scripts.

**Key Components:**
- `main.py` - Primary CLI entry point with all commands
- `init.py` - Global environment initialization
- `project.py` - Project registration and management
- `orchestrator.py` - Orchestrator control (start/stop/status)
- `setup.py` - Integration setup (Discord, AI providers)
- `info.py` - System information and diagnostics
- `migrate.py` - Migration from git-clone installations
- `web.py` - Web interface management
- `utils.py` - CLI utilities and helpers

**Command Structure:**
```bash
# Core workflow commands
agent-orch init                      # Initialize global environment
agent-orch register-project <path>   # Register project for orchestration
agent-orch start [--discord]        # Start orchestration
agent-orch status [--project]       # View status

# Setup and configuration
agent-orch setup-discord            # Configure Discord integration
agent-orch setup-api               # Configure AI provider
agent-orch configure               # Interactive configuration

# Management and diagnostics
agent-orch projects list           # List registered projects
agent-orch health                  # System health check
agent-orch migrate-from-git       # Migrate from git installation
agent-orch web                    # Start web visualization
```

### Core Module (`core/`)

Contains the fundamental orchestration components that power the AI agent workflows.

**Components:**
- `orchestrator.py` - Central coordination engine managing multiple projects
- `state_machine.py` - Finite state machine enforcing workflow transitions
- `data_models.py` - Data classes for Projects, Epics, Stories, Sprints
- `project_storage.py` - File-based persistence and data management

**Key Classes:**
```python
from agent_workflow.core import (
    Orchestrator,           # Main orchestration engine
    StateMachine, State,    # Workflow state management
    ProjectData,            # Project container
    Epic, Story, Sprint,    # Scrum entities
    ProjectStorage          # Data persistence
)
```

### Configuration Module (`config/`)

**Purpose:** Global and project-specific configuration management

**Responsibilities:**
- Global orchestrator settings and preferences
- Project-specific configuration templates
- Configuration validation and migration
- Default settings management
- Environment-specific overrides

### Security Module (`security/`)

**Purpose:** Security controls and access restrictions for AI agents

**Responsibilities:**
- Agent permission profiles and restrictions
- Credential encryption and secure storage
- Command access control enforcement
- Security policy validation
- Audit logging for security events

### Integrations Module (`integrations/`)

**Purpose:** External service integrations and API clients

**Planned Components:**
- Discord bot for Human-in-the-Loop commands
- AI provider clients (Claude, OpenAI, local models)
- GitHub integration for version control
- Webhook handlers for external events
- Plugin system for custom integrations

### Templates Module (`templates/`)

**Purpose:** Project scaffolding and configuration templates

**Planned Content:**
- Project initialization templates by framework type
- Configuration file templates (YAML, JSON)
- Default workflow definitions
- Integration setup templates
- Documentation templates

## Package Entry Points

### Console Scripts

The package provides two equivalent console script entry points:

```toml
[project.scripts]
agent-orch = "agent_workflow.cli.main:main"
aw = "agent_workflow.cli.main:main"
```

**Usage:**
```bash
# Full command name
agent-orch start --discord

# Short alias
aw start --discord
```

### Programmatic API

Core components are exported at the package level for programmatic use:

```python
# Direct import from package root
from agent_workflow import (
    Orchestrator,
    StateMachine, State,
    ProjectStorage,
    ProjectData, Epic, Story, Sprint
)

# Module-specific imports
from agent_workflow.core import Orchestrator
from agent_workflow.cli.main import main as cli_main
```

## Installation and Distribution

### Package Installation

```bash
# Install from PyPI (when published)
pip install agent-workflow

# Install with optional dependencies
pip install agent-workflow[dev,docs,web,ai]

# Development installation
pip install -e .
```

### Optional Dependencies

The package defines several optional dependency groups:

- `dev` - Development tools (pytest, black, mypy, pre-commit)
- `docs` - Documentation generation (mkdocs, mkdocs-material)
- `web` - Web interface components (Flask, Flask-SocketIO)
- `ai` - AI provider integrations (anthropic, openai)

### Package Metadata

```python
from agent_workflow import get_package_info, get_version

version = get_version()  # "1.0.0"
info = get_package_info()  # Complete package metadata
```

## Core Integration with lib/ Directory

The `agent_workflow` package is designed to work alongside the existing `lib/` directory, providing a clean migration path:

### Relationship Pattern

1. **Package as Interface:** The `agent_workflow` package provides the clean, user-facing API
2. **lib/ as Implementation:** The `lib/` directory contains the current implementation
3. **Gradual Migration:** Components migrate from `lib/` to `agent_workflow` over time
4. **Backward Compatibility:** Both can coexist during transition

### Import Strategy

```python
# Package provides clean interfaces
from agent_workflow.core import Orchestrator

# Implementation may delegate to lib/ during migration
class Orchestrator:
    def __init__(self):
        # May use lib.global_orchestrator.GlobalOrchestrator internally
        pass
```

## Development Guidelines

### Package Development Standards

1. **Modern Python Packaging:**
   - Use `pyproject.toml` for configuration
   - Follow PEP 517/518 build standards
   - Proper dependency specification

2. **API Design:**
   - Clear, intuitive public interfaces
   - Proper typing annotations
   - Comprehensive docstrings
   - Backward compatibility considerations

3. **Module Organization:**
   - Single responsibility per module
   - Clear import hierarchies
   - Minimal circular dependencies
   - Logical grouping of functionality

4. **Testing Strategy:**
   - Unit tests for each module
   - Integration tests for CLI commands
   - Mock external dependencies
   - High coverage standards

### CLI Development

1. **Command Design:**
   - Consistent argument patterns
   - Helpful error messages
   - Progress indicators for long operations
   - Interactive prompts where appropriate

2. **User Experience:**
   - Clear help text and examples
   - Sensible defaults
   - Validation with helpful feedback
   - Graceful error handling

3. **Implementation:**
   - Use Click framework for CLI
   - Separate command logic from implementation
   - Proper option validation
   - Support for shell completion

### Configuration Management

1. **Configuration Hierarchy:**
   ```
   System defaults → Global config → Project config → CLI options
   ```

2. **File Locations:**
   - Global: `~/.config/agent-workflow/`
   - Project: `.orch-state/config.yaml`
   - Environment: `AGENT_WORKFLOW_*` variables

3. **Validation:**
   - Schema validation for all configuration
   - Clear error messages for invalid values
   - Migration support for config changes

## Usage Patterns

### Basic Workflow

```bash
# 1. Initialize global environment
agent-orch init --profile solo-engineer

# 2. Register a project
cd /path/to/my-project
agent-orch register-project . my-app --framework web

# 3. Start orchestration with Discord
agent-orch start --discord

# 4. Monitor status
agent-orch status --project my-app
```

### Programmatic Usage

```python
import asyncio
from agent_workflow import Orchestrator, ProjectStorage

async def main():
    # Initialize orchestrator
    orchestrator = Orchestrator()
    
    # Load project configuration
    storage = ProjectStorage("/path/to/project")
    project_data = storage.load_project_data()
    
    # Start orchestration
    await orchestrator.start([{
        "name": "my-project",
        "path": "/path/to/project",
        "mode": "blocking"
    }])

asyncio.run(main())
```

### Advanced Configuration

```python
from agent_workflow.core import StateMachine, State
from agent_workflow.config import ConfigManager

# Custom state machine configuration
config = ConfigManager.load_global_config()
config.workflow.allowed_transitions.update({
    State.SPRINT_ACTIVE: [State.SPRINT_PAUSED, State.SPRINT_COMPLETED]
})

# Save updated configuration
ConfigManager.save_global_config(config)
```

## Future Enhancements

### Planned Features

1. **Plugin System:**
   - Custom agent implementations
   - Workflow extensions
   - Integration plugins

2. **Advanced CLI:**
   - Shell completion
   - Interactive wizards
   - Rich terminal UI

3. **Web Dashboard:**
   - Real-time project monitoring
   - Visual workflow designer
   - Team collaboration features

4. **AI Integration:**
   - Multiple AI provider support
   - Model switching and routing
   - Performance optimization

### Migration Strategy

The package is designed to eventually replace the current script-based approach:

1. **Phase 1:** Package coexists with current scripts
2. **Phase 2:** CLI commands delegate to package implementations  
3. **Phase 3:** Package becomes primary interface
4. **Phase 4:** Legacy scripts deprecated

This approach ensures smooth transition while maintaining all current functionality.

## Integration with Repository Structure

The `agent_workflow` package integrates with the broader repository structure:

- **Documentation:** Package docs integrate with main MkDocs site
- **Testing:** Package tests integrate with repository test suite
- **CI/CD:** Package builds integrate with repository workflows
- **Configuration:** Package respects repository configuration standards

This design ensures the package feels like a natural part of the overall system while providing the clean, professional interface expected from a PyPI package.

## Troubleshooting

### 🔴 CRITICAL: Development Changes Not Reflecting

**Problem**: After making code changes, running commands like `aw web` still uses old code

**Root Cause**: Package installed in standard mode instead of editable/development mode

**Solution**:
```bash
# Uninstall existing installation
pip uninstall -y agent-workflow --break-system-packages

# Reinstall in editable mode (REQUIRED for development)
pip install -e . --user --break-system-packages

# Verify installation mode
pip show agent-workflow | grep Location
# Should show your working directory, NOT site-packages
```

**Why This Matters**:
- **Standard Install** (`pip install .`): Copies files to site-packages, changes require reinstall
- **Editable Install** (`pip install -e .`): Uses symlinks, changes reflect immediately

### Common Installation Issues

#### "Externally Managed Environment" Error
Modern Python installations protect system packages. Solutions:
1. Use `--user` flag for user installation
2. Use `--break-system-packages` if you understand the risks
3. Create a virtual environment (recommended for isolation)

#### Package Not Found After Installation
```bash
# Check if scripts are in PATH
which aw
which agent-orch

# If not found, add to PATH:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### Web Interface Port Conflicts
```bash
# Check what's using port 5000
lsof -i:5000

# Kill process if needed
lsof -ti:5000 | xargs kill -9

# Or use different port
aw web --port 8080
```

### Browser Cache Issues (Web Interface)

When updating JavaScript/CSS files, browsers may cache old versions:

**Hard Refresh Methods**:
- Windows/Linux: `Ctrl+F5` or `Ctrl+Shift+R`
- Mac: `Cmd+Shift+R`
- Chrome DevTools: Right-click refresh → "Empty Cache and Hard Reload"
- Use incognito/private window to bypass all caches

### Development Best Practices

1. **Always use editable install** for development: `pip install -e .`
2. **Restart services** after Python changes: `aw web-stop && aw web`
3. **Hard refresh browser** after JS/CSS changes
4. **Check logs** with `--debug` flag for detailed error information
5. **Verify changes** by checking file timestamps or using `git status`