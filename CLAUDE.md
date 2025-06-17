# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**IMPORTANT**: The markdown documentation files in the main repository (HITL_COMMANDS.md, command_state_machine.md, sequence_diagram.md, user_profile.md) are current and accurate. The code in the `agent-workflow/` subdirectory is outdated and represents early prototyping work that has not been updated to match the current documentation.

## Project Overview

This is an **AI Agent TDD-Scrum workflow** system that implements a Human-In-The-Loop (HITL) orchestration framework. The system coordinates multiple specialized AI agents through a Discord interface, following a research-mode Scrum methodology optimized for solo engineers working with AI assistance.

## Architecture

### Core Components
- **Orchestrator** (`agent-workflow/orchestrator.py`): Central coordination engine that manages workflows across multiple projects, implements HITL approval gates, and maintains state
- **Agent Registry** (`agent-workflow/agents/`): Specialized AI agents (Design, Code, Data, QA) with base class inheritance 
- **Discord Interface** (`agent-workflow/interfaces/discord_bot.py`): Primary HITL command interface with slash commands and interactive state visualization
- **State Machine**: Finite state machine enforcing proper command sequencing (IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW)

### Key Patterns
- **Multi-Project Orchestration**: Single orchestrator manages multiple projects defined in `config/projects.yaml`
- **HITL Approval Workflow**: Strategic decisions escalate to humans after 3 failed attempts
- **Discord-First Interface**: Project-specific channels (`hostname-projectname`) with interactive buttons
- **State Persistence**: Runtime state maintained in `.orch-state/status.json` per project

## Development Commands

```bash
# Main development workflow
make run                    # Run full demo with Discord bot
make test                   # Run Discord integration tests
make orchestrator-only      # Run orchestrator without Discord interface

# Direct Python execution
python agent-workflow/demo_discord_server.py              # Full demo
python agent-workflow/test_discord_functionality.py       # Test Discord features
python agent-workflow/orchestrator.py                     # Orchestrator only
```

## Dependencies

Install Python dependencies:
```bash
cd agent-workflow && pip install -r requirements.txt
```

Core dependencies: `discord.py`, `pygithub`, `pyyaml`, `anthropic`

## Configuration

### Required Environment Variables
- `DISCORD_BOT_TOKEN`: Required for Discord bot functionality

### Configuration Files
- `agent-workflow/config/projects.yaml`: Project definitions and orchestration modes
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

## Agent Implementation Status

- **Current**: Agents are placeholder implementations that echo commands
- **TODO**: Integration with Anthropic API for actual AI agent capabilities
- **Pattern**: All agents inherit from `BaseAgent` with standardized `async def run(cmd, dry=False)` interface

## Testing Approach

- Test files focus on Discord integration and channel management
- Target TDD approach with failing tests first
- State machine validation through table-driven tests
- Mock Discord interactions for development without live bot

## Multi-Project Workflow

The orchestrator monitors multiple projects simultaneously, each with independent state machines and Discord channels. Projects are defined in YAML with orchestration modes: `blocking` (requires approval), `partial` (quarantined output), or `autonomous` (full execution).