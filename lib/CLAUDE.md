# lib/ Directory Documentation

This document provides comprehensive documentation for the `lib/` directory, which contains the core library components of the AI Agent TDD-Scrum workflow system.

## Overview

The `lib/` directory contains 42+ Python modules organized into a sophisticated orchestration framework that coordinates multiple specialized AI agents through a Discord interface, following a research-mode Scrum methodology optimized for solo engineers working with AI assistance.

## Directory Structure

```
lib/
├── agents/                    # Specialized AI agent implementations
│   ├── __init__.py           # Base agent framework and registry
│   ├── design_agent.py       # Architecture and design agent
│   ├── code_agent.py         # Implementation agent
│   ├── qa_agent.py           # Quality assurance and testing agent
│   ├── data_agent.py         # Data analysis agent
│   └── mock_agent.py         # Mock agents for testing
├── context/                   # Context management system
│   ├── __init__.py           # Context management interfaces
│   ├── models.py             # Context data models
│   ├── interfaces.py         # Abstract interfaces
│   ├── manager.py            # Context manager implementation
│   └── exceptions.py         # Context-specific exceptions
├── agent_memory.py           # Agent memory and learning system
├── agent_pool.py             # Agent pool management
├── agent_tool_config.py      # Security and tool access control
├── claude_client.py          # Claude Code integration
├── conflict_resolver.py      # Multi-agent conflict resolution
├── context_*.py              # Context management components
├── cross_project_intelligence.py  # Cross-project learning
├── data_models.py            # Core project data models
├── discord_bot.py            # Discord integration
├── global_orchestrator.py    # Multi-project orchestration
├── multi_project_*.py        # Multi-project management
├── parallel_tdd_*.py         # Parallel TDD execution
├── project_storage.py        # File-based persistence
├── resource_scheduler.py     # Resource allocation
├── state_*.py                # State management
├── tdd_*.py                  # TDD-specific components
└── token_calculator.py       # Token budget management
```

## Core Components

### 1. Agent System (`agents/`)

The agent system provides a sophisticated framework for specialized AI agents with TDD integration, security controls, and context management.

#### BaseAgent Framework

**Location:** `agents/__init__.py`

The `BaseAgent` class serves as the foundation for all specialized agents:

```python
class BaseAgent(ABC):
    def __init__(self, name: str, capabilities: List[str], context_manager: Optional[Any] = None)
    async def run(self, task: Task, dry_run: bool = False) -> AgentResult
    async def execute_tdd_phase(self, phase: TDDState, context: Dict[str, Any]) -> AgentResult
    async def handle_tdd_task(self, tdd_cycle: TDDCycle, phase: TDDState) -> AgentResult
```

**Key Features:**
- TDD state machine integration with phase validation
- Context manager integration for intelligent context preparation
- Agent memory system for learning and decision tracking
- Comprehensive logging and metrics collection
- Error handling with TDD-specific recovery strategies
- Security boundary enforcement through tool restrictions

#### Specialized Agents

**DesignAgent** (`agents/design_agent.py`)
- **Purpose:** System architecture, design specifications, acceptance criteria
- **TDD Phase:** DESIGN
- **Capabilities:** Architecture diagrams, API contracts, test scenarios, specifications
- **Security:** Read-only access, cannot modify code, can create documentation
- **Tools:** Documentation creation, web research, file analysis

**CodeAgent** (`agents/code_agent.py`)
- **Purpose:** Feature implementation, bug fixes, code refactoring
- **TDD Phases:** CODE_GREEN, REFACTOR, COMMIT
- **Capabilities:** Minimal implementation, test-driven development, refactoring
- **Security:** Code modification, version control (add/commit), testing tools
- **Tools:** File editing, git operations, test execution, code quality tools

**QAAgent** (`agents/qa_agent.py`)
- **Purpose:** Test creation, quality validation, coverage analysis
- **TDD Phase:** TEST_RED
- **Capabilities:** Failing test creation, comprehensive test suites, red state validation
- **Security:** Test file creation only, cannot modify implementation, cannot commit
- **Tools:** Test frameworks, coverage analysis, quality metrics

**DataAgent** (`agents/data_agent.py`)
- **Purpose:** Data analysis, metrics visualization, reporting
- **TDD Phases:** None (analysis only)
- **Capabilities:** TDD metrics analysis, coverage reporting, performance analysis
- **Security:** Read-only access, data processing tools, visualization
- **Tools:** Data analysis, notebook creation, visualization libraries

#### Agent Registry and Factory

