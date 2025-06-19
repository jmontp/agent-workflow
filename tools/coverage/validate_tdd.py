#!/usr/bin/env python3
"""
Simple validation script for TDD models and state machine.
This runs basic tests without pytest to verify functionality.
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from tdd_models import TDDState, TestStatus, TDDCycle, TDDTask, TestResult
from tdd_state_machine import TDDStateMachine, TDDCommandResult


def test_tdd_models():
    """Test TDD models basic functionality"""
    print("Testing TDD models...")
    
    # Test TestResult
    result = TestResult(
        test_file="test_example.py",
        test_name="test_addition",
        status=TestStatus.GREEN,
        output="All tests passed"
    )
    
    # Test serialization
    data = result.to_dict()
    restored = TestResult.from_dict(data)
    assert restored.test_file == result.test_file
    assert restored.status == result.status
    print("✓ TestResult serialization works")
    
    # Test TDDTask
    task = TDDTask(
        description="Implement calculator addition",
        acceptance_criteria=["Must handle positive numbers"],
        current_state=TDDState.DESIGN
    )
    
    assert not task.is_complete()
    assert not task.has_passing_tests()
    assert not task.has_failing_tests()
    
    # Add test results
    task.test_results.append(result)
    assert task.has_passing_tests()
    print("✓ TDDTask functionality works")
    
    # Test TDDCycle
    cycle = TDDCycle(story_id="story-123")
    cycle.add_task(task)
    
    assert len(cycle.tasks) == 1
    assert task.cycle_id == cycle.id
    assert not cycle.is_complete()
    
    # Start and complete task
    cycle.start_task(task.id)
    assert cycle.current_task_id == task.id
    
    cycle.complete_current_task()
    assert task.is_complete()
    assert cycle.is_complete()  # All tasks complete
    print("✓ TDDCycle functionality works")
    
    print("TDD models validation: PASSED\n")


def test_tdd_state_machine():
    """Test TDD state machine functionality"""
    print("Testing TDD state machine...")
    
    sm = TDDStateMachine()
    assert sm.current_state == TDDState.DESIGN
    print("✓ State machine initialization works")
    
    # Test valid transitions
    result = sm.transition("/tdd test")
    assert result.success
    assert sm.current_state == TDDState.TEST_RED
    print("✓ DESIGN -> TEST_RED transition works")
    
    result = sm.transition("/tdd code")
    assert result.success
    assert sm.current_state == TDDState.CODE_GREEN
    print("✓ TEST_RED -> CODE_GREEN transition works")
    
    # Test invalid transition
    sm.current_state = TDDState.DESIGN
    result = sm.validate_command("/tdd code")
    assert not result.success
    assert "not allowed" in result.error_message
    print("✓ Invalid transition validation works")
    
    # Test with cycle and conditions
    cycle = TDDCycle(story_id="story-123", current_state=TDDState.TEST_RED)
    task = TDDTask(description="Test task", current_state=TDDState.TEST_RED)
    cycle.add_task(task)
    cycle.start_task(task.id)
    
    sm.set_active_cycle(cycle)
    sm.current_state = TDDState.TEST_RED
    
    # Without failing tests, can't move to CODE_GREEN
    result = sm.validate_command("/tdd code")
    assert not result.success
    print("✓ Condition checking works (no failing tests)")
    
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
    print("✓ Condition checking works (with failing tests)")
    
    # Test allowed commands
    allowed = sm.get_allowed_commands()
    assert "/tdd code" in allowed
    assert "/tdd status" in allowed
    print("✓ Allowed commands calculation works")
    
    # Test next suggestion
    suggested = sm.get_next_suggested_command()
    assert suggested == "/tdd code"
    print("✓ Next command suggestion works")
    
    print("TDD state machine validation: PASSED\n")


def test_integration():
    """Test integration between models and state machine"""
    print("Testing integration...")
    
    # Create complete workflow
    cycle = TDDCycle(story_id="story-integration")
    task = TDDTask(description="Integration test task")
    cycle.add_task(task)
    cycle.start_task(task.id)
    
    sm = TDDStateMachine()
    sm.set_active_cycle(cycle)
    
    # Walk through complete TDD cycle
    # 1. DESIGN -> TEST_RED
    result = sm.transition("/tdd test")
    assert result.success
    assert sm.current_state == TDDState.TEST_RED
    assert cycle.current_state == TDDState.TEST_RED
    assert task.current_state == TDDState.TEST_RED
    
    # 2. Add failing test and move to CODE_GREEN
    failing_test = TestResult(
        test_file="test_integration.py",
        test_name="test_feature",
        status=TestStatus.RED
    )
    task.test_results.append(failing_test)
    
    result = sm.transition("/tdd code")
    assert result.success
    assert sm.current_state == TDDState.CODE_GREEN
    
    # 3. Add passing test and move to REFACTOR
    passing_test = TestResult(
        test_file="test_integration.py",
        test_name="test_feature",
        status=TestStatus.GREEN
    )
    task.test_results.append(passing_test)
    
    result = sm.transition("/tdd refactor")
    assert result.success
    assert sm.current_state == TDDState.REFACTOR
    
    # 4. Move to COMMIT
    result = sm.transition("/tdd commit")
    assert result.success
    assert sm.current_state == TDDState.COMMIT
    
    print("✓ Complete TDD workflow integration works")
    print("Integration validation: PASSED\n")


def main():
    """Run all validation tests"""
    print("=== TDD Implementation Validation ===\n")
    
    try:
        test_tdd_models()
        test_tdd_state_machine()
        test_integration()
        
        print("🎉 All validations PASSED! TDD implementation is working correctly.")
        return 0
        
    except Exception as e:
        print(f"❌ Validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())