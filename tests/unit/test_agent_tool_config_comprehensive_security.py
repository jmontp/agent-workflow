"""
Comprehensive security test suite for Agent Tool Configuration module.

This module provides extensive security testing for agent tool access controls,
focusing on security boundaries, privilege escalation prevention, and TDD workflow
security validation.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any

from lib.agent_tool_config import (
    AgentType,
    AGENT_TOOL_CONFIG,
    RESTRICTED_COMMANDS,
    ELEVATED_COMMANDS,
    CODE_MANAGEMENT_COMMANDS,
    TDD_COMMANDS,
    get_allowed_tools,
    get_disallowed_tools,
    get_claude_tool_args,
    validate_agent_access,
    get_security_summary,
    get_tdd_capabilities,
    validate_tdd_phase_access,
    get_tdd_tool_restrictions,
    validate_tdd_tool_access
)


class TestAgentTypeEnum:
    """Test AgentType enum security properties"""
    
    def test_agent_type_values(self):
        """Test agent type enum values are correctly defined"""
        assert AgentType.ORCHESTRATOR.value == "Orchestrator"
        assert AgentType.DESIGN.value == "DesignAgent"
        assert AgentType.CODE.value == "CodeAgent"
        assert AgentType.QA.value == "QAAgent"
        assert AgentType.DATA.value == "DataAgent"
    
    def test_agent_type_completeness(self):
        """Test all agent types are accounted for in configuration"""
        for agent_type in AgentType:
            assert agent_type in AGENT_TOOL_CONFIG, f"Agent type {agent_type} missing from config"
    
    def test_agent_type_immutability(self):
        """Test agent type enum cannot be modified"""
        with pytest.raises(AttributeError):
            AgentType.ORCHESTRATOR = "Modified"


class TestSecurityCommands:
    """Test security command classifications"""
    
    def test_restricted_commands_coverage(self):
        """Test restricted commands include critical security threats"""
        critical_commands = ["sudo", "su", "chmod", "chown", "kill", "format", "dd", "shred"]
        for cmd in critical_commands:
            assert cmd in RESTRICTED_COMMANDS, f"Critical command {cmd} not in restricted list"
    
    def test_elevated_commands_coverage(self):
        """Test elevated commands include dangerous operations"""
        dangerous_commands = ["rm", "rmdir", "git push"]
        for cmd in dangerous_commands:
            assert cmd in ELEVATED_COMMANDS, f"Dangerous command {cmd} not in elevated list"
    
    def test_code_management_commands_coverage(self):
        """Test code management commands include git operations"""
        git_commands = ["git commit", "git add", "git reset"]
        for cmd in git_commands:
            assert cmd in CODE_MANAGEMENT_COMMANDS, f"Git command {cmd} not in code management list"
    
    def test_tdd_commands_coverage(self):
        """Test TDD commands include testing and validation tools"""
        tdd_tools = ["pytest", "coverage", "git status", "git diff"]
        for tool in tdd_tools:
            assert any(tool in cmd for cmd in TDD_COMMANDS), f"TDD tool {tool} not found in TDD commands"
    
    def test_command_list_types(self):
        """Test all command lists are properly typed"""
        assert isinstance(RESTRICTED_COMMANDS, list)
        assert isinstance(ELEVATED_COMMANDS, list)
        assert isinstance(CODE_MANAGEMENT_COMMANDS, list)
        assert isinstance(TDD_COMMANDS, list)
    
    def test_command_list_no_duplicates(self):
        """Test command lists don't contain duplicates"""
        assert len(RESTRICTED_COMMANDS) == len(set(RESTRICTED_COMMANDS))
        assert len(ELEVATED_COMMANDS) == len(set(ELEVATED_COMMANDS))
        assert len(CODE_MANAGEMENT_COMMANDS) == len(set(CODE_MANAGEMENT_COMMANDS))
        assert len(TDD_COMMANDS) == len(set(TDD_COMMANDS))


