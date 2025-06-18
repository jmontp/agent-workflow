"""
Configuration settings for the UI Portal Backend
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # App configuration
    app_name: str = "AI Agent Workflow UI Portal"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Security configuration
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # WebSocket configuration
    websocket_ping_interval: int = 10
    websocket_ping_timeout: int = 5
    max_websocket_connections: int = 100
    
    # Integration configuration
    orchestrator_config_path: str = Field(
        default="../../orch-config.yaml",
        env="ORCHESTRATOR_CONFIG_PATH"
    )
    lib_path: str = Field(
        default="../../lib",
        env="LIB_PATH"
    )
    scripts_path: str = Field(
        default="../../scripts",
        env="SCRIPTS_PATH"
    )
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Redis configuration (for session storage and pub/sub)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()