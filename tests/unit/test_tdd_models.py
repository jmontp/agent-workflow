"""
Unit tests for TDD models and data structures.
"""

import pytest
import json
import unittest
from datetime import datetime
from lib.tdd_models import (
    TDDState, TestStatus, CIStatus, TestFileStatus,
    TDDCycle, TDDTask, TestResult, TestFile
)


class TestTestResult:
    """Test TestResult model"""
    
    def test_create_test_result(self):
        """Test creating a test result"""
        result = TestResult(
            test_file="test_example.py",
            test_name="test_addition",
            status=TestStatus.GREEN,
            output="All tests passed",
            execution_time=0.5
        )
        
        assert result.test_file == "test_example.py"
        assert result.test_name == "test_addition"
        assert result.status == TestStatus.GREEN
        assert result.output == "All tests passed"
        assert result.execution_time == 0.5
        assert result.error_message is None
    
    def test_test_result_serialization(self):
        """Test TestResult to_dict and from_dict"""
        original = TestResult(
            test_file="test_calc.py",
            test_name="test_multiply",
            status=TestStatus.RED,
            output="AssertionError",
            error_message="Expected 6, got 8",
            execution_time=0.2
        )
        
        # Test serialization
        data = original.to_dict()
        assert data["test_file"] == "test_calc.py"
        assert data["status"] == "red"
        assert data["error_message"] == "Expected 6, got 8"
        
        # Test deserialization
        restored = TestResult.from_dict(data)
        assert restored.test_file == original.test_file
        assert restored.test_name == original.test_name
        assert restored.status == original.status
        assert restored.output == original.output
        assert restored.error_message == original.error_message
        assert restored.execution_time == original.execution_time


class TestTDDTask:
    """Test TDDTask model"""
    
    def test_create_tdd_task(self):
        """Test creating a TDD task"""
        task = TDDTask(
            description="Implement calculator addition",
            acceptance_criteria=["Must handle positive numbers", "Must handle negative numbers"],
            current_state=TDDState.DESIGN
        )
        
        assert task.description == "Implement calculator addition"
        assert len(task.acceptance_criteria) == 2
        assert task.current_state == TDDState.DESIGN
        assert not task.is_complete()
    
    def test_tdd_task_serialization(self):
        """Test TDDTask to_dict and from_dict"""
        test_result = TestResult(
            test_file="test_calc.py",
            test_name="test_add",
            status=TestStatus.GREEN
        )
        
        original = TDDTask(
            description="Add method implementation",
            acceptance_criteria=["Handle integers", "Return correct sum"],
            current_state=TDDState.CODE_GREEN,
            test_files=["test_calc.py"],
            source_files=["calc.py"],
            test_results=[test_result],
            design_notes="Simple addition function"
        )
        
        # Test serialization
        data = original.to_dict()
        assert data["description"] == "Add method implementation"
        assert data["current_state"] == "code_green"
        assert len(data["test_results"]) == 1
        assert data["test_results"][0]["status"] == "green"
        
        # Test deserialization
        restored = TDDTask.from_dict(data)
        assert restored.description == original.description
        assert restored.current_state == original.current_state
        assert len(restored.test_results) == 1
        assert restored.test_results[0].status == TestStatus.GREEN
    
    def test_task_completion(self):
        """Test task completion tracking"""
        task = TDDTask(description="Test task")
        
        # Initially not complete
        assert not task.is_complete()
        
        # Mark as complete
        task.completed_at = datetime.now().isoformat()
        assert task.is_complete()
    
    def test_test_status_checking(self):
        """Test test status checking methods"""
        task = TDDTask(description="Test task")
        
        # No tests initially
        assert not task.has_passing_tests()
        assert not task.has_failing_tests()
        
        # Add failing test
        failing_test = TestResult(
            test_file="test.py",
            test_name="test_fail",
            status=TestStatus.RED
        )
        task.test_results.append(failing_test)
        
        assert not task.has_passing_tests()
        assert task.has_failing_tests()
        
        # Add passing test (newer timestamp)
        import time
        time.sleep(0.01)  # Ensure different timestamp
        passing_test = TestResult(
            test_file="test.py",
            test_name="test_fail",  # Same test, now passing
            status=TestStatus.GREEN
        )
        task.test_results.append(passing_test)
        
        assert task.has_passing_tests()
        assert not task.has_failing_tests()  # Latest result is passing
    
    def test_latest_test_results(self):
        """Test getting latest test results"""
        task = TDDTask(description="Test task")
        
        # Add multiple results for same test
        result1 = TestResult(
            test_file="test.py",
            test_name="test_example",
            status=TestStatus.RED,
            timestamp="2023-01-01T10:00:00"
        )
        result2 = TestResult(
            test_file="test.py",
            test_name="test_example",
            status=TestStatus.GREEN,
            timestamp="2023-01-01T11:00:00"
        )
        result3 = TestResult(
            test_file="test.py",
            test_name="test_other",
            status=TestStatus.GREEN,
            timestamp="2023-01-01T10:30:00"
        )
        
        task.test_results.extend([result1, result2, result3])
        
        latest = task.get_latest_test_results()
        assert len(latest) == 2  # Two different tests
        
        # Find the result for test_example (should be the later one)
        example_result = next(r for r in latest if r.test_name == "test_example")
        assert example_result.status == TestStatus.GREEN
        assert example_result.timestamp == "2023-01-01T11:00:00"


