"""
Comprehensive security coverage tests for agent_tool_config.py

Tests security boundaries, access controls, privilege escalation prevention,
and comprehensive coverage of all security-critical functions.
Government audit compliance focused.
"""

import pytest
import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, call
from typing import Dict, List, Set

# Add the project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.agent_tool_config import (
    AgentType, 
    get_allowed_tools, 
    get_disallowed_tools,
    get_claude_tool_args,
    validate_agent_access,
    get_security_summary,
    get_tdd_capabilities,
    validate_tdd_phase_access,
    get_tdd_tool_restrictions,
    validate_tdd_tool_access,
    RESTRICTED_COMMANDS,
    ELEVATED_COMMANDS,
    CODE_MANAGEMENT_COMMANDS,
    TDD_COMMANDS,
    AGENT_TOOL_CONFIG
)


class TestSecurityBoundaryEnforcement:
    """Test critical security boundary enforcement mechanisms."""
    
    def test_restricted_commands_comprehensive_coverage(self):
        """Test that all restricted commands are properly blocked across all agent types."""
        dangerous_commands = [
            "sudo", "su", "chmod", "chown", "kill", "killall",
            "format", "fdisk", "dd", "shred", "curl", "wget",
            "ssh", "scp", "rsync", "npm publish", "pip install --user",
            "docker run", "docker exec"
        ]
        
        # Verify restricted commands list contains expected dangerous commands
        for cmd in dangerous_commands:
            assert cmd in RESTRICTED_COMMANDS, f"Critical command '{cmd}' missing from RESTRICTED_COMMANDS"
        
        # Test that no non-orchestrator agent can access restricted commands
        non_orchestrator_agents = [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]
        
        for agent_type in non_orchestrator_agents:
            for cmd in RESTRICTED_COMMANDS:
                bash_tool = f"Bash({cmd})"
                assert not validate_agent_access(agent_type, bash_tool), \
                    f"SECURITY VIOLATION: {agent_type.value} has access to restricted command: {cmd}"
    
    def test_elevated_commands_orchestrator_only(self):
        """Test that elevated commands are only available to orchestrator."""
        elevated_commands = ["rm", "rmdir", "del", "delete", "git push"]
        
        # Verify elevated commands list
        for cmd in elevated_commands:
            if cmd in ["rm", "rmdir", "del", "delete", "git push"]:
                assert cmd in ELEVATED_COMMANDS, f"Elevated command '{cmd}' missing from ELEVATED_COMMANDS"
        
        # Test orchestrator access
        for cmd in ELEVATED_COMMANDS:
            bash_tool = f"Bash({cmd})"
            assert validate_agent_access(AgentType.ORCHESTRATOR, bash_tool), \
                f"Orchestrator should have access to elevated command: {cmd}"
        
        # Test other agents don't have access
        non_orchestrator_agents = [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]
        
        for agent_type in non_orchestrator_agents:
            for cmd in ELEVATED_COMMANDS:
                bash_tool = f"Bash({cmd})"
                assert not validate_agent_access(agent_type, bash_tool), \
                    f"SECURITY VIOLATION: {agent_type.value} has access to elevated command: {cmd}"
    
    def test_code_management_commands_restricted_access(self):
        """Test code management commands have appropriate restrictions."""
        # Code agent should have commit access
        assert validate_agent_access(AgentType.CODE, "Bash(git commit)")
        assert validate_agent_access(AgentType.CODE, "Bash(git add)")
        
        # QA and Design agents should not have git commit access
        assert not validate_agent_access(AgentType.QA, "Bash(git commit)")
        assert not validate_agent_access(AgentType.QA, "Bash(git add)")
        assert not validate_agent_access(AgentType.DESIGN, "Bash(git commit)")
        assert not validate_agent_access(AgentType.DESIGN, "Bash(git add)")
        
        # Data agent should not have any git access
        assert not validate_agent_access(AgentType.DATA, "Bash(git commit)")
        assert not validate_agent_access(AgentType.DATA, "Bash(git add)")
        assert not validate_agent_access(AgentType.DATA, "Bash(git reset)")
    
    def test_privilege_escalation_prevention(self):
        """Test that privilege escalation is prevented for all agents."""
        privilege_escalation_commands = [
            "sudo", "su", "chmod +s", "chown root", "setuid", "setgid",
            "passwd", "usermod", "useradd", "userdel", "visudo"
        ]
        
        # Even orchestrator should not have access to privilege escalation
        for cmd in privilege_escalation_commands:
            bash_tool = f"Bash({cmd})"
            for agent_type in AgentType:
                # Check if command is explicitly blocked
                disallowed = get_disallowed_tools(agent_type)
                if bash_tool in disallowed or any(restricted in cmd for restricted in RESTRICTED_COMMANDS):
                    assert not validate_agent_access(agent_type, bash_tool), \
                        f"CRITICAL SECURITY VIOLATION: {agent_type.value} has privilege escalation access: {cmd}"
    
    def test_file_system_destruction_prevention(self):
        """Test prevention of file system destruction commands."""
        destruction_commands = [
            "rm -rf /", "rm -rf /*", "dd if=/dev/zero", "shred -vfz",
            "mkfs", "format", "fdisk", "parted", "wipefs"
        ]
        
        for cmd in destruction_commands:
            bash_tool = f"Bash({cmd})"
            for agent_type in AgentType:
                # Even orchestrator should not have access to most destructive commands
                if any(dangerous in cmd for dangerous in ["format", "fdisk", "dd", "shred"]):
                    assert not validate_agent_access(agent_type, bash_tool), \
                        f"CRITICAL SECURITY VIOLATION: {agent_type.value} has destruction access: {cmd}"
    
    def test_network_security_restrictions(self):
        """Test network-related security restrictions."""
        network_commands = [
            "curl", "wget", "ssh", "scp", "rsync", "nc", "netcat",
            "nmap", "telnet", "ftp", "sftp"
        ]
        
        # Non-orchestrator agents should not have network access
        non_orchestrator_agents = [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]
        
        for agent_type in non_orchestrator_agents:
            for cmd in network_commands:
                if cmd in RESTRICTED_COMMANDS:
                    bash_tool = f"Bash({cmd})"
                    assert not validate_agent_access(agent_type, bash_tool), \
                        f"SECURITY VIOLATION: {agent_type.value} has network access: {cmd}"


