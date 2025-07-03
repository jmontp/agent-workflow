"""
Data models for agent-workflow package.

This module provides data classes for core entities like Projects, Epics,
Stories, and Sprints with serialization capabilities, as well as TDD-specific
models for test-driven development workflows.
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


# Priority and Status Enums
class Priority(Enum):
    """Priority levels for stories and tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EpicStatus(Enum):
    """Status of an epic."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class StoryStatus(Enum):
    """Status of a user story."""
    BACKLOG = "backlog"
    SPRINT = "sprint"  # In a sprint
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class SprintStatus(Enum):
    """Status of a sprint."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# TDD-specific Enums
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
class Epic:
    """
    Represents a high-level initiative or epic.
    
    Epics are large bodies of work that can be broken down
    into multiple user stories.
    """
    id: str = field(default_factory=lambda: f"epic-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: EpicStatus = EpicStatus.ACTIVE
    priority: Priority = Priority.MEDIUM
    stories: List[str] = field(default_factory=list)  # Story IDs
    acceptance_criteria: List[str] = field(default_factory=list)
    business_value: Optional[str] = None
    estimated_effort: Optional[int] = None  # Story points
    actual_effort: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # TDD orchestration fields
    tdd_requirements: List[str] = field(default_factory=list)  # TDD-specific requirements
    tdd_constraints: Dict[str, Any] = field(default_factory=dict)  # TDD constraints and policies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.status.value,
            "priority": self.priority.value,
            "stories": self.stories,
            "acceptance_criteria": self.acceptance_criteria,
            "business_value": self.business_value,
            "estimated_effort": self.estimated_effort,
            "actual_effort": self.actual_effort,
            "tags": self.tags,
            "metadata": self.metadata,
            "tdd_requirements": self.tdd_requirements,
            "tdd_constraints": self.tdd_constraints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Epic":
        """Create Epic from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            created_at=data["created_at"],
            status=EpicStatus(data["status"]),
            priority=Priority(data.get("priority", "medium")),
            stories=data.get("stories", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
            business_value=data.get("business_value"),
            estimated_effort=data.get("estimated_effort"),
            actual_effort=data.get("actual_effort"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            tdd_requirements=data.get("tdd_requirements", []),
            tdd_constraints=data.get("tdd_constraints", {})
        )
    
    def add_story(self, story_id: str) -> None:
        """Add a story to this epic."""
        if story_id not in self.stories:
            self.stories.append(story_id)
    
    def remove_story(self, story_id: str) -> None:
        """Remove a story from this epic."""
        if story_id in self.stories:
            self.stories.remove(story_id)
    
    def get_progress(self, story_statuses: Dict[str, StoryStatus]) -> Dict[str, Any]:
        """Calculate epic progress based on story statuses."""
        if not self.stories:
            return {"percentage": 0, "completed": 0, "total": 0}
        
        completed = sum(1 for story_id in self.stories 
                       if story_statuses.get(story_id) == StoryStatus.DONE)
        total = len(self.stories)
        percentage = (completed / total) * 100 if total > 0 else 0
        
        return {
            "percentage": percentage,
            "completed": completed,
            "total": total,
            "remaining": total - completed
        }


@dataclass
class Story:
    """
    Represents a user story in the product backlog.
    
    Stories are small, manageable pieces of functionality
    written from the user's perspective.
    """
    id: str = field(default_factory=lambda: f"story-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: StoryStatus = StoryStatus.BACKLOG
    priority: int = 3  # 1-5 scale, 1 being highest priority (keeping int for compatibility)
    epic_id: Optional[str] = None
    story_points: Optional[int] = None
    acceptance_criteria: List[str] = field(default_factory=list)
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    assigned_to: Optional[str] = None  # Agent or team member
    sprint_id: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Other story IDs
    blocked_by: List[str] = field(default_factory=list)
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # TDD-specific fields
    tdd_cycle_id: Optional[str] = None  # Link to TDD cycle
    test_status: str = "not_started"  # not_started, red, green, refactor, complete
    test_files: List[str] = field(default_factory=list)  # Array of test file paths
    ci_status: str = "not_run"  # not_run, pending, running, passed, failed, error
    test_coverage: float = 0.0  # Test coverage percentage
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.status.value,
            "priority": self.priority,
            "epic_id": self.epic_id,
            "story_points": self.story_points,
            "acceptance_criteria": self.acceptance_criteria,
            "tasks": self.tasks,
            "assigned_to": self.assigned_to,
            "sprint_id": self.sprint_id,
            "labels": self.labels,
            "dependencies": self.dependencies,
            "blocked_by": self.blocked_by,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "metadata": self.metadata,
            "tdd_cycle_id": self.tdd_cycle_id,
            "test_status": self.test_status,
            "test_files": self.test_files,
            "ci_status": self.ci_status,
            "test_coverage": self.test_coverage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Story":
        """Create Story from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            created_at=data["created_at"],
            status=StoryStatus(data["status"]),
            priority=data.get("priority", 3),
            epic_id=data.get("epic_id"),
            story_points=data.get("story_points"),
            acceptance_criteria=data.get("acceptance_criteria", []),
            tasks=data.get("tasks", []),
            assigned_to=data.get("assigned_to"),
            sprint_id=data.get("sprint_id"),
            labels=data.get("labels", []),
            dependencies=data.get("dependencies", []),
            blocked_by=data.get("blocked_by", []),
            estimated_hours=data.get("estimated_hours"),
            actual_hours=data.get("actual_hours"),
            metadata=data.get("metadata", {}),
            tdd_cycle_id=data.get("tdd_cycle_id"),
            test_status=data.get("test_status", "not_started"),
            test_files=data.get("test_files", []),
            ci_status=data.get("ci_status", "not_run"),
            test_coverage=data.get("test_coverage", 0.0)
        )
    
    def add_task(self, task: Dict[str, Any]) -> None:
        """Add a task to this story."""
        task["id"] = f"{self.id}_task_{len(self.tasks) + 1}"
        task["created"] = datetime.now().isoformat()
        task["status"] = task.get("status", "todo")
        self.tasks.append(task)
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update the status of a task."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = status
                task["updated"] = datetime.now().isoformat()
                return True
        return False
    
    def get_completion_percentage(self) -> float:
        """Calculate story completion based on task status."""
        if not self.tasks:
            return 100.0 if self.status == StoryStatus.DONE else 0.0
        
        completed_tasks = sum(1 for task in self.tasks if task.get("status") == "done")
        return (completed_tasks / len(self.tasks)) * 100
    
    def is_blocked(self) -> bool:
        """Check if story is blocked by dependencies."""
        return bool(self.blocked_by) or self.status == StoryStatus.BLOCKED
    
    def can_start(self, other_stories: Dict[str, "Story"]) -> bool:
        """Check if story can be started based on dependencies."""
        if self.is_blocked():
            return False
        
        # Check dependencies
        for dep_id in self.dependencies:
            if dep_id in other_stories:
                dep_story = other_stories[dep_id]
                if dep_story.status != StoryStatus.DONE:
                    return False
        
        return True


