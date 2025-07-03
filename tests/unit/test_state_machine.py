"""
Unit tests for agent-workflow state machines.

This module tests both the main workflow state machine and the TDD state machine,
including all state transitions, command validations, and error handling.
"""

import unittest
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent_workflow.core.state_machine import (
    # Main workflow state machine
    StateMachine, State, CommandResult,
    # TDD state machine
    TDDStateMachine, TDDCommandResult, TDDState,
    # Supporting classes
    ParallelStateInfo, ResourceLock
)
from agent_workflow.core.models import (
    TDDCycle, TDDTask, TestResult, TestStatus, TestFile, TestFileStatus, CIStatus
)


class TestStateMachine(unittest.TestCase):
    """Comprehensive test suite for StateMachine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.state_machine = StateMachine()
    
    def test_initial_state(self):
        """Test state machine starts in IDLE state"""
        self.assertEqual(self.state_machine.current_state, State.IDLE)
    
    def test_valid_transitions(self):
        """Test all valid state transitions according to specification"""
        test_cases = [
            # (start_state, command, expected_end_state)
            (State.IDLE, "/epic", State.BACKLOG_READY),
            (State.BACKLOG_READY, "/epic", State.BACKLOG_READY),
            (State.BACKLOG_READY, "/approve", State.BACKLOG_READY),
            (State.BACKLOG_READY, "/sprint plan", State.SPRINT_PLANNED),
            (State.SPRINT_PLANNED, "/sprint start", State.SPRINT_ACTIVE),
            (State.SPRINT_ACTIVE, "/sprint status", State.SPRINT_ACTIVE),
            (State.SPRINT_ACTIVE, "/sprint pause", State.SPRINT_PAUSED),
            (State.SPRINT_PAUSED, "/sprint resume", State.SPRINT_ACTIVE),
            (State.SPRINT_PAUSED, "/sprint status", State.SPRINT_PAUSED),
            (State.BLOCKED, "/sprint status", State.BLOCKED),
            (State.BLOCKED, "/suggest_fix", State.SPRINT_ACTIVE),
            (State.BLOCKED, "/skip_task", State.SPRINT_ACTIVE),
            (State.SPRINT_REVIEW, "/request_changes", State.BACKLOG_READY),
            (State.SPRINT_REVIEW, "/feedback", State.IDLE),
        ]
        
        for start_state, command, expected_end_state in test_cases:
            with self.subTest(start_state=start_state, command=command):
                # Set initial state
                self.state_machine.force_state(start_state)
                
                # Execute transition
                result = self.state_machine.transition(command)
                
                # Verify successful transition
                self.assertTrue(result.success, f"Transition failed: {start_state} + {command}")
                self.assertEqual(self.state_machine.current_state, expected_end_state)
    
    def test_invalid_transitions(self):
        """Test invalid state transitions are properly rejected"""
        invalid_test_cases = [
            # (start_state, command, expected_error_hint)
            (State.IDLE, "/sprint start", "No sprint planned"),
            (State.IDLE, "/approve", None),
            (State.SPRINT_ACTIVE, "/sprint plan", "Sprint already active"),
            (State.SPRINT_ACTIVE, "/sprint start", "Sprint already active"),
            (State.SPRINT_ACTIVE, "/epic", None),
            (State.SPRINT_PLANNED, "/sprint pause", None),
            (State.SPRINT_PAUSED, "/sprint start", None),
            (State.BLOCKED, "/sprint plan", None),
            (State.SPRINT_REVIEW, "/sprint start", None),
        ]
        
        for start_state, command, expected_hint in invalid_test_cases:
            with self.subTest(start_state=start_state, command=command):
                # Set initial state
                self.state_machine.force_state(start_state)
                original_state = self.state_machine.current_state
                
                # Attempt invalid transition
                result = self.state_machine.transition(command)
                
                # Verify transition was rejected
                self.assertFalse(result.success, f"Invalid transition should fail: {start_state} + {command}")
                self.assertIsNotNone(result.error_message)
                self.assertEqual(self.state_machine.current_state, original_state)
                
                if expected_hint:
                    self.assertIn(expected_hint.lower(), result.hint.lower())
    
    def test_backlog_commands_always_allowed(self):
        """Test backlog commands are allowed in all states except SPRINT_REVIEW"""
        backlog_commands = ["/backlog view", "/backlog add_story", "/backlog prioritize"]
        allowed_states = [
            State.IDLE, State.BACKLOG_READY, State.SPRINT_PLANNED,
            State.SPRINT_ACTIVE, State.SPRINT_PAUSED, State.BLOCKED
        ]
        
        for state in allowed_states:
            for command in backlog_commands:
                with self.subTest(state=state, command=command):
                    self.state_machine.force_state(state)
                    result = self.state_machine.validate_command(command)
                    self.assertTrue(result.success, f"Backlog command should be allowed: {state} + {command}")
    
    def test_backlog_commands_blocked_in_review(self):
        """Test backlog commands are blocked during SPRINT_REVIEW"""
        backlog_commands = ["/backlog view", "/backlog add_story", "/backlog prioritize"]
        
        self.state_machine.force_state(State.SPRINT_REVIEW)
        
        for command in backlog_commands:
            with self.subTest(command=command):
                result = self.state_machine.validate_command(command)
                self.assertFalse(result.success, f"Backlog command should be blocked in SPRINT_REVIEW: {command}")
                self.assertIn("review", result.error_message.lower())
    
    def test_state_command_always_allowed(self):
        """Test /state command is allowed in all states"""
        all_states = list(State)
        
        for state in all_states:
            with self.subTest(state=state):
                self.state_machine.force_state(state)
                result = self.state_machine.validate_command("/state")
                self.assertTrue(result.success, f"/state should be allowed in {state}")
                self.assertEqual(result.new_state, state)  # No state change
    
    def test_unknown_command(self):
        """Test unknown commands are properly rejected"""
        unknown_commands = ["/unknown", "/invalid", "/not_a_command"]
        
        for command in unknown_commands:
            with self.subTest(command=command):
                result = self.state_machine.validate_command(command)
                self.assertFalse(result.success)
                self.assertIn("Unknown command", result.error_message)
                self.assertIn("/state", result.hint)
    
    def test_get_allowed_commands(self):
        """Test get_allowed_commands returns correct commands for each state"""
        expected_commands = {
            State.IDLE: ["/epic", "/state"] + ["/backlog view", "/backlog add_story", "/backlog prioritize", "/backlog remove"],
            State.BACKLOG_READY: ["/approve", "/epic", "/sprint plan", "/state"] + ["/backlog view", "/backlog add_story", "/backlog prioritize", "/backlog remove"],
            State.SPRINT_PLANNED: ["/sprint start", "/state"] + ["/backlog view", "/backlog add_story", "/backlog prioritize", "/backlog remove"],
            State.SPRINT_ACTIVE: ["/sprint pause", "/sprint status", "/state"] + ["/backlog view", "/backlog add_story", "/backlog prioritize", "/backlog remove"],
            State.SPRINT_PAUSED: ["/sprint resume", "/sprint status", "/state"] + ["/backlog view", "/backlog add_story", "/backlog prioritize", "/backlog remove"],
            State.BLOCKED: ["/skip_task", "/sprint status", "/state", "/suggest_fix"] + ["/backlog view", "/backlog add_story", "/backlog prioritize", "/backlog remove"],
            State.SPRINT_REVIEW: ["/feedback", "/request_changes", "/state"],  # No backlog commands
        }
        
        for state, expected in expected_commands.items():
            with self.subTest(state=state):
                self.state_machine.force_state(state)
                allowed = self.state_machine.get_allowed_commands()
                
                # Convert to sets for comparison (order doesn't matter)
                allowed_set = set(allowed)
                expected_set = set(expected)
                
                self.assertEqual(allowed_set, expected_set, f"Allowed commands mismatch for {state}")
    
    def test_state_info(self):
        """Test get_state_info returns comprehensive state information"""
        self.state_machine.force_state(State.SPRINT_ACTIVE)
        
        info = self.state_machine.get_state_info(include_matrix=True)
        
        # Verify structure and content
        self.assertIn("current_state", info)
        self.assertIn("allowed_commands", info)
        self.assertIn("all_states", info)
        self.assertIn("transition_matrix", info)
        
        self.assertEqual(info["current_state"], "SPRINT_ACTIVE")
        self.assertIsInstance(info["allowed_commands"], list)
        self.assertIsInstance(info["all_states"], list)
        self.assertIsInstance(info["transition_matrix"], dict)
        
        # Verify all states are included
        expected_states = [s.value for s in State]
        self.assertEqual(set(info["all_states"]), set(expected_states))
    
    def test_force_state(self):
        """Test force_state allows arbitrary state transitions"""
        original_state = self.state_machine.current_state
        target_state = State.SPRINT_REVIEW
        
        self.state_machine.force_state(target_state)
        self.assertEqual(self.state_machine.current_state, target_state)
        
        # Verify it's different from original
        self.assertNotEqual(original_state, target_state)
    
    def test_terminal_states(self):
        """Test terminal state detection"""
        terminal_states = [State.BLOCKED, State.SPRINT_REVIEW]
        non_terminal_states = [State.IDLE, State.BACKLOG_READY, State.SPRINT_PLANNED, 
                              State.SPRINT_ACTIVE, State.SPRINT_PAUSED]
        
        for state in terminal_states:
            with self.subTest(state=state):
                self.state_machine.force_state(state)
                self.assertTrue(self.state_machine.is_terminal_state())
        
        for state in non_terminal_states:
            with self.subTest(state=state):
                self.state_machine.force_state(state)
                self.assertFalse(self.state_machine.is_terminal_state())
    
    def test_auto_progress_states(self):
        """Test auto-progress state detection"""
        auto_progress_states = [State.SPRINT_ACTIVE]
        non_auto_progress_states = [State.IDLE, State.BACKLOG_READY, State.SPRINT_PLANNED,
                                  State.SPRINT_PAUSED, State.BLOCKED, State.SPRINT_REVIEW]
        
        for state in auto_progress_states:
            with self.subTest(state=state):
                self.state_machine.force_state(state)
                self.assertTrue(self.state_machine.can_auto_progress())
        
        for state in non_auto_progress_states:
            with self.subTest(state=state):
                self.state_machine.force_state(state)
                self.assertFalse(self.state_machine.can_auto_progress())
    
    def test_mermaid_diagram_generation(self):
        """Test Mermaid diagram generation"""
        diagram = self.state_machine.get_mermaid_diagram()
        
        # Verify it's a valid Mermaid diagram
        self.assertIn("stateDiagram-v2", diagram)
        self.assertIn("IDLE", diagram)
        self.assertIn("SPRINT_ACTIVE", diagram)
        self.assertIn("SPRINT_REVIEW", diagram)
        
        # Verify key transitions are present
        self.assertIn("IDLE --> BACKLOG_READY", diagram)
        self.assertIn("SPRINT_PLANNED --> SPRINT_ACTIVE", diagram)
        self.assertIn("SPRINT_REVIEW --> IDLE", diagram)


class TestCommandResult(unittest.TestCase):
    """Test CommandResult data class"""
    
    def test_successful_result(self):
        """Test successful command result"""
        result = CommandResult(success=True, new_state=State.SPRINT_ACTIVE)
        
        self.assertTrue(result.success)
        self.assertEqual(result.new_state, State.SPRINT_ACTIVE)
        self.assertIsNone(result.error_message)
        self.assertIsNone(result.hint)
    
    def test_failed_result(self):
        """Test failed command result"""
        result = CommandResult(
            success=False,
            error_message="Invalid command",
            hint="Try /state command"
        )
        
        self.assertFalse(result.success)
        self.assertIsNone(result.new_state)
        self.assertEqual(result.error_message, "Invalid command")
        self.assertEqual(result.hint, "Try /state command")


class TestStateMachineEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.state_machine = StateMachine()
    
    def test_empty_command(self):
        """Test empty command handling"""
        result = self.state_machine.validate_command("")
        self.assertFalse(result.success)
        self.assertIn("Unknown command", result.error_message)
    
    def test_whitespace_command(self):
        """Test whitespace-only command handling"""
        result = self.state_machine.validate_command("   ")
        self.assertFalse(result.success)
        self.assertIn("Unknown command", result.error_message)
    
    def test_partial_command_matching(self):
        """Test partial command matching doesn't work"""
        partial_commands = ["/ep", "/spr", "/back"]
        
        for command in partial_commands:
            with self.subTest(command=command):
                result = self.state_machine.validate_command(command)
                self.assertFalse(result.success)
                self.assertIn("Unknown command", result.error_message)
    
    def test_case_sensitivity(self):
        """Test command case sensitivity"""
        # Commands should be case-sensitive (lowercase required)
        uppercase_commands = ["/EPIC", "/SPRINT START", "/APPROVE"]
        
        for command in uppercase_commands:
            with self.subTest(command=command):
                result = self.state_machine.validate_command(command)
                self.assertFalse(result.success)
                self.assertIn("Unknown command", result.error_message)


