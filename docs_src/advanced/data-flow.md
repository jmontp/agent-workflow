# Data Flow Architecture

This document describes how data flows between the orchestration repository and project repositories in the two-repository model, including the Test-Driven Development workflow and test preservation patterns.

## Overview

The AI Agent TDD-Scrum workflow system operates on a clear separation between:
- **Orchestration Repository**: Central framework, coordination, and dual state machine management
- **Project Repositories**: Individual codebases with embedded project management data and TDD state

The system implements dual data flows:
- **Workflow Data Flow**: Project-level state and management data
- **TDD Data Flow**: Story-level TDD cycles, test files, and test preservation

## Data Flow Patterns

### 4. TDD Cycle Initialization Flow

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant TSM as TDD SM
    participant DA as Design Agent
    participant P as Project Repo
    participant TDD as TDD Storage

    Note over O,P: Sprint starts, TDD cycles created
    O->>TSM: Create TDD cycle for story AUTH-1
    TSM->>TDD: Initialize cycle data
    TDD->>TDD: Create cycle-{id}.json
    TSM->>P: Create TDD test directory
    P->>P: mkdir tests/tdd/AUTH-1/
    
    Note over TSM,DA: DESIGN phase begins
    TSM->>DA: Start design phase
    DA->>P: Read story requirements
    P->>DA: Return story data
    DA->>DA: Create technical specifications
    DA->>TDD: Store design artifacts
    TDD->>TDD: Update cycle with design notes
    DA->>TSM: Design phase complete
    TSM->>TSM: Transition to TEST_RED
```

### 5. Test Preservation Workflow

```mermaid
sequenceDiagram
    participant QA as QA Agent
    participant CA as Code Agent
    participant P as Project Repo
    participant TDD as TDD Storage
    participant CI as CI System

    Note over QA,P: TEST_RED phase - create failing tests
    QA->>P: Create test files in tests/tdd/AUTH-1/
    P->>P: Write test_login.py (failing)
    QA->>P: Run tests to confirm failures
    P->>QA: Test results (RED)
    QA->>TDD: Store test results
    QA->>P: Git commit failing tests
    P->>P: Commit tests to repository
    
    Note over CA,P: CODE_GREEN phase - implement minimal code
    CA->>P: Read committed test files
    P->>CA: Return test requirements
    CA->>P: Implement minimal code in src/
    CA->>P: Run tests to verify GREEN
    P->>CA: Test results (GREEN)
    CA->>TDD: Store passing test results
    CA->>P: Git commit implementation
    
    Note over CA,CI: REFACTOR phase - improve while preserving tests
    CA->>P: Refactor code quality
    CA->>P: Run tests to ensure still GREEN
    P->>CA: Test results (GREEN)
    CA->>P: Git commit refactored code
    P->>CI: Trigger CI pipeline
    CI->>P: Run full test suite
    CI->>TDD: Store CI results
```

### 6. Test File Lifecycle Management

```mermaid
sequenceDiagram
    participant TSM as TDD SM
    participant TFM as Test File Manager
    participant P as Project Repo
    participant TDD as TDD Storage

    Note over TSM,P: Test file creation in TDD directory
    TSM->>TFM: Create test file for story
    TFM->>P: tests/tdd/AUTH-1/test_login.py
    TFM->>TDD: Track file in TestFile object
    TDD->>TDD: Store file metadata
    
    Note over TFM,P: Test file preservation through phases
    TFM->>P: Git commit (TEST_RED → CODE_GREEN)
    TFM->>TDD: Update file status to COMMITTED
    TFM->>P: Validate tests remain (CODE_GREEN → REFACTOR)
    TFM->>TDD: Update file status to PASSING
    
    Note over TFM,P: Test file promotion to permanent location
    TFM->>P: Copy to tests/unit/test_login.py
    TFM->>TDD: Update file status to INTEGRATED
    TFM->>P: Update CI configuration
    TFM->>P: Git commit final test integration
```

### 1. Project Registration Flow

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord Bot
    participant O as Orchestrator
    participant P as Project Repo
    participant G as Git

    U->>D: /project register <path>
    D->>D: Validate path exists
    D->>D: Check if git repository
    D->>D: Verify no existing channel
    D->>P: Initialize .orch-state/
    P->>P: Create directory structure
    P->>P: Create template files
    D->>D: Create Discord channel
    D->>O: Register project
    O->>O: Add to project registry
    D->>U: Registration complete
```

