"""
State machine module for agent-workflow package.

This module provides the finite state machine that enforces proper
workflow transitions and command sequencing.
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class State(Enum):
    """Workflow states for agent orchestration."""
    IDLE = "IDLE"
    BACKLOG_READY = "BACKLOG_READY"
    SPRINT_PLANNED = "SPRINT_PLANNED"
    SPRINT_ACTIVE = "SPRINT_ACTIVE"
    SPRINT_REVIEW = "SPRINT_REVIEW"
    ERROR = "ERROR"
    PAUSED = "PAUSED"


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
    Finite state machine for workflow management.
    
    Enforces proper state transitions and validates commands
    based on current workflow state.
    """
    
    def __init__(self, initial_state: State = State.IDLE):
        """
        Initialize the state machine.
        
        Args:
            initial_state: Starting state
        """
        self.current_state = initial_state
        self.state_history = [initial_state]
        self.transitions = self._define_transitions()
        self.context = {}
        
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
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get comprehensive state information.
        
        Returns:
            Dictionary with state details
        """
        return {
            "current_state": self.current_state.value,
            "valid_commands": self.get_valid_commands(),
            "state_history": [state.value for state in self.state_history],
            "context": self.context.copy(),
            "timestamp": datetime.now().isoformat()
        }
    
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