"""
Comprehensive tests for agent_workflow.config.templates module.

Tests configuration template generation for all template types,
output formats, and error handling scenarios.
"""

import json
import yaml
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from agent_workflow.config.templates import ConfigTemplates


class TestConfigTemplatesStaticMethods:
    """Test ConfigTemplates static methods for template generation"""
    
    def test_get_development_orch_config(self):
        """Test getting development orchestration configuration template"""
        config = ConfigTemplates.get_development_orch_config()
        
        # Test structure
        assert isinstance(config, dict)
        assert "global" in config
        assert "projects" in config
        
        # Test global section structure
        global_config = config["global"]
        assert isinstance(global_config, dict)
        
        # Test specific development settings
        assert global_config["global_cpu_cores"] == 2
        assert global_config["global_memory_limit_gb"] == 4
        assert global_config["global_disk_limit_gb"] == 10
        assert global_config["max_concurrent_projects"] == 5
        assert global_config["max_total_agents"] == 10
        assert global_config["backup_retention_days"] == 7
        assert global_config["enable_cloud_backup"] is False
        assert global_config["health_check_interval_seconds"] == 120
        assert global_config["resource_allocation_strategy"] == "fair_share"
        assert global_config["secret_management_provider"] == "local"
        
        # Test boolean flags
        assert global_config["enable_audit_logging"] is True
        assert global_config["enable_cross_project_insights"] is True
        assert global_config["enable_knowledge_sharing"] is True
        assert global_config["enable_pattern_learning"] is True
        assert global_config["enable_project_isolation"] is True
        
        # Test projects section
        assert config["projects"] == {}
        
    def test_get_production_orch_config(self):
        """Test getting production orchestration configuration template"""
        config = ConfigTemplates.get_production_orch_config()
        
        # Test structure
        assert isinstance(config, dict)
        assert "global" in config
        assert "projects" in config
        
        # Test global section structure
        global_config = config["global"]
        assert isinstance(global_config, dict)
        
        # Test specific production settings (higher limits)
        assert global_config["global_cpu_cores"] == 8
        assert global_config["global_memory_limit_gb"] == 16
        assert global_config["global_disk_limit_gb"] == 100
        assert global_config["max_concurrent_projects"] == 20
        assert global_config["max_total_agents"] == 50
        assert global_config["backup_retention_days"] == 30
        assert global_config["enable_cloud_backup"] is True
        assert global_config["health_check_interval_seconds"] == 60
        assert global_config["resource_allocation_strategy"] == "priority_based"
        assert global_config["secret_management_provider"] == "vault"
        
        # Test boolean flags
        assert global_config["enable_audit_logging"] is True
        assert global_config["enable_cross_project_insights"] is True
        assert global_config["enable_knowledge_sharing"] is True
        assert global_config["enable_pattern_learning"] is True
        assert global_config["enable_project_isolation"] is True
        
        # Test projects section
        assert config["projects"] == {}
        
    def test_development_vs_production_differences(self):
        """Test key differences between development and production configs"""
        dev_config = ConfigTemplates.get_development_orch_config()
        prod_config = ConfigTemplates.get_production_orch_config()
        
        dev_global = dev_config["global"]
        prod_global = prod_config["global"]
        
        # Production should have higher resource limits
        assert prod_global["global_cpu_cores"] > dev_global["global_cpu_cores"]
        assert prod_global["global_memory_limit_gb"] > dev_global["global_memory_limit_gb"]
        assert prod_global["global_disk_limit_gb"] > dev_global["global_disk_limit_gb"]
        assert prod_global["max_concurrent_projects"] > dev_global["max_concurrent_projects"]
        assert prod_global["max_total_agents"] > dev_global["max_total_agents"]
        
        # Production should have longer backup retention
        assert prod_global["backup_retention_days"] > dev_global["backup_retention_days"]
        
        # Production should enable cloud backup
        assert prod_global["enable_cloud_backup"] is True
        assert dev_global["enable_cloud_backup"] is False
        
        # Production should have more frequent health checks
        assert prod_global["health_check_interval_seconds"] < dev_global["health_check_interval_seconds"]
        
        # Different resource allocation strategies
        assert prod_global["resource_allocation_strategy"] == "priority_based"
        assert dev_global["resource_allocation_strategy"] == "fair_share"
        
        # Different secret management
        assert prod_global["secret_management_provider"] == "vault"
        assert dev_global["secret_management_provider"] == "local"


