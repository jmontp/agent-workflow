"""
TDD Data Models for Test-Driven Development Cycle Management.

This module defines data structures for managing TDD cycles, test results,
and tasks within the TDD workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import uuid
import os


class TDDState(Enum):
    """States in the TDD cycle"""
    DESIGN = "design"           # Create specifications and acceptance criteria
    TEST_RED = "test_red"       # Write failing tests
    CODE_GREEN = "code_green"   # Implement minimal code to pass tests
    REFACTOR = "refactor"       # Improve code quality while keeping tests green
    COMMIT = "commit"           # Save progress and mark task complete


class TestStatus(Enum):
    """Test execution status"""
    NOT_RUN = "not_run"
    RED = "red"         # Failing (expected in TEST_RED state)
    GREEN = "green"     # Passing
    ERROR = "error"     # Test execution error


class CIStatus(Enum):
    """CI/CD pipeline status"""
    NOT_RUN = "not_run"
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class TestFileStatus(Enum):
    """Test file lifecycle status"""
    DRAFT = "draft"           # Being written in TEST_RED phase
    COMMITTED = "committed"   # Committed to repo with failing tests
    PASSING = "passing"       # All tests in file are passing
    INTEGRATED = "integrated" # Promoted to permanent test location


@dataclass
class TestResult:
    """Result of test execution"""
    id: str = field(default_factory=lambda: f"test-{uuid.uuid4().hex[:8]}")
    test_file: str = ""
    test_name: str = ""
    status: TestStatus = TestStatus.NOT_RUN
    output: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "test_file": self.test_file,
            "test_name": self.test_name,
            "status": self.status.value,
            "output": self.output,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        return cls(
            id=data["id"],
            test_file=data["test_file"],
            test_name=data["test_name"],
            status=TestStatus(data["status"]),
            output=data["output"],
            error_message=data.get("error_message"),
            execution_time=data.get("execution_time", 0.0),
            timestamp=data["timestamp"]
        )


@dataclass
class TestFile:
    """Manages test file lifecycle and CI integration"""
    id: str = field(default_factory=lambda: f"testfile-{uuid.uuid4().hex[:8]}")
    file_path: str = ""
    relative_path: str = ""  # Path relative to project root
    story_id: str = ""
    task_id: str = ""
    status: TestFileStatus = TestFileStatus.DRAFT
    ci_status: CIStatus = CIStatus.NOT_RUN
    test_count: int = 0
    passing_tests: int = 0
    failing_tests: int = 0
    coverage_percentage: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    committed_at: Optional[str] = None
    integrated_at: Optional[str] = None
    ci_run_id: Optional[str] = None
    ci_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "relative_path": self.relative_path,
            "story_id": self.story_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "ci_status": self.ci_status.value,
            "test_count": self.test_count,
            "passing_tests": self.passing_tests,
            "failing_tests": self.failing_tests,
            "coverage_percentage": self.coverage_percentage,
            "created_at": self.created_at,
            "committed_at": self.committed_at,
            "integrated_at": self.integrated_at,
            "ci_run_id": self.ci_run_id,
            "ci_url": self.ci_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestFile':
        return cls(
            id=data["id"],
            file_path=data["file_path"],
            relative_path=data["relative_path"],
            story_id=data["story_id"],
            task_id=data["task_id"],
            status=TestFileStatus(data["status"]),
            ci_status=CIStatus(data["ci_status"]),
            test_count=data.get("test_count", 0),
            passing_tests=data.get("passing_tests", 0),
            failing_tests=data.get("failing_tests", 0),
            coverage_percentage=data.get("coverage_percentage", 0.0),
            created_at=data["created_at"],
            committed_at=data.get("committed_at"),
            integrated_at=data.get("integrated_at"),
            ci_run_id=data.get("ci_run_id"),
            ci_url=data.get("ci_url")
        )
    
    def exists(self) -> bool:
        """Check if test file exists on filesystem"""
        return os.path.isfile(self.file_path)
    
    def is_committed(self) -> bool:
        """Check if test file has been committed to repo"""
        return self.committed_at is not None
    
    def is_passing(self) -> bool:
        """Check if all tests in file are passing"""
        return self.test_count > 0 and self.failing_tests == 0
    
    def is_integrated(self) -> bool:
        """Check if test file has been promoted to permanent location"""
        return self.integrated_at is not None
    
    def get_test_directory(self) -> str:
        """Get the TDD test directory for this file's story"""
        if self.story_id:
            return f"tests/tdd/{self.story_id}"
        return "tests/tdd"
    
    def get_permanent_location(self) -> str:
        """Get the permanent test location after integration"""
        filename = os.path.basename(self.relative_path)
        
        # Determine if this should go to unit or integration tests
        if "unit" in self.relative_path.lower() or "test_unit" in filename:
            return f"tests/unit/{filename}"
        elif "integration" in self.relative_path.lower() or "test_integration" in filename:
            return f"tests/integration/{filename}"
        else:
            # Default to unit tests
            return f"tests/unit/{filename}"
    
    def update_test_results(self, test_results: List['TestResult']) -> None:
        """Update test counts based on latest test results"""
        if not test_results:
            return
        
        # Count tests by status
        self.test_count = len(test_results)
        self.passing_tests = sum(1 for r in test_results if r.status == TestStatus.GREEN)
        self.failing_tests = sum(1 for r in test_results if r.status == TestStatus.RED)
        
        # Update file status based on test results
        if self.failing_tests == 0 and self.passing_tests > 0:
            if self.status == TestFileStatus.COMMITTED:
                self.status = TestFileStatus.PASSING
        elif self.failing_tests > 0:
            if self.status == TestFileStatus.PASSING:
                self.status = TestFileStatus.COMMITTED  # Tests are failing again


