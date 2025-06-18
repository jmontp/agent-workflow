"""Configuration models for the UI Portal Backend"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ConfigurationScope(str, Enum):
    """Configuration scope enumeration"""
    GLOBAL = "global"
    PROJECT = "project"
    USER = "user"


class ConfigurationType(str, Enum):
    """Configuration type enumeration"""
    ORCHESTRATOR = "orchestrator"
    AGENT = "agent"
    WORKFLOW = "workflow"
    SECURITY = "security"
    INTEGRATION = "integration"
    UI = "ui"


class ConfigurationBase(BaseModel):
    """Base configuration model"""
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    scope: ConfigurationScope = ConfigurationScope.GLOBAL
    config_type: ConfigurationType = ConfigurationType.ORCHESTRATOR
    description: Optional[str] = None
    is_sensitive: bool = False
    is_readonly: bool = False


class ConfigurationCreate(ConfigurationBase):
    """Configuration creation model"""
    pass


class ConfigurationUpdate(BaseModel):
    """Configuration update model"""
    value: Optional[Any] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None


class Configuration(ConfigurationBase):
    """Configuration model with metadata"""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    project_id: Optional[int] = None
    
    class Config:
        orm_mode = True


class ConfigurationResponse(BaseModel):
    """Configuration response model"""
    id: int
    key: str
    value: Any
    scope: ConfigurationScope
    config_type: ConfigurationType
    description: Optional[str] = None
    is_sensitive: bool
    is_readonly: bool
    created_at: datetime
    updated_at: datetime
    project_id: Optional[int] = None
    
    class Config:
        orm_mode = True


class OrchestratorConfig(BaseModel):
    """Orchestrator configuration model"""
    projects: List[Dict[str, Any]] = []
    global_settings: Dict[str, Any] = {}
    agent_settings: Dict[str, Any] = {}
    workflow_settings: Dict[str, Any] = {}


class AgentConfig(BaseModel):
    """Agent configuration model"""
    agent_type: str
    enabled: bool = True
    max_concurrent_tasks: int = 3
    timeout: int = 300
    retry_count: int = 3
    tools: List[str] = []
    restrictions: List[str] = []
    custom_settings: Dict[str, Any] = {}


class WorkflowConfig(BaseModel):
    """Workflow configuration model"""
    max_concurrent_sprints: int = 1
    max_concurrent_tdd_cycles: int = 3
    auto_approve_safe_commands: bool = False
    require_approval_for: List[str] = []
    notification_settings: Dict[str, Any] = {}


class SecurityConfig(BaseModel):
    """Security configuration model"""
    allowed_commands: List[str] = []
    blocked_commands: List[str] = []
    rate_limiting: Dict[str, Any] = {}
    audit_logging: bool = True
    security_policies: Dict[str, Any] = {}


class IntegrationConfig(BaseModel):
    """Integration configuration model"""
    discord_enabled: bool = False
    discord_settings: Dict[str, Any] = {}
    github_enabled: bool = False
    github_settings: Dict[str, Any] = {}
    webhook_settings: Dict[str, Any] = {}


class UIConfig(BaseModel):
    """UI configuration model"""
    theme: str = "dark"
    auto_refresh_interval: int = 5
    show_advanced_features: bool = False
    dashboard_widgets: List[str] = []
    custom_css: Optional[str] = None


class ConfigurationBatch(BaseModel):
    """Batch configuration update model"""
    configurations: List[ConfigurationCreate]
    scope: ConfigurationScope
    project_id: Optional[int] = None


class ConfigurationExport(BaseModel):
    """Configuration export model"""
    configurations: List[Configuration]
    exported_at: datetime
    scope: ConfigurationScope
    project_id: Optional[int] = None
    format: str = "json"


class ConfigurationImport(BaseModel):
    """Configuration import model"""
    configurations: List[ConfigurationCreate]
    scope: ConfigurationScope
    project_id: Optional[int] = None
    overwrite_existing: bool = False
    validate_only: bool = False


class ConfigurationValidation(BaseModel):
    """Configuration validation result"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []