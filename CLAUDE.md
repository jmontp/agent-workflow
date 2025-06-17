# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**IMPORTANT**: This repository contains a complete implementation of the AI Agent TDD-Scrum workflow system. The documentation in `docs_src/` (built with MkDocs) is current and the code implementation in `lib/`, `scripts/`, and `tests/` is fully functional and up-to-date.

## Project Overview

This is an **AI Agent TDD-Scrum workflow** system that implements a Human-In-The-Loop (HITL) orchestration framework. The system coordinates multiple specialized AI agents through a Discord interface, following a research-mode Scrum methodology optimized for solo engineers working with AI assistance.

## Architecture

### Directory Structure
```
docs_src/       # MkDocs documentation source files
scripts/        # Executable scripts (orchestrator entry point)
lib/            # Library code (agents, state machine, Discord bot, security)
tests/          # Comprehensive test suite
```

### Core Components
- **Orchestrator** (`scripts/orchestrator.py`): Central coordination engine that manages workflows across multiple projects, implements HITL approval gates, and maintains state
- **State Machine** (`lib/state_machine.py`): Finite state machine enforcing proper command sequencing (IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW)
- **Agent Library** (`lib/agents/`): Specialized AI agents (Design, Code, Data, QA) with base class inheritance and security controls
- **Discord Bot** (`lib/discord_bot.py`): Primary HITL command interface with slash commands and interactive state visualization
- **Security System** (`lib/agent_tool_config.py`): Command access control and tool restrictions per agent type

### Key Patterns
- **Multi-Project Orchestration**: Single orchestrator manages multiple projects defined in YAML configuration
- **HITL Approval Workflow**: Strategic decisions escalate to humans after 3 failed attempts
- **Discord-First Interface**: Project-specific channels (`hostname-projectname`) with interactive buttons
- **State Persistence**: Runtime state maintained in `.orch-state/status.json` per project
- **Agent Security**: Command access control through Claude Code CLI flags with per-agent restrictions

## Development Commands

```bash
# Run orchestrator directly
python scripts/orchestrator.py

# Run Discord bot with orchestrator
python lib/discord_bot.py

# Run tests
pytest tests/                    # Full test suite
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest -m "not slow"           # Skip slow tests

# Run security tests
python3 tests/unit/test_agent_tool_config.py

# Build documentation
mkdocs serve                    # Local development server
mkdocs build                    # Build static site
```

## Dependencies

Install Python dependencies:
```bash
pip install discord.py pygithub pyyaml pytest pytest-asyncio mkdocs-material
```

Core dependencies: `discord.py`, `pygithub`, `pyyaml`, `pytest`, `mkdocs-material`

## Configuration

### Required Environment Variables
- `DISCORD_BOT_TOKEN`: Required for Discord bot functionality

### AI Integration
- **Claude Code**: The system integrates with Claude Code CLI for AI capabilities
- **Agent Security**: Each agent type uses restricted Claude clients with tool access controls
- **Automatic Detection**: System automatically detects if Claude Code is available
- **Graceful Fallback**: Uses placeholder implementations when Claude Code is not available

### Configuration Files
- YAML project configuration files define orchestration modes and project paths
- Individual project directories contain `.orch-state/status.json` for runtime state
- Agent security profiles defined in `lib/agent_tool_config.py`

## HITL Command System

The system implements a finite state machine with these key commands:
- `/epic "<description>"` - Define high-level initiatives
- `/sprint plan|start|status|pause|resume` - Sprint lifecycle management  
- `/backlog view|add_story|prioritize` - Backlog management
- `/approve [ID]` - Approve queued tasks
- `/request_changes "<description>"` - Request modifications on PRs
- `/state` - Interactive state inspection with diagram visualization

Commands are validated against current state - invalid commands return helpful error messages with suggested alternatives.

## Implementation Details

### Agent System
- **Complete Implementation**: All agents are fully implemented with sophisticated capabilities
- **Security Model**: Command access control enforced via Claude Code CLI flags (`--allowedTools`/`--disallowedTools`)
- **Agent Types**: Orchestrator (full access), CodeAgent (edit+commit), DesignAgent (read-only), QAAgent (test-only), DataAgent (analysis-only)
- **Pattern**: All agents inherit from `BaseAgent` with standardized `async def run(task, dry_run=False)` interface
- **Specializations**: DesignAgent (architecture), CodeAgent (implementation), QAAgent (testing), DataAgent (analysis)

