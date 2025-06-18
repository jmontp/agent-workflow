# C4 Code Diagram - AI Agent TDD-Scrum Workflow

## Dual State Machine Class Structure

The system implements dual state machines that work in coordination to manage both workflow progression and Test-Driven Development cycles.

### Workflow State Machine

```mermaid
classDiagram
    class WorkflowStateMachine {
        +current_state: WorkflowState
        +validate_command(command: Command) bool
        +transition(command: Command) WorkflowState
        +get_allowed_commands() List[Command]
        +get_state_diagram() str
        +coordinate_with_tdd(tdd_sm: TDDStateMachine) void
    }
    
    class WorkflowState {
        <<enumeration>>
        IDLE
        BACKLOG_READY
        SPRINT_PLANNED
        SPRINT_ACTIVE
        SPRINT_PAUSED
        SPRINT_REVIEW
        BLOCKED
    }
    
    class Command {
        +name: str
        +args: Dict
        +validate() bool
        +execute() Result
    }
    
    WorkflowStateMachine --> WorkflowState
    WorkflowStateMachine --> Command
```

### TDD State Machine

```mermaid
classDiagram
    class TDDStateMachine {
        +current_state: TDDState
        +active_cycle: TDDCycle
        +validate_command(command: str, cycle: TDDCycle) TDDCommandResult
        +transition(command: str, cycle: TDDCycle) TDDCommandResult
        +get_allowed_commands(cycle: TDDCycle) List[str]
        +get_next_suggested_command(cycle: TDDCycle) str
        +get_state_info(cycle: TDDCycle) Dict
        +set_active_cycle(cycle: TDDCycle) void
        +can_auto_progress(cycle: TDDCycle) bool
    }
    
    class TDDState {
        <<enumeration>>
        DESIGN
        TEST_RED
        CODE_GREEN
        REFACTOR
        COMMIT
    }
    
    class TDDCommandResult {
        +success: bool
        +new_state: TDDState
        +error_message: str
        +hint: str
        +data: Dict
    }
    
    TDDStateMachine --> TDDState
    TDDStateMachine --> TDDCommandResult
```

## TDD Data Models

```mermaid
classDiagram
    class TDDCycle {
        +id: str
        +story_id: str
        +current_state: TDDState
        +current_task_id: str
        +tasks: List[TDDTask]
        +started_at: str
        +completed_at: str
        +total_test_runs: int
        +total_refactors: int
        +total_commits: int
        +ci_status: CIStatus
        +overall_test_coverage: float
        +is_complete() bool
        +get_current_task() TDDTask
        +add_task(task: TDDTask) void
        +start_task(task_id: str) bool
        +complete_current_task() bool
    }
    
    class TDDTask {
        +id: str
        +cycle_id: str
        +description: str
        +acceptance_criteria: List[str]
        +current_state: TDDState
        +test_files: List[str]
        +test_file_objects: List[TestFile]
        +source_files: List[str]
        +test_results: List[TestResult]
        +design_notes: str
        +implementation_notes: str
        +refactor_notes: str
        +has_passing_tests() bool
        +has_failing_tests() bool
        +can_commit_tests() bool
        +can_commit_code() bool
    }
    
    class TestFile {
        +id: str
        +file_path: str
        +relative_path: str
        +story_id: str
        +task_id: str
        +status: TestFileStatus
        +ci_status: CIStatus
        +test_count: int
        +passing_tests: int
        +failing_tests: int
        +coverage_percentage: float
        +exists() bool
        +is_committed() bool
        +is_passing() bool
        +get_permanent_location() str
    }
    
    class TestResult {
        +id: str
        +test_file: str
        +test_name: str
        +status: TestStatus
        +output: str
        +error_message: str
        +execution_time: float
        +timestamp: str
    }
    
    TDDCycle --> TDDTask
    TDDTask --> TestFile
    TDDTask --> TestResult
    TestFile --> TestResult
```

## Enhanced Agent Class Hierarchy

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +name: str
        +capabilities: List[str]
        +tdd_capabilities: List[str]
        +run(task: Task, dry: bool) Result
        +run_tdd_phase(tdd_task: TDDTask, phase: TDDState) Result
        +validate_task(task: Task) bool
        +validate_tdd_task(tdd_task: TDDTask) bool
        +get_status() AgentStatus
        +get_tdd_context(cycle: TDDCycle) Dict
    }
    
    class DesignAgent {
        +run(task: Task, dry: bool) Result
        +run_tdd_phase(tdd_task: TDDTask, phase: TDDState) Result
        +create_architecture(requirements: str) str
        +create_tdd_specifications(story: Story) str
        +define_acceptance_criteria(story: Story) List[str]
        +create_test_strategy(story: Story) str
        +review_design(design: str) str
    }
    
    class CodeAgent {
        +run(task: Task, dry: bool) Result
        +run_tdd_phase(tdd_task: TDDTask, phase: TDDState) Result
        +implement_feature(spec: str) str
        +implement_minimal_code(test_files: List[TestFile]) str
        +refactor_code(target: str, preserve_tests: bool) str
        +commit_tdd_phase(phase: TDDState, files: List[str]) str
        +fix_bug(issue: str) str
    }
    
    class QAAgent {
        +run(task: Task, dry: bool) Result
        +run_tdd_phase(tdd_task: TDDTask, phase: TDDState) Result
        +write_failing_tests(spec: str, story_id: str) List[TestFile]
        +validate_test_failure(test_files: List[TestFile]) bool
        +preserve_tests_during_code(test_files: List[TestFile]) bool
        +validate_tests_still_pass(test_files: List[TestFile]) bool
        +promote_tests_to_permanent(test_files: List[TestFile]) bool
        +run_tests(code: str) TestResult
        +calculate_coverage(test_files: List[TestFile]) float
    }
    
    class DataAgent {
        +run(task: Task, dry: bool) Result
        +analyze_data(dataset: str) str
        +create_pipeline(spec: str) str
        +analyze_tdd_metrics(cycle: TDDCycle) Dict
    }
    
    BaseAgent <|-- DesignAgent
    BaseAgent <|-- CodeAgent
    BaseAgent <|-- QAAgent
    BaseAgent <|-- DataAgent
