#!/usr/bin/env python3
"""Debug the TDD state machine issue"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from tdd_state_machine import TDDStateMachine
from tdd_models import TDDState, TDDCycle, TDDTask, TestFile, TestResult, TestStatus

# Reproduce the failing test scenario
def debug_commit_commands():
    sm = TDDStateMachine(TDDState.TEST_RED)
    cycle = TDDCycle(story_id="story_debug", current_state=TDDState.TEST_RED)
    task = TDDTask(description="Debug task", current_state=TDDState.TEST_RED)
    
    # Set up conditions for commit-tests
    test_file = TestFile(file_path="/test.py")
    task.add_test_file(test_file)
    failing_test = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.RED, timestamp="2023-01-01T09:00:00")
    task.test_results.append(failing_test)
    
    cycle.add_task(task)
    cycle.start_task(task.id)
    sm.set_active_cycle(cycle)
    
    print(f"Initial state: sm={sm.current_state.value}, cycle={cycle.current_state.value}, task={task.current_state.value}")
    
    # Check conditions for commit-tests
    print(f"Task has failing tests: {task.has_failing_tests()}")
    print(f"Task has test files: {len(task.test_file_objects) > 0}")
    
    # Should include commit-tests in allowed commands
    allowed = sm.get_allowed_commands()
    print(f"Allowed commands in TEST_RED: {allowed}")
    
    # Execute transition
    result = sm.transition("/tdd commit-tests")
    print(f"Transition result: success={result.success}, new_state={result.new_state}")
    print(f"After transition: sm={sm.current_state.value}, cycle={cycle.current_state.value}, task={task.current_state.value}")
    
    # Set up for commit-code
    test_file.committed_at = "2023-01-01T10:00:00"
    # In real TDD, the same test changes from RED to GREEN after code implementation
    passing_test = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.GREEN, timestamp="2023-01-01T10:00:01")
    task.test_results.append(passing_test)
    
    # Check conditions for commit-code
    print(f"All test results: {[(r.test_name, r.status.value) for r in task.test_results]}")
    print(f"Latest test results: {[(r.test_name, r.status.value) for r in task.get_latest_test_results()]}")
    print(f"Test file is committed: {test_file.is_committed()}")
    print(f"Task has passing tests: {task.has_passing_tests()}")
    print(f"Task has committed tests: {len(task.get_committed_test_files()) > 0}")
    
    allowed = sm.get_allowed_commands()
    print(f"Allowed commands in CODE_GREEN: {allowed}")
    print(f"'/tdd commit-code' in allowed: {'/tdd commit-code' in allowed}")

if __name__ == "__main__":
    debug_commit_commands()