class TestTDDCycle:
    """Test TDDCycle model"""
    
    def test_create_tdd_cycle(self):
        """Test creating a TDD cycle"""
        cycle = TDDCycle(
            story_id="story-123",
            current_state=TDDState.DESIGN
        )
        
        assert cycle.story_id == "story-123"
        assert cycle.current_state == TDDState.DESIGN
        assert cycle.current_task_id is None
        assert len(cycle.tasks) == 0
        assert not cycle.is_complete()
    
    def test_tdd_cycle_serialization(self):
        """Test TDDCycle to_dict and from_dict"""
        task = TDDTask(description="Test task")
        
        original = TDDCycle(
            story_id="story-456",
            current_state=TDDState.TEST_RED,
            tasks=[task],
            total_test_runs=5,
            total_refactors=2
        )
        
        # Test serialization
        data = original.to_dict()
        assert data["story_id"] == "story-456"
        assert data["current_state"] == "test_red"
        assert data["total_test_runs"] == 5
        assert len(data["tasks"]) == 1
        
        # Test deserialization
        restored = TDDCycle.from_dict(data)
        assert restored.story_id == original.story_id
        assert restored.current_state == original.current_state
        assert restored.total_test_runs == original.total_test_runs
        assert len(restored.tasks) == 1
    
    def test_task_management(self):
        """Test adding and managing tasks in cycle"""
        cycle = TDDCycle(story_id="story-789")
        
        # Add a task
        task = TDDTask(description="First task")
        cycle.add_task(task)
        
        assert len(cycle.tasks) == 1
        assert task.cycle_id == cycle.id
        
        # Start the task
        assert cycle.start_task(task.id)
        assert cycle.current_task_id == task.id
        assert cycle.get_current_task() == task
        
        # Complete the task
        assert cycle.complete_current_task()
        assert task.is_complete()
        assert cycle.current_task_id is None
    
    def test_cycle_completion(self):
        """Test cycle completion logic"""
        cycle = TDDCycle(story_id="story-complete")
        
        # Add two tasks
        task1 = TDDTask(description="Task 1")
        task2 = TDDTask(description="Task 2")
        cycle.add_task(task1)
        cycle.add_task(task2)
        
        # Cycle not complete with incomplete tasks
        assert not cycle.is_complete()
        
        # Complete first task
        cycle.start_task(task1.id)
        cycle.complete_current_task()
        
        # Still not complete
        assert not cycle.is_complete()
        
        # Complete second task
        cycle.start_task(task2.id)
        cycle.complete_current_task()
        
        # Now cycle should be complete
        assert cycle.is_complete()
        assert cycle.current_state == TDDState.COMMIT
    
    def test_progress_summary(self):
        """Test progress summary generation"""
        cycle = TDDCycle(story_id="story-progress")
        
        # Add tasks
        task1 = TDDTask(description="Task 1")
        task2 = TDDTask(description="Task 2")
        task3 = TDDTask(description="Task 3")
        cycle.add_task(task1)
        cycle.add_task(task2)
        cycle.add_task(task3)
        
        # Complete one task
        cycle.start_task(task1.id)
        cycle.complete_current_task()
        
        summary = cycle.get_progress_summary()
        assert summary["completed_tasks"] == 1
        assert summary["total_tasks"] == 3
        assert summary["progress"] == "1/3"
        assert not summary["is_complete"]
        
        # Set some counters
        cycle.total_test_runs = 10
        cycle.total_refactors = 3
        
        summary = cycle.get_progress_summary()
        assert summary["total_test_runs"] == 10
        assert summary["total_refactors"] == 3
    
    def test_task_queries(self):
        """Test task query methods"""
        cycle = TDDCycle(story_id="story-queries")
        
        # Add tasks and complete one
        task1 = TDDTask(description="Completed task")
        task2 = TDDTask(description="Pending task")
        
        cycle.add_task(task1)
        cycle.add_task(task2)
        
        # Complete first task
        cycle.start_task(task1.id)
        cycle.complete_current_task()
        
        # Test queries
        completed = cycle.get_completed_tasks()
        pending = cycle.get_pending_tasks()
        
        assert len(completed) == 1
        assert len(pending) == 1
        assert completed[0] == task1
        assert pending[0] == task2