class TestDependencyConfigTemplate:
    """Test dependency tracking configuration template"""
    
    def test_get_dependency_config_structure(self):
        """Test dependency configuration template structure"""
        config = ConfigTemplates.get_dependency_config()
        
        # Test main sections
        assert isinstance(config, dict)
        assert "watcher" in config
        assert "updater" in config
        assert "claude_integration" in config
        assert "rules" in config
        
    def test_dependency_config_watcher_section(self):
        """Test dependency configuration watcher section"""
        config = ConfigTemplates.get_dependency_config()
        watcher = config["watcher"]
        
        assert isinstance(watcher, dict)
        assert "watch_patterns" in watcher
        assert "ignore_patterns" in watcher
        assert "debounce_seconds" in watcher
        assert "max_concurrent_updates" in watcher
        
        # Test watch patterns
        assert isinstance(watcher["watch_patterns"], list)
        assert "**/*.py" in watcher["watch_patterns"]
        assert "**/*.md" in watcher["watch_patterns"]
        assert "**/*.yaml" in watcher["watch_patterns"]
        
        # Test ignore patterns
        assert isinstance(watcher["ignore_patterns"], list)
        assert "__pycache__" in watcher["ignore_patterns"]
        assert ".git" in watcher["ignore_patterns"]
        assert ".pytest_cache" in watcher["ignore_patterns"]
        assert "venv" in watcher["ignore_patterns"]
        assert "env" in watcher["ignore_patterns"]
        
        # Test numeric settings
        assert isinstance(watcher["debounce_seconds"], float)
        assert watcher["debounce_seconds"] == 2.0
        assert isinstance(watcher["max_concurrent_updates"], int)
        assert watcher["max_concurrent_updates"] == 3
        
    def test_dependency_config_updater_section(self):
        """Test dependency configuration updater section"""
        config = ConfigTemplates.get_dependency_config()
        updater = config["updater"]
        
        assert isinstance(updater, dict)
        assert "auto_update" in updater
        assert "update_modes" in updater
        assert "validation" in updater
        
        # Test auto_update settings
        auto_update = updater["auto_update"]
        assert auto_update["tests"] is False
        assert auto_update["docs"] is False
        assert auto_update["dependent_code"] is False
        
        # Test update_modes settings
        update_modes = updater["update_modes"]
        assert update_modes["tests"] == "suggest"
        assert update_modes["docs"] == "suggest"
        assert update_modes["code"] == "manual"
        
        # Test validation settings
        validation = updater["validation"]
        assert validation["run_tests"] is True
        assert validation["check_coverage"] is True
        assert validation["lint_code"] is True
        
    def test_dependency_config_claude_integration_section(self):
        """Test dependency configuration Claude integration section"""
        config = ConfigTemplates.get_dependency_config()
        claude = config["claude_integration"]
        
        assert isinstance(claude, dict)
        assert "enabled" in claude
        assert "model" in claude
        assert "max_tokens" in claude
        assert "instructions" in claude
        assert "env_overrides" in claude
        
        # Test basic settings
        assert claude["enabled"] is True
        assert claude["model"] == "claude-3-opus-20240229"
        assert claude["max_tokens"] == 4096
        
        # Test instructions
        instructions = claude["instructions"]
        assert isinstance(instructions, dict)
        assert "test_creation" in instructions
        assert "test_update" in instructions
        assert "doc_update" in instructions
        
        # Test environment overrides
        env_overrides = claude["env_overrides"]
        assert env_overrides["model"] == "CLAUDE_MODEL"
        assert env_overrides["max_tokens"] == "CLAUDE_MAX_TOKENS"
        assert env_overrides["enabled"] == "CLAUDE_INTEGRATION_ENABLED"
        
    def test_dependency_config_rules_section(self):
        """Test dependency configuration rules section"""
        config = ConfigTemplates.get_dependency_config()
        rules = config["rules"]
        
        assert isinstance(rules, dict)
        assert "test_file_pattern" in rules
        assert "doc_file_pattern" in rules
        assert "coverage_threshold" in rules
        assert "require_tests_for_new_code" in rules
        
        # Test patterns
        assert rules["test_file_pattern"] == "tests/unit/test_{module}.py"
        assert rules["doc_file_pattern"] == "docs_src/api/{module}.md"
        
        # Test numeric threshold
        assert rules["coverage_threshold"] == 0.95
        
        # Test boolean requirement
        assert rules["require_tests_for_new_code"] is True


