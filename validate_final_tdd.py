#!/usr/bin/env python3
"""
Final validation script for TDD implementation.

Validates that all core TDD functionality is working correctly
before creating the final commit.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from tdd_models import (
    TDDState, TDDCycle, TDDTask, TestFile, TestResult, 
    TestStatus, TestFileStatus, CIStatus
)
from tdd_state_machine import TDDStateMachine, TDDCommandResult

def test_tdd_models():
    """Test core TDD models functionality"""
    print("=== Testing TDD Models ===")
    
    # Test TDD Task creation and management
    task = TDDTask(description="Test task for validation")
    print(f"✓ Created TDD task: {task.id}")
    
    # Test TestFile creation and lifecycle
    test_file = TestFile(
        file_path="/test/test_example.py",
        relative_path="test/test_example.py",
        story_id="story-123"
    )
    print(f"✓ Created test file: {test_file.file_path}")
    
    # Test test results
    failing_test = TestResult(
        test_file="test_example.py",
        test_name="test_example_function",
        status=TestStatus.RED,
        timestamp="2023-01-01T09:00:00"
    )
    
    passing_test = TestResult(
        test_file="test_example.py", 
        test_name="test_example_function",
        status=TestStatus.GREEN,
        timestamp="2023-01-01T10:00:00"
    )
    
    task.test_results.extend([failing_test, passing_test])
    task.add_test_file(test_file)
    
    # Test latest test results logic
    latest = task.get_latest_test_results()
    assert len(latest) == 1, f"Expected 1 latest result, got {len(latest)}"
    assert latest[0].status == TestStatus.GREEN, "Latest result should be GREEN"
    print("✓ Test result aggregation working correctly")
    
    # Test TDD cycle management
    cycle = TDDCycle(story_id="story-123", current_state=TDDState.DESIGN)
    cycle.add_task(task)
    cycle.start_task(task.id)
    
    assert cycle.current_task_id == task.id, "Task should be set as current"
    print("✓ TDD cycle management working correctly")
    
    # Test serialization
    task_dict = task.to_dict()
    restored_task = TDDTask.from_dict(task_dict)
    assert restored_task.id == task.id, "Task serialization should preserve ID"
    print("✓ Model serialization working correctly")

def test_tdd_state_machine():
    """Test TDD state machine functionality"""
    print("\n=== Testing TDD State Machine ===")
    
    # Test state machine initialization
    sm = TDDStateMachine(TDDState.DESIGN)
    assert sm.current_state == TDDState.DESIGN, "Should initialize to DESIGN state"
    print("✓ State machine initialization working")
    
    # Test basic transitions
    cycle = TDDCycle(story_id="test-cycle", current_state=TDDState.DESIGN)
    task = TDDTask(description="State machine test", current_state=TDDState.DESIGN)
    cycle.add_task(task)
    cycle.start_task(task.id)
    sm.set_active_cycle(cycle)
    
    # Test DESIGN -> TEST_RED transition
    result = sm.transition("/tdd test")
    assert result.success, f"Transition should succeed: {result.error_message}"
    assert sm.current_state == TDDState.TEST_RED, "Should be in TEST_RED state"
    print("✓ Basic state transitions working")
    
    # Test command validation
    result = sm.validate_command("/tdd code")
    assert not result.success, "Should not allow code without tests"
    print("✓ Command validation working correctly")
    
    # Test commit commands with proper conditions
    test_file = TestFile(file_path="/test.py")
    task.add_test_file(test_file)
    failing_test = TestResult(
        test_file="test.py", 
        test_name="test_fail", 
        status=TestStatus.RED,
        timestamp="2023-01-01T09:00:00"
    )
    task.test_results.append(failing_test)
    
    # Now commit-tests should be available
    allowed = sm.get_allowed_commands()
    assert "/tdd commit-tests" in allowed, "Should allow commit-tests with failing tests"
    print("✓ Conditional commands working correctly")
    
    # Test progression through TDD cycle  
    result = sm.transition("/tdd commit-tests")
    assert result.success, "Should transition to CODE_GREEN"
    assert sm.current_state == TDDState.CODE_GREEN, "Should be in CODE_GREEN state"
    
    # Add passing test and commit code
    test_file.committed_at = "2023-01-01T10:00:00" 
    passing_test = TestResult(
        test_file="test.py",
        test_name="test_fail", 
        status=TestStatus.GREEN,
        timestamp="2023-01-01T11:00:00"
    )
    task.test_results.append(passing_test)
    
    allowed = sm.get_allowed_commands()
    assert "/tdd commit-code" in allowed, "Should allow commit-code with passing tests"
    print("✓ Full TDD cycle progression working")

def test_tdd_integration():
    """Test integration between models and state machine"""
    print("\n=== Testing TDD Integration ===")
    
    # Create a complete TDD scenario
    sm = TDDStateMachine(TDDState.DESIGN)
    cycle = TDDCycle(story_id="integration-test")
    task = TDDTask(description="Integration test task")
    
    # Set up the scenario
    cycle.add_task(task)
    cycle.start_task(task.id)
    sm.set_active_cycle(cycle)
    
    # Go through complete cycle
    states_visited = []
    
    # Start in DESIGN
    states_visited.append(sm.current_state.value)
    
    # Move to TEST_RED
    result = sm.transition("/tdd test")
    assert result.success, "Should transition to TEST_RED"
    states_visited.append(sm.current_state.value)
    
    # Add test file and failing tests
    test_file = TestFile(file_path="/integration_test.py")
    task.add_test_file(test_file)
    failing_test = TestResult(
        test_file="integration_test.py",
        test_name="test_integration",
        status=TestStatus.RED,
        timestamp="2023-01-01T09:00:00"
    )
    task.test_results.append(failing_test)
    
    # Commit tests and move to CODE_GREEN
    result = sm.transition("/tdd commit-tests")
    assert result.success, "Should commit tests and move to CODE_GREEN"
    states_visited.append(sm.current_state.value)
    
    # Implement code (simulate test passing)
    test_file.committed_at = "2023-01-01T10:00:00"
    passing_test = TestResult(
        test_file="integration_test.py",
        test_name="test_integration",
        status=TestStatus.GREEN, 
        timestamp="2023-01-01T11:00:00"
    )
    task.test_results.append(passing_test)
    
    # Commit code and move to REFACTOR
    result = sm.transition("/tdd commit-code")
    assert result.success, "Should commit code and move to REFACTOR"
    states_visited.append(sm.current_state.value)
    
    expected_states = ["design", "test_red", "code_green", "refactor"]
    assert states_visited == expected_states, f"Expected {expected_states}, got {states_visited}"
    print(f"✓ Complete TDD cycle traversed: {' -> '.join(states_visited)}")

def test_error_conditions():
    """Test error conditions and edge cases"""
    print("\n=== Testing Error Conditions ===")
    
    sm = TDDStateMachine(TDDState.DESIGN)
    
    # Test invalid command
    result = sm.validate_command("/tdd invalid")
    assert not result.success, "Should reject invalid commands"
    assert "Unknown TDD command" in result.error_message, "Should provide helpful error"
    print("✓ Invalid command handling working")
    
    # Test invalid state transition
    result = sm.validate_command("/tdd refactor")  # Can't refactor from DESIGN
    assert not result.success, "Should reject invalid state transitions"
    print("✓ Invalid transition handling working")
    
    # Test state info retrieval
    info = sm.get_state_info()
    assert "current_state" in info, "State info should include current state"
    assert "allowed_commands" in info, "State info should include allowed commands"
    print("✓ State information retrieval working")

def main():
    """Run all validation tests"""
    print("TDD System Validation - Phase 8")
    print("=" * 50)
    
    try:
        test_tdd_models()
        test_tdd_state_machine()
        test_tdd_integration()
        test_error_conditions()
        
        print("\n" + "=" * 50)
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("\nTDD system is ready for production use.")
        print("\nCore functionality validated:")
        print("  ✓ TDD Models (Task, Cycle, TestFile, TestResult)")
        print("  ✓ TDD State Machine (transitions, validations)")
        print("  ✓ Test-preservation workflow (commit commands)")
        print("  ✓ Integration between components")
        print("  ✓ Error handling and edge cases")
        print("  ✓ Serialization and persistence")
        
        return True
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)