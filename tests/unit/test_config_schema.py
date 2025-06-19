"""
Comprehensive tests for agent_workflow.config.schema module.

Tests configuration schema validation, environment variable validation,
config file validation, and template generation functionality.
"""

import os
import json
import yaml
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from agent_workflow.config.schema import (
    EnvironmentVariable,
    ConfigSchema,
    ConfigValidator,
    validator,
    validate_environment_variables,
    generate_config_template
)


class TestEnvironmentVariable:
    """Test EnvironmentVariable dataclass"""
    
    def test_environment_variable_creation_minimal(self):
        """Test creating environment variable with minimal parameters"""
        env_var = EnvironmentVariable(name="TEST_VAR")
        
        assert env_var.name == "TEST_VAR"
        assert env_var.default is None
        assert env_var.required is False
        assert env_var.description == ""
        assert env_var.validator is None
        
    def test_environment_variable_creation_full(self):
        """Test creating environment variable with all parameters"""
        validator_func = lambda x: len(x) > 5
        
        env_var = EnvironmentVariable(
            name="FULL_VAR",
            default="default_value",
            required=True,
            description="Full variable description",
            validator=validator_func
        )
        
        assert env_var.name == "FULL_VAR"
        assert env_var.default == "default_value"
        assert env_var.required is True
        assert env_var.description == "Full variable description"
        assert env_var.validator == validator_func
        
    def test_environment_variable_validator_function(self):
        """Test environment variable with validator function"""
        def min_length_validator(value):
            return len(value) >= 3 if value else True
            
        env_var = EnvironmentVariable(
            name="VALIDATED_VAR",
            validator=min_length_validator
        )
        
        assert env_var.validator("abc") is True
        assert env_var.validator("ab") is False
        assert env_var.validator("") is True  # Empty values pass
        assert env_var.validator(None) is True


class TestConfigSchema:
    """Test ConfigSchema dataclass"""
    
    def test_config_schema_creation_minimal(self):
        """Test creating config schema with minimal parameters"""
        schema = ConfigSchema(
            name="test_schema",
            description="Test schema description"
        )
        
        assert schema.name == "test_schema"
        assert schema.description == "Test schema description"
        assert schema.env_vars == {}
        assert schema.required_sections == []
        assert schema.optional_sections == []
        
    def test_config_schema_creation_full(self):
        """Test creating config schema with all parameters"""
        env_var = EnvironmentVariable(name="TEST_VAR")
        
        schema = ConfigSchema(
            name="full_schema",
            description="Full schema description",
            env_vars={"TEST_VAR": env_var},
            required_sections=["global", "projects"],
            optional_sections=["monitoring", "alerts"]
        )
        
        assert schema.name == "full_schema"
        assert schema.description == "Full schema description"
        assert schema.env_vars == {"TEST_VAR": env_var}
        assert schema.required_sections == ["global", "projects"]
        assert schema.optional_sections == ["monitoring", "alerts"]


