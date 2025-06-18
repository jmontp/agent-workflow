"""
Comprehensive test suite for CodeAgent in agents/code_agent.py

Tests code agent functionality including feature implementation, bug fixing,
refactoring, TDD implementation cycles, and code quality management.
"""

import pytest
import asyncio
import json
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open
from datetime import datetime
from typing import Dict, Any, List

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from agents.code_agent import CodeAgent
from agents import Task, AgentResult, TaskStatus, TDDState, TDDCycle, TDDTask


class TestCodeAgentInitialization:
    """Test CodeAgent initialization and basic properties"""
    
    def test_code_agent_initialization_default(self):
        """Test CodeAgent initialization with default parameters"""
        agent = CodeAgent()
        
        assert agent.name == "CodeAgent"
        assert "feature_implementation" in agent.capabilities
        assert "bug_fixing" in agent.capabilities
        assert "tdd_implementation" in agent.capabilities
        assert "minimal_code_implementation" in agent.capabilities
        assert agent.claude_client is not None
        assert agent.github_client is None
    
    def test_code_agent_initialization_with_clients(self):
        """Test CodeAgent initialization with custom clients"""
        mock_claude_client = Mock()
        mock_github_client = Mock()
        
        agent = CodeAgent(
            claude_code_client=mock_claude_client,
            github_client=mock_github_client
        )
        
        assert agent.claude_client == mock_claude_client
        assert agent.github_client == mock_github_client
    
    def test_code_agent_capabilities(self):
        """Test CodeAgent has all expected capabilities"""
        agent = CodeAgent()
        
        expected_capabilities = [
            "feature_implementation",
            "bug_fixing",
            "code_refactoring",
            "test_creation",
            "code_review",
            "git_operations",
            "performance_optimization",
            "tdd_implementation",
            "minimal_code_implementation", 
            "test_green_validation",
            "tdd_refactoring",
            "test_preservation",
            "tdd_commits"
        ]
        
        for capability in expected_capabilities:
            assert capability in agent.capabilities


