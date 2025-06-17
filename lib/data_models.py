"""
Data models for project management entities.

This module defines the core data structures for managing projects,
including epics, stories, sprints, and tasks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import uuid


class EpicStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class StoryStatus(Enum):
    BACKLOG = "backlog"
    SPRINT = "sprint"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class SprintStatus(Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class Epic:
    """Represents a high-level project epic."""
    id: str = field(default_factory=lambda: f"epic-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: EpicStatus = EpicStatus.ACTIVE
    
    # TDD orchestration fields
    tdd_requirements: List[str] = field(default_factory=list)  # TDD-specific requirements
    tdd_constraints: Dict[str, Any] = field(default_factory=dict)  # TDD constraints and policies
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.status.value,
            "tdd_requirements": self.tdd_requirements,
            "tdd_constraints": self.tdd_constraints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Epic':
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            created_at=data["created_at"],
            status=EpicStatus(data["status"]),
            tdd_requirements=data.get("tdd_requirements", []),
            tdd_constraints=data.get("tdd_constraints", {})
        )


@dataclass
class Story:
    """Represents a user story within an epic."""
    id: str = field(default_factory=lambda: f"story-{uuid.uuid4().hex[:8]}")
    epic_id: Optional[str] = None
    title: str = ""
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    priority: int = 3  # 1-5 scale, 1 being highest priority
    status: StoryStatus = StoryStatus.BACKLOG
    sprint_id: Optional[str] = None
    tdd_cycle_id: Optional[str] = None  # Link to TDD cycle
    test_status: str = "not_started"  # not_started, red, green, refactor, complete
    test_files: List[str] = field(default_factory=list)  # Array of test file paths
    ci_status: str = "not_run"  # not_run, pending, running, passed, failed, error
    test_coverage: float = 0.0  # Test coverage percentage
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "epic_id": self.epic_id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "priority": self.priority,
            "status": self.status.value,
            "sprint_id": self.sprint_id,
            "tdd_cycle_id": self.tdd_cycle_id,
            "test_status": self.test_status,
            "test_files": self.test_files,
            "ci_status": self.ci_status,
            "test_coverage": self.test_coverage,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Story':
        return cls(
            id=data["id"],
            epic_id=data.get("epic_id"),
            title=data["title"],
            description=data["description"],
            acceptance_criteria=data.get("acceptance_criteria", []),
            priority=data.get("priority", 3),
            status=StoryStatus(data["status"]),
            sprint_id=data.get("sprint_id"),
            tdd_cycle_id=data.get("tdd_cycle_id"),
            test_status=data.get("test_status", "not_started"),
            test_files=data.get("test_files", []),
            ci_status=data.get("ci_status", "not_run"),
            test_coverage=data.get("test_coverage", 0.0),
            created_at=data["created_at"]
        )


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
    """Represents a development sprint."""
    id: str = field(default_factory=lambda: f"sprint-{uuid.uuid4().hex[:8]}")
    goal: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    story_ids: List[str] = field(default_factory=list)
    status: SprintStatus = SprintStatus.PLANNED
    retrospective: Optional[Retrospective] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # TDD orchestration fields
    active_tdd_cycles: List[str] = field(default_factory=list)  # List of active TDD cycle IDs
    tdd_metrics: Dict[str, Any] = field(default_factory=dict)  # Sprint-level TDD metrics
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "goal": self.goal,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "story_ids": self.story_ids,
            "status": self.status.value,
            "created_at": self.created_at,
            "active_tdd_cycles": self.active_tdd_cycles,
            "tdd_metrics": self.tdd_metrics
        }
        if self.retrospective:
            data["retrospective"] = self.retrospective.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sprint':
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
            active_tdd_cycles=data.get("active_tdd_cycles", []),
            tdd_metrics=data.get("tdd_metrics", {})
        )


@dataclass
class ProjectData:
    """Container for all project management data."""
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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "epics": [epic.to_dict() for epic in self.epics],
            "stories": [story.to_dict() for story in self.stories],
            "sprints": [sprint.to_dict() for sprint in self.sprints],
            "tdd_settings": self.tdd_settings
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
            tdd_settings=data.get("tdd_settings", default_tdd_settings)
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