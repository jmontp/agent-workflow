"""
Context Configuration Management

Configuration system for context management modes and settings.
"""

import yaml
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ContextMode(Enum):
    """Context management modes"""
    FANCY = "fancy"
    SIMPLE = "simple"
    AUTO = "auto"


@dataclass
class ContextConfig:
    """Configuration for context management system"""
    
    # Core settings
    default_mode: ContextMode = ContextMode.AUTO
    max_tokens: int = 200000
    cache_ttl_seconds: int = 300
    
    # Fancy mode settings
    enable_intelligence: bool = True
    enable_advanced_caching: bool = True
    enable_monitoring: bool = True
    enable_cross_story: bool = True
    enable_background_processing: bool = True
    max_preparation_time: int = 30
    
    # Simple mode settings
    simple_max_files: int = 10
    simple_max_file_size: int = 50000
    simple_enable_caching: bool = True
    simple_cache_size: int = 50
    
    # Auto-detection settings
    auto_detection_enabled: bool = True
    force_simple_in_ci: bool = True
    force_simple_with_mock: bool = True
    min_memory_for_fancy: int = 2048  # MB
    min_cpu_cores_for_fancy: int = 2
    
    # Performance thresholds
    max_fancy_preparation_time: float = 10.0  # seconds
    max_simple_preparation_time: float = 1.0  # seconds
    
    # Switching rules
    auto_switch_enabled: bool = True
    switch_threshold_failures: int = 3
    switch_cooldown_seconds: int = 60
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if isinstance(self.default_mode, str):
            self.default_mode = ContextMode(self.default_mode)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextConfig':
        """Create configuration from dictionary"""
        # Handle enum conversion
        if 'default_mode' in data and isinstance(data['default_mode'], str):
            data['default_mode'] = ContextMode(data['default_mode'])
        
        # Filter out unknown keys
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        data = asdict(self)
        # Convert enum to string
        data['default_mode'] = self.default_mode.value
        return data
    
    @classmethod
    def from_file(cls, file_path: str) -> 'ContextConfig':
        """Load configuration from YAML file"""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            logger.info(f"Loaded context configuration from {file_path}")
            return cls.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to load context configuration from {file_path}: {e}")
            raise
    
    def to_file(self, file_path: str):
        """Save configuration to YAML file"""
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
            
            logger.info(f"Saved context configuration to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save context configuration to {file_path}: {e}")
            raise
    
    def validate(self) -> Dict[str, list]:
        """
        Validate configuration settings.
        
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []
        
        # Validate token limits
        if self.max_tokens <= 0:
            errors.append("max_tokens must be positive")
        elif self.max_tokens < 1000:
            warnings.append("max_tokens is very low, may cause issues")
        elif self.max_tokens > 1000000:
            warnings.append("max_tokens is very high, may cause performance issues")
        
        # Validate cache settings
        if self.cache_ttl_seconds <= 0:
            errors.append("cache_ttl_seconds must be positive")
        
        # Validate simple mode settings
        if self.simple_max_files <= 0:
            errors.append("simple_max_files must be positive")
        elif self.simple_max_files > 100:
            warnings.append("simple_max_files is high, may impact performance")
        
        if self.simple_max_file_size <= 0:
            errors.append("simple_max_file_size must be positive")
        elif self.simple_max_file_size > 1000000:
            warnings.append("simple_max_file_size is very large")
        
        if self.simple_cache_size <= 0:
            errors.append("simple_cache_size must be positive")
        
        # Validate resource thresholds
        if self.min_memory_for_fancy <= 0:
            errors.append("min_memory_for_fancy must be positive")
        
        if self.min_cpu_cores_for_fancy <= 0:
            errors.append("min_cpu_cores_for_fancy must be positive")
        
        # Validate performance thresholds
        if self.max_fancy_preparation_time <= 0:
            errors.append("max_fancy_preparation_time must be positive")
        
        if self.max_simple_preparation_time <= 0:
            errors.append("max_simple_preparation_time must be positive")
        
        if self.max_simple_preparation_time >= self.max_fancy_preparation_time:
            warnings.append("max_simple_preparation_time should be less than max_fancy_preparation_time")
        
        # Validate switching settings
        if self.switch_threshold_failures <= 0:
            errors.append("switch_threshold_failures must be positive")
        
        if self.switch_cooldown_seconds < 0:
            errors.append("switch_cooldown_seconds must be non-negative")
        
        return {
            "errors": errors,
            "warnings": warnings
        }
    
    def get_mode_specific_config(self, mode: ContextMode) -> Dict[str, Any]:
        """Get configuration specific to a mode"""
        if mode == ContextMode.FANCY:
            return {
                "enable_intelligence": self.enable_intelligence,
                "enable_advanced_caching": self.enable_advanced_caching,
                "enable_monitoring": self.enable_monitoring,
                "enable_cross_story": self.enable_cross_story,
                "enable_background_processing": self.enable_background_processing,
                "max_preparation_time": self.max_preparation_time,
                "cache_ttl_seconds": self.cache_ttl_seconds
            }
        elif mode == ContextMode.SIMPLE:
            return {
                "max_files": self.simple_max_files,
                "max_file_size": self.simple_max_file_size,
                "enable_caching": self.simple_enable_caching,
                "cache_size": self.simple_cache_size
            }
        else:
            return {}
    
    def update_from_dict(self, updates: Dict[str, Any]) -> 'ContextConfig':
        """Update configuration with new values"""
        # Create new config with updates
        current_dict = self.to_dict()
        current_dict.update(updates)
        
        return ContextConfig.from_dict(current_dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "mode": self.default_mode.value,
            "max_tokens": self.max_tokens,
            "features": {
                "intelligence": self.enable_intelligence,
                "advanced_caching": self.enable_advanced_caching,
                "monitoring": self.enable_monitoring,
                "cross_story": self.enable_cross_story,
                "background_processing": self.enable_background_processing
            },
            "simple_mode": {
                "max_files": self.simple_max_files,
                "max_file_size": self.simple_max_file_size,
                "caching": self.simple_enable_caching
            },
            "auto_detection": {
                "enabled": self.auto_detection_enabled,
                "force_simple_in_ci": self.force_simple_in_ci,
                "force_simple_with_mock": self.force_simple_with_mock
            }
        }


def load_context_config(config_path: Optional[str] = None) -> ContextConfig:
    """
    Load context configuration from file or create default.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Context configuration instance
    """
    if config_path is None:
        config_path = str(Path.cwd() / ".orch-state" / "context_config.yaml")
    
    try:
        if Path(config_path).exists():
            return ContextConfig.from_file(config_path)
        else:
            logger.info(f"Configuration file not found at {config_path}, using defaults")
            return ContextConfig()
    except Exception as e:
        logger.warning(f"Failed to load configuration: {e}, using defaults")
        return ContextConfig()


def save_context_config(config: ContextConfig, config_path: Optional[str] = None):
    """
    Save context configuration to file.
    
    Args:
        config: Configuration to save
        config_path: Path to save configuration to
    """
    if config_path is None:
        config_path = str(Path.cwd() / ".orch-state" / "context_config.yaml")
    
    config.to_file(config_path)


def create_default_config_file(config_path: Optional[str] = None) -> str:
    """
    Create a default configuration file with documentation.
    
    Args:
        config_path: Path to create configuration file at
        
    Returns:
        Path to created configuration file
    """
    if config_path is None:
        config_path = str(Path.cwd() / ".orch-state" / "context_config.yaml")
    
    config = ContextConfig()
    
    # Create documented YAML content
    yaml_content = f"""# Context Management Configuration