class TestTestFile:
    """Test TestFile model"""
    
    def test_create_test_file(self):
        """Test creating a test file"""
        test_file = TestFile(
            file_path="/project/tests/tdd/story_123/test_feature.py",
            relative_path="tests/tdd/story_123/test_feature.py",
            story_id="story_123",
            task_id="task_456",
            status=TestFileStatus.DRAFT
        )
        
        assert test_file.file_path.endswith("test_feature.py")
        assert test_file.story_id == "story_123"
        assert test_file.task_id == "task_456"
        assert test_file.status == TestFileStatus.DRAFT
        assert test_file.ci_status == CIStatus.NOT_RUN
        assert not test_file.is_committed()
        assert not test_file.is_passing()
    
    def test_test_file_serialization(self):
        """Test TestFile to_dict and from_dict"""
        original = TestFile(
            file_path="/project/tests/test_calc.py",
            relative_path="tests/test_calc.py", 
            story_id="story_789",
            task_id="task_101",
            status=TestFileStatus.COMMITTED,
            ci_status=CIStatus.PASSED,
            test_count=5,
            passing_tests=4,
            failing_tests=1,
            coverage_percentage=85.5
        )
        
        # Test serialization
        data = original.to_dict()
        assert data["file_path"] == "/project/tests/test_calc.py"
        assert data["status"] == "committed"
        assert data["ci_status"] == "passed"
        assert data["test_count"] == 5
        assert data["coverage_percentage"] == 85.5
        
        # Test deserialization
        restored = TestFile.from_dict(data)
        assert restored.file_path == original.file_path
        assert restored.status == original.status
        assert restored.ci_status == original.ci_status
        assert restored.test_count == original.test_count
        assert restored.coverage_percentage == original.coverage_percentage
    
    def test_test_file_lifecycle_methods(self):
        """Test test file lifecycle status methods"""
        test_file = TestFile(
            file_path="/project/test.py",
            story_id="story_123"
        )
        
        # Initially not committed or passing
        assert not test_file.is_committed()
        assert not test_file.is_passing()
        assert not test_file.is_integrated()
        
        # Mark as committed
        test_file.committed_at = datetime.now().isoformat()
        assert test_file.is_committed()
        
        # Update to passing tests
        test_file.test_count = 3
        test_file.failing_tests = 0
        test_file.passing_tests = 3
        assert test_file.is_passing()
        
        # Mark as integrated
        test_file.integrated_at = datetime.now().isoformat()
        assert test_file.is_integrated()
    
    def test_test_file_directory_methods(self):
        """Test test file directory management methods"""
        test_file = TestFile(
            file_path="/project/tests/tdd/story_123/test_feature.py",
            relative_path="tests/tdd/story_123/test_feature.py",
            story_id="story_123"
        )
        
        # Test directory methods
        assert test_file.get_test_directory() == "tests/tdd/story_123"
        
        # Test permanent location logic
        permanent_loc = test_file.get_permanent_location()
        assert permanent_loc == "tests/unit/test_feature.py"  # Default to unit
        
        # Test integration test detection
        test_file.relative_path = "tests/tdd/story_123/test_integration_feature.py"
        permanent_loc = test_file.get_permanent_location()
        assert permanent_loc == "tests/integration/test_integration_feature.py"
    
    def test_test_file_update_results(self):
        """Test updating test file with test results"""
        test_file = TestFile(
            file_path="/project/test.py",
            story_id="story_123"
        )
        
        # Create test results
        results = [
            TestResult(test_file="test.py", test_name="test_1", status=TestStatus.GREEN),
            TestResult(test_file="test.py", test_name="test_2", status=TestStatus.GREEN),
            TestResult(test_file="test.py", test_name="test_3", status=TestStatus.RED)
        ]
        
        # Update test file with results
        test_file.update_test_results(results)
        
        assert test_file.test_count == 3
        assert test_file.passing_tests == 2
        assert test_file.failing_tests == 1
        assert not test_file.is_passing()  # Has failing tests
        
        # Update to all passing
        results[2].status = TestStatus.GREEN
        test_file.update_test_results(results)
        
        assert test_file.passing_tests == 3
        assert test_file.failing_tests == 0
        # Status should update to passing if it was committed
        test_file.status = TestFileStatus.COMMITTED
        test_file.update_test_results(results)
        assert test_file.status == TestFileStatus.PASSING


