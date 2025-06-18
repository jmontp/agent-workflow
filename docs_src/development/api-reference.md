# API Reference

Complete API reference for the AI Agent TDD-Scrum workflow system.

## Core Classes

### Orchestrator

Main coordination engine for the workflow system.

```python
from lib.orchestrator import Orchestrator

orchestrator = Orchestrator(config_path="config.yml")
```

#### Methods

**`async create_epic(description: str, priority: str = "medium") -> Epic`**

Create a new epic with the given description.

**Parameters:**
- `description` (str): Human-readable description of the epic
- `priority` (str, optional): Priority level ("low", "medium", "high"). Defaults to "medium"

**Returns:**
- `Epic`: The created epic instance

**Raises:**
- `ValueError`: If description is empty or invalid

**Example:**
```python
epic = await orchestrator.create_epic("Build authentication system", "high")
print(f"Created epic: {epic.id}")
```

**`async plan_sprint(story_ids: List[str]) -> Sprint`**

Plan a new sprint with the specified stories.

**`async start_sprint() -> bool`**

Start the currently planned sprint.

**`async get_state() -> OrchestratorState`**

Get the current orchestrator state.

### State Machine

Finite state machine managing workflow transitions.

```python
from lib.state_machine import StateMachine, OrchestratorState

state_machine = StateMachine()
```

#### States

- `IDLE`: Initial state, ready for epic creation
- `BACKLOG_READY`: Epic created, ready for sprint planning
- `SPRINT_PLANNED`: Sprint planned, ready to start
- `SPRINT_ACTIVE`: Sprint in progress
- `SPRINT_PAUSED`: Sprint temporarily paused
- `SPRINT_REVIEW`: Sprint completed, awaiting review
- `BLOCKED`: System blocked, requires intervention

#### Methods

**`transition(current_state: OrchestratorState, command: str) -> OrchestratorState`**

Execute a state transition based on the current state and command.

**`get_allowed_commands(state: OrchestratorState) -> List[str]`**

Get the list of commands allowed in the given state.

## Data Models

### Epic

High-level initiative or feature area.

```python
from lib.data_models import Epic

epic = Epic(
    id="AUTH-EPIC-001",
    description="Build comprehensive authentication system",
    priority="high",
    status="active"
)
```

#### Attributes

- `id` (str): Unique identifier
- `description` (str): Human-readable description
- `priority` (str): Priority level ("low", "medium", "high")
- `status` (str): Current status ("pending", "active", "completed")
- `created_at` (datetime): Creation timestamp
- `stories` (List[Story]): Associated stories

#### Methods

**`add_story(story: Story) -> None`**

Add a story to this epic.

**`to_dict() -> dict`**

Serialize epic to dictionary.

**`from_dict(data: dict) -> Epic`** (classmethod)

Create epic from dictionary.

### Story

Specific, actionable task within an epic.

```python
from lib.data_models import Story

story = Story(
    id="AUTH-001",
    description="Create user registration form",
    epic_id="AUTH-EPIC-001",
    priority="high"
)
```

#### Attributes

- `id` (str): Unique identifier
- `description` (str): Detailed task description
- `epic_id` (str): Parent epic identifier
- `priority` (str): Priority level
- `status` (str): Current status
- `assigned_agent` (str, optional): Agent type assigned
- `created_at` (datetime): Creation timestamp

### Sprint

Time-boxed development iteration.

```python
from lib.data_models import Sprint

sprint = Sprint(
    id="SPRINT-001",
    stories=["AUTH-001", "AUTH-002"],
    start_date=datetime.now(),
    duration_days=7
)
```

#### Attributes

- `id` (str): Unique identifier
- `stories` (List[str]): Story IDs included in sprint
- `start_date` (datetime): Sprint start date
- `duration_days` (int): Sprint length in days
- `status` (str): Current status ("planned", "active", "completed")

## Agent System

### BaseAgent

Abstract base class for all agents.

