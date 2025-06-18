"""
Context Configuration - Production-Ready Configuration Management

Comprehensive configuration system for context management with environment-specific
settings, validation, hot reloading, and configuration templates.
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import time

try:
    from .context_cache import CacheStrategy, CacheWarmingStrategy
    from .context_monitoring import MonitoringInterval, AlertSeverity
    from .context_learning import LearningStrategy
except ImportError:
    from context_cache import CacheStrategy, CacheWarmingStrategy
    from context_monitoring import MonitoringInterval, AlertSeverity
    from context_learning import LearningStrategy

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigFormat(Enum):
    """Configuration file formats"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"


@dataclass
class CacheConfig:
    """Cache configuration settings"""
    
    enabled: bool = True
    strategy: CacheStrategy = CacheStrategy.PREDICTIVE
    warming_strategy: CacheWarmingStrategy = CacheWarmingStrategy.PATTERN_BASED
    max_entries: int = 1000
    max_memory_mb: int = 500
    ttl_seconds: int = 1800
    enable_predictions: bool = True
    prediction_confidence_threshold: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "enabled": self.enabled,
            "strategy": self.strategy.value,
            "warming_strategy": self.warming_strategy.value,
            "max_entries": self.max_entries,
            "max_memory_mb": self.max_memory_mb,
            "ttl_seconds": self.ttl_seconds,
            "enable_predictions": self.enable_predictions,
            "prediction_confidence_threshold": self.prediction_confidence_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheConfig':
        """Create from dictionary"""
        return cls(
            enabled=data.get("enabled", True),
            strategy=CacheStrategy(data.get("strategy", "predictive")),
            warming_strategy=CacheWarmingStrategy(data.get("warming_strategy", "pattern_based")),
            max_entries=data.get("max_entries", 1000),
            max_memory_mb=data.get("max_memory_mb", 500),
            ttl_seconds=data.get("ttl_seconds", 1800),
            enable_predictions=data.get("enable_predictions", True),
            prediction_confidence_threshold=data.get("prediction_confidence_threshold", 0.7)
        )


@dataclass
class MonitoringConfig:
    """Monitoring configuration settings"""
    
    enabled: bool = True
    collection_interval: int = 5
    retention_hours: int = 24
    enable_system_metrics: bool = True
    enable_alerts: bool = True
    metrics_buffer_size: int = 10000
    alert_cooldown_seconds: int = 300
    performance_targets: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringConfig':
        """Create from dictionary"""
        return cls(
            enabled=data.get("enabled", True),
            collection_interval=data.get("collection_interval", 5),
            retention_hours=data.get("retention_hours", 24),
            enable_system_metrics=data.get("enable_system_metrics", True),
            enable_alerts=data.get("enable_alerts", True),
            metrics_buffer_size=data.get("metrics_buffer_size", 10000),
            alert_cooldown_seconds=data.get("alert_cooldown_seconds", 300),
            performance_targets=data.get("performance_targets", {})
        )


@dataclass
class LearningConfig:
    """Learning system configuration settings"""
    
    enabled: bool = True
    strategy: LearningStrategy = LearningStrategy.ENSEMBLE
    learning_rate: float = 0.01
    feature_decay_days: int = 30
    pattern_confidence_threshold: float = 0.7
    enable_persistence: bool = True
    auto_discovery: bool = True
    optimization_interval_hours: int = 24
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "enabled": self.enabled,
            "strategy": self.strategy.value,
            "learning_rate": self.learning_rate,
            "feature_decay_days": self.feature_decay_days,
            "pattern_confidence_threshold": self.pattern_confidence_threshold,
            "enable_persistence": self.enable_persistence,
            "auto_discovery": self.auto_discovery,
            "optimization_interval_hours": self.optimization_interval_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningConfig':
        """Create from dictionary"""
        return cls(
            enabled=data.get("enabled", True),
            strategy=LearningStrategy(data.get("strategy", "ensemble")),
            learning_rate=data.get("learning_rate", 0.01),
            feature_decay_days=data.get("feature_decay_days", 30),
            pattern_confidence_threshold=data.get("pattern_confidence_threshold", 0.7),
            enable_persistence=data.get("enable_persistence", True),
            auto_discovery=data.get("auto_discovery", True),
            optimization_interval_hours=data.get("optimization_interval_hours", 24)
        )


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    
    enable_sandbox: bool = True
    max_file_size_mb: int = 100
    allowed_file_extensions: List[str] = field(default_factory=lambda: [
        ".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml", ".yml"
    ])
    blocked_paths: List[str] = field(default_factory=lambda: [
        ".git", "__pycache__", "node_modules", ".env"
    ])
    enable_content_filtering: bool = True
    max_context_size_mb: int = 50
    rate_limit_requests_per_minute: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityConfig':
        """Create from dictionary"""
        return cls(
            enable_sandbox=data.get("enable_sandbox", True),
            max_file_size_mb=data.get("max_file_size_mb", 100),
            allowed_file_extensions=data.get("allowed_file_extensions", [
                ".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml", ".yml"
            ]),
            blocked_paths=data.get("blocked_paths", [
                ".git", "__pycache__", "node_modules", ".env"
            ]),
            enable_content_filtering=data.get("enable_content_filtering", True),
            max_context_size_mb=data.get("max_context_size_mb", 50),
            rate_limit_requests_per_minute=data.get("rate_limit_requests_per_minute", 100)
        )


