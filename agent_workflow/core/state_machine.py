"""
State machine module for agent-workflow package.

This module provides finite state machines for both main workflow management
and TDD cycle management, enforcing proper transitions and command sequencing.
"""

import logging
import json
import uuid
import asyncio
import threading
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

# Import models
try:
    from .models import TDDState, TDDCycle, TDDTask, TestResult, TestStatus
except ImportError:
    # Fallback for imports when models module not available
    from agent_workflow.core.models import TDDState, TDDCycle, TDDTask, TestResult, TestStatus

# Import state broadcaster for real-time visualization
try:
    from .state_broadcaster import emit_workflow_transition, emit_tdd_transition, emit_parallel_status
except ImportError:
    # Graceful fallback if broadcaster is not available
    def emit_workflow_transition(old_state, new_state, project_name="default"):
        pass
    
    def emit_tdd_transition(story_id, old_state, new_state, project_name="default"):
        pass
    
    def emit_parallel_status(status_data):
        pass

logger = logging.getLogger(__name__)


# Main Workflow States
class State(Enum):
    """Workflow states for agent orchestration."""
    IDLE = "IDLE"
    BACKLOG_READY = "BACKLOG_READY"
    SPRINT_PLANNED = "SPRINT_PLANNED"
    SPRINT_ACTIVE = "SPRINT_ACTIVE"
    SPRINT_PAUSED = "SPRINT_PAUSED"
    SPRINT_REVIEW = "SPRINT_REVIEW"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"
    PAUSED = "PAUSED"


@dataclass
class CommandResult:
    """Result of command validation and execution"""
    success: bool
    new_state: Optional[State] = None
    error_message: Optional[str] = None
    hint: Optional[str] = None


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