class TestTDDTaskEnhancements:
    """Test enhanced TDDTask functionality"""
    
    def test_tdd_task_with_test_files(self):
        """Test TDDTask with TestFile objects"""
        task = TDDTask(description="Test task with files")
        
        # Add test files
        test_file1 = TestFile(
            file_path="/project/test1.py",
            story_id="story_123",
            status=TestFileStatus.DRAFT
        )
        test_file2 = TestFile(
            file_path="/project/test2.py", 
            story_id="story_123",
            status=TestFileStatus.COMMITTED,
            committed_at=datetime.now().isoformat()
        )
        
        task.add_test_file(test_file1)
        task.add_test_file(test_file2)
        
        assert len(task.test_file_objects) == 2
        assert len(task.test_files) == 2
        assert test_file1.task_id == task.id
        assert test_file2.task_id == task.id
    
    def test_tdd_task_test_file_queries(self):
        """Test TDDTask test file query methods"""
        task = TDDTask(description="Task with various test files")
        
        # Add test files in different states
        draft_file = TestFile(file_path="/project/draft.py", status=TestFileStatus.DRAFT)
        committed_file = TestFile(
            file_path="/project/committed.py",
            status=TestFileStatus.COMMITTED,
            committed_at=datetime.now().isoformat()
        )
        passing_file = TestFile(
            file_path="/project/passing.py",
            status=TestFileStatus.PASSING,
            test_count=2,
            passing_tests=2,
            failing_tests=0
        )
        
        task.add_test_file(draft_file)
        task.add_test_file(committed_file)
        task.add_test_file(passing_file)
        
        # Test query methods
        committed_files = task.get_committed_test_files()
        assert len(committed_files) == 1
        assert committed_files[0] == committed_file
        
        passing_files = task.get_passing_test_files()
        assert len(passing_files) == 1
        assert passing_files[0] == passing_file
        
        # Test file lookup
        found_file = task.get_test_file_by_path("/project/draft.py")
        assert found_file == draft_file
    
    def test_tdd_task_ci_integration(self):
        """Test TDDTask CI integration features"""
        task = TDDTask(description="CI integration task")
        
        # Test CI status updates
        task.update_ci_status(CIStatus.RUNNING, "run_123", "https://ci.example.com/run_123")
        
        assert task.ci_status == CIStatus.RUNNING
        assert task.ci_run_id == "run_123"
        assert task.ci_url == "https://ci.example.com/run_123"
        
        # Test coverage calculation
        test_file1 = TestFile(file_path="/test1.py", coverage_percentage=80.0)
        test_file2 = TestFile(file_path="/test2.py", coverage_percentage=90.0)
        
        task.add_test_file(test_file1)
        task.add_test_file(test_file2)
        
        coverage = task.calculate_test_coverage()
        assert coverage == 85.0  # Average of 80 and 90
        assert task.test_coverage == 85.0
    
    def test_tdd_task_commit_conditions(self):
        """Test TDDTask commit readiness conditions"""
        task = TDDTask(description="Commit conditions task", current_state=TDDState.TEST_RED)
        
        # Initially can't commit anything
        assert not task.can_commit_tests()
        assert not task.can_commit_code()
        assert not task.can_commit_refactor()
        
        # Add test file with failing tests
        test_file = TestFile(file_path="/test.py")
        task.add_test_file(test_file)
        failing_result = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.RED)
        task.test_results.append(failing_result)
        
        # Now can commit tests
        assert task.can_commit_tests()
        
        # Move to CODE_GREEN state and commit the test
        task.current_state = TDDState.CODE_GREEN
        test_file.committed_at = datetime.now().isoformat()
        
        # Add passing test result
        passing_result = TestResult(test_file="test.py", test_name="test_fail", status=TestStatus.GREEN)
        task.test_results.append(passing_result)
        
        # Now can commit code
        assert task.can_commit_code()
        
        # Move to REFACTOR state
        task.current_state = TDDState.REFACTOR
        assert task.can_commit_refactor()


