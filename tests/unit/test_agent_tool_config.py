"""
Tests for agent tool configuration and command access control.

Verifies that agents have appropriate tool restrictions for security.
"""

import unittest
import sys
import os
from pathlib import Path

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
    TDD_COMMANDS
)


class TestAgentToolConfig(unittest.TestCase):
    """Test agent tool configuration system"""
    
    def test_orchestrator_has_full_access(self):
        """Test that orchestrator has broad tool access"""
        allowed = get_allowed_tools(AgentType.ORCHESTRATOR)
        
        # Should have all basic tools
        self.assertIn("Read", allowed)
        self.assertIn("Write", allowed)
        self.assertIn("Edit", allowed)
        self.assertIn("Bash(*)", allowed)
        
        # Should have elevated permissions
        disallowed = get_disallowed_tools(AgentType.ORCHESTRATOR)
        self.assertNotIn("Bash(rm)", disallowed)
        self.assertNotIn("Bash(git commit)", disallowed)
    
    def test_design_agent_restrictions(self):
        """Test that design agent has appropriate restrictions"""
        allowed = get_allowed_tools(AgentType.DESIGN)
        disallowed = get_disallowed_tools(AgentType.DESIGN)
        
        # Should have read/write for docs
        self.assertIn("Read", allowed)
        self.assertIn("Write", allowed)
        
        # Should not modify existing code
        self.assertIn("Edit", disallowed)
        self.assertIn("MultiEdit", disallowed)
        
        # Should not have dangerous commands
        dangerous_bash_commands = [f"Bash({cmd})" for cmd in RESTRICTED_COMMANDS + ELEVATED_COMMANDS]
        for dangerous_cmd in dangerous_bash_commands:
            self.assertIn(dangerous_cmd, disallowed)
    
    def test_code_agent_permissions(self):
        """Test that code agent has code modification but not dangerous commands"""
        allowed = get_allowed_tools(AgentType.CODE)
        disallowed = get_disallowed_tools(AgentType.CODE)
        
        # Should have code modification tools
        self.assertIn("Edit", allowed)
        self.assertIn("MultiEdit", allowed)
        self.assertIn("Bash(git commit)", allowed)
        self.assertIn("Bash(git add)", allowed)
        
        # Should not have dangerous commands
        self.assertIn("Bash(rm)", disallowed)
        self.assertIn("Bash(sudo)", disallowed)
        self.assertIn("Bash(git push)", disallowed)
    
    def test_qa_agent_restrictions(self):
        """Test that QA agent cannot modify code but can run tests"""
        allowed = get_allowed_tools(AgentType.QA)
        disallowed = get_disallowed_tools(AgentType.QA)
        
        # Should have testing tools
        self.assertIn("Bash(pytest)", allowed)
        self.assertIn("Bash(coverage)", allowed)
        
        # Should not modify code but can create test files for TDD
        self.assertIn("Edit", disallowed)
        # Note: QA agent CAN write test files for TDD TEST_RED phase
        self.assertIn("Write", allowed)  # TDD enhancement: QA can create test files
        
        # Should not have git access
        self.assertIn("Bash(git commit)", disallowed)
        self.assertIn("Bash(git add)", disallowed)
    
    def test_data_agent_permissions(self):
        """Test that data agent has data processing but not code modification"""
        allowed = get_allowed_tools(AgentType.DATA)
        disallowed = get_disallowed_tools(AgentType.DATA)
        
        # Should have data tools
        self.assertIn("Read", allowed)
        self.assertIn("Write", allowed)  # For reports
        self.assertIn("NotebookEdit", allowed)  # For analysis notebooks
        
        # Should not modify source code
        self.assertIn("Edit", disallowed)
        self.assertIn("MultiEdit", disallowed)
        
        # Should not have git access
        self.assertIn("Bash(git commit)", disallowed)
    
    def test_claude_tool_args_generation(self):
        """Test that Claude CLI arguments are generated correctly"""
        args = get_claude_tool_args(AgentType.DESIGN)
        
        # Should contain allowedTools and disallowedTools
        self.assertIn("--allowedTools", args)
        self.assertIn("--disallowedTools", args)
        
        # Should have the tools as space-separated strings
        allowed_idx = args.index("--allowedTools")
        allowed_tools = args[allowed_idx + 1]
        self.assertIn("Read", allowed_tools)
        self.assertIn("Write", allowed_tools)
    
    def test_validate_agent_access(self):
        """Test agent access validation"""
        # Design agent should have read access
        self.assertTrue(validate_agent_access(AgentType.DESIGN, "Read"))
        
        # Design agent should not have edit access
        self.assertFalse(validate_agent_access(AgentType.DESIGN, "Edit"))
        
        # Code agent should have git commit access
        self.assertTrue(validate_agent_access(AgentType.CODE, "Bash(git commit)"))
        
        # QA agent should not have git commit access
        self.assertFalse(validate_agent_access(AgentType.QA, "Bash(git commit)"))
        
        # No agent should have sudo access (except orchestrator)
        self.assertFalse(validate_agent_access(AgentType.CODE, "Bash(sudo)"))
        self.assertFalse(validate_agent_access(AgentType.QA, "Bash(sudo)"))
        self.assertFalse(validate_agent_access(AgentType.DATA, "Bash(sudo)"))
    
    def test_orchestrator_dangerous_command_restrictions(self):
        """Test that even orchestrator has some command restrictions"""
        disallowed = get_disallowed_tools(AgentType.ORCHESTRATOR)
        
        # Even orchestrator should not have these
        self.assertIn("Bash(sudo)", disallowed)
        self.assertIn("Bash(format)", disallowed)
        self.assertIn("Bash(dd)", disallowed)
    
    def test_security_summary(self):
        """Test security summary generation"""
        summary = get_security_summary(AgentType.CODE)
        
        self.assertEqual(summary["agent_type"], "CodeAgent")
        self.assertIsInstance(summary["allowed_tools_count"], int)
        self.assertIsInstance(summary["disallowed_tools_count"], int)
        self.assertIsInstance(summary["allowed_tools"], list)
        self.assertIsInstance(summary["disallowed_tools"], list)
        self.assertGreater(summary["restricted_commands_blocked"], 0)
    
    def test_all_agent_types_have_config(self):
        """Test that all agent types have configuration"""
        for agent_type in AgentType:
            allowed = get_allowed_tools(agent_type)
            disallowed = get_disallowed_tools(agent_type)
            
            # Every agent should have some configuration
            self.assertIsInstance(allowed, list)
            self.assertIsInstance(disallowed, list)
            
            # Generate CLI args should work for all
            args = get_claude_tool_args(agent_type)
            self.assertIsInstance(args, list)
    
    def test_bash_command_patterns(self):
        """Test bash command pattern matching"""
        # Test specific git commands
        self.assertTrue(validate_agent_access(AgentType.CODE, "Bash(git status)"))
        self.assertTrue(validate_agent_access(AgentType.CODE, "Bash(git commit)"))
        self.assertFalse(validate_agent_access(AgentType.QA, "Bash(git commit)"))
        
        # Test dangerous commands are blocked
        self.assertFalse(validate_agent_access(AgentType.CODE, "Bash(rm -rf /)"))
        self.assertFalse(validate_agent_access(AgentType.DATA, "Bash(sudo rm)"))
    
    def test_no_agent_has_conflicting_permissions(self):
        """Test that no agent has conflicting allowed/disallowed tools"""
        for agent_type in AgentType:
            allowed = set(get_allowed_tools(agent_type))
            disallowed = set(get_disallowed_tools(agent_type))
            
            # Should not have overlap (except for Bash patterns)
            overlap = allowed.intersection(disallowed)
            # Filter out Bash patterns which might have complex matching
            simple_overlap = {tool for tool in overlap if not tool.startswith("Bash(")}
            self.assertEqual(len(simple_overlap), 0, 
                           f"Agent {agent_type} has conflicting permissions: {simple_overlap}")


