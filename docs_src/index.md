# 🤖 AI Agent TDD-Scrum Workflow - Complete Guide

> **AI-powered development framework with Discord integration, automated testing, and human-in-the-loop control for software projects**

A comprehensive **AI agent development framework** with **Human-In-The-Loop (HITL)** orchestration that coordinates multiple specialized AI agents through a Discord interface, following a research-mode Scrum methodology optimized for solo engineers working with AI assistance.

!!! success "What You Get"
    **Complete AI-powered development team** that handles design, testing, implementation, and quality assurance while keeping you in control of strategic decisions.

## System Overview - How It Works

### AI Agent Orchestration | Test-Driven Development | Scrum Workflow | Discord Integration

This system implements a sophisticated dual state machine architecture for AI-assisted software development with integrated Test-Driven Development and human oversight. It coordinates multiple TDD cycles in parallel while maintaining proper Scrum methodology, optimized for solo engineers working with AI assistance.

## Simple Workflow - From Idea to Code

### Step-by-Step Process | User Interaction | AI Collaboration | Code Generation

```mermaid
flowchart LR
    You["👨‍💻<br/>YOU"] 
    Chat["💬<br/>Discord<br/>Chat"]
    AI["🤖<br/>AI Team<br/>Helper"]
    Code["📝<br/>Your<br/>Project"]
    
    You -->|"Tell it what to build"| Chat
    Chat -->|"Coordinates"| AI
    AI -->|"Builds & tests"| Code
    Code -->|"Shows you progress"| You
    
    style You fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Chat fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style AI fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style Code fill:#fff3e0,stroke:#f57c00,stroke-width:2px
```

**The Big Picture:** You tell the system what you want to build through simple Discord messages. A team of AI agents collaborates to design, code, test, and improve your project while keeping you in control of every major decision.

---

### Complete System Architecture | Technical Design | Component Overview


```mermaid
graph TB
    subgraph "👤 Solo Engineer"
        User[User]
    end
    
    subgraph DISCORD ["🎮 Discord Interface"]
        Discord["/epic /sprint /approve<br/>Slash Commands"]
        State[Interactive State<br/>Visualization]
    end
    
    subgraph WORKFLOW ["🤖 TDD-Scrum Workflow System"]
        subgraph "🎛️ Control Layer"
            SM[Workflow State Machine<br/>IDLE - BACKLOG - SPRINT]
            HITL[Approval Gates<br/>Strategic Decisions]
            PM[Persistent Storage<br/>Epics - Stories - Tasks]
        end
        
        subgraph "🎭 Ephemeral Agents"
            Orch[🎭 Orchestrator Agent<br/>Scrum Master<br/>spun up on demand]
        end
        
        subgraph "🔄 TDD Execution Layer"
            TDD[TDD State Machine<br/>DESIGN - TEST - CODE - REFACTOR]
            Design[🎨 Design Agent<br/>Architecture and Specs]
            QA[🧪 Test Agent<br/>Write Tests First]
            Code[💻 Code Agent<br/>Make Tests Pass]
            Data[📊 Analytics Agent<br/>Metrics and Coverage]
        end
    end
    
    subgraph PROJECT ["💾 Your Project 1 to n"]
        Tests[🧪 Test Suite<br/>RED - GREEN - REFACTOR]
        Repo[📁 Git Repository<br/>Code & Documentation]
    end
    
    User -->|"Commands"| Discord
    Discord <-->|"Validates"| SM
    Discord -->|"Updates"| State
    State -->|"Progress"| User
    
    SM -->|"Spins up"| Orch
    Orch -->|"Decisions"| SM
    SM <-->|"Enforces"| HITL
    SM <-->|"Reads/Writes"| PM
    
    Orch -->|"Plans Sprint"| PM
    PM -->|"Assigns Story"| TDD
    TDD -->|"1 Design"| Design
    Design -->|"Specs"| TDD
    TDD -->|"2 Test"| QA
    QA -->|"Tests"| Tests
    TDD -->|"3 Code"| Code
    Code <-->|"TDD Cycle"| Tests
    TDD -->|"4 Analyze"| Data
    Data -->|"Metrics"| TDD
    
    TDD -->|"Story Complete"| SM
    HITL <-->|"Approvals"| Discord
    
    Code -->|"Commits"| Repo
    Tests -->|"Validates"| Repo
    
    style User fill:#e1f5fe,stroke:#0277bd,stroke-width:3px
    style DISCORD fill:#f8f4ff,stroke:#7b1fa2,stroke-width:3px
    style WORKFLOW fill:#f0f8f0,stroke:#388e3c,stroke-width:3px
    style PROJECT fill:#fff8e1,stroke:#f57c00,stroke-width:3px
    style Discord fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style State fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style SM fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px
    style PM fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style HITL fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Orch fill:#ffd43b,stroke:#fab005,stroke-width:3px
    style TDD fill:#4dabf7,stroke:#1971c2,stroke-width:3px
    style Design fill:#f1f8e9,stroke:#388e3c,stroke-width:2px
    style QA fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    style Code fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style Data fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style Tests fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    style Repo fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
```