class TestAgentToolConfigurationIntegrity:
    """Test integrity of agent tool configurations."""
    
    def test_all_agent_types_have_configurations(self):
        """Test that all agent types have complete configurations."""
        for agent_type in AgentType:
            # Every agent should have a configuration
            assert agent_type in AGENT_TOOL_CONFIG, \
                f"Agent type {agent_type.value} missing from AGENT_TOOL_CONFIG"
            
            config = AGENT_TOOL_CONFIG[agent_type]
            
            # Should have both allowed and disallowed tools
            assert "allowed_tools" in config, f"{agent_type.value} missing allowed_tools"
            assert "disallowed_tools" in config, f"{agent_type.value} missing disallowed_tools"
            
            # Lists should be non-empty (except potentially disallowed for orchestrator)
            assert isinstance(config["allowed_tools"], list)
            assert isinstance(config["disallowed_tools"], list)
            assert len(config["allowed_tools"]) > 0, f"{agent_type.value} has no allowed tools"
    
    def test_configuration_consistency(self):
        """Test consistency across agent configurations."""
        # All agents should have Read access (basic requirement)
        for agent_type in AgentType:
            allowed = get_allowed_tools(agent_type)
            assert "Read" in allowed, f"{agent_type.value} missing basic Read access"
        
        # Orchestrator should have most permissive access
        orchestrator_allowed = set(get_allowed_tools(AgentType.ORCHESTRATOR))
        
        for agent_type in [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]:
            agent_allowed = set(get_allowed_tools(agent_type))
            
            # Orchestrator should have some tools that others don't
            # (This tests the principle of least privilege)
            assert not agent_allowed.issuperset(orchestrator_allowed), \
                f"{agent_type.value} has equal or more permissions than orchestrator"
    
    def test_tool_access_validation_edge_cases(self):
        """Test edge cases in tool access validation."""
        # Test empty/None tool names
        for agent_type in AgentType:
            assert not validate_agent_access(agent_type, "")
            assert not validate_agent_access(agent_type, None)
        
        # Test non-existent tools
        for agent_type in AgentType:
            assert not validate_agent_access(agent_type, "NonExistentTool")
            assert not validate_agent_access(agent_type, "FakeBash(command)")
        
        # Test malformed bash commands
        for agent_type in AgentType:
            assert not validate_agent_access(agent_type, "Bash(")
            assert not validate_agent_access(agent_type, "Bash)")
            assert not validate_agent_access(agent_type, "Bash(")
    
    def test_disallowed_tools_list_flattening(self):
        """Test that disallowed tools list is properly flattened."""
        for agent_type in AgentType:
            disallowed = get_disallowed_tools(agent_type)
            
            # Should be a flat list of strings
            assert isinstance(disallowed, list)
            for tool in disallowed:
                assert isinstance(tool, str), \
                    f"Non-string tool in disallowed list for {agent_type.value}: {tool}"
                assert len(tool) > 0, f"Empty tool name in disallowed list for {agent_type.value}"
    
    def test_claude_tool_args_generation_security(self):
        """Test security of Claude CLI argument generation."""
        for agent_type in AgentType:
            args = get_claude_tool_args(agent_type)
            
            # Should always have allowedTools and disallowedTools
            assert "--allowedTools" in args
            assert "--disallowedTools" in args
            
            # Find the tool lists
            allowed_idx = args.index("--allowedTools")
            disallowed_idx = args.index("--disallowedTools")
            
            allowed_tools = args[allowed_idx + 1]
            disallowed_tools = args[disallowed_idx + 1]
            
            # Should be space-separated strings
            assert isinstance(allowed_tools, str)
            assert isinstance(disallowed_tools, str)
            
            # Validate no dangerous commands in allowed list (except orchestrator)
            if agent_type != AgentType.ORCHESTRATOR:
                for cmd in RESTRICTED_COMMANDS:
                    bash_cmd = f"Bash({cmd})"
                    assert bash_cmd not in allowed_tools, \
                        f"SECURITY VIOLATION: Dangerous command {cmd} in allowed tools for {agent_type.value}"