class TestContextConfigTemplate:
    """Test context management configuration template"""
    
    def test_get_context_config_structure(self):
        """Test context configuration template structure"""
        config = ConfigTemplates.get_context_config()
        
        # Test main sections
        assert isinstance(config, dict)
        assert "environment" in config
        assert "project_path" in config
        assert "log_level" in config
        assert "cache" in config
        assert "monitoring" in config
        assert "learning" in config
        assert "security" in config
        assert "performance" in config
        assert "custom_settings" in config
        
    def test_context_config_basic_settings(self):
        """Test context configuration basic settings"""
        config = ConfigTemplates.get_context_config()
        
        assert config["environment"] == "development"
        assert config["project_path"] is None
        assert config["log_level"] == "INFO"
        assert config["enable_debug"] is False
        assert config["enable_intelligence"] is True
        assert config["enable_cross_story"] is True
        
    def test_context_config_cache_section(self):
        """Test context configuration cache section"""
        config = ConfigTemplates.get_context_config()
        cache = config["cache"]
        
        assert isinstance(cache, dict)
        assert cache["enabled"] is True
        assert cache["strategy"] == "predictive"
        assert cache["warming_strategy"] == "pattern_based"
        assert cache["max_entries"] == 1000
        assert cache["max_memory_mb"] == 500
        assert cache["ttl_seconds"] == 1800
        assert cache["enable_predictions"] is True
        assert cache["prediction_confidence_threshold"] == 0.7
        
    def test_context_config_monitoring_section(self):
        """Test context configuration monitoring section"""
        config = ConfigTemplates.get_context_config()
        monitoring = config["monitoring"]
        
        assert isinstance(monitoring, dict)
        assert monitoring["enabled"] is True
        assert monitoring["collection_interval"] == 5
        assert monitoring["retention_hours"] == 24
        assert monitoring["enable_system_metrics"] is True
        assert monitoring["enable_alerts"] is True
        assert monitoring["metrics_buffer_size"] == 10000
        assert monitoring["alert_cooldown_seconds"] == 300
        assert isinstance(monitoring["performance_targets"], dict)
        
    def test_context_config_learning_section(self):
        """Test context configuration learning section"""
        config = ConfigTemplates.get_context_config()
        learning = config["learning"]
        
        assert isinstance(learning, dict)
        assert learning["enabled"] is True
        assert learning["strategy"] == "ensemble"
        assert learning["learning_rate"] == 0.01
        assert learning["feature_decay_days"] == 30
        assert learning["pattern_confidence_threshold"] == 0.7
        assert learning["enable_persistence"] is True
        assert learning["auto_discovery"] is True
        assert learning["optimization_interval_hours"] == 24
        
    def test_context_config_security_section(self):
        """Test context configuration security section"""
        config = ConfigTemplates.get_context_config()
        security = config["security"]
        
        assert isinstance(security, dict)
        assert security["enable_sandbox"] is True
        assert security["max_file_size_mb"] == 100
        assert security["max_context_size_mb"] == 50
        assert security["rate_limit_requests_per_minute"] == 100
        assert security["enable_content_filtering"] is True
        
        # Test allowed file extensions
        allowed_extensions = security["allowed_file_extensions"]
        assert isinstance(allowed_extensions, list)
        assert ".py" in allowed_extensions
        assert ".js" in allowed_extensions
        assert ".ts" in allowed_extensions
        assert ".md" in allowed_extensions
        assert ".json" in allowed_extensions
        assert ".yaml" in allowed_extensions
        
        # Test blocked paths
        blocked_paths = security["blocked_paths"]
        assert isinstance(blocked_paths, list)
        assert ".git" in blocked_paths
        assert "__pycache__" in blocked_paths
        assert "node_modules" in blocked_paths
        assert ".env" in blocked_paths
        
    def test_context_config_performance_section(self):
        """Test context configuration performance section"""
        config = ConfigTemplates.get_context_config()
        performance = config["performance"]
        
        assert isinstance(performance, dict)
        assert performance["max_tokens"] == 200000
        assert performance["max_preparation_time"] == 30
        assert performance["max_concurrent_requests"] == 10
        assert performance["enable_compression"] is True
        assert performance["compression_threshold"] == 0.8
        assert performance["enable_parallel_processing"] is True
        assert performance["worker_pool_size"] == 4
        assert performance["memory_limit_mb"] == 2048
        assert performance["enable_profiling"] is False


