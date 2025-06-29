# System Architecture Overview - Complete Technical Design

> **Comprehensive C4 architecture diagrams, component specifications, and system design for AI agent orchestration framework**

The AI Agent TDD-Scrum Workflow system is designed as a sophisticated multi-layered architecture that orchestrates AI agents through Test-Driven Development cycles within a Scrum framework. This document provides a comprehensive view using the C4 model (Context, Container, Component, Code).

## Level 1: System Context Diagram

### High-Level Architecture | System Boundaries | External Integrations | User Interactions

The system operates as a central orchestration hub between engineers, AI agents, and project repositories:

```mermaid
graph TB
    subgraph "External Systems"
        Claude[Claude AI API<br/>AI Agent Backend]
        GitHub[GitHub API<br/>Version Control]
        FileSystem[File System<br/>Project Storage]
    end
    
    subgraph "Users"
        Engineer[Solo Engineer<br/>Primary User]
        TeamLead[Team Lead<br/>Review & Approval]
    end
    
    System[AI Agent TDD-Scrum<br/>Workflow System<br/><br/>Orchestrates AI agents through<br/>TDD cycles for software development]
    
    Engineer -->|Commands via Discord| System
    TeamLead -->|Approvals & Reviews| System
    System -->|AI Agent Requests| Claude
    System -->|Code & PR Management| GitHub
    System -->|Project Data Persistence| FileSystem
    
    style System fill:#4ecdc4,stroke:#2d6e6e,stroke-width:3px
    style Engineer fill:#95e1d3,stroke:#3aa68b,stroke-width:2px
    style TeamLead fill:#95e1d3,stroke:#3aa68b,stroke-width:2px
    style Claude fill:#f38181,stroke:#c44569,stroke-width:2px
    style GitHub fill:#f38181,stroke:#c44569,stroke-width:2px
    style FileSystem fill:#f38181,stroke:#c44569,stroke-width:2px
```

### Key Relationships

- **Engineer → System**: Primary interaction through Discord slash commands
- **System → Claude AI**: Specialized agent requests with security boundaries
- **System → GitHub**: Automated PR creation, code commits, issue management
- **System → File System**: Persistent storage of project state and configuration

## Level 2: Container Architecture

### Application Containers | Service Components | Data Flow | Technology Stack

The system is composed of multiple containers working in concert:

```mermaid
graph TB
    subgraph "AI Agent TDD-Scrum Workflow System"
        subgraph "Interface Layer"
            Discord[Discord Bot<br/>Container<br/><br/>Python/discord.py<br/>Slash commands & UI]
            WebAPI[REST API<br/>Container<br/><br/>Python/FastAPI<br/>External integrations]
        end
        
        subgraph "Orchestration Layer"
            Orchestrator[Multi-Project<br/>Orchestrator<br/><br/>Python<br/>Workflow coordination]
            StateMachine[Dual State<br/>Machine System<br/><br/>Python<br/>Workflow & TDD states]
            ResourceMgr[Resource<br/>Scheduler<br/><br/>Python<br/>Agent allocation]
        end
        
        subgraph "Agent Layer"
            AgentFactory[Agent Factory<br/>Container<br/><br/>Python<br/>Agent lifecycle]
            AgentPool[Agent Pool<br/>Manager<br/><br/>Python<br/>Pool management]
            Security[Security<br/>Controller<br/><br/>Python<br/>Access control]
        end
        
        subgraph "Context Layer"
            ContextMgr[Context Manager<br/>Container<br/><br/>Python<br/>Cross-agent memory]
            TokenCalc[Token Calculator<br/>Container<br/><br/>Python/tiktoken<br/>Context optimization]
            Cache[Context Cache<br/>Container<br/><br/>Python/Redis<br/>Performance cache]
        end
        
        subgraph "Data Layer"
            ProjectStore[Project Storage<br/>Container<br/><br/>Python/JSON<br/>File persistence]
            StateStore[State Storage<br/>Container<br/><br/>Python/JSON<br/>Runtime state]
            ConfigMgr[Configuration<br/>Manager<br/><br/>Python/YAML<br/>System config]
        end
    end
    
    Discord --> Orchestrator
    WebAPI --> Orchestrator
    Orchestrator --> StateMachine
    Orchestrator --> ResourceMgr
    StateMachine --> AgentFactory
    ResourceMgr --> AgentPool
    AgentFactory --> Security
    AgentPool --> ContextMgr
    ContextMgr --> TokenCalc
    ContextMgr --> Cache
    StateMachine --> ProjectStore
    Orchestrator --> StateStore
    Orchestrator --> ConfigMgr
    
    style Discord fill:#7b68ee,stroke:#483d8b,stroke-width:2px
    style Orchestrator fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    style StateMachine fill:#4dabf7,stroke:#1971c2,stroke-width:2px
    style ContextMgr fill:#51cf66,stroke:#37b24d,stroke-width:2px
```