The system includes a dynamic agent registry for runtime instantiation:

```python
AGENT_REGISTRY: Dict[str, type] = {
    "DesignAgent": DesignAgent,
    "CodeAgent": CodeAgent,
    "QAAgent": QAAgent,
    "DataAgent": DataAgent,
}

def create_agent(agent_type: str, context_manager: Optional[Any] = None, **kwargs) -> BaseAgent
```

### 2. Context Management System (`context/`)

Advanced context management system for intelligent agent communication and token optimization.

#### Core Models (`context/models.py`)

**AgentContext** - Prepared context for agent execution
```python
@dataclass
class AgentContext:
    request_id: str
    agent_type: str
    story_id: str
    core_context: str = ""
    dependencies: str = ""
    historical_context: str = ""
    agent_memory: str = ""
    token_budget: Optional[TokenBudget] = None
    token_usage: Optional[TokenUsage] = None
    relevance_scores: List[RelevanceScore] = field(default_factory=list)
    file_contents: Dict[str, str] = field(default_factory=dict)
```

**TokenBudget** - Token allocation management
```python
@dataclass
class TokenBudget:
    total_budget: int
    core_task: int = 0
    historical: int = 0
    dependencies: int = 0
    agent_memory: int = 0
    buffer: int = 0
```

**Decision Tracking** - Agent decision history
```python
@dataclass
class Decision:
    agent_type: str
    description: str
    rationale: str
    outcome: str
    confidence: float
    artifacts: Dict[str, str]
```

#### Interfaces (`context/interfaces.py`)

Abstract interfaces ensuring separation of concerns:

- `IContextFilter` - Intelligent file relevance filtering
- `ITokenCalculator` - Token budget calculation and optimization
- `IAgentMemory` - Agent memory management
- `IContextCompressor` - Content compression for token limits
- `IContextIndex` - Codebase indexing and search
- `IContextStorage` - Context persistence and caching

### 3. Security System (`agent_tool_config.py`)

Comprehensive security framework enforcing tool access restrictions per agent type.

#### Agent Security Profiles

**Tool Access Control:**
```python
AGENT_TOOL_CONFIG: Dict[AgentType, Dict[str, List[str]]] = {
    AgentType.ORCHESTRATOR: {
        "allowed_tools": ["Read", "Write", "Edit", "Bash(*)", ...],
        "disallowed_tools": ["Bash(sudo)", "Bash(format)", ...]
    },
    AgentType.DESIGN: {
        "allowed_tools": ["Read", "Write", "Bash(ls)", "WebFetch", ...],
        "disallowed_tools": ["Edit", "MultiEdit", "Bash(rm)", ...]
    },
    # ... other agent types
}
```

**TDD-Specific Restrictions:**
- Phase-based access control (DESIGN, TEST_RED, CODE_GREEN, REFACTOR, COMMIT)
- Tool validation with detailed reasoning
- Command access control with Claude Code CLI integration
- Security boundary enforcement with audit trails

#### Validation Functions

```python
def validate_agent_access(agent_type: AgentType, tool_name: str) -> bool
def validate_tdd_phase_access(agent_type: AgentType, tdd_phase: str) -> bool
def validate_tdd_tool_access(agent_type: AgentType, tool_name: str, tdd_context: Dict) -> Dict
```

### 4. State Management

#### Main State Machine (`state_machine.py`)

Finite state machine governing command transitions and workflow validation:

```python
class StateMachine:
    TRANSITIONS: Dict[str, Dict[State, State]] = {
        "/epic": {State.IDLE: State.BACKLOG_READY},
        "/sprint plan": {State.BACKLOG_READY: State.SPRINT_PLANNED},
        "/sprint start": {State.SPRINT_PLANNED: State.SPRINT_ACTIVE},
        # ... more transitions
    }
```

**States:**
- `IDLE` - Initial state, no active work
- `BACKLOG_READY` - Epic defined, stories can be managed
- `SPRINT_PLANNED` - Sprint created with stories
- `SPRINT_ACTIVE` - Sprint in progress with TDD cycles
- `SPRINT_PAUSED` - Sprint temporarily paused
- `SPRINT_REVIEW` - Sprint completed, awaiting review
- `BLOCKED` - Workflow blocked (e.g., CI failures)

#### TDD State Machine (`tdd_state_machine.py`)

Specialized state machine for TDD cycle management:

**TDD States:**
- `DESIGN` - Specification and acceptance criteria creation
- `TEST_RED` - Failing test creation
- `CODE_GREEN` - Minimal implementation to pass tests
- `REFACTOR` - Code improvement while maintaining green tests
- `COMMIT` - Save progress and complete cycle

