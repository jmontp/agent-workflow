"""
TDD State Machine for Test-Driven Development Workflow.

Implements a finite state machine that governs TDD cycle transitions
and validates TDD command sequences according to TDD best practices.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
try:
    from .tdd_models import TDDState, TDDCycle, TDDTask, TestResult, TestStatus
except ImportError:
    from tdd_models import TDDState, TDDCycle, TDDTask, TestResult, TestStatus

# Import state broadcaster for real-time visualization
try:
    from .state_broadcaster import emit_tdd_transition
except ImportError:
    # Graceful fallback if broadcaster is not available
    def emit_tdd_transition(story_id, old_state, new_state, project_name="default"):
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


class TDDStateMachine:
    """
    Finite state machine that enforces proper TDD command sequencing
    according to Test-Driven Development best practices.
    
    States:
    - DESIGN: Create detailed specifications and acceptance criteria
    - TEST_RED: Write failing tests based on specifications  
    - CODE_GREEN: Implement minimal code to make tests pass
    - REFACTOR: Improve code quality while keeping tests green
    - COMMIT: Save progress and mark task complete
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
    
    def __init__(self, initial_state: TDDState = TDDState.DESIGN):
        self.current_state = initial_state
        self.active_cycle: Optional[TDDCycle] = None
        logger.info(f"TDDStateMachine initialized in state: {initial_state.value}")
    
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