class TestStateMachineEdgeCases(unittest.TestCase):
    """Test edge cases and additional coverage for state machine"""
    
    def setUp(self):
        """Set up test environment"""
        self.state_machine = StateMachine()
    
    def test_state_broadcaster_integration(self):
        """Test state broadcaster integration (should not crash if not available)"""
        # Force state change to test broadcaster integration
        old_state = self.state_machine.current_state
        self.state_machine.force_state(State.BACKLOG_READY)
        
        # Should not raise exception even if broadcaster is mocked/unavailable
        result = self.state_machine.validate_command("/epic")
        self.assertTrue(result.success)
        
        # Verify transition was recorded (even if broadcast fails gracefully)
        self.assertEqual(self.state_machine.current_state, State.BACKLOG_READY)
    
    def test_command_result_creation(self):
        """Test CommandResult dataclass creation and attributes"""
        # Test successful command result
        success_result = CommandResult(
            success=True,
            new_state=State.BACKLOG_READY,
            error_message=None,
            hint=None
        )
        
        self.assertTrue(success_result.success)
        self.assertEqual(success_result.new_state, State.BACKLOG_READY)
        self.assertIsNone(success_result.error_message)
        self.assertIsNone(success_result.hint)
        
        # Test failure command result
        failure_result = CommandResult(
            success=False,
            new_state=None,
            error_message="Command failed",
            hint="Try using /state to see current state"
        )
        
        self.assertFalse(failure_result.success)
        self.assertIsNone(failure_result.new_state)
        self.assertEqual(failure_result.error_message, "Command failed")
        self.assertEqual(failure_result.hint, "Try using /state to see current state")
    
    def test_state_enum_completeness(self):
        """Test that State enum has all expected values"""
        expected_states = {
            "IDLE", "BACKLOG_READY", "SPRINT_PLANNED", 
            "SPRINT_ACTIVE", "SPRINT_PAUSED", "SPRINT_REVIEW", "BLOCKED"
        }
        
        actual_states = {state.value for state in State}
        self.assertEqual(actual_states, expected_states)
        
        # Test string representations
        for state in State:
            self.assertIsInstance(state.value, str)
            self.assertTrue(state.value.isupper())
    
    def test_transition_matrix_completeness(self):
        """Test that transition matrix covers all necessary transitions"""
        transitions = StateMachine.TRANSITIONS
        
        # Verify all commands have transition definitions
        essential_commands = [
            "/epic", "/approve", "/sprint plan", "/sprint start",
            "/sprint pause", "/sprint resume", "/sprint status",
            "/request_changes", "/suggest_fix", "/skip_task", "/feedback", "/state"
        ]
        
        for command in essential_commands:
            self.assertIn(command, transitions, f"Command {command} missing from transitions")
        
        # Verify state command exists for all states
        state_transitions = transitions["/state"]
        for state in State:
            self.assertIn(state, state_transitions, f"State command missing for {state}")
            # State command should not change state
            self.assertEqual(state_transitions[state], state)
    
    def test_backlog_commands_mapping(self):
        """Test backlog commands mapping and validation"""
        backlog_commands = StateMachine.BACKLOG_COMMANDS
        
        # Should be a list of strings
        self.assertIsInstance(backlog_commands, list)
        self.assertGreater(len(backlog_commands), 0)
        
        # All should be strings starting with /backlog
        for command in backlog_commands:
            self.assertIsInstance(command, str)
            self.assertTrue(command.startswith("/backlog"))
        
        # Test expected backlog commands are present
        expected_backlog = ["/backlog view", "/backlog add_story", "/backlog prioritize", "/backlog remove"]
        for expected in expected_backlog:
            self.assertIn(expected, backlog_commands)
    
    def test_error_message_quality(self):
        """Test that error messages are helpful and informative"""
        # Test unknown command error
        result = self.state_machine.validate_command("/unknown")
        self.assertFalse(result.success)
        self.assertIn("Unknown command", result.error_message)
        self.assertIsNotNone(result.hint)
        self.assertIn("/state", result.hint)
        
        # Test invalid transition error
        self.state_machine.force_state(State.IDLE)
        result = self.state_machine.validate_command("/sprint start")
        self.assertFalse(result.success)
        self.assertIn("not allowed", result.error_message.lower())
        self.assertIsNotNone(result.hint)
    
    def test_state_persistence_across_validations(self):
        """Test that state persists correctly across multiple validations"""
        initial_state = self.state_machine.current_state
        
        # Multiple state inspections should not change state
        for _ in range(5):
            result = self.state_machine.validate_command("/state")
            self.assertTrue(result.success)
            self.assertEqual(self.state_machine.current_state, initial_state)
        
        # Invalid commands should not change state
        for invalid_command in ["/unknown", "/invalid", ""]:
            result = self.state_machine.validate_command(invalid_command)
            self.assertFalse(result.success)
            self.assertEqual(self.state_machine.current_state, initial_state)
    
    def test_complex_workflow_sequences(self):
        """Test complex multi-step workflow sequences"""
        # Test complete workflow: IDLE -> BACKLOG_READY -> SPRINT_PLANNED -> SPRINT_ACTIVE -> SPRINT_REVIEW -> IDLE
        self.state_machine.force_state(State.IDLE)
        
        # Start epic
        result = self.state_machine.validate_command("/epic")
        self.assertTrue(result.success)
        self.assertEqual(result.new_state, State.BACKLOG_READY)
        self.state_machine.force_state(result.new_state)
        
        # Plan sprint
        result = self.state_machine.validate_command("/sprint plan")
        self.assertTrue(result.success)
        self.assertEqual(result.new_state, State.SPRINT_PLANNED)
        self.state_machine.force_state(result.new_state)
        
        # Start sprint
        result = self.state_machine.validate_command("/sprint start")
        self.assertTrue(result.success)
        self.assertEqual(result.new_state, State.SPRINT_ACTIVE)
        self.state_machine.force_state(result.new_state)
        
        # Pause and resume
        result = self.state_machine.validate_command("/sprint pause")
        self.assertTrue(result.success)
        self.assertEqual(result.new_state, State.SPRINT_PAUSED)
        self.state_machine.force_state(result.new_state)
        
        result = self.state_machine.validate_command("/sprint resume")
        self.assertTrue(result.success)
        self.assertEqual(result.new_state, State.SPRINT_ACTIVE)
        self.state_machine.force_state(result.new_state)
        
        # Test the full sequence completed successfully  
        self.assertEqual(self.state_machine.current_state, State.SPRINT_ACTIVE)