### Security Architecture
- **Command Access Control**: Each agent type has specific tool restrictions
- **Principle of Least Privilege**: Agents can only access tools necessary for their function
- **Automatic Enforcement**: Security boundaries applied transparently via Claude CLI
- **Comprehensive Testing**: All security restrictions validated in test suite

### Testing Framework
- **Comprehensive Test Suite**: Unit, integration, and E2E tests with >90% coverage target
- **Security Testing**: Agent tool access control validation in `tests/unit/test_agent_tool_config.py`
- **State Machine Testing**: Table-driven tests for all transitions and error conditions
- **Mocked Dependencies**: Discord, Claude Code, and GitHub APIs mocked for testing
- **Test Categories**: Unit tests in `tests/unit/`, integration tests in `tests/integration/`

### Discord Integration
- **Full Slash Command Support**: All HITL commands implemented with interactive UI
- **State Visualization**: Interactive buttons for state inspection and command discovery
- **Project Channels**: Automatic channel creation per project with naming convention
- **Error Handling**: Comprehensive error messages with helpful hints and suggestions

### Multi-Project Orchestration
The orchestrator monitors multiple projects simultaneously, each with independent state machines and Discord channels. Projects are defined in YAML with orchestration modes:
- `blocking`: Requires human approval for all strategic decisions
- `partial`: Executes with quarantined output for review
- `autonomous`: Full execution with monitoring and alerts

## Documentation Strategy

### MkDocs Structure
The documentation is organized in `docs_src/` for MkDocs build system:

```
docs_src/
├── index.md                    # Project overview
├── getting-started/
│   ├── installation.md         # Setup instructions
│   └── quick-start.md          # Getting started guide
├── user-guide/
│   ├── hitl-commands.md        # Command reference
│   ├── state-machine.md        # Workflow states
│   ├── user-profile.md         # User configuration
│   └── workflow-sequences.md   # Sequence diagrams
├── architecture/
│   ├── overview.md             # System architecture
│   ├── security.md             # Security model and agent restrictions
│   ├── component.md            # Component design
│   ├── container.md            # Container architecture
│   ├── context.md              # System context
│   └── code.md                 # Code organization
├── development/
│   └── testing.md              # Testing strategy
└── deployment/                 # Deployment guides
```

### Documentation Best Practices
- **Living Documentation**: Keep docs in sync with code changes
- **Security Documentation**: Document all agent restrictions and security boundaries
- **Architecture Diagrams**: Use Mermaid for visual documentation
- **Code Examples**: Include working code examples in documentation
- **Testing Coverage**: Document testing strategy and security validation

## Agent Security Profiles

### Orchestrator Agent
- **Access Level**: Full system access
- **Allowed**: All tools including rm, git commit, git push
- **Restricted**: Still blocks dangerous system commands (sudo, format, dd)
- **Use Case**: System-level workflow management and coordination

### Code Agent
- **Access Level**: Code modification and version control
- **Allowed**: File editing, git add/commit, testing tools, package management
- **Restricted**: File deletion, git push, system administration
- **Use Case**: Feature implementation, bug fixes, code refactoring

### Design Agent  
- **Access Level**: Read-only analysis and documentation
- **Allowed**: File reading, documentation creation, web research
- **Restricted**: Code editing, version control, system commands
- **Use Case**: Architecture design, technical specifications, code review

### QA Agent
- **Access Level**: Testing and quality analysis only
- **Allowed**: Test execution, code quality tools, coverage analysis
- **Restricted**: Code modification, version control, file creation
- **Use Case**: Test creation, quality validation, coverage reporting

### Data Agent
- **Access Level**: Data processing and analysis
- **Allowed**: Data file access, notebook creation, visualization tools
- **Restricted**: Source code modification, version control
- **Use Case**: Data analysis, reporting, metrics visualization

## Security Guidelines for Claude Code Integration

When working with this repository, Claude Code should be aware of:

1. **Agent Context**: If working within an agent context, tool access is automatically restricted
2. **Security Boundaries**: Different agent types have different permissions
3. **Test Requirements**: All security-related changes must include tests
4. **Documentation Updates**: Security changes require documentation updates

## Important Notes for Claude Code

- **Documentation Location**: Primary docs are in `docs_src/` (MkDocs format)
- **Security Testing**: Always run `tests/unit/test_agent_tool_config.py` after security changes
- **Agent Restrictions**: Each agent type has specific tool limitations for security
- **State Management**: The system uses finite state machines with strict validation
- **HITL Workflow**: Human approval is required for strategic decisions