## 🎯 Key Features

### 🏗️ Core Architecture
=== "Dual State Machine"
    **Primary workflow coordination with secondary TDD state machines**
    
    - Scrum workflow orchestration (IDLE → BACKLOG → SPRINT → REVIEW)
    - Parallel TDD cycles (DESIGN → TEST → CODE → REFACTOR → COMMIT)
    - Intelligent state transitions and error recovery

=== "Ephemeral Agents"
    **On-demand agent creation and coordination for optimal resource utilization**
    
    - Design agents for technical specifications
    - QA agents for comprehensive testing
    - Code agents for implementation and refactoring
    - Analytics agents for performance monitoring

=== "Context Management"
    **Intelligent agent communication with optimized context sharing**
    
    - Memory-efficient context compression
    - Cross-agent knowledge sharing
    - Token optimization for large codebases

### 🌐 Multi-Project Orchestration
=== "Resource Management"
    **Intelligent allocation of CPU, memory, and agents across projects**
    
    - Priority-based scheduling
    - Dynamic resource allocation
    - Performance monitoring and optimization

=== "Cross-Project Intelligence"
    **Pattern recognition and knowledge sharing between projects**
    
    - Best practice identification
    - Anti-pattern detection
    - Knowledge transfer recommendations

=== "Security Isolation"
    **Project-level security boundaries and access control**
    
    - Agent access restrictions
    - Data isolation between projects
    - Audit logging and compliance

### 💬 Human-In-The-Loop Interface
=== "Discord Integration"
    **Complete HITL interface with TDD-aware slash commands**
    
    - Interactive state visualization
    - Real-time progress monitoring
    - Approval gates for strategic decisions

=== "Real-time Monitoring"
    **Live visibility into all TDD cycles with WebSocket updates**
    
    - Multi-project dashboard
    - Performance metrics
    - Error escalation and alerts

### 🧪 Quality & Testing
=== "TDD Enforcement"
    **Strict RED-GREEN-REFACTOR cycle implementation**
    
    - Automated test creation
    - Minimal implementation approach
    - Quality-focused refactoring

=== "Comprehensive Testing"
    **Unit, integration, and E2E test coverage**
    
    - >90% code coverage target
    - Performance benchmarking
    - Security validation

## 🚀 Quick Start

Get up and running in minutes:

!!! example "Installation"
    ```bash
    # Clone and install
    git clone https://github.com/jmontp/agent-workflow.git
    cd agent-workflow
    make install

    # Configure
    export DISCORD_BOT_TOKEN="your_token_here"

    # Run
    make run
    ```

!!! tip "Next Steps"
    Once running, try these commands in Discord:
    
    - `/epic "Build authentication system"` - Define your first epic
    - `/sprint plan` - Plan your first sprint
    - `/state` - View interactive system state

