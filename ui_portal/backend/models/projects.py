"""Project models for the UI Portal Backend"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class OrchestrationMode(str, Enum):
    """Orchestration mode enumeration"""
    BLOCKING = "blocking"
    PARTIAL = "partial"
    AUTONOMOUS = "autonomous"


class WorkflowState(str, Enum):
    """Workflow state enumeration"""
    IDLE = "IDLE"
    BACKLOG_READY = "BACKLOG_READY"
    SPRINT_PLANNED = "SPRINT_PLANNED"
    SPRINT_ACTIVE = "SPRINT_ACTIVE"
    SPRINT_PAUSED = "SPRINT_PAUSED"
    SPRINT_REVIEW = "SPRINT_REVIEW"
    BLOCKED = "BLOCKED"


class ProjectBase(BaseModel):
    """Base project model"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    path: str = Field(..., description="File system path to the project")
    orchestration_mode: OrchestrationMode = OrchestrationMode.BLOCKING
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectCreate(ProjectBase):
    """Project creation model"""
    pass


class ProjectUpdate(BaseModel):
    """Project update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    orchestration_mode: Optional[OrchestrationMode] = None
    status: Optional[ProjectStatus] = None


class Project(ProjectBase):
    """Project model with full details"""
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    current_state: WorkflowState = WorkflowState.IDLE
    active_tasks: int = 0
    pending_approvals: int = 0
    active_tdd_cycles: int = 0
    
    class Config:
        orm_mode = True


class ProjectResponse(BaseModel):
    """Project response model"""
    id: int
    name: str
    description: Optional[str] = None
    path: str
    orchestration_mode: OrchestrationMode
    status: ProjectStatus
    current_state: WorkflowState
    active_tasks: int
    pending_approvals: int
    active_tdd_cycles: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    
    class Config:
        orm_mode = True


class ProjectMetrics(BaseModel):
    """Project metrics model"""
    total_epics: int = 0
    total_stories: int = 0
    completed_stories: int = 0
    total_sprints: int = 0
    completed_sprints: int = 0
    total_commits: int = 0
    test_coverage: float = 0.0
    last_activity: Optional[datetime] = None


class ProjectDetails(ProjectResponse):
    """Detailed project model with metrics"""
    metrics: ProjectMetrics
    configuration: Dict[str, Any] = {}
    recent_activity: List[Dict[str, Any]] = []


class Epic(BaseModel):
    """Epic model"""
    id: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    project_id: int


class Story(BaseModel):
    """Story model"""
    id: str
    title: str
    description: str
    epic_id: Optional[str] = None
    priority: int = 3
    status: str
    test_status: Optional[str] = None
    tdd_cycle_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    project_id: int


class Sprint(BaseModel):
    """Sprint model"""
    id: str
    goal: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    project_id: int


class ProjectBacklog(BaseModel):
    """Project backlog model"""
    project_id: int
    epics: List[Epic] = []
    stories: List[Story] = []
    sprints: List[Sprint] = []


class ProjectStateMachine(BaseModel):
    """State machine information for a project"""
    current_state: WorkflowState
    allowed_commands: List[str]
    transition_matrix: Dict[str, Dict[str, str]]
    active_tdd_cycles: Dict[str, str] = {}
    can_transition_to_review: bool = True
    mermaid_diagram: str