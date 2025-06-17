"""
State Machine for AI Agent TDD-Scrum Workflow

Implements the finite state machine that governs command transitions
and validates user interactions according to the workflow specification.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class State(Enum):
    """Workflow states as defined in command_state_machine.md"""
    IDLE = "IDLE"
    BACKLOG_READY = "BACKLOG_READY" 
    SPRINT_PLANNED = "SPRINT_PLANNED"
    SPRINT_ACTIVE = "SPRINT_ACTIVE"
    SPRINT_PAUSED = "SPRINT_PAUSED"
    SPRINT_REVIEW = "SPRINT_REVIEW"
    BLOCKED = "BLOCKED"


@dataclass
class CommandResult:
    """Result of command validation and execution"""
    success: bool
    new_state: Optional[State] = None
    error_message: Optional[str] = None
    hint: Optional[str] = None


class StateMachine:
    """
    Finite state machine that enforces proper command sequencing
    according to the research-mode Scrum workflow.
    """
    
    # Command → State transition matrix
    TRANSITIONS: Dict[str, Dict[State, State]] = {
        "/epic": {
            State.IDLE: State.BACKLOG_READY,
            State.BACKLOG_READY: State.BACKLOG_READY,
        },
        "/approve": {
            State.BACKLOG_READY: State.BACKLOG_READY,
        },
        "/sprint plan": {
            State.BACKLOG_READY: State.SPRINT_PLANNED,
        },
        "/sprint start": {
            State.SPRINT_PLANNED: State.SPRINT_ACTIVE,
        },
        "/sprint status": {
            State.SPRINT_ACTIVE: State.SPRINT_ACTIVE,
            State.SPRINT_PAUSED: State.SPRINT_PAUSED,
            State.BLOCKED: State.BLOCKED,
        },
        "/sprint pause": {
            State.SPRINT_ACTIVE: State.SPRINT_PAUSED,
        },
        "/sprint resume": {
            State.SPRINT_PAUSED: State.SPRINT_ACTIVE,
        },
        "/request_changes": {
            State.SPRINT_REVIEW: State.BACKLOG_READY,
        },
        "/suggest_fix": {
            State.BLOCKED: State.SPRINT_ACTIVE,
        },
        "/skip_task": {
            State.BLOCKED: State.SPRINT_ACTIVE,
        },
        "/feedback": {
            State.SPRINT_REVIEW: State.IDLE,
        },
        "/state": {
            # Always allowed - introspection command
            State.IDLE: State.IDLE,
            State.BACKLOG_READY: State.BACKLOG_READY,
            State.SPRINT_PLANNED: State.SPRINT_PLANNED,
            State.SPRINT_ACTIVE: State.SPRINT_ACTIVE,
            State.SPRINT_PAUSED: State.SPRINT_PAUSED,
            State.SPRINT_REVIEW: State.SPRINT_REVIEW,
            State.BLOCKED: State.BLOCKED,
        },
    }
    
    # Backlog commands are always safe (except in SPRINT_REVIEW)
    BACKLOG_COMMANDS = ["/backlog view", "/backlog add_story", "/backlog prioritize", "/backlog remove"]
    
    # Error messages and hints for invalid transitions
    ERROR_HINTS: Dict[Tuple[str, State], str] = {
        ("/sprint plan", State.SPRINT_ACTIVE): "Sprint already active. Use /sprint status or /sprint pause.",
        ("/sprint start", State.SPRINT_ACTIVE): "Sprint already active. Use /sprint status.",
        ("/epic", State.SPRINT_ACTIVE): "Cannot create epic during active sprint. Use /sprint pause first.",
        ("/approve", State.SPRINT_ACTIVE): "No items pending approval. Use /sprint status.",
        ("/sprint start", State.IDLE): "No sprint planned. Use /epic then /sprint plan first.",
    }
    
    def __init__(self, initial_state: State = State.IDLE):
        self.current_state = initial_state
        self.active_tdd_cycles: Dict[str, str] = {}  # story_id -> cycle_id mapping
        self.tdd_transition_listeners: List[callable] = []
        logger.info(f"StateMachine initialized in state: {initial_state.value}")
    
    def validate_command(self, command: str) -> CommandResult:
        """
        Validate if a command is allowed in the current state.
        
        Args:
            command: The command to validate (e.g., "/epic", "/sprint start")
            
        Returns:
            CommandResult with validation outcome
        """
        # Handle backlog commands specially
        if any(command.startswith(bc) for bc in self.BACKLOG_COMMANDS):
            if self.current_state == State.SPRINT_REVIEW:
                return CommandResult(
                    success=False,
                    error_message=f"Backlog modifications not allowed during sprint review",
                    hint="Complete sprint review with /feedback or /request_changes first"
                )
            return CommandResult(success=True, new_state=self.current_state)
        
        # Check if command exists in transition matrix
        if command not in self.TRANSITIONS:
            return CommandResult(
                success=False,
                error_message=f"Unknown command: {command}",
                hint="Use /state to see available commands"
            )
        
        # Check if command is allowed in current state
        allowed_states = self.TRANSITIONS[command]
        if self.current_state not in allowed_states:
            hint = self.ERROR_HINTS.get((command, self.current_state))
            if not hint:
                # Generate generic hint
                valid_states = ", ".join([s.value for s in allowed_states.keys()])
                hint = f"Try when in states: {valid_states}"
            
            return CommandResult(
                success=False,
                error_message=f"Command {command} not allowed in state {self.current_state.value}",
                hint=hint
            )
        
        new_state = allowed_states[self.current_state]
        return CommandResult(success=True, new_state=new_state)
    
    def transition(self, command: str) -> CommandResult:
        """
        Execute a state transition if the command is valid.
        
        Args:
            command: The command to execute
            
        Returns:
            CommandResult with transition outcome
        """
        result = self.validate_command(command)
        
        if result.success and result.new_state:
            old_state = self.current_state
            self.current_state = result.new_state
            logger.info(f"State transition: {old_state.value} → {self.current_state.value} via {command}")
        
        return result
    
    def get_allowed_commands(self) -> List[str]:
        """Get list of commands allowed in current state"""
        allowed = []
        
        # Add commands from transition matrix
        for command, states in self.TRANSITIONS.items():
            if self.current_state in states:
                allowed.append(command)
        
        # Add backlog commands (except in SPRINT_REVIEW)
        if self.current_state != State.SPRINT_REVIEW:
            allowed.extend(self.BACKLOG_COMMANDS)
        
        return sorted(allowed)
    
    def get_state_info(self) -> Dict:
        """Get comprehensive state information for debugging"""
        return {
            "current_state": self.current_state.value,
            "allowed_commands": self.get_allowed_commands(),
            "all_states": [s.value for s in State],
            "transition_matrix": {
                cmd: {s.value: target.value for s, target in states.items()}
                for cmd, states in self.TRANSITIONS.items()
            }
        }
    
    def force_state(self, state: State) -> None:
        """Force transition to specific state (for testing/recovery)"""
        old_state = self.current_state
        self.current_state = state
        logger.warning(f"Forced state transition: {old_state.value} → {state.value}")
    
    def is_terminal_state(self) -> bool:
        """Check if current state requires external input to progress"""
        return self.current_state in [State.BLOCKED, State.SPRINT_REVIEW]
    
    def can_auto_progress(self) -> bool:
        """Check if state machine can automatically progress"""
        return self.current_state in [State.SPRINT_ACTIVE]
    
    def register_tdd_cycle(self, story_id: str, cycle_id: str) -> None:
        """Register an active TDD cycle for a story"""
        self.active_tdd_cycles[story_id] = cycle_id
        logger.info(f"Registered TDD cycle {cycle_id} for story {story_id}")
    
    def unregister_tdd_cycle(self, story_id: str) -> None:
        """Unregister a TDD cycle when complete"""
        if story_id in self.active_tdd_cycles:
            cycle_id = self.active_tdd_cycles.pop(story_id)
            logger.info(f"Unregistered TDD cycle {cycle_id} for story {story_id}")
    
    def get_active_tdd_cycles(self) -> Dict[str, str]:
        """Get all active TDD cycles"""
        return self.active_tdd_cycles.copy()
    
    def has_active_tdd_cycles(self) -> bool:
        """Check if there are any active TDD cycles"""
        return len(self.active_tdd_cycles) > 0
    
    def add_tdd_transition_listener(self, listener: callable) -> None:
        """Add a listener for TDD state transitions"""
        self.tdd_transition_listeners.append(listener)
    
    def notify_tdd_transition(self, event_data: Dict) -> None:
        """Notify listeners of TDD state transitions"""
        for listener in self.tdd_transition_listeners:
            try:
                listener(event_data)
            except Exception as e:
                logger.error(f"Error in TDD transition listener: {e}")
    
    def validate_sprint_transition_with_tdd(self, target_state: State) -> CommandResult:
        """Validate sprint transitions considering active TDD cycles"""
        if target_state == State.SPRINT_REVIEW and self.has_active_tdd_cycles():
            active_cycles = list(self.active_tdd_cycles.values())
            return CommandResult(
                success=False,
                error_message=f"Cannot transition to SPRINT_REVIEW with active TDD cycles: {active_cycles}",
                hint="Complete or abort active TDD cycles before sprint review"
            )
        
        if target_state == State.IDLE and self.has_active_tdd_cycles():
            return CommandResult(
                success=False,
                error_message="Cannot transition to IDLE with active TDD cycles",
                hint="Complete or abort all TDD cycles before ending sprint"
            )
        
        return CommandResult(success=True)
    
    def get_tdd_workflow_status(self) -> Dict[str, Any]:
        """Get comprehensive TDD workflow status for the main state machine"""
        return {
            "main_workflow_state": self.current_state.value,
            "active_tdd_cycles": len(self.active_tdd_cycles),
            "tdd_cycles_by_story": self.active_tdd_cycles,
            "can_transition_to_review": not self.has_active_tdd_cycles(),
            "sprint_tdd_coordination": {
                "blocking_sprint_review": self.current_state == State.SPRINT_ACTIVE and self.has_active_tdd_cycles(),
                "sprint_allows_tdd": self.current_state in [State.SPRINT_ACTIVE, State.SPRINT_PAUSED]
            }
        }
    
    def get_mermaid_diagram(self) -> str:
        """Generate Mermaid state diagram for visualization"""
        active_tdd_info = f" ({len(self.active_tdd_cycles)} TDD cycles)" if self.has_active_tdd_cycles() else ""
        
        return f'''
```mermaid
%%{{init: {{'theme': 'dark'}}}}%%
stateDiagram-v2
    [*] --> IDLE
    IDLE --> BACKLOG_READY : /epic
    BACKLOG_READY --> BACKLOG_READY : /approve
    BACKLOG_READY --> SPRINT_PLANNED : /sprint plan
    SPRINT_PLANNED --> SPRINT_ACTIVE : /sprint start
    SPRINT_ACTIVE --> SPRINT_PAUSED : /sprint pause
    SPRINT_PAUSED --> SPRINT_ACTIVE : /sprint resume
    SPRINT_ACTIVE --> BLOCKED : CI fails 3×
    BLOCKED --> SPRINT_ACTIVE : /suggest_fix | /skip_task
    SPRINT_ACTIVE --> SPRINT_REVIEW : all tasks done (TDD complete)
    SPRINT_REVIEW --> BACKLOG_READY : /request_changes
    SPRINT_REVIEW --> IDLE : /feedback
    
    note right of SPRINT_ACTIVE : TDD cycles active{active_tdd_info}
    note right of SPRINT_REVIEW : Requires TDD completion
```
        '''.strip()