class TestStateMachineTDDIntegration(unittest.TestCase):
    """Test StateMachine TDD workflow integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.state_machine = StateMachine()
    
    def test_tdd_cycle_registration(self):
        """Test TDD cycle registration and tracking"""
        # Initially no active cycles
        assert not self.state_machine.has_active_tdd_cycles()
        assert len(self.state_machine.get_active_tdd_cycles()) == 0
        
        # Register TDD cycles
        self.state_machine.register_tdd_cycle("story-1", "cycle-1")
        self.state_machine.register_tdd_cycle("story-2", "cycle-2")
        
        # Verify registration
        assert self.state_machine.has_active_tdd_cycles()
        active_cycles = self.state_machine.get_active_tdd_cycles()
        assert len(active_cycles) == 2
        assert active_cycles["story-1"] == "cycle-1"
        assert active_cycles["story-2"] == "cycle-2"
        
        # Unregister one cycle
        self.state_machine.unregister_tdd_cycle("story-1")
        active_cycles = self.state_machine.get_active_tdd_cycles()
        assert len(active_cycles) == 1
        assert "story-1" not in active_cycles
        assert active_cycles["story-2"] == "cycle-2"
        
        # Unregister non-existent cycle (should not error)
        self.state_machine.unregister_tdd_cycle("story-nonexistent")
        assert len(self.state_machine.get_active_tdd_cycles()) == 1
    
    def test_sprint_transition_validation_with_tdd(self):
        """Test sprint transitions are blocked with active TDD cycles"""
        self.state_machine.force_state(State.SPRINT_ACTIVE)
        
        # Register active TDD cycle
        self.state_machine.register_tdd_cycle("story-1", "cycle-1")
        
        # Test transition to SPRINT_REVIEW blocked
        result = self.state_machine.validate_sprint_transition_with_tdd(State.SPRINT_REVIEW)
        assert not result.success
        assert "active TDD cycles" in result.error_message
        assert "cycle-1" in result.error_message
        
        # Test transition to IDLE blocked
        result = self.state_machine.validate_sprint_transition_with_tdd(State.IDLE)
        assert not result.success
        assert "active TDD cycles" in result.error_message
        
        # Test other transitions allowed
        result = self.state_machine.validate_sprint_transition_with_tdd(State.SPRINT_PAUSED)
        assert result.success
        
        # Unregister cycle and test transitions allowed
        self.state_machine.unregister_tdd_cycle("story-1")
        result = self.state_machine.validate_sprint_transition_with_tdd(State.SPRINT_REVIEW)
        assert result.success
    
    def test_tdd_workflow_status(self):
        """Test comprehensive TDD workflow status reporting"""
        self.state_machine.force_state(State.SPRINT_ACTIVE)
        
        # Initially no TDD cycles
        status = self.state_machine.get_tdd_workflow_status()
        assert status["main_workflow_state"] == "SPRINT_ACTIVE"
        assert status["active_tdd_cycles"] == 0
        assert status["tdd_cycles_by_story"] == {}
        assert status["can_transition_to_review"] is True
        assert not status["sprint_tdd_coordination"]["blocking_sprint_review"]
        assert status["sprint_tdd_coordination"]["sprint_allows_tdd"]
        
        # Add TDD cycles
        self.state_machine.register_tdd_cycle("story-1", "cycle-1")
        self.state_machine.register_tdd_cycle("story-2", "cycle-2")
        
        status = self.state_machine.get_tdd_workflow_status()
        assert status["active_tdd_cycles"] == 2
        assert status["can_transition_to_review"] is False
        assert status["sprint_tdd_coordination"]["blocking_sprint_review"]
        
        # Test in different states
        self.state_machine.force_state(State.SPRINT_PAUSED)
        status = self.state_machine.get_tdd_workflow_status()
        assert status["main_workflow_state"] == "SPRINT_PAUSED"
        assert status["sprint_tdd_coordination"]["sprint_allows_tdd"]
        assert not status["sprint_tdd_coordination"]["blocking_sprint_review"]
    
    def test_tdd_transition_listeners(self):
        """Test TDD transition listener system"""
        # Track listener calls
        listener_calls = []
        
        def test_listener(event_data):
            listener_calls.append(event_data)
        
        # Add listener
        self.state_machine.add_tdd_transition_listener(test_listener)
        
        # Notify transition
        event_data = {
            "story_id": "story-1",
            "cycle_id": "cycle-1",
            "old_state": "design",
            "new_state": "test_red",
            "timestamp": "2024-01-01T12:00:00"
        }
        
        self.state_machine.notify_tdd_transition(event_data)
        
        # Verify listener was called
        assert len(listener_calls) == 1
        assert listener_calls[0] == event_data
        
        # Test with multiple listeners
        listener_calls_2 = []
        def test_listener_2(event_data):
            listener_calls_2.append(event_data)
        
        self.state_machine.add_tdd_transition_listener(test_listener_2)
        
        event_data_2 = {"cycle_id": "cycle-2", "transition": "test"}
        self.state_machine.notify_tdd_transition(event_data_2)
        
        # Both listeners should be called
        assert len(listener_calls) == 2
        assert len(listener_calls_2) == 1
        
        # Test with failing listener (should not crash)
        def failing_listener(event_data):
            raise Exception("Listener error")
        
        self.state_machine.add_tdd_transition_listener(failing_listener)
        self.state_machine.notify_tdd_transition({"test": "data"})
        
        # Other listeners should still work
        assert len(listener_calls) == 3
    
    def test_mermaid_diagram_with_tdd_cycles(self):
        """Test Mermaid diagram generation includes TDD cycle info"""
        # Without TDD cycles
        diagram = self.state_machine.get_mermaid_diagram()
        assert "TDD cycles active" in diagram
        assert "(0 TDD cycles)" not in diagram  # Should show empty when no cycles
        
        # With TDD cycles
        self.state_machine.register_tdd_cycle("story-1", "cycle-1")
        self.state_machine.register_tdd_cycle("story-2", "cycle-2")
        
        diagram = self.state_machine.get_mermaid_diagram()
        assert "(2 TDD cycles)" in diagram
        assert "TDD completion" in diagram
        assert "stateDiagram-v2" in diagram


class TestStateMachineComprehensiveCoverage(unittest.TestCase):
    """Comprehensive coverage tests for StateMachine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.state_machine = StateMachine()
    
    def test_initialization_with_custom_state(self):
        """Test StateMachine initialization with custom initial state"""
        sm = StateMachine(initial_state=State.SPRINT_ACTIVE)
        assert sm.current_state == State.SPRINT_ACTIVE
    
    def test_validate_vs_transition_methods(self):
        """Test difference between validate_command and transition methods"""
        # validate_command should not change state
        original_state = self.state_machine.current_state
        result = self.state_machine.validate_command("/epic")
        assert result.success
        assert self.state_machine.current_state == original_state
        
        # transition should change state
        result = self.state_machine.transition("/epic")
        assert result.success
        assert self.state_machine.current_state != original_state
        assert self.state_machine.current_state == State.BACKLOG_READY
    
    def test_transition_with_project_name(self):
        """Test transition method with project name parameter"""
        result = self.state_machine.transition("/epic", project_name="test-project")
        assert result.success
        assert self.state_machine.current_state == State.BACKLOG_READY
    
    def test_comprehensive_command_coverage(self):
        """Test all commands in transition matrix are covered"""
        transitions = StateMachine.TRANSITIONS
        
        # Test each command at least once
        for command in transitions.keys():
            # Find a state where this command is valid
            valid_states = list(transitions[command].keys())
            if valid_states:
                test_state = valid_states[0]
                self.state_machine.force_state(test_state)
                result = self.state_machine.validate_command(command)
                assert result.success, f"Command {command} should be valid in state {test_state}"
    
    def test_all_states_reachable(self):
        """Test that all states are reachable through valid transitions"""
        transitions = StateMachine.TRANSITIONS
        
        # Collect all reachable states
        reachable_states = set([State.IDLE])  # Start state
        
        for command, state_transitions in transitions.items():
            for target_state in state_transitions.values():
                reachable_states.add(target_state)
        
        # All states should be reachable
        all_states = set(State)
        assert reachable_states == all_states, f"Unreachable states: {all_states - reachable_states}"
    
    def test_error_hints_coverage(self):
        """Test error hints are provided for common invalid transitions"""
        error_hints = StateMachine.ERROR_HINTS
        
        # Test each error hint
        for (command, state), expected_hint in error_hints.items():
            self.state_machine.force_state(state)
            result = self.state_machine.validate_command(command)
            assert not result.success
            assert expected_hint.lower() in result.hint.lower()
    
    def test_backlog_commands_comprehensive(self):
        """Test backlog commands comprehensively"""
        backlog_commands = StateMachine.BACKLOG_COMMANDS
        
        # Test all backlog commands in all allowed states
        allowed_states = [s for s in State if s != State.SPRINT_REVIEW]
        
        for state in allowed_states:
            for command in backlog_commands:
                self.state_machine.force_state(state)
                result = self.state_machine.validate_command(command)
                assert result.success, f"Backlog command {command} should be allowed in {state}"
                assert result.new_state == state  # Should not change state


