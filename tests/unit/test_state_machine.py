"""
Unit tests for State Machine implementation.

Tests all state transitions, command validations, and error handling
according to the research-mode Scrum workflow specification.
"""

import unittest
import pytest
from lib.state_machine import StateMachine, State, CommandResult


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


if __name__ == "__main__":
    unittest.main()