class TestEnvironmentTemplate:
    """Test environment variables template"""
    
    def test_get_environment_template_content(self):
        """Test environment template content and structure"""
        template = ConfigTemplates.get_environment_template()
        
        assert isinstance(template, str)
        assert len(template) > 0
        
        # Test header
        assert "Agent Workflow Environment Variables" in template
        assert "Copy this file to .env and customize as needed" in template
        
        # Test sections
        assert "# Discord Integration" in template
        assert "# Configuration Directory" in template
        assert "# Environment Settings" in template
        assert "# Claude AI Integration" in template
        assert "# Context Management" in template
        assert "# Performance Settings" in template
        assert "# Security Settings" in template
        
    def test_environment_template_variables(self):
        """Test specific environment variables in template"""
        template = ConfigTemplates.get_environment_template()
        
        # Test Discord variables
        assert "DISCORD_BOT_TOKEN=" in template
        
        # Test Configuration variables
        assert "AGENT_WORKFLOW_CONFIG_DIR=" in template
        
        # Test Environment variables with defaults
        assert "CONTEXT_ENV=development" in template
        assert "CONTEXT_LOG_LEVEL=INFO" in template
        assert "CONTEXT_DEBUG=false" in template
        
        # Test Claude AI variables
        assert "CLAUDE_MODEL=claude-3-opus-20240229" in template
        assert "CLAUDE_MAX_TOKENS=4096" in template
        assert "CLAUDE_INTEGRATION_ENABLED=true" in template
        
        # Test Context Management variables
        assert "CONTEXT_CACHE_ENABLED=true" in template
        assert "CONTEXT_CACHE_MAX_ENTRIES=1000" in template
        assert "CONTEXT_CACHE_MEMORY_MB=500" in template
        assert "CONTEXT_MONITORING_ENABLED=true" in template
        assert "CONTEXT_LEARNING_ENABLED=true" in template
        assert "CONTEXT_LEARNING_RATE=0.01" in template
        
        # Test Performance variables
        assert "CONTEXT_MAX_TOKENS=200000" in template
        assert "CONTEXT_MAX_CONCURRENT_REQUESTS=10" in template
        assert "CONTEXT_ENABLE_COMPRESSION=true" in template
        
        # Test Security variables
        assert "CONTEXT_ENABLE_SANDBOX=true" in template
        assert "CONTEXT_MAX_FILE_SIZE_MB=100" in template
        assert "CONTEXT_MAX_CONTEXT_SIZE_MB=50" in template
        
    def test_environment_template_format(self):
        """Test environment template format and structure"""
        template = ConfigTemplates.get_environment_template()
        lines = template.split('\n')
        
        # Should have comment sections
        comment_lines = [line for line in lines if line.startswith('#')]
        assert len(comment_lines) > 0
        
        # Should have variable assignments
        assignment_lines = [line for line in lines if '=' in line and not line.startswith('#')]
        assert len(assignment_lines) > 0
        
        # Each assignment should be valid
        for line in assignment_lines:
            if line.strip():
                assert '=' in line
                var_name, var_value = line.split('=', 1)
                assert var_name.strip()  # Variable name should not be empty


