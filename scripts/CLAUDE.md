# scripts/ Directory - Legacy Scripts (Migrated)

**IMPORTANT**: As of the Phase 1-4 refactoring completion, the functionality previously provided by scripts in this directory has been **migrated to the modern CLI interface**.

## Migration Status

The scripts that were previously in this directory have been **removed** and their functionality has been integrated into the `agent_workflow` package structure:

### Migrated Functionality

1. **`orchestrator.py`** (REMOVED) → Migrated to:
   - CLI: `aw start` command
   - Package: `agent_workflow/orchestrator.py` 
   - Core: `agent_workflow/core/orchestrator.py`

2. **`multi_project_orchestrator.py`** (REMOVED) → Migrated to:
   - CLI: `aw start --multi-project` command
   - Package: Multi-project functionality integrated into CLI

## Modern Usage

**Use the CLI interface instead of the old scripts:**

```bash
# Instead of: python scripts/orchestrator.py
aw start

# Instead of: python scripts/multi_project_orchestrator.py --interactive  
aw start --interactive

# Project management
aw projects
aw register-project /path/to/project

# Web interface
aw web

# Status and health
aw status
aw health
```

See `agent_workflow/CLAUDE.md` for complete CLI documentation.

## Historical Documentation

The following sections document the functionality that was previously provided by the removed scripts. This information is preserved for reference and to understand the migration path.

### Previous orchestrator.py Functionality

The removed `orchestrator.py` script provided single-project orchestration with:

- **State Machine Management**: Workflow sequencing (IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW)
- **Agent Coordination**: DesignAgent, CodeAgent, QAAgent, and DataAgent management
- **TDD State Machine**: Test-Driven Development workflow support
- **HITL Approval Gates**: Human approval workflow for strategic decisions
- **Context Management**: Enhanced agent coordination capabilities
- **Project Storage**: File-based persistence for project data and state

**Migrated to**: `aw start` command and `agent_workflow/core/orchestrator.py`

### Previous multi_project_orchestrator.py Functionality

The removed `multi_project_orchestrator.py` script provided multi-project coordination with:

- **Multi-Project Management**: Simultaneous coordination of multiple projects
- **Resource Scheduling**: CPU, memory, and agent allocation across projects  
- **Security System**: Project isolation, user management, and access control
- **Cross-Project Intelligence**: Pattern recognition and knowledge transfer
- **Monitoring System**: Real-time monitoring capabilities
- **Discord Bot Integration**: Multi-project Discord interface
- **Interactive Shell**: Command-line interface for system management

**Migrated to**: `aw` CLI commands with multi-project support

## Migration Path Documentation

### CLI Command Mapping

The functionality from the removed scripts is now available through CLI commands:

```bash
# Package module execution
python -m agent_workflow.orchestrator

# Modern CLI commands
aw start --project myproject
aw status
aw stop
aw projects
aw web
```

### Configuration Management

Configuration is now handled through:

```yaml
# config.yml (unified configuration)
global:
  max_concurrent_projects: 5
  resource_allocation_strategy: "dynamic"
projects:
  project1:
    path: "/path/to/project1"
    priority: "high"
```

## Current Architecture Integration

### Package Structure

The functionality is now integrated into the `agent_workflow` package:

```
agent_workflow/
├── cli/                    # CLI interface with 'aw' commands
│   ├── orchestrator.py     # Orchestrator CLI commands
│   └── main.py            # Main CLI entry point
├── core/                   # Core functionality
│   ├── orchestrator.py    # Core orchestrator class
│   └── state_machine.py   # State machine implementation
└── orchestrator.py        # Package-level orchestrator entry point
```

### Modern Usage Examples

```bash
# Single-project development
aw start --project my-project --mode autonomous

# Multi-project coordination
aw start --multi-project --interactive

# Project discovery and registration
aw register-project ~/projects/my-project

# System management
aw status
aw health
aw projects

# Web interface
aw web
```

## Migration Complete

The scripts directory migration is complete. All script functionality has been successfully integrated into the modern `agent_workflow` CLI interface.

### For Developers

If you need to add new executable functionality:

1. **Use CLI Commands**: Add new commands to `agent_workflow/cli/`
2. **Package Integration**: Integrate with the `agent_workflow` package structure
3. **Follow Patterns**: Follow existing CLI command patterns in the codebase

### For Users

- **Modern Interface**: Use `aw` or `agent-orch` commands
- **Full Documentation**: See `agent_workflow/CLAUDE.md` for complete CLI reference
- **Web Interface**: Use `aw web` for the Discord-style web interface

This completes the scripts directory refactoring as part of the comprehensive architectural consolidation.