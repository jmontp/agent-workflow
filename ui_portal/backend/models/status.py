"""Status and health check models for the UI Portal Backend"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """Component type enumeration"""
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    ORCHESTRATOR = "orchestrator"
    AGENT = "agent"
    WEBSOCKET = "websocket"
    EXTERNAL = "external"


class HealthCheck(BaseModel):
    """Health check model"""
    component: str
    component_type: ComponentType
    status: ServiceStatus
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    response_time: Optional[float] = None  # in milliseconds
    last_checked: datetime
    uptime: Optional[float] = None  # in seconds


class SystemStatus(BaseModel):
    """System status model"""
    overall_status: ServiceStatus
    timestamp: datetime
    uptime: float  # in seconds
    version: str
    environment: str
    components: List[HealthCheck] = []
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ServiceMetrics(BaseModel):
    """Service metrics model"""
    requests_total: int = 0
    requests_per_minute: float = 0.0
    active_connections: int = 0
    active_websockets: int = 0
    memory_usage: float = 0.0  # in MB
    cpu_usage: float = 0.0  # percentage
    disk_usage: float = 0.0  # percentage
    last_updated: datetime


class OrchestratorStatus(BaseModel):
    """Orchestrator status model"""
    status: ServiceStatus
    active_projects: int = 0
    total_projects: int = 0
    active_tasks: int = 0
    pending_approvals: int = 0
    active_tdd_cycles: int = 0
    agents_status: Dict[str, ServiceStatus] = Field(default_factory=dict)
    last_activity: Optional[datetime] = None
    configuration_valid: bool = True
    errors: List[str] = []


class AgentStatus(BaseModel):
    """Agent status model"""
    agent_type: str
    status: ServiceStatus
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_activity: Optional[datetime] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = []
    warnings: List[str] = []


class ProjectStatus(BaseModel):
    """Project status model"""
    project_id: int
    project_name: str
    status: ServiceStatus
    current_state: str
    active_tasks: int = 0
    pending_approvals: int = 0
    active_tdd_cycles: int = 0
    last_activity: Optional[datetime] = None
    health_score: float = 100.0  # 0-100
    issues: List[str] = []


class WebSocketStatus(BaseModel):
    """WebSocket status model"""
    status: ServiceStatus
    active_connections: int = 0
    total_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    connection_errors: int = 0
    last_activity: Optional[datetime] = None


class DatabaseStatus(BaseModel):
    """Database status model"""
    status: ServiceStatus
    connection_pool_size: int = 0
    active_connections: int = 0
    total_queries: int = 0
    slow_queries: int = 0
    last_backup: Optional[datetime] = None
    size: Optional[float] = None  # in MB
    errors: List[str] = []


class CacheStatus(BaseModel):
    """Cache status model"""
    status: ServiceStatus
    hit_rate: float = 0.0  # percentage
    miss_rate: float = 0.0  # percentage
    memory_usage: float = 0.0  # in MB
    keys_count: int = 0
    expired_keys: int = 0
    errors: List[str] = []


class SystemLoad(BaseModel):
    """System load model"""
    cpu_usage: float  # percentage
    memory_usage: float  # percentage
    disk_usage: float  # percentage
    network_io: Dict[str, float] = Field(default_factory=dict)  # bytes
    active_processes: int = 0
    load_average: List[float] = []  # 1, 5, 15 minute averages
    timestamp: datetime


class AlertLevel(str, Enum):
    """Alert level enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert(BaseModel):
    """Alert model"""
    id: str
    level: AlertLevel
    component: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class StatusSummary(BaseModel):
    """Status summary model"""
    overall_health: ServiceStatus
    critical_alerts: int = 0
    warning_alerts: int = 0
    active_projects: int = 0
    active_tasks: int = 0
    system_load: SystemLoad
    last_updated: datetime