[**→ Complete Installation Guide**](getting-started/installation.md) | [**→ Quick Start Tutorial**](getting-started/quick-start.md)

## Dual State Machine Workflow

The system operates two coordinated state machines for complete TDD-Scrum integration:

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> BACKLOG_READY : /epic
    BACKLOG_READY --> SPRINT_PLANNED : /sprint plan
    SPRINT_PLANNED --> SPRINT_ACTIVE : /sprint start
    SPRINT_ACTIVE --> SPRINT_REVIEW : tasks complete
    SPRINT_REVIEW --> IDLE : /feedback
    SPRINT_ACTIVE --> SPRINT_PAUSED : /sprint pause
    SPRINT_PAUSED --> SPRINT_ACTIVE : /sprint resume
    SPRINT_ACTIVE --> BLOCKED : CI fails 3×
    BLOCKED --> SPRINT_ACTIVE : /suggest_fix
```

### TDD State Machine (Per Story)

```mermaid
stateDiagram-v2
    [*] --> DESIGN
    DESIGN --> TEST_RED : specs complete
    TEST_RED --> CODE_GREEN : tests failing
    CODE_GREEN --> REFACTOR : tests passing
    REFACTOR --> COMMIT : quality gates met
    COMMIT --> [*] : story complete
    
    REFACTOR --> CODE_GREEN : tests broken
    CODE_GREEN --> TEST_RED : need more tests
    TEST_RED --> DESIGN : requirements unclear