class TestConfigTemplatesSaveMethod:
    """Test ConfigTemplates save_template method"""
    
    def test_save_template_orch_dev_yaml(self):
        """Test saving development orchestration template as YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("orch-dev", temp_path, "yaml")
            
            assert result is True
            
            # Verify file was created and has correct content
            with open(temp_path, 'r') as f:
                content = yaml.safe_load(f)
                
            assert isinstance(content, dict)
            assert "global" in content
            assert "projects" in content
            assert content["global"]["global_cpu_cores"] == 2  # Development setting
        finally:
            Path(temp_path).unlink()
            
    def test_save_template_orch_prod_json(self):
        """Test saving production orchestration template as JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("orch-prod", temp_path, "json")
            
            assert result is True
            
            # Verify file was created and has correct content
            with open(temp_path, 'r') as f:
                content = json.load(f)
                
            assert isinstance(content, dict)
            assert "global" in content
            assert "projects" in content
            assert content["global"]["global_cpu_cores"] == 8  # Production setting
        finally:
            Path(temp_path).unlink()
            
    def test_save_template_dependency_yaml(self):
        """Test saving dependency template as YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("dependency", temp_path, "yaml")
            
            assert result is True
            
            # Verify file was created and has correct content
            with open(temp_path, 'r') as f:
                content = yaml.safe_load(f)
                
            assert isinstance(content, dict)
            assert "watcher" in content
            assert "updater" in content
            assert "claude_integration" in content
            assert "rules" in content
        finally:
            Path(temp_path).unlink()
            
    def test_save_template_context_json(self):
        """Test saving context template as JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("context", temp_path, "json")
            
            assert result is True
            
            # Verify file was created and has correct content
            with open(temp_path, 'r') as f:
                content = json.load(f)
                
            assert isinstance(content, dict)
            assert "cache" in content
            assert "monitoring" in content
            assert "learning" in content
            assert "security" in content
            assert "performance" in content
        finally:
            Path(temp_path).unlink()
            
    def test_save_template_env_format(self):
        """Test saving environment template (always text format)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("env", temp_path, "yaml")  # Format ignored for env
            
            assert result is True
            
            # Verify file was created and has correct content
            with open(temp_path, 'r') as f:
                content = f.read()
                
            assert isinstance(content, str)
            assert "Agent Workflow Environment Variables" in content
            assert "DISCORD_BOT_TOKEN=" in content
            assert "CLAUDE_MODEL=" in content
        finally:
            Path(temp_path).unlink()
            
    def test_save_template_unknown_template(self):
        """Test saving unknown template returns False"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("unknown", temp_path, "yaml")
            
            assert result is False
        finally:
            Path(temp_path).unlink()
            
    def test_save_template_unsupported_format(self):
        """Test saving template with unsupported format returns False"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("orch-dev", temp_path, "xml")
            
            assert result is False
        finally:
            Path(temp_path).unlink()
            
    def test_save_template_file_write_error(self):
        """Test saving template with file write error returns False"""
        # Try to write to an invalid path
        result = ConfigTemplates.save_template("orch-dev", "/invalid/path/config.yaml", "yaml")
        
        assert result is False
        
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_template_permission_error(self, mock_open):
        """Test saving template with permission error returns False"""
        result = ConfigTemplates.save_template("orch-dev", "test.yaml", "yaml")
        
        assert result is False
        
    @patch('yaml.dump', side_effect=Exception("YAML error"))
    def test_save_template_yaml_error(self, mock_yaml_dump):
        """Test saving template with YAML serialization error returns False"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("orch-dev", temp_path, "yaml")
            
            assert result is False
        finally:
            Path(temp_path).unlink()
            
    @patch('json.dump', side_effect=Exception("JSON error"))
    def test_save_template_json_error(self, mock_json_dump):
        """Test saving template with JSON serialization error returns False"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            
        try:
            result = ConfigTemplates.save_template("orch-dev", temp_path, "json")
            
            assert result is False
        finally:
            Path(temp_path).unlink()


class TestConfigTemplatesListMethod:
    """Test ConfigTemplates list_templates method"""
    
    def test_list_templates_content(self):
        """Test list_templates returns correct template information"""
        templates = ConfigTemplates.list_templates()
        
        assert isinstance(templates, dict)
        assert len(templates) == 5
        
        # Test all expected templates are present
        assert "orch-dev" in templates
        assert "orch-prod" in templates
        assert "dependency" in templates
        assert "context" in templates
        assert "env" in templates
        
    def test_list_templates_descriptions(self):
        """Test list_templates returns correct descriptions"""
        templates = ConfigTemplates.list_templates()
        
        # Test descriptions
        assert templates["orch-dev"] == "Development orchestration configuration"
        assert templates["orch-prod"] == "Production orchestration configuration"
        assert templates["dependency"] == "Dependency tracking configuration"
        assert templates["context"] == "Context management configuration"
        assert templates["env"] == "Environment variables template"
        
    def test_list_templates_immutable(self):
        """Test that modifying returned dict doesn't affect future calls"""
        templates1 = ConfigTemplates.list_templates()
        templates1["new_template"] = "Modified"
        
        templates2 = ConfigTemplates.list_templates()
        assert "new_template" not in templates2
        assert len(templates2) == 5