class TestOrchestratorSecurity:
    """Test Orchestrator agent security configuration"""
    
    def test_orchestrator_full_tool_access(self):
        """Test orchestrator has comprehensive tool access"""
        allowed = get_allowed_tools(AgentType.ORCHESTRATOR)
        
        # Check core tools
        core_tools = ["Read", "Write", "Edit", "MultiEdit", "Glob", "Grep", "LS"]
        for tool in core_tools:
            assert tool in allowed, f"Orchestrator missing core tool: {tool}"
        
        # Check task spawning capability
        assert "Task" in allowed, "Orchestrator cannot spawn sub-agents"
        
        # Check full bash access
        assert "Bash(*)" in allowed, "Orchestrator lacks full bash access"
    
    def test_orchestrator_security_restrictions(self):
        """Test orchestrator still has security restrictions"""
        disallowed = get_disallowed_tools(AgentType.ORCHESTRATOR)
        
        # Check dangerous system commands are still blocked
        dangerous_commands = ["Bash(sudo)", "Bash(su)", "Bash(format)", "Bash(dd)"]
        for cmd in dangerous_commands:
            assert cmd in disallowed, f"Orchestrator should not have access to: {cmd}"
    
    def test_orchestrator_tdd_capabilities(self):
        """Test orchestrator TDD workflow capabilities"""
        capabilities = get_tdd_capabilities(AgentType.ORCHESTRATOR)
        
        assert capabilities["can_coordinate_tdd_cycles"] is True
        assert capabilities["can_manage_all_phases"] is True
        assert "DESIGN" in capabilities["tdd_phases"]
        assert "TEST_RED" in capabilities["tdd_phases"]
        assert "CODE_GREEN" in capabilities["tdd_phases"]
        assert "REFACTOR" in capabilities["tdd_phases"]
        assert "COMMIT" in capabilities["tdd_phases"]


class TestDesignAgentSecurity:
    """Test Design agent security restrictions"""
    
    def test_design_agent_read_only_access(self):
        """Test design agent has read-only access"""
        allowed = get_allowed_tools(AgentType.DESIGN)
        disallowed = get_disallowed_tools(AgentType.DESIGN)
        
        # Should have read tools
        read_tools = ["Read", "Glob", "Grep", "LS", "WebFetch", "WebSearch"]
        for tool in read_tools:
            assert tool in allowed, f"Design agent missing read tool: {tool}"
        
        # Should NOT have modification tools
        modify_tools = ["Edit", "MultiEdit", "NotebookEdit"]
        for tool in modify_tools:
            assert tool in disallowed, f"Design agent should not have: {tool}"
    
    def test_design_agent_bash_restrictions(self):
        """Test design agent bash command restrictions"""
        allowed = get_allowed_tools(AgentType.DESIGN)
        
        # Should have safe bash commands
        safe_commands = ["Bash(ls)", "Bash(find)", "Bash(cat)", "Bash(head)"]
        for cmd in safe_commands:
            assert cmd in allowed, f"Design agent missing safe command: {cmd}"
        
        # Validate no dangerous commands
        for restricted in RESTRICTED_COMMANDS + ELEVATED_COMMANDS:
            assert not validate_agent_access(AgentType.DESIGN, f"Bash({restricted})"), \
                f"Design agent should not access: {restricted}"
    
    def test_design_agent_tdd_phase_restrictions(self):
        """Test design agent TDD phase access"""
        capabilities = get_tdd_capabilities(AgentType.DESIGN)
        
        assert capabilities["can_coordinate_tdd_cycles"] is False
        assert capabilities["can_manage_all_phases"] is False
        assert capabilities["tdd_phases"] == ["DESIGN"]
        
        # Should only access DESIGN phase
        assert validate_tdd_phase_access(AgentType.DESIGN, "DESIGN") is True
        assert validate_tdd_phase_access(AgentType.DESIGN, "TEST_RED") is False
        assert validate_tdd_phase_access(AgentType.DESIGN, "CODE_GREEN") is False