class TestConfigValidator:
    """Test ConfigValidator class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ConfigValidator()
        
    def test_config_validator_initialization(self):
        """Test ConfigValidator initialization"""
        assert isinstance(self.validator.schemas, dict)
        assert "dependency" in self.validator.schemas
        assert "orchestration" in self.validator.schemas
        
    def test_common_env_vars_defined(self):
        """Test that common environment variables are properly defined"""
        common_vars = self.validator.COMMON_ENV_VARS
        
        assert "DISCORD_BOT_TOKEN" in common_vars
        assert "AGENT_WORKFLOW_CONFIG_DIR" in common_vars
        assert "CONTEXT_ENV" in common_vars
        assert "CONTEXT_LOG_LEVEL" in common_vars
        assert "CLAUDE_MODEL" in common_vars
        assert "CLAUDE_MAX_TOKENS" in common_vars
        assert "CLAUDE_INTEGRATION_ENABLED" in common_vars
        
        # Test specific properties
        discord_var = common_vars["DISCORD_BOT_TOKEN"]
        assert discord_var.name == "DISCORD_BOT_TOKEN"
        assert discord_var.required is False
        assert "Discord bot authentication token" in discord_var.description
        assert discord_var.validator is not None
        
    def test_dependency_schema_registration(self):
        """Test dependency schema is properly registered"""
        schema = self.validator.schemas["dependency"]
        
        assert schema.name == "dependency"
        assert "Dependency tracking configuration" in schema.description
        assert "watcher" in schema.required_sections
        assert "updater" in schema.required_sections
        assert "claude_integration" in schema.required_sections
        assert "rules" in schema.required_sections
        assert "logging" in schema.optional_sections
        
    def test_orchestration_schema_registration(self):
        """Test orchestration schema is properly registered"""
        schema = self.validator.schemas["orchestration"]
        
        assert schema.name == "orchestration"
        assert "Multi-project orchestration configuration" in schema.description
        assert "global" in schema.required_sections
        assert "projects" in schema.required_sections
        assert "monitoring" in schema.optional_sections
        assert "alerts" in schema.optional_sections


class TestConfigValidatorEnvVars:
    """Test ConfigValidator environment variable validation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ConfigValidator()
        
    @patch.dict(os.environ, {
        'DISCORD_BOT_TOKEN': 'valid_token_123456789012345',
        'CONTEXT_ENV': 'production'
    })
    def test_validate_env_vars_orchestration_success(self):
        """Test successful environment variable validation for orchestration"""
        results = self.validator.validate_env_vars("orchestration")
        
        assert results["valid"] is True
        assert len(results["errors"]) == 0
        assert "DISCORD_BOT_TOKEN" in results["values"]
        assert "CONTEXT_ENV" in results["values"]
        assert results["values"]["DISCORD_BOT_TOKEN"] == "valid_token_123456789012345"
        assert results["values"]["CONTEXT_ENV"] == "production"
        
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_env_vars_with_defaults(self):
        """Test environment variable validation with default values"""
        results = self.validator.validate_env_vars("orchestration")
        
        assert results["valid"] is True
        assert "CONTEXT_ENV" in results["values"]
        assert results["values"]["CONTEXT_ENV"] == "development"  # Default value
        
    @patch.dict(os.environ, {
        'DISCORD_BOT_TOKEN': 'short'  # Invalid - too short
    })
    def test_validate_env_vars_validation_failure(self):
        """Test environment variable validation with validator failure"""
        results = self.validator.validate_env_vars("orchestration")
        
        assert results["valid"] is False
        assert len(results["errors"]) >= 1
        assert any("Invalid value for DISCORD_BOT_TOKEN" in error for error in results["errors"])
        
    def test_validate_env_vars_unknown_schema(self):
        """Test environment variable validation for unknown schema"""
        with pytest.raises(ValueError, match="Unknown schema: unknown"):
            self.validator.validate_env_vars("unknown")
            
    @patch.dict(os.environ, {
        'CLAUDE_MAX_TOKENS': 'not_a_number'  # Invalid number
    })
    def test_validate_env_vars_number_validation_failure(self):
        """Test environment variable validation with number validator failure"""
        results = self.validator.validate_env_vars("dependency")
        
        assert results["valid"] is False
        assert any("Invalid value for CLAUDE_MAX_TOKENS" in error for error in results["errors"])
        
    @patch.dict(os.environ, {
        'CLAUDE_INTEGRATION_ENABLED': 'maybe'  # Invalid boolean
    })
    def test_validate_env_vars_boolean_validation_failure(self):
        """Test environment variable validation with boolean validator failure"""
        results = self.validator.validate_env_vars("dependency")
        
        assert results["valid"] is False
        assert any("Invalid value for CLAUDE_INTEGRATION_ENABLED" in error for error in results["errors"])
        
    def test_validate_env_vars_validator_exception(self):
        """Test environment variable validation when validator raises exception"""
        # Create a custom schema with a failing validator
        failing_validator = lambda x: 1/0  # Will raise ZeroDivisionError
        
        env_var = EnvironmentVariable(
            name="FAILING_VAR",
            validator=failing_validator
        )
        
        schema = ConfigSchema(
            name="test_failing",
            description="Test failing validation",
            env_vars={"FAILING_VAR": env_var}
        )
        
        self.validator.schemas["test_failing"] = schema
        
        with patch.dict(os.environ, {'FAILING_VAR': 'test_value'}):
            results = self.validator.validate_env_vars("test_failing")
            
            assert results["valid"] is False
            assert any("Validation error for FAILING_VAR" in error for error in results["errors"])
            
    def test_validate_env_vars_required_missing(self):
        """Test environment variable validation with missing required variable"""
        # Create a custom schema with a required variable
        required_env_var = EnvironmentVariable(
            name="REQUIRED_VAR",
            required=True,
            description="Required test variable"
        )
        
        schema = ConfigSchema(
            name="test_required",
            description="Test required validation",
            env_vars={"REQUIRED_VAR": required_env_var}
        )
        
        self.validator.schemas["test_required"] = schema
        
        with patch.dict(os.environ, {}, clear=True):
            results = self.validator.validate_env_vars("test_required")
            
            assert results["valid"] is False
            assert any("Required environment variable not set: REQUIRED_VAR" in error 
                      for error in results["errors"])


