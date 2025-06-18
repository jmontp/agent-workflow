"""
Comprehensive test suite for Context Configuration Management System.

Tests environment-specific configurations, validation, hot reloading,
configuration templates, and environment variable overrides.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import yaml
import os
import threading
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_config import (
    Environment,
    ConfigFormat,
    CacheConfig,
    MonitoringConfig,
    LearningConfig,
    SecurityConfig,
    PerformanceConfig,
    ContextConfig,
    ConfigurationManager,
    create_config_templates,
    load_config_from_env,
    validate_config_file
)
from context_cache import CacheStrategy, CacheWarmingStrategy
from context_monitoring import MonitoringInterval, AlertSeverity
from context_learning import LearningStrategy


class TestEnvironmentEnum:
    """Test Environment enumeration"""
    
    def test_environment_values(self):
        """Test environment enum values"""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.TESTING.value == "testing"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
    
    def test_environment_count(self):
        """Test that all expected environments are defined"""
        environments = list(Environment)
        assert len(environments) == 4


class TestConfigFormat:
    """Test ConfigFormat enumeration"""
    
    def test_config_format_values(self):
        """Test config format enum values"""
        assert ConfigFormat.JSON.value == "json"
        assert ConfigFormat.YAML.value == "yaml"
        assert ConfigFormat.TOML.value == "toml"
        assert ConfigFormat.ENV.value == "env"


class TestCacheConfig:
    """Test CacheConfig data class"""
    
    def test_default_values(self):
        """Test default cache configuration values"""
        config = CacheConfig()
        
        assert config.enabled is True
        assert config.strategy == CacheStrategy.PREDICTIVE
        assert config.warming_strategy == CacheWarmingStrategy.PATTERN_BASED
        assert config.max_entries == 1000
        assert config.max_memory_mb == 500
        assert config.ttl_seconds == 1800
        assert config.enable_predictions is True
        assert config.prediction_confidence_threshold == 0.7
    
    def test_custom_values(self):
        """Test cache configuration with custom values"""
        config = CacheConfig(
            enabled=False,
            strategy=CacheStrategy.LRU,
            warming_strategy=CacheWarmingStrategy.LAZY,
            max_entries=500,
            max_memory_mb=1000,
            ttl_seconds=3600,
            enable_predictions=False,
            prediction_confidence_threshold=0.8
        )
        
        assert config.enabled is False
        assert config.strategy == CacheStrategy.LRU
        assert config.warming_strategy == CacheWarmingStrategy.LAZY
        assert config.max_entries == 500
        assert config.max_memory_mb == 1000
        assert config.ttl_seconds == 3600
        assert config.enable_predictions is False
        assert config.prediction_confidence_threshold == 0.8
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = CacheConfig(max_entries=2000, ttl_seconds=900)
        result = config.to_dict()
        
        assert isinstance(result, dict)
        assert result["enabled"] is True
        assert result["strategy"] == "predictive"
        assert result["warming_strategy"] == "pattern_based"
        assert result["max_entries"] == 2000
        assert result["ttl_seconds"] == 900
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "enabled": False,
            "strategy": "lru",
            "warming_strategy": "aggressive",
            "max_entries": 1500,
            "max_memory_mb": 750,
            "ttl_seconds": 2400,
            "enable_predictions": False,
            "prediction_confidence_threshold": 0.9
        }
        
        config = CacheConfig.from_dict(data)
        
        assert config.enabled is False
        assert config.strategy == CacheStrategy.LRU
        assert config.warming_strategy == CacheWarmingStrategy.AGGRESSIVE
        assert config.max_entries == 1500
        assert config.max_memory_mb == 750
        assert config.ttl_seconds == 2400
        assert config.enable_predictions is False
        assert config.prediction_confidence_threshold == 0.9
    
    def test_from_dict_with_defaults(self):
        """Test creation from dictionary with missing values"""
        data = {"max_entries": 2000}
        config = CacheConfig.from_dict(data)
        
        assert config.enabled is True  # Default value
        assert config.max_entries == 2000  # Provided value


class TestMonitoringConfig:
    """Test MonitoringConfig data class"""
    
    def test_default_values(self):
        """Test default monitoring configuration"""
        config = MonitoringConfig()
        
        assert config.enabled is True
        assert config.collection_interval == 5
        assert config.retention_hours == 24
        assert config.enable_system_metrics is True
        assert config.enable_alerts is True
        assert config.metrics_buffer_size == 10000
        assert config.alert_cooldown_seconds == 300
        assert isinstance(config.performance_targets, dict)
        assert len(config.performance_targets) == 0
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = MonitoringConfig(collection_interval=10, retention_hours=48)
        result = config.to_dict()
        
        assert isinstance(result, dict)
        assert result["collection_interval"] == 10
        assert result["retention_hours"] == 48
        assert result["enabled"] is True
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "enabled": False,
            "collection_interval": 15,
            "retention_hours": 72,
            "enable_alerts": False,
            "performance_targets": {"test": "value"}
        }
        
        config = MonitoringConfig.from_dict(data)
        
        assert config.enabled is False
        assert config.collection_interval == 15
        assert config.retention_hours == 72
        assert config.enable_alerts is False
        assert config.performance_targets == {"test": "value"}


class TestLearningConfig:
    """Test LearningConfig data class"""
    
    def test_default_values(self):
        """Test default learning configuration"""
        config = LearningConfig()
        
        assert config.enabled is True
        assert config.strategy == LearningStrategy.ENSEMBLE
        assert config.learning_rate == 0.01
        assert config.feature_decay_days == 30
        assert config.pattern_confidence_threshold == 0.7
        assert config.enable_persistence is True
        assert config.auto_discovery is True
        assert config.optimization_interval_hours == 24
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = LearningConfig(learning_rate=0.02, feature_decay_days=60)
        result = config.to_dict()
        
        assert result["learning_rate"] == 0.02
        assert result["feature_decay_days"] == 60
        assert result["strategy"] == "ensemble"
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "enabled": False,
            "strategy": "feedback_based",
            "learning_rate": 0.05,
            "feature_decay_days": 15,
            "auto_discovery": False
        }
        
        config = LearningConfig.from_dict(data)
        
        assert config.enabled is False
        assert config.strategy == LearningStrategy.FEEDBACK_BASED
        assert config.learning_rate == 0.05
        assert config.feature_decay_days == 15
        assert config.auto_discovery is False


class TestSecurityConfig:
    """Test SecurityConfig data class"""
    
    def test_default_values(self):
        """Test default security configuration"""
        config = SecurityConfig()
        
        assert config.enable_sandbox is True
        assert config.max_file_size_mb == 100
        assert ".py" in config.allowed_file_extensions
        assert ".git" in config.blocked_paths
        assert config.enable_content_filtering is True
        assert config.max_context_size_mb == 50
        assert config.rate_limit_requests_per_minute == 100
    
    def test_custom_values(self):
        """Test security configuration with custom values"""
        config = SecurityConfig(
            enable_sandbox=False,
            max_file_size_mb=200,
            allowed_file_extensions=[".txt", ".md"],
            blocked_paths=[".test"],
            rate_limit_requests_per_minute=50
        )
        
        assert config.enable_sandbox is False
        assert config.max_file_size_mb == 200
        assert config.allowed_file_extensions == [".txt", ".md"]
        assert config.blocked_paths == [".test"]
        assert config.rate_limit_requests_per_minute == 50
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = SecurityConfig(max_file_size_mb=150)
        result = config.to_dict()
        
        assert result["max_file_size_mb"] == 150
        assert result["enable_sandbox"] is True
        assert isinstance(result["allowed_file_extensions"], list)
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "enable_sandbox": False,
            "max_file_size_mb": 75,
            "allowed_file_extensions": [".py", ".js"],
            "blocked_paths": [".secret"],
            "rate_limit_requests_per_minute": 200
        }
        
        config = SecurityConfig.from_dict(data)
        
        assert config.enable_sandbox is False
        assert config.max_file_size_mb == 75
        assert config.allowed_file_extensions == [".py", ".js"]
        assert config.blocked_paths == [".secret"]
        assert config.rate_limit_requests_per_minute == 200


class TestPerformanceConfig:
    """Test PerformanceConfig data class"""
    
    def test_default_values(self):
        """Test default performance configuration"""
        config = PerformanceConfig()
        
        assert config.max_tokens == 200000
        assert config.max_preparation_time == 30
        assert config.max_concurrent_requests == 10
        assert config.enable_compression is True
        assert config.compression_threshold == 0.8
        assert config.enable_parallel_processing is True
        assert config.worker_pool_size == 4
        assert config.memory_limit_mb == 2048
        assert config.enable_profiling is False
    
    def test_to_dict_and_from_dict(self):
        """Test serialization round trip"""
        original = PerformanceConfig(
            max_tokens=150000,
            max_preparation_time=45,
            enable_profiling=True
        )
        
        data = original.to_dict()
        restored = PerformanceConfig.from_dict(data)
        
        assert restored.max_tokens == 150000
        assert restored.max_preparation_time == 45
        assert restored.enable_profiling is True
        assert restored.max_concurrent_requests == 10  # Default value


class TestContextConfig:
    """Test ContextConfig main configuration class"""
    
    def test_default_values(self):
        """Test default context configuration"""
        config = ContextConfig()
        
        assert config.environment == Environment.DEVELOPMENT
        assert config.project_path is None
        assert config.log_level == "INFO"
        assert config.enable_debug is False
        assert config.enable_intelligence is True
        assert config.enable_cross_story is True
        assert isinstance(config.cache, CacheConfig)
        assert isinstance(config.monitoring, MonitoringConfig)
        assert isinstance(config.learning, LearningConfig)
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.custom_settings, dict)
    
    def test_custom_values(self):
        """Test context configuration with custom values"""
        custom_cache = CacheConfig(max_entries=500)
        custom_monitoring = MonitoringConfig(collection_interval=10)
        
        config = ContextConfig(
            environment=Environment.PRODUCTION,
            project_path="/test/path",
            log_level="WARNING",
            enable_debug=True,
            cache=custom_cache,
            monitoring=custom_monitoring,
            custom_settings={"key": "value"}
        )
        
        assert config.environment == Environment.PRODUCTION
        assert config.project_path == "/test/path"
        assert config.log_level == "WARNING"
        assert config.enable_debug is True
        assert config.cache.max_entries == 500
        assert config.monitoring.collection_interval == 10
        assert config.custom_settings == {"key": "value"}
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = ContextConfig(
            environment=Environment.STAGING,
            project_path="/test",
            enable_debug=True
        )
        
        result = config.to_dict()
        
        assert isinstance(result, dict)
        assert result["environment"] == "staging"
        assert result["project_path"] == "/test"
        assert result["enable_debug"] is True
        assert "cache" in result
        assert "monitoring" in result
        assert "learning" in result
        assert "security" in result
        assert "performance" in result
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "environment": "production",
            "project_path": "/prod/path",
            "log_level": "ERROR",
            "enable_debug": False,
            "cache": {"max_entries": 5000},
            "monitoring": {"collection_interval": 30},
            "custom_settings": {"prod": True}
        }
        
        config = ContextConfig.from_dict(data)
        
        assert config.environment == Environment.PRODUCTION
        assert config.project_path == "/prod/path"
        assert config.log_level == "ERROR"
        assert config.enable_debug is False
        assert config.cache.max_entries == 5000
        assert config.monitoring.collection_interval == 30
        assert config.custom_settings == {"prod": True}
    
    def test_validate_success(self):
        """Test successful validation"""
        config = ContextConfig()
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validate_errors(self):
        """Test validation with errors"""
        # Create invalid configuration
        invalid_cache = CacheConfig(max_entries=-1, max_memory_mb=0)
        invalid_performance = PerformanceConfig(max_tokens=-100, max_preparation_time=0)
        invalid_learning = LearningConfig(learning_rate=2.0)  # > 1.0
        
        config = ContextConfig(
            cache=invalid_cache,
            performance=invalid_performance,
            learning=invalid_learning
        )
        
        errors = config.validate()
        
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert "max_entries must be positive" in error_text
        assert "max_memory_mb must be positive" in error_text
        assert "max_tokens must be positive" in error_text
        assert "max_preparation_time must be positive" in error_text
        assert "learning_rate must be between 0 and 1" in error_text
    
    def test_validate_production_warnings(self):
        """Test production-specific validation warnings"""
        config = ContextConfig(
            environment=Environment.PRODUCTION,
            enable_debug=True,
            performance=PerformanceConfig(enable_profiling=True)
        )
        
        errors = config.validate()
        
        assert len(errors) >= 2
        error_text = " ".join(errors)
        assert "Debug mode should not be enabled in production" in error_text
        assert "Profiling should not be enabled in production" in error_text


class TestConfigurationManager:
    """Test ConfigurationManager class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_file(self, temp_dir):
        """Create test configuration file"""
        config_path = Path(temp_dir) / "test_config.yaml"
        config_data = {
            "environment": "testing",
            "project_path": "/test/project",
            "log_level": "DEBUG",
            "cache": {"max_entries": 2000},
            "monitoring": {"collection_interval": 15}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        return str(config_path)
    
    def test_init_default(self):
        """Test ConfigurationManager initialization with defaults"""
        manager = ConfigurationManager()
        
        assert manager.config_path is None
        assert isinstance(manager.environment, Environment)
        assert manager.enable_hot_reload is True
        assert manager.enable_env_overrides is True
        assert manager._config is None
    
    def test_init_with_params(self, temp_dir):
        """Test ConfigurationManager initialization with parameters"""
        config_path = Path(temp_dir) / "config.yaml"
        
        manager = ConfigurationManager(
            config_path=str(config_path),
            environment=Environment.PRODUCTION,
            enable_hot_reload=False,
            enable_env_overrides=False
        )
        
        assert manager.config_path == config_path
        assert manager.environment == Environment.PRODUCTION
        assert manager.enable_hot_reload is False
        assert manager.enable_env_overrides is False
    
    def test_detect_environment(self):
        """Test environment detection from environment variables"""
        test_cases = [
            ("development", Environment.DEVELOPMENT),
            ("dev", Environment.DEVELOPMENT),
            ("testing", Environment.TESTING),
            ("test", Environment.TESTING),
            ("staging", Environment.STAGING),
            ("stage", Environment.STAGING),
            ("production", Environment.PRODUCTION),
            ("prod", Environment.PRODUCTION),
            ("unknown", Environment.DEVELOPMENT)  # Default fallback
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"CONTEXT_ENV": env_value}):
                manager = ConfigurationManager()
                assert manager.environment == expected
    
    def test_load_config_from_file(self, config_file):
        """Test loading configuration from file"""
        manager = ConfigurationManager(config_path=config_file)
        config = manager.load_config()
        
        assert isinstance(config, ContextConfig)
        assert config.environment == Environment.TESTING
        assert config.project_path == "/test/project"
        assert config.log_level == "DEBUG"
        assert config.cache.max_entries == 2000
        assert config.monitoring.collection_interval == 15
    
    def test_load_config_missing_file(self, temp_dir):
        """Test loading configuration with missing file"""
        missing_path = Path(temp_dir) / "missing.yaml"
        manager = ConfigurationManager(config_path=str(missing_path))
        
        config = manager.load_config()
        
        # Should return default configuration
        assert isinstance(config, ContextConfig)
        assert config.environment == manager.environment
    
    def test_load_config_invalid_file(self, temp_dir):
        """Test loading configuration with invalid file"""
        invalid_path = Path(temp_dir) / "invalid.yaml"
        with open(invalid_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        manager = ConfigurationManager(config_path=str(invalid_path))
        config = manager.load_config()
        
        # Should return default configuration on error
        assert isinstance(config, ContextConfig)
    
    def test_get_config(self, config_file):
        """Test get_config method"""
        manager = ConfigurationManager(config_path=config_file)
        
        # First call should load configuration
        config1 = manager.get_config()
        assert isinstance(config1, ContextConfig)
        
        # Second call should return cached configuration
        config2 = manager.get_config()
        assert config1 is config2
    
    def test_save_config_json(self, temp_dir):
        """Test saving configuration to JSON file"""
        config = ContextConfig(
            environment=Environment.STAGING,
            log_level="WARNING"
        )
        
        save_path = Path(temp_dir) / "saved_config.json"
        manager = ConfigurationManager()
        
        result = manager.save_config(config, str(save_path))
        
        assert result is True
        assert save_path.exists()
        
        # Verify saved content
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["environment"] == "staging"
        assert saved_data["log_level"] == "WARNING"
    
    def test_save_config_yaml(self, temp_dir):
        """Test saving configuration to YAML file"""
        config = ContextConfig(environment=Environment.PRODUCTION)
        save_path = Path(temp_dir) / "saved_config.yaml"
        manager = ConfigurationManager()
        
        result = manager.save_config(config, str(save_path))
        
        assert result is True
        assert save_path.exists()
        
        # Verify saved content
        with open(save_path, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["environment"] == "production"
    
    def test_save_config_invalid(self, temp_dir):
        """Test saving invalid configuration"""
        # Create invalid configuration
        invalid_config = ContextConfig(
            performance=PerformanceConfig(max_tokens=-1)
        )
        
        save_path = Path(temp_dir) / "invalid_config.yaml"
        manager = ConfigurationManager()
        
        result = manager.save_config(invalid_config, str(save_path))
        
        assert result is False
        assert not save_path.exists()
    
    def test_create_template(self, temp_dir):
        """Test creating configuration template"""
        output_path = Path(temp_dir) / "template.yaml"
        manager = ConfigurationManager()
        
        result = manager.create_template(Environment.DEVELOPMENT, str(output_path))
        
        assert result is True
        assert output_path.exists()
        
        # Verify template content
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "Context Management Configuration Template" in content
        assert "Environment: development" in content
        assert "Generated:" in content
    
    def test_environment_config_path(self):
        """Test environment-specific config path generation"""
        manager = ConfigurationManager(environment=Environment.STAGING)
        
        base_path = "/config/app.yaml"
        env_path = manager.get_environment_config_path(base_path)
        
        assert env_path == "/config/app.staging.yaml"
    
    def test_merge_configs(self):
        """Test configuration merging"""
        base_config = ContextConfig(
            environment=Environment.DEVELOPMENT,
            log_level="INFO",
            cache=CacheConfig(max_entries=1000)
        )
        
        override_data = {
            "log_level": "DEBUG",
            "cache": {"max_entries": 2000, "ttl_seconds": 900},
            "new_setting": "value"
        }
        
        manager = ConfigurationManager()
        merged = manager.merge_configs(base_config, override_data)
        
        assert merged.environment == Environment.DEVELOPMENT  # Unchanged
        assert merged.log_level == "DEBUG"  # Overridden
        assert merged.cache.max_entries == 2000  # Overridden
        assert merged.cache.ttl_seconds == 900  # Added
    
    def test_environment_variable_overrides(self):
        """Test environment variable configuration overrides"""
        env_vars = {
            "CONTEXT_LOG_LEVEL": "ERROR",
            "CONTEXT_DEBUG": "true",
            "CONTEXT_MAX_TOKENS": "150000",
            "CONTEXT_CACHE_ENABLED": "false",
            "CONTEXT_CACHE_MAX_ENTRIES": "3000"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = ConfigurationManager(enable_env_overrides=True)
            config = manager.load_config()
            
            assert config.log_level == "ERROR"
            assert config.enable_debug is True
            assert config.performance.max_tokens == 150000
            assert config.cache.enabled is False
            assert config.cache.max_entries == 3000
    
    def test_hot_reload_disabled(self, config_file):
        """Test configuration loading with hot reload disabled"""
        manager = ConfigurationManager(
            config_path=config_file,
            enable_hot_reload=False
        )
        
        config = manager.load_config()
        assert isinstance(config, ContextConfig)
        assert manager._reload_thread is None
    
    def test_stop_hot_reload(self, config_file):
        """Test stopping hot reload"""
        manager = ConfigurationManager(
            config_path=config_file,
            enable_hot_reload=True
        )
        
        manager.load_config()
        # Hot reload would be started in real scenario
        
        manager.stop_hot_reload()
        # Should not raise any errors
    
    def test_reload_callbacks(self, config_file):
        """Test reload callbacks management"""
        manager = ConfigurationManager(config_path=config_file)
        
        callback = Mock()
        manager.add_reload_callback(callback)
        assert callback in manager._reload_callbacks
        
        manager.remove_reload_callback(callback)
        assert callback not in manager._reload_callbacks
    
    def test_deep_merge_functionality(self):
        """Test deep merge implementation"""
        manager = ConfigurationManager()
        
        base = {
            "level1": {
                "level2": {
                    "key1": "value1",
                    "key2": "value2"
                },
                "simple": "base"
            },
            "top_level": "base_value"
        }
        
        override = {
            "level1": {
                "level2": {
                    "key2": "override2",
                    "key3": "value3"
                },
                "new_key": "new_value"
            },
            "new_top": "new_value"
        }
        
        result = manager._deep_merge(base, override)
        
        assert result["level1"]["level2"]["key1"] == "value1"  # Preserved
        assert result["level1"]["level2"]["key2"] == "override2"  # Overridden
        assert result["level1"]["level2"]["key3"] == "value3"  # Added
        assert result["level1"]["simple"] == "base"  # Preserved
        assert result["level1"]["new_key"] == "new_value"  # Added
        assert result["top_level"] == "base_value"  # Preserved
        assert result["new_top"] == "new_value"  # Added


class TestConfigurationHelpers:
    """Test helper functions"""
    
    def test_create_config_templates(self):
        """Test configuration template creation"""
        templates = create_config_templates()
        
        assert isinstance(templates, dict)
        assert len(templates) == 4  # One for each environment
        
        for env in Environment:
            assert env.value in templates
            template_json = templates[env.value]
            
            # Verify it's valid JSON
            config_data = json.loads(template_json)
            assert "environment" in config_data
            assert config_data["environment"] == env.value
    
    def test_load_config_from_env_with_file(self, tmp_path):
        """Test loading config from environment with existing file"""
        config_path = Path(tmp_path) / "context_config.yaml"
        config_data = {"environment": "testing"}
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Change to temp directory so config file is found
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            config = load_config_from_env()
            
            assert isinstance(config, ContextConfig)
            assert config.environment == Environment.TESTING
        finally:
            os.chdir(original_cwd)
    
    def test_load_config_from_env_no_file(self, tmp_path):
        """Test loading config from environment without file"""
        # Change to empty temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            config = load_config_from_env()
            
            # Should return default configuration
            assert isinstance(config, ContextConfig)
        finally:
            os.chdir(original_cwd)
    
    def test_validate_config_file_valid(self, tmp_path):
        """Test validating a valid configuration file"""
        config_path = Path(tmp_path) / "valid_config.json"
        config_data = {
            "environment": "development",
            "log_level": "INFO",
            "performance": {"max_tokens": 200000}
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        errors = validate_config_file(str(config_path))
        assert len(errors) == 0
    
    def test_validate_config_file_invalid(self, tmp_path):
        """Test validating an invalid configuration file"""
        config_path = Path(tmp_path) / "invalid_config.json"
        config_data = {
            "environment": "development",
            "performance": {"max_tokens": -1000}  # Invalid value
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        errors = validate_config_file(str(config_path))
        assert len(errors) > 0
        assert "max_tokens must be positive" in " ".join(errors)
    
    def test_validate_config_file_missing(self):
        """Test validating a missing configuration file"""
        errors = validate_config_file("/nonexistent/config.json")
        assert len(errors) > 0
        assert "Error loading config file" in errors[0]
    
    def test_validate_config_file_malformed(self, tmp_path):
        """Test validating a malformed configuration file"""
        config_path = Path(tmp_path) / "malformed_config.json"
        
        with open(config_path, 'w') as f:
            f.write("{invalid json content")
        
        errors = validate_config_file(str(config_path))
        assert len(errors) > 0
        assert "Error loading config file" in errors[0]


class TestConfigurationIntegration:
    """Integration tests for configuration system"""
    
    @pytest.fixture
    def integration_setup(self):
        """Setup for integration tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_full_configuration_lifecycle(self, integration_setup):
        """Test complete configuration lifecycle"""
        temp_dir = integration_setup
        
        # 1. Create initial configuration
        config = ContextConfig(
            environment=Environment.DEVELOPMENT,
            project_path=temp_dir,
            log_level="DEBUG",
            cache=CacheConfig(max_entries=1500)
        )
        
        # 2. Save configuration
        config_path = Path(temp_dir) / "lifecycle_config.yaml"
        manager = ConfigurationManager()
        assert manager.save_config(config, str(config_path))
        
        # 3. Load configuration
        manager2 = ConfigurationManager(config_path=str(config_path))
        loaded_config = manager2.load_config()
        
        # 4. Verify loaded configuration
        assert loaded_config.environment == Environment.DEVELOPMENT
        assert loaded_config.project_path == temp_dir
        assert loaded_config.log_level == "DEBUG"
        assert loaded_config.cache.max_entries == 1500
        
        # 5. Create environment override
        env_config_path = Path(temp_dir) / "lifecycle_config.development.yaml"
        env_override = {"log_level": "INFO", "cache": {"max_entries": 2000}}
        
        with open(env_config_path, 'w') as f:
            yaml.dump(env_override, f)
        
        # 6. Load with environment override
        manager3 = ConfigurationManager(config_path=str(config_path))
        override_config = manager3.load_config()
        
        assert override_config.log_level == "INFO"  # Overridden
        assert override_config.cache.max_entries == 2000  # Overridden
        assert override_config.environment == Environment.DEVELOPMENT  # Preserved
    
    def test_environment_specific_defaults(self):
        """Test environment-specific default configurations"""
        environments_configs = [
            (Environment.DEVELOPMENT, {"log_level": "DEBUG", "enable_debug": True}),
            (Environment.TESTING, {"log_level": "DEBUG", "enable_debug": True}),
            (Environment.STAGING, {"log_level": "INFO", "enable_debug": False}),
            (Environment.PRODUCTION, {"log_level": "WARNING", "enable_debug": False})
        ]
        
        for env, expected_attrs in environments_configs:
            manager = ConfigurationManager(environment=env)
            config = manager._get_environment_defaults(env)
            
            for attr_name, expected_value in expected_attrs.items():
                actual_value = getattr(config, attr_name)
                assert actual_value == expected_value, f"Environment {env.value}: {attr_name} should be {expected_value}, got {actual_value}"
    
    def test_configuration_validation_edge_cases(self):
        """Test configuration validation edge cases"""
        # Test monitoring collection interval validation
        config = ContextConfig(
            monitoring=MonitoringConfig(collection_interval=0)
        )
        errors = config.validate()
        assert "monitoring collection_interval must be positive" in " ".join(errors)
        
        # Test security max file size validation
        config = ContextConfig(
            security=SecurityConfig(max_file_size_mb=0)
        )
        errors = config.validate()
        assert "security max_file_size_mb must be positive" in " ".join(errors)
        
        # Test learning pattern confidence threshold bounds
        config = ContextConfig(
            learning=LearningConfig(pattern_confidence_threshold=1.5)  # > 1.0
        )
        errors = config.validate()
        # This should be fine as the validation only checks learning_rate bounds
        
        # Test zero learning rate
        config = ContextConfig(
            learning=LearningConfig(learning_rate=0.0)
        )
        errors = config.validate()
        assert "learning_rate must be between 0 and 1" in " ".join(errors)


class TestConfigurationErrors:
    """Test error handling in configuration system"""
    
    def test_parse_env_value_types(self):
        """Test environment variable value parsing"""
        manager = ConfigurationManager()
        
        # Test boolean parsing
        assert manager._parse_env_value("true") is True
        assert manager._parse_env_value("false") is False
        assert manager._parse_env_value("True") is True
        assert manager._parse_env_value("FALSE") is False
        
        # Test integer parsing
        assert manager._parse_env_value("123") == 123
        assert manager._parse_env_value("-456") == -456
        
        # Test float parsing
        assert manager._parse_env_value("123.45") == 123.45
        assert manager._parse_env_value("-67.89") == -67.89
        
        # Test string fallback
        assert manager._parse_env_value("hello") == "hello"
        assert manager._parse_env_value("not_a_number") == "not_a_number"
    
    def test_set_nested_value(self):
        """Test nested value setting utility"""
        manager = ConfigurationManager()
        data = {}
        
        # Test setting nested value
        manager._set_nested_value(data, "level1.level2.key", "value")
        
        assert data["level1"]["level2"]["key"] == "value"
        
        # Test updating existing nested value
        manager._set_nested_value(data, "level1.level2.new_key", "new_value")
        
        assert data["level1"]["level2"]["key"] == "value"  # Preserved
        assert data["level1"]["level2"]["new_key"] == "new_value"  # Added
        
        # Test setting top-level value
        manager._set_nested_value(data, "top_level", "top_value")
        
        assert data["top_level"] == "top_value"
    
    def test_unsupported_config_format(self, tmp_path):
        """Test handling of unsupported configuration format"""
        config_path = Path(tmp_path) / "config.unsupported"
        
        with open(config_path, 'w') as f:
            f.write("some content")
        
        manager = ConfigurationManager()
        
        with pytest.raises(ValueError, match="Unsupported configuration format"):
            manager._load_config_file(config_path)


if __name__ == "__main__":
    pytest.main([__file__])