# ============================================================================
# TDD State Machine Tests (from test_tdd_state_machine.py)
# ============================================================================


class TestTDDStateMachine:
    """Test TDD state machine transitions and command validation"""
    
    def test_initial_state(self):
        """Test state machine initialization"""
        sm = TDDStateMachine()
        assert sm.current_state == TDDState.DESIGN
        assert sm.active_cycle is None
    
    def test_custom_initial_state(self):
        """Test state machine with custom initial state"""
        sm = TDDStateMachine(TDDState.TEST_RED)
        assert sm.current_state == TDDState.TEST_RED
    
    def test_set_active_cycle(self):
        """Test setting active cycle"""
        sm = TDDStateMachine()
        cycle = TDDCycle(story_id="story-123", current_state=TDDState.CODE_GREEN)
        
        sm.set_active_cycle(cycle)
        assert sm.active_cycle == cycle
        assert sm.current_state == TDDState.CODE_GREEN
    
    def test_validate_unknown_command(self):
        """Test validation of unknown command"""
        sm = TDDStateMachine()
        result = sm.validate_command("/tdd unknown")
        
        assert not result.success
        assert "Unknown TDD command" in result.error_message
        assert "Use /tdd status" in result.hint
    
    def test_validate_invalid_state_transition(self):
        """Test validation of invalid state transitions"""
        sm = TDDStateMachine(TDDState.DESIGN)
        
        # Can't code without tests
        result = sm.validate_command("/tdd code")
        assert not result.success
        assert "not allowed in TDD state design" in result.error_message
        assert "Write failing tests first" in result.hint
        
        # Can't refactor from design
        result = sm.validate_command("/tdd refactor")
        assert not result.success
        assert "Need to write tests and implement code first" in result.hint
    
    def test_validate_valid_transitions(self):
        """Test validation of valid state transitions"""
        sm = TDDStateMachine(TDDState.DESIGN)
        
        # Valid transitions from DESIGN
        result = sm.validate_command("/tdd test")
        assert result.success
        assert result.new_state == TDDState.TEST_RED
        
        result = sm.validate_command("/tdd start")
        assert result.success
        assert result.new_state == TDDState.DESIGN
        
        result = sm.validate_command("/tdd status")
        assert result.success
        assert result.new_state == TDDState.DESIGN
    
    def test_state_transitions(self):
        """Test actual state transitions"""
        sm = TDDStateMachine()
        
        # DESIGN -> TEST_RED
        result = sm.transition("/tdd test")
        assert result.success
        assert sm.current_state == TDDState.TEST_RED
        
        # TEST_RED -> CODE_GREEN
        result = sm.transition("/tdd code")
        assert result.success
        assert sm.current_state == TDDState.CODE_GREEN
        
        # CODE_GREEN -> REFACTOR
        result = sm.transition("/tdd refactor")
        assert result.success
        assert sm.current_state == TDDState.REFACTOR
        
        # REFACTOR -> COMMIT
        result = sm.transition("/tdd commit")
        assert result.success
        assert sm.current_state == TDDState.COMMIT
    
    def test_transition_with_cycle(self):
        """Test transitions with active cycle"""
        sm = TDDStateMachine()
        cycle = TDDCycle(story_id="story-123")
        task = TDDTask(description="Test task")
        cycle.add_task(task)
        cycle.start_task(task.id)
        
        sm.set_active_cycle(cycle)
        
        # Transition should update both state machine and cycle
        result = sm.transition("/tdd test")
        assert result.success
        assert sm.current_state == TDDState.TEST_RED
        assert cycle.current_state == TDDState.TEST_RED
        assert task.current_state == TDDState.TEST_RED
    
    def test_condition_checking_failing_tests_required(self):
        """Test condition checking for failing tests requirement"""
        sm = TDDStateMachine(TDDState.TEST_RED)
        cycle = TDDCycle(story_id="story-123", current_state=TDDState.TEST_RED)
        task = TDDTask(description="Test task", current_state=TDDState.TEST_RED)
        cycle.add_task(task)
        cycle.start_task(task.id)
        
        sm.set_active_cycle(cycle)
        
        # Without failing tests, can't move to CODE_GREEN
        result = sm.validate_command("/tdd code")
        assert not result.success
        assert "has_failing_tests" in result.error_message
        
        # Add failing test
        failing_test = TestResult(
            test_file="test.py",
            test_name="test_fail",
            status=TestStatus.RED
        )
        task.test_results.append(failing_test)
        
        # Now should be able to move to CODE_GREEN
        result = sm.validate_command("/tdd code")
        assert result.success
    
    def test_condition_checking_passing_tests_required(self):
        """Test condition checking for passing tests requirement"""
        sm = TDDStateMachine(TDDState.CODE_GREEN)
        cycle = TDDCycle(story_id="story-123", current_state=TDDState.CODE_GREEN)
        task = TDDTask(description="Test task", current_state=TDDState.CODE_GREEN)
        cycle.add_task(task)
        cycle.start_task(task.id)
        
        sm.set_active_cycle(cycle)
        
        # Without passing tests, can't refactor or commit
        result = sm.validate_command("/tdd refactor")
        assert not result.success
        assert "has_passing_tests" in result.error_message
        
        result = sm.validate_command("/tdd commit")
        assert not result.success
        
        # Add passing test
        passing_test = TestResult(
            test_file="test.py",
            test_name="test_pass",
            status=TestStatus.GREEN
        )
        task.test_results.append(passing_test)
        
        # Now should be able to refactor and commit
        result = sm.validate_command("/tdd refactor")
        assert result.success
        
        result = sm.validate_command("/tdd commit")
        assert result.success
    
    def test_get_allowed_commands(self):
        """Test getting allowed commands in different states"""
        sm = TDDStateMachine(TDDState.DESIGN)
        
        allowed = sm.get_allowed_commands()
        assert "/tdd start" in allowed
        assert "/tdd test" in allowed
        assert "/tdd status" in allowed
        assert "/tdd abort" in allowed
        assert "/tdd run_tests" in allowed
        
        # Commands not allowed in DESIGN
        assert "/tdd code" not in allowed
        assert "/tdd refactor" not in allowed
        assert "/tdd commit" not in allowed
    
    def test_get_allowed_commands_with_conditions(self):
        """Test allowed commands with condition checking"""
        sm = TDDStateMachine(TDDState.CODE_GREEN)
        cycle = TDDCycle(story_id="story-123", current_state=TDDState.CODE_GREEN)
        task = TDDTask(description="Test task", current_state=TDDState.CODE_GREEN)
        cycle.add_task(task)
        cycle.start_task(task.id)
        
        sm.set_active_cycle(cycle)
        
        # Without passing tests, refactor and commit not allowed
        allowed = sm.get_allowed_commands()
        assert "/tdd refactor" not in allowed
        assert "/tdd commit" not in allowed
        
        # Add passing test
        passing_test = TestResult(
            test_file="test.py",
            test_name="test_pass",
            status=TestStatus.GREEN
        )
        task.test_results.append(passing_test)
        
        # Now refactor and commit should be allowed
        allowed = sm.get_allowed_commands()
        assert "/tdd refactor" in allowed
        assert "/tdd commit" in allowed
    
    def test_get_next_suggested_command(self):
        """Test getting next suggested command"""
        sm = TDDStateMachine()
        
        # Test suggestions for each state (updated for test preservation workflow)
        sm.current_state = TDDState.DESIGN
        assert sm.get_next_suggested_command() == "/tdd test"
        
        sm.current_state = TDDState.TEST_RED
        assert sm.get_next_suggested_command() == "/tdd commit-tests"  # Commit tests first
        
        sm.current_state = TDDState.CODE_GREEN
        assert sm.get_next_suggested_command() == "/tdd commit-code"  # Commit implementation
        
        sm.current_state = TDDState.REFACTOR
        assert sm.get_next_suggested_command() == "/tdd commit-refactor"  # Commit refactored code
        
        sm.current_state = TDDState.COMMIT
        assert sm.get_next_suggested_command() == "/tdd start"
    
    def test_get_state_info(self):
        """Test getting comprehensive state information"""
        sm = TDDStateMachine(TDDState.CODE_GREEN)
        cycle = TDDCycle(story_id="story-info", current_state=TDDState.CODE_GREEN)
        
        sm.set_active_cycle(cycle)
        
        info = sm.get_state_info()
        assert info["current_state"] == "code_green"
        assert info["has_active_cycle"] is True
        assert info["cycle_id"] == cycle.id
        assert info["story_id"] == "story-info"
        assert isinstance(info["allowed_commands"], list)
        assert info["next_suggested"] is not None
        assert "transition_matrix" in info
    
    def test_get_state_info_no_cycle(self):
        """Test state info without active cycle"""
        sm = TDDStateMachine(TDDState.DESIGN)
        
        info = sm.get_state_info()
        assert info["current_state"] == "design"
        assert info["has_active_cycle"] is False
        assert "cycle_id" not in info
    
    def test_auto_progress_checking(self):
        """Test auto-progress capability checking"""
        sm = TDDStateMachine(TDDState.DESIGN)
        
        # No auto-progress without cycle
        assert not sm.can_auto_progress()
        
        # Set up cycle with task
        cycle = TDDCycle(story_id="story-123", current_state=TDDState.DESIGN)
        task = TDDTask(description="Test task", current_state=TDDState.DESIGN)
        cycle.add_task(task)
        cycle.start_task(task.id)
        
        sm.set_active_cycle(cycle)
        
        # Should be able to auto-progress from DESIGN to TEST_RED
        assert sm.can_auto_progress()
        
        # Move to TEST_RED - can auto-progress once tests are written (test-preservation workflow)
        sm.transition("/tdd test")
        # Note: In test-preservation workflow, /tdd commit-tests is available once tests exist
        # This test may need to be updated based on refined condition checking
        
        # Add failing test - now can auto-progress
        failing_test = TestResult(
            test_file="test.py",
            test_name="test_fail",
            status=TestStatus.RED
        )
        task.test_results.append(failing_test)
        assert sm.can_auto_progress()
    
    def test_reset(self):
        """Test state machine reset"""
        sm = TDDStateMachine(TDDState.REFACTOR)
        cycle = TDDCycle(story_id="story-123")
        sm.set_active_cycle(cycle)
        
        # Reset to initial state
        sm.reset()
        assert sm.current_state == TDDState.DESIGN
        assert sm.active_cycle is None
    
    def test_mermaid_diagram_generation(self):
        """Test Mermaid diagram generation"""
        sm = TDDStateMachine()
        diagram = sm.get_mermaid_diagram()
        
        assert "```mermaid" in diagram
        assert "stateDiagram-v2" in diagram
        assert "DESIGN" in diagram
        assert "TEST_RED" in diagram
        assert "CODE_GREEN" in diagram
        assert "REFACTOR" in diagram
        assert "COMMIT" in diagram
    
    def test_iterative_workflow(self):
        """Test complete iterative TDD workflow"""
        sm = TDDStateMachine()
        cycle = TDDCycle(story_id="story-workflow")
        task = TDDTask(description="Complete workflow task")
        cycle.add_task(task)
        cycle.start_task(task.id)
        
        sm.set_active_cycle(cycle)
        
        # 1. DESIGN -> TEST_RED
        result = sm.transition("/tdd test")
        assert result.success
        assert sm.current_state == TDDState.TEST_RED
        
        # 2. Add failing test and move to CODE_GREEN
        failing_test = TestResult(
            test_file="test.py",
            test_name="test_feature",
            status=TestStatus.RED
        )
        task.test_results.append(failing_test)
        
        result = sm.transition("/tdd code")
        assert result.success
        assert sm.current_state == TDDState.CODE_GREEN
        
        # 3. Add passing test and move to REFACTOR
        passing_test = TestResult(
            test_file="test.py",
            test_name="test_feature",
            status=TestStatus.GREEN
        )
        task.test_results.append(passing_test)
        
        result = sm.transition("/tdd refactor")
        assert result.success
        assert sm.current_state == TDDState.REFACTOR
        
        # 4. REFACTOR -> COMMIT
        result = sm.transition("/tdd commit")
        assert result.success
        assert sm.current_state == TDDState.COMMIT
        
        # 5. Start next cycle
        result = sm.transition("/tdd next")
        assert result.success
        assert sm.current_state == TDDState.DESIGN
    
    def test_error_conditions_and_hints(self):
        """Test error conditions provide helpful hints"""
        sm = TDDStateMachine(TDDState.DESIGN)
        
        # Test condition hint for missing failing tests
        cycle = TDDCycle(story_id="story-123", current_state=TDDState.TEST_RED)
        task = TDDTask(description="Test task", current_state=TDDState.TEST_RED)
        cycle.add_task(task)
        cycle.start_task(task.id)
        sm.set_active_cycle(cycle)
        sm.current_state = TDDState.TEST_RED
        
        result = sm.validate_command("/tdd code")
        assert not result.success
        assert "Write and run tests first" in result.hint
        
        # Test condition hint for missing passing tests
        sm.current_state = TDDState.CODE_GREEN
        cycle.current_state = TDDState.CODE_GREEN
        task.current_state = TDDState.CODE_GREEN
        
        result = sm.validate_command("/tdd refactor")
        assert not result.success
        assert "Run tests with /tdd run_tests" in result.hint