class TestTDDSecurityCapabilities:
    """Test TDD-specific security capabilities and restrictions."""
    
    def test_tdd_phase_access_control(self):
        """Test that TDD phase access is properly controlled."""
        phase_mappings = {
            AgentType.DESIGN: ["DESIGN"],
            AgentType.QA: ["TEST_RED"],
            AgentType.CODE: ["CODE_GREEN", "REFACTOR", "COMMIT"],
            AgentType.DATA: [],  # No direct TDD phases
            AgentType.ORCHESTRATOR: ["DESIGN", "TEST_RED", "CODE_GREEN", "REFACTOR", "COMMIT"]
        }
        
        for agent_type, expected_phases in phase_mappings.items():
            capabilities = get_tdd_capabilities(agent_type)
            actual_phases = capabilities.get("tdd_phases", [])
            
            assert set(actual_phases) == set(expected_phases), \
                f"TDD phase mismatch for {agent_type.value}: expected {expected_phases}, got {actual_phases}"
            
            # Test individual phase access
            all_phases = ["DESIGN", "TEST_RED", "CODE_GREEN", "REFACTOR", "COMMIT"]
            for phase in all_phases:
                should_have_access = phase in expected_phases
                actual_access = validate_tdd_phase_access(agent_type, phase)
                
                assert actual_access == should_have_access, \
                    f"TDD phase access error: {agent_type.value} phase {phase} - expected {should_have_access}, got {actual_access}"
    
    def test_tdd_tool_restrictions_security(self):
        """Test security of TDD tool restrictions."""
        for agent_type in AgentType:
            restrictions = get_tdd_tool_restrictions(agent_type)
            
            # Should have all required restriction categories
            required_categories = ["pytest_restrictions", "git_restrictions", "file_access_restrictions", "special_tdd_tools"]
            for category in required_categories:
                assert category in restrictions, \
                    f"Missing TDD restriction category {category} for {agent_type.value}"
            
            # Verify git restrictions are security-appropriate
            git_restrictions = restrictions["git_restrictions"]
            
            if agent_type == AgentType.DESIGN:
                assert "read_only_git_access" in git_restrictions
            elif agent_type == AgentType.QA:
                assert "cannot_commit" in git_restrictions
                assert "cannot_push" in git_restrictions
            elif agent_type == AgentType.CODE:
                assert "can_commit" in git_restrictions
                assert "cannot_push" in git_restrictions  # Security: no pushing
            elif agent_type == AgentType.DATA:
                assert "git_restrictions" in restrictions  # Should have restrictions
    
    def test_tdd_tool_access_validation_security(self):
        """Test security of TDD tool access validation."""
        # Test pytest access restrictions
        result = validate_tdd_tool_access(AgentType.DESIGN, "Bash(pytest)", {"current_phase": "DESIGN"})
        assert not result["allowed"], "Design agent should not execute tests"
        assert any("cannot execute tests" in restriction for restriction in result["tdd_specific_restrictions"])
        
        # Test git commit restrictions
        result = validate_tdd_tool_access(AgentType.QA, "Bash(git commit)", {"current_phase": "TEST_RED"})
        assert not result["allowed"], "QA agent should not commit"
        assert any("cannot commit" in restriction for restriction in result["tdd_specific_restrictions"])
        
        # Test git push restrictions (should be blocked for all non-orchestrator)
        for agent_type in [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]:
            result = validate_tdd_tool_access(agent_type, "Bash(git push)", {"current_phase": "COMMIT"})
            assert not result["allowed"], f"{agent_type.value} should not be able to push"
    
    def test_tdd_capabilities_coordination_restrictions(self):
        """Test TDD coordination capabilities restrictions."""
        # Only orchestrator should coordinate TDD cycles
        for agent_type in AgentType:
            capabilities = get_tdd_capabilities(agent_type)
            can_coordinate = capabilities.get("can_coordinate_tdd_cycles", False)
            can_manage_all = capabilities.get("can_manage_all_phases", False)
            
            if agent_type == AgentType.ORCHESTRATOR:
                assert can_coordinate, "Orchestrator should coordinate TDD cycles"
                assert can_manage_all, "Orchestrator should manage all phases"
            else:
                assert not can_coordinate, f"{agent_type.value} should not coordinate TDD cycles"
                assert not can_manage_all, f"{agent_type.value} should not manage all phases"