```

**Key TDD Commands:**
- `/tdd overview` - Monitor all active TDD cycles
- `/tdd status AUTH-1` - Check specific story progress
- `/tdd review_cycle AUTH-1` - Request human review
- `/tdd metrics` - View TDD performance data

[**→ Complete State Machine Reference**](user-guide/state-machine.md) | [**→ TDD Workflow Guide**](user-guide/tdd-workflow.md)

## Ephemeral AI Agent System

Specialized agents are created on-demand for optimal resource utilization:

### Orchestrator Agent (Temporary)
- Sprint coordination and multi-task management
- Spun up during SPRINT_ACTIVE state
- Manages parallel TDD cycle execution
- Handles cross-story dependencies and coordination

### Design Agents (Per Story)
- Technical specifications for individual stories
- Created during TDD DESIGN phase
- Architecture decisions and interface definitions
- Destroyed after design phase completion

### QA Agents (Per TDD Cycle)
- Test suite creation following TDD methodology
- Active during TEST_RED phase
- Comprehensive test coverage for story requirements
- Ensures proper failing tests before implementation

### Code Agents (Per TDD Cycle)
- Implementation during CODE_GREEN and REFACTOR phases
- Makes tests pass with minimal implementation
- Applies refactoring while maintaining green tests
- Handles version control and final commits

### Analytics Agent (Persistent)
- Cross-story metrics and performance analysis
- TDD cycle time tracking and optimization
- Sprint progress reporting and forecasting
- Continuous process improvement insights

[**→ Agent Capabilities Reference**](concepts/overview.md)

## ⚡ Essential Commands

Master these key slash commands for dual state machine control:

### 📋 Workflow Commands
| Command | Purpose | Example |
|---------|---------|---------|
| **`/epic`** | Define high-level initiatives | `/epic "Build authentication system"` |
| **`/sprint plan`** | Plan sprint with stories | `/sprint plan AUTH-1 AUTH-2` |
| **`/sprint start`** | Begin sprint execution (creates TDD cycles) | `/sprint start` |
| **`/approve`** | Approve pending tasks | `/approve AUTH-1 AUTH-2` |
| **`/state`** | Interactive state inspection | `/state` |

### 🧪 TDD Commands
| Command | Purpose | Example |
|---------|---------|---------|
| **`/tdd overview`** | Monitor all TDD cycles | `/tdd overview` |
| **`/tdd status`** | Check specific story progress | `/tdd status AUTH-1` |
| **`/tdd review_cycle`** | Request human review | `/tdd review_cycle AUTH-1` |
| **`/tdd metrics`** | View TDD performance data | `/tdd metrics` |
| **`/tdd pause/resume`** | Control TDD cycle execution | `/tdd pause AUTH-1` |

!!! info "Command Discovery"
    Use `/state` in Discord to see all available commands for your current workflow state.

[**→ Complete Command Reference**](user-guide/hitl-commands.md)

## Architecture

The system uses a clean layered architecture:

- **Scripts Layer**: Executable orchestrator entry points
- **Library Layer**: Core business logic and agents
- **Interface Layer**: Discord bot and external integrations
- **Data Layer**: State persistence and configuration

[**→ Detailed Architecture Documentation**](concepts/overview.md)

## Testing & Quality

Comprehensive testing strategy ensures reliability:

- **Unit Tests**: State machine validation and component testing
- **Integration Tests**: Orchestrator workflows and agent coordination  
- **E2E Tests**: Complete user scenarios and error handling
- **Coverage Target**: >90% code coverage with automated reporting

[**→ Testing Strategy & Implementation**](advanced/testing.md)

## Contributing

We welcome contributions! The system is designed for extensibility:

1. **Fork** the repository
2. **Create** a feature branch
3. **Implement** with tests
4. **Submit** a pull request

[**→ Contributing Guidelines**](user-guide/faq.md)

## 📚 Documentation Sections

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Getting Started**

    ---
    
    Installation, setup, and first workflow examples
    
    [:octicons-arrow-right-24: Quick Start](getting-started/quick-start.md)

-   :material-console:{ .lg .middle } **User Guide**

    ---
    
    Commands, workflows, and daily usage patterns
    
    [:octicons-arrow-right-24: Commands](user-guide/hitl-commands.md)

-   :material-test-tube:{ .lg .middle } **TDD Workflow**

    ---
    
    Complete TDD cycle management and monitoring
    
    [:octicons-arrow-right-24: TDD Guide](user-guide/tdd-workflow.md)

-   :material-sitemap:{ .lg .middle } **Architecture**

    ---
    
    Dual state machine system design and coordination
    
    [:octicons-arrow-right-24: Overview](architecture/overview.md)

-   :material-brain:{ .lg .middle } **Context Management**

    ---
    
    Intelligent agent communication and optimization
    
    [:octicons-arrow-right-24: Context System](architecture/context-management-system.md)

-   :material-security:{ .lg .middle } **Security & Deployment**

    ---
    
    Multi-project security and production setup
    
    [:octicons-arrow-right-24: Security](advanced/security-implementation.md)

</div>

### 🔍 Quick Reference

| Topic | Best For | Documentation |
|-------|----------|---------------|
| **First Time Users** | Getting started quickly | [Installation](getting-started/installation.md) → [Quick Start](getting-started/quick-start.md) |
| **Daily Usage** | Command reference and workflows | [HITL Commands](user-guide/hitl-commands.md) → [State Machine](user-guide/state-machine.md) |
| **Multi-Project** | Managing multiple codebases | [Multi-Project Guide](user-guide/multi-project-orchestration.md) |
| **Technical Deep-Dive** | Understanding the system | [Architecture](architecture/overview.md) → [Advanced](advanced/architecture-detailed.md) |
| **Troubleshooting** | Fixing issues | [Troubleshooting](user-guide/troubleshooting.md) → [FAQ](user-guide/faq.md) |

---

!!! tip "Getting Help"
    - Check the [**Command Reference**](user-guide/hitl-commands.md) for syntax
    - Use `/state` in Discord to see available commands
    - Review [**Common Workflows**](user-guide/workflow-sequences.md) for examples
    - See [**Troubleshooting**](user-guide/troubleshooting.md) for issues