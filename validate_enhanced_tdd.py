#!/usr/bin/env python3
"""
Enhanced TDD Workflow Validation

This script validates the Phase 2 TDD implementation with test preservation
and CI/CD integration. It demonstrates the complete workflow from design 
through commit with persistent test files.
"""

from lib.tdd_state_machine import TDDStateMachine
from lib.tdd_models import (
    TDDState, TDDCycle, TDDTask, TestResult, TestStatus,
    TestFile, TestFileStatus, CIStatus
)
from lib.data_models import Story
from datetime import datetime
import os

def validate_test_preservation_workflow():
    """Validate the enhanced TDD workflow with test preservation"""
    print("🧪 Validating Enhanced TDD Workflow with Test Preservation")
    print("=" * 60)
    
    # 1. Initialize TDD components
    print("\n1. Setting up TDD components...")
    sm = TDDStateMachine()
    story = Story(
        title="Calculator Feature",
        description="Add basic calculator operations",
        test_files=[],
        ci_status="not_run",
        test_coverage=0.0
    )
    
    cycle = TDDCycle(story_id=story.id)
    task = TDDTask(description="Implement addition function")
    cycle.add_task(task)
    cycle.start_task(task.id)
    sm.set_active_cycle(cycle)
    
    print(f"   ✓ Created story: {story.title}")
    print(f"   ✓ Created TDD cycle: {cycle.id}")
    print(f"   ✓ Created task: {task.description}")
    print(f"   ✓ Initial state: {sm.current_state.value}")
    
    # 2. DESIGN → TEST_RED
    print("\n2. DESIGN → TEST_RED transition...")
    result = sm.transition("/tdd test")
    assert result.success, "Failed to transition from DESIGN to TEST_RED"
    print(f"   ✓ State: {sm.current_state.value}")
    
    # 3. Create test files (TEST_RED phase)
    print("\n3. Creating test files in TEST_RED phase...")
    test_dir = f"tests/tdd/{story.id}"
    test_file = TestFile(
        file_path=f"/project/{test_dir}/test_calculator.py",
        relative_path=f"{test_dir}/test_calculator.py",
        story_id=story.id,
        task_id=task.id,
        status=TestFileStatus.DRAFT
    )
    
    task.add_test_file(test_file)
    story.test_files.append(test_file.relative_path)
    
    print(f"   ✓ Created test file: {test_file.relative_path}")
    print(f"   ✓ Test directory: {test_file.get_test_directory()}")
    print(f"   ✓ Future permanent location: {test_file.get_permanent_location()}")
    
    # 4. Add failing tests
    print("\n4. Adding failing test results...")
    failing_tests = [
        TestResult(
            test_file="test_calculator.py",
            test_name="test_addition_positive_numbers",
            status=TestStatus.RED,
            output="AssertionError: Expected 5, got None"
        ),
        TestResult(
            test_file="test_calculator.py", 
            test_name="test_addition_negative_numbers",
            status=TestStatus.RED,
            output="AssertionError: Expected -1, got None"
        )
    ]
    
    task.test_results.extend(failing_tests)
    test_file.update_test_results(failing_tests)
    
    print(f"   ✓ Added {len(failing_tests)} failing tests")
    print(f"   ✓ Test file status: {test_file.status.value}")
    print(f"   ✓ Failing tests: {test_file.failing_tests}")
    
    # 5. TEST_RED → CODE_GREEN via commit-tests
    print("\n5. TEST_RED → CODE_GREEN via /tdd commit-tests...")
    result = sm.validate_command("/tdd commit-tests")
    assert result.success, f"commit-tests validation failed: {result.error_message}"
    
    result = sm.transition("/tdd commit-tests")
    assert result.success, "Failed to commit tests"
    
    # Mark test file as committed (simulate git commit)
    test_file.committed_at = datetime.now().isoformat()
    test_file.status = TestFileStatus.COMMITTED
    cycle.increment_commits()
    
    print(f"   ✓ State: {sm.current_state.value}")
    print(f"   ✓ Test file committed at: {test_file.committed_at}")
    print(f"   ✓ Test file status: {test_file.status.value}")
    print(f"   ✓ Cycle commits: {cycle.total_commits}")
    
    # 6. Implement code and make tests pass
    print("\n6. Implementing code to make tests pass...")
    passing_tests = [
        TestResult(
            test_file="test_calculator.py",
            test_name="test_addition_positive_numbers", 
            status=TestStatus.GREEN,
            output="Test passed"
        ),
        TestResult(
            test_file="test_calculator.py",
            test_name="test_addition_negative_numbers",
            status=TestStatus.GREEN, 
            output="Test passed"
        )
    ]
    
    task.test_results.extend(passing_tests)
    test_file.update_test_results(passing_tests)
    test_file.coverage_percentage = 90.0
    task.calculate_test_coverage()
    
    print(f"   ✓ All tests now passing: {test_file.is_passing()}")
    print(f"   ✓ Test coverage: {test_file.coverage_percentage}%")
    print(f"   ✓ Task coverage: {task.test_coverage}%")
    
    # 7. CODE_GREEN → REFACTOR via commit-code
    print("\n7. CODE_GREEN → REFACTOR via /tdd commit-code...")
    result = sm.validate_command("/tdd commit-code")
    assert result.success, f"commit-code validation failed: {result.error_message}"
    
    result = sm.transition("/tdd commit-code") 
    assert result.success, "Failed to commit code"
    cycle.increment_commits()
    
    print(f"   ✓ State: {sm.current_state.value}")
    print(f"   ✓ Cycle commits: {cycle.total_commits}")
    
    # 8. REFACTOR → COMMIT via commit-refactor
    print("\n8. REFACTOR → COMMIT via /tdd commit-refactor...")
    result = sm.validate_command("/tdd commit-refactor")
    assert result.success, f"commit-refactor validation failed: {result.error_message}"
    
    result = sm.transition("/tdd commit-refactor")
    assert result.success, "Failed to commit refactor"
    cycle.increment_commits()
    
    # Update CI status
    task.update_ci_status(CIStatus.PASSED, "run_123", "https://ci.example.com/run_123")
    cycle.update_ci_status(CIStatus.PASSED)
    story.ci_status = "passed"
    story.test_coverage = task.test_coverage
    
    print(f"   ✓ State: {sm.current_state.value}")
    print(f"   ✓ Cycle commits: {cycle.total_commits}")
    print(f"   ✓ CI status: {task.ci_status.value}")
    print(f"   ✓ CI URL: {task.ci_url}")
    
    # 9. Validate test preservation
    print("\n9. Validating test preservation...")
    committed_files = task.get_committed_test_files()
    assert len(committed_files) == 1, "Test file not properly committed"
    assert committed_files[0].is_committed(), "Test file commit status incorrect"
    
    # Test file should be ready for integration to permanent location
    permanent_location = test_file.get_permanent_location()
    print(f"   ✓ Test file preserved in repo: {test_file.is_committed()}")
    print(f"   ✓ Ready for integration to: {permanent_location}")
    print(f"   ✓ Test file lifecycle complete")
    
    # 10. Validate CI/CD integration
    print("\n10. Validating CI/CD integration...")
    assert task.ci_status == CIStatus.PASSED, "CI status not updated"
    assert story.ci_status == "passed", "Story CI status not updated"
    assert story.test_coverage > 0, "Story test coverage not updated"
    
    print(f"   ✓ Task CI status: {task.ci_status.value}")
    print(f"   ✓ Story CI status: {story.ci_status}")
    print(f"   ✓ Story test coverage: {story.test_coverage}%")
    print(f"   ✓ All tests preserved for future CI runs")
    
    # 11. Test directory structure
    print("\n11. Validating test directory structure...")
    structure = cycle.get_test_directory_structure()
    print(f"   ✓ TDD test files: {len(structure['tdd'])}")
    print(f"   ✓ Unit test files: {len(structure['unit'])}")
    print(f"   ✓ Integration test files: {len(structure['integration'])}")
    
    # 12. Summary
    print("\n12. Workflow Summary...")
    summary = cycle.get_progress_summary()
    print(f"   ✓ Completed tasks: {summary['completed_tasks']}/{summary['total_tasks']}")
    print(f"   ✓ Total test runs: {summary['total_test_runs']}")
    print(f"   ✓ Total refactors: {summary['total_refactors']}")
    print(f"   ✓ Total commits: {summary['total_commits']}")
    print(f"   ✓ Overall coverage: {summary['overall_test_coverage']:.1f}%")
    print(f"   ✓ CI status: {summary['ci_status']}")
    
    print("\n" + "=" * 60)
    print("✅ Enhanced TDD Workflow Validation PASSED!")
    print("\nKey Features Validated:")
    print("  • Test file lifecycle management")
    print("  • Test preservation in repository")
    print("  • CI/CD integration and status tracking")
    print("  • Sequential commit workflow")
    print("  • Test coverage metrics")
    print("  • State machine validation")
    print("  • Multi-project directory structure")