### Container Responsibilities

#### Interface Layer
- **Discord Bot**: Primary user interface with slash commands and interactive UI
- **REST API**: External system integration endpoints (future)

#### Orchestration Layer
- **Multi-Project Orchestrator**: Coordinates workflows across multiple projects
- **Dual State Machine**: Manages workflow states (Scrum) and TDD states independently
- **Resource Scheduler**: Intelligent agent allocation and priority management

#### Agent Layer
- **Agent Factory**: Creates specialized agents on-demand with proper security
- **Agent Pool Manager**: Manages agent lifecycle and resource optimization
- **Security Controller**: Enforces tool access restrictions per agent type

#### Context Layer
- **Context Manager**: Optimizes cross-agent communication and memory
- **Token Calculator**: Manages context size for efficient AI interactions
- **Context Cache**: High-performance caching for frequently accessed data

#### Data Layer
- **Project Storage**: Persistent file-based storage for project data
- **State Storage**: Runtime state management and recovery
- **Configuration Manager**: YAML-based system and project configuration

## Level 3: Core Components - Orchestration Engine

### Internal Architecture | Component Interactions | State Management | Resource Allocation

Deep dive into the orchestration system components:

```mermaid
graph TB
    subgraph "Orchestration Container"
        subgraph "State Management"
            WSM[Workflow State<br/>Machine<br/><br/>IDLE→BACKLOG→SPRINT]
            TSM[TDD State<br/>Machine<br/><br/>DESIGN→TEST→CODE]
            StateSync[State<br/>Synchronizer<br/><br/>Coordinates machines]
        end
        
        subgraph "Coordination"
            MPO[Multi-Project<br/>Orchestrator<br/><br/>Project routing]
            TaskCoord[Task<br/>Coordinator<br/><br/>Story distribution]
            ConflictRes[Conflict<br/>Resolver<br/><br/>Merge conflicts]
        end
        
        subgraph "Resource Management"
            Scheduler[Resource<br/>Scheduler<br/><br/>CPU/Memory limits]
            PriorityMgr[Priority<br/>Manager<br/><br/>Task prioritization]
            LoadBalance[Load<br/>Balancer<br/><br/>Agent distribution]
        end
        
        subgraph "Monitoring"
            MetricsCol[Metrics<br/>Collector<br/><br/>Performance data]
            HealthCheck[Health<br/>Monitor<br/><br/>System health]
            AlertMgr[Alert<br/>Manager<br/><br/>Error escalation]
        end
    end
    
    WSM --> StateSync
    TSM --> StateSync
    StateSync --> MPO
    MPO --> TaskCoord
    TaskCoord --> ConflictRes
    
    MPO --> Scheduler
    Scheduler --> PriorityMgr
    PriorityMgr --> LoadBalance
    
    TaskCoord --> MetricsCol
    LoadBalance --> HealthCheck
    HealthCheck --> AlertMgr
    
    style WSM fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    style TSM fill:#4dabf7,stroke:#1971c2,stroke-width:2px
    style MPO fill:#51cf66,stroke:#37b24d,stroke-width:2px
    style Scheduler fill:#ffd43b,stroke:#fab005,stroke-width:2px
```

### Component Interactions

#### State Management Components
- **Workflow State Machine**: Manages high-level Scrum workflow states
- **TDD State Machine**: Controls individual story TDD cycles
- **State Synchronizer**: Ensures consistency between state machines