class TestConfigValidatorConfigFile:
    """Test ConfigValidator configuration file validation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ConfigValidator()
        
    def test_validate_config_file_yaml_success(self):
        """Test successful YAML configuration file validation"""
        config_data = {
            "global": {"setting": "value"},
            "projects": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            assert results["valid"] is True
            assert len(results["errors"]) == 0
            assert results["config"] == config_data
        finally:
            os.unlink(temp_path)
            
    def test_validate_config_file_json_success(self):
        """Test successful JSON configuration file validation"""
        config_data = {
            "global": {"setting": "value"},
            "projects": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            assert results["valid"] is True
            assert len(results["errors"]) == 0
            assert results["config"] == config_data
        finally:
            os.unlink(temp_path)
            
    def test_validate_config_file_missing_required_sections(self):
        """Test configuration file validation with missing required sections"""
        config_data = {
            "global": {"setting": "value"}
            # Missing "projects" section
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            assert results["valid"] is False
            assert any("Missing required section: projects" in error for error in results["errors"])
        finally:
            os.unlink(temp_path)
            
    def test_validate_config_file_unknown_sections(self):
        """Test configuration file validation with unknown sections"""
        config_data = {
            "global": {"setting": "value"},
            "projects": {},
            "unknown_section": {"test": "value"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            assert results["valid"] is True  # Unknown sections are warnings, not errors
            assert any("Unknown configuration section: unknown_section" in warning 
                      for warning in results["warnings"])
        finally:
            os.unlink(temp_path)
            
    def test_validate_config_file_not_found(self):
        """Test configuration file validation with non-existent file"""
        results = self.validator.validate_config_file("/nonexistent/file.yaml", "orchestration")
        
        assert results["valid"] is False
        assert any("Configuration file not found" in error for error in results["errors"])
        
    def test_validate_config_file_unsupported_format(self):
        """Test configuration file validation with unsupported format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("not a config file")
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            assert results["valid"] is False
            assert any("Unsupported file format" in error for error in results["errors"])
        finally:
            os.unlink(temp_path)
            
    def test_validate_config_file_invalid_yaml(self):
        """Test configuration file validation with invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            assert results["valid"] is False
            assert any("Error loading configuration file" in error for error in results["errors"])
        finally:
            os.unlink(temp_path)
            
    def test_validate_config_file_invalid_json(self):
        """Test configuration file validation with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json,}')
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            assert results["valid"] is False
            assert any("Error loading configuration file" in error for error in results["errors"])
        finally:
            os.unlink(temp_path)
            
    def test_validate_config_file_unknown_schema(self):
        """Test configuration file validation with unknown schema"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"test": "value"}, f)
            temp_path = f.name
            
        try:
            with pytest.raises(ValueError, match="Unknown schema: unknown"):
                self.validator.validate_config_file(temp_path, "unknown")
        finally:
            os.unlink(temp_path)


class TestConfigValidatorTemplateGeneration:
    """Test ConfigValidator template generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ConfigValidator()
        
    def test_generate_env_template_orchestration(self):
        """Test generating environment template for orchestration schema"""
        template = self.validator.generate_env_template("orchestration")
        
        assert "Environment Variables for Multi-project orchestration configuration" in template
        assert "DISCORD_BOT_TOKEN=" in template
        assert "CONTEXT_ENV=development" in template
        assert "Generated automatically" in template
        
    def test_generate_env_template_dependency(self):
        """Test generating environment template for dependency schema"""
        template = self.validator.generate_env_template("dependency")
        
        assert "Environment Variables for Dependency tracking configuration" in template
        assert "CLAUDE_MODEL=claude-3-opus-20240229" in template
        assert "CLAUDE_MAX_TOKENS=4096" in template
        assert "CLAUDE_INTEGRATION_ENABLED=true" in template
        
    def test_generate_env_template_unknown_schema(self):
        """Test generating environment template for unknown schema"""
        with pytest.raises(ValueError, match="Unknown schema: unknown"):
            self.validator.generate_env_template("unknown")
            
    def test_generate_env_template_format(self):
        """Test environment template format and structure"""
        template = self.validator.generate_env_template("orchestration")
        lines = template.split('\n')
        
        # Check header format
        assert lines[0].startswith("# Environment Variables for")
        assert lines[1] == "# Generated automatically - modify as needed"
        assert lines[2] == ""
        
        # Check variable format (description, required, default, assignment)
        var_sections = template.split('\n\n')[1:]  # Skip header
        for section in var_sections:
            if section.strip():
                section_lines = section.split('\n')
                assert any(line.startswith("# ") for line in section_lines)  # Has description
                assert any("# Required:" in line for line in section_lines)  # Has required info
                assert any("# Default:" in line for line in section_lines)  # Has default info
                assert any("=" in line and not line.startswith("#") for line in section_lines)  # Has assignment