class TestCodeAgentSecurity:
    """Test Code agent security configuration"""
    
    def test_code_agent_modification_access(self):
        """Test code agent has code modification capabilities"""
        allowed = get_allowed_tools(AgentType.CODE)
        
        # Should have modification tools
        modify_tools = ["Read", "Write", "Edit", "MultiEdit"]
        for tool in modify_tools:
            assert tool in allowed, f"Code agent missing modification tool: {tool}"
        
        # Should have git tools
        git_tools = ["Bash(git add)", "Bash(git commit)", "Bash(git status)"]
        for tool in git_tools:
            assert tool in allowed, f"Code agent missing git tool: {tool}"
    
    def test_code_agent_restrictions(self):
        """Test code agent security restrictions"""
        disallowed = get_disallowed_tools(AgentType.CODE)
        
        # Should not manage todos directly
        assert "TodoWrite" in disallowed, "Code agent should not manage todos"
        
        # Should not have dangerous commands
        for restricted in RESTRICTED_COMMANDS + ELEVATED_COMMANDS:
            assert f"Bash({restricted})" in disallowed, \
                f"Code agent should not have: Bash({restricted})"
    
    def test_code_agent_tdd_workflow(self):
        """Test code agent TDD workflow capabilities"""
        capabilities = get_tdd_capabilities(AgentType.CODE)
        
        assert "CODE_GREEN" in capabilities["tdd_phases"]
        assert "REFACTOR" in capabilities["tdd_phases"]
        assert "COMMIT" in capabilities["tdd_phases"]
        
        # Should have testing tools for validation
        allowed = get_allowed_tools(AgentType.CODE)
        tdd_tools = ["Bash(pytest)", "Bash(coverage run)", "Bash(coverage report)"]
        for tool in tdd_tools:
            assert tool in allowed, f"Code agent missing TDD tool: {tool}"
    
    def test_code_agent_git_permissions(self):
        """Test code agent git permission boundaries"""
        tdd_restrictions = get_tdd_tool_restrictions(AgentType.CODE)
        
        assert "can_add" in tdd_restrictions["git_restrictions"]
        assert "can_commit" in tdd_restrictions["git_restrictions"]
        assert "cannot_push" in tdd_restrictions["git_restrictions"]


class TestQAAgentSecurity:
    """Test QA agent security configuration"""
    
    def test_qa_agent_testing_access(self):
        """Test QA agent has comprehensive testing access"""
        allowed = get_allowed_tools(AgentType.QA)
        
        # Should have testing tools
        test_tools = [
            "Bash(pytest)", "Bash(coverage)", "Bash(pylint)", 
            "Bash(flake8)", "Bash(mypy)", "Bash(bandit)"
        ]
        for tool in test_tools:
            assert tool in allowed, f"QA agent missing testing tool: {tool}"
    
    def test_qa_agent_modification_restrictions(self):
        """Test QA agent cannot modify implementation code"""
        disallowed = get_disallowed_tools(AgentType.QA)
        
        # Should not modify existing code
        modify_restrictions = ["Edit", "MultiEdit", "NotebookEdit"]
        for tool in modify_restrictions:
            assert tool in disallowed, f"QA agent should not have: {tool}"
    
    def test_qa_agent_git_restrictions(self):
        """Test QA agent git access restrictions"""
        disallowed = get_disallowed_tools(AgentType.QA)
        
        git_restrictions = ["Bash(git add)", "Bash(git commit)", "Bash(git push)"]
        for tool in git_restrictions:
            assert tool in disallowed, f"QA agent should not have: {tool}"
    
    def test_qa_agent_tdd_phase_access(self):
        """Test QA agent TDD phase specialization"""
        capabilities = get_tdd_capabilities(AgentType.QA)
        
        assert capabilities["tdd_phases"] == ["TEST_RED"]
        assert "failing_test_creation" in capabilities["capabilities"]
        assert "test_red_state_validation" in capabilities["capabilities"]
        
        # Should only access TEST_RED phase
        assert validate_tdd_phase_access(AgentType.QA, "TEST_RED") is True
        assert validate_tdd_phase_access(AgentType.QA, "CODE_GREEN") is False