#### Coordination Components
- **Multi-Project Orchestrator**: Routes commands to appropriate projects
- **Task Coordinator**: Distributes stories to parallel TDD cycles
- **Conflict Resolver**: Handles merge conflicts in parallel development

#### Resource Management Components
- **Resource Scheduler**: Allocates CPU/memory based on priorities
- **Priority Manager**: Determines task execution order
- **Load Balancer**: Distributes work across available agents

#### Monitoring Components
- **Metrics Collector**: Gathers performance and progress data
- **Health Monitor**: Tracks system health and agent status
- **Alert Manager**: Escalates issues to human operators

## Level 4: Implementation Details - State Machine Code

### Class Diagrams | Code Structure | Implementation Patterns | Technical Specifications

Detailed view of the state machine implementation:

```mermaid
classDiagram
    class StateMachine {
        -current_state: State
        -transitions: Dict[State, List[Transition]]
        -history: List[StateChange]
        +transition(trigger: str): bool
        +can_transition(trigger: str): bool
        +get_valid_triggers(): List[str]
        +rollback(): bool
    }
    
    class WorkflowStateMachine {
        -project_id: str
        -approval_queue: Queue[Approval]
        +plan_sprint(stories: List[Story]): bool
        +start_sprint(): bool
        +complete_sprint(): bool
        +require_approval(decision: Decision): Approval
    }
    
    class TDDStateMachine {
        -story_id: str
        -current_phase: TDDPhase
        -test_results: TestResults
        +start_design(): bool
        +write_tests(): bool
        +implement_code(): bool
        +refactor(): bool
        +commit(): bool
    }
    
    class State {
        <<enumeration>>
        IDLE
        BACKLOG_READY
        SPRINT_PLANNED
        SPRINT_ACTIVE
        SPRINT_REVIEW
    }
    
    class TDDPhase {
        <<enumeration>>
        DESIGN
        TEST_RED
        CODE_GREEN
        REFACTOR
        COMMIT
    }
    
    class Transition {
        -from_state: State
        -to_state: State
        -trigger: str
        -guard: Callable
        -action: Callable
        +execute(): bool
    }
    
    class StateSync {
        -workflow_sm: WorkflowStateMachine
        -tdd_machines: List[TDDStateMachine]
        +sync_states(): void
        +handle_completion(story_id: str): void
        +handle_failure(story_id: str): void
    }
    
    StateMachine <|-- WorkflowStateMachine
    StateMachine <|-- TDDStateMachine
    StateMachine --> State
    StateMachine --> Transition
    WorkflowStateMachine --> State
    TDDStateMachine --> TDDPhase
    StateSync --> WorkflowStateMachine
    StateSync --> TDDStateMachine
```

### Implementation Details

#### Base State Machine
- **Generic Implementation**: Reusable state machine with history and rollback
- **Transition Guards**: Conditional transitions based on system state
- **Action Hooks**: Execute code during state transitions

#### Workflow State Machine
- **Project Scoped**: Each project has its own workflow instance
- **Approval Queue**: Human approval integration for strategic decisions
- **Sprint Management**: Handles sprint planning and execution lifecycle

#### TDD State Machine
- **Story Scoped**: Each story gets its own TDD instance
- **Phase Tracking**: Enforces proper RED-GREEN-REFACTOR sequence
- **Test Integration**: Validates test results before transitions

#### State Synchronization
- **Bidirectional Sync**: Keeps workflow and TDD states consistent
- **Completion Handling**: Updates workflow when stories complete
- **Failure Recovery**: Handles TDD failures gracefully

## Technology Stack & Architectural Decisions

### Framework Choices | Design Patterns | Trade-offs | Performance Considerations

### Architecture Style: Microkernel + Pipes and Filters

**Decision**: Hybrid architecture combining microkernel for extensibility with pipes and filters for data flow.

**Rationale**:
- **Microkernel**: Core orchestration with pluggable agents
- **Pipes and Filters**: Natural fit for TDD phase transitions
- **Event-Driven**: Asynchronous agent coordination

