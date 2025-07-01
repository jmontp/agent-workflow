# scripts/ Directory - Main Executable Scripts

This directory contains the main entry point scripts for the AI Agent TDD-Scrum workflow orchestration system. These scripts serve as the primary executable interfaces for running the orchestrator in different configurations.

## Overview

The scripts/ directory provides two main orchestration entry points:

1. **`orchestrator.py`** - Single-project orchestrator for focused development
2. **`multi_project_orchestrator.py`** - Multi-project coordination system

Both scripts integrate with the `lib/` modules and the `agent_workflow/` package to provide comprehensive orchestration capabilities.

> **💡 Note**: For most users, the modern CLI commands (`agent-orch` or `aw`) provide a cleaner interface:
> - `aw start` instead of `python scripts/orchestrator.py`
> - `aw web` for the web interface with Discord chat
> - `aw projects` for project management
> 
> See `agent_workflow/CLAUDE.md` for CLI documentation.

## Scripts Description

### orchestrator.py - Single-Project Orchestrator

**Purpose**: Main single-project orchestration engine that manages AI agent workflows, state machines, and Human-In-The-Loop (HITL) approval processes.

**Key Features**:
- **State Machine Management**: Enforces proper workflow sequencing (IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW)
- **Agent Coordination**: Manages DesignAgent, CodeAgent, QAAgent, and DataAgent with security restrictions
- **TDD State Machine**: Integrated Test-Driven Development workflow support
- **HITL Approval Gates**: Human approval workflow for strategic decisions
- **Context Management**: Optional context manager integration for enhanced agent coordination
- **Project Storage**: File-based persistence for project data and state
- **Discord Integration**: Preparatory integration with Discord bot interface

**Command Line Interface**:
```bash
# Direct execution
python scripts/orchestrator.py

# With configuration
python scripts/orchestrator.py --config config/projects.yaml
```

**Integration Points**:
- Uses `lib/state_machine.py` for workflow state management
- Integrates with `lib/agents/` for AI agent coordination
- Connects to `lib/project_storage.py` for data persistence
- Supports `lib/context_manager.py` for enhanced context awareness
- Implements `lib/tdd_state_machine.py` for TDD workflows

**Orchestration Modes**:
- **BLOCKING**: Requires human approval for all strategic decisions
- **PARTIAL**: Executes with quarantined output for review
- **AUTONOMOUS**: Full execution with monitoring and alerts

### multi_project_orchestrator.py - Multi-Project Coordination

**Purpose**: Unified entry point for multi-project AI-assisted development orchestration with advanced resource management, security, and cross-project intelligence.

**Key Features**:
- **Multi-Project Management**: Simultaneous coordination of multiple projects
- **Resource Scheduling**: CPU, memory, and agent allocation across projects
- **Security System**: Project isolation, user management, and access control
- **Cross-Project Intelligence**: Pattern recognition and knowledge transfer
- **Monitoring System**: Real-time monitoring with Prometheus/Grafana support
- **Discord Bot Integration**: Multi-project Discord interface
- **Interactive Shell**: Command-line interface for system management

**Command Line Interface**:
```bash
# Basic startup
python scripts/multi_project_orchestrator.py

# With configuration
python scripts/multi_project_orchestrator.py --config orch-config.yaml

# Enable all features
python scripts/multi_project_orchestrator.py --enable-discord --debug

# Daemon mode
python scripts/multi_project_orchestrator.py --daemon

# Interactive mode
python scripts/multi_project_orchestrator.py --interactive

# Project discovery
python scripts/multi_project_orchestrator.py --discover /path/to/projects

# Register specific project
python scripts/multi_project_orchestrator.py --register MyProject /path/to/project

# Status check
python scripts/multi_project_orchestrator.py --status
```

**Advanced Options**:
- `--no-security`: Disable security features
- `--no-monitoring`: Disable monitoring
- `--no-intelligence`: Disable cross-project intelligence
- `--enable-discord`: Enable Discord bot integration
- `--debug`: Enable debug logging

**Integration Points**:
- Uses `lib/global_orchestrator.py` for unified coordination
- Integrates with `lib/resource_scheduler.py` for resource management
- Connects to `lib/multi_project_security.py` for security
- Implements `lib/cross_project_intelligence.py` for intelligence
- Supports `lib/multi_project_monitoring.py` for monitoring
- Includes `lib/multi_project_discord_bot.py` for Discord integration

## Script Execution Patterns

### Direct Execution

Both scripts can be executed directly from the command line:

```bash
# Single-project orchestrator
python scripts/orchestrator.py

# Multi-project orchestrator
python scripts/multi_project_orchestrator.py --interactive
```

### Module Integration

The scripts integrate with the `agent_workflow/` package structure:

```bash
# Via package module
python -m agent_workflow.orchestrator

# Via CLI commands
agent-orch start --project myproject
agent-orch status
agent-orch stop
```

### Configuration Management

Both scripts support configuration files:

```yaml
# config/projects.yaml (single-project)
projects:
  - name: "my-project"
    path: "/path/to/project"
    orchestration: "blocking"

# orch-config.yaml (multi-project)
global:
  max_concurrent_projects: 5
  resource_allocation_strategy: "dynamic"
projects:
  project1:
    path: "/path/to/project1"
    priority: "high"
```

## Integration with lib/ Modules

### Core Dependencies

Both scripts depend on core `lib/` modules:

```python
# State management
from lib.state_machine import StateMachine
from lib.tdd_state_machine import TDDStateMachine

# Agent coordination
from lib.agents import create_agent, get_available_agents

# Data persistence
from lib.project_storage import ProjectStorage
from lib.data_models import ProjectData, Epic, Story, Sprint

# Context management (optional)
from lib.context_manager import ContextManager
```

### Multi-Project Specific