class TestAgentIntegration(unittest.TestCase):
    """Test agent integration with tool restrictions"""
    
    def test_agent_client_creation(self):
        """Test that agent-specific clients can be created"""
        from lib.claude_client import create_agent_client
        
        # Should be able to create clients for all agent types
        for agent_type in AgentType:
            client = create_agent_client(agent_type)
            self.assertEqual(client.agent_type, agent_type)
            self.assertIsNotNone(client.timeout)
    
    def test_agent_instances_use_restricted_clients(self):
        """Test that agent instances use properly restricted Claude clients"""
        from lib.agents.design_agent import DesignAgent
        from lib.agents.code_agent import CodeAgent
        from lib.agents.qa_agent import QAAgent
        from lib.agents.data_agent import DataAgent
        
        # Create agent instances
        design_agent = DesignAgent()
        code_agent = CodeAgent()
        qa_agent = QAAgent()
        data_agent = DataAgent()
        
        # Verify they have the correct agent types set (check string values to avoid enum import issues)
        self.assertEqual(design_agent.claude_client.agent_type.value, "DesignAgent")
        self.assertEqual(code_agent.claude_client.agent_type.value, "CodeAgent")
        self.assertEqual(qa_agent.claude_client.agent_type.value, "QAAgent")
        self.assertEqual(data_agent.claude_client.agent_type.value, "DataAgent")