**Trade-offs**:
- ✅ Highly extensible for new agent types
- ✅ Clear separation of concerns
- ✅ Natural parallelization
- ❌ Additional complexity in state synchronization
- ❌ Potential performance overhead in message passing

### State Management: Dual State Machines

**Decision**: Separate state machines for workflow and TDD cycles.

**Rationale**:
- **Separation**: Different concerns require different state models
- **Parallelization**: Multiple TDD cycles can run independently
- **Clarity**: Each state machine has focused responsibility

**Alternatives Considered**:
1. **Single State Machine**: Too complex with mixed concerns
2. **Hierarchical State Machine**: Unnecessary coupling
3. **Actor Model**: Overkill for current scale

### Agent Architecture: Ephemeral + Factory Pattern

**Decision**: On-demand agent creation with standardized factory.

**Rationale**:
- **Resource Efficiency**: Agents only exist when needed
- **Security**: Fresh environment for each task
- **Scalability**: Easy to scale horizontally

**Performance Characteristics**:
- Agent creation: ~100-200ms
- Memory per agent: ~50-100MB
- Concurrent agents: 10-20 per project

### Data Persistence: File-Based JSON

**Decision**: JSON files in project directories.

**Rationale**:
- **Simplicity**: No database dependencies
- **Version Control**: Data versioned with code
- **Portability**: Easy backup and migration

**Limitations**:
- File locking for concurrent access
- Limited query capabilities
- Manual index management

## Performance and Scaling

### Current Performance Metrics

```mermaid
graph LR
    subgraph "System Capacity"
        Projects[Projects: 1-10]
        Stories[Stories/Sprint: 5-20]
        Agents[Concurrent Agents: 10-50]
        Memory[Memory: 2-8GB]
    end
    
    subgraph "Response Times"
        Command[Command Response: <100ms]
        Agent[Agent Creation: 100-200ms]
        Context[Context Load: 50-500ms]
        Transition[State Transition: <50ms]
    end
    
    subgraph "Throughput"
        TDD[TDD Cycles/Hour: 10-30]
        Commits[Commits/Day: 50-200]
        PRs[PRs/Week: 10-50]
    end
```

### Scaling Strategies

#### Horizontal Scaling
- **Multi-Instance**: Run orchestrators per project group
- **Agent Distribution**: Distribute agents across machines
- **Load Balancing**: Route projects to available instances

#### Vertical Scaling
- **Resource Pools**: Pre-warmed agent pools
- **Context Sharding**: Distribute context across nodes
- **Parallel Execution**: Increase concurrent TDD cycles

### Bottlenecks and Optimizations

#### Identified Bottlenecks
1. **Context Loading**: Large codebases slow context preparation
2. **Agent Creation**: Cold start penalty for new agents
3. **State Synchronization**: Coordination overhead in parallel execution

#### Optimization Strategies
1. **Context Caching**: LRU cache for frequently accessed context
2. **Agent Pooling**: Pre-create agents for common tasks
3. **Async Operations**: Non-blocking state updates

## Integration Architecture

### API Surface

```mermaid
graph TB
    subgraph "External APIs"
        subgraph "Discord Integration"
            SlashCmd[Slash Commands<br/>/epic, /sprint, /tdd]
            Interactive[Interactive UI<br/>Buttons & Modals]
            Webhooks[Event Webhooks<br/>State updates]
        end
        
        subgraph "REST API"
            Projects[/api/projects<br/>Project management]
            Status[/api/status<br/>System status]
            Metrics[/api/metrics<br/>Performance data]
        end
        
        subgraph "WebSocket"
            StateStream[/ws/state<br/>Real-time state]
            LogStream[/ws/logs<br/>Live logs]
            MetricStream[/ws/metrics<br/>Live metrics]
        end
    end
    
    subgraph "Internal APIs"
        AgentAPI[Agent API<br/>standardized interface]
        StorageAPI[Storage API<br/>data persistence]
        ContextAPI[Context API<br/>memory management]
    end
    
    SlashCmd --> AgentAPI
    Projects --> StorageAPI
    StateStream --> ContextAPI
    
    style SlashCmd fill:#7b68ee,stroke:#483d8b,stroke-width:2px
    style Projects fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    style StateStream fill:#4dabf7,stroke:#1971c2,stroke-width:2px
```