```python
from lib.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def run(self, task: str, dry_run: bool = False) -> str:
        # Implementation
        pass
```

#### Methods

**`async run(task: str, dry_run: bool = False) -> str`** (abstract)

Execute the given task.

**`get_capabilities() -> List[str]`**

Return list of agent capabilities.

### DesignAgent

Specialized agent for architecture and design tasks.

```python
from lib.agents.design_agent import DesignAgent

agent = DesignAgent()
result = await agent.run("Create API specification for user authentication")
```

#### Capabilities

- System architecture design
- API specification creation
- Component interface design
- Technical documentation
- Design review and validation

### CodeAgent

Specialized agent for code implementation tasks.

```python
from lib.agents.code_agent import CodeAgent

agent = CodeAgent()
result = await agent.run("Implement user registration endpoint")
```

#### Capabilities

- Feature implementation
- Bug fixing and debugging
- Code refactoring
- Performance optimization
- Integration development

### QAAgent

Specialized agent for testing and quality assurance.

```python
from lib.agents.qa_agent import QAAgent

agent = QAAgent()
result = await agent.run("Create unit tests for authentication module")
```

#### Capabilities

- Test suite creation
- Quality validation
- Coverage analysis
- Performance testing
- Security testing

### DataAgent

Specialized agent for data analysis and visualization.

```python
from lib.agents.data_agent import DataAgent

agent = DataAgent()
result = await agent.run("Analyze user registration patterns")
```

#### Capabilities

- Data analysis and insights
- Pipeline creation
- Metrics reporting
- Visualization generation
- Statistical analysis

## Discord Bot

Discord interface for Human-In-The-Loop control.

```python
from lib.discord_bot import DiscordBot

bot = DiscordBot(orchestrator=orchestrator)
```

### Commands

All Discord commands are implemented as slash commands:

- `/epic "description"` - Create new epic
- `/approve [ID...]` - Approve pending items
- `/sprint plan|start|status|pause|resume` - Sprint management
- `/backlog view|add_story|prioritize` - Backlog operations
- `/state` - Interactive state inspection

## Storage System

### ProjectStorage

File-based persistence for project data.

```python
from lib.project_storage import ProjectStorage

storage = ProjectStorage(project_path="/path/to/project")
```

#### Methods

**`save_epic(epic: Epic) -> None`**

Persist epic to storage.

**`load_epic(epic_id: str) -> Epic`**

Load epic from storage.

**`save_sprint(sprint: Sprint) -> None`**

Persist sprint to storage.

**`get_project_state() -> dict`**

Get complete project state.

## Security System

### Agent Tool Configuration

Security controls for agent capabilities.

```python
from lib.agent_tool_config import get_agent_security_profile

profile = get_agent_security_profile("CodeAgent")
allowed_tools = profile["allowed_tools"]
blocked_tools = profile["blocked_tools"]
```

#### Security Profiles

Each agent type has specific tool restrictions:

- **DesignAgent**: Read-only access, documentation creation
- **CodeAgent**: Code editing, version control (limited)
- **QAAgent**: Testing tools only
- **DataAgent**: Data processing and visualization

## Error Handling

### Custom Exceptions

```python
from lib.exceptions import (
    InvalidStateTransitionError,
    AgentExecutionError,
    ConfigurationError
)

try:
    await orchestrator.start_sprint()
except InvalidStateTransitionError as e:
    print(f"Invalid state transition: {e}")
```

#### Exception Types

- `InvalidStateTransitionError`: Illegal state machine transition
- `AgentExecutionError`: Agent task execution failure
- `ConfigurationError`: Invalid configuration settings
- `StorageError`: File system or data persistence error

## Configuration

### Config Schema

```python
from lib.config import Config

config = Config.from_file("config.yml")
```

#### Configuration Structure

