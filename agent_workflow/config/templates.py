"""
Configuration Templates for Agent Workflow

Provides default configuration templates for different deployment scenarios
and project types.
"""

from typing import Dict, Any
import yaml
import json
from pathlib import Path


class ConfigTemplates:
    """Configuration template generator"""
    
    @staticmethod
    def get_development_orch_config() -> Dict[str, Any]:
        """Get development orchestration configuration template"""
        return {
            "global": {
                "alert_channels": [],
                "backup_retention_days": 7,
                "enable_audit_logging": True,
                "enable_cloud_backup": False,
                "enable_cross_project_insights": True,
                "enable_knowledge_sharing": True,
                "enable_pattern_learning": True,
                "enable_project_isolation": True,
                "global_cpu_cores": 2,
                "global_discord_guild": None,
                "global_disk_limit_gb": 10,
                "global_memory_limit_gb": 4,
                "global_state_path": ".orch-global",
                "health_check_interval_seconds": 120,
                "max_concurrent_projects": 5,
                "max_total_agents": 10,
                "monitoring_webhook_url": None,
                "resource_allocation_strategy": "fair_share",
                "resource_rebalance_interval_seconds": 600,
                "scheduling_interval_seconds": 60,
                "secret_management_provider": "local"
            },
            "projects": {}
        }
    
    @staticmethod
    def get_production_orch_config() -> Dict[str, Any]:
        """Get production orchestration configuration template"""
        return {
            "global": {
                "alert_channels": [],
                "backup_retention_days": 30,
                "enable_audit_logging": True,
                "enable_cloud_backup": True,
                "enable_cross_project_insights": True,
                "enable_knowledge_sharing": True,
                "enable_pattern_learning": True,
                "enable_project_isolation": True,
                "global_cpu_cores": 8,
                "global_discord_guild": None,
                "global_disk_limit_gb": 100,
                "global_memory_limit_gb": 16,
                "global_state_path": ".orch-global",
                "health_check_interval_seconds": 60,
                "max_concurrent_projects": 20,
                "max_total_agents": 50,
                "monitoring_webhook_url": None,
                "resource_allocation_strategy": "priority_based",
                "resource_rebalance_interval_seconds": 300,
                "scheduling_interval_seconds": 30,
                "secret_management_provider": "vault"
            },
            "projects": {}
        }
    
    @staticmethod
    def get_dependency_config() -> Dict[str, Any]:
        """Get dependency tracking configuration template"""
        return {
            "watcher": {
                "watch_patterns": ["**/*.py", "**/*.md", "**/*.yaml"],
                "ignore_patterns": [
                    "__pycache__", ".git", ".pytest_cache", 
                    "venv", "env", "build", "dist", "*.egg-info", "htmlcov"
                ],
                "debounce_seconds": 2.0,
                "max_concurrent_updates": 3
            },
            "updater": {
                "auto_update": {
                    "tests": False,
                    "docs": False,
                    "dependent_code": False
                },
                "update_modes": {
                    "tests": "suggest",
                    "docs": "suggest", 
                    "code": "manual"
                },
                "validation": {
                    "run_tests": True,
                    "check_coverage": True,
                    "lint_code": True
                }
            },
            "claude_integration": {
                "enabled": True,
                "model": "claude-3-opus-20240229",
                "max_tokens": 4096,
                "instructions": {
                    "test_creation": "Create comprehensive unit tests following existing patterns",
                    "test_update": "Update tests to cover changes, maintain existing test style",
                    "doc_update": "Update documentation to reflect changes, keep examples current"
                },
                "env_overrides": {
                    "model": "CLAUDE_MODEL",
                    "max_tokens": "CLAUDE_MAX_TOKENS",
                    "enabled": "CLAUDE_INTEGRATION_ENABLED"
                }
            },
            "rules": {
                "test_file_pattern": "tests/unit/test_{module}.py",
                "doc_file_pattern": "docs_src/api/{module}.md",
                "coverage_threshold": 0.95,
                "require_tests_for_new_code": True
            }
        }
    
    @staticmethod
    def get_context_config() -> Dict[str, Any]:
        """Get context management configuration template"""
        return {
            "environment": "development",
            "project_path": None,
            "log_level": "INFO",
            "enable_debug": False,
            "enable_intelligence": True,
            "enable_cross_story": True,
            "cache": {
                "enabled": True,
                "strategy": "predictive",
                "warming_strategy": "pattern_based",
                "max_entries": 1000,
                "max_memory_mb": 500,
                "ttl_seconds": 1800,
                "enable_predictions": True,
                "prediction_confidence_threshold": 0.7
            },
            "monitoring": {
                "enabled": True,
                "collection_interval": 5,
                "retention_hours": 24,
                "enable_system_metrics": True,
                "enable_alerts": True,
                "metrics_buffer_size": 10000,
                "alert_cooldown_seconds": 300,
                "performance_targets": {}
            },
            "learning": {
                "enabled": True,
                "strategy": "ensemble",
                "learning_rate": 0.01,
                "feature_decay_days": 30,
                "pattern_confidence_threshold": 0.7,
                "enable_persistence": True,
                "auto_discovery": True,
                "optimization_interval_hours": 24
            },
            "security": {
                "enable_sandbox": True,
                "max_file_size_mb": 100,
                "allowed_file_extensions": [
                    ".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml", ".yml"
                ],
                "blocked_paths": [".git", "__pycache__", "node_modules", ".env"],
                "enable_content_filtering": True,
                "max_context_size_mb": 50,
                "rate_limit_requests_per_minute": 100
            },
            "performance": {
                "max_tokens": 200000,
                "max_preparation_time": 30,
                "max_concurrent_requests": 10,
                "enable_compression": True,
                "compression_threshold": 0.8,
                "enable_parallel_processing": True,
                "worker_pool_size": 4,
                "memory_limit_mb": 2048,
                "enable_profiling": False
            },
            "custom_settings": {}
        }
    
    @staticmethod
    def get_environment_template() -> str:
        """Get environment variables template"""
        return """# Agent Workflow Environment Variables
# Copy this file to .env and customize as needed

# Discord Integration
DISCORD_BOT_TOKEN=

# Configuration Directory
AGENT_WORKFLOW_CONFIG_DIR=

# Environment Settings
CONTEXT_ENV=development
CONTEXT_LOG_LEVEL=INFO
CONTEXT_DEBUG=false

# Claude AI Integration  
CLAUDE_MODEL=claude-3-opus-20240229
CLAUDE_MAX_TOKENS=4096
CLAUDE_INTEGRATION_ENABLED=true

# Context Management
CONTEXT_CACHE_ENABLED=true
CONTEXT_CACHE_MAX_ENTRIES=1000
CONTEXT_CACHE_MEMORY_MB=500
CONTEXT_MONITORING_ENABLED=true
CONTEXT_LEARNING_ENABLED=true
CONTEXT_LEARNING_RATE=0.01

# Performance Settings
CONTEXT_MAX_TOKENS=200000
CONTEXT_MAX_CONCURRENT_REQUESTS=10
CONTEXT_ENABLE_COMPRESSION=true

# Security Settings
CONTEXT_ENABLE_SANDBOX=true
CONTEXT_MAX_FILE_SIZE_MB=100
CONTEXT_MAX_CONTEXT_SIZE_MB=50
"""

    @staticmethod
    def save_template(template_name: str, output_path: str, format: str = "yaml") -> bool:
        """
        Save configuration template to file
        
        Args:
            template_name: Name of template to save
            output_path: Path to save template 
            format: Output format (yaml, json, env)
            
        Returns:
            True if saved successfully
        """
        try:
            templates = ConfigTemplates()
            
            # Get template data
            if template_name == "orch-dev":
                data = templates.get_development_orch_config()
            elif template_name == "orch-prod":
                data = templates.get_production_orch_config()
            elif template_name == "dependency":
                data = templates.get_dependency_config()
            elif template_name == "context":
                data = templates.get_context_config()
            elif template_name == "env":
                # Environment template is always text format
                with open(output_path, 'w') as f:
                    f.write(templates.get_environment_template())
                return True
            else:
                raise ValueError(f"Unknown template: {template_name}")
            
            # Save in requested format
            with open(output_path, 'w') as f:
                if format == "yaml":
                    yaml.dump(data, f, default_flow_style=False, indent=2)
                elif format == "json":
                    json.dump(data, f, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def list_templates() -> Dict[str, str]:
        """List available templates"""
        return {
            "orch-dev": "Development orchestration configuration",
            "orch-prod": "Production orchestration configuration", 
            "dependency": "Dependency tracking configuration",
            "context": "Context management configuration",
            "env": "Environment variables template"
        }