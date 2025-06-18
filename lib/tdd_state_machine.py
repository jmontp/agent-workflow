"""
TDD State Machine for Test-Driven Development Workflow.

Implements a finite state machine that governs TDD cycle transitions
and validates TDD command sequences according to TDD best practices.
Enhanced with parallel execution support, resource locking, and coordination events.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import asyncio
import threading
import uuid

try:
    from .tdd_models import TDDState, TDDCycle, TDDTask, TestResult, TestStatus
except ImportError:
    from tdd_models import TDDState, TDDCycle, TDDTask, TestResult, TestStatus

# Import state broadcaster for real-time visualization
try:
    from .state_broadcaster import emit_tdd_transition, emit_parallel_status
except ImportError:
    # Graceful fallback if broadcaster is not available
    def emit_tdd_transition(story_id, old_state, new_state, project_name="default"):
        pass
    def emit_parallel_status(status_data):
        pass

logger = logging.getLogger(__name__)


@dataclass
class TDDCommandResult:
    """Result of TDD command validation and execution"""
    success: bool
    new_state: Optional[TDDState] = None
    error_message: Optional[str] = None
    hint: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    requires_coordination: bool = False
    affected_resources: List[str] = field(default_factory=list)
    coordination_events: List[str] = field(default_factory=list)


@dataclass
class ParallelStateInfo:
    """Information about parallel state tracking"""
    cycle_id: str
    story_id: str
    current_state: TDDState
    parallel_cycles: Set[str] = field(default_factory=set)
    locked_resources: Set[str] = field(default_factory=set)
    coordination_events: List[str] = field(default_factory=list)
    last_transition: datetime = field(default_factory=datetime.utcnow)
    is_coordinated: bool = False


@dataclass
class ResourceLock:
    """Resource lock for parallel execution coordination"""
    resource_id: str
    cycle_id: str
    story_id: str
    lock_type: str  # exclusive, shared
    locked_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationEvent:
    """Event for coordinating parallel cycles"""
    event_id: str
    event_type: str  # state_change, resource_request, conflict_detected
    source_cycle: str
    target_cycles: Set[str] = field(default_factory=set)
    event_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    handled: bool = False


class TDDStateMachine:
    """
    Finite state machine that enforces proper TDD command sequencing
    according to Test-Driven Development best practices.
    Enhanced with parallel execution support, resource locking, and coordination events.
    
    States:
    - DESIGN: Create detailed specifications and acceptance criteria
    - TEST_RED: Write failing tests based on specifications  
    - CODE_GREEN: Implement minimal code to make tests pass
    - REFACTOR: Improve code quality while keeping tests green
    - COMMIT: Save progress and mark task complete
    
    Parallel Features:
    - Multi-cycle state tracking
    - Resource locking for conflict prevention
    - Coordination events for cycle synchronization
    - Cross-cycle dependency management
    """
    
    # Command → State transition matrix for TDD workflow
    TRANSITIONS: Dict[str, Dict[TDDState, TDDState]] = {
        "/tdd start": {
            # Can start TDD from any state (creates new cycle/task)
            TDDState.DESIGN: TDDState.DESIGN,
            TDDState.TEST_RED: TDDState.DESIGN,
            TDDState.CODE_GREEN: TDDState.DESIGN,
            TDDState.REFACTOR: TDDState.DESIGN,
            TDDState.COMMIT: TDDState.DESIGN,
        },
        "/tdd design": {
            TDDState.DESIGN: TDDState.DESIGN,  # Can iterate on design
        },
        "/tdd test": {
            TDDState.DESIGN: TDDState.TEST_RED,  # Move from design to writing tests
            TDDState.TEST_RED: TDDState.TEST_RED,  # Can iterate on tests
        },
        "/tdd code": {
            TDDState.TEST_RED: TDDState.CODE_GREEN,  # Move from red tests to implementation
            TDDState.CODE_GREEN: TDDState.CODE_GREEN,  # Can iterate on implementation
        },
        "/tdd refactor": {
            TDDState.CODE_GREEN: TDDState.REFACTOR,  # Move from green tests to refactoring
            TDDState.REFACTOR: TDDState.REFACTOR,  # Can iterate on refactoring
        },
        "/tdd commit": {
            TDDState.CODE_GREEN: TDDState.COMMIT,  # Can commit when tests are green
            TDDState.REFACTOR: TDDState.COMMIT,   # Can commit after refactoring
        },
        "/tdd next": {
            # Auto-advance to next logical state based on current state and conditions
            TDDState.DESIGN: TDDState.TEST_RED,
            TDDState.TEST_RED: TDDState.CODE_GREEN,
            TDDState.CODE_GREEN: TDDState.REFACTOR,
            TDDState.REFACTOR: TDDState.COMMIT,
            TDDState.COMMIT: TDDState.DESIGN,  # Start next task or complete cycle
        },
        "/tdd status": {
            # Always allowed - introspection command
            TDDState.DESIGN: TDDState.DESIGN,
            TDDState.TEST_RED: TDDState.TEST_RED,
            TDDState.CODE_GREEN: TDDState.CODE_GREEN,
            TDDState.REFACTOR: TDDState.REFACTOR,
            TDDState.COMMIT: TDDState.COMMIT,
        },
        "/tdd abort": {
            # Always allowed - cancel current cycle
            TDDState.DESIGN: TDDState.COMMIT,
            TDDState.TEST_RED: TDDState.COMMIT,
            TDDState.CODE_GREEN: TDDState.COMMIT,
            TDDState.REFACTOR: TDDState.COMMIT,
            TDDState.COMMIT: TDDState.COMMIT,
        },
        "/tdd run_tests": {
            # Can run tests in any state for validation
            TDDState.DESIGN: TDDState.DESIGN,
            TDDState.TEST_RED: TDDState.TEST_RED,
            TDDState.CODE_GREEN: TDDState.CODE_GREEN,
            TDDState.REFACTOR: TDDState.REFACTOR,
            TDDState.COMMIT: TDDState.COMMIT,
        },
        "/tdd commit-tests": {
            # Commit failing tests to repo (TEST_RED → CODE_GREEN)
            TDDState.TEST_RED: TDDState.CODE_GREEN,
        },
        "/tdd commit-code": {
            # Commit implementation with tests (CODE_GREEN → REFACTOR or COMMIT)
            TDDState.CODE_GREEN: TDDState.REFACTOR,
        },
        "/tdd commit-refactor": {
            # Commit refactored code with tests (REFACTOR → COMMIT)
            TDDState.REFACTOR: TDDState.COMMIT,
        },
    }
    
    # Error messages and hints for invalid transitions
    ERROR_HINTS: Dict[Tuple[str, TDDState], str] = {
        ("/tdd test", TDDState.CODE_GREEN): "Tests already written. Use /tdd run_tests to verify or /tdd refactor to improve.",
        ("/tdd test", TDDState.REFACTOR): "Already in refactor phase. Use /tdd run_tests or /tdd commit.",
        ("/tdd code", TDDState.DESIGN): "Write failing tests first with /tdd test.",
        ("/tdd code", TDDState.REFACTOR): "Already implemented. Use /tdd refactor to improve or /tdd commit.",
        ("/tdd refactor", TDDState.DESIGN): "Need to write tests and implement code first.",
        ("/tdd refactor", TDDState.TEST_RED): "Make tests pass first with /tdd code.",
        ("/tdd commit", TDDState.DESIGN): "Complete the TDD cycle first (design → test → code).",
        ("/tdd commit", TDDState.TEST_RED): "Make tests pass first with /tdd code.",
        ("/tdd commit-tests", TDDState.DESIGN): "Write failing tests first with /tdd test.",
        ("/tdd commit-tests", TDDState.CODE_GREEN): "Tests already committed. Use /tdd commit-code to commit implementation.",
        ("/tdd commit-tests", TDDState.REFACTOR): "Tests already committed. Use /tdd commit-refactor to commit refactored code.",
        ("/tdd commit-tests", TDDState.COMMIT): "Tests already committed. Start new cycle with /tdd start.",
        ("/tdd commit-code", TDDState.DESIGN): "Write and commit tests first.",
        ("/tdd commit-code", TDDState.TEST_RED): "Tests not committed yet. Use /tdd commit-tests first.",
        ("/tdd commit-code", TDDState.REFACTOR): "Code already committed. Use /tdd commit-refactor for refactored code.",
        ("/tdd commit-code", TDDState.COMMIT): "Code already committed. Start new cycle with /tdd start.",
        ("/tdd commit-refactor", TDDState.DESIGN): "Complete TDD cycle first (design → test → code → refactor).",
        ("/tdd commit-refactor", TDDState.TEST_RED): "Write code to make tests pass first.",
        ("/tdd commit-refactor", TDDState.CODE_GREEN): "Code not committed yet. Use /tdd commit-code first.",
        ("/tdd commit-refactor", TDDState.COMMIT): "Refactoring already committed. Start new cycle with /tdd start.",
    }
    
    # Required conditions for state transitions
    TRANSITION_CONDITIONS: Dict[str, Dict[TDDState, List[str]]] = {
        "/tdd code": {
            TDDState.TEST_RED: ["has_failing_tests"],  # Must have failing tests to implement
        },
        "/tdd refactor": {
            TDDState.CODE_GREEN: ["has_passing_tests"],  # Must have passing tests to refactor
        },
        "/tdd commit": {
            TDDState.CODE_GREEN: ["has_passing_tests"],
            TDDState.REFACTOR: ["has_passing_tests"],
        },
        "/tdd commit-tests": {
            TDDState.TEST_RED: ["has_failing_tests", "has_test_files"],
        },
        "/tdd commit-code": {
            TDDState.CODE_GREEN: ["has_passing_tests", "has_committed_tests"],
        },
        "/tdd commit-refactor": {
            TDDState.REFACTOR: ["has_passing_tests", "has_committed_tests"],
        },
    }
    
    def __init__(
        self, 
        initial_state: TDDState = TDDState.DESIGN,
        enable_parallel_execution: bool = False,
        enable_resource_locking: bool = False,
        enable_coordination_events: bool = False,
        resource_lock_timeout: int = 300  # 5 minutes default
    ):
        # Sequential execution state (legacy compatibility)
        self.current_state = initial_state
        self.active_cycle: Optional[TDDCycle] = None
        
        # Parallel execution features
        self.enable_parallel_execution = enable_parallel_execution
        self.enable_resource_locking = enable_resource_locking
        self.enable_coordination_events = enable_coordination_events
        self.resource_lock_timeout = resource_lock_timeout
        
        # Parallel state tracking
        self.parallel_states: Dict[str, ParallelStateInfo] = {}  # cycle_id -> state info
        self.resource_locks: Dict[str, ResourceLock] = {}       # resource_id -> lock
        self.coordination_events: Dict[str, CoordinationEvent] = {}  # event_id -> event
        self.cycle_dependencies: Dict[str, Set[str]] = {}       # cycle_id -> dependency cycle_ids
        
        # Event handlers and coordination
        self.coordination_handlers: Dict[str, Callable] = {}
        self._coordination_lock = threading.Lock()
        
        # Performance metrics
        self.parallel_metrics = {
            "total_transitions": 0,
            "parallel_transitions": 0,
            "coordination_events": 0,
            "resource_conflicts": 0,
            "average_coordination_time": 0.0
        }
        
        logger.info(
            f"TDDStateMachine initialized: state={initial_state.value}, "
            f"parallel={enable_parallel_execution}, locking={enable_resource_locking}, "
            f"coordination={enable_coordination_events}"
        )
    
    def set_active_cycle(self, cycle: TDDCycle) -> None:
        """Set the active TDD cycle"""
        self.active_cycle = cycle
        if cycle:
            self.current_state = cycle.current_state
            logger.info(f"Active TDD cycle set: {cycle.id}, state: {cycle.current_state.value}")
    
    def validate_command(self, command: str, cycle: Optional[TDDCycle] = None) -> TDDCommandResult:
        """
        Validate if a TDD command is allowed in the current state.
        
        Args:
            command: The command to validate (e.g., "/tdd test", "/tdd code")
            cycle: Optional TDD cycle for context validation
            
        Returns:
            TDDCommandResult with validation outcome
        """
        # Use provided cycle or active cycle
        target_cycle = cycle or self.active_cycle
        current_state = target_cycle.current_state if target_cycle else self.current_state
        
        # Check if command exists in transition matrix
        if command not in self.TRANSITIONS:
            return TDDCommandResult(
                success=False,
                error_message=f"Unknown TDD command: {command}",
                hint="Use /tdd status to see available commands"
            )
        
        # Check if command is allowed in current state
        allowed_states = self.TRANSITIONS[command]
        if current_state not in allowed_states:
            hint = self.ERROR_HINTS.get((command, current_state))
            if not hint:
                # Generate generic hint
                valid_states = ", ".join([s.value for s in allowed_states.keys()])
                hint = f"Try when in states: {valid_states}"
            
            return TDDCommandResult(
                success=False,
                error_message=f"Command {command} not allowed in TDD state {current_state.value}",
                hint=hint
            )
        
        # Check transition conditions if any
        if command in self.TRANSITION_CONDITIONS:
            state_conditions = self.TRANSITION_CONDITIONS[command].get(current_state, [])
            if state_conditions and target_cycle:
                current_task = target_cycle.get_current_task()
                if current_task:
                    for condition in state_conditions:
                        if not self._check_condition(condition, current_task):
                            return TDDCommandResult(
                                success=False,
                                error_message=f"Condition not met for {command}: {condition}",
                                hint=self._get_condition_hint(condition, current_task)
                            )
        
        new_state = allowed_states[current_state]
        return TDDCommandResult(success=True, new_state=new_state)
    
    def transition(self, command: str, cycle: Optional[TDDCycle] = None, project_name: str = "default") -> TDDCommandResult:
        """
        Execute a TDD state transition if the command is valid.
        
        Args:
            command: The command to execute
            cycle: Optional TDD cycle for state updates
            project_name: Name of the project for broadcasting
            
        Returns:
            TDDCommandResult with transition outcome
        """
        result = self.validate_command(command, cycle)
        
        if result.success and result.new_state:
            # Use provided cycle or active cycle
            target_cycle = cycle or self.active_cycle
            old_state = target_cycle.current_state if target_cycle else self.current_state
            
            # Update state
            if target_cycle:
                target_cycle.current_state = result.new_state
                # Update current task state if exists
                current_task = target_cycle.get_current_task()
                if current_task:
                    current_task.current_state = result.new_state
            
            self.current_state = result.new_state
            logger.info(f"TDD state transition: {old_state.value} → {self.current_state.value} via {command}")
            
            # Emit TDD transition for real-time visualization
            try:
                story_id = target_cycle.story_id if target_cycle else "unknown"
                emit_tdd_transition(story_id, old_state, self.current_state, project_name)
            except Exception as e:
                logger.warning(f"Failed to emit TDD transition: {e}")
        
        return result
    
    def get_allowed_commands(self, cycle: Optional[TDDCycle] = None) -> List[str]:
        """Get list of TDD commands allowed in current state"""
        target_cycle = cycle or self.active_cycle
        current_state = target_cycle.current_state if target_cycle else self.current_state
        
        allowed = []
        
        # Add commands from transition matrix
        for command, states in self.TRANSITIONS.items():
            if current_state in states:
                # Check transition conditions
                if command in self.TRANSITION_CONDITIONS:
                    state_conditions = self.TRANSITION_CONDITIONS[command].get(current_state, [])
                    if state_conditions and target_cycle:
                        current_task = target_cycle.get_current_task()
                        if current_task and all(self._check_condition(cond, current_task) for cond in state_conditions):
                            allowed.append(command)
                        elif not current_task:
                            allowed.append(command)  # Allow if no current task
                    else:
                        allowed.append(command)
                else:
                    allowed.append(command)
        
        return sorted(allowed)
    
    def get_next_suggested_command(self, cycle: Optional[TDDCycle] = None) -> Optional[str]:
        """Get the next suggested command based on current state and conditions"""
        target_cycle = cycle or self.active_cycle
        current_state = target_cycle.current_state if target_cycle else self.current_state
        
        # Suggest next logical command in TDD cycle based on test preservation workflow
        suggestions = {
            TDDState.DESIGN: "/tdd test",
            TDDState.TEST_RED: "/tdd commit-tests",  # Commit failing tests first
            TDDState.CODE_GREEN: "/tdd commit-code",  # Commit implementation 
            TDDState.REFACTOR: "/tdd commit-refactor",  # Commit refactored code
            TDDState.COMMIT: "/tdd start"  # Start next task or complete
        }
        
        suggested = suggestions.get(current_state)
        if suggested and suggested in self.get_allowed_commands(cycle):
            return suggested
        
        return "/tdd next"  # Fallback to auto-advance
    
    def get_state_info(self, cycle: Optional[TDDCycle] = None) -> Dict[str, Any]:
        """Get comprehensive TDD state information for debugging"""
        target_cycle = cycle or self.active_cycle
        current_state = target_cycle.current_state if target_cycle else self.current_state
        
        info = {
            "current_state": current_state.value,
            "allowed_commands": self.get_allowed_commands(cycle),
            "next_suggested": self.get_next_suggested_command(cycle),
            "all_states": [s.value for s in TDDState],
            "has_active_cycle": self.active_cycle is not None,
            "transition_matrix": {
                cmd: {s.value: target.value for s, target in states.items()}
                for cmd, states in self.TRANSITIONS.items()
            }
        }
        
        if target_cycle:
            info.update({
                "cycle_id": target_cycle.id,
                "story_id": target_cycle.story_id,
                "current_task_id": target_cycle.current_task_id,
                "cycle_progress": target_cycle.get_progress_summary()
            })
        
        return info
    
    def _check_condition(self, condition: str, task: TDDTask) -> bool:
        """Check if a transition condition is met"""
        if condition == "has_failing_tests":
            return task.has_failing_tests()
        elif condition == "has_passing_tests":
            return task.has_passing_tests()
        elif condition == "has_test_files":
            return len(task.test_file_objects) > 0
        elif condition == "has_committed_tests":
            return len(task.get_committed_test_files()) > 0
        else:
            logger.warning(f"Unknown condition: {condition}")
            return True  # Default to allowing transition
    
    def _get_condition_hint(self, condition: str, task: TDDTask) -> str:
        """Get helpful hint for unmet condition"""
        if condition == "has_failing_tests":
            if not task.test_results:
                return "Write and run tests first using /tdd test and /tdd run_tests"
            elif not task.has_failing_tests():
                return "Tests are passing. Write more specific tests or ensure they fail initially"
        elif condition == "has_passing_tests":
            if not task.test_results:
                return "No test results found. Run tests with /tdd run_tests"
            elif task.has_failing_tests():
                return "Tests are still failing. Fix implementation until tests pass"
        elif condition == "has_test_files":
            return "No test files found. Create test files using /tdd test"
        elif condition == "has_committed_tests":
            if not task.test_file_objects:
                return "No test files found. Create and commit test files first"
            else:
                return "Test files not committed yet. Use /tdd commit-tests to commit them"
        
        return f"Condition '{condition}' not met"
    
    def get_mermaid_diagram(self) -> str:
        """Generate Mermaid state diagram for TDD workflow visualization"""
        return '''
```mermaid
%%{init: {'theme': 'dark'}}%%
stateDiagram-v2
    [*] --> DESIGN
    DESIGN --> DESIGN : /tdd design
    DESIGN --> TEST_RED : /tdd test
    TEST_RED --> TEST_RED : /tdd test
    TEST_RED --> CODE_GREEN : /tdd commit-tests
    CODE_GREEN --> CODE_GREEN : /tdd code
    CODE_GREEN --> REFACTOR : /tdd commit-code
    CODE_GREEN --> COMMIT : /tdd commit
    REFACTOR --> REFACTOR : /tdd refactor
    REFACTOR --> COMMIT : /tdd commit-refactor
    COMMIT --> DESIGN : /tdd next (new task)
    COMMIT --> [*] : cycle complete
    
    note right of DESIGN : Create specs & acceptance criteria
    note right of TEST_RED : Write failing tests (preserved in repo)
    note right of CODE_GREEN : Implement minimal code (tests committed)
    note right of REFACTOR : Improve code quality (code committed)
    note right of COMMIT : Save progress (refactoring committed)
```
        '''.strip()
    
    def reset(self) -> None:
        """Reset state machine to initial state"""
        self.current_state = TDDState.DESIGN
        self.active_cycle = None
        logger.info("TDD state machine reset to DESIGN state")
    
    def can_auto_progress(self, cycle: Optional[TDDCycle] = None) -> bool:
        """Check if state machine can automatically progress to next state"""
        target_cycle = cycle or self.active_cycle
        if not target_cycle:
            return False
        
        current_task = target_cycle.get_current_task()
        if not current_task:
            return False
        
        # Can auto-progress if conditions are met for next state
        current_state = target_cycle.current_state
        next_command = self.get_next_suggested_command(cycle)
        
        if next_command:
            result = self.validate_command(next_command, cycle)
            return result.success
        
        return False
    
    # Parallel Execution Methods
    
    def register_parallel_cycle(self, cycle: TDDCycle) -> None:
        """Register a TDD cycle for parallel execution tracking"""
        if not self.enable_parallel_execution:
            logger.warning("Parallel execution not enabled")
            return
        
        parallel_info = ParallelStateInfo(
            cycle_id=cycle.id,
            story_id=cycle.story_id,
            current_state=cycle.current_state
        )
        
        self.parallel_states[cycle.id] = parallel_info
        logger.info(f"Registered parallel cycle {cycle.id} in state {cycle.current_state.value}")
    
    def unregister_parallel_cycle(self, cycle_id: str) -> None:
        """Unregister a TDD cycle from parallel tracking"""
        if cycle_id in self.parallel_states:
            # Release any resource locks
            self._release_cycle_resources(cycle_id)
            
            # Remove from tracking
            del self.parallel_states[cycle_id]
            
            # Clean up dependencies
            if cycle_id in self.cycle_dependencies:
                del self.cycle_dependencies[cycle_id]
            
            # Remove from other cycles' dependencies
            for deps in self.cycle_dependencies.values():
                deps.discard(cycle_id)
            
            logger.info(f"Unregistered parallel cycle {cycle_id}")
    
    def validate_parallel_command(
        self, 
        command: str, 
        cycle: TDDCycle,
        requested_resources: Optional[List[str]] = None
    ) -> TDDCommandResult:
        """
        Validate command in parallel execution context.
        
        Args:
            command: TDD command to validate
            cycle: TDD cycle requesting the command
            requested_resources: Resources required for the command
            
        Returns:
            TDDCommandResult with parallel-specific validation
        """
        # First perform standard validation
        result = self.validate_command(command, cycle)
        
        if not result.success or not self.enable_parallel_execution:
            return result
        
        # Parallel-specific validation
        cycle_id = cycle.id
        
        # Check if cycle is registered for parallel execution
        if cycle_id not in self.parallel_states:
            result.success = False
            result.error_message = f"Cycle {cycle_id} not registered for parallel execution"
            return result
        
        # Check resource availability if resource locking is enabled
        if self.enable_resource_locking and requested_resources:
            resource_conflicts = self._check_resource_conflicts(cycle_id, requested_resources)
            if resource_conflicts:
                result.success = False
                result.error_message = f"Resource conflicts detected: {resource_conflicts}"
                result.requires_coordination = True
                result.affected_resources = resource_conflicts
                return result
        
        # Check for coordination requirements
        coordination_required = self._check_coordination_requirements(cycle_id, command)
        if coordination_required:
            result.requires_coordination = True
            result.coordination_events = coordination_required
        
        return result
    
    def execute_parallel_transition(
        self, 
        command: str, 
        cycle: TDDCycle,
        requested_resources: Optional[List[str]] = None,
        project_name: str = "default"
    ) -> TDDCommandResult:
        """
        Execute TDD state transition in parallel context.
        
        Args:
            command: TDD command to execute
            cycle: TDD cycle executing the command
            requested_resources: Resources to lock for the command
            project_name: Project name for broadcasting
            
        Returns:
            TDDCommandResult with parallel execution outcome
        """
        if not self.enable_parallel_execution:
            return self.transition(command, cycle, project_name)
        
        # Validate parallel command
        result = self.validate_parallel_command(command, cycle, requested_resources)
        
        if not result.success:
            return result
        
        cycle_id = cycle.id
        
        with self._coordination_lock:
            # Acquire resource locks if needed
            if self.enable_resource_locking and requested_resources:
                locks_acquired = self._acquire_resource_locks(cycle_id, requested_resources)
                if not locks_acquired:
                    result.success = False
                    result.error_message = "Failed to acquire required resource locks"
                    return result
            
            # Execute the transition
            old_state = cycle.current_state
            transition_result = self.transition(command, cycle, project_name)
            
            if transition_result.success:
                # Update parallel state tracking
                if cycle_id in self.parallel_states:
                    parallel_info = self.parallel_states[cycle_id]
                    parallel_info.current_state = cycle.current_state
                    parallel_info.last_transition = datetime.utcnow()
                    
                    # Add locked resources
                    if requested_resources:
                        parallel_info.locked_resources.update(requested_resources)
                
                # Emit coordination events if needed
                if self.enable_coordination_events:
                    self._emit_coordination_events(cycle_id, old_state, cycle.current_state, command)
                
                # Update metrics
                self.parallel_metrics["total_transitions"] += 1
                self.parallel_metrics["parallel_transitions"] += 1
                
                # Check for automatic coordination
                self._handle_automatic_coordination(cycle_id, cycle.current_state)
        
        return transition_result
    
    def add_cycle_dependency(self, cycle_id: str, dependency_cycle_id: str) -> bool:
        """
        Add a dependency between cycles.
        
        Args:
            cycle_id: Cycle that depends on another
            dependency_cycle_id: Cycle that must complete first
            
        Returns:
            True if dependency added successfully, False if it would create a cycle
        """
        # Check for circular dependencies
        if self._would_create_dependency_cycle(cycle_id, dependency_cycle_id):
            logger.warning(f"Cannot add dependency {cycle_id} -> {dependency_cycle_id}: would create cycle")
            return False
        
        if cycle_id not in self.cycle_dependencies:
            self.cycle_dependencies[cycle_id] = set()
        
        self.cycle_dependencies[cycle_id].add(dependency_cycle_id)
        logger.info(f"Added dependency: {cycle_id} depends on {dependency_cycle_id}")
        return True
    
    def check_cycle_dependencies(self, cycle_id: str) -> List[str]:
        """
        Check which dependencies are still blocking a cycle.
        
        Args:
            cycle_id: Cycle to check dependencies for
            
        Returns:
            List of dependency cycle IDs that are still active
        """
        if cycle_id not in self.cycle_dependencies:
            return []
        
        blocking_dependencies = []
        
        for dep_cycle_id in self.cycle_dependencies[cycle_id]:
            # Check if dependency cycle is still active
            if dep_cycle_id in self.parallel_states:
                dep_state = self.parallel_states[dep_cycle_id].current_state
                # Consider cycle blocking if not yet committed
                if dep_state != TDDState.COMMIT:
                    blocking_dependencies.append(dep_cycle_id)
        
        return blocking_dependencies
    
    def get_parallel_status(self) -> Dict[str, Any]:
        """Get comprehensive parallel execution status"""
        if not self.enable_parallel_execution:
            return {"parallel_execution": False}
        
        parallel_cycles = []
        for cycle_id, info in self.parallel_states.items():
            parallel_cycles.append({
                "cycle_id": cycle_id,
                "story_id": info.story_id,
                "current_state": info.current_state.value,
                "locked_resources": list(info.locked_resources),
                "parallel_cycles": list(info.parallel_cycles),
                "last_transition": info.last_transition.isoformat(),
                "is_coordinated": info.is_coordinated
            })
        
        return {
            "parallel_execution": True,
            "resource_locking": self.enable_resource_locking,
            "coordination_events": self.enable_coordination_events,
            "active_cycles": len(self.parallel_states),
            "parallel_cycles": parallel_cycles,
            "resource_locks": len(self.resource_locks),
            "coordination_events_count": len(self.coordination_events),
            "cycle_dependencies": {
                cycle_id: list(deps) for cycle_id, deps in self.cycle_dependencies.items()
            },
            "metrics": self.parallel_metrics
        }
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get resource locking status"""
        if not self.enable_resource_locking:
            return {"resource_locking": False}
        
        active_locks = []
        expired_locks = []
        current_time = datetime.utcnow()
        
        for resource_id, lock in self.resource_locks.items():
            lock_info = {
                "resource_id": resource_id,
                "cycle_id": lock.cycle_id,
                "story_id": lock.story_id,
                "lock_type": lock.lock_type,
                "locked_at": lock.locked_at.isoformat(),
                "expires_at": lock.expires_at.isoformat() if lock.expires_at else None
            }
            
            if lock.expires_at and current_time > lock.expires_at:
                expired_locks.append(lock_info)
            else:
                active_locks.append(lock_info)
        
        return {
            "resource_locking": True,
            "active_locks": active_locks,
            "expired_locks": expired_locks,
            "total_locks": len(self.resource_locks),
            "lock_timeout_seconds": self.resource_lock_timeout
        }
    
    def cleanup_expired_resources(self) -> int:
        """Clean up expired resource locks"""
        if not self.enable_resource_locking:
            return 0
        
        current_time = datetime.utcnow()
        expired_resources = []
        
        for resource_id, lock in self.resource_locks.items():
            if lock.expires_at and current_time > lock.expires_at:
                expired_resources.append(resource_id)
        
        # Remove expired locks
        for resource_id in expired_resources:
            self._release_resource_lock(resource_id)
        
        if expired_resources:
            logger.info(f"Cleaned up {len(expired_resources)} expired resource locks")
        
        return len(expired_resources)
    
    # Private parallel execution methods
    
    def _check_resource_conflicts(self, cycle_id: str, requested_resources: List[str]) -> List[str]:
        """Check for resource conflicts with other cycles"""
        conflicts = []
        
        for resource_id in requested_resources:
            if resource_id in self.resource_locks:
                existing_lock = self.resource_locks[resource_id]
                if existing_lock.cycle_id != cycle_id and existing_lock.lock_type == "exclusive":
                    conflicts.append(resource_id)
        
        return conflicts
    
    def _check_coordination_requirements(self, cycle_id: str, command: str) -> List[str]:
        """Check if command requires coordination with other cycles"""
        coordination_events = []
        
        # Commands that typically require coordination
        coordination_commands = ["/tdd commit", "/tdd commit-tests", "/tdd commit-code", "/tdd commit-refactor"]
        
        if command in coordination_commands:
            # Check for cycles working on same story or dependent stories
            if cycle_id in self.parallel_states:
                current_info = self.parallel_states[cycle_id]
                
                for other_cycle_id, other_info in self.parallel_states.items():
                    if other_cycle_id != cycle_id:
                        # Same story coordination
                        if other_info.story_id == current_info.story_id:
                            coordination_events.append(f"same_story_coordination_{other_cycle_id}")
                        
                        # Dependency coordination
                        if other_cycle_id in self.cycle_dependencies.get(cycle_id, set()):
                            coordination_events.append(f"dependency_coordination_{other_cycle_id}")
        
        return coordination_events
    
    def _acquire_resource_locks(self, cycle_id: str, resources: List[str]) -> bool:
        """Acquire resource locks for a cycle"""
        # Check if all resources are available
        for resource_id in resources:
            if resource_id in self.resource_locks:
                existing_lock = self.resource_locks[resource_id]
                if existing_lock.cycle_id != cycle_id:
                    return False
        
        # Acquire locks
        current_time = datetime.utcnow()
        expires_at = current_time + timedelta(seconds=self.resource_lock_timeout)
        
        for resource_id in resources:
            if resource_id not in self.resource_locks:
                # Get cycle info for story_id
                story_id = "unknown"
                if cycle_id in self.parallel_states:
                    story_id = self.parallel_states[cycle_id].story_id
                
                lock = ResourceLock(
                    resource_id=resource_id,
                    cycle_id=cycle_id,
                    story_id=story_id,
                    lock_type="exclusive",
                    locked_at=current_time,
                    expires_at=expires_at
                )
                
                self.resource_locks[resource_id] = lock
        
        return True
    
    def _release_resource_lock(self, resource_id: str) -> None:
        """Release a specific resource lock"""
        if resource_id in self.resource_locks:
            lock = self.resource_locks[resource_id]
            del self.resource_locks[resource_id]
            
            # Update parallel state info
            if lock.cycle_id in self.parallel_states:
                self.parallel_states[lock.cycle_id].locked_resources.discard(resource_id)
    
    def _release_cycle_resources(self, cycle_id: str) -> None:
        """Release all resource locks for a cycle"""
        resources_to_release = []
        
        for resource_id, lock in self.resource_locks.items():
            if lock.cycle_id == cycle_id:
                resources_to_release.append(resource_id)
        
        for resource_id in resources_to_release:
            self._release_resource_lock(resource_id)
    
    def _emit_coordination_events(
        self, 
        cycle_id: str, 
        old_state: TDDState, 
        new_state: TDDState, 
        command: str
    ) -> None:
        """Emit coordination events for state transition"""
        event_id = str(uuid.uuid4())
        
        event = CoordinationEvent(
            event_id=event_id,
            event_type="state_change",
            source_cycle=cycle_id,
            event_data={
                "old_state": old_state.value,
                "new_state": new_state.value,
                "command": command
            }
        )
        
        # Find target cycles that need to be notified
        if cycle_id in self.parallel_states:
            current_info = self.parallel_states[cycle_id]
            
            for other_cycle_id, other_info in self.parallel_states.items():
                if other_cycle_id != cycle_id:
                    # Notify cycles working on same story
                    if other_info.story_id == current_info.story_id:
                        event.target_cycles.add(other_cycle_id)
                    
                    # Notify dependent cycles
                    if cycle_id in self.cycle_dependencies.get(other_cycle_id, set()):
                        event.target_cycles.add(other_cycle_id)
        
        self.coordination_events[event_id] = event
        self.parallel_metrics["coordination_events"] += 1
        
        # Emit for monitoring
        try:
            emit_parallel_status({
                "event_type": "coordination_event",
                "event_id": event_id,
                "source_cycle": cycle_id,
                "target_cycles": list(event.target_cycles),
                "state_transition": f"{old_state.value} -> {new_state.value}"
            })
        except Exception as e:
            logger.warning(f"Failed to emit coordination event: {e}")
    
    def _handle_automatic_coordination(self, cycle_id: str, new_state: TDDState) -> None:
        """Handle automatic coordination based on state transitions"""
        # Check if any blocked cycles can now proceed
        for blocked_cycle_id, deps in self.cycle_dependencies.items():
            if cycle_id in deps:
                # Check if this transition unblocks the dependent cycle
                if new_state == TDDState.COMMIT:
                    remaining_deps = self.check_cycle_dependencies(blocked_cycle_id)
                    if not remaining_deps:
                        logger.info(f"Cycle {blocked_cycle_id} is now unblocked")
                        
                        # Emit unblocked event
                        if self.enable_coordination_events:
                            event_id = str(uuid.uuid4())
                            event = CoordinationEvent(
                                event_id=event_id,
                                event_type="cycle_unblocked",
                                source_cycle=cycle_id,
                                target_cycles={blocked_cycle_id},
                                event_data={"unblocked_cycle": blocked_cycle_id}
                            )
                            self.coordination_events[event_id] = event
    
    def _would_create_dependency_cycle(self, cycle_id: str, dependency_cycle_id: str) -> bool:
        """Check if adding a dependency would create a circular dependency"""
        # Simple DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            # Check existing dependencies
            for neighbor in self.cycle_dependencies.get(node, set()):
                if has_cycle(neighbor):
                    return True
            
            # Check the new dependency we're trying to add
            if node == dependency_cycle_id and cycle_id in self.cycle_dependencies.get(node, set()):
                return True
            
            rec_stack.remove(node)
            return False
        
        # Test from the dependency cycle to see if it can reach back to the original cycle
        return has_cycle(dependency_cycle_id)