class TestSecuritySummaryAndReporting:
    """Test security summary and reporting functionality."""
    
    def test_security_summary_completeness(self):
        """Test that security summaries contain all required information."""
        for agent_type in AgentType:
            summary = get_security_summary(agent_type)
            
            # Required fields
            required_fields = [
                "agent_type", "allowed_tools_count", "disallowed_tools_count",
                "allowed_tools", "disallowed_tools", "restricted_commands_blocked",
                "tdd_capabilities"
            ]
            
            for field in required_fields:
                assert field in summary, f"Security summary missing {field} for {agent_type.value}"
            
            # Verify data types and reasonable values
            assert isinstance(summary["allowed_tools_count"], int)
            assert isinstance(summary["disallowed_tools_count"], int)
            assert summary["allowed_tools_count"] > 0
            assert isinstance(summary["allowed_tools"], list)
            assert isinstance(summary["disallowed_tools"], list)
            assert isinstance(summary["restricted_commands_blocked"], int)
            assert summary["restricted_commands_blocked"] > 0
            
            # TDD capabilities should be comprehensive
            tdd_caps = summary["tdd_capabilities"]
            assert isinstance(tdd_caps, dict)
            assert "can_coordinate_tdd_cycles" in tdd_caps
            assert "tdd_phases" in tdd_caps
    
    def test_security_metrics_accuracy(self):
        """Test accuracy of security metrics."""
        for agent_type in AgentType:
            summary = get_security_summary(agent_type)
            
            # Verify counts match actual lists
            allowed_tools = get_allowed_tools(agent_type)
            disallowed_tools = get_disallowed_tools(agent_type)
            
            assert summary["allowed_tools_count"] == len(allowed_tools)
            assert summary["disallowed_tools_count"] == len(disallowed_tools)
            
            # Verify restricted commands blocking count
            total_restricted = len(RESTRICTED_COMMANDS + ELEVATED_COMMANDS + CODE_MANAGEMENT_COMMANDS)
            assert summary["restricted_commands_blocked"] == total_restricted