class TestConfigValidatorValidateAll:
    """Test ConfigValidator validate_all_configs method"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ConfigValidator()
        
    @patch('agent_workflow.config.schema.Path')
    def test_validate_all_configs_default_dir(self, mock_path_class):
        """Test validate_all_configs with default configuration directory"""
        # Mock Path behavior with proper path operations
        mock_home_path = Mock()
        mock_path_class.home.return_value = mock_home_path
        
        mock_config_path = Mock()
        mock_home_path.__truediv__ = Mock(return_value=mock_config_path)
        mock_config_path.parent = Mock()
        
        # Mock file existence
        def mock_file_exists(filename):
            mock_file = Mock()
            mock_file.exists.return_value = filename == "orch-config.yaml"
            return mock_file
            
        mock_config_path.parent.__truediv__ = Mock(side_effect=mock_file_exists)
        
        # Mock validation methods
        with patch.object(self.validator, 'validate_config_file') as mock_validate_file, \
             patch.object(self.validator, 'validate_env_vars') as mock_validate_env:
            
            mock_validate_file.return_value = {"valid": True}
            mock_validate_env.return_value = {"valid": True, "values": {"TEST": "value"}}
            
            results = self.validator.validate_all_configs()
            
            assert "overall_valid" in results
            assert "files" in results
            assert "env_vars" in results
            assert "summary" in results
            
    def test_validate_all_configs_no_existing_files(self):
        """Test validate_all_configs with no existing configuration files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a subdirectory to use as config dir, so parent is the temp dir
            config_subdir = Path(temp_dir) / "config"
            config_subdir.mkdir()
            
            # Empty directories with no config files
            results = self.validator.validate_all_configs(str(config_subdir))
            
            assert results["summary"]["total_files"] == 0
            assert "env_vars" in results
            # Environment validation should still run
            assert len(results["env_vars"]) >= 2
            
    def test_validate_all_configs_custom_dir(self):
        """Test validate_all_configs with custom configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test config files
            orch_config = Path(temp_dir) / "orch-config.yaml"
            orch_config.write_text(yaml.dump({"global": {}, "projects": {}}))
            
            dep_config = Path(temp_dir).parent / ".dependency-config.yaml"
            dep_config.write_text(yaml.dump({
                "watcher": {},
                "updater": {},
                "claude_integration": {},
                "rules": {}
            }))
            
            results = self.validator.validate_all_configs(temp_dir)
            
            assert "files" in results
            assert "env_vars" in results
            # At least one file should be validated
            assert results["summary"]["total_files"] >= 1
            
    @patch.dict(os.environ, {
        'DISCORD_BOT_TOKEN': 'test_token_123456789012345',
        'CLAUDE_MODEL': 'claude-3-opus-20240229'
    })
    def test_validate_all_configs_with_env_vars(self):
        """Test validate_all_configs with environment variables set"""
        results = self.validator.validate_all_configs()
        
        assert "env_vars" in results
        assert "orchestration" in results["env_vars"]
        assert "dependency" in results["env_vars"]
        assert results["summary"]["total_env_vars"] > 0
        
    def test_validate_all_configs_with_invalid_files_and_env(self):
        """Test validate_all_configs with invalid config files and environment variables"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a subdirectory to use as config dir
            config_subdir = Path(temp_dir) / "config"
            config_subdir.mkdir()
            
            # Create invalid orchestration config in parent directory
            invalid_orch_config = {
                # Missing required "projects" section
                "global": {"test": "value"}
            }
            
            orch_path = Path(temp_dir) / "orch-config.yaml"
            with open(orch_path, 'w') as f:
                yaml.dump(invalid_orch_config, f)
                
            # Create a schema with required env vars for this test
            required_env_var = EnvironmentVariable(
                name="TEST_REQUIRED_VAR",
                required=True,
                description="Test required variable"
            )
            
            test_schema = ConfigSchema(
                name="test_with_required",
                description="Test schema with required env var",
                env_vars={"TEST_REQUIRED_VAR": required_env_var}
            )
            
            # Temporarily add this schema
            original_schemas = self.validator.schemas.copy()
            self.validator.schemas["test_with_required"] = test_schema
            
            try:
                with patch.dict(os.environ, {}, clear=True):
                    results = self.validator.validate_all_configs(str(config_subdir))
                    
                    # Should be invalid due to both file and env var issues
                    assert results["overall_valid"] is False
                    assert results["summary"]["total_files"] >= 1
                    assert results["summary"]["valid_files"] == 0  # No valid files
                    
            finally:
                # Restore original schemas
                self.validator.schemas = original_schemas
                
    @patch('platform.system')
    def test_validate_all_configs_windows_path_coverage(self, mock_system):
        """Test validate_all_configs with Windows system to cover line 272"""
        mock_system.return_value = "Windows"
        
        # Call without config_dir to trigger default path logic
        results = self.validator.validate_all_configs()
        
        # Should call platform.system when determining default path
        mock_system.assert_called_once()
        assert "overall_valid" in results