@dataclass
class Retrospective:
    """Sprint retrospective data."""
    what_went_well: List[str] = field(default_factory=list)
    what_could_improve: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "what_went_well": self.what_went_well,
            "what_could_improve": self.what_could_improve,
            "action_items": self.action_items
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Retrospective':
        return cls(
            what_went_well=data.get("what_went_well", []),
            what_could_improve=data.get("what_could_improve", []),
            action_items=data.get("action_items", [])
        )


@dataclass
class Sprint:
    """
    Represents a sprint in the Scrum methodology.
    
    Sprints are time-boxed iterations containing a set of
    stories to be completed.
    """
    id: str = field(default_factory=lambda: f"sprint-{uuid.uuid4().hex[:8]}")
    goal: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    story_ids: List[str] = field(default_factory=list)
    status: SprintStatus = SprintStatus.PLANNED
    retrospective: Optional[Retrospective] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Additional fields from agent_workflow
    name: str = ""
    description: str = ""
    capacity: Optional[int] = None  # Story points
    velocity: Optional[int] = None  # Actual completed points
    team_members: List[str] = field(default_factory=list)
    retrospective_notes: List[str] = field(default_factory=list)
    burndown_data: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # TDD orchestration fields
    active_tdd_cycles: List[str] = field(default_factory=list)  # List of active TDD cycle IDs
    tdd_metrics: Dict[str, Any] = field(default_factory=dict)  # Sprint-level TDD metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "id": self.id,
            "goal": self.goal,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "story_ids": self.story_ids,
            "status": self.status.value,
            "created_at": self.created_at,
            "name": self.name,
            "description": self.description,
            "capacity": self.capacity,
            "velocity": self.velocity,
            "team_members": self.team_members,
            "retrospective_notes": self.retrospective_notes,
            "burndown_data": self.burndown_data,
            "metadata": self.metadata,
            "active_tdd_cycles": self.active_tdd_cycles,
            "tdd_metrics": self.tdd_metrics
        }
        if self.retrospective:
            data["retrospective"] = self.retrospective.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sprint":
        """Create Sprint from dictionary."""
        retrospective = None
        if "retrospective" in data:
            retrospective = Retrospective.from_dict(data["retrospective"])
        
        return cls(
            id=data["id"],
            goal=data["goal"],
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            story_ids=data.get("story_ids", []),
            status=SprintStatus(data["status"]),
            retrospective=retrospective,
            created_at=data["created_at"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            capacity=data.get("capacity"),
            velocity=data.get("velocity"),
            team_members=data.get("team_members", []),
            retrospective_notes=data.get("retrospective_notes", []),
            burndown_data=data.get("burndown_data", []),
            metadata=data.get("metadata", {}),
            active_tdd_cycles=data.get("active_tdd_cycles", []),
            tdd_metrics=data.get("tdd_metrics", {})
        )
    
    def add_story(self, story_id: str) -> None:
        """Add a story to this sprint."""
        if story_id not in self.story_ids:
            self.story_ids.append(story_id)
    
    def remove_story(self, story_id: str) -> None:
        """Remove a story from this sprint."""
        if story_id in self.story_ids:
            self.story_ids.remove(story_id)
    
    def start_sprint(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> None:
        """Start the sprint."""
        self.status = SprintStatus.ACTIVE
        self.start_date = start_date or datetime.now().isoformat()
        if end_date:
            self.end_date = end_date
    
    def complete_sprint(self) -> None:
        """Complete the sprint."""
        self.status = SprintStatus.COMPLETED
        if not self.end_date:
            self.end_date = datetime.now().isoformat()
    
    def calculate_velocity(self, story_points: Dict[str, int]) -> int:
        """Calculate sprint velocity based on completed stories."""
        completed_points = 0
        for story_id in self.story_ids:
            if story_id in story_points:
                completed_points += story_points[story_id]
        
        self.velocity = completed_points
        return completed_points
    
    def get_burndown_point(self, date: str, remaining_points: int) -> None:
        """Add a burndown chart data point."""
        self.burndown_data.append({
            "date": date,
            "remaining_points": remaining_points
        })
    
    def get_duration_days(self) -> Optional[int]:
        """Get sprint duration in days."""
        if self.start_date and self.end_date:
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
            return (end - start).days
        return None


# TDD-specific Models
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


@dataclass
class ProjectData:
    """
    Container for all project management data.
    
    This is the main container for project management data including
    epics, stories, sprints, and TDD configuration.
    """
    epics: List[Epic] = field(default_factory=list)
    stories: List[Story] = field(default_factory=list)
    sprints: List[Sprint] = field(default_factory=list)
    
    # TDD orchestration configuration
    tdd_settings: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "max_concurrent_cycles": 3,
        "auto_commit_tests": True,
        "require_coverage_threshold": 80.0,
        "test_directory_structure": {
            "tdd": "tests/tdd",
            "unit": "tests/unit",
            "integration": "tests/integration"
        },
        "ci_integration": {
            "enabled": True,
            "webhook_url": "",
            "fail_on_coverage_drop": True
        }
    })
    
    # Additional fields from agent_workflow
    project_name: str = ""
    created: Optional[str] = None
    updated: Optional[str] = None
    current_sprint_id: Optional[str] = None
    next_epic_id: int = 1
    next_story_id: int = 1
    next_sprint_id: int = 1
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "epics": [epic.to_dict() for epic in self.epics],
            "stories": [story.to_dict() for story in self.stories],
            "sprints": [sprint.to_dict() for sprint in self.sprints],
            "tdd_settings": self.tdd_settings,
            "project_name": self.project_name,
            "created": self.created or datetime.now().isoformat(),
            "updated": self.updated or datetime.now().isoformat(),
            "current_sprint_id": self.current_sprint_id,
            "next_epic_id": self.next_epic_id,
            "next_story_id": self.next_story_id,
            "next_sprint_id": self.next_sprint_id,
            "settings": self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectData':
        # Create default TDD settings if not present
        default_tdd_settings = {
            "enabled": True,
            "max_concurrent_cycles": 3,
            "auto_commit_tests": True,
            "require_coverage_threshold": 80.0,
            "test_directory_structure": {
                "tdd": "tests/tdd",
                "unit": "tests/unit",
                "integration": "tests/integration"
            },
            "ci_integration": {
                "enabled": True,
                "webhook_url": "",
                "fail_on_coverage_drop": True
            }
        }
        
        return cls(
            epics=[Epic.from_dict(epic_data) for epic_data in data.get("epics", [])],
            stories=[Story.from_dict(story_data) for story_data in data.get("stories", [])],
            sprints=[Sprint.from_dict(sprint_data) for sprint_data in data.get("sprints", [])],
            tdd_settings=data.get("tdd_settings", default_tdd_settings),
            project_name=data.get("project_name", ""),
            created=data.get("created"),
            updated=data.get("updated"),
            current_sprint_id=data.get("current_sprint_id"),
            next_epic_id=data.get("next_epic_id", 1),
            next_story_id=data.get("next_story_id", 1),
            next_sprint_id=data.get("next_sprint_id", 1),
            settings=data.get("settings", {})
        )
    
    def get_epic_by_id(self, epic_id: str) -> Optional[Epic]:
        """Find an epic by ID."""
        return next((epic for epic in self.epics if epic.id == epic_id), None)
    
    def get_story_by_id(self, story_id: str) -> Optional[Story]:
        """Find a story by ID."""
        return next((story for story in self.stories if story.id == story_id), None)
    
    def get_sprint_by_id(self, sprint_id: str) -> Optional[Sprint]:
        """Find a sprint by ID."""
        return next((sprint for sprint in self.sprints if sprint.id == sprint_id), None)
    
    def get_stories_by_epic(self, epic_id: str) -> List[Story]:
        """Get all stories for a specific epic."""
        return [story for story in self.stories if story.epic_id == epic_id]
    
    def get_stories_by_sprint(self, sprint_id: str) -> List[Story]:
        """Get all stories for a specific sprint."""
        return [story for story in self.stories if story.sprint_id == sprint_id]
    
    def get_backlog_stories(self) -> List[Story]:
        """Get all stories in the backlog (not assigned to a sprint)."""
        return [story for story in self.stories if story.status == StoryStatus.BACKLOG]
    
    def get_active_sprint(self) -> Optional[Sprint]:
        """Get the currently active sprint."""
        return next((sprint for sprint in self.sprints if sprint.status == SprintStatus.ACTIVE), None)
    
    def get_stories_with_tdd_cycles(self) -> List[Story]:
        """Get all stories that have TDD cycles"""
        return [story for story in self.stories if story.tdd_cycle_id]
    
    def get_stories_ready_for_tdd(self) -> List[Story]:
        """Get stories ready for TDD (no active cycle, has acceptance criteria)"""
        return [
            story for story in self.stories 
            if not story.tdd_cycle_id and 
               story.acceptance_criteria and 
               story.status in [StoryStatus.SPRINT, StoryStatus.IN_PROGRESS]
        ]
    
    def update_tdd_settings(self, new_settings: Dict[str, Any]) -> None:
        """Update TDD configuration settings"""
        self.tdd_settings.update(new_settings)
    
    def is_tdd_enabled(self) -> bool:
        """Check if TDD is enabled for this project"""
        return self.tdd_settings.get("enabled", True)
    
    def get_max_concurrent_tdd_cycles(self) -> int:
        """Get maximum allowed concurrent TDD cycles"""
        return self.tdd_settings.get("max_concurrent_cycles", 3)
    
    def get_coverage_threshold(self) -> float:
        """Get required test coverage threshold"""
        return self.tdd_settings.get("require_coverage_threshold", 80.0)
    
    def get_test_directory_for_type(self, test_type: str) -> str:
        """Get test directory path for a specific test type"""
        test_dirs = self.tdd_settings.get("test_directory_structure", {})
        return test_dirs.get(test_type, f"tests/{test_type}")
    
    def add_tdd_cycle_to_sprint(self, sprint_id: str, cycle_id: str) -> bool:
        """Add TDD cycle to active sprint tracking"""
        sprint = self.get_sprint_by_id(sprint_id)
        if sprint and cycle_id not in sprint.active_tdd_cycles:
            sprint.active_tdd_cycles.append(cycle_id)
            return True
        return False
    
    def remove_tdd_cycle_from_sprint(self, sprint_id: str, cycle_id: str) -> bool:
        """Remove TDD cycle from sprint tracking"""
        sprint = self.get_sprint_by_id(sprint_id)
        if sprint and cycle_id in sprint.active_tdd_cycles:
            sprint.active_tdd_cycles.remove(cycle_id)
            return True
        return False
    
    def update_sprint_tdd_metrics(self, sprint_id: str, metrics: Dict[str, Any]) -> bool:
        """Update TDD metrics for a sprint"""
        sprint = self.get_sprint_by_id(sprint_id)
        if sprint:
            sprint.tdd_metrics.update(metrics)
            return True
        return False
    
    def create_epic(self, title: str, description: str, **kwargs) -> Epic:
        """Create a new epic."""
        epic_id = f"epic_{self.next_epic_id}"
        self.next_epic_id += 1
        
        epic = Epic(
            id=epic_id,
            title=title,
            description=description,
            **kwargs
        )
        
        self.epics.append(epic)
        self.updated = datetime.now().isoformat()
        return epic
    
    def create_story(self, title: str, description: str, epic_id: Optional[str] = None, **kwargs) -> Story:
        """Create a new story."""
        story_id = f"story_{self.next_story_id}"
        self.next_story_id += 1
        
        story = Story(
            id=story_id,
            title=title,
            description=description,
            epic_id=epic_id,
            **kwargs
        )
        
        self.stories.append(story)
        
        # Add to epic if specified
        if epic_id:
            epic = self.get_epic_by_id(epic_id)
            if epic:
                epic.add_story(story_id)
        
        self.updated = datetime.now().isoformat()
        return story
    
    def create_sprint(self, name: str, description: str, **kwargs) -> Sprint:
        """Create a new sprint."""
        sprint_id = f"sprint_{self.next_sprint_id}"
        self.next_sprint_id += 1
        
        sprint = Sprint(
            id=sprint_id,
            name=name,
            description=description,
            goal=kwargs.get("goal", description),  # Use description as goal if not provided
            **kwargs
        )
        
        self.sprints.append(sprint)
        self.updated = datetime.now().isoformat()
        return sprint
    
    def get_current_sprint(self) -> Optional[Sprint]:
        """Get the current active sprint."""
        if self.current_sprint_id:
            sprint = self.get_sprint_by_id(self.current_sprint_id)
            if sprint:
                return sprint
        # Fallback to finding any active sprint
        return self.get_active_sprint()
    
    def get_epic_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get progress for all epics."""
        story_statuses = {story.id: story.status for story in self.stories}
        return {epic.id: epic.get_progress(story_statuses) 
                for epic in self.epics}
    
    def export_to_json(self) -> str:
        """Export all project data to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def import_from_json(cls, json_str: str) -> "ProjectData":
        """Import project data from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)