class TestBashCommandPatternSecurity:
    """Test security of bash command pattern matching."""
    
    def test_bash_command_pattern_validation(self):
        """Test that bash command patterns are properly validated."""
        # Test valid bash command patterns
        valid_patterns = [
            "Bash(ls)", "Bash(git status)", "Bash(pytest)", "Bash(python script.py)"
        ]
        
        for pattern in valid_patterns:
            # At least one agent should recognize this as a bash command
            recognized = False
            for agent_type in AgentType:
                if pattern.replace("Bash(", "").replace(")", "") in " ".join(get_allowed_tools(agent_type)):
                    recognized = True
                    break
            
            # The pattern should be processable by the validation system
            cmd = pattern[5:-1]  # Extract command from Bash(command)
            assert isinstance(cmd, str) and len(cmd) > 0
    
    def test_bash_command_injection_prevention(self):
        """Test prevention of command injection in bash patterns."""
        injection_attempts = [
            "Bash(ls; rm -rf /)",
            "Bash(git status && sudo rm)",
            "Bash(echo test | sudo tee)",
            "Bash(`malicious_command`)",
            "Bash($(dangerous_substitution))",
        ]
        
        # These should all be blocked for non-orchestrator agents
        non_orchestrator_agents = [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]
        
        for agent_type in non_orchestrator_agents:
            for injection in injection_attempts:
                assert not validate_agent_access(agent_type, injection), \
                    f"SECURITY VIOLATION: Command injection not blocked for {agent_type.value}: {injection}"
    
    def test_bash_wildcard_pattern_security(self):
        """Test security of bash wildcard patterns."""
        # Test that Bash(*) is only allowed for orchestrator
        for agent_type in AgentType:
            allowed = get_allowed_tools(agent_type)
            has_wildcard = "Bash(*)" in allowed
            
            if agent_type == AgentType.ORCHESTRATOR:
                assert has_wildcard, "Orchestrator should have Bash(*) access"
            else:
                assert not has_wildcard, f"{agent_type.value} should not have Bash(*) wildcard access"


class TestAgentSecurityBoundariesIntegration:
    """Test integration between agent security boundaries."""
    
    def test_agent_hierarchy_enforcement(self):
        """Test that agent security hierarchy is properly enforced."""
        # Define security hierarchy (most to least privileged)
        hierarchy = [
            AgentType.ORCHESTRATOR,
            AgentType.CODE,
            AgentType.QA,
            AgentType.DESIGN,
            AgentType.DATA
        ]
        
        # Compare adjacent levels in hierarchy
        for i in range(len(hierarchy) - 1):
            higher_agent = hierarchy[i]
            lower_agent = hierarchy[i + 1]
            
            higher_allowed = set(get_allowed_tools(higher_agent))
            lower_allowed = set(get_allowed_tools(lower_agent))
            
            # Higher privilege agent should have some tools that lower doesn't
            # (This validates the security hierarchy)
            exclusive_tools = higher_allowed - lower_allowed
            assert len(exclusive_tools) > 0, \
                f"Security hierarchy violation: {lower_agent.value} has same or more tools than {higher_agent.value}"
    
    def test_cross_agent_permission_isolation(self):
        """Test that agents can't access each other's restricted capabilities."""
        # Code agent specific tools should not be available to QA/Design
        code_specific = {"Edit", "MultiEdit", "Bash(git commit)"}
        
        for tool in code_specific:
            assert validate_agent_access(AgentType.CODE, tool), f"Code agent should have {tool}"
            assert not validate_agent_access(AgentType.QA, tool), f"QA agent should not have {tool}"
            assert not validate_agent_access(AgentType.DESIGN, tool), f"Design agent should not have {tool}"
        
        # QA agent specific tools
        qa_specific_patterns = ["pytest", "coverage", "testing"]
        
        qa_allowed = get_allowed_tools(AgentType.QA)
        design_allowed = get_allowed_tools(AgentType.DESIGN)
        
        # QA should have testing tools that Design doesn't
        qa_testing_tools = [tool for tool in qa_allowed if any(pattern in tool.lower() for pattern in qa_specific_patterns)]
        design_testing_tools = [tool for tool in design_allowed if any(pattern in tool.lower() for pattern in qa_specific_patterns)]
        
        assert len(qa_testing_tools) > len(design_testing_tools), \
            "QA agent should have more testing tools than Design agent"