@dataclass
class TDDTask:
    """Individual task within a TDD cycle"""
    id: str = field(default_factory=lambda: f"tdd-task-{uuid.uuid4().hex[:8]}")
    cycle_id: str = ""
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    current_state: TDDState = TDDState.DESIGN
    test_files: List[str] = field(default_factory=list)  # List of file paths
    test_file_objects: List['TestFile'] = field(default_factory=list)  # TestFile objects
    source_files: List[str] = field(default_factory=list)
    test_results: List[TestResult] = field(default_factory=list)
    design_notes: str = ""
    implementation_notes: str = ""
    refactor_notes: str = ""
    ci_status: CIStatus = CIStatus.NOT_RUN
    test_coverage: float = 0.0  # Overall test coverage percentage
    ci_run_id: Optional[str] = None
    ci_url: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cycle_id": self.cycle_id,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "current_state": self.current_state.value,
            "test_files": self.test_files,
            "test_file_objects": [tf.to_dict() for tf in self.test_file_objects],
            "source_files": self.source_files,
            "test_results": [tr.to_dict() for tr in self.test_results],
            "design_notes": self.design_notes,
            "implementation_notes": self.implementation_notes,
            "refactor_notes": self.refactor_notes,
            "ci_status": self.ci_status.value,
            "test_coverage": self.test_coverage,
            "ci_run_id": self.ci_run_id,
            "ci_url": self.ci_url,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TDDTask':
        return cls(
            id=data["id"],
            cycle_id=data["cycle_id"],
            description=data["description"],
            acceptance_criteria=data.get("acceptance_criteria", []),
            current_state=TDDState(data["current_state"]),
            test_files=data.get("test_files", []),
            test_file_objects=[TestFile.from_dict(tf) for tf in data.get("test_file_objects", [])],
            source_files=data.get("source_files", []),
            test_results=[TestResult.from_dict(tr) for tr in data.get("test_results", [])],
            design_notes=data.get("design_notes", ""),
            implementation_notes=data.get("implementation_notes", ""),
            refactor_notes=data.get("refactor_notes", ""),
            ci_status=CIStatus(data.get("ci_status", "not_run")),
            test_coverage=data.get("test_coverage", 0.0),
            ci_run_id=data.get("ci_run_id"),
            ci_url=data.get("ci_url"),
            started_at=data["started_at"],
            completed_at=data.get("completed_at")
        )
    
    def is_complete(self) -> bool:
        """Check if task has been completed (committed)"""
        return self.completed_at is not None
    
    def get_latest_test_results(self) -> List[TestResult]:
        """Get the most recent test results"""
        if not self.test_results:
            return []
        
        # Group by test file and name, keep latest timestamp
        latest_results = {}
        for result in self.test_results:
            key = (result.test_file, result.test_name)
            if key not in latest_results or result.timestamp > latest_results[key].timestamp:
                latest_results[key] = result
        
        return list(latest_results.values())
    
    def has_passing_tests(self) -> bool:
        """Check if all tests are currently passing"""
        latest_results = self.get_latest_test_results()
        if not latest_results:
            return False
        
        return all(result.status == TestStatus.GREEN for result in latest_results)
    
    def has_failing_tests(self) -> bool:
        """Check if any tests are currently failing"""
        latest_results = self.get_latest_test_results()
        return any(result.status == TestStatus.RED for result in latest_results)
    
    def add_test_file(self, test_file: 'TestFile') -> None:
        """Add a test file to this task"""
        test_file.task_id = self.id
        self.test_file_objects.append(test_file)
        if test_file.file_path not in self.test_files:
            self.test_files.append(test_file.file_path)
    
    def get_test_file_by_path(self, file_path: str) -> Optional['TestFile']:
        """Get test file object by file path"""
        return next((tf for tf in self.test_file_objects if tf.file_path == file_path), None)
    
    def get_committed_test_files(self) -> List['TestFile']:
        """Get all test files that have been committed to repo"""
        return [tf for tf in self.test_file_objects if tf.is_committed()]
    
    def get_passing_test_files(self) -> List['TestFile']:
        """Get all test files with passing tests"""
        return [tf for tf in self.test_file_objects if tf.is_passing()]
    
    def update_ci_status(self, status: CIStatus, ci_run_id: Optional[str] = None, ci_url: Optional[str] = None) -> None:
        """Update CI status for this task"""
        self.ci_status = status
        if ci_run_id:
            self.ci_run_id = ci_run_id
        if ci_url:
            self.ci_url = ci_url
    
    def calculate_test_coverage(self) -> float:
        """Calculate overall test coverage for this task"""
        if not self.test_file_objects:
            return 0.0
        
        total_coverage = sum(tf.coverage_percentage for tf in self.test_file_objects)
        self.test_coverage = total_coverage / len(self.test_file_objects)
        return self.test_coverage
    
    def can_commit_tests(self) -> bool:
        """Check if tests are ready to be committed (in RED state with failing tests)"""
        return (self.current_state == TDDState.TEST_RED and 
                self.has_failing_tests() and 
                len(self.test_file_objects) > 0)
    
    def can_commit_code(self) -> bool:
        """Check if code can be committed (tests are passing)"""
        return (self.current_state == TDDState.CODE_GREEN and 
                self.has_passing_tests() and 
                all(tf.is_committed() for tf in self.test_file_objects))
    
    def can_commit_refactor(self) -> bool:
        """Check if refactored code can be committed (tests still passing)"""
        return (self.current_state == TDDState.REFACTOR and 
                self.has_passing_tests() and 
                all(tf.is_committed() for tf in self.test_file_objects))


