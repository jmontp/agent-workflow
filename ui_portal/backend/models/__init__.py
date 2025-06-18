"""API Models for UI Portal Backend"""

from .auth import User, UserCreate, UserResponse, Token, TokenData
from .projects import Project, ProjectCreate, ProjectUpdate, ProjectResponse, ProjectStatus
from .commands import Command, CommandRequest, CommandResponse, CommandHistory
from .config import Configuration, ConfigurationUpdate, ConfigurationResponse
from .status import SystemStatus, HealthCheck, ServiceStatus
from .websocket import WebSocketMessage, WebSocketEventType, WebSocketResponse

__all__ = [
    # Auth models
    "User", "UserCreate", "UserResponse", "Token", "TokenData",
    
    # Project models
    "Project", "ProjectCreate", "ProjectUpdate", "ProjectResponse", "ProjectStatus",
    
    # Command models
    "Command", "CommandRequest", "CommandResponse", "CommandHistory",
    
    # Config models
    "Configuration", "ConfigurationUpdate", "ConfigurationResponse",
    
    # Status models
    "SystemStatus", "HealthCheck", "ServiceStatus",
    
    # WebSocket models
    "WebSocketMessage", "WebSocketEventType", "WebSocketResponse"
]