class TestConfigTemplatesInstantiation:
    """Test ConfigTemplates class instantiation and usage patterns"""
    
    def test_config_templates_as_static_class(self):
        """Test that ConfigTemplates works as a static utility class"""
        # Should be able to call methods without instantiation
        templates = ConfigTemplates.list_templates()
        assert isinstance(templates, dict)
        
        config = ConfigTemplates.get_development_orch_config()
        assert isinstance(config, dict)
        
    def test_config_templates_instantiation(self):
        """Test that ConfigTemplates can be instantiated if needed"""
        instance = ConfigTemplates()
        assert isinstance(instance, ConfigTemplates)
        
        # Instance methods should work the same as static methods
        templates = instance.list_templates()
        assert isinstance(templates, dict)
        assert len(templates) == 5
        
    def test_save_template_with_instance(self):
        """Test save_template method works with instance"""
        instance = ConfigTemplates()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
            
        try:
            result = instance.save_template("orch-dev", temp_path, "yaml")
            assert result is True
            
            # Verify content
            with open(temp_path, 'r') as f:
                content = yaml.safe_load(f)
            assert "global" in content
        finally:
            Path(temp_path).unlink()


class TestConfigTemplatesIntegration:
    """Integration tests for ConfigTemplates"""
    
    def test_all_templates_generate_and_validate(self):
        """Test that all templates can be generated and are valid"""
        template_names = ["orch-dev", "orch-prod", "dependency", "context", "env"]
        
        for template_name in template_names:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                temp_path = f.name
                
            try:
                # Determine appropriate format
                if template_name == "env":
                    format_type = "env"
                else:
                    format_type = "yaml"
                    
                # Generate template
                result = ConfigTemplates.save_template(template_name, temp_path, format_type)
                assert result is True, f"Failed to generate template: {template_name}"
                
                # Verify file exists and has content
                assert Path(temp_path).exists()
                assert Path(temp_path).stat().st_size > 0
                
                # Verify format-specific content
                if format_type == "yaml":
                    with open(temp_path, 'r') as f:
                        content = yaml.safe_load(f)
                    assert isinstance(content, dict)
                elif format_type == "env":
                    with open(temp_path, 'r') as f:
                        content = f.read()
                    assert isinstance(content, str)
                    assert len(content) > 0
                    
            finally:
                Path(temp_path).unlink()
                
    def test_template_consistency(self):
        """Test that templates are consistent across different calls"""
        # Get the same template multiple times
        config1 = ConfigTemplates.get_development_orch_config()
        config2 = ConfigTemplates.get_development_orch_config()
        
        assert config1 == config2
        
        # Test with production config
        prod_config1 = ConfigTemplates.get_production_orch_config()
        prod_config2 = ConfigTemplates.get_production_orch_config()
        
        assert prod_config1 == prod_config2
        
    def test_template_format_independence(self):
        """Test that the same template produces consistent data regardless of output format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_path = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name
            
        try:
            # Save same template in different formats
            yaml_result = ConfigTemplates.save_template("orch-dev", yaml_path, "yaml")
            json_result = ConfigTemplates.save_template("orch-dev", json_path, "json")
            
            assert yaml_result is True
            assert json_result is True
            
            # Load both files and compare content
            with open(yaml_path, 'r') as f:
                yaml_content = yaml.safe_load(f)
                
            with open(json_path, 'r') as f:
                json_content = json.load(f)
                
            assert yaml_content == json_content
            
        finally:
            Path(yaml_path).unlink()
            Path(json_path).unlink()


class TestConfigTemplatesEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_save_template_empty_filename(self):
        """Test saving template with empty filename"""
        result = ConfigTemplates.save_template("orch-dev", "", "yaml")
        assert result is False
        
    def test_save_template_none_filename(self):
        """Test saving template with None filename"""
        result = ConfigTemplates.save_template("orch-dev", None, "yaml")
        assert result is False
        
    def test_get_template_data_completeness(self):
        """Test that all template data structures are complete"""
        # Test development orchestration config completeness
        dev_config = ConfigTemplates.get_development_orch_config()
        global_section = dev_config["global"]
        
        # Should have all required global settings
        required_global_keys = [
            "alert_channels", "backup_retention_days", "enable_audit_logging",
            "enable_cloud_backup", "enable_cross_project_insights", "enable_knowledge_sharing",
            "enable_pattern_learning", "enable_project_isolation", "global_cpu_cores",
            "global_discord_guild", "global_disk_limit_gb", "global_memory_limit_gb",
            "global_state_path", "health_check_interval_seconds", "max_concurrent_projects",
            "max_total_agents", "monitoring_webhook_url", "resource_allocation_strategy",
            "resource_rebalance_interval_seconds", "scheduling_interval_seconds",
            "secret_management_provider"
        ]
        
        for key in required_global_keys:
            assert key in global_section, f"Missing key in global section: {key}"
            
    def test_template_type_consistency(self):
        """Test that template values have consistent types"""
        dev_config = ConfigTemplates.get_development_orch_config()
        prod_config = ConfigTemplates.get_production_orch_config()
        
        # Compare types of corresponding values
        for key in dev_config["global"]:
            if key in prod_config["global"]:
                dev_type = type(dev_config["global"][key])
                prod_type = type(prod_config["global"][key])
                assert dev_type == prod_type, f"Type mismatch for key {key}: {dev_type} vs {prod_type}"


if __name__ == '__main__':
    pytest.main([__file__])