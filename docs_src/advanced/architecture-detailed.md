# Architecture Overview

The AI Agent TDD-Scrum Workflow system follows a clean, layered architecture designed for scalability, maintainability, and extensibility.

## Two-Repository Model

The system operates on a clear separation between orchestration and project concerns:

### Orchestration Repository (this repo)
- **Purpose**: Central framework for AI agent coordination
- **Contents**: Agent definitions, workflow engine, Discord bot, security policies
- **Scope**: Global across all managed projects
- **Lifecycle**: Long-lived, evolves with framework capabilities

### Project Repositories (1 to n)
- **Purpose**: Individual codebases being developed with AI assistance
- **Contents**: Project code + embedded workflow data in `.orch-state/`
- **Scope**: Project-specific data and state
- **Lifecycle**: Tied to project development lifecycle

This separation ensures:
- **Data Ownership**: Project data stays with the project code
- **Version Control**: Project management data versioned with code changes
- **Portability**: Projects can move between orchestration instances
- **Security**: Clear boundaries between global and project-specific access

## System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        Discord[Discord Bot Interface]
        CLI[Command Line Interface]
    end
    
    subgraph "Application Layer"
        Orch[Orchestrator]
        SM[State Machine]
        Commands[Command Handlers]
    end
    
    subgraph "Domain Layer"
        Agents[AI Agent Library]
        Tasks[Task Management]
        Projects[Project Management]
    end
    
    subgraph "Infrastructure Layer"
        State[State Persistence]
        Config[Configuration]
        Logging[Logging & Monitoring]
    end
    
    Discord --> Orch
    CLI --> Orch
    Orch --> SM
    Orch --> Commands
    Commands --> Agents
    Commands --> Tasks
    Commands --> Projects
    Agents --> State
    Projects --> State
    Orch --> Config
    Orch --> Logging
```

## Core Principles

### 1. **Separation of Concerns**
Each layer has distinct responsibilities:
- **Interface Layer**: User interaction and external communication
- **Application Layer**: Workflow orchestration and business logic
- **Domain Layer**: Core business entities and AI agent coordination
- **Infrastructure Layer**: Data persistence, configuration, and cross-cutting concerns

### 2. **Finite State Machine**
The system enforces a strict state machine to ensure workflow integrity:
- Prevents invalid command sequences
- Provides clear error messages and hints
- Enables state visualization and debugging

### 3. **Event-Driven Architecture**
Components communicate through well-defined events:
- Command execution triggers state transitions
- Agent completion events update project status
- Human approval events unblock workflows

### 4. **Plugin Architecture**
Agents are designed as pluggable components:
- Common base interface for all agents
- Easy to add new specialized agents
- Configurable agent behavior per project

## Directory Structure

```
agent-workflow/
├── docs_src/           # MkDocs documentation source
├── docs/              # Original documentation files
├── scripts/           # Executable entry points
│   └── orchestrator.py
├── lib/               # Core library code
│   ├── agents/        # AI agent implementations
│   ├── state_machine.py
│   └── discord_bot.py
├── tests/             # Test suite
│   ├── unit/         # Unit tests
│   ├── integration/  # Integration tests
│   └── conftest.py   # Test configuration
├── requirements.txt   # Dependencies
├── mkdocs.yml        # Documentation configuration
├── Makefile          # Build automation
└── README.md         # Project overview
```

## Component Interaction

### 1. **Command Flow**
```mermaid
sequenceDiagram
    participant User
    participant Discord
    participant Orchestrator
    participant StateMachine
    participant Agent
    
    User->>Discord: /epic "Build auth system"
    Discord->>Orchestrator: handle_command()
    Orchestrator->>StateMachine: validate_command()
    StateMachine-->>Orchestrator: validation_result
    Orchestrator->>Agent: dispatch_task()
    Agent-->>Orchestrator: task_result
    Orchestrator->>StateMachine: transition_state()
    Orchestrator-->>Discord: command_response
    Discord-->>User: Success message
```

### 2. **State Management**
- **Centralized State**: Single source of truth in orchestrator
- **Persistent Storage**: State saved to `.orch-state/status.json`
- **State Recovery**: System recovers state on restart
- **Multi-Project**: Independent state machines per project

### 3. **Agent Coordination**
- **Task Queue**: Orchestrator maintains task queues per project
- **Retry Logic**: Automatic retry with exponential backoff
- **Human Escalation**: HITL approval after 3 failed attempts
- **Parallel Execution**: Multiple agents can work simultaneously

## Design Patterns

### 1. **Command Pattern**
Each user command is encapsulated as a command object:
- Enables undo/redo functionality
- Facilitates command logging and auditing
- Allows command queuing and batch processing

### 2. **State Pattern**
Workflow states encapsulate behavior:
- Each state defines allowed commands
- State transitions are explicit and validated
- Easy to add new states and transitions

### 3. **Strategy Pattern**
Agent implementations use strategy pattern:
- Agents can be swapped at runtime
- Different strategies for different project types
- Easy A/B testing of agent behaviors

### 4. **Observer Pattern**
Event-driven communication between components:
- Loose coupling between layers
- Easy to add new event handlers
- Supports monitoring and debugging

## Scalability Considerations

### 1. **Horizontal Scaling**
- Multiple orchestrator instances can run simultaneously
- Discord bot can be load-balanced
- Agent execution can be distributed

### 2. **Performance Optimization**
- Async/await throughout for I/O operations
- Caching of frequently accessed data
- Batch processing of similar tasks

### 3. **Resource Management**
- Connection pooling for external services
- Rate limiting for API calls
- Memory-efficient state storage

## Security Architecture

The system implements comprehensive security through multiple layers of protection. See [Security Implementation](security-implementation.md) for detailed information.

### 1. **Agent Security Model**
- **Command Access Control**: Each agent type has restricted tool access
- **Principle of Least Privilege**: Agents can only access necessary tools
- **Automatic Enforcement**: Security boundaries applied via Claude Code CLI flags

### 2. **Authentication & Authorization**
- Discord bot token authentication
- Role-based access control in Discord
- Project-level permission isolation
- Agent-specific security profiles

### 3. **Data Protection**
- No sensitive data stored in state files
- Environment variables for secrets
- Audit logging of all commands and agent tool usage
- State file access controls

## Extensibility Points

### 1. **Custom Agents**
```python
class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CustomAgent",
            capabilities=["custom_capability"]
        )
    
    async def run(self, task, dry_run=False):
        # Custom implementation
        pass
```

### 2. **Custom Commands**
Add new slash commands by extending the Discord bot:
```python
@app_commands.command(name="custom", description="Custom command")
async def custom_command(self, interaction, param: str):
    # Custom command implementation
    pass
```

### 3. **Custom States**
Extend the state machine with new workflow states:
```python
class CustomState(Enum):
    CUSTOM_STATE = "CUSTOM_STATE"
```

## Monitoring & Observability

### 1. **Logging Strategy**
- Structured logging with JSON format
- Different log levels per component
- Centralized log aggregation ready

### 2. **Metrics Collection**
- Command execution metrics
- Agent performance metrics
- State transition tracking

### 3. **Health Checks**
- Discord bot connectivity
- Agent responsiveness
- State persistence availability

---

!!! info "Architecture Evolution"
    This architecture is designed to evolve with the system's needs. New patterns and components can be added while maintaining backward compatibility.