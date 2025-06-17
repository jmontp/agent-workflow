# System Overview

The AI Agent TDD-Scrum Workflow system is a Human-In-The-Loop orchestration framework that coordinates specialized AI agents for software development tasks.

## Core Concepts

### Multi-Agent Coordination
The system manages four specialized AI agents:
- **DesignAgent**: Architecture and technical specifications
- **CodeAgent**: Feature implementation and bug fixes  
- **QAAgent**: Testing and quality validation
- **DataAgent**: Data analysis and visualization

### Human-In-The-Loop Control
Strategic decisions require human approval:
- Epic and story creation
- Sprint planning and execution
- Code review and deployment
- Error handling and escalation

### State-Driven Workflow
A finite state machine enforces proper development sequences:
- `IDLE` → `BACKLOG_READY` → `SPRINT_PLANNED` → `SPRINT_ACTIVE`
- Invalid commands are rejected with helpful guidance
- Current state determines available actions

## Two-Repository Architecture

### Orchestration Repository
**Purpose**: Central coordination framework
- Agent definitions and capabilities
- Workflow engine and state machine
- Discord bot and user interface
- Security policies and tool restrictions

### Project Repositories  
**Purpose**: Individual development projects
- Project source code
- Embedded workflow data (`.orch-state/` directory)
- Sprint plans, backlogs, and progress tracking
- Architecture decisions and documentation

**Benefits:**
- Project data stays with project code
- Version control for management artifacts
- Easy project migration between orchestrator instances
- Clear security boundaries

## Key Components

### Discord Interface
Primary user interaction through slash commands:
- `/epic "description"` - Define high-level initiatives
- `/sprint plan|start|status` - Manage development cycles
- `/approve [ID...]` - Authorize agent actions
- `/state` - Interactive system inspection

### State Machine
Enforces proper workflow sequences:
- Prevents invalid operations
- Guides users through correct command sequences
- Provides clear error messages
- Visual state diagrams for understanding

### Agent Security
Tool access control ensures safe operation:
- DesignAgent: Read-only documentation creation
- CodeAgent: Code editing and version control
- QAAgent: Testing and quality analysis only
- DataAgent: Data processing and visualization

### Project Management
Integrated development lifecycle:
- Epic and story hierarchies
- Sprint planning and execution
- Progress tracking and reporting
- Automated task escalation

## Workflow Philosophy

The system follows **research-mode Scrum** principles:
- Minimal ceremony, maximum momentum
- Solo engineer optimization
- AI-assisted task execution
- Human oversight for strategic decisions
- Continuous learning and adaptation

This approach balances automation benefits with human control, ensuring high-quality output while reducing manual effort.