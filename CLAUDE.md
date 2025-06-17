# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**IMPORTANT**: This repository contains a complete implementation of the AI Agent TDD-Scrum workflow system. The documentation in `docs/` is current and the code implementation in `lib/`, `scripts/`, and `tests/` is fully functional and up-to-date.

## Project Overview

This is an **AI Agent TDD-Scrum workflow** system that implements a Human-In-The-Loop (HITL) orchestration framework. The system coordinates multiple specialized AI agents through a Discord interface, following a research-mode Scrum methodology optimized for solo engineers working with AI assistance.

## Architecture

### Directory Structure
```
docs/           # Documentation and specifications
scripts/        # Executable scripts (orchestrator entry point)
lib/            # Library code (agents, state machine, Discord bot)
tests/          # Comprehensive test suite
```

### Core Components
- **Orchestrator** (`scripts/orchestrator.py`): Central coordination engine that manages workflows across multiple projects, implements HITL approval gates, and maintains state
- **State Machine** (`lib/state_machine.py`): Finite state machine enforcing proper command sequencing (IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW)
- **Agent Library** (`lib/agents/`): Specialized AI agents (Design, Code, Data, QA) with base class inheritance
- **Discord Bot** (`lib/discord_bot.py`): Primary HITL command interface with slash commands and interactive state visualization

### Key Patterns
- **Multi-Project Orchestration**: Single orchestrator manages multiple projects defined in YAML configuration
- **HITL Approval Workflow**: Strategic decisions escalate to humans after 3 failed attempts
- **Discord-First Interface**: Project-specific channels (`hostname-projectname`) with interactive buttons
- **State Persistence**: Runtime state maintained in `.orch-state/status.json` per project

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
- **Automatic Detection**: System automatically detects if Claude Code is available
- **Graceful Fallback**: Uses placeholder implementations when Claude Code is not available

### Configuration Files
- YAML project configuration files define orchestration modes and project paths
- Individual project directories contain `.orch-state/status.json` for runtime state

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
- **Anthropic Integration**: Ready for AI model integration (placeholder implementations for development)
- **Pattern**: All agents inherit from `BaseAgent` with standardized `async def run(task, dry_run=False)` interface
- **Specializations**: DesignAgent (architecture), CodeAgent (implementation), QAAgent (testing), DataAgent (analysis)

### Testing Framework
- **Comprehensive Test Suite**: Unit, integration, and E2E tests with >90% coverage target
- **State Machine Testing**: Table-driven tests for all transitions and error conditions
- **Mocked Dependencies**: Discord, Anthropic, and GitHub APIs mocked for testing
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