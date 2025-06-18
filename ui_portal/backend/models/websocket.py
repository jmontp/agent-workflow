"""WebSocket models for the UI Portal Backend"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class WebSocketEventType(str, Enum):
    """WebSocket event type enumeration"""
    # Connection events
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # Command events
    COMMAND_STARTED = "command_started"
    COMMAND_PROGRESS = "command_progress"
    COMMAND_COMPLETED = "command_completed"
    COMMAND_FAILED = "command_failed"
    
    # Project events
    PROJECT_UPDATED = "project_updated"
    PROJECT_STATE_CHANGED = "project_state_changed"
    
    # Workflow events
    WORKFLOW_TRANSITION = "workflow_transition"
    AGENT_ACTIVITY = "agent_activity"
    TDD_CYCLE_EVENT = "tdd_cycle_event"
    
    # Approval events
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    
    # System events
    SYSTEM_STATUS_CHANGED = "system_status_changed"
    ALERT_CREATED = "alert_created"
    ALERT_RESOLVED = "alert_resolved"
    
    # Real-time data
    METRICS_UPDATE = "metrics_update"
    LOGS_UPDATE = "logs_update"
    
    # User events
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    
    # Error events
    ERROR = "error"
    WARNING = "warning"


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    event_type: WebSocketEventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    correlation_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class WebSocketResponse(BaseModel):
    """WebSocket response model"""
    success: bool
    message: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


class WebSocketSubscription(BaseModel):
    """WebSocket subscription model"""
    event_types: List[WebSocketEventType]
    project_ids: Optional[List[int]] = None
    user_id: Optional[int] = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class CommandProgressEvent(BaseModel):
    """Command progress event model"""
    command_id: str
    progress: float = Field(..., ge=0.0, le=100.0)
    message: Optional[str] = None
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    completed_steps: Optional[int] = None
    estimated_completion: Optional[datetime] = None


class WorkflowTransitionEvent(BaseModel):
    """Workflow transition event model"""
    project_id: int
    project_name: str
    from_state: str
    to_state: str
    command: str
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[int] = None


class AgentActivityEvent(BaseModel):
    """Agent activity event model"""
    agent_type: str
    story_id: str
    action: str
    status: str
    project_id: int
    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)


class TDDCycleEvent(BaseModel):
    """TDD cycle event model"""
    cycle_id: str
    story_id: str
    project_id: int
    event_type: str  # started, state_changed, completed, failed
    current_state: Optional[str] = None
    previous_state: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)


class ApprovalRequestEvent(BaseModel):
    """Approval request event model"""
    request_id: str
    project_id: int
    task_id: str
    reason: str
    requested_by: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    timeout: Optional[datetime] = None


class SystemStatusEvent(BaseModel):
    """System status event model"""
    component: str
    status: str
    previous_status: Optional[str] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)


class MetricsUpdateEvent(BaseModel):
    """Metrics update event model"""
    metric_type: str
    value: Union[int, float, str]
    timestamp: datetime = Field(default_factory=datetime.now)
    project_id: Optional[int] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class LogsUpdateEvent(BaseModel):
    """Logs update event model"""
    level: str
    message: str
    component: str
    timestamp: datetime = Field(default_factory=datetime.now)
    project_id: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class UserPresenceEvent(BaseModel):
    """User presence event model"""
    user_id: int
    username: str
    action: str  # joined, left, active, idle
    project_id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class AlertEvent(BaseModel):
    """Alert event model"""
    alert_id: str
    level: str
    component: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    project_id: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class WebSocketConnection(BaseModel):
    """WebSocket connection model"""
    connection_id: str
    user_id: Optional[int] = None
    project_ids: List[int] = Field(default_factory=list)
    subscriptions: List[WebSocketSubscription] = Field(default_factory=list)
    connected_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class WebSocketStats(BaseModel):
    """WebSocket statistics model"""
    total_connections: int = 0
    active_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    connection_errors: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)