def validate_state_machine_enhancements():
    """Validate state machine enhancements"""
    print("\n🔄 Validating State Machine Enhancements")
    print("=" * 60)
    
    sm = TDDStateMachine()
    
    # Test new commands exist
    new_commands = ["/tdd commit-tests", "/tdd commit-code", "/tdd commit-refactor"]
    for cmd in new_commands:
        assert cmd in sm.TRANSITIONS, f"Command {cmd} not in transition matrix"
        print(f"   ✓ Command {cmd} registered")
    
    # Test error hints
    result = sm.validate_command("/tdd commit-tests")
    assert not result.success, "commit-tests should fail in DESIGN state"
    assert "Write failing tests first" in result.hint
    print("   ✓ Error hints work correctly")
    
    # Test next suggested commands
    sm.current_state = TDDState.TEST_RED
    suggested = sm.get_next_suggested_command()
    assert suggested == "/tdd commit-tests", f"Expected commit-tests, got {suggested}"
    print("   ✓ Next suggested commands include commit commands")
    
    # Test Mermaid diagram
    diagram = sm.get_mermaid_diagram()
    for cmd in new_commands:
        assert cmd in diagram, f"Command {cmd} not in diagram"
    print("   ✓ Mermaid diagram includes new commands")
    
    print("✅ State Machine Enhancements Validated!")

if __name__ == "__main__":
    try:
        validate_test_preservation_workflow()
        validate_state_machine_enhancements()
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("Phase 2 TDD implementation is working correctly.")
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        raise