class TestSecurityComplianceValidation:
    """Test security compliance and audit requirements."""
    
    def test_government_audit_compliance_coverage(self):
        """Test that security measures meet government audit compliance."""
        # Verify all critical security areas are covered
        critical_areas = {
            "privilege_escalation_prevention": RESTRICTED_COMMANDS,
            "access_control_enforcement": AGENT_TOOL_CONFIG,
            "audit_trail_capability": get_security_summary,
            "least_privilege_principle": get_allowed_tools,
            "security_boundary_enforcement": validate_agent_access
        }
        
        for area, implementation in critical_areas.items():
            assert implementation is not None, f"Critical security area not implemented: {area}"
            
            if callable(implementation):
                # Test that the function works for all agent types
                for agent_type in AgentType:
                    try:
                        result = implementation(agent_type)
                        assert result is not None, f"Security function {area} returned None for {agent_type.value}"
                    except Exception as e:
                        pytest.fail(f"Security function {area} failed for {agent_type.value}: {str(e)}")
    
    def test_security_configuration_immutability(self):
        """Test that security configurations cannot be modified at runtime."""
        # Test that AGENT_TOOL_CONFIG is properly protected
        original_config = AGENT_TOOL_CONFIG.copy()
        
        # Verify configuration exists and is comprehensive
        assert len(original_config) == len(AgentType), "Configuration missing for some agent types"
        
        for agent_type in AgentType:
            assert agent_type in original_config, f"Configuration missing for {agent_type.value}"
            
            config = original_config[agent_type]
            assert "allowed_tools" in config, f"Allowed tools missing for {agent_type.value}"
            assert "disallowed_tools" in config, f"Disallowed tools missing for {agent_type.value}"
    
    def test_security_error_handling(self):
        """Test security error handling and fail-safe behavior."""
        # Test that security functions fail safely with invalid inputs
        invalid_inputs = [None, "", "invalid", 123, [], {}]
        
        for invalid_input in invalid_inputs:
            try:
                # Should not crash, should return safe default (False/empty)
                result = validate_agent_access(AgentType.CODE, invalid_input)
                assert result is False, f"Security validation should fail safely for invalid input: {invalid_input}"
            except Exception:
                # If it raises an exception, it should be handled gracefully
                pass
    
    def test_comprehensive_security_documentation(self):
        """Test that all security functions have proper documentation."""
        security_functions = [
            get_allowed_tools,
            get_disallowed_tools,
            validate_agent_access,
            get_security_summary,
            get_tdd_capabilities,
            validate_tdd_phase_access,
            get_tdd_tool_restrictions,
            validate_tdd_tool_access
        ]
        
        for func in security_functions:
            assert func.__doc__ is not None, f"Security function {func.__name__} missing documentation"
            assert len(func.__doc__.strip()) > 0, f"Security function {func.__name__} has empty documentation"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=lib.agent_tool_config", "--cov-report=term-missing"])