class TestGlobalValidator:
    """Test global validator instance and utility functions"""
    
    def test_global_validator_instance(self):
        """Test that global validator instance is properly created"""
        assert validator is not None
        assert isinstance(validator, ConfigValidator)
        assert len(validator.schemas) >= 2
        
    @patch('agent_workflow.config.schema.validator')
    def test_validate_environment_variables_all(self, mock_validator):
        """Test validate_environment_variables function with 'all' schema"""
        mock_validator.validate_all_configs.return_value = {"test": "result"}
        
        result = validate_environment_variables("all")
        
        assert result == {"test": "result"}
        mock_validator.validate_all_configs.assert_called_once()
        
    @patch('agent_workflow.config.schema.validator')
    def test_validate_environment_variables_specific(self, mock_validator):
        """Test validate_environment_variables function with specific schema"""
        mock_validator.validate_env_vars.return_value = {"test": "result"}
        
        result = validate_environment_variables("orchestration")
        
        assert result == {"test": "result"}
        mock_validator.validate_env_vars.assert_called_once_with("orchestration")
        
    @patch('agent_workflow.config.schema.validator')
    def test_generate_config_template_success(self, mock_validator):
        """Test generate_config_template function success"""
        mock_validator.generate_env_template.return_value = "template content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            
        try:
            result = generate_config_template("orchestration", temp_path)
            
            assert result is True
            mock_validator.generate_env_template.assert_called_once_with("orchestration")
            
            # Check file was written
            with open(temp_path, 'r') as f:
                content = f.read()
            assert content == "template content"
        finally:
            os.unlink(temp_path)
            
    @patch('agent_workflow.config.schema.validator')
    @patch('agent_workflow.config.schema.logger')
    def test_generate_config_template_failure(self, mock_logger, mock_validator):
        """Test generate_config_template function failure"""
        mock_validator.generate_env_template.side_effect = ValueError("Template error")
        
        result = generate_config_template("unknown", "/nonexistent/path")
        
        assert result is False
        mock_logger.error.assert_called_once()


class TestConfigValidatorEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ConfigValidator()
        
    def test_empty_config_file(self):
        """Test validation of empty configuration file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            # Empty YAML should load as empty dict and fail validation
            assert results["valid"] is False
            assert any("Missing required section" in error for error in results["errors"])
        finally:
            os.unlink(temp_path)
            
    def test_null_config_file(self):
        """Test validation of config file with null content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("null")  # YAML null
            temp_path = f.name
            
        try:
            results = self.validator.validate_config_file(temp_path, "orchestration")
            
            # Null YAML should be treated as empty and fail validation
            assert results["config"] == {}
        finally:
            os.unlink(temp_path)
            
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_env_vars_all_missing(self):
        """Test environment variable validation with all variables missing"""
        results = self.validator.validate_env_vars("orchestration")
        
        # Should still be valid since no variables are required in orchestration schema
        assert results["valid"] is True
        assert len(results["warnings"]) >= 1  # Should have warnings for missing optional vars
        
    def test_validator_with_none_values(self):
        """Test validator functions that handle None values correctly"""
        # Test the lambda validators with None values
        discord_validator = self.validator.COMMON_ENV_VARS["DISCORD_BOT_TOKEN"].validator
        assert discord_validator(None) is True
        
        tokens_validator = self.validator.COMMON_ENV_VARS["CLAUDE_MAX_TOKENS"].validator
        assert tokens_validator(None) is True
        
        bool_validator = self.validator.COMMON_ENV_VARS["CLAUDE_INTEGRATION_ENABLED"].validator
        assert bool_validator(None) is True


class TestConfigValidatorIntegration:
    """Integration tests for ConfigValidator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ConfigValidator()
        
    def test_full_validation_workflow(self):
        """Test complete validation workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create orchestration config
            orch_config = {
                "global": {
                    "max_concurrent_projects": 5,
                    "enable_audit_logging": True
                },
                "projects": {}
            }
            
            orch_path = Path(temp_dir) / "orch-config.yaml"
            with open(orch_path, 'w') as f:
                yaml.dump(orch_config, f)
                
            # Create dependency config
            dep_config = {
                "watcher": {"watch_patterns": ["**/*.py"]},
                "updater": {"auto_update": {"tests": False}},
                "claude_integration": {"enabled": True},
                "rules": {"coverage_threshold": 0.95}
            }
            
            dep_path = Path(temp_dir).parent / ".dependency-config.yaml"
            with open(dep_path, 'w') as f:
                yaml.dump(dep_config, f)
                
            # Test individual file validation
            orch_results = self.validator.validate_config_file(str(orch_path), "orchestration")
            dep_results = self.validator.validate_config_file(str(dep_path), "dependency")
            
            assert orch_results["valid"] is True
            assert dep_results["valid"] is True
            
            # Test environment validation
            env_results = self.validator.validate_env_vars("orchestration")
            assert "valid" in env_results
            
            # Test template generation
            template = self.validator.generate_env_template("orchestration")
            assert len(template) > 0
            assert "DISCORD_BOT_TOKEN" in template
            
            # Test full validation
            all_results = self.validator.validate_all_configs(temp_dir)
            assert "overall_valid" in all_results
            assert "summary" in all_results


if __name__ == '__main__':
    pytest.main([__file__])