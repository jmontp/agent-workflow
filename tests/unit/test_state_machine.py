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
        
        info = self.state_machine.get_state_info()
        
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


if __name__ == "__main__":
    unittest.main()