### 2. Command Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord Bot
    participant O as Orchestrator
    participant SM as State Machine
    participant A as Agent
    participant P as Project Repo

    U->>D: /epic "New feature"
    D->>O: Route command to project
    O->>SM: Validate against state
    SM->>O: Command allowed
    O->>A: Create epic task
    A->>P: Read current backlog.json
    P->>A: Return project data
    A->>A: Create epic object
    A->>P: Write updated backlog.json
    A->>O: Task complete
    O->>D: Success response
    D->>U: Epic created notification
```

### 3. Sprint Management with TDD Integration Flow

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord Bot
    participant O as Orchestrator
    participant WSM as Workflow SM
    participant TSM as TDD SM
    participant P as Project Repo

    U->>D: /sprint plan
    D->>O: Route to project
    O->>WSM: Validate sprint planning
    WSM->>O: Planning allowed
    O->>P: Read backlog.json
    P->>O: Return stories
    O->>P: Create sprint in sprints/
    P->>P: Write sprint-xxx.json
    O->>P: Update story assignments
    P->>P: Update backlog.json
    
    Note over O,TSM: Sprint start triggers TDD cycles
    U->>D: /sprint start
    D->>O: Start sprint
    O->>WSM: Transition to SPRINT_ACTIVE
    loop For each story in sprint
        O->>TSM: Create TDD cycle
        TSM->>P: Create TDD state in .orch-state/tdd/
        P->>P: Initialize story TDD directory
    end
    
    O->>D: Sprint and TDD cycles active
    D->>U: Show sprint and TDD status
```

## Data Storage Patterns

### Orchestration Repository
```
agent-workflow/
├── lib/
│   ├── agents/              # Agent definitions (global)
│   ├── state_machine.py     # Workflow states (global)
│   ├── discord_bot.py       # Interface (global)
│   └── agent_tool_config.py # Security policies (global)
├── scripts/
│   └── orchestrator.py      # Coordination engine (global)
└── docs_src/               # Framework documentation (global)
```

### Project Repository
```
project-repo/
├── src/                    # Project code (project-specific)
├── tests/                  # Project tests (project-specific)
│   ├── unit/              # Permanent unit tests
│   ├── integration/       # Permanent integration tests
│   └── tdd/               # TDD working directory
│       └── {story-id}/    # Per-story TDD tests
├── .orch-state/           # Workflow data (project-specific)
│   ├── backlog.json       # Project management data
│   ├── sprints/           # Sprint history
│   ├── tdd/               # TDD state storage
│   │   ├── cycles/        # TDD cycle data
│   │   └── test-results/  # Test execution results
│   ├── architecture.md    # Project architecture decisions
│   ├── best-practices.md  # Project conventions
│   └── status.json        # Current workflow state
└── .git/                  # Version control (project-specific)
```

## Read/Write Access Patterns

### Read Operations
- **Orchestrator → Project**: Reads workflow state, backlog, and configuration
- **TDD State Machine → Project**: Reads TDD cycles, test results, and coverage
- **Discord Bot → Project**: Displays current workflow and TDD status
- **Agents → Project**: Access context for both workflow and TDD decision making
- **Test File Manager → Project**: Reads test files and execution results

### Write Operations
- **Orchestrator → Project**: Updates workflow state and project data
- **TDD State Machine → Project**: Updates TDD cycle state and test data
- **Agents → Project**: Persist workflow task results and TDD artifacts
- **Discord Commands → Project**: Modify backlogs, sprints, and TDD cycles
- **Test Preservation → Project**: Commit and promote test files

### Security Boundaries
- **No Cross-Project Access**: Agents cannot read other project data or TDD cycles
- **Limited Write Scope**: Only `.orch-state/` and `tests/tdd/` directories writable
- **TDD Isolation**: TDD cycles isolated per story to prevent test contamination
- **Git Permissions**: Standard repository access controls apply to both workflow and test data

## State Synchronization

### Dual State Machine Coordination

