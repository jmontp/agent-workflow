"""
Configuration Schema Validation for Agent Workflow

Provides centralized schema validation for all configuration files
including YAML, JSON, and environment variable validation.
"""

import os
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentVariable:
    """Environment variable configuration"""
    name: str
    default: Optional[str] = None
    required: bool = False
    description: str = ""
    validator: Optional[callable] = None


@dataclass  
class ConfigSchema:
    """Configuration schema definition"""
    name: str
    description: str
    env_vars: Dict[str, EnvironmentVariable] = field(default_factory=dict)
    required_sections: List[str] = field(default_factory=list)
    optional_sections: List[str] = field(default_factory=list)


class ConfigValidator:
    """Configuration validation utilities"""
    
    # Common environment variables across the system
    COMMON_ENV_VARS = {
        "DISCORD_BOT_TOKEN": EnvironmentVariable(
            name="DISCORD_BOT_TOKEN",
            required=False,
            description="Discord bot authentication token",
            validator=lambda x: len(x) > 20 if x else True
        ),
        "AGENT_WORKFLOW_CONFIG_DIR": EnvironmentVariable(
            name="AGENT_WORKFLOW_CONFIG_DIR", 
            description="Custom configuration directory path"
        ),
        "CONTEXT_ENV": EnvironmentVariable(
            name="CONTEXT_ENV",
            default="development",
            description="Deployment environment (development/testing/staging/production)"
        ),
        "CONTEXT_LOG_LEVEL": EnvironmentVariable(
            name="CONTEXT_LOG_LEVEL",
            default="INFO", 
            description="Logging level (DEBUG/INFO/WARNING/ERROR)"
        ),
        "CLAUDE_MODEL": EnvironmentVariable(
            name="CLAUDE_MODEL",
            default="claude-3-opus-20240229",
            description="Claude model to use for AI integration"
        ),
        "CLAUDE_MAX_TOKENS": EnvironmentVariable(
            name="CLAUDE_MAX_TOKENS",
            default="4096",
            description="Maximum tokens for Claude requests",
            validator=lambda x: x.isdigit() and int(x) > 0 if x else True
        ),
        "CLAUDE_INTEGRATION_ENABLED": EnvironmentVariable(
            name="CLAUDE_INTEGRATION_ENABLED",
            default="true",
            description="Enable/disable Claude integration",
            validator=lambda x: x.lower() in ['true', 'false'] if x else True
        )
    }
    
    def __init__(self):
        self.schemas: Dict[str, ConfigSchema] = {}
        self._register_default_schemas()
    
    def _register_default_schemas(self):
        """Register default configuration schemas"""
        
        # Dependency configuration schema
        self.schemas["dependency"] = ConfigSchema(
            name="dependency",
            description="Dependency tracking configuration",
            env_vars={
                "CLAUDE_MODEL": self.COMMON_ENV_VARS["CLAUDE_MODEL"],
                "CLAUDE_MAX_TOKENS": self.COMMON_ENV_VARS["CLAUDE_MAX_TOKENS"],
                "CLAUDE_INTEGRATION_ENABLED": self.COMMON_ENV_VARS["CLAUDE_INTEGRATION_ENABLED"]
            },
            required_sections=["watcher", "updater", "claude_integration", "rules"],
            optional_sections=["logging"]
        )
        
        # Orchestration configuration schema  
        self.schemas["orchestration"] = ConfigSchema(
            name="orchestration",
            description="Multi-project orchestration configuration",
            env_vars={
                "DISCORD_BOT_TOKEN": self.COMMON_ENV_VARS["DISCORD_BOT_TOKEN"],
                "CONTEXT_ENV": self.COMMON_ENV_VARS["CONTEXT_ENV"]
            },
            required_sections=["global", "projects"],
            optional_sections=["monitoring", "alerts"]
        )
    
    def validate_env_vars(self, schema_name: str) -> Dict[str, Any]:
        """
        Validate environment variables for a schema
        
        Args:
            schema_name: Name of schema to validate
            
        Returns:
            Dict with validation results and resolved values
        """
        if schema_name not in self.schemas:
            raise ValueError(f"Unknown schema: {schema_name}")
        
        schema = self.schemas[schema_name]
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "values": {}
        }
        
        for var_name, env_var in schema.env_vars.items():
            value = os.getenv(env_var.name, env_var.default)
            
            # Check required variables
            if env_var.required and value is None:
                results["valid"] = False
                results["errors"].append(f"Required environment variable not set: {env_var.name}")
                continue
            
            # Validate value if validator provided
            if value and env_var.validator:
                try:
                    if not env_var.validator(value):
                        results["valid"] = False
                        results["errors"].append(f"Invalid value for {env_var.name}: {value}")
                        continue
                except Exception as e:
                    results["valid"] = False
                    results["errors"].append(f"Validation error for {env_var.name}: {str(e)}")
                    continue
            
            results["values"][var_name] = value
            
            # Log missing optional variables
            if value is None and not env_var.required:
                results["warnings"].append(f"Optional environment variable not set: {env_var.name}")
        
        return results
    
    def validate_config_file(self, file_path: str, schema_name: str) -> Dict[str, Any]:
        """
        Validate configuration file against schema
        
        Args:
            file_path: Path to configuration file
            schema_name: Name of schema to validate against
            
        Returns:
            Dict with validation results
        """
        if schema_name not in self.schemas:
            raise ValueError(f"Unknown schema: {schema_name}")
        
        schema = self.schemas[schema_name]
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": {}
        }
        
        try:
            # Load configuration file
            config_path = Path(file_path)
            if not config_path.exists():
                results["valid"] = False
                results["errors"].append(f"Configuration file not found: {file_path}")
                return results
            
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f) or {}
                elif config_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    results["valid"] = False
                    results["errors"].append(f"Unsupported file format: {config_path.suffix}")
                    return results
            
            results["config"] = config
            
            # Check required sections
            for section in schema.required_sections:
                if section not in config:
                    results["valid"] = False
                    results["errors"].append(f"Missing required section: {section}")
            
            # Warn about unknown sections
            known_sections = set(schema.required_sections + schema.optional_sections)
            for section in config.keys():
                if section not in known_sections:
                    results["warnings"].append(f"Unknown configuration section: {section}")
            
        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Error loading configuration file: {str(e)}")
        
        return results
    
    def generate_env_template(self, schema_name: str) -> str:
        """
        Generate environment variable template for schema
        
        Args:
            schema_name: Name of schema
            
        Returns:
            Environment variable template as string
        """
        if schema_name not in self.schemas:
            raise ValueError(f"Unknown schema: {schema_name}")
        
        schema = self.schemas[schema_name]
        template_lines = [
            f"# Environment Variables for {schema.description}",
            f"# Generated automatically - modify as needed",
            ""
        ]
        
        for var_name, env_var in schema.env_vars.items():
            template_lines.extend([
                f"# {env_var.description}",
                f"# Required: {'Yes' if env_var.required else 'No'}",
                f"# Default: {env_var.default or 'None'}",
                f"{env_var.name}={env_var.default or ''}",
                ""
            ])
        
        return "\n".join(template_lines)
    
    def validate_all_configs(self, config_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate all configuration files in the system
        
        Args:
            config_dir: Optional custom config directory
            
        Returns:
            Comprehensive validation results
        """
        if config_dir:
            config_path = Path(config_dir)
        else:
            # Use default config dir without importing from CLI to avoid circular imports
            import platform
            if platform.system() == "Windows":
                base_dir = Path.home() / "AppData" / "Local"
            else:
                base_dir = Path.home()
            config_path = base_dir / ".agent-workflow"
        
        results = {
            "overall_valid": True,
            "files": {},
            "env_vars": {},
            "summary": {
                "total_files": 0,
                "valid_files": 0,
                "total_env_vars": 0,
                "valid_env_vars": 0
            }
        }
        
        # Check common config files
        config_files = [
            ("orch-config.yaml", "orchestration"),
            (".dependency-config.yaml", "dependency")
        ]
        
        for filename, schema in config_files:
            file_path = config_path.parent / filename
            if file_path.exists():
                file_results = self.validate_config_file(str(file_path), schema)
                results["files"][filename] = file_results
                results["summary"]["total_files"] += 1
                if file_results["valid"]:
                    results["summary"]["valid_files"] += 1
                else:
                    results["overall_valid"] = False
        
        # Check environment variables for all schemas
        for schema_name in self.schemas:
            env_results = self.validate_env_vars(schema_name)
            results["env_vars"][schema_name] = env_results
            results["summary"]["total_env_vars"] += len(self.schemas[schema_name].env_vars)
            if env_results["valid"]:
                results["summary"]["valid_env_vars"] += len([v for v in env_results["values"].values() if v])
            else:
                results["overall_valid"] = False
        
        return results


# Global validator instance
validator = ConfigValidator()


def validate_environment_variables(schema: str = "all") -> Dict[str, Any]:
    """Validate environment variables for specified schema or all schemas"""
    if schema == "all":
        return validator.validate_all_configs()
    else:
        return validator.validate_env_vars(schema)


def generate_config_template(schema: str, output_path: str) -> bool:
    """Generate configuration template file"""
    try:
        template = validator.generate_env_template(schema)
        with open(output_path, 'w') as f:
            f.write(template)
        return True
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}")
        return False