class TestTDDStateTransitions:
    """Test TDD state transition logic and validation"""
    
    def test_tdd_state_enum_values(self):
        """Test TDD state enum has correct values"""
        assert TDDState.DESIGN.value == "design"
        assert TDDState.TEST_RED.value == "test_red"
        assert TDDState.CODE_GREEN.value == "code_green"
        assert TDDState.REFACTOR.value == "refactor"
        assert TDDState.COMMIT.value == "commit"
    
    def test_test_status_enum_values(self):
        """Test test status enum has correct values"""
        assert TestStatus.NOT_RUN.value == "not_run"
        assert TestStatus.RED.value == "red"
        assert TestStatus.GREEN.value == "green"
        assert TestStatus.ERROR.value == "error"
    
    def test_ci_status_enum_values(self):
        """Test CI status enum has correct values"""
        assert CIStatus.NOT_RUN.value == "not_run"
        assert CIStatus.PENDING.value == "pending"
        assert CIStatus.RUNNING.value == "running"
        assert CIStatus.PASSED.value == "passed"
        assert CIStatus.FAILED.value == "failed"
        assert CIStatus.ERROR.value == "error"
    
    def test_test_file_status_enum_values(self):
        """Test test file status enum has correct values"""
        assert TestFileStatus.DRAFT.value == "draft"
        assert TestFileStatus.COMMITTED.value == "committed"
        assert TestFileStatus.PASSING.value == "passing"
        assert TestFileStatus.INTEGRATED.value == "integrated"


