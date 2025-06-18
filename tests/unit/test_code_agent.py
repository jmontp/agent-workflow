"""
Unit tests for Code Agent.

Tests the AI agent specialized in code implementation and development,
including TDD-specific functionality for RED-GREEN-REFACTOR cycles.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agents.code_agent import CodeAgent
from lib.agents import Task, AgentResult, TDDState
from lib.agent_tool_config import AgentType


class TestCodeAgent:
    """Test the CodeAgent class."""
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create a mock Claude client."""
        mock_client = Mock()
        mock_client.generate_code = AsyncMock(return_value="# Generated code")
        return mock_client
    
    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        return Mock()
    
    @pytest.fixture
    def code_agent(self, mock_claude_client, mock_github_client):
        """Create a CodeAgent for testing."""
        return CodeAgent(
            claude_code_client=mock_claude_client,
            github_client=mock_github_client
        )
    
    def test_code_agent_init(self, code_agent, mock_claude_client, mock_github_client):
        """Test CodeAgent initialization."""
        assert code_agent.name == "CodeAgent"
        assert code_agent.claude_client == mock_claude_client
        assert code_agent.github_client == mock_github_client
        
        # Check capabilities
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
            assert capability in code_agent.capabilities

    @pytest.mark.asyncio
    async def test_implement_feature_dry_run(self, code_agent):
        """Test feature implementation in dry run mode."""
        task = Task(
            id="test-1",
            agent_type="CodeAgent",
            command="implement feature",
            context={
                "specification": "Create a user authentication system",
                "target_file": "auth.py",
                "language": "python"
            }
        )
        
        result = await code_agent.run(task, dry_run=True)
        
        assert result.success
        assert "[DRY RUN]" in result.output
        assert "auth.py" in result.artifacts
        assert "# Generated feature implementation" in result.artifacts["auth.py"]

    @pytest.mark.asyncio
    async def test_implement_feature_with_claude(self, code_agent, mock_claude_client):
        """Test feature implementation using Claude client."""
        mock_claude_client.generate_code.return_value = "def authenticate(user): return True"
        
        task = Task(
            id="test-2",
            agent_type="CodeAgent", 
            command="implement feature",
            context={
                "specification": "User login function",
                "target_file": "login.py"
            }
        )
        
        with patch.object(code_agent, '_write_code_file', new_callable=AsyncMock) as mock_write:
            result = await code_agent.run(task, dry_run=False)
            
            assert result.success
            assert "Feature implemented" in result.output
            assert "login.py" in result.artifacts
            mock_claude_client.generate_code.assert_called_once()
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_implement_feature_fallback(self, code_agent, mock_claude_client):
        """Test feature implementation fallback when Claude is unavailable."""
        mock_claude_client.generate_code.side_effect = Exception("Claude unavailable")
        
        task = Task(
            id="test-3",
            agent_type="CodeAgent",
            command="implement feature", 
            context={
                "specification": "User registration",
                "target_file": "register.py"
            }
        )
        
        with patch.object(code_agent, '_write_code_file', new_callable=AsyncMock):
            result = await code_agent.run(task, dry_run=False)
            
            assert result.success
            assert "Feature implemented" in result.output
            assert "class Feature:" in result.artifacts["register.py"]

    @pytest.mark.asyncio
    async def test_fix_bug_dry_run(self, code_agent):
        """Test bug fixing in dry run mode."""
        task = Task(
            id="test-4",
            agent_type="CodeAgent",
            command="fix bug",
            context={
                "bug_description": "Null pointer exception in login",
                "file_path": "auth.py"
            }
        )
        
        result = await code_agent.run(task, dry_run=True)
        
        assert result.success
        assert "[DRY RUN]" in result.output
        assert "fix bug" in result.output

    @pytest.mark.asyncio
    async def test_fix_bug_implementation(self, code_agent):
        """Test bug fixing implementation."""
        task = Task(
            id="test-5",
            agent_type="CodeAgent",
            command="fix bug in authentication",
            context={
                "bug_description": "Password validation fails",
                "file_path": "auth.py"
            }
        )
        
        with patch.object(code_agent, '_apply_code_changes', new_callable=AsyncMock):
            result = await code_agent.run(task, dry_run=False)
            
            assert result.success
            assert "Bug fixed" in result.output
            assert "auth.py" in result.artifacts

    @pytest.mark.asyncio
    async def test_refactor_code(self, code_agent):
        """Test code refactoring functionality."""
        task = Task(
            id="test-6", 
            agent_type="CodeAgent",
            command="refactor code",
            context={
                "code": "def old_function(): pass",
                "goal": "improve maintainability"
            }
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "refactored for: improve maintainability" in result.output
        assert "refactored_code.py" in result.artifacts
        assert "RefactoredClass" in result.artifacts["refactored_code.py"]

    @pytest.mark.asyncio
    async def test_create_tests(self, code_agent):
        """Test test creation functionality."""
        task = Task(
            id="test-7",
            agent_type="CodeAgent",
            command="create tests",
            context={
                "code": "def calculate(a, b): return a + b",
                "test_type": "unit"
            }
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "Created unit tests" in result.output
        assert "test_unit.py" in result.artifacts
        assert "unittest" in result.artifacts["test_unit.py"]

    @pytest.mark.asyncio
    async def test_review_code(self, code_agent):
        """Test code review functionality."""
        task = Task(
            id="test-8",
            agent_type="CodeAgent",
            command="review code quality",
            context={
                "code": "def example(): return 'hello'"
            }
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "Code review completed" in result.output
        assert "code-review.md" in result.artifacts
        assert "Quality Metrics" in result.artifacts["code-review.md"]

    @pytest.mark.asyncio
    async def test_optimize_code(self, code_agent):
        """Test code optimization functionality."""
        task = Task(
            id="test-9",
            agent_type="CodeAgent",
            command="optimize for performance",
            context={
                "code": "def slow_function(): return sum(range(1000))",
                "target": "performance"
            }
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "optimized for: performance" in result.output
        assert "optimized_code.py" in result.artifacts
        assert "lru_cache" in result.artifacts["optimized_code.py"]

    @pytest.mark.asyncio
    async def test_general_code_task(self, code_agent):
        """Test handling of general code tasks."""
        task = Task(
            id="test-10",
            agent_type="CodeAgent",
            command="custom code operation",
            context={}
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "CodeAgent executed: custom code operation" in result.output

    @pytest.mark.asyncio
    async def test_error_handling(self, code_agent):
        """Test error handling during task execution."""
        task = Task(
            id="test-11",
            agent_type="CodeAgent",
            command="implement feature",
            context={"specification": "test"}
        )
        
        with patch.object(code_agent, '_implement_feature', side_effect=Exception("Test error")):
            result = await code_agent.run(task, dry_run=False)
            
            assert not result.success
            assert "Test error" in result.error
            assert result.execution_time > 0

    # TDD-specific tests
    
    @pytest.mark.asyncio
    async def test_implement_minimal_solution_dry_run(self, code_agent):
        """Test minimal solution implementation in dry run mode."""
        task = Task(
            id="tdd-1",
            agent_type="CodeAgent",
            command="implement_minimal_solution",
            context={
                "failing_tests": ["test_user_creation", "test_user_validation"],
                "test_files": ["test_user.py"],
                "story_id": "user_management"
            }
        )
        
        result = await code_agent.run(task, dry_run=True)
        
        assert result.success
        assert "[DRY RUN]" in result.output
        assert "minimal_implementation.py" in result.artifacts

    @pytest.mark.asyncio
    async def test_implement_minimal_solution(self, code_agent):
        """Test minimal solution implementation."""
        task = Task(
            id="tdd-2",
            agent_type="CodeAgent",
            command="tdd_implement minimal",
            context={
                "failing_tests": ["test_create_user"],
                "test_files": ["tests/test_user.py"], 
                "story_id": "user_creation"
            }
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "TDD Minimal Implementation Complete" in result.output
        assert "src/user_creation_module.py" in result.artifacts
        assert "test_results.json" in result.artifacts
        
        # Check test results structure
        test_results = json.loads(result.artifacts["test_results.json"])
        assert "all_passing" in test_results
        assert "total_tests" in test_results

    @pytest.mark.asyncio
    async def test_validate_test_green_state_dry_run(self, code_agent):
        """Test GREEN state validation in dry run mode."""
        task = Task(
            id="tdd-3",
            agent_type="CodeAgent",
            command="validate_test_green_state",
            context={
                "test_files": ["test_user.py"],
                "implementation_files": ["user.py"],
                "story_id": "user_management"
            }
        )
        
        result = await code_agent.run(task, dry_run=True)
        
        assert result.success
        assert "[DRY RUN]" in result.output

    @pytest.mark.asyncio
    async def test_validate_test_green_state(self, code_agent):
        """Test GREEN state validation."""
        task = Task(
            id="tdd-4",
            agent_type="CodeAgent",
            command="validate_test_green_state",
            context={
                "test_files": ["tests/test_auth.py"],
                "implementation_files": ["src/auth.py"],
                "story_id": "authentication"
            }
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "TDD GREEN State Validation" in result.output
        assert "green_state_validation.json" in result.artifacts
        
        # Check validation results
        validation_data = json.loads(result.artifacts["green_state_validation.json"])
        assert "test_results" in validation_data
        assert "test_integrity" in validation_data
        assert "quality_metrics" in validation_data

    @pytest.mark.asyncio
    async def test_refactor_implementation_dry_run(self, code_agent):
        """Test refactor implementation in dry run mode."""
        task = Task(
            id="tdd-5",
            agent_type="CodeAgent",
            command="refactor_implementation",
            context={
                "implementation_files": ["src/user.py"],
                "refactor_goals": ["improve_readability", "reduce_complexity"],
                "story_id": "user_management"
            }
        )
        
        result = await code_agent.run(task, dry_run=True)
        
        assert result.success
        assert "[DRY RUN]" in result.output
        assert "refactored_code.py" in result.artifacts

    @pytest.mark.asyncio
    async def test_refactor_implementation(self, code_agent):
        """Test refactor implementation."""
        task = Task(
            id="tdd-6",
            agent_type="CodeAgent",
            command="refactor_implementation",
            context={
                "implementation_files": ["src/auth.py", "src/user.py"],
                "refactor_goals": ["improve_readability", "eliminate_duplication"],
                "story_id": "authentication"
            }
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "TDD Refactoring Complete" in result.output
        assert "refactor_report.json" in result.artifacts
        
        # Check refactor report
        report_data = json.loads(result.artifacts["refactor_report.json"])
        assert "refactor_analysis" in report_data
        assert "quality_improvement" in report_data
        assert "test_results" in report_data

    @pytest.mark.asyncio
    async def test_commit_tdd_cycle_dry_run(self, code_agent):
        """Test TDD cycle commit in dry run mode."""
        task = Task(
            id="tdd-7",
            agent_type="CodeAgent",
            command="commit_tdd_cycle",
            context={
                "implementation_files": ["src/user.py"],
                "test_files": ["tests/test_user.py"],
                "story_id": "user_management",
                "commit_message": "Complete user management TDD cycle"
            }
        )
        
        result = await code_agent.run(task, dry_run=True)
        
        assert result.success
        assert "[DRY RUN]" in result.output
        assert "commit_summary.txt" in result.artifacts

    @pytest.mark.asyncio
    async def test_commit_tdd_cycle(self, code_agent):
        """Test TDD cycle commit."""
        task = Task(
            id="tdd-8",
            agent_type="CodeAgent",
            command="commit_tdd_cycle",
            context={
                "implementation_files": ["src/auth.py", "src/models.py"],
                "test_files": ["tests/test_auth.py", "tests/test_models.py"],
                "story_id": "authentication",
                "commit_message": "feat: Complete authentication TDD cycle"
            }
        )
        
        result = await code_agent.run(task, dry_run=False)
        
        assert result.success
        assert "TDD Commit Phase Complete" in result.output
        assert "commit_details.json" in result.artifacts
        
        # Check commit details
        commit_data = json.loads(result.artifacts["commit_details.json"])
        assert "final_validation" in commit_data
        assert "commit_result" in commit_data
        assert "cycle_summary" in commit_data

    @pytest.mark.asyncio
    async def test_execute_tdd_phase_code_green(self, code_agent):
        """Test executing TDD CODE_GREEN phase."""
        context = {
            "test_files": ["tests/test_feature.py"],
            "failing_tests": ["test_create_feature"],
            "story_id": "feature_creation"
        }
        
        result = await code_agent.execute_tdd_phase(TDDState.CODE_GREEN, context)
        
        assert result.success
        assert "TDD CODE_GREEN Phase Complete" in result.output
        assert "Ready for REFACTOR Phase" in result.output

    @pytest.mark.asyncio
    async def test_execute_tdd_phase_refactor(self, code_agent):
        """Test executing TDD REFACTOR phase."""
        context = {
            "implementation_files": ["src/feature.py"],
            "story_id": "feature_creation",
            "refactor_goals": ["improve_readability"]
        }
        
        result = await code_agent.execute_tdd_phase(TDDState.REFACTOR, context)
        
        assert result.success
        assert "TDD REFACTOR Phase Complete" in result.output
        assert "Ready for COMMIT Phase" in result.output

    @pytest.mark.asyncio
    async def test_execute_tdd_phase_commit(self, code_agent):
        """Test executing TDD COMMIT phase."""
        context = {
            "implementation_files": ["src/feature.py"],
            "test_files": ["tests/test_feature.py"],
            "story_id": "feature_creation"
        }
        
        result = await code_agent.execute_tdd_phase(TDDState.COMMIT, context)
        
        assert result.success
        assert "TDD COMMIT Phase Complete" in result.output
        assert "TDD Process Complete" in result.output

    @pytest.mark.asyncio
    async def test_execute_tdd_phase_invalid(self, code_agent):
        """Test executing invalid TDD phase."""
        context = {"story_id": "test"}
        
        result = await code_agent.execute_tdd_phase(TDDState.DESIGN, context)
        
        assert not result.success
        assert "can execute CODE_GREEN, REFACTOR, or COMMIT phases" in result.error

    # Test helper methods

    @pytest.mark.asyncio
    async def test_write_code_file(self, code_agent):
        """Test writing code to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = f"{temp_dir}/test_code.py"
            content = "def test_function(): pass"
            
            await code_agent._write_code_file(file_path, content)
            
            assert Path(file_path).exists()
            with open(file_path) as f:
                assert f.read() == content

    @pytest.mark.asyncio
    async def test_apply_code_changes(self, code_agent):
        """Test applying code changes to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = f"{temp_dir}/existing_code.py"
            changes = "def updated_function(): return True"
            
            await code_agent._apply_code_changes(file_path, changes)
            
            assert Path(file_path).exists()
            with open(file_path) as f:
                assert f.read() == changes

    def test_generate_feature_code(self, code_agent):
        """Test generating feature code."""
        spec = "User authentication system"
        target_file = "auth.py"
        
        code = code_agent._generate_feature_code(spec, target_file)
        
        assert isinstance(code, str)
        assert "class Feature:" in code
        assert spec in code
        assert "def execute(self):" in code

    def test_generate_bug_fix(self, code_agent):
        """Test generating bug fix code."""
        bug_description = "Null pointer exception"
        file_path = "auth.py"
        
        fix = code_agent._generate_bug_fix(bug_description, file_path)
        
        assert isinstance(fix, str)
        assert bug_description in fix
        assert file_path in fix
        assert "def fixed_function():" in fix

    def test_perform_refactoring(self, code_agent):
        """Test performing code refactoring."""
        code = "def old_function(): pass"
        goal = "improve maintainability"
        
        refactored = code_agent._perform_refactoring(code, goal)
        
        assert isinstance(refactored, str)
        assert goal in refactored
        assert "RefactoredClass" in refactored

    def test_generate_tests(self, code_agent):
        """Test generating test code."""
        code = "def calculate(a, b): return a + b"
        test_type = "unit"
        
        tests = code_agent._generate_tests(code, test_type)
        
        assert isinstance(tests, str)
        assert test_type in tests
        assert "unittest" in tests
        assert "TestUnit" in tests

    def test_analyze_code_quality(self, code_agent):
        """Test analyzing code quality."""
        code = "def example(): return 'test'"
        
        review = code_agent._analyze_code_quality(code)
        
        assert isinstance(review, str)
        assert "Code Review Report" in review
        assert "Quality Metrics" in review
        assert "Recommendations" in review

    def test_apply_optimizations(self, code_agent):
        """Test applying code optimizations."""
        code = "def slow_function(): return sum(range(1000))"
        target = "performance"
        
        optimized = code_agent._apply_optimizations(code, target)
        
        assert isinstance(optimized, str)
        assert target in optimized
        assert "lru_cache" in optimized
        assert "async" in optimized

    def test_generate_main_module(self, code_agent):
        """Test generating main module implementation."""
        test_analysis = {
            "required_classes": ["UserService"],
            "required_methods": ["create_user", "validate_user"]
        }
        story_id = "user_management"
        
        module_code = code_agent._generate_main_module(test_analysis, story_id)
        
        assert isinstance(module_code, str)
        assert f"{story_id.title()}Model" in module_code
        assert f"{story_id.title()}Service" in module_code
        assert "def create_item" in module_code

    def test_generate_interfaces(self, code_agent):
        """Test generating interface definitions."""
        test_analysis = {"required_interfaces": ["Repository", "EventBus"]}
        story_id = "user_management"
        
        interfaces = code_agent._generate_interfaces(test_analysis, story_id)
        
        assert isinstance(interfaces, str)
        assert f"{story_id.title()}Repository" in interfaces
        assert f"{story_id.title()}EventBus" in interfaces
        assert "ABC" in interfaces
        assert "@abstractmethod" in interfaces

    def test_generate_models(self, code_agent):
        """Test generating data models."""
        test_analysis = {"data_models": ["User", "Profile"]}
        story_id = "user_management"
        
        models = code_agent._generate_models(test_analysis, story_id)
        
        assert isinstance(models, str)
        assert f"{story_id.title()}Data" in models
        assert f"{story_id.title()}Request" in models
        assert f"{story_id.title()}Response" in models
        assert "@dataclass" in models

    def test_generate_repository(self, code_agent):
        """Test generating repository implementation."""
        test_analysis = {"requires_persistence": True}
        story_id = "user_management"
        
        repository = code_agent._generate_repository(test_analysis, story_id)
        
        assert isinstance(repository, str)
        assert f"{story_id.title()}FileRepository" in repository
        assert "def save" in repository
        assert "def find_by_id" in repository

    def test_generate_api_layer(self, code_agent):
        """Test generating API layer implementation."""
        test_analysis = {"requires_api": True}
        story_id = "user_management"
        
        api_layer = code_agent._generate_api_layer(test_analysis, story_id)
        
        assert isinstance(api_layer, str)
        assert f"{story_id.title()}API" in api_layer
        assert "def create" in api_layer
        assert "def get" in api_layer
        assert "def update" in api_layer
        assert "def delete" in api_layer

    @pytest.mark.asyncio
    async def test_analyze_failing_tests(self, code_agent):
        """Test analyzing failing tests."""
        test_files = ["test_user.py", "test_auth.py"]
        
        analysis = await code_agent._analyze_failing_tests(test_files)
        
        assert isinstance(analysis, dict)
        assert "required_classes" in analysis
        assert "required_methods" in analysis
        assert "required_interfaces" in analysis

    @pytest.mark.asyncio
    async def test_generate_minimal_implementation(self, code_agent):
        """Test generating minimal implementation."""
        test_analysis = {
            "required_classes": ["UserService"],
            "required_interfaces": ["UserRepository"],
            "data_models": ["User"],
            "requires_persistence": True,
            "requires_api": True
        }
        story_id = "user_management"
        
        implementation = await code_agent._generate_minimal_implementation(test_analysis, story_id)
        
        assert isinstance(implementation, dict)
        assert f"src/{story_id}_module.py" in implementation
        assert f"src/{story_id}_interfaces.py" in implementation
        assert f"src/{story_id}_models.py" in implementation
        assert f"src/{story_id}_repository.py" in implementation
        assert f"src/{story_id}_api.py" in implementation

    @pytest.mark.asyncio
    async def test_run_tests_against_implementation(self, code_agent):
        """Test running tests against implementation."""
        test_files = ["test_user.py"]
        implementation = {"src/user.py": "class User: pass"}
        
        results = await code_agent._run_tests_against_implementation(test_files, implementation)
        
        assert isinstance(results, dict)
        assert "all_passing" in results
        assert "total_tests" in results
        assert "passing_tests" in results
        assert "failing_tests" in results

    @pytest.mark.asyncio
    async def test_write_implementation_files(self, code_agent):
        """Test writing implementation files."""
        implementation = {
            "src/user.py": "class User: pass",
            "src/auth.py": "class Auth: pass"
        }
        story_id = "user_management"
        
        written_files = await code_agent._write_implementation_files(implementation, story_id)
        
        assert isinstance(written_files, dict)
        assert written_files == implementation

    @pytest.mark.asyncio
    async def test_various_helper_methods(self, code_agent):
        """Test various helper methods."""
        # Test analyze_refactor_opportunities
        implementation_files = ["src/user.py"]
        analysis = await code_agent._analyze_refactor_opportunities(implementation_files)
        assert "code_smells" in analysis
        
        # Test apply_refactoring_strategies
        goals = ["improve_readability"]
        refactored = await code_agent._apply_refactoring_strategies(implementation_files, goals, analysis)
        assert isinstance(refactored, dict)
        
        # Test validate_refactoring_preserves_tests
        validation = await code_agent._validate_refactoring_preserves_tests(refactored)
        assert "all_tests_pass" in validation
        
        # Test measure_quality_improvement
        improvement = await code_agent._measure_quality_improvement(implementation_files, refactored)
        assert "complexity_reduction" in improvement
        
        # Test perform_final_validation
        test_files = ["test_user.py"]
        final_validation = await code_agent._perform_final_validation(implementation_files, test_files)
        assert "ready_for_commit" in final_validation
        
        # Test prepare_tdd_commit
        preparation = await code_agent._prepare_tdd_commit(implementation_files, test_files, "user_mgmt")
        assert "files_to_stage" in preparation
        
        # Test execute_git_commit
        commit_result = await code_agent._execute_git_commit("Test commit", preparation)
        assert "success" in commit_result
        assert commit_result["success"] is True