### Plugin Architecture

The system supports extensibility through plugins:

```mermaid
classDiagram
    class Plugin {
        <<interface>>
        +name: str
        +version: str
        +initialize(): void
        +shutdown(): void
    }
    
    class AgentPlugin {
        <<interface>>
        +agent_type: str
        +create_agent(): BaseAgent
        +get_capabilities(): List[str]
    }
    
    class StoragePlugin {
        <<interface>>
        +storage_type: str
        +save(data: Any): void
        +load(key: str): Any
    }
    
    class IntegrationPlugin {
        <<interface>>
        +service_name: str
        +connect(): void
        +disconnect(): void
    }
    
    class PluginManager {
        -plugins: Dict[str, Plugin]
        +register(plugin: Plugin): void
        +unregister(name: str): void
        +get_plugin(name: str): Plugin
        +list_plugins(): List[str]
    }
    
    Plugin <|-- AgentPlugin
    Plugin <|-- StoragePlugin
    Plugin <|-- IntegrationPlugin
    PluginManager --> Plugin
```

### Extension Points

1. **Custom Agents**: Implement new agent types for specialized tasks
2. **Storage Backends**: Add database or cloud storage options
3. **Integration Services**: Connect to Jira, Slack, Teams, etc.
4. **Metrics Exporters**: Export metrics to monitoring systems (basic Prometheus format available)
5. **Security Providers**: Custom authentication and authorization

## Security Architecture

### Defense in Depth

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Layer 1: Authentication"
            Discord[Discord OAuth<br/>User identity]
            API[API Keys<br/>Service auth]
        end
        
        subgraph "Layer 2: Authorization"
            RBAC[Role-Based<br/>Access Control]
            ProjectACL[Project<br/>Access Lists]
        end
        
        subgraph "Layer 3: Agent Security"
            ToolRestrict[Tool<br/>Restrictions]
            Sandbox[Execution<br/>Sandbox]
        end
        
        subgraph "Layer 4: Audit"
            ActionLog[Action<br/>Logging]
            Compliance[Compliance<br/>Reports]
        end
    end
    
    Discord --> RBAC
    API --> RBAC
    RBAC --> ProjectACL
    ProjectACL --> ToolRestrict
    ToolRestrict --> Sandbox
    Sandbox --> ActionLog
    ActionLog --> Compliance
    
    style Discord fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    style ToolRestrict fill:#4dabf7,stroke:#1971c2,stroke-width:2px
    style ActionLog fill:#51cf66,stroke:#37b24d,stroke-width:2px
```

### Agent Security Profiles

Detailed security boundaries per agent type:

| Agent Type | File Access | Git Operations | System Commands | Network | Build Tools |
|------------|------------|----------------|-----------------|---------|-------------|
| Orchestrator | Full | All | Limited | Yes | Yes |
| Design | Read-only | None | None | Yes | No |
| Code | Read/Write | Add/Commit | Limited | No | Yes |
| QA | Read/Write | None | Test only | No | Yes |
| Data | Read-only | None | Analysis | Yes | No |

### Security Implementation

```python
# Example: Agent security enforcement
class SecurityController:
    def get_agent_restrictions(self, agent_type: str) -> Dict[str, List[str]]:
        """Return tool restrictions for agent type"""
        profiles = {
            "orchestrator": {
                "allowed": ["*"],
                "blocked": ["rm -rf", "sudo", "format"]
            },
            "code": {
                "allowed": ["edit", "write", "git add", "git commit"],
                "blocked": ["rm", "git push", "sudo"]
            },
            "design": {
                "allowed": ["read", "web_search"],
                "blocked": ["edit", "write", "git", "rm"]
            }
        }
        return profiles.get(agent_type, {"allowed": [], "blocked": ["*"]})