class TestTDDCycleEnhancements:
    """Test enhanced TDDCycle functionality"""
    
    def test_tdd_cycle_test_file_management(self):
        """Test TDDCycle test file management"""
        cycle = TDDCycle(story_id="story_456")
        
        # Add tasks with test files
        task1 = TDDTask(description="Task 1")
        task2 = TDDTask(description="Task 2")
        
        test_file1 = TestFile(file_path="/test1.py", status=TestFileStatus.COMMITTED, committed_at=datetime.now().isoformat())
        test_file2 = TestFile(file_path="/test2.py", status=TestFileStatus.PASSING, test_count=2, passing_tests=2, failing_tests=0)
        test_file3 = TestFile(file_path="/test3.py", status=TestFileStatus.DRAFT)
        
        task1.add_test_file(test_file1)
        task1.add_test_file(test_file2)
        task2.add_test_file(test_file3)
        
        cycle.add_task(task1)
        cycle.add_task(task2)
        
        # Test cycle-level queries
        all_files = cycle.get_all_test_files()
        assert len(all_files) == 3
        
        committed_files = cycle.get_committed_test_files()
        assert len(committed_files) == 1
        assert committed_files[0] == test_file1
        
        passing_files = cycle.get_passing_test_files()
        assert len(passing_files) == 1
        assert passing_files[0] == test_file2
    
    def test_tdd_cycle_ci_integration(self):
        """Test TDDCycle CI integration features"""
        cycle = TDDCycle(story_id="story_ci")
        
        # Test CI status updates
        cycle.update_ci_status(CIStatus.PASSED)
        assert cycle.ci_status == CIStatus.PASSED
        
        # Test commit counting
        cycle.increment_commits()
        cycle.increment_commits()
        assert cycle.total_commits == 2
        
        # Test coverage calculation
        task = TDDTask(description="Coverage task")
        test_file1 = TestFile(file_path="/test1.py", coverage_percentage=70.0)
        test_file2 = TestFile(file_path="/test2.py", coverage_percentage=90.0)
        
        task.add_test_file(test_file1)
        task.add_test_file(test_file2)
        cycle.add_task(task)
        
        coverage = cycle.calculate_overall_coverage()
        assert coverage == 80.0  # Average of 70 and 90
        assert cycle.overall_test_coverage == 80.0
    
    def test_tdd_cycle_directory_structure(self):
        """Test TDDCycle test directory structure"""
        cycle = TDDCycle(story_id="story_structure")
        
        task = TDDTask(description="Structure task")
        
        # Add test files in different directories
        tdd_file = TestFile(file_path="/tests/tdd/story_123/test_feature.py", relative_path="tests/tdd/story_123/test_feature.py")
        unit_file = TestFile(file_path="/tests/unit/test_utils.py", relative_path="tests/unit/test_utils.py")
        integration_file = TestFile(file_path="/tests/integration/test_api.py", relative_path="tests/integration/test_api.py")
        
        task.add_test_file(tdd_file)
        task.add_test_file(unit_file)
        task.add_test_file(integration_file)
        cycle.add_task(task)
        
        structure = cycle.get_test_directory_structure()
        
        assert len(structure["tdd"]) == 1
        assert len(structure["unit"]) == 1
        assert len(structure["integration"]) == 1
        assert "tests/tdd/story_123/test_feature.py" in structure["tdd"]
        assert "tests/unit/test_utils.py" in structure["unit"]
        assert "tests/integration/test_api.py" in structure["integration"]
    
    def test_tdd_cycle_enhanced_serialization(self):
        """Test enhanced TDDCycle serialization with new fields"""
        original = TDDCycle(
            story_id="story_serial",
            total_commits=5,
            ci_status=CIStatus.PASSED,
            overall_test_coverage=78.5
        )
        
        # Test serialization
        data = original.to_dict()
        assert data["total_commits"] == 5
        assert data["ci_status"] == "passed"
        assert data["overall_test_coverage"] == 78.5
        
        # Test deserialization
        restored = TDDCycle.from_dict(data)
        assert restored.total_commits == original.total_commits
        assert restored.ci_status == original.ci_status
        assert restored.overall_test_coverage == original.overall_test_coverage
        
        # Test progress summary includes new fields
        summary = restored.get_progress_summary()
        assert summary["total_commits"] == 5
        assert summary["ci_status"] == "passed" 
        assert summary["overall_test_coverage"] == 78.5