The multi-project orchestrator uses advanced modules:

```python
# Configuration management
from lib.multi_project_config import MultiProjectConfigManager

# Resource management
from lib.resource_scheduler import ResourceScheduler

# Security system
from lib.multi_project_security import MultiProjectSecurity

# Intelligence system
from lib.cross_project_intelligence import CrossProjectIntelligence

# Monitoring
from lib.multi_project_monitoring import MultiProjectMonitoring
```

## Integration with agent_workflow/ Package

### CLI Interface

The scripts integrate with the structured CLI interface:

```python
# CLI orchestrator commands
from agent_workflow.cli.orchestrator import start_command, stop_command, status_command

# Core orchestrator functionality
from agent_workflow.core.orchestrator import Orchestrator
from agent_workflow.core.state_machine import StateMachine
```

### Package Structure Integration

The scripts serve as entry points to the structured package:

```
agent_workflow/
├── cli/                    # CLI interface
│   ├── orchestrator.py     # Orchestrator CLI commands
│   └── main.py            # Main CLI entry point
├── core/                   # Core functionality
│   ├── orchestrator.py    # Core orchestrator class
│   └── state_machine.py   # State machine implementation
└── orchestrator.py        # Package-level orchestrator
```

## Usage Examples

### Single-Project Development

```bash
# Start orchestrator for focused development
python scripts/orchestrator.py

# With specific configuration
python scripts/orchestrator.py --config my-project.yaml

# Via CLI package
agent-orch start --project my-project --mode autonomous
```

### Multi-Project Coordination

```bash
# Start multi-project system
python scripts/multi_project_orchestrator.py --interactive

# Discover and register projects
python scripts/multi_project_orchestrator.py --discover ~/projects

# Run as daemon with Discord
python scripts/multi_project_orchestrator.py --daemon --enable-discord

# Check system status
python scripts/multi_project_orchestrator.py --status
```

### Interactive Management

```bash
# Multi-project interactive shell
python scripts/multi_project_orchestrator.py --interactive

multi-orch> help
multi-orch> projects
multi-orch> status
multi-orch> register new-project /path/to/project
multi-orch> start new-project
multi-orch> optimize
multi-orch> insights
multi-orch> exit
```

## Development Guidelines

### Adding New Scripts

When adding new scripts to this directory:

1. **Follow Naming Convention**: Use descriptive names that indicate purpose
2. **Include Docstrings**: Comprehensive module and function documentation
3. **Integration Points**: Clearly document integration with lib/ and agent_workflow/
4. **Command Line Interface**: Provide argparse-based CLI with help text
5. **Error Handling**: Implement comprehensive error handling and logging
6. **Configuration Support**: Support configuration files and environment variables

### Script Organization

```python
#!/usr/bin/env python3
"""
Script Title - Brief Description

Detailed description of script purpose, features, and usage.
"""

# Standard library imports
import asyncio
import argparse
import logging

# Third-party imports
import yaml

# Add lib directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# Local imports
from module_name import ClassName

# Script implementation
class ScriptClass:
    """Main script class with initialization and execution logic."""
    
    def __init__(self, config_path: str):
        """Initialize script with configuration."""
        pass
    
    async def run(self):
        """Main execution method."""
        pass

async def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Script description")
    # Add arguments
    args = parser.parse_args()
    
    # Initialize and run script
    script = ScriptClass(args.config)
    await script.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Testing Integration

Scripts should be testable and integrate with the test suite:

```python
# In tests/integration/test_scripts.py
def test_orchestrator_script():
    """Test orchestrator script execution."""
    pass

def test_multi_project_orchestrator_script():
    """Test multi-project orchestrator script execution."""
    pass
```

## Security Considerations

### Agent Security

Both scripts implement agent security through:

- **Tool Restrictions**: Specific tools allowed per agent type
- **Command Validation**: State machine validation for all commands
- **Isolation**: Project isolation and sandboxing
- **Audit Logging**: Comprehensive logging of all actions

### Multi-Project Security

The multi-project orchestrator adds:

- **User Management**: Role-based access control
- **Project Isolation**: Containerized project environments
- **Resource Limits**: CPU, memory, and agent limits
- **Audit Trails**: Complete audit logging

## Performance Considerations

### Resource Management

- **Async Operations**: All I/O operations are asynchronous
- **Resource Pooling**: Shared resources across projects
- **Monitoring**: Real-time resource monitoring
- **Optimization**: Automatic resource optimization

### Scalability Features

- **Horizontal Scaling**: Support for distributed execution
- **Load Balancing**: Intelligent task distribution
- **Caching**: Context and state caching
- **Batching**: Batch processing for efficiency

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure lib/ directory is in Python path
2. **Configuration Errors**: Validate YAML configuration files
3. **Permission Errors**: Check file system permissions
4. **Resource Conflicts**: Monitor resource usage and limits

### Debugging

```bash
# Enable debug logging
python scripts/orchestrator.py --log-level DEBUG

# Verbose mode
python scripts/multi_project_orchestrator.py --debug --verbose

# Status checking
python scripts/multi_project_orchestrator.py --status
```

## Future Enhancements

### Planned Features

1. **Web Interface**: Web-based orchestrator management
2. **API Endpoints**: RESTful API for external integration
3. **Plugin System**: Extensible plugin architecture
4. **Cloud Integration**: Cloud provider integration
5. **Advanced Analytics**: Machine learning-based optimization

### Extension Points

- **Custom Agents**: Framework for custom agent development
- **Workflow Templates**: Reusable workflow templates
- **Integration Hooks**: Webhook and API integration points
- **Custom Metrics**: User-defined performance metrics

This documentation provides a comprehensive overview of the scripts/ directory and its role as the main entry point for the AI Agent TDD-Scrum workflow orchestration system.