```mermaid
stateDiagram-v2
    [*] --> IDLE
    
    state "Workflow States" as WF {
        IDLE --> BACKLOG_READY: /epic
        BACKLOG_READY --> SPRINT_PLANNED: /sprint plan
        SPRINT_PLANNED --> SPRINT_ACTIVE: /sprint start
        SPRINT_ACTIVE --> SPRINT_REVIEW: /sprint status
        SPRINT_REVIEW --> IDLE: /feedback
    }
    
    state "TDD States (Per Story)" as TDD {
        [*] --> DESIGN
        DESIGN --> TEST_RED: /tdd test
        TEST_RED --> CODE_GREEN: /tdd commit-tests
        CODE_GREEN --> REFACTOR: /tdd commit-code
        REFACTOR --> COMMIT: /tdd commit-refactor
        COMMIT --> [*]
    }
    
    SPRINT_ACTIVE --> TDD: Story TDD cycles
    TDD --> SPRINT_REVIEW: All stories complete
    
    note right of WF
        Workflow state stored in
        .orch-state/status.json
    end note
    
    note right of TDD
        TDD state stored in
        .orch-state/tdd/cycles/
    end note
```

### Multi-Project Coordination
- **Independent Dual States**: Each project has own workflow and TDD state machines
- **Parallel Execution**: Multiple projects and TDD cycles can be active simultaneously
- **Resource Sharing**: Agents allocated per project and TDD phase needs
- **Conflict Prevention**: Discord channels provide isolation for both workflow and TDD commands
- **TDD Isolation**: TDD cycles per story prevent cross-story test contamination

## Data Consistency

### Eventual Consistency Model
- **Local Consistency**: Each project maintains internal consistency for both workflow and TDD data
- **Dual State Consistency**: Workflow and TDD state machines maintain synchronized state
- **Global Coordination**: Orchestrator ensures cross-project resource allocation and TDD cycle coordination
- **Conflict Resolution**: Manual intervention for complex workflow and TDD scenarios

### Transaction Boundaries
- **Single Project**: ACID properties maintained within project for both workflow and TDD data
- **Cross Project**: No transactions spanning projects or TDD cycles
- **TDD Atomicity**: TDD phase transitions are atomic within a story
- **Rollback Strategy**: Git provides rollback capabilities for both code and test artifacts

### Backup and Recovery
- **Git History**: Complete audit trail of all workflow and TDD changes
- **State Recovery**: Projects can be restored from any git commit including TDD state
- **Test Preservation**: TDD test artifacts preserved through git history
- **Disaster Recovery**: Projects portable between orchestration instances with full TDD history

## Performance Considerations

### Read Performance
- **Local Access**: Project and TDD data accessed directly from filesystem
- **Caching Strategy**: Orchestrator caches frequently accessed workflow and TDD state
- **Lazy Loading**: Project and TDD data loaded on-demand
- **TDD State Optimization**: TDD cycles loaded only when stories are active

### Write Performance
- **Batched Writes**: Multiple workflow and TDD changes combined into single commits
- **Asynchronous Operations**: Non-blocking writes to project repositories and TDD storage
- **Conflict Avoidance**: Structured data minimizes merge conflicts for both workflow and TDD data
- **Test File Efficiency**: Test files written incrementally during TDD phases

### Scalability
- **Horizontal Scaling**: Add projects and TDD cycles without affecting others
- **Resource Isolation**: Per-project and per-story resource allocation
- **Network Efficiency**: Local filesystem access minimizes I/O for both workflow and test data
- **TDD Parallelization**: Multiple TDD cycles can run simultaneously across stories

## Monitoring and Observability

### Data Flow Metrics
- **Command Latency**: Time from Discord to project and TDD updates
- **State Transition Frequency**: Workflow and TDD progression rates
- **Error Rates**: Failed operations per project and TDD cycle
- **TDD Cycle Metrics**: Time spent in each TDD phase, test coverage progression
- **Test Preservation Success**: Rate of successful test file lifecycle management

### Audit Trail
- **Git History**: All workflow and TDD changes tracked in version control
- **Discord Logs**: Command execution history for both workflow and TDD commands
- **Agent Logs**: Detailed task execution traces including TDD phase transitions
- **TDD Logs**: Test creation, execution, and preservation activities
- **Test Result History**: Complete test execution timeline and results

### Health Checks
- **Project Repository**: Git status and filesystem health for both workflow and test data
- **Data Integrity**: JSON schema validation for workflow and TDD state
- **State Consistency**: Dual state machine validation and synchronization
- **Test File Integrity**: Verification of test file preservation and promotion
- **TDD Cycle Health**: Detection of stuck TDD cycles and automated recovery