class TestTDDCapabilities(unittest.TestCase):
    """Test TDD-specific agent capabilities and restrictions"""
    
    def test_get_tdd_capabilities_all_agents(self):
        """Test TDD capabilities for all agent types"""
        for agent_type in AgentType:
            capabilities = get_tdd_capabilities(agent_type)
            
            # All agents should have a capabilities dict
            self.assertIsInstance(capabilities, dict)
            self.assertIn("can_coordinate_tdd_cycles", capabilities)
            self.assertIn("can_manage_all_phases", capabilities)
            self.assertIn("tdd_phases", capabilities)
            self.assertIsInstance(capabilities["tdd_phases"], list)
    
    def test_orchestrator_tdd_capabilities(self):
        """Test that orchestrator has full TDD capabilities"""
        capabilities = get_tdd_capabilities(AgentType.ORCHESTRATOR)
        
        self.assertTrue(capabilities["can_coordinate_tdd_cycles"])
        self.assertTrue(capabilities["can_manage_all_phases"])
        self.assertEqual(len(capabilities["tdd_phases"]), 5)  # All phases
        self.assertIn("DESIGN", capabilities["tdd_phases"])
        self.assertIn("TEST_RED", capabilities["tdd_phases"])
        self.assertIn("CODE_GREEN", capabilities["tdd_phases"])
        self.assertIn("REFACTOR", capabilities["tdd_phases"])
        self.assertIn("COMMIT", capabilities["tdd_phases"])
    
    def test_design_agent_tdd_capabilities(self):
        """Test DesignAgent TDD capabilities"""
        capabilities = get_tdd_capabilities(AgentType.DESIGN)
        
        self.assertFalse(capabilities["can_coordinate_tdd_cycles"])
        self.assertFalse(capabilities["can_manage_all_phases"])
        self.assertEqual(capabilities["tdd_phases"], ["DESIGN"])
        self.assertIn("tdd_specification_creation", capabilities["capabilities"])
        self.assertIn("acceptance_criteria_definition", capabilities["capabilities"])
        self.assertIn("read_only_code_access", capabilities["restrictions"])
    
    def test_qa_agent_tdd_capabilities(self):
        """Test QAAgent TDD capabilities"""
        capabilities = get_tdd_capabilities(AgentType.QA)
        
        self.assertFalse(capabilities["can_coordinate_tdd_cycles"])
        self.assertFalse(capabilities["can_manage_all_phases"])
        self.assertEqual(capabilities["tdd_phases"], ["TEST_RED"])
        self.assertIn("failing_test_creation", capabilities["capabilities"])
        self.assertIn("test_red_state_validation", capabilities["capabilities"])
        self.assertIn("cannot_modify_implementation_code", capabilities["restrictions"])
    
    def test_code_agent_tdd_capabilities(self):
        """Test CodeAgent TDD capabilities"""
        capabilities = get_tdd_capabilities(AgentType.CODE)
        
        self.assertFalse(capabilities["can_coordinate_tdd_cycles"])
        self.assertFalse(capabilities["can_manage_all_phases"])
        self.assertEqual(set(capabilities["tdd_phases"]), {"CODE_GREEN", "REFACTOR", "COMMIT"})
        self.assertIn("minimal_implementation_creation", capabilities["capabilities"])
        self.assertIn("test_driven_development", capabilities["capabilities"])
        self.assertIn("tdd_commit_management", capabilities["capabilities"])
    
    def test_data_agent_tdd_capabilities(self):
        """Test DataAgent TDD capabilities"""
        capabilities = get_tdd_capabilities(AgentType.DATA)
        
        self.assertFalse(capabilities["can_coordinate_tdd_cycles"])
        self.assertFalse(capabilities["can_manage_all_phases"])
        self.assertEqual(capabilities["tdd_phases"], [])  # No direct TDD phases
        self.assertIn("tdd_metrics_analysis", capabilities["capabilities"])
        self.assertIn("test_coverage_reporting", capabilities["capabilities"])
        self.assertIn("read_only_access", capabilities["restrictions"])
    
    def test_validate_tdd_phase_access(self):
        """Test TDD phase access validation"""
        # DesignAgent should only access DESIGN phase
        self.assertTrue(validate_tdd_phase_access(AgentType.DESIGN, "DESIGN"))
        self.assertFalse(validate_tdd_phase_access(AgentType.DESIGN, "TEST_RED"))
        self.assertFalse(validate_tdd_phase_access(AgentType.DESIGN, "CODE_GREEN"))
        
        # QAAgent should only access TEST_RED phase
        self.assertFalse(validate_tdd_phase_access(AgentType.QA, "DESIGN"))
        self.assertTrue(validate_tdd_phase_access(AgentType.QA, "TEST_RED"))
        self.assertFalse(validate_tdd_phase_access(AgentType.QA, "CODE_GREEN"))
        
        # CodeAgent should access CODE_GREEN, REFACTOR, COMMIT phases
        self.assertFalse(validate_tdd_phase_access(AgentType.CODE, "DESIGN"))
        self.assertFalse(validate_tdd_phase_access(AgentType.CODE, "TEST_RED"))
        self.assertTrue(validate_tdd_phase_access(AgentType.CODE, "CODE_GREEN"))
        self.assertTrue(validate_tdd_phase_access(AgentType.CODE, "REFACTOR"))
        self.assertTrue(validate_tdd_phase_access(AgentType.CODE, "COMMIT"))
        
        # Orchestrator should access all phases
        for phase in ["DESIGN", "TEST_RED", "CODE_GREEN", "REFACTOR", "COMMIT"]:
            self.assertTrue(validate_tdd_phase_access(AgentType.ORCHESTRATOR, phase))
    
    def test_get_tdd_tool_restrictions(self):
        """Test TDD tool restrictions for all agent types"""
        for agent_type in AgentType:
            restrictions = get_tdd_tool_restrictions(agent_type)
            
            self.assertIsInstance(restrictions, dict)
            self.assertIn("pytest_restrictions", restrictions)
            self.assertIn("git_restrictions", restrictions)
            self.assertIn("file_access_restrictions", restrictions)
            self.assertIn("special_tdd_tools", restrictions)
    
    def test_design_agent_tdd_restrictions(self):
        """Test DesignAgent TDD restrictions"""
        restrictions = get_tdd_tool_restrictions(AgentType.DESIGN)
        
        self.assertIn("cannot_execute_tests", restrictions["pytest_restrictions"])
        self.assertIn("read_only_git_access", restrictions["git_restrictions"])
        self.assertIn("cannot_modify_existing_code", restrictions["file_access_restrictions"])
        self.assertIn("specification_generation", restrictions["special_tdd_tools"])
    
    def test_qa_agent_tdd_restrictions(self):
        """Test QAAgent TDD restrictions"""
        restrictions = get_tdd_tool_restrictions(AgentType.QA)
        
        self.assertIn("can_execute_tests", restrictions["pytest_restrictions"])
        self.assertIn("can_create_test_files", restrictions["pytest_restrictions"])
        self.assertIn("cannot_commit", restrictions["git_restrictions"])
        self.assertIn("cannot_push", restrictions["git_restrictions"])
        self.assertIn("can_create_test_files", restrictions["file_access_restrictions"])
        self.assertIn("test_file_generation", restrictions["special_tdd_tools"])
    
    def test_code_agent_tdd_restrictions(self):
        """Test CodeAgent TDD restrictions"""
        restrictions = get_tdd_tool_restrictions(AgentType.CODE)
        
        self.assertIn("can_execute_tests", restrictions["pytest_restrictions"])
        self.assertIn("can_validate_green_state", restrictions["pytest_restrictions"])
        self.assertIn("can_add", restrictions["git_restrictions"])
        self.assertIn("can_commit", restrictions["git_restrictions"])
        self.assertIn("cannot_push", restrictions["git_restrictions"])
        self.assertIn("can_modify_implementation", restrictions["file_access_restrictions"])
        self.assertIn("minimal_implementation", restrictions["special_tdd_tools"])
    
    def test_validate_tdd_tool_access_pytest(self):
        """Test TDD tool access validation for pytest commands"""
        # DesignAgent should not execute tests
        result = validate_tdd_tool_access(AgentType.DESIGN, "Bash(pytest)", {"current_phase": "DESIGN"})
        self.assertFalse(result["allowed"])
        self.assertIn("cannot execute tests", result["tdd_specific_restrictions"][0])
        
        # QAAgent should execute tests
        result = validate_tdd_tool_access(AgentType.QA, "Bash(pytest)", {"current_phase": "TEST_RED"})
        self.assertTrue(result["allowed"])
        self.assertIn("test execution permissions", result["reasoning"][1])
        
        # CodeAgent should execute tests
        result = validate_tdd_tool_access(AgentType.CODE, "Bash(pytest)", {"current_phase": "CODE_GREEN"})
        self.assertTrue(result["allowed"])
        self.assertIn("test execution permissions", result["reasoning"][1])
    
    def test_validate_tdd_tool_access_git(self):
        """Test TDD tool access validation for git commands"""
        # DesignAgent should not commit
        result = validate_tdd_tool_access(AgentType.DESIGN, "Bash(git commit)", {"current_phase": "DESIGN"})
        self.assertFalse(result["allowed"])
        self.assertIn("read-only git access", result["tdd_specific_restrictions"][0])
        
        # QAAgent should not commit
        result = validate_tdd_tool_access(AgentType.QA, "Bash(git commit)", {"current_phase": "TEST_RED"})
        self.assertFalse(result["allowed"])
        self.assertIn("cannot commit", result["tdd_specific_restrictions"][0])
        
        # CodeAgent should commit but not push
        result = validate_tdd_tool_access(AgentType.CODE, "Bash(git commit)", {"current_phase": "COMMIT"})
        self.assertTrue(result["allowed"])
        
        result = validate_tdd_tool_access(AgentType.CODE, "Bash(git push)", {"current_phase": "COMMIT"})
        self.assertFalse(result["allowed"])
        self.assertIn("cannot push", result["tdd_specific_restrictions"][0])
    
    def test_validate_tdd_tool_access_phase_recommendations(self):
        """Test TDD phase recommendations in tool access validation"""
        # DesignAgent in wrong phase
        result = validate_tdd_tool_access(AgentType.DESIGN, "Read", {"current_phase": "TEST_RED"})
        self.assertIn("should not be active in TEST_RED phase", result["recommendations"][0])
        
        # QAAgent in correct phase
        result = validate_tdd_tool_access(AgentType.QA, "Write", {"current_phase": "TEST_RED"})
        self.assertIn("properly configured for TEST_RED phase", result["recommendations"][0])
        
        # CodeAgent in correct phase
        result = validate_tdd_tool_access(AgentType.CODE, "Edit", {"current_phase": "CODE_GREEN"})
        self.assertIn("properly configured for CODE_GREEN phase", result["recommendations"][0])
    
    def test_tdd_commands_defined(self):
        """Test that TDD commands are properly defined"""
        self.assertIsInstance(TDD_COMMANDS, list)
        self.assertGreater(len(TDD_COMMANDS), 0)
        
        # Check for expected TDD commands
        tdd_command_strings = " ".join(TDD_COMMANDS)
        self.assertIn("pytest", tdd_command_strings)
        self.assertIn("coverage", tdd_command_strings)
        self.assertIn("git status", tdd_command_strings)
    
    def test_qa_agent_can_write_test_files(self):
        """Test that QAAgent can write test files in TDD workflow"""
        allowed_tools = get_allowed_tools(AgentType.QA)
        
        # QAAgent should be able to write test files
        self.assertIn("Write", allowed_tools)
        
        # Verify this is allowed for test creation but not general code
        restrictions = get_tdd_tool_restrictions(AgentType.QA)
        self.assertIn("can_create_test_files", restrictions["file_access_restrictions"])
        self.assertIn("cannot_modify_implementation", restrictions["file_access_restrictions"])
    
    def test_code_agent_enhanced_tdd_tools(self):
        """Test that CodeAgent has enhanced TDD tools"""
        allowed_tools = get_allowed_tools(AgentType.CODE)
        
        # Should have enhanced pytest commands
        self.assertIn("Bash(pytest --tb=short)", allowed_tools)
        self.assertIn("Bash(pytest -v)", allowed_tools)
        self.assertIn("Bash(pytest --cov)", allowed_tools)
        self.assertIn("Bash(coverage run)", allowed_tools)
        self.assertIn("Bash(coverage report)", allowed_tools)
        
        # Should have enhanced git commands for TDD
        self.assertIn("Bash(git status --porcelain)", allowed_tools)
        self.assertIn("Bash(git diff --name-only)", allowed_tools)
        self.assertIn("Bash(git diff --stat)", allowed_tools)
        
        # Should have code quality tools for refactoring
        self.assertIn("Bash(isort)", allowed_tools)
        self.assertIn("Bash(autopep8)", allowed_tools)
    
    def test_security_summary_includes_tdd(self):
        """Test that security summary includes TDD capabilities"""
        for agent_type in AgentType:
            summary = get_security_summary(agent_type)
            
            self.assertIn("tdd_capabilities", summary)
            tdd_caps = summary["tdd_capabilities"]
            self.assertIsInstance(tdd_caps, dict)
            self.assertIn("can_coordinate_tdd_cycles", tdd_caps)
            self.assertIn("tdd_phases", tdd_caps)


if __name__ == "__main__":
    unittest.main()