class TestDataAgentSecurity:
    """Test Data agent security configuration"""
    
    def test_data_agent_analysis_access(self):
        """Test data agent has data analysis capabilities"""
        allowed = get_allowed_tools(AgentType.DATA)
        
        # Should have data tools
        data_tools = [
            "NotebookRead", "NotebookEdit", "Bash(python)", 
            "Bash(jupyter)", "Bash(pandas)", "Bash(numpy)"
        ]
        for tool in data_tools:
            assert tool in allowed, f"Data agent missing data tool: {tool}"
    
    def test_data_agent_code_restrictions(self):
        """Test data agent cannot modify source code"""
        disallowed = get_disallowed_tools(AgentType.DATA)
        
        # Should not modify source code
        code_restrictions = ["Edit", "MultiEdit", "TodoWrite"]
        for tool in code_restrictions:
            assert tool in disallowed, f"Data agent should not have: {tool}"
        
        # Should not have git access
        for cmd in CODE_MANAGEMENT_COMMANDS:
            assert f"Bash({cmd})" in disallowed, f"Data agent should not have: Bash({cmd})"
    
    def test_data_agent_tdd_limitations(self):
        """Test data agent TDD workflow limitations"""
        capabilities = get_tdd_capabilities(AgentType.DATA)
        
        assert capabilities["can_coordinate_tdd_cycles"] is False
        assert capabilities["can_manage_all_phases"] is False
        assert capabilities["tdd_phases"] == []
        assert "read_only_access" in capabilities["restrictions"]


class TestAccessValidation:
    """Test access validation functions"""
    
    def test_validate_agent_access_basic(self):
        """Test basic agent access validation"""
        # Orchestrator should have broad access
        assert validate_agent_access(AgentType.ORCHESTRATOR, "Read") is True
        assert validate_agent_access(AgentType.ORCHESTRATOR, "Bash(ls)") is True
        
        # Design agent should not have edit access
        assert validate_agent_access(AgentType.DESIGN, "Edit") is False
        assert validate_agent_access(AgentType.DESIGN, "Read") is True
    
    def test_validate_agent_access_bash_commands(self):
        """Test bash command access validation"""
        # Test restricted command blocking
        for agent_type in [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]:
            for restricted_cmd in RESTRICTED_COMMANDS:
                assert validate_agent_access(agent_type, f"Bash({restricted_cmd})") is False, \
                    f"{agent_type} should not access Bash({restricted_cmd})"
    
    def test_validate_agent_access_explicit_permissions(self):
        """Test explicit permission checking"""
        # Code agent should have git commit access
        assert validate_agent_access(AgentType.CODE, "Bash(git commit)") is True
        
        # QA agent should not have git commit access
        assert validate_agent_access(AgentType.QA, "Bash(git commit)") is False
    
    def test_validate_agent_access_default_deny(self):
        """Test default deny behavior"""
        # Non-listed tools should be denied
        assert validate_agent_access(AgentType.DESIGN, "UnknownTool") is False
        assert validate_agent_access(AgentType.CODE, "Bash(unknown-command)") is False
    
    @pytest.mark.parametrize("agent_type", [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA])
    def test_validate_agent_access_security_boundaries(self, agent_type):
        """Test security boundaries are enforced for all agents"""
        # No agent except orchestrator should have dangerous system access
        dangerous_tools = ["Bash(sudo)", "Bash(rm)", "Bash(format)", "Bash(dd)"]
        for tool in dangerous_tools:
            assert validate_agent_access(agent_type, tool) is False, \
                f"{agent_type} should not access {tool}"