# This file configures the context management system for AI Agent Workflow

# Default mode: auto, fancy, or simple
# - auto: Automatically choose based on system state
# - fancy: Full-featured context processing (recommended for production)
# - simple: Fast processing with minimal overhead (good for demos/testing)
default_mode: {config.default_mode.value}

# Core Settings
max_tokens: {config.max_tokens}  # Maximum tokens for context
cache_ttl_seconds: {config.cache_ttl_seconds}  # Cache time-to-live

# Fancy Mode Settings (when using full-featured context processing)
enable_intelligence: {config.enable_intelligence}  # Enable intelligent filtering/compression
enable_advanced_caching: {config.enable_advanced_caching}  # Enable predictive caching
enable_monitoring: {config.enable_monitoring}  # Enable performance monitoring
enable_cross_story: {config.enable_cross_story}  # Enable cross-story management
enable_background_processing: {config.enable_background_processing}  # Enable background tasks
max_preparation_time: {config.max_preparation_time}  # Maximum context preparation time (seconds)

# Simple Mode Settings (when using fast processing)
simple_max_files: {config.simple_max_files}  # Maximum files to process
simple_max_file_size: {config.simple_max_file_size}  # Maximum characters per file
simple_enable_caching: {config.simple_enable_caching}  # Enable basic caching
simple_cache_size: {config.simple_cache_size}  # Number of contexts to cache

# Auto-Detection Settings
auto_detection_enabled: {config.auto_detection_enabled}  # Enable automatic mode detection
force_simple_in_ci: {config.force_simple_in_ci}  # Force simple mode in CI environments
force_simple_with_mock: {config.force_simple_with_mock}  # Force simple mode with mock interfaces
min_memory_for_fancy: {config.min_memory_for_fancy}  # Minimum memory (MB) for fancy mode
min_cpu_cores_for_fancy: {config.min_cpu_cores_for_fancy}  # Minimum CPU cores for fancy mode

# Performance Thresholds
max_fancy_preparation_time: {config.max_fancy_preparation_time}  # Max fancy mode prep time (seconds)
max_simple_preparation_time: {config.max_simple_preparation_time}  # Max simple mode prep time (seconds)

# Auto-Switching Rules
auto_switch_enabled: {config.auto_switch_enabled}  # Enable automatic mode switching
switch_threshold_failures: {config.switch_threshold_failures}  # Failures before switching
switch_cooldown_seconds: {config.switch_cooldown_seconds}  # Cooldown between switches
"""
    
    # Ensure directory exists
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write configuration file
    with open(config_path, 'w') as f:
        f.write(yaml_content)
    
    logger.info(f"Created default context configuration at {config_path}")
    return config_path