```yaml
orchestrator:
  mode: "blocking"  # blocking, partial, autonomous
  max_concurrent_projects: 3
  state_save_interval: 60

discord:
  bot_token: "your_token_here"
  command_prefix: "/"
  max_commands_per_minute: 20

agents:
  timeout_minutes: 30
  max_retries: 3
  
projects:
  - name: "web-app"
    path: "/path/to/project"
    mode: "partial"
```

## Utilities

### Logging

```python
from lib.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Orchestrator started")
```

### Async Helpers

```python
from lib.utils.async_helpers import run_with_timeout

result = await run_with_timeout(agent.run(task), timeout=300)
```

## Examples

### Complete Workflow Example

```python
import asyncio
from lib.orchestrator import Orchestrator

async def main():
    # Initialize orchestrator
    orchestrator = Orchestrator("config.yml")
    
    # Create epic
    epic = await orchestrator.create_epic(
        "Build user authentication system", 
        priority="high"
    )
    
    # Plan sprint
    sprint = await orchestrator.plan_sprint([
        "AUTH-001", "AUTH-002", "AUTH-003"
    ])
    
    # Start sprint
    success = await orchestrator.start_sprint()
    
    if success:
        print("Sprint started successfully!")
    
    # Monitor progress
    while True:
        state = await orchestrator.get_state()
        if state == "SPRINT_REVIEW":
            break
        await asyncio.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Agent Example

```python
from lib.agents.base_agent import BaseAgent

class DocumentationAgent(BaseAgent):
    """Agent specialized in creating and maintaining documentation."""
    
    def get_capabilities(self) -> List[str]:
        return [
            "markdown_generation",
            "api_documentation", 
            "user_guide_creation",
            "code_commenting"
        ]
    
    async def run(self, task: str, dry_run: bool = False) -> str:
        if "api documentation" in task.lower():
            return await self._generate_api_docs(task)
        elif "user guide" in task.lower():
            return await self._create_user_guide(task)
        else:
            return await self._general_documentation(task)
    
    async def _generate_api_docs(self, task: str) -> str:
        # Implementation for API documentation
        return "Generated API documentation"
```

## TDD System APIs

### TDDStateMachine

Finite state machine that enforces proper TDD command sequencing according to Test-Driven Development best practices.

```python
from lib.tdd_state_machine import TDDStateMachine, TDDCommandResult
from lib.tdd_models import TDDState, TDDCycle

state_machine = TDDStateMachine()
```

#### Methods

**`validate_command(command: str, cycle: Optional[TDDCycle] = None) -> TDDCommandResult`**

Validate if a TDD command is allowed in the current state.

**Parameters:**
- `command` (str): The TDD command to validate (e.g., "/tdd test", "/tdd code")
- `cycle` (TDDCycle, optional): TDD cycle for context validation

**Returns:**
- `TDDCommandResult`: Validation outcome with success flag, new state, error message, and hints

**Example:**
```python
result = state_machine.validate_command("/tdd code", active_cycle)
if result.success:
    print(f"Command allowed, new state: {result.new_state}")
else:
    print(f"Error: {result.error_message}")
    print(f"Hint: {result.hint}")
```

**`transition(command: str, cycle: Optional[TDDCycle] = None) -> TDDCommandResult`**

Execute a TDD state transition if the command is valid.

**`get_allowed_commands(cycle: Optional[TDDCycle] = None) -> List[str]`**

Get list of TDD commands allowed in current state.

**`get_next_suggested_command(cycle: Optional[TDDCycle] = None) -> Optional[str]`**

Get the next suggested command based on current state and conditions.

**`get_state_info(cycle: Optional[TDDCycle] = None) -> Dict[str, Any]`**

Get comprehensive TDD state information for debugging and visualization.

**`can_auto_progress(cycle: Optional[TDDCycle] = None) -> bool`**

Check if state machine can automatically progress to next state.

**`get_mermaid_diagram() -> str`**

Generate Mermaid state diagram for TDD workflow visualization.

### TDD Data Models

#### TDDState Enum

TDD cycle states with their purposes:

```python
from lib.tdd_models import TDDState