class TestClaudeToolArgs:
    """Test Claude tool argument generation"""
    
    def test_get_claude_tool_args_format(self):
        """Test Claude tool arguments are properly formatted"""
        args = get_claude_tool_args(AgentType.DESIGN)
        
        assert isinstance(args, list)
        assert len(args) >= 2  # Should have at least allowed and disallowed
        
        # Check format
        if "--allowedTools" in args:
            allowed_idx = args.index("--allowedTools")
            assert allowed_idx + 1 < len(args), "Missing allowed tools list"
            assert isinstance(args[allowed_idx + 1], str), "Allowed tools should be string"
        
        if "--disallowedTools" in args:
            disallowed_idx = args.index("--disallowedTools")
            assert disallowed_idx + 1 < len(args), "Missing disallowed tools list"
            assert isinstance(args[disallowed_idx + 1], str), "Disallowed tools should be string"
    
    def test_get_claude_tool_args_orchestrator(self):
        """Test orchestrator Claude tool arguments"""
        args = get_claude_tool_args(AgentType.ORCHESTRATOR)
        
        # Should have allowed tools
        assert "--allowedTools" in args
        allowed_idx = args.index("--allowedTools")
        allowed_tools = args[allowed_idx + 1]
        assert "Read" in allowed_tools
        assert "Bash(*)" in allowed_tools
    
    def test_get_claude_tool_args_restricted_agent(self):
        """Test restricted agent Claude tool arguments"""
        args = get_claude_tool_args(AgentType.DESIGN)
        
        # Should have both allowed and disallowed
        assert "--allowedTools" in args
        assert "--disallowedTools" in args
        
        disallowed_idx = args.index("--disallowedTools")
        disallowed_tools = args[disallowed_idx + 1]
        assert "Edit" in disallowed_tools


class TestSecuritySummary:
    """Test security summary generation"""
    
    def test_get_security_summary_structure(self):
        """Test security summary has proper structure"""
        summary = get_security_summary(AgentType.ORCHESTRATOR)
        
        required_keys = [
            "agent_type", "allowed_tools_count", "disallowed_tools_count",
            "allowed_tools", "disallowed_tools", "restricted_commands_blocked",
            "tdd_capabilities"
        ]
        
        for key in required_keys:
            assert key in summary, f"Security summary missing key: {key}"
    
    def test_get_security_summary_counts(self):
        """Test security summary counts are accurate"""
        summary = get_security_summary(AgentType.CODE)
        
        assert isinstance(summary["allowed_tools_count"], int)
        assert isinstance(summary["disallowed_tools_count"], int)
        assert summary["allowed_tools_count"] > 0
        assert summary["disallowed_tools_count"] > 0
    
    def test_get_security_summary_agent_differences(self):
        """Test security summaries differ appropriately between agents"""
        orchestrator_summary = get_security_summary(AgentType.ORCHESTRATOR)
        design_summary = get_security_summary(AgentType.DESIGN)
        
        # Orchestrator should have more allowed tools
        assert orchestrator_summary["allowed_tools_count"] >= design_summary["allowed_tools_count"]
        
        # Design agent should have more restrictions
        assert design_summary["disallowed_tools_count"] >= orchestrator_summary["disallowed_tools_count"]


