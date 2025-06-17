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
    RESTRICTED_COMMANDS,
    ELEVATED_COMMANDS,
    CODE_MANAGEMENT_COMMANDS
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
        
        # Should not modify code
        self.assertIn("Edit", disallowed)
        self.assertIn("Write", disallowed)
        
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


if __name__ == "__main__":
    unittest.main()