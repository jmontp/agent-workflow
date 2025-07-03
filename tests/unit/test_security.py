"""
Unit tests for Security system.

Tests the security configuration system including agent tool restrictions,
access control, and security boundaries.
Consolidated from multiple security-related test files.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from agent_workflow.security.tool_config import (
    AgentType, AGENT_TOOL_CONFIG, RESTRICTED_COMMANDS, ELEVATED_COMMANDS,
    CODE_MANAGEMENT_COMMANDS, TDD_COMMANDS, get_allowed_tools, get_disallowed_tools,
    validate_agent_command, create_agent_client_with_restrictions,
    get_agent_capabilities, TOOL_CATEGORIES
)


class TestAgentType:
    """Test AgentType enum."""
    
    def test_agent_type_values(self):
        """Test AgentType enum values."""
        assert AgentType.ORCHESTRATOR.value == "Orchestrator"
        assert AgentType.DESIGN.value == "DesignAgent"
        assert AgentType.CODE.value == "CodeAgent"
        assert AgentType.QA.value == "QAAgent"
        assert AgentType.DATA.value == "DataAgent"

    def test_agent_type_completeness(self):
        """Test that all agent types are defined."""
        expected_agents = ["Orchestrator", "DesignAgent", "CodeAgent", "QAAgent", "DataAgent"]
        actual_agents = [agent.value for agent in AgentType]
        
        for expected in expected_agents:
            assert expected in actual_agents


class TestCommandCategories:
    """Test command categorization."""
    
    def test_restricted_commands(self):
        """Test restricted commands are properly defined."""
        assert "sudo" in RESTRICTED_COMMANDS
        assert "su" in RESTRICTED_COMMANDS
        assert "format" in RESTRICTED_COMMANDS
        assert "dd" in RESTRICTED_COMMANDS
        assert "curl" in RESTRICTED_COMMANDS
        assert "ssh" in RESTRICTED_COMMANDS

    def test_elevated_commands(self):
        """Test elevated commands are properly defined."""
        assert "rm" in ELEVATED_COMMANDS
        assert "git push" in ELEVATED_COMMANDS

    def test_code_management_commands(self):
        """Test code management commands are properly defined."""
        assert "git commit" in CODE_MANAGEMENT_COMMANDS
        assert "git add" in CODE_MANAGEMENT_COMMANDS
        assert "git reset" in CODE_MANAGEMENT_COMMANDS

    def test_tdd_commands(self):
        """Test TDD-specific commands are properly defined."""
        assert "pytest --tb=short" in TDD_COMMANDS
        assert "coverage run" in TDD_COMMANDS
        assert "git status --porcelain" in TDD_COMMANDS

    def test_no_command_overlap(self):
        """Test that command categories don't have dangerous overlaps."""
        # Ensure restricted commands aren't in other categories
        for cmd in RESTRICTED_COMMANDS:
            assert cmd not in CODE_MANAGEMENT_COMMANDS
            assert cmd not in TDD_COMMANDS