class TDDState(Enum):
    DESIGN = "design"           # Create specifications and acceptance criteria
    TEST_RED = "test_red"       # Write failing tests
    CODE_GREEN = "code_green"   # Implement minimal code to pass tests
    REFACTOR = "refactor"       # Improve code quality while keeping tests green
    COMMIT = "commit"           # Save progress and mark task complete
```

#### TDDCycle

TDD cycle linked to a story with task management and progress tracking.

```python
from lib.tdd_models import TDDCycle, TDDTask

cycle = TDDCycle(
    id="tdd-cycle-abc123",
    story_id="AUTH-001",
    current_state=TDDState.DESIGN
)
```

**Attributes:**
- `id` (str): Unique identifier
- `story_id` (str): Associated story identifier
- `current_state` (TDDState): Current TDD phase
- `current_task_id` (Optional[str]): Active task identifier
- `tasks` (List[TDDTask]): All tasks in the cycle
- `started_at` (str): Cycle start timestamp
- `completed_at` (Optional[str]): Cycle completion timestamp
- `total_test_runs` (int): Count of test executions
- `total_refactors` (int): Count of refactor operations
- `total_commits` (int): Count of commits made
- `ci_status` (CIStatus): Overall CI status
- `overall_test_coverage` (float): Average test coverage

**Methods:**

**`get_current_task() -> Optional[TDDTask]`**

Get the currently active task.

**`add_task(task: TDDTask) -> None`**

Add a new task to the cycle.

**`start_task(task_id: str) -> bool`**

Start a specific task (only one can be active).

**`complete_current_task() -> bool`**

Mark current task as complete and advance cycle.

**`get_progress_summary() -> Dict[str, Any]`**

Get detailed progress information including task counts and metrics.

**`calculate_overall_coverage() -> float`**

Calculate overall test coverage for the entire cycle.

#### TDDTask

Individual task within a TDD cycle with test management and state tracking.

```python
from lib.tdd_models import TDDTask, TestFile, TestResult

task = TDDTask(
    id="tdd-task-xyz789",
    cycle_id="tdd-cycle-abc123",
    description="Implement user authentication API",
    current_state=TDDState.DESIGN
)
```

**Attributes:**
- `id` (str): Unique identifier
- `cycle_id` (str): Parent cycle identifier
- `description` (str): Task description
- `acceptance_criteria` (List[str]): Acceptance criteria list
- `current_state` (TDDState): Current task state
- `test_files` (List[str]): Test file paths
- `test_file_objects` (List[TestFile]): TestFile objects with metadata
- `source_files` (List[str]): Source file paths
- `test_results` (List[TestResult]): Test execution results
- `design_notes` (str): Design phase documentation
- `implementation_notes` (str): Implementation notes
- `refactor_notes` (str): Refactoring documentation
- `ci_status` (CIStatus): CI pipeline status
- `test_coverage` (float): Task-specific test coverage

**Methods:**

**`has_passing_tests() -> bool`**

Check if all tests are currently passing.

**`has_failing_tests() -> bool`**

Check if any tests are currently failing.

**`add_test_file(test_file: TestFile) -> None`**

Add a test file to this task.

**`get_committed_test_files() -> List[TestFile]`**

Get all test files that have been committed to repository.

**`can_commit_tests() -> bool`**

Check if tests are ready to be committed (RED state with failing tests).

**`can_commit_code() -> bool`**

Check if code can be committed (tests passing with committed test files).

**`can_commit_refactor() -> bool`**

Check if refactored code can be committed (tests still passing).

#### TestFile

Test file lifecycle management with CI integration.

```python
from lib.tdd_models import TestFile, TestFileStatus, CIStatus