```

## TDD Phase Management Classes

```mermaid
classDiagram
    class TDDPhaseManager {
        +current_phase: TDDState
        +active_cycles: Dict[str, TDDCycle]
        +coordinate_agent_handoff(from_agent: BaseAgent, to_agent: BaseAgent) bool
        +validate_phase_completion(cycle: TDDCycle, phase: TDDState) bool
        +trigger_phase_transition(cycle: TDDCycle, new_phase: TDDState) bool
        +handle_phase_failure(cycle: TDDCycle, error: Exception) void
    }
    
    class TestPreservationManager {
        +preserve_test_files(test_files: List[TestFile]) bool
        +validate_test_integrity(test_files: List[TestFile]) bool
        +commit_test_phase(cycle: TDDCycle, phase: TDDState) bool
        +promote_tests_to_permanent(cycle: TDDCycle) bool
        +rollback_test_changes(cycle: TDDCycle, to_phase: TDDState) bool
    }
    
    class TDDCycleCoordinator {
        +create_cycle_for_story(story: Story) TDDCycle
        +start_cycle(cycle_id: str) bool
        +pause_cycle(cycle_id: str) bool
        +resume_cycle(cycle_id: str) bool
        +complete_cycle(cycle_id: str) bool
        +get_cycle_progress(cycle_id: str) Dict
        +coordinate_multiple_cycles(story_ids: List[str]) bool
    }
    
    TDDPhaseManager --> TDDCycle
    TestPreservationManager --> TestFile
    TDDCycleCoordinator --> TDDCycle
```

## Enhanced Orchestrator Core Classes

```mermaid
classDiagram
    class Orchestrator {
        +projects: Dict[str, Project]
        +agents: Dict[str, BaseAgent]
        +workflow_state_machine: WorkflowStateMachine
        +tdd_state_machine: TDDStateMachine
        +state_coordinator: StateCoordinator
        +tdd_coordinator: TDDCycleCoordinator
        +handle_command(command: Command) Result
        +handle_tdd_command(command: str, story_id: str) Result
        +dispatch_task(task: Task) Result
        +dispatch_tdd_task(tdd_task: TDDTask, phase: TDDState) Result
        +escalate_to_human(task: Task) ApprovalRequest
        +coordinate_dual_states() void
    }
    
    class Project {
        +name: str
        +path: Path
        +workflow_state: ProjectState
        +tdd_state: TDDProjectState
        +orchestration_mode: OrchestrationMode
        +load_workflow_state() ProjectState
        +save_workflow_state(state: ProjectState) void
        +load_tdd_state() TDDProjectState
        +save_tdd_state(state: TDDProjectState) void
    }
    
    class ProjectState {
        +current_state: WorkflowState
        +active_tasks: List[Task]
        +pending_approvals: List[ApprovalRequest]
        +sprint_backlog: List[Story]
        +product_backlog: List[Story]
    }
    
    class TDDProjectState {
        +active_cycles: Dict[str, TDDCycle]
        +completed_cycles: List[TDDCycle]
        +test_coverage_metrics: Dict
        +tdd_performance_metrics: Dict
        +get_active_cycle_for_story(story_id: str) TDDCycle
        +create_cycle_for_story(story: Story) TDDCycle
    }
    
    class StateCoordinator {
        +coordinate_workflow_and_tdd() bool
        +validate_state_consistency() bool
        +handle_state_conflicts() void
        +sync_sprint_with_tdd_cycles() bool
    }
    
    class Task {
        +id: str
        +agent_type: str
        +command: str
        +status: TaskStatus
        +retry_count: int
        +created_at: datetime
        +tdd_context: Dict
    }
    
    Orchestrator --> Project
    Orchestrator --> StateCoordinator
    Orchestrator --> TDDCycleCoordinator
    Project --> ProjectState
    Project --> TDDProjectState
    ProjectState --> Task
    TDDProjectState --> TDDCycle
    Orchestrator --> WorkflowStateMachine
    Orchestrator --> TDDStateMachine
    Orchestrator --> BaseAgent
```

## Discord Bot Classes

```mermaid
classDiagram
    class DiscordBot {
        +orchestrator: Orchestrator
        +client: discord.Client
        +handle_slash_command(interaction: Interaction) void
        +send_notification(message: str, channel: str) void
        +create_interactive_view(state: State) discord.View
    }
    
    class CommandHandler {
        +parse_command(interaction: Interaction) Command
        +validate_command(command: Command) bool
        +execute_command(command: Command) Result
    }
    
    class StateView {
        +state: State
        +create_buttons() List[discord.Button]
        +create_embed() discord.Embed
        +handle_button_click(interaction: Interaction) void
    }
    
    class NotificationManager {
        +send_approval_request(request: ApprovalRequest) void
        +send_status_update(project: str, status: str) void
        +send_error_notification(error: Exception) void
    }
    
    DiscordBot --> CommandHandler
    DiscordBot --> StateView
    DiscordBot --> NotificationManager
    DiscordBot --> Orchestrator
```