class Transition:
    """Represents a state transition with validation."""
    
    def __init__(self, from_state: State, to_state: State, command: str, 
                 conditions: Optional[List[str]] = None):
        """
        Initialize a transition.
        
        Args:
            from_state: Starting state
            to_state: Target state
            command: Command that triggers transition
            conditions: Optional conditions that must be met
        """
        self.from_state = from_state
        self.to_state = to_state
        self.command = command
        self.conditions = conditions or []
    
    def can_transition(self, context: Dict[str, Any]) -> bool:
        """
        Check if transition is valid given current context.
        
        Args:
            context: Current execution context
            
        Returns:
            True if transition is allowed
        """
        # Check conditions
        for condition in self.conditions:
            if not self._check_condition(condition, context):
                return False
        return True
    
    def _check_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Check a specific condition."""
        if condition == "has_backlog":
            return bool(context.get("backlog_items", []))
        elif condition == "has_active_sprint":
            return bool(context.get("active_sprint"))
        elif condition == "sprint_complete":
            return context.get("sprint_status") == "complete"
        elif condition == "has_stories":
            return bool(context.get("stories", []))
        else:
            logger.warning(f"Unknown condition: {condition}")
            return True


class StateMachine:
    """
    Finite state machine that enforces proper command sequencing
    according to the research-mode Scrum workflow with TDD integration.
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
        """Initialize the state machine with TDD integration."""
        self.current_state = initial_state
        self.state_history = [initial_state]
        self.transitions = self._define_transitions()
        self.context = {}
        
        # TDD integration
        self.active_tdd_cycles: Dict[str, str] = {}  # story_id -> cycle_id mapping
        self.tdd_cycles: Dict[str, Dict[str, Any]] = {}  # cycle_id -> cycle data
        self.tdd_transition_listeners: List[Callable] = []
        self.tdd_state_machine: Dict[str, str] = {}  # cycle_id -> current TDD state
        
        # TDD state machine instance
        self.tdd_sm = TDDStateMachine()
        
        logger.info(f"StateMachine initialized in state: {initial_state.value}")
    
    def _define_transitions(self) -> Dict[str, Transition]:
        """Define all valid state transitions."""
        transitions = [
            # From IDLE
            Transition(State.IDLE, State.BACKLOG_READY, "create_backlog"),
            Transition(State.IDLE, State.BACKLOG_READY, "add_story"),
            Transition(State.IDLE, State.ERROR, "error"),
            
            # From BACKLOG_READY
            Transition(State.BACKLOG_READY, State.SPRINT_PLANNED, "plan_sprint", ["has_stories"]),
            Transition(State.BACKLOG_READY, State.BACKLOG_READY, "add_story"),
            Transition(State.BACKLOG_READY, State.BACKLOG_READY, "prioritize_backlog"),
            Transition(State.BACKLOG_READY, State.IDLE, "clear_backlog"),
            Transition(State.BACKLOG_READY, State.ERROR, "error"),
            
            # From SPRINT_PLANNED
            Transition(State.SPRINT_PLANNED, State.SPRINT_ACTIVE, "start_sprint"),
            Transition(State.SPRINT_PLANNED, State.BACKLOG_READY, "cancel_sprint"),
            Transition(State.SPRINT_PLANNED, State.SPRINT_PLANNED, "modify_sprint"),
            Transition(State.SPRINT_PLANNED, State.ERROR, "error"),
            
            # From SPRINT_ACTIVE
            Transition(State.SPRINT_ACTIVE, State.SPRINT_REVIEW, "complete_sprint"),
            Transition(State.SPRINT_ACTIVE, State.PAUSED, "pause_sprint"),
            Transition(State.SPRINT_ACTIVE, State.SPRINT_ACTIVE, "update_task"),
            Transition(State.SPRINT_ACTIVE, State.SPRINT_ACTIVE, "approve_task"),
            Transition(State.SPRINT_ACTIVE, State.ERROR, "error"),
            
            # From SPRINT_REVIEW
            Transition(State.SPRINT_REVIEW, State.BACKLOG_READY, "finish_review"),
            Transition(State.SPRINT_REVIEW, State.SPRINT_PLANNED, "plan_next_sprint"),
            Transition(State.SPRINT_REVIEW, State.IDLE, "end_project"),
            Transition(State.SPRINT_REVIEW, State.ERROR, "error"),
            
            # From PAUSED
            Transition(State.PAUSED, State.SPRINT_ACTIVE, "resume_sprint"),
            Transition(State.PAUSED, State.BACKLOG_READY, "cancel_sprint"),
            Transition(State.PAUSED, State.ERROR, "error"),
            
            # From ERROR
            Transition(State.ERROR, State.IDLE, "reset"),
            Transition(State.ERROR, State.BACKLOG_READY, "recover_to_backlog"),
            Transition(State.ERROR, State.SPRINT_ACTIVE, "recover_to_sprint"),
        ]
        
        # Convert to lookup dictionary
        transition_dict = {}
        for transition in transitions:
            key = f"{transition.from_state.value}:{transition.command}"
            transition_dict[key] = transition
        
        return transition_dict
    
    def validate_command(self, command: str, context: Optional[Dict] = None) -> CommandResult:
        """
        Validate if a command is allowed in the current state.
        
        Args:
            command: The command to validate (e.g., "/epic", "/sprint start")
            context: Optional validation context
            
        Returns:
            CommandResult with validation outcome
        """
        # Extract base command for validation
        base_command = command.split()[0] if command.strip() else ""
        
        logger.debug(f"Validating command '{command}' (base: '{base_command}') in state {self.current_state.value}")
        
        # Handle backlog commands specially
        if any(base_command.startswith(bc) for bc in self.BACKLOG_COMMANDS):
            if self.current_state == State.SPRINT_REVIEW:
                return CommandResult(
                    success=False,
                    error_message=f"Backlog modifications not allowed during sprint review",
                    hint="Complete sprint review with /feedback or /request_changes first"
                )
            return CommandResult(success=True, new_state=self.current_state)
        
        # Check if base command exists in transition matrix
        if base_command not in self.TRANSITIONS:
            # Check if it's a TDD command
            if base_command.startswith("/tdd"):
                # Forward to TDD state machine
                tdd_result = self.tdd_sm.validate_command(base_command)
                return CommandResult(
                    success=tdd_result.success,
                    error_message=tdd_result.error_message,
                    hint=tdd_result.hint
                )
            
            return CommandResult(
                success=False,
                error_message=f"Unknown command: {base_command}",
                hint="Use /state to see available commands"
            )
        
        # Check if base command is allowed in current state
        allowed_states = self.TRANSITIONS[base_command]
        if self.current_state not in allowed_states:
            hint = self.ERROR_HINTS.get((base_command, self.current_state))
            if not hint:
                # Generate generic hint
                valid_states = ", ".join([s.value for s in allowed_states.keys()])
                hint = f"Try when in states: {valid_states}"
            
            return CommandResult(
                success=False,
                error_message=f"Command {base_command} not allowed in state {self.current_state.value}",
                hint=hint
            )
        
        new_state = allowed_states[self.current_state]
        
        # Apply context-aware validation
        if context:
            context_result = self._validate_transition_context(base_command, new_state, context)
            if not context_result.success:
                return context_result
        
        return CommandResult(success=True, new_state=new_state)
    
    def _validate_transition_context(self, command: str, target_state: State, context: Dict) -> CommandResult:
        """Apply context-aware validation rules"""
        # Validate TDD cycle constraints
        if target_state in [State.SPRINT_REVIEW, State.IDLE] and self.has_active_tdd_cycles():
            if not context.get("force_transition", False):
                return CommandResult(
                    success=False,
                    error_message=f"Cannot transition to {target_state.value} with active TDD cycles",
                    hint="Complete active TDD cycles or use force_transition=True in context"
                )
        
        # Validate pending work constraints
        if command == "/sprint start" and context.get("has_uncommitted_changes", False):
            return CommandResult(
                success=False,
                error_message="Cannot start sprint with uncommitted changes",
                hint="Commit or stash pending changes before starting sprint"
            )
        
        # Validate CI status constraints
        if target_state == State.SPRINT_ACTIVE and context.get("ci_status") == "failing":
            return CommandResult(
                success=False,
                error_message="Cannot start sprint with failing CI",
                hint="Fix CI failures before starting sprint"
            )
        
        return CommandResult(success=True)
    
    def transition(self, command: str, project_name: str = "default") -> CommandResult:
        """
        Execute a state transition if the command is valid.
        
        Args:
            command: The command to execute
            project_name: Name of the project for broadcasting
            
        Returns:
            CommandResult with transition outcome
        """
        result = self.validate_command(command)
        
        if result.success and result.new_state:
            old_state = self.current_state
            self.current_state = result.new_state
            
            # Use base command for cleaner logging
            base_command = command.split()[0] if command.strip() else command
            logger.info(f"State transition: {old_state.value} → {self.current_state.value} via {base_command}")
            
            # Track transition history
            self._track_transition_minimal(old_state, self.current_state, command)
            
            # Emit workflow transition for real-time visualization
            try:
                emit_workflow_transition(old_state, self.current_state, project_name)
            except Exception as e:
                logger.warning(f"Failed to emit workflow transition: {e}")
        
        return result
    
    def execute_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Execute a command and transition state if valid.
        
        Args:
            command: Command to execute
            context: Optional execution context
            
        Returns:
            True if command was executed successfully
        """
        if not self.can_execute_command(command, context):
            logger.warning(f"Invalid command '{command}' in state {self.current_state.value}")
            return False
        
        # Get transition
        key = f"{self.current_state.value}:{command}"
        transition = self.transitions[key]
        
        # Execute transition
        old_state = self.current_state
        self.current_state = transition.to_state
        self.state_history.append(self.current_state)
        
        # Update context
        if context:
            self.context.update(context)
        
        logger.info(f"State transition: {old_state.value} -> {self.current_state.value} (command: {command})")
        
        return True
    
    def can_execute_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a command can be executed in the current state.
        
        Args:
            command: Command to check
            context: Optional execution context
            
        Returns:
            True if command is valid in current state
        """
        key = f"{self.current_state.value}:{command}"
        transition = self.transitions.get(key)
        
        if not transition:
            return False
        
        # Merge context
        exec_context = self.context.copy()
        if context:
            exec_context.update(context)
        
        return transition.can_transition(exec_context)
    
    def _track_transition_minimal(self, old_state: State, new_state: State, command: str) -> None:
        """Minimal transition tracking for history and debugging"""
        if not hasattr(self, '_transition_history'):
            self._transition_history = []
        
        self._transition_history.append({
            "timestamp": datetime.now().isoformat(),
            "from": old_state.value,
            "to": new_state.value,
            "command": command
        })
        
        # Keep only last 20 transitions to prevent memory growth
        if len(self._transition_history) > 20:
            self._transition_history.pop(0)
    
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
        
        # Add TDD commands if in appropriate state
        if self.current_state in [State.SPRINT_ACTIVE, State.SPRINT_PAUSED]:
            allowed.extend(self.tdd_sm.get_allowed_commands())
        
        return sorted(allowed)
    
    def get_valid_commands(self, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Get list of valid commands for current state.
        
        Args:
            context: Optional execution context
            
        Returns:
            List of valid command names
        """
        valid_commands = []
        
        for key, transition in self.transitions.items():
            state_str, command = key.split(':', 1)
            
            if state_str == self.current_state.value:
                exec_context = self.context.copy()
                if context:
                    exec_context.update(context)
                
                if transition.can_transition(exec_context):
                    valid_commands.append(command)
        
        return valid_commands
    
    def get_state_info(self, include_matrix: bool = False) -> Dict:
        """Get comprehensive state information for debugging"""
        base_info = {
            "current_state": self.current_state.value,
            "allowed_commands": self.get_allowed_commands(),
            "valid_commands": self.get_valid_commands(),
            "state_history": [state.value for state in self.state_history[-10:]],
            "context": self.context.copy(),
            "timestamp": datetime.now().isoformat(),
            "tdd_integration": {
                "active_cycles": len(self.active_tdd_cycles),
                "cycle_ids": list(self.active_tdd_cycles.keys()),
                "can_transition_to_review": not self.has_active_tdd_cycles()
            },
            "state_flags": {
                "is_terminal": self.is_terminal_state(),
                "can_auto_progress": self.can_auto_progress(),
                "has_active_work": bool(self.active_tdd_cycles)
            }
        }
        
        # Include expensive transition matrix only when requested
        if include_matrix:
            base_info.update({
                "all_states": [s.value for s in State],
                "transition_matrix": {
                    cmd: {s.value: target.value for s, target in states.items()}
                    for cmd, states in self.TRANSITIONS.items()
                }
            })
        
        # Include recent transition history if available
        if hasattr(self, '_transition_history'):
            base_info["recent_transitions"] = self._transition_history[-5:]  # Last 5 transitions
        
        return base_info
    
    def force_state(self, state: State, reason: str = "manual") -> None:
        """Force transition to specific state (for testing/recovery)"""
        old_state = self.current_state
        self.current_state = state
        logger.warning(f"Forced state transition: {old_state.value} → {state.value} (reason: {reason})")
        
        # Track this as a transition for history
        self._track_transition_minimal(old_state, state, f"force_state:{reason}")
    
    def get_transition_history(self, limit: int = 10) -> List[Dict]:
        """Get recent transition history for debugging and analysis"""
        if not hasattr(self, '_transition_history'):
            return []
        
        return self._transition_history[-limit:] if limit > 0 else self._transition_history
    
    def get_recovery_options(self) -> List[Dict]:
        """Get available recovery options based on state history"""
        if not hasattr(self, '_transition_history') or not self._transition_history:
            return [{"state": State.IDLE.value, "reason": "fallback_to_idle"}]
        
        # Return unique recent states as recovery options
        recent_states = []
        seen_states = set()
        for transition in reversed(self._transition_history[-5:]):  # Last 5 transitions
            state = transition["from"]
            if state not in seen_states and state != self.current_state.value:
                seen_states.add(state)
                recent_states.append({
                    "state": state,
                    "timestamp": transition["timestamp"],
                    "reason": f"recover_from_{transition['command']}"
                })
        
        return recent_states[:3]  # Top 3 recovery options
    
    def is_terminal_state(self) -> bool:
        """Check if current state requires external input to progress"""
        return self.current_state in [State.BLOCKED, State.SPRINT_REVIEW]
    
    def can_auto_progress(self) -> bool:
        """Check if state machine can automatically progress"""
        return self.current_state in [State.SPRINT_ACTIVE]
    
    def reset(self, new_state: State = State.IDLE) -> None:
        """
        Reset state machine to specified state.
        
        Args:
            new_state: State to reset to
        """
        old_state = self.current_state
        self.current_state = new_state
        self.state_history.append(new_state)
        self.context.clear()
        
        logger.info(f"State machine reset: {old_state.value} -> {new_state.value}")
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """
        Update execution context.
        
        Args:
            updates: Context updates to apply
        """
        self.context.update(updates)
        logger.debug(f"Context updated: {updates}")
    
    def get_transition_diagram(self) -> str:
        """
        Generate a text representation of the state machine.
        
        Returns:
            String diagram of states and transitions
        """
        lines = ["State Machine Diagram:", ""]
        
        # Group transitions by from_state
        state_transitions = {}
        for transition in self.transitions.values():
            from_state = transition.from_state.value
            if from_state not in state_transitions:
                state_transitions[from_state] = []
            state_transitions[from_state].append(transition)
        
        # Generate diagram
        for state in State:
            state_name = state.value
            current_marker = " <- CURRENT" if state == self.current_state else ""
            lines.append(f"[{state_name}]{current_marker}")
            
            if state_name in state_transitions:
                for transition in state_transitions[state_name]:
                    conditions_str = ""
                    if transition.conditions:
                        conditions_str = f" (requires: {', '.join(transition.conditions)})"
                    lines.append(f"  --{transition.command}--> {transition.to_state.value}{conditions_str}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def validate_workflow(self) -> List[str]:
        """
        Validate the state machine configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check that all states have at least one outgoing transition
        states_with_transitions = set()
        for transition in self.transitions.values():
            states_with_transitions.add(transition.from_state)
        
        for state in State:
            if state not in states_with_transitions and state != State.ERROR:
                errors.append(f"State {state.value} has no outgoing transitions")
        
        # Check for unreachable states
        reachable_states = {State.IDLE}  # IDLE is always reachable (initial state)
        changed = True
        while changed:
            changed = False
            for transition in self.transitions.values():
                if transition.from_state in reachable_states and transition.to_state not in reachable_states:
                    reachable_states.add(transition.to_state)
                    changed = True
        
        for state in State:
            if state not in reachable_states:
                errors.append(f"State {state.value} is unreachable")
        
        return errors
    
    # TDD Integration Methods
    
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
    
    def add_tdd_transition_listener(self, listener: Callable) -> None:
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
        tdd_cycle_details = {}
        for cycle_id, cycle_data in self.tdd_cycles.items():
            tdd_cycle_details[cycle_id] = {
                "story_id": cycle_data.get("story_id", ""),
                "current_state": cycle_data.get("current_state", TDDState.DESIGN),
                "progress": cycle_data.get("progress", {}),
                "last_updated": cycle_data.get("last_updated", datetime.now().isoformat())
            }
        
        return {
            "main_workflow_state": self.current_state.value,
            "active_tdd_cycles": len(self.active_tdd_cycles),
            "tdd_cycles_by_story": self.active_tdd_cycles,
            "tdd_cycle_details": tdd_cycle_details,
            "can_transition_to_review": not self.has_active_tdd_cycles(),
            "sprint_tdd_coordination": {
                "blocking_sprint_review": self.current_state == State.SPRINT_ACTIVE and self.has_active_tdd_cycles(),
                "sprint_allows_tdd": self.current_state in [State.SPRINT_ACTIVE, State.SPRINT_PAUSED]
            },
            "tdd_constraints": self.get_tdd_constraints()
        }
    
    def start_tdd_cycle(self, story_id: str, cycle_id: Optional[str] = None, project_name: str = "default") -> str:
        """Start a new TDD cycle for a story"""
        if not cycle_id:
            cycle_id = f"tdd-cycle-{story_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Initialize TDD cycle data
        cycle_data = {
            "story_id": story_id,
            "current_state": TDDState.DESIGN,
            "tasks": [],
            "current_task_id": None,
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "progress": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "test_runs": 0,
                "commits": 0
            }
        }
        
        # Register the cycle
        self.active_tdd_cycles[story_id] = cycle_id
        self.tdd_cycles[cycle_id] = cycle_data
        self.tdd_state_machine[cycle_id] = TDDState.DESIGN
        
        # Emit TDD transition event
        emit_tdd_transition(story_id, None, TDDState.DESIGN, project_name)
        
        logger.info(f"Started TDD cycle {cycle_id} for story {story_id}")
        return cycle_id
    
    def transition_tdd_cycle(self, cycle_id: str, new_state: str, project_name: str = "default") -> bool:
        """Transition a TDD cycle to a new state"""
        if cycle_id not in self.tdd_cycles:
            logger.error(f"TDD cycle {cycle_id} not found")
            return False
        
        # Validate TDD state transition
        valid_transitions = {
            TDDState.DESIGN: [TDDState.TEST_RED],
            TDDState.TEST_RED: [TDDState.CODE_GREEN, TDDState.DESIGN],
            TDDState.CODE_GREEN: [TDDState.REFACTOR, TDDState.COMMIT, TDDState.TEST_RED],
            TDDState.REFACTOR: [TDDState.COMMIT, TDDState.TEST_RED],
            TDDState.COMMIT: [TDDState.DESIGN]  # Can start next task or complete cycle
        }
        
        current_state = self.tdd_state_machine.get(cycle_id, TDDState.DESIGN)
        
        # Allow transition if valid or if it's a string state
        if isinstance(new_state, str):
            # Convert string to TDD state if possible
            try:
                new_tdd_state = getattr(TDDState, new_state.upper())
            except AttributeError:
                # Try with exact value match
                for state in [TDDState.DESIGN, TDDState.TEST_RED, TDDState.CODE_GREEN, TDDState.REFACTOR, TDDState.COMMIT]:
                    if state == new_state:
                        new_tdd_state = state
                        break
                else:
                    logger.error(f"Invalid TDD state: {new_state}")
                    return False
        else:
            new_tdd_state = new_state
        
        # Update cycle state
        old_state = current_state
        self.tdd_state_machine[cycle_id] = new_tdd_state
        self.tdd_cycles[cycle_id]["current_state"] = new_tdd_state
        self.tdd_cycles[cycle_id]["last_updated"] = datetime.now().isoformat()
        
        # Get story ID for emission
        story_id = self.tdd_cycles[cycle_id]["story_id"]
        
        # Emit TDD transition event
        emit_tdd_transition(story_id, old_state, new_tdd_state, project_name)
        
        # Notify listeners
        self.notify_tdd_transition({
            "cycle_id": cycle_id,
            "story_id": story_id,
            "old_state": old_state,
            "new_state": new_tdd_state,
            "timestamp": datetime.now().isoformat(),
            "project": project_name
        })
        
        logger.info(f"TDD cycle {cycle_id} transitioned: {old_state} → {new_tdd_state}")
        return True
    
    def complete_tdd_cycle(self, cycle_id: str, project_name: str = "default") -> bool:
        """Complete a TDD cycle and remove it from active cycles"""
        if cycle_id not in self.tdd_cycles:
            logger.error(f"TDD cycle {cycle_id} not found")
            return False
        
        cycle_data = self.tdd_cycles[cycle_id]
        story_id = cycle_data["story_id"]
        
        # Mark as completed
        cycle_data["completed_at"] = datetime.now().isoformat()
        cycle_data["current_state"] = TDDState.COMMIT
        
        # Remove from active cycles
        if story_id in self.active_tdd_cycles:
            del self.active_tdd_cycles[story_id]
        
        # Keep in tdd_cycles for history but remove from state machine
        if cycle_id in self.tdd_state_machine:
            del self.tdd_state_machine[cycle_id]
        
        # Emit completion event
        emit_tdd_transition(story_id, TDDState.COMMIT, None, project_name)
        
        logger.info(f"Completed TDD cycle {cycle_id} for story {story_id}")
        return True
    
    def get_tdd_cycle_data(self, cycle_id: str) -> Optional[Dict[str, Any]]:
        """Get TDD cycle data by cycle ID"""
        return self.tdd_cycles.get(cycle_id)
    
    def get_active_tdd_cycle_for_story(self, story_id: str) -> Optional[str]:
        """Get active TDD cycle ID for a story"""
        return self.active_tdd_cycles.get(story_id)
    
    def get_tdd_constraints(self) -> Dict[str, Any]:
        """Get TDD-related constraints for workflow transitions"""
        constraints = {
            "has_active_cycles": self.has_active_tdd_cycles(),
            "blocking_states": [],
            "allowed_transitions": []
        }
        
        if self.has_active_tdd_cycles():
            if self.current_state == State.SPRINT_ACTIVE:
                constraints["blocking_states"].append("SPRINT_REVIEW")
                constraints["allowed_transitions"] = ["SPRINT_PAUSED", "BLOCKED"]
            else:
                constraints["allowed_transitions"] = ["SPRINT_ACTIVE"]
        
        return constraints
    
    def update_tdd_cycle_progress(self, cycle_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update progress data for a TDD cycle"""
        if cycle_id not in self.tdd_cycles:
            return False
        
        cycle_data = self.tdd_cycles[cycle_id]
        cycle_data["progress"].update(progress_data)
        cycle_data["last_updated"] = datetime.now().isoformat()
        
        return True
    
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