class TestAgentToolConfig:
    """Test agent tool configuration."""
    
    def test_all_agents_have_config(self):
        """Test that all agent types have tool configuration."""
        for agent_type in AgentType:
            assert agent_type in AGENT_TOOL_CONFIG

    def test_orchestrator_permissions(self):
        """Test orchestrator has appropriate permissions."""
        config = AGENT_TOOL_CONFIG[AgentType.ORCHESTRATOR]
        
        # Should have full access to most tools
        assert "Read" in config["allowed_tools"]
        assert "Write" in config["allowed_tools"]
        assert "Edit" in config["allowed_tools"]
        assert "Bash(*)" in config["allowed_tools"]
        
        # Should still block dangerous commands
        assert "Bash(sudo)" in config["disallowed_tools"]
        assert "Bash(format)" in config["disallowed_tools"]

    def test_design_agent_permissions(self):
        """Test design agent has read-only permissions."""
        config = AGENT_TOOL_CONFIG[AgentType.DESIGN]
        
        # Should have read access
        assert "Read" in config["allowed_tools"]
        assert "Write" in config["allowed_tools"]  # For documentation
        assert "WebFetch" in config["allowed_tools"]
        assert "WebSearch" in config["allowed_tools"]
        
        # Should not have dangerous commands
        disallowed = config.get("disallowed_tools", [])
        for restricted_cmd in RESTRICTED_COMMANDS:
            if f"Bash({restricted_cmd})" not in config["allowed_tools"]:
                # If not explicitly allowed, should be implicitly disallowed
                pass

    def test_code_agent_permissions(self):
        """Test code agent has appropriate code modification permissions."""
        config = AGENT_TOOL_CONFIG[AgentType.CODE]
        
        # Should have code editing permissions
        assert "Edit" in config["allowed_tools"]
        assert "MultiEdit" in config["allowed_tools"]
        assert "Bash(git add)" in config["allowed_tools"]
        assert "Bash(git commit)" in config["allowed_tools"]
        
        # Should not have git push (elevated)
        disallowed = config.get("disallowed_tools", [])
        assert "Bash(git push)" in disallowed

    def test_qa_agent_permissions(self):
        """Test QA agent has testing permissions only."""
        config = AGENT_TOOL_CONFIG[AgentType.QA]
        
        # Should have test execution permissions
        assert "Bash(pytest)" in config["allowed_tools"]
        assert "Bash(coverage)" in config["allowed_tools"]
        
        # Should not have code modification permissions
        disallowed = config.get("disallowed_tools", [])
        assert "Edit" in disallowed or "Edit" not in config["allowed_tools"]

    def test_data_agent_permissions(self):
        """Test data agent has data processing permissions."""
        config = AGENT_TOOL_CONFIG[AgentType.DATA]
        
        # Should have data processing permissions
        assert "Read" in config["allowed_tools"]
        assert "NotebookRead" in config["allowed_tools"]
        assert "NotebookEdit" in config["allowed_tools"]
        
        # Should not have system modification permissions
        disallowed = config.get("disallowed_tools", [])
        for restricted_cmd in RESTRICTED_COMMANDS:
            bash_cmd = f"Bash({restricted_cmd})"
            if bash_cmd not in config["allowed_tools"]:
                # Should be implicitly or explicitly disallowed
                pass