class TestCodeAgentTaskExecution:
    """Test CodeAgent run method and task routing"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_claude_client = AsyncMock()
        self.mock_github_client = Mock()
        self.agent = CodeAgent(
            claude_code_client=self.mock_claude_client,
            github_client=self.mock_github_client
        )
    
    @pytest.mark.asyncio
    async def test_run_with_implement_minimal_solution_command(self):
        """Test run method with TDD minimal implementation command"""
        task = Task(
            id="minimal-task",
            agent_type="CodeAgent",
            command="implement_minimal_solution",
            context={"failing_tests": ["test1.py"], "story_id": "story-1"}
        )
        
        with patch.object(self.agent, '_implement_minimal_solution') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Minimal solution implemented")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            assert result.execution_time > 0
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_validate_test_green_state_command(self):
        """Test run method with test green state validation command"""
        task = Task(
            id="green-task",
            agent_type="CodeAgent",
            command="validate_test_green_state",
            context={"test_files": ["test1.py"], "implementation_files": ["impl.py"]}
        )
        
        with patch.object(self.agent, '_validate_test_green_state') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Green state validated")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_refactor_implementation_command(self):
        """Test run method with refactor implementation command"""
        task = Task(
            id="refactor-task",
            agent_type="CodeAgent",
            command="refactor_implementation",
            context={"implementation_files": ["impl.py"], "refactor_goals": ["improve_readability"]}
        )
        
        with patch.object(self.agent, '_refactor_implementation') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Refactoring complete")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_commit_tdd_cycle_command(self):
        """Test run method with TDD cycle commit command"""
        task = Task(
            id="commit-task",
            agent_type="CodeAgent",
            command="commit_tdd_cycle",
            context={"implementation_files": ["impl.py"], "test_files": ["test.py"]}
        )
        
        with patch.object(self.agent, '_commit_tdd_cycle') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="TDD cycle committed")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_implement_feature_command(self):
        """Test run method with feature implementation command"""
        task = Task(
            id="feature-task",
            agent_type="CodeAgent",
            command="implement feature",
            context={"specification": "User login", "target_file": "login.py"}
        )
        
        with patch.object(self.agent, '_implement_feature') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Feature implemented")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_fix_bug_command(self):
        """Test run method with bug fix command"""
        task = Task(
            id="bug-task",
            agent_type="CodeAgent",
            command="fix bug",
            context={"bug_description": "Null pointer exception", "file_path": "main.py"}
        )
        
        with patch.object(self.agent, '_fix_bug') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Bug fixed")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_refactor_command(self):
        """Test run method with refactor command"""
        task = Task(
            id="refactor-task",
            agent_type="CodeAgent",
            command="refactor code",
            context={"code": "old code", "goal": "improve performance"}
        )
        
        with patch.object(self.agent, '_refactor_code') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Code refactored")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_test_command(self):
        """Test run method with test creation command"""
        task = Task(
            id="test-task",
            agent_type="CodeAgent",
            command="create test",
            context={"code": "function code", "test_type": "unit"}
        )
        
        with patch.object(self.agent, '_create_tests') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Tests created")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_review_command(self):
        """Test run method with code review command"""
        task = Task(
            id="review-task",
            agent_type="CodeAgent",
            command="review code",
            context={"code": "review this code"}
        )
        
        with patch.object(self.agent, '_review_code') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Code reviewed")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_optimize_command(self):
        """Test run method with optimization command"""
        task = Task(
            id="optimize-task",
            agent_type="CodeAgent",
            command="optimize performance",
            context={"code": "unoptimized code", "target": "speed"}
        )
        
        with patch.object(self.agent, '_optimize_code') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Code optimized")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_general_command(self):
        """Test run method with general/unknown command"""
        task = Task(
            id="general-task",
            agent_type="CodeAgent",
            command="unknown_command",
            context={}
        )
        
        with patch.object(self.agent, '_general_code_task') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="General task completed")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_exception(self):
        """Test run method handles exceptions and returns error result"""
        task = Task(
            id="error-task",
            agent_type="CodeAgent",
            command="implement",
            context={}
        )
        
        with patch.object(self.agent, '_implement_feature') as mock_method:
            mock_method.side_effect = Exception("Test exception")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is False
            assert "Test exception" in result.error
            assert result.execution_time > 0


class TestFeatureImplementation:
    """Test CodeAgent feature implementation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_claude_client = AsyncMock()
        self.agent = CodeAgent(claude_code_client=self.mock_claude_client)
    
    @pytest.mark.asyncio
    async def test_implement_feature_dry_run(self):
        """Test _implement_feature in dry run mode"""
        task = Task(
            id="feature-task",
            agent_type="CodeAgent",
            command="implement",
            context={
                "specification": "User authentication system",
                "target_file": "auth.py"
            }
        )
        
        result = await self.agent._implement_feature(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "auth.py" in result.artifacts
        assert "# Generated feature implementation" in result.artifacts["auth.py"]
    
    @pytest.mark.asyncio
    async def test_implement_feature_with_claude_client(self):
        """Test _implement_feature with Claude client"""
        task = Task(
            id="feature-task",
            agent_type="CodeAgent",
            command="implement",
            context={
                "specification": "User registration API",
                "target_file": "registration.py",
                "language": "python",
                "framework": "FastAPI"
            }
        )
        
        self.mock_claude_client.generate_code.return_value = "Generated registration code"
        
        with patch.object(self.agent, '_write_code_file') as mock_write:
            result = await self.agent._implement_feature(task, dry_run=False)
            
            assert result.success is True
            assert "Feature implemented: User registration API" in result.output
            assert "registration.py" in result.artifacts
            assert result.artifacts["registration.py"] == "Generated registration code"
            
            self.mock_claude_client.generate_code.assert_called_once()
            mock_write.assert_called_once_with("registration.py", "Generated registration code")
    
    @pytest.mark.asyncio
    async def test_implement_feature_claude_client_fallback(self):
        """Test _implement_feature fallback when Claude client fails"""
        task = Task(
            id="feature-task",
            agent_type="CodeAgent",
            command="implement",
            context={
                "specification": "Password reset",
                "target_file": "password_reset.py"
            }
        )
        
        self.mock_claude_client.generate_code.side_effect = Exception("Claude error")
        
        with patch.object(self.agent, '_write_code_file') as mock_write:
            result = await self.agent._implement_feature(task, dry_run=False)
            
            assert result.success is True
            assert "Feature implemented: Password reset" in result.output
            assert "password_reset.py" in result.artifacts
            mock_write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_implement_feature_no_target_file(self):
        """Test _implement_feature without target file"""
        task = Task(
            id="feature-task",
            agent_type="CodeAgent",
            command="implement",
            context={"specification": "Generic feature"}
        )
        
        self.mock_claude_client.generate_code.return_value = "Generic feature code"
        
        result = await self.agent._implement_feature(task, dry_run=False)
        
        assert result.success is True
        assert "feature.py" in result.artifacts  # Default filename
    
    def test_generate_feature_code(self):
        """Test _generate_feature_code method"""
        specification = "User profile management"
        target_file = "profile.py"
        
        code = self.agent._generate_feature_code(specification, target_file)
        
        assert "Generated feature implementation" in code
        assert specification in code
        assert "class Feature:" in code
        assert "def execute(self):" in code
        assert "def validate(self):" in code
        assert "if __name__ == \"__main__\":" in code


class TestBugFixing:
    """Test CodeAgent bug fixing functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_fix_bug_dry_run(self):
        """Test _fix_bug in dry run mode"""
        task = Task(
            id="bug-task",
            agent_type="CodeAgent",
            command="fix",
            context={
                "bug_description": "Memory leak in user session handler",
                "file_path": "session.py"
            }
        )
        
        result = await self.agent._fix_bug(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "Memory leak in user session handler" in result.output
    
    @pytest.mark.asyncio
    async def test_fix_bug_normal(self):
        """Test _fix_bug in normal mode"""
        task = Task(
            id="bug-task",
            agent_type="CodeAgent",
            command="fix",
            context={
                "bug_description": "Database connection not closed",
                "file_path": "database.py"
            }
        )
        
        with patch.object(self.agent, '_apply_code_changes') as mock_apply:
            result = await self.agent._fix_bug(task, dry_run=False)
            
            assert result.success is True
            assert "Bug fixed: Database connection not closed" in result.output
            assert "database.py" in result.artifacts
            mock_apply.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fix_bug_no_file_path(self):
        """Test _fix_bug without file path"""
        task = Task(
            id="bug-task",
            agent_type="CodeAgent",
            command="fix",
            context={"bug_description": "Logic error in calculation"}
        )
        
        result = await self.agent._fix_bug(task, dry_run=False)
        
        assert result.success is True
        assert result.artifacts == {}
    
    def test_generate_bug_fix(self):
        """Test _generate_bug_fix method"""
        bug_description = "Null pointer exception in user validation"
        file_path = "validation.py"
        
        fix = self.agent._generate_bug_fix(bug_description, file_path)
        
        assert "# Bug Fix Applied" in fix
        assert bug_description in fix
        assert file_path in fix
        assert "def fixed_function():" in fix
        assert "try:" in fix
        assert "except Exception as e:" in fix


class TestCodeRefactoring:
    """Test CodeAgent refactoring functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_refactor_code_dry_run(self):
        """Test _refactor_code in dry run mode"""
        task = Task(
            id="refactor-task",
            agent_type="CodeAgent",
            command="refactor",
            context={
                "code": "legacy spaghetti code",
                "goal": "improve maintainability"
            }
        )
        
        result = await self.agent._refactor_code(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "improve maintainability" in result.output
    
    @pytest.mark.asyncio
    async def test_refactor_code_normal(self):
        """Test _refactor_code in normal mode"""
        task = Task(
            id="refactor-task",
            agent_type="CodeAgent",
            command="refactor",
            context={
                "code": "old code structure",
                "goal": "extract methods"
            }
        )
        
        result = await self.agent._refactor_code(task, dry_run=False)
        
        assert result.success is True
        assert "Code refactored for: extract methods" in result.output
        assert "refactored_code.py" in result.artifacts
    
    def test_perform_refactoring(self):
        """Test _perform_refactoring method"""
        code = "original code to refactor"
        goal = "improve readability"
        
        refactored = self.agent._perform_refactoring(code, goal)
        
        assert "# Refactored Code" in refactored
        assert goal in refactored
        assert f"# Original code length: {len(code)} characters" in refactored
        assert "class RefactoredClass:" in refactored
        assert "def _initialize_components(self):" in refactored
        assert "def _validate_input(self, data):" in refactored


class TestTestCreation:
    """Test CodeAgent test creation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_create_tests_dry_run(self):
        """Test _create_tests in dry run mode"""
        task = Task(
            id="test-task",
            agent_type="CodeAgent",
            command="test",
            context={
                "code": "function to test",
                "test_type": "integration"
            }
        )
        
        result = await self.agent._create_tests(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "integration tests" in result.output
    
    @pytest.mark.asyncio
    async def test_create_tests_normal(self):
        """Test _create_tests in normal mode"""
        task = Task(
            id="test-task",
            agent_type="CodeAgent",
            command="test",
            context={
                "code": "class to test",
                "test_type": "unit"
            }
        )
        
        result = await self.agent._create_tests(task, dry_run=False)
        
        assert result.success is True
        assert "Created unit tests" in result.output
        assert "test_unit.py" in result.artifacts
    
    def test_generate_tests(self):
        """Test _generate_tests method"""
        code = "sample code for testing"
        test_type = "unit"
        
        tests = self.agent._generate_tests(code, test_type)
        
        assert f"Generated {test_type} tests" in tests
        assert "import unittest" in tests
        assert f"class Test{test_type.title()}(unittest.TestCase):" in tests
        assert "def setUp(self):" in tests
        assert "def test_basic_functionality(self):" in tests
        assert "def test_error_handling(self):" in tests
        assert "def test_edge_cases(self):" in tests
        assert "if __name__ == \"__main__\":" in tests


class TestCodeReview:
    """Test CodeAgent code review functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_review_code_dry_run(self):
        """Test _review_code in dry run mode"""
        task = Task(
            id="review-task",
            agent_type="CodeAgent",
            command="review",
            context={"code": "code to review"}
        )
        
        result = await self.agent._review_code(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "13 characters" in result.output  # Length of "code to review"
    
    @pytest.mark.asyncio
    async def test_review_code_normal(self):
        """Test _review_code in normal mode"""
        task = Task(
            id="review-task",
            agent_type="CodeAgent",
            command="review",
            context={"code": "def function(): pass"}
        )
        
        result = await self.agent._review_code(task, dry_run=False)
        
        assert result.success is True
        assert "Code review completed" in result.output
        assert "code-review.md" in result.artifacts
    
    def test_analyze_code_quality(self):
        """Test _analyze_code_quality method"""
        code = "sample code for quality analysis"
        
        analysis = self.agent._analyze_code_quality(code)
        
        assert "# Code Review Report" in analysis
        assert "## Overview" in analysis
        assert f"Code analysis for {len(code)} characters" in analysis
        assert "## Quality Metrics" in analysis
        assert "## Issues Found" in analysis
        assert "## Recommendations" in analysis
        assert "## Security Considerations" in analysis
        assert "## Performance Notes" in analysis
        assert "## Overall Score:" in analysis


class TestCodeOptimization:
    """Test CodeAgent optimization functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_optimize_code_dry_run(self):
        """Test _optimize_code in dry run mode"""
        task = Task(
            id="optimize-task",
            agent_type="CodeAgent",
            command="optimize",
            context={
                "code": "unoptimized code",
                "target": "memory usage"
            }
        )
        
        result = await self.agent._optimize_code(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "memory usage" in result.output
    
    @pytest.mark.asyncio
    async def test_optimize_code_normal(self):
        """Test _optimize_code in normal mode"""
        task = Task(
            id="optimize-task",
            agent_type="CodeAgent",
            command="optimize",
            context={
                "code": "slow code",
                "target": "performance"
            }
        )
        
        result = await self.agent._optimize_code(task, dry_run=False)
        
        assert result.success is True
        assert "Code optimized for: performance" in result.output
        assert "optimized_code.py" in result.artifacts
    
    def test_apply_optimizations(self):
        """Test _apply_optimizations method"""
        code = "original slow code"
        target = "performance"
        
        optimized = self.agent._apply_optimizations(code, target)
        
        assert f"# Optimized Code - Target: {target}" in optimized
        assert "import asyncio" in optimized
        assert "from functools import lru_cache" in optimized
        assert "class OptimizedClass:" in optimized
        assert "@lru_cache(maxsize=128)" in optimized
        assert "async def async_operation" in optimized
        assert "def batch_operation" in optimized


class TestFileOperations:
    """Test CodeAgent file operation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_write_code_file_creates_directory(self):
        """Test _write_code_file creates directory if needed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "new_dir", "test_file.py")
            content = "test content"
            
            await self.agent._write_code_file(filepath, content)
            
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                assert f.read() == content
    
    @pytest.mark.asyncio
    async def test_write_code_file_overwrites_existing(self):
        """Test _write_code_file overwrites existing file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as temp_file:
            temp_file.write("original content")
            temp_file.flush()
            
            new_content = "new content"
            await self.agent._write_code_file(temp_file.name, new_content)
            
            with open(temp_file.name, 'r') as f:
                assert f.read() == new_content
            
            os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_apply_code_changes(self):
        """Test _apply_code_changes calls _write_code_file"""
        filepath = "test_file.py"
        changes = "updated code"
        
        with patch.object(self.agent, '_write_code_file') as mock_write:
            await self.agent._apply_code_changes(filepath, changes)
            
            mock_write.assert_called_once_with(filepath, changes)


class TestGeneralCodeTasks:
    """Test CodeAgent general task functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_general_code_task_dry_run(self):
        """Test _general_code_task in dry run mode"""
        task = Task(
            id="general-task",
            agent_type="CodeAgent",
            command="custom_code_command",
            context={}
        )
        
        result = await self.agent._general_code_task(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "custom_code_command" in result.output
    
    @pytest.mark.asyncio
    async def test_general_code_task_normal(self):
        """Test _general_code_task in normal mode"""
        task = Task(
            id="general-task",
            agent_type="CodeAgent",
            command="another_command",
            context={}
        )
        
        result = await self.agent._general_code_task(task, dry_run=False)
        
        assert result.success is True
        assert "CodeAgent executed: another_command" in result.output


class TestTDDMinimalImplementation:
    """Test CodeAgent TDD minimal implementation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_implement_minimal_solution_dry_run(self):
        """Test _implement_minimal_solution in dry run mode"""
        task = Task(
            id="minimal-task",
            agent_type="CodeAgent",
            command="implement_minimal_solution",
            context={
                "failing_tests": ["test_user.py", "test_auth.py"],
                "test_files": ["test_user.py", "test_auth.py"],
                "story_id": "user-authentication"
            }
        )
        
        result = await self.agent._implement_minimal_solution(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "2 test files" in result.output
        assert "minimal_implementation.py" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_implement_minimal_solution_normal(self):
        """Test _implement_minimal_solution in normal mode"""
        task = Task(
            id="minimal-task",
            agent_type="CodeAgent",
            command="implement_minimal_solution",
            context={
                "failing_tests": ["test_login.py"],
                "test_files": ["test_login.py"],
                "story_id": "login-feature"
            }
        )
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            with patch.object(self.agent, '_analyze_failing_tests') as mock_analyze:
                with patch.object(self.agent, '_generate_minimal_implementation') as mock_generate:
                    with patch.object(self.agent, '_run_tests_against_implementation') as mock_run_tests:
                        with patch.object(self.agent, '_write_implementation_files') as mock_write:
                            
                            # Setup mocks
                            mock_analyze.return_value = {"required_classes": ["User"]}
                            mock_generate.return_value = {"src/login.py": "minimal login code"}
                            mock_run_tests.return_value = {
                                "all_passing": True,
                                "total_tests": 5,
                                "passing_tests": 5,
                                "failing_tests": 0,
                                "test_errors": 0
                            }
                            mock_write.return_value = {"src/login.py": "minimal login code"}
                            
                            result = await self.agent._implement_minimal_solution(task, dry_run=False)
                            
                            assert result.success is True
                            assert "TDD Minimal Implementation Complete" in result.output
                            assert "Ready for REFACTOR Phase" in result.output
                            assert "src/login.py" in result.artifacts
                            assert "test_results.json" in result.artifacts
                            
                            mock_log.assert_called()
                            mock_analyze.assert_called_once()
                            mock_generate.assert_called_once()
                            mock_run_tests.assert_called_once()
                            mock_write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_failing_tests(self):
        """Test _analyze_failing_tests method"""
        test_files = ["test_user.py", "test_auth.py"]
        
        result = await self.agent._analyze_failing_tests(test_files)
        
        assert isinstance(result, dict)
        assert "required_classes" in result
        assert "required_methods" in result
        assert "required_interfaces" in result
        assert "data_models" in result
        assert "error_types" in result
        assert "test_expectations" in result
    
    @pytest.mark.asyncio
    async def test_generate_minimal_implementation(self):
        """Test _generate_minimal_implementation method"""
        test_analysis = {
            "required_classes": ["User", "Auth"],
            "required_interfaces": ["UserRepository"],
            "data_models": ["UserModel"],
            "requires_persistence": True,
            "requires_api": True
        }
        story_id = "user-management"
        
        implementation = await self.agent._generate_minimal_implementation(test_analysis, story_id)
        
        assert isinstance(implementation, dict)
        assert f"src/{story_id}_module.py" in implementation
        assert f"src/{story_id}_interfaces.py" in implementation
        assert f"src/{story_id}_models.py" in implementation
        assert f"src/{story_id}_repository.py" in implementation
        assert f"src/{story_id}_api.py" in implementation
    
    def test_generate_main_module(self):
        """Test _generate_main_module method"""
        test_analysis = {"required_classes": ["Service"]}
        story_id = "test-feature"
        
        module_code = self.agent._generate_main_module(test_analysis, story_id)
        
        assert f"{story_id.title()} Module" in module_code
        assert f"class {story_id.title()}Exception(Exception):" in module_code
        assert f"class {story_id.title()}Model:" in module_code
        assert f"class {story_id.title()}Service:" in module_code
        assert "def create_item(self" in module_code
        assert "def get_item(self" in module_code
        assert "def update_item(self" in module_code
        assert "def delete_item(self" in module_code
        assert "def list_items(self" in module_code
    
    def test_generate_interfaces(self):
        """Test _generate_interfaces method"""
        test_analysis = {}
        story_id = "feature"
        
        interfaces_code = self.agent._generate_interfaces(test_analysis, story_id)
        
        assert f"{story_id.title()} Interfaces" in interfaces_code
        assert f"class {story_id.title()}Repository(ABC):" in interfaces_code
        assert f"class {story_id.title()}EventBus(ABC):" in interfaces_code
        assert f"class {story_id.title()}Validator(ABC):" in interfaces_code
        assert "@abstractmethod" in interfaces_code
    
    def test_generate_models(self):
        """Test _generate_models method"""
        test_analysis = {}
        story_id = "feature"
        
        models_code = self.agent._generate_models(test_analysis, story_id)
        
        assert f"{story_id.title()} Data Models" in models_code
        assert f"class {story_id.title()}Data:" in models_code
        assert f"class {story_id.title()}Request:" in models_code
        assert f"class {story_id.title()}Response:" in models_code
        assert "@dataclass" in models_code
        assert "from datetime import datetime" in models_code
    
    def test_generate_repository(self):
        """Test _generate_repository method"""
        test_analysis = {}
        story_id = "feature"
        
        repository_code = self.agent._generate_repository(test_analysis, story_id)
        
        assert f"{story_id.title()} Repository" in repository_code
        assert f"class {story_id.title()}FileRepository:" in repository_code
        assert "def save(self, item: Any) -> bool:" in repository_code
        assert "def find_by_id(self, item_id: str)" in repository_code
        assert "def find_all(self)" in repository_code
        assert "def delete(self, item_id: str)" in repository_code
    
    def test_generate_api_layer(self):
        """Test _generate_api_layer method"""
        test_analysis = {}
        story_id = "feature"
        
        api_code = self.agent._generate_api_layer(test_analysis, story_id)
        
        assert f"{story_id.title()} API Layer" in api_code
        assert f"class {story_id.title()}API:" in api_code
        assert "def create(self, data: Dict[str, Any])" in api_code
        assert "def get(self, item_id: str)" in api_code
        assert "def update(self, item_id: str" in api_code
        assert "def delete(self, item_id: str" in api_code
        assert "def list(self, limit: int = 100" in api_code
    
    @pytest.mark.asyncio
    async def test_run_tests_against_implementation(self):
        """Test _run_tests_against_implementation method"""
        test_files = ["test1.py", "test2.py"]
        implementation = {"impl.py": "code"}
        
        result = await self.agent._run_tests_against_implementation(test_files, implementation)
        
        assert result["all_passing"] is True
        assert result["total_tests"] == 15
        assert result["passing_tests"] == 15
        assert result["failing_tests"] == 0
        assert result["test_errors"] == 0
        assert result["coverage_percentage"] == 95.0
    
    @pytest.mark.asyncio
    async def test_write_implementation_files(self):
        """Test _write_implementation_files method"""
        implementation = {
            "src/module.py": "module code",
            "src/models.py": "models code"
        }
        story_id = "test-story"
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            result = await self.agent._write_implementation_files(implementation, story_id)
            
            assert result == implementation
            assert mock_log.call_count == 2  # One call per file


class TestTDDGreenStateValidation:
    """Test CodeAgent TDD green state validation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_validate_test_green_state_dry_run(self):
        """Test _validate_test_green_state in dry run mode"""
        task = Task(
            id="green-task",
            agent_type="CodeAgent",
            command="validate_test_green_state",
            context={
                "test_files": ["test1.py", "test2.py"],
                "implementation_files": ["impl1.py", "impl2.py"],
                "story_id": "validation-story"
            }
        )
        
        result = await self.agent._validate_test_green_state(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "2 test files" in result.output
    
    @pytest.mark.asyncio
    async def test_validate_test_green_state_normal(self):
        """Test _validate_test_green_state in normal mode"""
        task = Task(
            id="green-task",
            agent_type="CodeAgent",
            command="validate_test_green_state",
            context={
                "test_files": ["test.py"],
                "implementation_files": ["impl.py"],
                "story_id": "green-validation"
            }
        )
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            with patch.object(self.agent, '_run_comprehensive_test_suite') as mock_run_tests:
                with patch.object(self.agent, '_validate_test_integrity') as mock_validate_integrity:
                    with patch.object(self.agent, '_analyze_implementation_quality') as mock_analyze_quality:
                        
                        # Setup mocks
                        mock_run_tests.return_value = {
                            "total_tests": 10,
                            "passing_tests": 10,
                            "failing_tests": 0,
                            "test_errors": 0,
                            "coverage_percentage": 95.0
                        }
                        mock_validate_integrity.return_value = {
                            "tests_preserved": True
                        }
                        mock_analyze_quality.return_value = {
                            "overall_score": 8.5,
                            "complexity": 7,
                            "maintainability": 9,
                            "test_coverage": 95.0
                        }
                        
                        result = await self.agent._validate_test_green_state(task, dry_run=False)
                        
                        assert result.success is True
                        assert "TDD GREEN State Validation" in result.output
                        assert "All tests passing: True ✓" in result.output
                        assert "Ready for REFACTOR Phase: True" in result.output
                        assert "green_state_validation.json" in result.artifacts
                        
                        mock_log.assert_called()
                        mock_run_tests.assert_called_once()
                        mock_validate_integrity.assert_called_once()
                        mock_analyze_quality.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_comprehensive_test_suite(self):
        """Test _run_comprehensive_test_suite method"""
        test_files = ["test1.py", "test2.py"]
        implementation_files = ["impl1.py", "impl2.py"]
        
        result = await self.agent._run_comprehensive_test_suite(test_files, implementation_files)
        
        assert result["total_tests"] == 20
        assert result["passing_tests"] == 20
        assert result["failing_tests"] == 0
        assert result["test_errors"] == 0
        assert result["coverage_percentage"] == 96.5
        assert "test_duration" in result
    
    @pytest.mark.asyncio
    async def test_validate_test_integrity(self):
        """Test _validate_test_integrity method"""
        test_files = ["test1.py", "test2.py"]
        
        result = await self.agent._validate_test_integrity(test_files)
        
        assert result["tests_preserved"] is True
        assert result["modified_files"] == []
        assert result["checksum_matches"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_implementation_quality(self):
        """Test _analyze_implementation_quality method"""
        implementation_files = ["impl1.py", "impl2.py"]
        
        result = await self.agent._analyze_implementation_quality(implementation_files)
        
        assert result["overall_score"] == 8.5
        assert result["complexity"] == 7
        assert result["maintainability"] == 9
        assert result["test_coverage"] == 96.5
        assert "code_smells" in result
        assert "cyclomatic_complexity" in result


class TestTDDPhaseExecution:
    """Test CodeAgent TDD phase execution functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_code_green(self):
        """Test execute_tdd_phase for CODE_GREEN phase"""
        context = {
            "test_files": ["test.py"],
            "failing_tests": ["test_login"],
            "story_id": "login-feature",
            "dry_run": False
        }
        
        with patch.object(self.agent, '_execute_code_green_phase') as mock_execute:
            mock_execute.return_value = AgentResult(success=True, output="CODE_GREEN complete")
            
            result = await self.agent.execute_tdd_phase(TDDState.CODE_GREEN, context)
            
            assert result.success is True
            assert result.output == "CODE_GREEN complete"
            mock_execute.assert_called_once_with(context)
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_refactor(self):
        """Test execute_tdd_phase for REFACTOR phase"""
        context = {
            "implementation_files": ["impl.py"],
            "story_id": "refactor-story"
        }
        
        with patch.object(self.agent, '_execute_refactor_phase') as mock_execute:
            mock_execute.return_value = AgentResult(success=True, output="REFACTOR complete")
            
            result = await self.agent.execute_tdd_phase(TDDState.REFACTOR, context)
            
            assert result.success is True
            assert result.output == "REFACTOR complete"
            mock_execute.assert_called_once_with(context)
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_commit(self):
        """Test execute_tdd_phase for COMMIT phase"""
        context = {
            "implementation_files": ["impl.py"],
            "test_files": ["test.py"],
            "story_id": "commit-story"
        }
        
        with patch.object(self.agent, '_execute_commit_phase') as mock_execute:
            mock_execute.return_value = AgentResult(success=True, output="COMMIT complete")
            
            result = await self.agent.execute_tdd_phase(TDDState.COMMIT, context)
            
            assert result.success is True
            assert result.output == "COMMIT complete"
            mock_execute.assert_called_once_with(context)
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_wrong_phase(self):
        """Test execute_tdd_phase with unsupported phase"""
        result = await self.agent.execute_tdd_phase(TDDState.DESIGN, {})
        
        assert result.success is False
        assert "can execute CODE_GREEN, REFACTOR, or COMMIT phases" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_code_green_phase(self):
        """Test _execute_code_green_phase method"""
        context = {
            "test_files": ["test.py"],
            "failing_tests": ["test1"],
            "story_id": "feature"
        }
        
        with patch.object(self.agent, '_implement_minimal_solution') as mock_implement:
            with patch.object(self.agent, '_validate_test_green_state') as mock_validate:
                
                # Setup mocks
                mock_implement.return_value = AgentResult(
                    success=True, 
                    output="Implementation complete",
                    artifacts={"impl.py": "code"}
                )
                mock_validate.return_value = AgentResult(
                    success=True,
                    output="Validation complete",
                    artifacts={"validation.json": "{}"}
                )
                
                result = await self.agent._execute_code_green_phase(context)
                
                assert result.success is True
                assert "TDD CODE_GREEN Phase Complete" in result.output
                assert "Ready for REFACTOR Phase" in result.output
                assert "impl.py" in result.artifacts
                assert "validation.json" in result.artifacts
                
                mock_implement.assert_called_once()
                mock_validate.assert_called_once()


class TestTDDRefactoring:
    """Test CodeAgent TDD refactoring functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_refactor_implementation_dry_run(self):
        """Test _refactor_implementation in dry run mode"""
        task = Task(
            id="refactor-task",
            agent_type="CodeAgent",
            command="refactor_implementation",
            context={
                "implementation_files": ["impl1.py", "impl2.py"],
                "refactor_goals": ["improve_readability", "reduce_complexity"],
                "story_id": "refactor-story"
            }
        )
        
        result = await self.agent._refactor_implementation(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "2 files" in result.output
        assert "improve_readability" in result.output
        assert "reduce_complexity" in result.output
        assert "refactored_code.py" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_refactor_implementation_normal(self):
        """Test _refactor_implementation in normal mode"""
        task = Task(
            id="refactor-task",
            agent_type="CodeAgent",
            command="refactor_implementation",
            context={
                "implementation_files": ["impl.py"],
                "refactor_goals": ["improve_readability"],
                "story_id": "refactor-feature"
            }
        )
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            with patch.object(self.agent, '_analyze_refactor_opportunities') as mock_analyze:
                with patch.object(self.agent, '_apply_refactoring_strategies') as mock_apply:
                    with patch.object(self.agent, '_validate_refactoring_preserves_tests') as mock_validate:
                        with patch.object(self.agent, '_measure_quality_improvement') as mock_measure:
                            
                            # Setup mocks
                            mock_analyze.return_value = {"code_smells": ["long_method"]}
                            mock_apply.return_value = {"impl.py": "refactored code"}
                            mock_validate.return_value = {"all_tests_pass": True}
                            mock_measure.return_value = {
                                "complexity_reduction": 25.0,
                                "maintainability_increase": 30.0,
                                "duplication_reduction": 40.0,
                                "test_coverage": 96.5
                            }
                            
                            result = await self.agent._refactor_implementation(task, dry_run=False)
                            
                            assert result.success is True
                            assert "TDD Refactoring Complete" in result.output
                            assert "Ready for COMMIT Phase" in result.output
                            assert "impl.py" in result.artifacts
                            assert "refactor_report.json" in result.artifacts
                            
                            mock_log.assert_called()
                            mock_analyze.assert_called_once()
                            mock_apply.assert_called_once()
                            mock_validate.assert_called_once()
                            mock_measure.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_refactor_opportunities(self):
        """Test _analyze_refactor_opportunities method"""
        implementation_files = ["impl1.py", "impl2.py"]
        
        result = await self.agent._analyze_refactor_opportunities(implementation_files)
        
        assert "code_smells" in result
        assert "complexity_hotspots" in result
        assert "improvement_opportunities" in result
        assert "maintainability_score" in result
    
    @pytest.mark.asyncio
    async def test_apply_refactoring_strategies(self):
        """Test _apply_refactoring_strategies method"""
        implementation_files = ["impl1.py", "impl2.py"]
        goals = ["improve_readability", "reduce_complexity"]
        analysis = {"code_smells": ["long_method"]}
        
        result = await self.agent._apply_refactoring_strategies(implementation_files, goals, analysis)
        
        assert isinstance(result, dict)
        assert len(result) == len(implementation_files)
        for file_path in implementation_files:
            assert file_path in result
            assert "Refactored version" in result[file_path]
            assert "improve_readability, reduce_complexity" in result[file_path]
    
    @pytest.mark.asyncio
    async def test_validate_refactoring_preserves_tests(self):
        """Test _validate_refactoring_preserves_tests method"""
        refactored_code = {"impl.py": "refactored code"}
        
        result = await self.agent._validate_refactoring_preserves_tests(refactored_code)
        
        assert result["all_tests_pass"] is True
        assert result["total_tests"] == 20
        assert result["passing_tests"] == 20
        assert result["failing_tests"] == 0
        assert result["refactoring_safe"] is True
    
    @pytest.mark.asyncio
    async def test_measure_quality_improvement(self):
        """Test _measure_quality_improvement method"""
        original_files = ["original1.py", "original2.py"]
        refactored_files = {"refactored1.py": "code", "refactored2.py": "code"}
        
        result = await self.agent._measure_quality_improvement(original_files, refactored_files)
        
        assert result["complexity_reduction"] == 25.0
        assert result["maintainability_increase"] == 30.0
        assert result["duplication_reduction"] == 40.0
        assert result["test_coverage"] == 96.5
        assert result["overall_improvement"] == 28.5


class TestTDDCommitPhase:
    """Test CodeAgent TDD commit phase functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = CodeAgent()
    
    @pytest.mark.asyncio
    async def test_commit_tdd_cycle_dry_run(self):
        """Test _commit_tdd_cycle in dry run mode"""
        task = Task(
            id="commit-task",
            agent_type="CodeAgent",
            command="commit_tdd_cycle",
            context={
                "implementation_files": ["impl1.py", "impl2.py"],
                "test_files": ["test1.py", "test2.py"],
                "story_id": "commit-story",
                "commit_message": "Complete TDD cycle for feature"
            }
        )
        
        result = await self.agent._commit_tdd_cycle(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "2 impl files + 2 test files" in result.output
        assert "commit_summary.txt" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_commit_tdd_cycle_normal_success(self):
        """Test _commit_tdd_cycle in normal mode with successful commit"""
        task = Task(
            id="commit-task",
            agent_type="CodeAgent",
            command="commit_tdd_cycle",
            context={
                "implementation_files": ["impl.py"],
                "test_files": ["test.py"],
                "story_id": "feature",
                "commit_message": "Complete feature implementation"
            }
        )
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            with patch.object(self.agent, '_perform_final_validation') as mock_validate:
                with patch.object(self.agent, '_prepare_tdd_commit') as mock_prepare:
                    with patch.object(self.agent, '_execute_git_commit') as mock_commit:
                        
                        # Setup mocks
                        mock_validate.return_value = {
                            "ready_for_commit": True,
                            "all_tests_pass": True,
                            "quality_validated": True,
                            "clean_working_directory": True,
                            "cycle_complete": True
                        }
                        mock_prepare.return_value = {
                            "files_to_stage": ["impl.py", "test.py"],
                            "commit_type": "feat",
                            "scope": "feature"
                        }
                        mock_commit.return_value = {
                            "success": True,
                            "commit_hash": "abc123",
                            "branch": "main",
                            "files_staged": 2
                        }
                        
                        result = await self.agent._commit_tdd_cycle(task, dry_run=False)
                        
                        assert result.success is True
                        assert "TDD Commit Phase Complete" in result.output
                        assert "Final validation: True ✓" in result.output
                        assert "Git commit: True ✓" in result.output
                        assert "commit_details.json" in result.artifacts
                        
                        mock_log.assert_called()
                        mock_validate.assert_called_once()
                        mock_prepare.assert_called_once()
                        mock_commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_commit_tdd_cycle_validation_failure(self):
        """Test _commit_tdd_cycle with validation failure"""
        task = Task(
            id="commit-task",
            agent_type="CodeAgent",
            command="commit_tdd_cycle",
            context={
                "implementation_files": ["impl.py"],
                "test_files": ["test.py"],
                "story_id": "feature"
            }
        )
        
        with patch.object(self.agent, '_perform_final_validation') as mock_validate:
            mock_validate.return_value = {"ready_for_commit": False}
            
            result = await self.agent._commit_tdd_cycle(task, dry_run=False)
            
            assert result.success is False  # Should fail when validation fails
    
    @pytest.mark.asyncio
    async def test_perform_final_validation(self):
        """Test _perform_final_validation method"""
        implementation_files = ["impl.py"]
        test_files = ["test.py"]
        
        result = await self.agent._perform_final_validation(implementation_files, test_files)
        
        assert result["ready_for_commit"] is True
        assert result["all_tests_pass"] is True
        assert result["quality_validated"] is True
        assert result["clean_working_directory"] is True
        assert result["cycle_complete"] is True
    
    @pytest.mark.asyncio
    async def test_prepare_tdd_commit(self):
        """Test _prepare_tdd_commit method"""
        implementation_files = ["impl1.py", "impl2.py"]
        test_files = ["test1.py", "test2.py"]
        story_id = "feature-123"
        
        result = await self.agent._prepare_tdd_commit(implementation_files, test_files, story_id)
        
        assert result["files_to_stage"] == implementation_files + test_files
        assert result["commit_type"] == "feat"
        assert result["scope"] == story_id
        assert result["breaking_changes"] is False
    
    @pytest.mark.asyncio
    async def test_execute_git_commit(self):
        """Test _execute_git_commit method"""
        message = "feat: Complete TDD cycle"
        preparation = {"files_to_stage": ["impl.py", "test.py"]}
        
        result = await self.agent._execute_git_commit(message, preparation)
        
        assert result["success"] is True
        assert result["commit_hash"] == "abc123def456"
        assert result["branch"] == "main"
        assert result["files_staged"] == 2
        assert result["commit_message"] == message
    
    @pytest.mark.asyncio
    async def test_execute_commit_phase(self):
        """Test _execute_commit_phase method"""
        context = {
            "implementation_files": ["impl.py"],
            "test_files": ["test.py"],
            "story_id": "complete-feature"
        }
        
        with patch.object(self.agent, '_commit_tdd_cycle') as mock_commit:
            mock_commit.return_value = AgentResult(
                success=True,
                output="Commit complete",
                artifacts={"commit.json": "{}"}
            )
            
            result = await self.agent._execute_commit_phase(context)
            
            assert result.success is True
            assert "TDD COMMIT Phase Complete" in result.output
            assert "TDD Process Complete" in result.output
            assert result.artifacts == {"commit.json": "{}"}
            
            mock_commit.assert_called_once()
            
            # Verify commit message format
            commit_task = mock_commit.call_args[0][0]
            assert "feat: Complete TDD implementation for complete-feature" in commit_task.context["commit_message"]
            assert "Closes #complete-feature" in commit_task.context["commit_message"]


if __name__ == "__main__":
    pytest.main([__file__])