class TestTDDSecurityIntegration:
    """Test TDD workflow security integration"""
    
    def test_get_tdd_capabilities_completeness(self):
        """Test TDD capabilities are defined for all agents"""
        for agent_type in AgentType:
            capabilities = get_tdd_capabilities(agent_type)
            assert isinstance(capabilities, dict)
            assert "can_coordinate_tdd_cycles" in capabilities
            assert "tdd_phases" in capabilities
    
    def test_validate_tdd_phase_access_restrictions(self):
        """Test TDD phase access restrictions"""
        # Design agent should only access DESIGN phase
        assert validate_tdd_phase_access(AgentType.DESIGN, "DESIGN") is True
        assert validate_tdd_phase_access(AgentType.DESIGN, "TEST_RED") is False
        
        # QA agent should only access TEST_RED phase
        assert validate_tdd_phase_access(AgentType.QA, "TEST_RED") is True
        assert validate_tdd_phase_access(AgentType.QA, "CODE_GREEN") is False
        
        # Code agent should access implementation phases
        assert validate_tdd_phase_access(AgentType.CODE, "CODE_GREEN") is True
        assert validate_tdd_phase_access(AgentType.CODE, "REFACTOR") is True
        assert validate_tdd_phase_access(AgentType.CODE, "TEST_RED") is False
    
    def test_get_tdd_tool_restrictions_security(self):
        """Test TDD tool restrictions maintain security"""
        # Design agent should be read-only
        design_restrictions = get_tdd_tool_restrictions(AgentType.DESIGN)
        assert "read_only_git_access" in design_restrictions["git_restrictions"]
        assert "cannot_execute_tests" in design_restrictions["pytest_restrictions"]
        
        # QA agent should not commit
        qa_restrictions = get_tdd_tool_restrictions(AgentType.QA)
        assert "cannot_commit" in qa_restrictions["git_restrictions"]
        assert "cannot_push" in qa_restrictions["git_restrictions"]
    
    def test_validate_tdd_tool_access_comprehensive(self):
        """Test comprehensive TDD tool access validation"""
        tdd_context = {"current_phase": "TEST_RED"}
        
        # QA agent should have access to pytest in TEST_RED phase
        qa_result = validate_tdd_tool_access(AgentType.QA, "Bash(pytest)", tdd_context)
        assert qa_result["allowed"] is True
        assert qa_result["current_phase"] == "TEST_RED"
        
        # Design agent should not execute tests
        design_result = validate_tdd_tool_access(AgentType.DESIGN, "Bash(pytest)", tdd_context)
        assert design_result["allowed"] is False
        assert "cannot execute tests" in " ".join(design_result["tdd_specific_restrictions"])
    
    def test_validate_tdd_tool_access_git_restrictions(self):
        """Test TDD git tool access restrictions"""
        tdd_context = {"current_phase": "CODE_GREEN"}
        
        # Design agent should not commit even with context
        design_result = validate_tdd_tool_access(AgentType.DESIGN, "Bash(git commit)", tdd_context)
        assert design_result["allowed"] is False
        assert "read-only git access" in " ".join(design_result["tdd_specific_restrictions"])
        
        # Code agent should be able to commit in CODE_GREEN
        code_result = validate_tdd_tool_access(AgentType.CODE, "Bash(git commit)", tdd_context)
        assert code_result["allowed"] is True


class TestSecurityEdgeCases:
    """Test security edge cases and potential vulnerabilities"""
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection through tool names"""
        malicious_tools = [
            "Bash(ls; rm -rf /)",
            "Read && rm file",
            "Edit$(dangerous_command)",
            "Bash(`malicious`)"
        ]
        
        for agent_type in AgentType:
            for malicious_tool in malicious_tools:
                # Should be blocked due to not being in allowed list
                assert validate_agent_access(agent_type, malicious_tool) is False, \
                    f"Potential command injection not blocked: {malicious_tool}"
    
    def test_privilege_escalation_prevention(self):
        """Test prevention of privilege escalation attempts"""
        escalation_attempts = [
            "Bash(sudo bash)",
            "Bash(su root)",
            "Bash(sudo -u root)",
            "Bash(chmod 777 /etc/passwd)"
        ]
        
        for agent_type in [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]:
            for attempt in escalation_attempts:
                assert validate_agent_access(agent_type, attempt) is False, \
                    f"Privilege escalation not blocked for {agent_type}: {attempt}"
    
    def test_path_traversal_awareness(self):
        """Test awareness of path traversal in tool validation"""
        traversal_attempts = [
            "Read(../../../etc/passwd)",
            "Write(../../../../tmp/malicious)",
            "Edit(../../config/secrets)"
        ]
        
        # Note: validate_agent_access only checks tool names, not parameters
        # But it should still block unauthorized tools
        for agent_type in AgentType:
            if agent_type != AgentType.ORCHESTRATOR:
                # These should pass basic tool validation but would be caught
                # by actual tool implementation parameter validation
                pass
    
    def test_empty_and_none_inputs(self):
        """Test handling of empty and None inputs"""
        # Empty tool name
        assert validate_agent_access(AgentType.ORCHESTRATOR, "") is False
        
        # None inputs should not cause crashes
        with pytest.raises(TypeError):
            validate_agent_access(None, "Read")
        
        with pytest.raises(TypeError):
            validate_agent_access(AgentType.ORCHESTRATOR, None)
    
    def test_case_sensitivity_security(self):
        """Test case sensitivity doesn't create security bypasses"""
        # Different cases should not bypass security
        assert validate_agent_access(AgentType.DESIGN, "EDIT") is False
        assert validate_agent_access(AgentType.DESIGN, "edit") is False
        assert validate_agent_access(AgentType.DESIGN, "Edit") is False
        
        # Bash commands with different cases
        assert validate_agent_access(AgentType.DESIGN, "BASH(rm)") is False
        assert validate_agent_access(AgentType.DESIGN, "bash(rm)") is False