test_file = TestFile(
    file_path="/path/to/test_auth.py",
    relative_path="tests/tdd/AUTH-001/test_auth.py",
    story_id="AUTH-001",
    status=TestFileStatus.DRAFT
)
```

**Attributes:**
- `id` (str): Unique identifier
- `file_path` (str): Absolute file path
- `relative_path` (str): Path relative to project root
- `story_id` (str): Associated story identifier
- `task_id` (str): Associated task identifier
- `status` (TestFileStatus): File lifecycle status
- `ci_status` (CIStatus): CI pipeline status
- `test_count` (int): Total number of tests
- `passing_tests` (int): Count of passing tests
- `failing_tests` (int): Count of failing tests
- `coverage_percentage` (float): Code coverage percentage

**Methods:**

**`exists() -> bool`**

Check if test file exists on filesystem.

**`is_committed() -> bool`**

Check if test file has been committed to repository.

**`is_passing() -> bool`**

Check if all tests in file are passing.

**`get_permanent_location() -> str`**

Get the permanent test location after integration (tests/unit/ or tests/integration/).

#### TestResult

Individual test execution result with timing and output capture.

```python
from lib.tdd_models import TestResult, TestStatus

result = TestResult(
    test_file="test_auth.py",
    test_name="test_login_success",
    status=TestStatus.GREEN,
    execution_time=0.045
)
```

**Attributes:**
- `id` (str): Unique identifier
- `test_file` (str): Test file name
- `test_name` (str): Specific test name
- `status` (TestStatus): Execution status (RED, GREEN, ERROR)
- `output` (str): Test output capture
- `error_message` (Optional[str]): Error details if failed
- `execution_time` (float): Test execution time in seconds
- `timestamp` (str): Execution timestamp

### Enhanced Agent APIs for TDD

#### DesignAgent (TDD Mode)

Extended capabilities for TDD design phase.

```python
from lib.agents.design_agent import DesignAgent

agent = DesignAgent()
result = await agent.run_tdd_design(
    story="Implement user authentication", 
    acceptance_criteria=["User can login", "Passwords are hashed"]
)
```

**TDD-Specific Methods:**

**`async run_tdd_design(story: str, acceptance_criteria: List[str]) -> TDDTask`**

Create detailed technical specifications for TDD implementation.

**`async create_acceptance_tests(task: TDDTask) -> List[str]`**

Generate acceptance test scenarios from design specifications.

#### QAAgent (TDD Mode)

Specialized for TDD test creation and validation.

```python
from lib.agents.qa_agent import QAAgent

agent = QAAgent()
result = await agent.run_tdd_test_creation(
    task=tdd_task,
    ensure_failures=True
)
```

**TDD-Specific Methods:**

**`async run_tdd_test_creation(task: TDDTask, ensure_failures: bool = True) -> List[TestFile]`**

Create comprehensive failing tests based on design specifications.

**`async validate_test_red_state(task: TDDTask) -> bool`**

Verify that tests are properly failing before implementation.

**`async run_tdd_test_validation(task: TDDTask) -> List[TestResult]`**

Execute tests and validate results against TDD requirements.

#### CodeAgent (TDD Mode)

Implementation with TDD constraints and refactoring support.

```python
from lib.agents.code_agent import CodeAgent

agent = CodeAgent()
result = await agent.run_tdd_implementation(
    task=tdd_task,
    minimal_implementation=True
)
```

**TDD-Specific Methods:**

**`async run_tdd_implementation(task: TDDTask, minimal_implementation: bool = True) -> List[str]`**

Implement minimal code to make tests pass in CODE_GREEN phase.

**`async run_tdd_refactor(task: TDDTask, maintain_green: bool = True) -> List[str]`**

Improve code quality while ensuring all tests remain green.

**`async validate_green_state(task: TDDTask) -> bool`**

Verify that all tests are passing after implementation.

### TDD Orchestration APIs

#### TDDOrchestrator

Coordinates TDD cycles with the main Scrum workflow.

```python
from lib.tdd_orchestrator import TDDOrchestrator