@dataclass
class PerformanceConfig:
    """Performance configuration settings"""
    
    max_tokens: int = 200000
    max_preparation_time: int = 30
    max_concurrent_requests: int = 10
    enable_compression: bool = True
    compression_threshold: float = 0.8
    enable_parallel_processing: bool = True
    worker_pool_size: int = 4
    memory_limit_mb: int = 2048
    enable_profiling: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Create from dictionary"""
        return cls(
            max_tokens=data.get("max_tokens", 200000),
            max_preparation_time=data.get("max_preparation_time", 30),
            max_concurrent_requests=data.get("max_concurrent_requests", 10),
            enable_compression=data.get("enable_compression", True),
            compression_threshold=data.get("compression_threshold", 0.8),
            enable_parallel_processing=data.get("enable_parallel_processing", True),
            worker_pool_size=data.get("worker_pool_size", 4),
            memory_limit_mb=data.get("memory_limit_mb", 2048),
            enable_profiling=data.get("enable_profiling", False)
        )


@dataclass
class ContextConfig:
    """Complete context management configuration"""
    
    # Environment and basic settings
    environment: Environment = Environment.DEVELOPMENT
    project_path: Optional[str] = None
    log_level: str = "INFO"
    enable_debug: bool = False
    
    # Feature toggles
    enable_intelligence: bool = True
    enable_cross_story: bool = True
    
    # Component configurations
    cache: CacheConfig = field(default_factory=CacheConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "environment": self.environment.value,
            "project_path": self.project_path,
            "log_level": self.log_level,
            "enable_debug": self.enable_debug,
            "enable_intelligence": self.enable_intelligence,
            "enable_cross_story": self.enable_cross_story,
            "cache": self.cache.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "learning": self.learning.to_dict(),
            "security": self.security.to_dict(),
            "performance": self.performance.to_dict(),
            "custom_settings": self.custom_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextConfig':
        """Create from dictionary"""
        return cls(
            environment=Environment(data.get("environment", "development")),
            project_path=data.get("project_path"),
            log_level=data.get("log_level", "INFO"),
            enable_debug=data.get("enable_debug", False),
            enable_intelligence=data.get("enable_intelligence", True),
            enable_cross_story=data.get("enable_cross_story", True),
            cache=CacheConfig.from_dict(data.get("cache", {})),
            monitoring=MonitoringConfig.from_dict(data.get("monitoring", {})),
            learning=LearningConfig.from_dict(data.get("learning", {})),
            security=SecurityConfig.from_dict(data.get("security", {})),
            performance=PerformanceConfig.from_dict(data.get("performance", {})),
            custom_settings=data.get("custom_settings", {})
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        # Validate performance settings
        if self.performance.max_tokens <= 0:
            errors.append("max_tokens must be positive")
        
        if self.performance.max_preparation_time <= 0:
            errors.append("max_preparation_time must be positive")
        
        # Validate cache settings
        if self.cache.max_entries <= 0:
            errors.append("cache max_entries must be positive")
        
        if self.cache.max_memory_mb <= 0:
            errors.append("cache max_memory_mb must be positive")
        
        # Validate monitoring settings
        if self.monitoring.collection_interval <= 0:
            errors.append("monitoring collection_interval must be positive")
        
        # Validate learning settings
        if not (0 < self.learning.learning_rate <= 1):
            errors.append("learning_rate must be between 0 and 1")
        
        # Validate security settings
        if self.security.max_file_size_mb <= 0:
            errors.append("security max_file_size_mb must be positive")
        
        # Environment-specific validations
        if self.environment == Environment.PRODUCTION:
            if self.enable_debug:
                errors.append("Debug mode should not be enabled in production")
            
            if self.performance.enable_profiling:
                errors.append("Profiling should not be enabled in production")
        
        return errors


class ConfigurationManager:
    """
    Production-ready configuration management system.
    
    Features:
    - Environment-specific configurations
    - Configuration validation
    - Hot reloading
    - Configuration templates
    - Environment variable overrides
    - Configuration merging and inheritance
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        environment: Optional[Environment] = None,
        enable_hot_reload: bool = True,
        enable_env_overrides: bool = True
    ):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
            environment: Environment to load configuration for
            enable_hot_reload: Whether to enable hot reloading
            enable_env_overrides: Whether to enable environment variable overrides
        """
        self.config_path = Path(config_path) if config_path else None
        self.environment = environment or self._detect_environment()
        self.enable_hot_reload = enable_hot_reload
        self.enable_env_overrides = enable_env_overrides
        
        # Configuration state
        self._config: Optional[ContextConfig] = None
        self._last_modified: Optional[float] = None
        self._reload_callbacks: List[Callable[[ContextConfig], None]] = []
        
        # Hot reload thread
        self._reload_thread: Optional[threading.Thread] = None
        self._reload_stop_event = threading.Event()
        
        logger.info(f"ConfigurationManager initialized for environment: {self.environment.value}")
    
    def load_config(self, config_path: Optional[str] = None) -> ContextConfig:
        """
        Load configuration from file.
        
        Args:
            config_path: Optional path to config file
            
        Returns:
            Loaded configuration
        """
        if config_path:
            self.config_path = Path(config_path)
        
        try:
            # Load base configuration
            if self.config_path and self.config_path.exists():
                config_data = self._load_config_file(self.config_path)
                self._config = ContextConfig.from_dict(config_data)
            else:
                # Use default configuration
                self._config = self._get_default_config()
            
            # Apply environment-specific overrides
            self._apply_environment_overrides()
            
            # Apply environment variable overrides
            if self.enable_env_overrides:
                self._apply_env_overrides()
            
            # Validate configuration
            errors = self._config.validate()
            if errors:
                logger.warning(f"Configuration validation errors: {errors}")
            
            # Update last modified time
            if self.config_path and self.config_path.exists():
                self._last_modified = self.config_path.stat().st_mtime
            
            # Start hot reload if enabled
            if self.enable_hot_reload and not self._reload_thread:
                self._start_hot_reload()
            
            logger.info(f"Configuration loaded for environment: {self.environment.value}")
            return self._config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Return default configuration on error
            self._config = self._get_default_config()
            return self._config
    
    def get_config(self) -> ContextConfig:
        """Get current configuration"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def save_config(self, config: ContextConfig, config_path: Optional[str] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            config_path: Optional path to save to
            
        Returns:
            True if saved successfully
        """
        try:
            save_path = Path(config_path) if config_path else self.config_path
            if not save_path:
                raise ValueError("No config path specified")
            
            # Validate configuration before saving
            errors = config.validate()
            if errors:
                logger.error(f"Cannot save invalid configuration: {errors}")
                return False
            
            # Save configuration
            config_data = config.to_dict()
            
            if save_path.suffix.lower() == '.json':
                with open(save_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
            elif save_path.suffix.lower() in ['.yaml', '.yml']:
                with open(save_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                # Default to JSON
                with open(save_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def create_template(self, environment: Environment, output_path: str) -> bool:
        """
        Create configuration template for environment.
        
        Args:
            environment: Environment to create template for
            output_path: Path to save template
            
        Returns:
            True if template created successfully
        """
        try:
            # Get environment-specific defaults
            template_config = self._get_environment_defaults(environment)
            
            # Add comments and documentation
            config_dict = template_config.to_dict()
            
            # Save template
            output_file = Path(output_path)
            
            if output_file.suffix.lower() == '.json':
                with open(output_file, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            elif output_file.suffix.lower() in ['.yaml', '.yml']:
                with open(output_file, 'w') as f:
                    # Add header comment
                    f.write(f"# Context Management Configuration Template\n")
                    f.write(f"# Environment: {environment.value}\n")
                    f.write(f"# Generated: {datetime.utcnow().isoformat()}\n\n")
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration template created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return False
    
    def add_reload_callback(self, callback: Callable[[ContextConfig], None]) -> None:
        """Add callback for configuration reloads"""
        self._reload_callbacks.append(callback)
    
    def remove_reload_callback(self, callback: Callable[[ContextConfig], None]) -> None:
        """Remove reload callback"""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)
    
    def stop_hot_reload(self) -> None:
        """Stop hot reload monitoring"""
        if self._reload_thread:
            self._reload_stop_event.set()
            self._reload_thread.join(timeout=5)
            self._reload_thread = None
    
    def get_environment_config_path(self, base_path: str) -> str:
        """Get environment-specific config file path"""
        base_file = Path(base_path)
        stem = base_file.stem
        suffix = base_file.suffix
        parent = base_file.parent
        
        env_filename = f"{stem}.{self.environment.value}{suffix}"
        return str(parent / env_filename)
    
    def merge_configs(self, base_config: ContextConfig, override_config: Dict[str, Any]) -> ContextConfig:
        """
        Merge configuration with overrides.
        
        Args:
            base_config: Base configuration
            override_config: Override values
            
        Returns:
            Merged configuration
        """
        base_dict = base_config.to_dict()
        merged_dict = self._deep_merge(base_dict, override_config)
        return ContextConfig.from_dict(merged_dict)
    
    # Private methods
    
    def _detect_environment(self) -> Environment:
        """Detect environment from environment variables"""
        env_name = os.getenv('CONTEXT_ENV', os.getenv('ENV', 'development')).lower()
        
        env_mapping = {
            'dev': Environment.DEVELOPMENT,
            'development': Environment.DEVELOPMENT,
            'test': Environment.TESTING,
            'testing': Environment.TESTING,
            'stage': Environment.STAGING,
            'staging': Environment.STAGING,
            'prod': Environment.PRODUCTION,
            'production': Environment.PRODUCTION
        }
        
        return env_mapping.get(env_name, Environment.DEVELOPMENT)
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() == '.json':
                return json.load(f)
            elif config_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            else:
                raise ValueError(f"Unsupported configuration format: {config_path.suffix}")
    
    def _get_default_config(self) -> ContextConfig:
        """Get default configuration"""
        return self._get_environment_defaults(self.environment)
    
    def _get_environment_defaults(self, environment: Environment) -> ContextConfig:
        """Get default configuration for environment"""
        if environment == Environment.PRODUCTION:
            return ContextConfig(
                environment=environment,
                log_level="WARNING",
                enable_debug=False,
                cache=CacheConfig(
                    max_entries=5000,
                    max_memory_mb=2048,
                    ttl_seconds=3600
                ),
                monitoring=MonitoringConfig(
                    retention_hours=72,
                    enable_alerts=True
                ),
                learning=LearningConfig(
                    enable_persistence=True,
                    optimization_interval_hours=12
                ),
                performance=PerformanceConfig(
                    max_concurrent_requests=50,
                    enable_profiling=False,
                    memory_limit_mb=4096
                )
            )
        elif environment == Environment.STAGING:
            return ContextConfig(
                environment=environment,
                log_level="INFO",
                enable_debug=False,
                cache=CacheConfig(
                    max_entries=2000,
                    max_memory_mb=1024
                ),
                monitoring=MonitoringConfig(
                    retention_hours=48
                ),
                performance=PerformanceConfig(
                    max_concurrent_requests=20,
                    memory_limit_mb=2048
                )
            )
        elif environment == Environment.TESTING:
            return ContextConfig(
                environment=environment,
                log_level="DEBUG",
                enable_debug=True,
                cache=CacheConfig(
                    max_entries=100,
                    max_memory_mb=256,
                    ttl_seconds=300
                ),
                monitoring=MonitoringConfig(
                    retention_hours=4,
                    enable_alerts=False
                ),
                learning=LearningConfig(
                    enable_persistence=False
                ),
                performance=PerformanceConfig(
                    max_concurrent_requests=5,
                    memory_limit_mb=512
                )
            )
        else:  # DEVELOPMENT
            return ContextConfig(
                environment=environment,
                log_level="DEBUG",
                enable_debug=True,
                cache=CacheConfig(
                    max_entries=500,
                    max_memory_mb=512
                ),
                monitoring=MonitoringConfig(
                    retention_hours=12
                ),
                performance=PerformanceConfig(
                    enable_profiling=True,
                    memory_limit_mb=1024
                )
            )
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides"""
        if not self.config_path:
            return
        
        # Look for environment-specific config file
        env_config_path = Path(self.get_environment_config_path(str(self.config_path)))
        
        if env_config_path.exists():
            try:
                env_config_data = self._load_config_file(env_config_path)
                base_dict = self._config.to_dict()
                merged_dict = self._deep_merge(base_dict, env_config_data)
                self._config = ContextConfig.from_dict(merged_dict)
                
                logger.info(f"Applied environment overrides from {env_config_path}")
                
            except Exception as e:
                logger.warning(f"Error loading environment config: {str(e)}")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        # Define environment variable mappings
        env_mappings = {
            'CONTEXT_LOG_LEVEL': 'log_level',
            'CONTEXT_DEBUG': 'enable_debug',
            'CONTEXT_MAX_TOKENS': 'performance.max_tokens',
            'CONTEXT_CACHE_ENABLED': 'cache.enabled',
            'CONTEXT_CACHE_MAX_ENTRIES': 'cache.max_entries',
            'CONTEXT_CACHE_MEMORY_MB': 'cache.max_memory_mb',
            'CONTEXT_MONITORING_ENABLED': 'monitoring.enabled',
            'CONTEXT_LEARNING_ENABLED': 'learning.enabled',
            'CONTEXT_LEARNING_RATE': 'learning.learning_rate'
        }
        
        config_dict = self._config.to_dict()
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Parse environment variable value
                parsed_value = self._parse_env_value(env_value)
                
                # Set nested configuration value
                self._set_nested_value(config_dict, config_path, parsed_value)
        
        # Update configuration
        self._config = ContextConfig.from_dict(config_dict)
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer values
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float values
        try:
            return float(value)
        except ValueError:
            pass
        
        # String values
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _start_hot_reload(self) -> None:
        """Start hot reload monitoring thread"""
        if not self.config_path or not self.config_path.exists():
            return
        
        self._reload_thread = threading.Thread(
            target=self._hot_reload_worker,
            daemon=True
        )
        self._reload_thread.start()
        
        logger.info("Hot reload monitoring started")
    
    def _hot_reload_worker(self) -> None:
        """Hot reload worker thread"""
        while not self._reload_stop_event.is_set():
            try:
                if self.config_path and self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime
                    
                    if self._last_modified and current_mtime > self._last_modified:
                        logger.info("Configuration file changed, reloading...")
                        
                        # Reload configuration
                        old_config = self._config
                        self.load_config()
                        
                        # Notify callbacks
                        for callback in self._reload_callbacks:
                            try:
                                callback(self._config)
                            except Exception as e:
                                logger.error(f"Error in reload callback: {str(e)}")
                
                # Check every 5 seconds
                self._reload_stop_event.wait(5)
                
            except Exception as e:
                logger.error(f"Error in hot reload worker: {str(e)}")
                self._reload_stop_event.wait(5)


def create_config_templates() -> Dict[str, str]:
    """Create configuration templates for all environments"""
    manager = ConfigurationManager()
    templates = {}
    
    for env in Environment:
        config = manager._get_environment_defaults(env)
        templates[env.value] = json.dumps(config.to_dict(), indent=2)
    
    return templates


def load_config_from_env() -> ContextConfig:
    """Load configuration from environment variables and files"""
    manager = ConfigurationManager(enable_env_overrides=True)
    
    # Look for config file in standard locations
    config_paths = [
        "context_config.yaml",
        "context_config.json",
        ".context/config.yaml",
        ".context/config.json",
        os.path.expanduser("~/.context/config.yaml"),
        "/etc/context/config.yaml"
    ]
    
    for path in config_paths:
        if Path(path).exists():
            return manager.load_config(path)
    
    # No config file found, use defaults with env overrides
    return manager.load_config()


def validate_config_file(config_path: str) -> List[str]:
    """Validate a configuration file"""
    try:
        manager = ConfigurationManager()
        config_data = manager._load_config_file(Path(config_path))
        config = ContextConfig.from_dict(config_data)
        return config.validate()
    except Exception as e:
        return [f"Error loading config file: {str(e)}"]