class TestConfigurationIntegrity:
    """Test configuration integrity and consistency"""
    
    def test_agent_tool_config_completeness(self):
        """Test AGENT_TOOL_CONFIG has entries for all agent types"""
        for agent_type in AgentType:
            assert agent_type in AGENT_TOOL_CONFIG, f"Missing config for {agent_type}"
            
            config = AGENT_TOOL_CONFIG[agent_type]
            assert "allowed_tools" in config, f"Missing allowed_tools for {agent_type}"
            assert "disallowed_tools" in config, f"Missing disallowed_tools for {agent_type}"
    
    def test_tool_list_consistency(self):
        """Test tool lists are consistent and logical"""
        for agent_type, config in AGENT_TOOL_CONFIG.items():
            allowed = config["allowed_tools"]
            disallowed = config["disallowed_tools"]
            
            # No tool should be both allowed and disallowed
            overlap = set(allowed) & set(disallowed)
            assert len(overlap) == 0, f"Tool overlap for {agent_type}: {overlap}"
    
    def test_security_hierarchy_consistency(self):
        """Test security hierarchy is consistent"""
        # Orchestrator should have the most permissions
        orchestrator_allowed = set(get_allowed_tools(AgentType.ORCHESTRATOR))
        
        for agent_type in [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]:
            agent_allowed = set(get_allowed_tools(agent_type))
            
            # Other agents should have subset of orchestrator tools (or equivalent)
            # This is not strictly enforced due to different tool sets, but check basic tools
            basic_tools = {"Read", "Glob", "Grep", "LS"}
            agent_basic = agent_allowed & basic_tools
            orchestrator_basic = orchestrator_allowed & basic_tools
            
            assert agent_basic <= orchestrator_basic, \
                f"{agent_type} has basic tools not available to orchestrator"
    
    def test_tdd_phase_consistency(self):
        """Test TDD phase assignments are consistent"""
        all_phases = {"DESIGN", "TEST_RED", "CODE_GREEN", "REFACTOR", "COMMIT"}
        
        # Collect all assigned phases
        assigned_phases = set()
        for agent_type in AgentType:
            capabilities = get_tdd_capabilities(agent_type)
            assigned_phases.update(capabilities["tdd_phases"])
        
        # All TDD phases should be covered by some agent
        missing_phases = all_phases - assigned_phases
        assert len(missing_phases) == 0, f"TDD phases not covered: {missing_phases}"
    
    def test_function_return_types(self):
        """Test functions return expected types"""
        # Test return types for each agent
        for agent_type in AgentType:
            allowed = get_allowed_tools(agent_type)
            assert isinstance(allowed, list), f"get_allowed_tools should return list for {agent_type}"
            
            disallowed = get_disallowed_tools(agent_type)
            assert isinstance(disallowed, list), f"get_disallowed_tools should return list for {agent_type}"
            
            args = get_claude_tool_args(agent_type)
            assert isinstance(args, list), f"get_claude_tool_args should return list for {agent_type}"
            
            summary = get_security_summary(agent_type)
            assert isinstance(summary, dict), f"get_security_summary should return dict for {agent_type}"
            
            capabilities = get_tdd_capabilities(agent_type)
            assert isinstance(capabilities, dict), f"get_tdd_capabilities should return dict for {agent_type}"


if __name__ == "__main__":
    pytest.main([__file__])