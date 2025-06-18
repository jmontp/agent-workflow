"""
Data models for agent-workflow package.

This module provides data classes for core entities like Projects, Epics,
Stories, and Sprints with serialization capabilities.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class Priority(Enum):
    """Priority levels for stories and tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StoryStatus(Enum):
    """Status of a user story."""
    BACKLOG = "backlog"
    PLANNED = "planned"
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


@dataclass
class Epic:
    """
    Represents a high-level initiative or epic.
    
    Epics are large bodies of work that can be broken down
    into multiple user stories.
    """
    id: str
    title: str
    description: str
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    priority: Priority = Priority.MEDIUM
    status: str = "active"
    stories: List[str] = field(default_factory=list)  # Story IDs
    acceptance_criteria: List[str] = field(default_factory=list)
    business_value: Optional[str] = None
    estimated_effort: Optional[int] = None  # Story points
    actual_effort: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data["created"] = self.created.isoformat()
        data["updated"] = self.updated.isoformat()
        data["priority"] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Epic":
        """Create Epic from dictionary."""
        # Convert ISO strings back to datetime
        if isinstance(data["created"], str):
            data["created"] = datetime.fromisoformat(data["created"])
        if isinstance(data["updated"], str):
            data["updated"] = datetime.fromisoformat(data["updated"])
        
        # Convert priority string to enum
        if isinstance(data["priority"], str):
            data["priority"] = Priority(data["priority"])
        
        return cls(**data)
    
    def add_story(self, story_id: str) -> None:
        """Add a story to this epic."""
        if story_id not in self.stories:
            self.stories.append(story_id)
            self.updated = datetime.now()
    
    def remove_story(self, story_id: str) -> None:
        """Remove a story from this epic."""
        if story_id in self.stories:
            self.stories.remove(story_id)
            self.updated = datetime.now()
    
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
    id: str
    title: str
    description: str
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    status: StoryStatus = StoryStatus.BACKLOG
    priority: Priority = Priority.MEDIUM
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data["created"] = self.created.isoformat()
        data["updated"] = self.updated.isoformat()
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Story":
        """Create Story from dictionary."""
        # Convert ISO strings back to datetime
        if isinstance(data["created"], str):
            data["created"] = datetime.fromisoformat(data["created"])
        if isinstance(data["updated"], str):
            data["updated"] = datetime.fromisoformat(data["updated"])
        
        # Convert enum strings
        if isinstance(data["status"], str):
            data["status"] = StoryStatus(data["status"])
        if isinstance(data["priority"], str):
            data["priority"] = Priority(data["priority"])
        
        return cls(**data)
    
    def add_task(self, task: Dict[str, Any]) -> None:
        """Add a task to this story."""
        task["id"] = f"{self.id}_task_{len(self.tasks) + 1}"
        task["created"] = datetime.now().isoformat()
        task["status"] = task.get("status", "todo")
        self.tasks.append(task)
        self.updated = datetime.now()
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update the status of a task."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = status
                task["updated"] = datetime.now().isoformat()
                self.updated = datetime.now()
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
class Sprint:
    """
    Represents a sprint in the Scrum methodology.
    
    Sprints are time-boxed iterations containing a set of
    stories to be completed.
    """
    id: str
    name: str
    description: str
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: SprintStatus = SprintStatus.PLANNED
    goal: Optional[str] = None
    stories: List[str] = field(default_factory=list)  # Story IDs
    capacity: Optional[int] = None  # Story points
    velocity: Optional[int] = None  # Actual completed points
    team_members: List[str] = field(default_factory=list)
    retrospective_notes: List[str] = field(default_factory=list)
    burndown_data: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data["created"] = self.created.isoformat()
        data["updated"] = self.updated.isoformat()
        data["start_date"] = self.start_date.isoformat() if self.start_date else None
        data["end_date"] = self.end_date.isoformat() if self.end_date else None
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sprint":
        """Create Sprint from dictionary."""
        # Convert ISO strings back to datetime
        if isinstance(data["created"], str):
            data["created"] = datetime.fromisoformat(data["created"])
        if isinstance(data["updated"], str):
            data["updated"] = datetime.fromisoformat(data["updated"])
        if data.get("start_date") and isinstance(data["start_date"], str):
            data["start_date"] = datetime.fromisoformat(data["start_date"])
        if data.get("end_date") and isinstance(data["end_date"], str):
            data["end_date"] = datetime.fromisoformat(data["end_date"])
        
        # Convert status string to enum
        if isinstance(data["status"], str):
            data["status"] = SprintStatus(data["status"])
        
        return cls(**data)
    
    def add_story(self, story_id: str) -> None:
        """Add a story to this sprint."""
        if story_id not in self.stories:
            self.stories.append(story_id)
            self.updated = datetime.now()
    
    def remove_story(self, story_id: str) -> None:
        """Remove a story from this sprint."""
        if story_id in self.stories:
            self.stories.remove(story_id)
            self.updated = datetime.now()
    
    def start_sprint(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> None:
        """Start the sprint."""
        self.status = SprintStatus.ACTIVE
        self.start_date = start_date or datetime.now()
        if end_date:
            self.end_date = end_date
        self.updated = datetime.now()
    
    def complete_sprint(self) -> None:
        """Complete the sprint."""
        self.status = SprintStatus.COMPLETED
        if not self.end_date:
            self.end_date = datetime.now()
        self.updated = datetime.now()
    
    def calculate_velocity(self, story_points: Dict[str, int]) -> int:
        """Calculate sprint velocity based on completed stories."""
        completed_points = 0
        for story_id in self.stories:
            if story_id in story_points:
                completed_points += story_points[story_id]
        
        self.velocity = completed_points
        return completed_points
    
    def get_burndown_point(self, date: datetime, remaining_points: int) -> None:
        """Add a burndown chart data point."""
        self.burndown_data.append({
            "date": date.isoformat(),
            "remaining_points": remaining_points
        })
    
    def get_duration_days(self) -> Optional[int]:
        """Get sprint duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None


@dataclass
class ProjectData:
    """
    Represents all data for a project including epics, stories, and sprints.
    
    This is the main container for project management data.
    """
    project_name: str
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    epics: Dict[str, Epic] = field(default_factory=dict)
    stories: Dict[str, Story] = field(default_factory=dict)
    sprints: Dict[str, Sprint] = field(default_factory=dict)
    current_sprint_id: Optional[str] = None
    next_epic_id: int = 1
    next_story_id: int = 1
    next_sprint_id: int = 1
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_name": self.project_name,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "epics": {k: v.to_dict() for k, v in self.epics.items()},
            "stories": {k: v.to_dict() for k, v in self.stories.items()},
            "sprints": {k: v.to_dict() for k, v in self.sprints.items()},
            "current_sprint_id": self.current_sprint_id,
            "next_epic_id": self.next_epic_id,
            "next_story_id": self.next_story_id,
            "next_sprint_id": self.next_sprint_id,
            "settings": self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectData":
        """Create ProjectData from dictionary."""
        # Convert datetime strings
        created = datetime.fromisoformat(data["created"]) if isinstance(data["created"], str) else data["created"]
        updated = datetime.fromisoformat(data["updated"]) if isinstance(data["updated"], str) else data["updated"]
        
        # Convert nested objects
        epics = {k: Epic.from_dict(v) for k, v in data.get("epics", {}).items()}
        stories = {k: Story.from_dict(v) for k, v in data.get("stories", {}).items()}
        sprints = {k: Sprint.from_dict(v) for k, v in data.get("sprints", {}).items()}
        
        return cls(
            project_name=data["project_name"],
            created=created,
            updated=updated,
            epics=epics,
            stories=stories,
            sprints=sprints,
            current_sprint_id=data.get("current_sprint_id"),
            next_epic_id=data.get("next_epic_id", 1),
            next_story_id=data.get("next_story_id", 1),
            next_sprint_id=data.get("next_sprint_id", 1),
            settings=data.get("settings", {})
        )
    
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
        
        self.epics[epic_id] = epic
        self.updated = datetime.now()
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
        
        self.stories[story_id] = story
        
        # Add to epic if specified
        if epic_id and epic_id in self.epics:
            self.epics[epic_id].add_story(story_id)
        
        self.updated = datetime.now()
        return story
    
    def create_sprint(self, name: str, description: str, **kwargs) -> Sprint:
        """Create a new sprint."""
        sprint_id = f"sprint_{self.next_sprint_id}"
        self.next_sprint_id += 1
        
        sprint = Sprint(
            id=sprint_id,
            name=name,
            description=description,
            **kwargs
        )
        
        self.sprints[sprint_id] = sprint
        self.updated = datetime.now()
        return sprint
    
    def get_backlog_stories(self) -> List[Story]:
        """Get all stories in the backlog."""
        return [story for story in self.stories.values() 
                if story.status == StoryStatus.BACKLOG and story.sprint_id is None]
    
    def get_current_sprint(self) -> Optional[Sprint]:
        """Get the current active sprint."""
        if self.current_sprint_id and self.current_sprint_id in self.sprints:
            return self.sprints[self.current_sprint_id]
        return None
    
    def get_epic_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get progress for all epics."""
        story_statuses = {story.id: story.status for story in self.stories.values()}
        return {epic_id: epic.get_progress(story_statuses) 
                for epic_id, epic in self.epics.items()}
    
    def export_to_json(self) -> str:
        """Export all project data to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def import_from_json(cls, json_str: str) -> "ProjectData":
        """Import project data from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)