orchestrator = TDDOrchestrator()
```

**Methods:**

**`async start_tdd_cycle(story_id: str, tasks: List[str]) -> TDDCycle`**

Start a new TDD cycle for a story with specified tasks.

**`async progress_tdd_cycle(cycle_id: str, command: str) -> TDDCommandResult`**

Advance a TDD cycle through the next state based on command.

**`async get_active_tdd_cycles() -> List[TDDCycle]`**

Get all currently active TDD cycles across all stories.

**`async pause_tdd_cycle(cycle_id: str) -> bool`**

Temporarily pause a TDD cycle.

**`async resume_tdd_cycle(cycle_id: str) -> bool`**

Resume a paused TDD cycle.

**`async get_tdd_metrics(time_period: str = "30d") -> Dict[str, Any]`**

Get TDD performance metrics and analytics.

### TDD Integration Examples

#### Complete TDD Cycle Management

```python
import asyncio
from lib.tdd_state_machine import TDDStateMachine
from lib.tdd_models import TDDCycle, TDDTask
from lib.agents.design_agent import DesignAgent
from lib.agents.qa_agent import QAAgent
from lib.agents.code_agent import CodeAgent

async def run_complete_tdd_cycle():
    # Initialize TDD cycle
    cycle = TDDCycle(story_id="AUTH-001")
    task = TDDTask(
        description="Implement user login API",
        acceptance_criteria=["User can authenticate", "Invalid credentials rejected"]
    )
    cycle.add_task(task)
    
    # Initialize state machine
    tdd_sm = TDDStateMachine()
    tdd_sm.set_active_cycle(cycle)
    
    # Phase 1: Design
    design_agent = DesignAgent()
    design_result = await design_agent.run_tdd_design(
        story=task.description,
        acceptance_criteria=task.acceptance_criteria
    )
    
    # Transition to TEST_RED
    transition_result = tdd_sm.transition("/tdd test", cycle)
    if transition_result.success:
        # Phase 2: Write failing tests
        qa_agent = QAAgent()
        test_files = await qa_agent.run_tdd_test_creation(task)
        
        # Commit tests
        commit_result = tdd_sm.transition("/tdd commit-tests", cycle)
        if commit_result.success:
            # Phase 3: Implement code
            code_agent = CodeAgent()
            source_files = await code_agent.run_tdd_implementation(task)
            
            # Validate green state
            is_green = await code_agent.validate_green_state(task)
            if is_green:
                # Phase 4: Refactor
                refactor_result = tdd_sm.transition("/tdd refactor", cycle)
                if refactor_result.success:
                    refactored_files = await code_agent.run_tdd_refactor(task)
                    
                    # Final commit
                    final_result = tdd_sm.transition("/tdd commit", cycle)
                    return final_result.success
    
    return False

# Usage
success = asyncio.run(run_complete_tdd_cycle())
```

#### TDD Metrics and Monitoring

```python
from lib.tdd_orchestrator import TDDOrchestrator

async def monitor_tdd_progress():
    orchestrator = TDDOrchestrator()
    
    # Get all active cycles
    active_cycles = await orchestrator.get_active_tdd_cycles()
    
    for cycle in active_cycles:
        progress = cycle.get_progress_summary()
        print(f"Story {cycle.story_id}: {progress['current_state']} "
              f"({progress['progress']} tasks complete)")
        
        current_task = cycle.get_current_task()
        if current_task:
            if current_task.has_failing_tests():
                print(f"  - RED: {len(current_task.test_results)} tests failing")
            elif current_task.has_passing_tests():
                print(f"  - GREEN: All tests passing, coverage: {current_task.test_coverage:.1f}%")
    
    # Get performance metrics
    metrics = await orchestrator.get_tdd_metrics("7d")
    print(f"Last 7 days: {metrics['total_cycles']} cycles, "
          f"avg cycle time: {metrics['avg_cycle_time']} minutes")

# Usage
asyncio.run(monitor_tdd_progress())
```

This API reference provides comprehensive coverage of the system's public interfaces and usage patterns.