### 5. Data Models (`data_models.py`)

Core project management entities with TDD integration:

```python
@dataclass
class Epic:
    id: str
    title: str
    description: str
    status: EpicStatus
    tdd_requirements: List[str]
    tdd_constraints: Dict[str, Any]

@dataclass
class Story:
    id: str
    epic_id: Optional[str]
    title: str
    description: str
    acceptance_criteria: List[str]
    tdd_cycle_id: Optional[str]
    test_status: str
    test_files: List[str]
    ci_status: str
    test_coverage: float

@dataclass
class Sprint:
    id: str
    goal: str
    story_ids: List[str]
    status: SprintStatus
    active_tdd_cycles: List[str]
    tdd_metrics: Dict[str, Any]
```

### 6. TDD Models (`tdd_models.py`)

Specialized models for TDD cycle management:

```python
@dataclass
class TDDCycle:
    id: str
    story_id: str
    current_state: TDDState
    tasks: List[TDDTask]
    total_test_runs: int
    overall_test_coverage: float

@dataclass
class TDDTask:
    id: str
    cycle_id: str
    description: str
    acceptance_criteria: List[str]
    current_state: TDDState
    test_files: List[str]
    test_file_objects: List[TestFile]
    test_results: List[TestResult]

@dataclass
class TestFile:
    file_path: str
    story_id: str
    status: TestFileStatus
    ci_status: CIStatus
    test_count: int
    passing_tests: int
    failing_tests: int
    coverage_percentage: float
```

### 7. Storage System (`project_storage.py`)

File-based persistence system with version control integration:

```python
class ProjectStorage:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.orch_state_dir = self.project_path / ".orch-state"
        self.backlog_file = self.orch_state_dir / "backlog.json"
        self.sprints_dir = self.orch_state_dir / "sprints"
        self.tdd_cycles_dir = self.orch_state_dir / "tdd_cycles"
```

**Directory Structure:**
```
.orch-state/
├── backlog.json              # Project data (epics, stories)
├── status.json               # Current state
├── architecture.md           # Architecture documentation
├── best-practices.md         # Project guidelines
├── sprints/                  # Individual sprint files
│   ├── sprint-abc123.json
│   └── ...
├── tdd_cycles/              # TDD cycle data
│   ├── cycle-def456.json
│   ├── cycle-def456_state.json
│   └── ...
└── backups/                 # Recovery data
```

### 8. Multi-Project Orchestration (`global_orchestrator.py`)

Global coordination system for managing multiple projects:

```python
class GlobalOrchestrator:
    def __init__(self, config_manager: MultiProjectConfigManager)
    async def start_project(self, project_name: str) -> bool
    async def stop_project(self, project_name: str) -> bool
    async def get_global_status(self) -> Dict[str, Any]
```

**Features:**
- Resource allocation and scheduling
- Cross-project dependency management
- Shared pattern recognition
- Performance monitoring and optimization
- Discord integration for multi-project management

### 9. Discord Integration (`discord_bot.py`)

Discord interface for human-in-the-loop interactions:

**Slash Commands:**
- `/project register <path> [name]` - Register new project
- `/epic "<description>"` - Define high-level initiatives
- `/backlog view|add_story|prioritize` - Backlog management
- `/sprint plan|start|status|pause|resume` - Sprint lifecycle
- `/state` - Interactive state inspection
- `/approve [ID]` - Approve queued tasks

**Real-time Features:**
- State visualization with interactive buttons
- Project-specific channels
- Error handling with helpful hints
- Cross-project coordination

### 10. Context Intelligence Layer

Advanced context management components for intelligent filtering and compression:

#### Context Filter (`context_filter.py`)
- Intelligent file relevance scoring
- TDD phase-aware filtering
- Historical usage learning
- Cross-story conflict detection

#### Context Compressor (`context_compressor.py`)
- Content-aware compression
- Token budget optimization
- Structure preservation
- File type-specific strategies

#### Context Index (`context_index.py`)
- Codebase indexing and search
- Dependency analysis
- Symbol extraction
- Semantic search capabilities

#### Token Calculator (`token_calculator.py`)
- Accurate token estimation
- Budget allocation optimization
- Usage pattern analysis
- Performance metrics

## Integration Patterns

### 1. Agent-Context Integration

Agents integrate with the context management system for intelligent context preparation:

```python
async def prepare_context(
    self, 
    task: Union[TDDTask, Dict[str, Any]], 
    story_id: Optional[str] = None,
    max_tokens: Optional[int] = None
) -> Optional[Any]:
    if not self.context_manager:
        return None
    
    context = await self.context_manager.prepare_context(
        agent_type=self.__class__.__name__,
        task=task,
        max_tokens=max_tokens,
        story_id=story_id
    )
    
    self._current_context = context
    return context
```

### 2. TDD-State Integration

State machines coordinate TDD cycles with main workflow:

```python
def validate_sprint_transition_with_tdd(self, target_state: State) -> CommandResult:
    if target_state == State.SPRINT_REVIEW and self.has_active_tdd_cycles():
        return CommandResult(
            success=False,
            error_message="Cannot transition to SPRINT_REVIEW with active TDD cycles",
            hint="Complete or abort active TDD cycles before sprint review"
        )
```

### 3. Security Integration

Security policies are enforced transparently via Claude Code CLI:

```python
def get_claude_tool_args(agent_type: AgentType) -> List[str]:
    args = []
    allowed = get_allowed_tools(agent_type)
    if allowed:
        args.extend(["--allowedTools", " ".join(allowed)])
    
    disallowed = get_disallowed_tools(agent_type)
    if disallowed:
        args.extend(["--disallowedTools", " ".join(disallowed)])
    
    return args
```

### 4. Storage Integration

All components use consistent file-based persistence:

```python
# State synchronization
project_data = storage.load_project_data()
project_data.stories.append(new_story)
storage.save_project_data(project_data)

# TDD cycle management
cycle = storage.load_tdd_cycle(cycle_id)
cycle.tasks.append(new_task)
storage.save_tdd_cycle(cycle)
```

## Dependencies

### External Dependencies
- `discord.py` - Discord bot framework
- `pygithub` - GitHub API integration
- `pyyaml` - Configuration management
- `pytest` - Testing framework
- `asyncio` - Asynchronous operations
- `pathlib` - Path manipulation
- `dataclasses` - Data model definitions
- `enum` - Enumeration types
- `logging` - Comprehensive logging

### Internal Dependencies
- Clear separation of concerns with abstract interfaces
- Dependency injection for testability
- Graceful fallbacks when components are unavailable
- Environment variable configuration
- NO_AGENT_MODE for testing without Claude Code

## Key Features

### 1. Intelligent Context Management
- Token budget optimization with intelligent allocation
- File relevance scoring based on agent type and TDD phase
- Content compression with structure preservation
- Cross-story context management and conflict detection
- Agent memory integration for learning and handoffs

### 2. Comprehensive Security
- Agent-specific tool restrictions enforced via Claude Code CLI
- TDD phase-based access control
- Command validation with detailed reasoning
- Security audit trails and compliance reporting
- Principle of least privilege enforcement

### 3. Advanced TDD Integration
- Full TDD lifecycle management (DESIGN → TEST_RED → CODE_GREEN → REFACTOR → COMMIT)
- Test file lifecycle tracking with CI integration
- Coverage analysis and quality metrics
- TDD cycle coordination with main workflow
- Recovery mechanisms for interrupted cycles

### 4. Multi-Project Orchestration
- Resource allocation across multiple projects
- Cross-project pattern recognition and learning
- Shared knowledge and best practices
- Performance monitoring and optimization
- Discord integration for unified management

### 5. Human-in-the-Loop Workflow
- Strategic decision escalation after 3 failed attempts
- Interactive state visualization and debugging
- Project-specific Discord channels
- Real-time status monitoring and alerts
- Graceful error handling with helpful hints

## Architecture Principles

### 1. Separation of Concerns
- Clear boundaries between orchestration, agent logic, and context management
- Abstract interfaces for all major components
- Dependency injection for testing and flexibility

### 2. Security-First Design
- Tool access control at the system level
- Agent capability restrictions based on role
- Audit trails for all security-relevant operations

### 3. TDD-Driven Development
- TDD cycles as first-class entities
- State machine enforcement of proper TDD workflow
- Comprehensive test file and CI integration

### 4. Scalability and Performance
- Intelligent context compression and filtering
- Token budget optimization
- Background processing for non-critical operations
- Caching and performance monitoring

### 5. Extensibility
- Plugin architecture for new agent types
- Configurable context management strategies
- Extensible security policies
- Modular component design

This library represents a sophisticated AI orchestration framework that combines the rigor of TDD with the flexibility of AI-assisted development, all while maintaining strict security boundaries and comprehensive audit trails.