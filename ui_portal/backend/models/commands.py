"""Command models for the UI Portal Backend"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class CommandStatus(str, Enum):
    """Command execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandType(str, Enum):
    """Command type enumeration"""
    EPIC = "epic"
    BACKLOG = "backlog"
    SPRINT = "sprint"
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    SUGGEST_FIX = "suggest_fix"
    SKIP_TASK = "skip_task"
    FEEDBACK = "feedback"
    STATE = "state"
    TDD = "tdd"
    CUSTOM = "custom"


class CommandRequest(BaseModel):
    """Command execution request"""
    command: str = Field(..., description="The command to execute")
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    timeout: Optional[int] = Field(default=300, description="Timeout in seconds")


class CommandResponse(BaseModel):
    """Command execution response"""
    id: str = Field(..., description="Unique command execution ID")
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    hint: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    status: CommandStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None  # in seconds
    project_id: Optional[int] = None
    user_id: Optional[int] = None


class Command(BaseModel):
    """Command model for database storage"""
    id: str
    command: str
    command_type: CommandType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: CommandStatus
    success: Optional[bool] = None
    message: Optional[str] = None
    error: Optional[str] = None
    hint: Optional[str] = None
    response_data: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    project_id: Optional[int] = None
    user_id: Optional[int] = None
    dry_run: bool = False
    timeout: int = 300
    
    class Config:
        orm_mode = True


class CommandHistory(BaseModel):
    """Command history model"""
    commands: List[Command]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class EpicCommand(BaseModel):
    """Epic command parameters"""
    title: Optional[str] = None
    description: str = Field(..., min_length=1)


class BacklogCommand(BaseModel):
    """Backlog command parameters"""
    action: str = Field(..., description="view, add_story, prioritize, remove")
    story_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    epic_id: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    backlog_type: Optional[str] = "product"  # product or sprint


class SprintCommand(BaseModel):
    """Sprint command parameters"""
    action: str = Field(..., description="plan, start, status, pause, resume")
    story_ids: Optional[List[str]] = None
    goal: Optional[str] = None


class ApprovalCommand(BaseModel):
    """Approval command parameters"""
    item_ids: Optional[List[str]] = None


class TDDCommand(BaseModel):
    """TDD command parameters"""
    action: str = Field(..., description="start, status, next, abort, logs, overview, design, test, code, refactor, commit, run_tests")
    story_id: Optional[str] = None
    task_description: Optional[str] = None


class RequestChangesCommand(BaseModel):
    """Request changes command parameters"""
    description: str = Field(..., min_length=1)
    pr_id: Optional[str] = None


class SuggestFixCommand(BaseModel):
    """Suggest fix command parameters"""
    description: str = Field(..., min_length=1)
    task_id: Optional[str] = None


class FeedbackCommand(BaseModel):
    """Feedback command parameters"""
    description: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)
    suggestions: Optional[List[str]] = None


class CommandValidation(BaseModel):
    """Command validation result"""
    valid: bool
    error_message: Optional[str] = None
    hint: Optional[str] = None
    allowed_commands: List[str] = []
    current_state: Optional[str] = None


class BatchCommandRequest(BaseModel):
    """Batch command execution request"""
    commands: List[CommandRequest]
    stop_on_error: bool = True
    max_concurrent: int = Field(default=3, ge=1, le=10)


class BatchCommandResponse(BaseModel):
    """Batch command execution response"""
    batch_id: str
    total_commands: int
    completed: int
    failed: int
    results: List[CommandResponse]
    overall_success: bool
    started_at: datetime
    completed_at: Optional[datetime] = None