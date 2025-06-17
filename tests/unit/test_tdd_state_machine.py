"""
Unit tests for TDD state machine transitions and validation.
"""

import pytest
from lib.tdd_state_machine import TDDStateMachine, TDDCommandResult, TDDState
from lib.tdd_models import TDDCycle, TDDTask, TestResult, TestStatus, TestFile, TestFileStatus


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