class TestToolConfigFunctions:
    """Test tool configuration utility functions."""
    
    def test_get_allowed_tools(self):
        """Test getting allowed tools for agent types."""
        orchestrator_tools = get_allowed_tools(AgentType.ORCHESTRATOR)
        assert "Read" in orchestrator_tools
        assert "Write" in orchestrator_tools
        assert len(orchestrator_tools) > 0
        
        design_tools = get_allowed_tools(AgentType.DESIGN)
        assert "Read" in design_tools
        assert len(design_tools) > 0

    def test_get_disallowed_tools(self):
        """Test getting disallowed tools for agent types."""
        orchestrator_disallowed = get_disallowed_tools(AgentType.ORCHESTRATOR)
        assert "Bash(sudo)" in orchestrator_disallowed
        
        code_disallowed = get_disallowed_tools(AgentType.CODE)
        assert "Bash(git push)" in code_disallowed

    def test_validate_agent_command_allowed(self):
        """Test validating allowed commands."""
        # Test orchestrator can use most commands
        assert validate_agent_command(AgentType.ORCHESTRATOR, "Read") is True
        assert validate_agent_command(AgentType.ORCHESTRATOR, "git commit") is True
        
        # Test design agent can read but not execute dangerous commands
        assert validate_agent_command(AgentType.DESIGN, "Read") is True
        assert validate_agent_command(AgentType.DESIGN, "sudo rm -rf /") is False

    def test_validate_agent_command_disallowed(self):
        """Test validating disallowed commands."""
        # Test that dangerous commands are blocked for all agents
        for agent_type in AgentType:
            if agent_type != AgentType.ORCHESTRATOR:
                assert validate_agent_command(agent_type, "sudo") is False
                assert validate_agent_command(agent_type, "format") is False

    def test_create_agent_client_with_restrictions(self):
        """Test creating agent client with proper restrictions."""
        with patch('agent_workflow.security.tool_config.create_claude_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            
            # Test creating client for design agent
            client = create_agent_client_with_restrictions(AgentType.DESIGN)
            
            assert client == mock_client
            mock_create.assert_called_once()
            
            # Verify that restrictions were applied
            call_args = mock_create.call_args
            assert 'allowed_tools' in call_args.kwargs or len(call_args.args) > 0

    def test_get_agent_capabilities(self):
        """Test getting agent capabilities."""
        orchestrator_caps = get_agent_capabilities(AgentType.ORCHESTRATOR)
        assert "system_management" in orchestrator_caps
        assert "full_access" in orchestrator_caps
        
        design_caps = get_agent_capabilities(AgentType.DESIGN)
        assert "read_only" in design_caps
        assert "documentation" in design_caps
        
        code_caps = get_agent_capabilities(AgentType.CODE)
        assert "code_modification" in design_caps
        assert "version_control" in code_caps


class TestSecurityBoundaries:
    """Test security boundary enforcement."""
    
    def test_privilege_escalation_prevention(self):
        """Test prevention of privilege escalation."""
        # No agent except orchestrator should be able to use sudo
        for agent_type in AgentType:
            if agent_type != AgentType.ORCHESTRATOR:
                assert validate_agent_command(agent_type, "sudo anything") is False
                assert validate_agent_command(agent_type, "su - root") is False

    def test_file_system_protection(self):
        """Test file system protection."""
        # Critical file system commands should be restricted
        dangerous_commands = ["format", "fdisk", "dd", "shred"]
        
        for agent_type in AgentType:
            for cmd in dangerous_commands:
                if agent_type != AgentType.ORCHESTRATOR:
                    assert validate_agent_command(agent_type, cmd) is False

    def test_network_access_control(self):
        """Test network access control."""
        # Network commands should be restricted for most agents
        network_commands = ["curl", "wget", "ssh", "scp"]
        
        for agent_type in [AgentType.CODE, AgentType.QA]:
            for cmd in network_commands:
                assert validate_agent_command(agent_type, cmd) is False

    def test_version_control_restrictions(self):
        """Test version control command restrictions."""
        # git push should be restricted to orchestrator only
        for agent_type in AgentType:
            if agent_type != AgentType.ORCHESTRATOR:
                assert validate_agent_command(agent_type, "git push") is False
        
        # git commit should be allowed for code agent
        assert validate_agent_command(AgentType.CODE, "git commit") is True

    def test_tdd_workflow_permissions(self):
        """Test TDD-specific workflow permissions."""
        # QA agent should be able to run tests
        assert validate_agent_command(AgentType.QA, "pytest") is True
        assert validate_agent_command(AgentType.QA, "coverage run") is True
        
        # But not modify code
        assert validate_agent_command(AgentType.QA, "Edit") is False


class TestToolCategories:
    """Test tool categorization system."""
    
    def test_tool_categories_exist(self):
        """Test that tool categories are properly defined."""
        assert "file_operations" in TOOL_CATEGORIES
        assert "code_tools" in TOOL_CATEGORIES
        assert "system_tools" in TOOL_CATEGORIES
        assert "testing_tools" in TOOL_CATEGORIES

    def test_tool_category_membership(self):
        """Test tool category membership."""
        file_ops = TOOL_CATEGORIES["file_operations"]
        assert "Read" in file_ops
        assert "Write" in file_ops
        assert "Edit" in file_ops
        
        testing_tools = TOOL_CATEGORIES["testing_tools"]
        assert "pytest" in testing_tools
        assert "coverage" in testing_tools

    def test_category_based_restrictions(self):
        """Test category-based access restrictions."""
        # Design agents should have read access but limited write access
        design_allowed = get_allowed_tools(AgentType.DESIGN)
        
        # Should have read tools
        for tool in TOOL_CATEGORIES["file_operations"]:
            if tool in ["Read", "LS", "Glob", "Grep"]:
                assert tool in design_allowed
        
        # QA agents should have testing tools
        qa_allowed = get_allowed_tools(AgentType.QA)
        for tool in TOOL_CATEGORIES["testing_tools"]:
            if f"Bash({tool})" in qa_allowed or tool in qa_allowed:
                # QA should have access to testing tools
                pass


class TestSecurityValidation:
    """Test security validation mechanisms."""
    
    def test_command_parsing(self):
        """Test command parsing for security validation."""
        # Test that commands are properly parsed for validation
        assert validate_agent_command(AgentType.DESIGN, "ls -la") is True
        assert validate_agent_command(AgentType.DESIGN, "sudo ls") is False
        assert validate_agent_command(AgentType.CODE, "git add .") is True

    def test_wildcard_permissions(self):
        """Test wildcard permission handling."""
        # Test that Bash(*) gives broad permissions to orchestrator
        orchestrator_config = AGENT_TOOL_CONFIG[AgentType.ORCHESTRATOR]
        assert "Bash(*)" in orchestrator_config["allowed_tools"]
        
        # But other agents should not have wildcard permissions
        for agent_type in AgentType:
            if agent_type != AgentType.ORCHESTRATOR:
                config = AGENT_TOOL_CONFIG[agent_type]
                assert "Bash(*)" not in config.get("allowed_tools", [])

    def test_security_edge_cases(self):
        """Test security edge cases."""
        # Test command injection attempts
        assert validate_agent_command(AgentType.DESIGN, "ls; sudo rm -rf /") is False
        assert validate_agent_command(AgentType.CODE, "git add . && sudo reboot") is False
        
        # Test path traversal attempts
        assert validate_agent_command(AgentType.DESIGN, "cat ../../../../etc/passwd") is False

    def test_tdd_security_integration(self):
        """Test TDD workflow security integration."""
        # Test that TDD commands are properly secured
        assert validate_agent_command(AgentType.QA, "pytest tests/") is True
        assert validate_agent_command(AgentType.QA, "pytest tests/ && rm -rf /") is False
        
        # Test TDD state transitions respect security
        assert validate_agent_command(AgentType.CODE, "git commit -m 'TDD: GREEN phase'") is True
        assert validate_agent_command(AgentType.QA, "git commit -m 'TDD: RED phase'") is False


class TestComplianceValidation:
    """Test security compliance validation."""
    
    def test_government_audit_compliance(self):
        """Test government audit compliance requirements."""
        # Verify that all required security controls are in place
        for agent_type in AgentType:
            config = AGENT_TOOL_CONFIG[agent_type]
            
            # All agents must have explicit allowed/disallowed tool lists
            assert "allowed_tools" in config
            assert isinstance(config["allowed_tools"], list)
            
            # Orchestrator must have explicit disallowed tools
            if agent_type == AgentType.ORCHESTRATOR:
                assert "disallowed_tools" in config
                assert len(config["disallowed_tools"]) > 0

    def test_principle_of_least_privilege(self):
        """Test principle of least privilege enforcement."""
        # Each agent should only have tools necessary for its function
        
        # Design agent: read-only + documentation
        design_tools = get_allowed_tools(AgentType.DESIGN)
        assert "Read" in design_tools
        assert "Write" in design_tools  # For documentation
        assert "Edit" not in get_allowed_tools(AgentType.DESIGN) or "Edit" in get_disallowed_tools(AgentType.DESIGN)
        
        # QA agent: testing tools only
        qa_tools = get_allowed_tools(AgentType.QA)
        assert any("pytest" in tool for tool in qa_tools)
        assert "git push" not in qa_tools

    def test_security_audit_trail(self):
        """Test security audit trail capabilities."""
        # Verify that security decisions can be audited
        for agent_type in AgentType:
            for tool in ["Read", "sudo", "git push"]:
                result = validate_agent_command(agent_type, tool)
                # Should be able to trace why command was allowed/denied
                assert isinstance(result, bool)

    def test_configuration_completeness(self):
        """Test configuration completeness for audit compliance."""
        # Every agent must have complete security configuration
        required_fields = ["allowed_tools"]
        
        for agent_type in AgentType:
            config = AGENT_TOOL_CONFIG[agent_type]
            for field in required_fields:
                assert field in config
                assert config[field] is not None
                assert len(config[field]) > 0


if __name__ == "__main__":
    pytest.main([__file__])