```

## Deployment Architecture

### Deployment Options

```mermaid
graph TB
    subgraph "Development"
        LocalDev[Local Machine<br/>Single developer]
        DevBot[Dev Discord Bot<br/>Test server]
    end
    
    subgraph "Team Deployment"
        SharedVM[Shared VM<br/>Team access]
        TeamBot[Team Discord Bot<br/>Private server]
        SharedFS[Shared Storage<br/>Project data]
    end
    
    subgraph "Production"
        Container[Container Cluster<br/>Kubernetes/Docker]
        ProdBot[Production Bot<br/>Organization server]
        CloudStore[Cloud Storage<br/>S3/GCS]
        Monitoring[Monitoring Stack<br/>Prometheus/Grafana]
    end
    
    LocalDev --> SharedVM
    SharedVM --> Container
    DevBot --> TeamBot
    TeamBot --> ProdBot
    SharedFS --> CloudStore
    
    style LocalDev fill:#95e1d3,stroke:#3aa68b,stroke-width:2px
    style SharedVM fill:#f38181,stroke:#c44569,stroke-width:2px
    style Container fill:#4ecdc4,stroke:#2d6e6e,stroke-width:2px
```

### Container Architecture

```yaml
# Example: Docker Compose deployment
version: '3.8'
services:
  orchestrator:
    image: agent-workflow:latest
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    volumes:
      - ./projects:/projects
      - ./config:/config
    depends_on:
      - redis
      
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
      
  monitoring:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
volumes:
  redis_data:
```

## Enhanced Components (Recent Additions)

The system has been enhanced with modern components that provide improved performance, flexibility, and monitoring capabilities:

### Context Management Enhancement
- **Context Manager Factory** (`lib/context_manager_factory.py`): Dynamic context manager selection based on system state and configuration
  - Factory pattern for creating appropriate context managers
  - Supports switching between full and simple context management modes
  - Optimizes resource usage based on agent interface type
  - Thread-safe initialization and configuration management

- **Simple Context Manager** (`lib/simple_context_manager.py`): Performance-optimized implementation for high-frequency interactions
  - Lightweight context management for mock/demo scenarios
  - Async-first design with token budget management
  - Minimal memory footprint with fast context resolution
  - Specialized for scenarios requiring rapid agent interactions

### Agent Interface Management
- **Agent Interface Management** (`tools/visualizer/agent_interfaces.py`): Multi-interface support for different agent backends
  - Claude Code Interface (default integration)
  - Anthropic API Interface (direct API key usage)
  - Mock Interface (testing and demonstration)
  - Automatic interface detection and graceful fallback
  - Standardized agent communication protocols

### Real-Time Broadcasting
- **State Broadcasting** (`lib/state_broadcaster.py`): WebSocket-based real-time state updates
  - Live state machine transition broadcasting
  - Multi-client WebSocket support with connection management
  - Real-time workflow and TDD state visualization
  - Event-driven architecture for instant updates
  - Integration with web-based monitoring dashboards

### Background Processing & Monitoring
- **Context Monitoring** (`lib/context_monitoring.py`): Advanced context performance monitoring
  - Real-time metrics collection and alerting
  - Performance analytics and bottleneck detection
  - Comprehensive context usage tracking
  - Automatic performance optimization recommendations

- **Multi-Project Monitoring** (`lib/multi_project_monitoring.py`): Enterprise-scale observability
  - Cross-project metrics aggregation and analysis
  - Real-time dashboard integration
  - Automated alerting and notification systems
  - Historical performance trending and analytics

- **Context Background Processing** (`lib/context_background.py`): Async background operations
  - Background context indexing and cache warming
  - Pattern discovery and context optimization
  - Maintenance task scheduling and execution
  - Async processing queue management

## Summary

The AI Agent TDD-Scrum Workflow system implements a sophisticated architecture that:

1. **Separates Concerns**: Clear boundaries between orchestration, agents, and data
2. **Scales Efficiently**: Handles multiple projects and parallel execution
3. **Maintains Security**: Multi-layered security with agent restrictions
4. **Enables Extension**: Plugin architecture for customization
5. **Supports Teams**: From solo developers to large organizations
6. **Provides Flexibility**: Dynamic context management and multiple agent interfaces
7. **Offers Real-Time Insights**: Live state broadcasting and comprehensive monitoring

The architecture prioritizes clarity, security, and extensibility while maintaining performance for practical software development workflows.