class TestTDDStateMachineCommitCommands:
    """Test new TDD commit commands with test preservation"""
    
    def test_commit_tests_command_validation(self):
        """Test /tdd commit-tests command validation"""
        sm = TDDStateMachine(TDDState.TEST_RED)
        cycle = TDDCycle(story_id="story_commit", current_state=TDDState.TEST_RED)
        task = TDDTask(description="Commit tests task", current_state=TDDState.TEST_RED)
        cycle.add_task(task)
        cycle.start_task(task.id)
        sm.set_active_cycle(cycle)
        
        # Initially can't commit tests - missing conditions
        result = sm.validate_command("/tdd commit-tests")
        assert not result.success
        # Could fail on either has_failing_tests or has_test_files condition
        assert ("has_test_files" in result.error_message or "has_failing_tests" in result.error_message)
        
        # Add test file but no failing tests
        test_file = TestFile(file_path="/test.py")
        task.add_test_file(test_file)
        
        result = sm.validate_command("/tdd commit-tests")
        assert not result.success
        assert "has_failing_tests" in result.error_message
        
        # Add failing test - now should be valid
        failing_test = TestResult(
            test_file="test.py",
            test_name="test_fail",
            status=TestStatus.RED
        )
        task.test_results.append(failing_test)
        
        result = sm.validate_command("/tdd commit-tests")
        assert result.success
        assert result.new_state == TDDState.CODE_GREEN
    
    def test_commit_tests_transition(self):
        """Test /tdd commit-tests state transition"""
        sm = TDDStateMachine(TDDState.TEST_RED)
        cycle = TDDCycle(story_id="story_transition", current_state=TDDState.TEST_RED)
        task = TDDTask(description="Transition task", current_state=TDDState.TEST_RED)
        
        # Set up valid conditions
        test_file = TestFile(file_path="/test.py")
        task.add_test_file(test_file)
        failing_test = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.RED)
        task.test_results.append(failing_test)
        
        cycle.add_task(task)
        cycle.start_task(task.id)
        sm.set_active_cycle(cycle)
        
        # Execute transition
        result = sm.transition("/tdd commit-tests")
        assert result.success
        assert sm.current_state == TDDState.CODE_GREEN
        assert cycle.current_state == TDDState.CODE_GREEN
        assert task.current_state == TDDState.CODE_GREEN
    
    def test_commit_code_command_validation(self):
        """Test /tdd commit-code command validation"""
        sm = TDDStateMachine(TDDState.CODE_GREEN)
        cycle = TDDCycle(story_id="story_code", current_state=TDDState.CODE_GREEN)
        task = TDDTask(description="Code task", current_state=TDDState.CODE_GREEN)
        cycle.add_task(task)
        cycle.start_task(task.id)
        sm.set_active_cycle(cycle)
        
        # Initially can't commit code - missing conditions
        result = sm.validate_command("/tdd commit-code")
        assert not result.success
        # Could fail on either has_passing_tests or has_committed_tests condition
        assert ("has_committed_tests" in result.error_message or "has_passing_tests" in result.error_message)
        
        # Add committed test file but no passing tests
        test_file = TestFile(file_path="/test.py", committed_at="2023-01-01T10:00:00")
        task.add_test_file(test_file)
        
        result = sm.validate_command("/tdd commit-code")
        assert not result.success
        assert "has_passing_tests" in result.error_message
        
        # Add passing test - now should be valid
        passing_test = TestResult(
            test_file="test.py",
            test_name="test_pass",
            status=TestStatus.GREEN
        )
        task.test_results.append(passing_test)
        
        result = sm.validate_command("/tdd commit-code")
        assert result.success
        assert result.new_state == TDDState.REFACTOR
    
    def test_commit_refactor_command_validation(self):
        """Test /tdd commit-refactor command validation"""
        sm = TDDStateMachine(TDDState.REFACTOR)
        cycle = TDDCycle(story_id="story_refactor", current_state=TDDState.REFACTOR)
        task = TDDTask(description="Refactor task", current_state=TDDState.REFACTOR)
        cycle.add_task(task)
        cycle.start_task(task.id)
        sm.set_active_cycle(cycle)
        
        # Set up valid conditions
        test_file = TestFile(file_path="/test.py", committed_at="2023-01-01T10:00:00")
        task.add_test_file(test_file)
        passing_test = TestResult(test_file="test.py", test_name="test_pass", status=TestStatus.GREEN)
        task.test_results.append(passing_test)
        
        result = sm.validate_command("/tdd commit-refactor")
        assert result.success
        assert result.new_state == TDDState.COMMIT
    
    def test_commit_commands_error_hints(self):
        """Test error hints for commit commands"""
        sm = TDDStateMachine()
        
        # Test commit-tests from wrong states
        sm.current_state = TDDState.DESIGN
        result = sm.validate_command("/tdd commit-tests")
        assert not result.success
        assert "Write failing tests first" in result.hint
        
        sm.current_state = TDDState.CODE_GREEN
        result = sm.validate_command("/tdd commit-tests")
        assert not result.success
        assert "Tests already committed" in result.hint
        
        # Test commit-code from wrong states
        sm.current_state = TDDState.TEST_RED
        result = sm.validate_command("/tdd commit-code")
        assert not result.success
        assert "Use /tdd commit-tests first" in result.hint
        
        # Test commit-refactor from wrong states
        sm.current_state = TDDState.CODE_GREEN
        result = sm.validate_command("/tdd commit-refactor")
        assert not result.success
        assert "Use /tdd commit-code first" in result.hint
    
    def test_commit_commands_in_allowed_commands(self):
        """Test commit commands appear in allowed commands when appropriate"""
        sm = TDDStateMachine(TDDState.TEST_RED)
        cycle = TDDCycle(story_id="story_allowed", current_state=TDDState.TEST_RED)
        task = TDDTask(description="Allowed task", current_state=TDDState.TEST_RED)
        
        # Set up conditions for commit-tests
        test_file = TestFile(file_path="/test.py")
        task.add_test_file(test_file)
        failing_test = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.RED, timestamp="2023-01-01T09:00:00")
        task.test_results.append(failing_test)
        
        cycle.add_task(task)
        cycle.start_task(task.id)
        sm.set_active_cycle(cycle)
        
        # Should include commit-tests in allowed commands
        allowed = sm.get_allowed_commands()
        assert "/tdd commit-tests" in allowed
        assert "/tdd commit-code" not in allowed
        assert "/tdd commit-refactor" not in allowed
        
        # Move to CODE_GREEN and set up for commit-code
        sm.transition("/tdd commit-tests")
        test_file.committed_at = "2023-01-01T10:00:00"
        # In TDD, the same test changes from RED to GREEN after code implementation
        passing_test = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.GREEN, timestamp="2023-01-01T10:00:00")
        task.test_results.append(passing_test)
        
        allowed = sm.get_allowed_commands()
        assert "/tdd commit-code" in allowed
        assert "/tdd commit-tests" not in allowed
        assert "/tdd commit-refactor" not in allowed
    
    def test_next_suggested_command_with_commits(self):
        """Test next suggested command includes commit commands"""
        sm = TDDStateMachine(TDDState.TEST_RED)
        cycle = TDDCycle(story_id="story_suggest", current_state=TDDState.TEST_RED)
        task = TDDTask(description="Suggest task", current_state=TDDState.TEST_RED)
        
        # Set up valid conditions
        test_file = TestFile(file_path="/test.py")
        task.add_test_file(test_file)
        failing_test = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.RED, timestamp="2023-01-01T09:00:00")
        task.test_results.append(failing_test)
        
        cycle.add_task(task)
        cycle.start_task(task.id)
        sm.set_active_cycle(cycle)
        
        # Should suggest commit-tests in TEST_RED
        suggested = sm.get_next_suggested_command()
        assert suggested == "/tdd commit-tests"
        
        # Move to CODE_GREEN
        sm.transition("/tdd commit-tests")
        test_file.committed_at = "2023-01-01T10:00:00"
        # In TDD, the same test changes from RED to GREEN after code implementation
        passing_test = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.GREEN, timestamp="2023-01-01T10:00:00")
        task.test_results.append(passing_test)
        
        # Should suggest commit-code in CODE_GREEN
        suggested = sm.get_next_suggested_command()
        assert suggested == "/tdd commit-code"
        
        # Move to REFACTOR
        sm.transition("/tdd commit-code")
        
        # Should suggest commit-refactor in REFACTOR
        suggested = sm.get_next_suggested_command()
        assert suggested == "/tdd commit-refactor"
    
    def test_condition_checking_with_test_files(self):
        """Test new condition checking for test files"""
        sm = TDDStateMachine()
        task = TDDTask(description="Condition task")
        
        # Test has_test_files condition
        assert not sm._check_condition("has_test_files", task)
        
        test_file = TestFile(file_path="/test.py")
        task.add_test_file(test_file)
        assert sm._check_condition("has_test_files", task)
        
        # Test has_committed_tests condition
        assert not sm._check_condition("has_committed_tests", task)
        
        test_file.committed_at = "2023-01-01T10:00:00"
        assert sm._check_condition("has_committed_tests", task)
        
        # Test condition hints
        task_no_files = TDDTask(description="No files task")
        hint = sm._get_condition_hint("has_test_files", task_no_files)
        assert "Create test files using /tdd test" in hint
        
        task_no_commits = TDDTask(description="No commits task")
        test_file_draft = TestFile(file_path="/draft.py")
        task_no_commits.add_test_file(test_file_draft)
        hint = sm._get_condition_hint("has_committed_tests", task_no_commits)
        assert "Use /tdd commit-tests to commit them" in hint
    
    def test_full_commit_workflow(self):
        """Test complete workflow with commit commands"""
        sm = TDDStateMachine()
        cycle = TDDCycle(story_id="story_workflow")
        task = TDDTask(description="Full workflow task")
        cycle.add_task(task)
        cycle.start_task(task.id)
        sm.set_active_cycle(cycle)
        
        # 1. DESIGN -> TEST_RED
        result = sm.transition("/tdd test")
        assert result.success
        assert sm.current_state == TDDState.TEST_RED
        
        # 2. Add test file and failing tests
        test_file = TestFile(file_path="/test_feature.py")
        task.add_test_file(test_file)
        failing_test = TestResult(
            test_file="test_feature.py",
            test_name="test_feature",
            status=TestStatus.RED
        )
        task.test_results.append(failing_test)
        
        # 3. TEST_RED -> CODE_GREEN via commit-tests
        result = sm.transition("/tdd commit-tests")
        assert result.success
        assert sm.current_state == TDDState.CODE_GREEN
        
        # 4. Mark test as committed and add passing test
        test_file.committed_at = "2023-01-01T10:00:00"
        passing_test = TestResult(
            test_file="test_feature.py",
            test_name="test_feature",
            status=TestStatus.GREEN
        )
        task.test_results.append(passing_test)
        
        # 5. CODE_GREEN -> REFACTOR via commit-code
        result = sm.transition("/tdd commit-code")
        assert result.success
        assert sm.current_state == TDDState.REFACTOR
        
        # 6. REFACTOR -> COMMIT via commit-refactor
        result = sm.transition("/tdd commit-refactor")
        assert result.success
        assert sm.current_state == TDDState.COMMIT
        
        # Verify cycle tracking
        assert cycle.current_state == TDDState.COMMIT
        assert task.current_state == TDDState.COMMIT
    
    def test_mermaid_diagram_includes_commit_commands(self):
        """Test that Mermaid diagram includes commit commands"""
        sm = TDDStateMachine()
        diagram = sm.get_mermaid_diagram()
        
        assert "/tdd commit-tests" in diagram
        assert "/tdd commit-code" in diagram
        assert "/tdd commit-refactor" in diagram
        assert "tests committed" in diagram
        assert "code committed" in diagram
        assert "refactoring committed" in diagram


if __name__ == "__main__":
    unittest.main()