@dataclass
class TDDCycle:
    """TDD cycle linked to a story"""
    id: str = field(default_factory=lambda: f"tdd-cycle-{uuid.uuid4().hex[:8]}")
    story_id: str = ""
    current_state: TDDState = TDDState.DESIGN
    current_task_id: Optional[str] = None  # Only one active task at a time
    tasks: List[TDDTask] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    total_test_runs: int = 0
    total_refactors: int = 0
    total_commits: int = 0
    ci_status: CIStatus = CIStatus.NOT_RUN
    overall_test_coverage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "story_id": self.story_id,
            "current_state": self.current_state.value,
            "current_task_id": self.current_task_id,
            "tasks": [task.to_dict() for task in self.tasks],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_test_runs": self.total_test_runs,
            "total_refactors": self.total_refactors,
            "total_commits": self.total_commits,
            "ci_status": self.ci_status.value,
            "overall_test_coverage": self.overall_test_coverage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TDDCycle':
        return cls(
            id=data["id"],
            story_id=data["story_id"],
            current_state=TDDState(data["current_state"]),
            current_task_id=data.get("current_task_id"),
            tasks=[TDDTask.from_dict(task) for task in data.get("tasks", [])],
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            total_test_runs=data.get("total_test_runs", 0),
            total_refactors=data.get("total_refactors", 0),
            total_commits=data.get("total_commits", 0),
            ci_status=CIStatus(data.get("ci_status", "not_run")),
            overall_test_coverage=data.get("overall_test_coverage", 0.0)
        )
    
    def is_complete(self) -> bool:
        """Check if the TDD cycle is complete"""
        return self.completed_at is not None
    
    def get_current_task(self) -> Optional[TDDTask]:
        """Get the currently active task"""
        if not self.current_task_id:
            return None
        
        return next((task for task in self.tasks if task.id == self.current_task_id), None)
    
    def get_completed_tasks(self) -> List[TDDTask]:
        """Get all completed tasks in this cycle"""
        return [task for task in self.tasks if task.is_complete()]
    
    def get_pending_tasks(self) -> List[TDDTask]:
        """Get all pending (not started or incomplete) tasks"""
        return [task for task in self.tasks if not task.is_complete()]
    
    def add_task(self, task: TDDTask) -> None:
        """Add a new task to the cycle"""
        task.cycle_id = self.id
        self.tasks.append(task)
    
    def start_task(self, task_id: str) -> bool:
        """Start a specific task (only one can be active)"""
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            return False
        
        self.current_task_id = task_id
        self.current_state = task.current_state
        return True
    
    def complete_current_task(self) -> bool:
        """Mark current task as complete and reset current task"""
        current_task = self.get_current_task()
        if not current_task:
            return False
        
        current_task.completed_at = datetime.now().isoformat()
        self.current_task_id = None
        
        # If all tasks are complete, complete the cycle
        if all(task.is_complete() for task in self.tasks):
            self.completed_at = datetime.now().isoformat()
            self.current_state = TDDState.COMMIT
        else:
            # Reset to DESIGN state for next task
            self.current_state = TDDState.DESIGN
        
        return True
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get progress summary for the cycle"""
        completed_tasks = len(self.get_completed_tasks())
        total_tasks = len(self.tasks)
        
        return {
            "cycle_id": self.id,
            "story_id": self.story_id,
            "current_state": self.current_state.value,
            "current_task_id": self.current_task_id,
            "progress": f"{completed_tasks}/{total_tasks}",
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "total_test_runs": self.total_test_runs,
            "total_refactors": self.total_refactors,
            "total_commits": self.total_commits,
            "ci_status": self.ci_status.value,
            "overall_test_coverage": self.overall_test_coverage,
            "is_complete": self.is_complete(),
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    def get_all_test_files(self) -> List['TestFile']:
        """Get all test files across all tasks in this cycle"""
        test_files = []
        for task in self.tasks:
            test_files.extend(task.test_file_objects)
        return test_files
    
    def get_committed_test_files(self) -> List['TestFile']:
        """Get all committed test files in this cycle"""
        return [tf for tf in self.get_all_test_files() if tf.is_committed()]
    
    def get_passing_test_files(self) -> List['TestFile']:
        """Get all test files with passing tests in this cycle"""
        return [tf for tf in self.get_all_test_files() if tf.is_passing()]
    
    def calculate_overall_coverage(self) -> float:
        """Calculate overall test coverage for the entire cycle"""
        test_files = self.get_all_test_files()
        if not test_files:
            return 0.0
        
        total_coverage = sum(tf.coverage_percentage for tf in test_files)
        self.overall_test_coverage = total_coverage / len(test_files)
        return self.overall_test_coverage
    
    def increment_commits(self) -> None:
        """Increment the commit counter"""
        self.total_commits += 1
    
    def update_ci_status(self, status: CIStatus) -> None:
        """Update CI status for the entire cycle"""
        self.ci_status = status
    
    def get_test_directory_structure(self) -> Dict[str, List[str]]:
        """Get the test directory structure for this cycle"""
        structure = {
            "tdd": [],
            "unit": [],
            "integration": [],
            "ci": []
        }
        
        for test_file in self.get_all_test_files():
            if "tdd" in test_file.relative_path:
                structure["tdd"].append(test_file.relative_path)
            elif "unit" in test_file.relative_path:
                structure["unit"].append(test_file.relative_path)
            elif "integration" in test_file.relative_path:
                structure["integration"].append(test_file.relative_path)
            elif "ci" in test_file.relative_path:
                structure["ci"].append(test_file.relative_path)
        
        return structure