class TestTDDModelsEdgeCases:
    """Test edge cases and error conditions for TDD models"""
    
    def test_test_result_default_values(self):
        """Test TestResult defaults and edge cases"""
        result = TestResult()
        
        assert result.id.startswith("test-")
        assert result.test_file == ""
        assert result.test_name == ""
        assert result.status == TestStatus.NOT_RUN
        assert result.output == ""
        assert result.error_message is None
        assert result.execution_time == 0.0
        assert isinstance(result.timestamp, str)
    
    def test_test_result_with_error(self):
        """Test TestResult with error status"""
        result = TestResult(
            test_file="test_broken.py",
            test_name="test_broken",
            status=TestStatus.ERROR,
            error_message="ImportError: module not found",
            execution_time=0.1
        )
        
        assert result.status == TestStatus.ERROR
        assert "ImportError" in result.error_message
        
        # Test serialization preserves error
        data = result.to_dict()
        restored = TestResult.from_dict(data)
        assert restored.status == TestStatus.ERROR
        assert restored.error_message == "ImportError: module not found"
    
    def test_test_file_exists_method(self):
        """Test TestFile.exists() method"""
        # Create with non-existent path
        test_file = TestFile(file_path="/nonexistent/path/test.py")
        assert not test_file.exists()
        
        # Create with existing file (this file itself)
        import os
        current_file = os.path.abspath(__file__)
        test_file = TestFile(file_path=current_file)
        assert test_file.exists()
    
    def test_test_file_directory_edge_cases(self):
        """Test TestFile directory methods edge cases"""
        # Test with empty story_id
        test_file = TestFile(file_path="/test.py", story_id="")
        assert test_file.get_test_directory() == "tests/tdd"
        
        # Test with various path patterns
        test_file.relative_path = "tests/unit/test_example.py"
        assert test_file.get_permanent_location() == "tests/unit/test_example.py"
        
        test_file.relative_path = "tests/some_other/test_feature.py"
        assert test_file.get_permanent_location() == "tests/unit/test_feature.py"
    
    def test_test_file_update_results_edge_cases(self):
        """Test TestFile.update_test_results edge cases"""
        test_file = TestFile(file_path="/test.py")
        
        # Update with empty results
        test_file.update_test_results([])
        assert test_file.test_count == 0
        assert test_file.passing_tests == 0
        assert test_file.failing_tests == 0
        
        # Test status transitions
        test_file.status = TestFileStatus.COMMITTED
        results = [TestResult(status=TestStatus.RED)]
        test_file.update_test_results(results)
        assert test_file.status == TestFileStatus.COMMITTED  # Should stay committed with failing tests
        
        # Test transition to passing
        test_file.status = TestFileStatus.COMMITTED
        results = [TestResult(status=TestStatus.GREEN)]
        test_file.update_test_results(results)
        assert test_file.status == TestFileStatus.PASSING
        
        # Test transition back to committed when tests fail
        test_file.status = TestFileStatus.PASSING
        results = [TestResult(status=TestStatus.RED)]
        test_file.update_test_results(results)
        assert test_file.status == TestFileStatus.COMMITTED
    
    def test_tdd_task_edge_cases(self):
        """Test TDDTask edge cases and boundary conditions"""
        task = TDDTask()
        
        # Test defaults
        assert task.id.startswith("tdd-task-")
        assert task.cycle_id == ""
        assert task.description == ""
        assert task.acceptance_criteria == []
        assert task.current_state == TDDState.DESIGN
        assert task.test_files == []
        assert task.test_file_objects == []
        assert task.source_files == []
        assert task.test_results == []
        assert task.ci_status == CIStatus.NOT_RUN
        assert task.test_coverage == 0.0
        assert not task.is_complete()
        
        # Test coverage calculation with no test files
        coverage = task.calculate_test_coverage()
        assert coverage == 0.0
        
        # Test commit conditions in wrong states
        task.current_state = TDDState.DESIGN
        assert not task.can_commit_tests()
        assert not task.can_commit_code()
        assert not task.can_commit_refactor()
    
    def test_tdd_cycle_edge_cases(self):
        """Test TDDCycle edge cases and boundary conditions"""
        cycle = TDDCycle()
        
        # Test defaults
        assert cycle.id.startswith("tdd-cycle-")
        assert cycle.story_id == ""
        assert cycle.current_state == TDDState.DESIGN
        assert cycle.current_task_id is None
        assert cycle.tasks == []
        assert cycle.total_test_runs == 0
        assert cycle.total_refactors == 0
        assert cycle.total_commits == 0
        assert cycle.ci_status == CIStatus.NOT_RUN
        assert cycle.overall_test_coverage == 0.0
        assert not cycle.is_complete()
        
        # Test with invalid task ID
        assert not cycle.start_task("nonexistent-task")
        assert cycle.current_task_id is None
        
        # Test complete with no current task
        assert not cycle.complete_current_task()
        
        # Test coverage calculation with no test files
        coverage = cycle.calculate_overall_coverage()
        assert coverage == 0.0
    
    def test_tdd_cycle_complex_task_management(self):
        """Test complex task management scenarios in TDDCycle"""
        cycle = TDDCycle(story_id="story-complex")
        
        # Add multiple tasks
        task1 = TDDTask(description="Task 1")
        task2 = TDDTask(description="Task 2")
        task3 = TDDTask(description="Task 3")
        
        cycle.add_task(task1)
        cycle.add_task(task2)
        cycle.add_task(task3)
        
        # Complete tasks in sequence
        cycle.start_task(task1.id)
        cycle.complete_current_task()
        
        cycle.start_task(task2.id)
        cycle.complete_current_task()
        
        # Verify states before final task
        assert not cycle.is_complete()
        assert len(cycle.get_completed_tasks()) == 2
        assert len(cycle.get_pending_tasks()) == 1
        
        # Complete final task
        cycle.start_task(task3.id)
        cycle.complete_current_task()
        
        # Now cycle should be complete
        assert cycle.is_complete()
        assert cycle.current_state == TDDState.COMMIT
        assert len(cycle.get_completed_tasks()) == 3
        assert len(cycle.get_pending_tasks()) == 0
    
    def test_comprehensive_tdd_workflow(self):
        """Test complete TDD workflow from start to finish"""
        # Create a complete TDD cycle
        cycle = TDDCycle(story_id="story-comprehensive")
        
        # Create task with full workflow
        task = TDDTask(
            description="Implement calculator addition",
            acceptance_criteria=[
                "Should handle positive integers",
                "Should handle negative integers",
                "Should return correct sum"
            ],
            current_state=TDDState.DESIGN
        )
        
        cycle.add_task(task)
        cycle.start_task(task.id)
        
        # Design phase - add design notes
        task.design_notes = "Simple addition function with input validation"
        
        # Move to TEST_RED - create test file
        task.current_state = TDDState.TEST_RED
        test_file = TestFile(
            file_path="/project/tests/tdd/story-comprehensive/test_calculator.py",
            relative_path="tests/tdd/story-comprehensive/test_calculator.py",
            story_id="story-comprehensive",
            status=TestFileStatus.DRAFT
        )
        task.add_test_file(test_file)
        
        # Add failing test results
        failing_result = TestResult(
            test_file="test_calculator.py",
            test_name="test_addition",
            status=TestStatus.RED,
            output="AssertionError: Function not implemented"
        )
        task.test_results.append(failing_result)
        
        # Verify can commit tests
        assert task.can_commit_tests()
        
        # Commit test (mark as committed)
        test_file.committed_at = datetime.now().isoformat()
        test_file.status = TestFileStatus.COMMITTED
        
        # Move to CODE_GREEN
        task.current_state = TDDState.CODE_GREEN
        task.implementation_notes = "Basic addition implementation"
        
        # Add passing test result
        passing_result = TestResult(
            test_file="test_calculator.py",
            test_name="test_addition",
            status=TestStatus.GREEN,
            output="All tests passed",
            execution_time=0.05
        )
        task.test_results.append(passing_result)
        
        # Update test file with results
        test_file.update_test_results([passing_result])
        
        # Verify can commit code
        assert task.can_commit_code()
        
        # Move to REFACTOR
        task.current_state = TDDState.REFACTOR
        task.refactor_notes = "Optimized algorithm and improved readability"
        
        # Add CI status
        task.update_ci_status(CIStatus.PASSED, "ci-run-123", "https://ci.example.com/123")
        test_file.coverage_percentage = 95.0
        task.calculate_test_coverage()
        
        # Verify can commit refactor
        assert task.can_commit_refactor()
        
        # Complete task
        task.current_state = TDDState.COMMIT
        cycle.complete_current_task()
        cycle.increment_commits()
        cycle.update_ci_status(CIStatus.PASSED)
        cycle.calculate_overall_coverage()
        
        # Verify final state
        assert cycle.is_complete()
        assert cycle.total_commits == 1
        assert cycle.ci_status == CIStatus.PASSED
        assert task.test_coverage == 95.0
        
        # Test progress summary
        summary = cycle.get_progress_summary()
        assert summary["is_complete"] is True
        assert summary["completed_tasks"] == 1
        assert summary["total_tasks"] == 1
        assert summary["overall_test_coverage"] == 95.0