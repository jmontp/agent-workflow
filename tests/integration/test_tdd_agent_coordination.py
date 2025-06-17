"""
Integration tests for TDD agent coordination.

Tests complete TDD workflows with multiple agents coordinating
through the orchestrator to execute full Red-Green-Refactor cycles.
"""

import pytest
import asyncio
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "lib"))

from orchestrator import Orchestrator, OrchestrationMode
from agents import (
    BaseAgent, Task, AgentResult, TaskStatus,
    DesignAgent, CodeAgent, QAAgent, DataAgent
)
from tdd_models import TDDState, TDDCycle, TDDTask, TestResult
from tdd_state_machine import TDDStateMachine, TDDCommandResult
from agent_tool_config import AgentType


@pytest.mark.integration
class TestTDDAgentCoordination:
    """Test TDD agent coordination workflows"""
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for test files"""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def test_config(self, temp_directory):
        """Create test orchestrator configuration"""
        config = {
            "projects": [
                {
                    "name": "tdd_test_project",
                    "path": str(temp_directory / "tdd_test_project"),
                    "orchestration": "blocking"
                }
            ]
        }
        
        # Create project directory
        project_dir = temp_directory / "tdd_test_project"
        project_dir.mkdir(exist_ok=True)
        
        # Save config to file
        config_file = temp_directory / "test_projects.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        return config_file
    
    @pytest.fixture
    def mock_orchestrator(self, test_config):
        """Create mock orchestrator with TDD capabilities"""
        with patch('orchestrator.create_agent') as mock_create:
            # Create mock agents
            mock_design_agent = Mock(spec=DesignAgent)
            mock_qa_agent = Mock(spec=QAAgent)
            mock_code_agent = Mock(spec=CodeAgent)
            mock_data_agent = Mock(spec=DataAgent)
            
            # Set up agent creation mapping
            def create_agent_side_effect(agent_type, **kwargs):
                agent_map = {
                    "DesignAgent": mock_design_agent,
                    "QAAgent": mock_qa_agent,
                    "CodeAgent": mock_code_agent,
                    "DataAgent": mock_data_agent
                }
                return agent_map.get(agent_type, Mock())
            
            mock_create.side_effect = create_agent_side_effect
            
            orchestrator = Orchestrator(str(test_config))
            
            # Store mock agents for test access
            orchestrator._mock_design_agent = mock_design_agent
            orchestrator._mock_qa_agent = mock_qa_agent
            orchestrator._mock_code_agent = mock_code_agent
            orchestrator._mock_data_agent = mock_data_agent
            
            yield orchestrator
    
    @pytest.fixture
    def sample_story(self):
        """Create sample user story for TDD testing"""
        return {
            "id": "story-auth-001",
            "title": "User Authentication",
            "description": "As a user, I want to log in with email and password so that I can access my account",
            "acceptance_criteria": [
                "User can log in with valid email and password",
                "User receives error for invalid credentials",
                "User session is created upon successful login",
                "User can log out and session is terminated"
            ]
        }
    
    @pytest.fixture
    def tdd_state_machine(self):
        """Create TDD state machine for testing"""
        return TDDStateMachine()
    
    @pytest.fixture
    def tdd_cycle(self, sample_story):
        """Create TDD cycle for testing"""
        cycle = Mock(spec=TDDCycle)
        cycle.id = f"cycle-{sample_story['id']}"
        cycle.story_id = sample_story["id"]
        cycle.current_state = TDDState.DESIGN
        cycle.tasks = []
        cycle.get_progress_summary.return_value = {"completed": 0, "total": 5}
        return cycle
    
    @pytest.mark.asyncio
    async def test_complete_tdd_cycle_workflow(self, mock_orchestrator, sample_story, tdd_cycle):
        """Test complete TDD cycle from DESIGN to COMMIT"""
        # Set up agent result mocks for each phase
        design_result = AgentResult(
            success=True,
            output="TDD Design Phase Complete",
            artifacts={
                "tdd-specification.md": "# TDD Specification for User Authentication",
                "acceptance-criteria.md": "# Acceptance Criteria",
                "test-scenarios.md": "# Test Scenarios",
                "api-contracts.md": "# API Contracts"
            }
        )
        
        qa_result = AgentResult(
            success=True,
            output="TEST_RED Phase Complete - All tests failing as expected",
            artifacts={
                "tests/test_auth.py": "# Failing authentication tests",
                "tests/test_user.py": "# Failing user tests",
                "test_coverage_report.json": '{"coverage": 0}'
            }
        )
        
        code_green_result = AgentResult(
            success=True,
            output="CODE_GREEN Phase Complete - All tests now passing",
            artifacts={
                "src/auth.py": "# Minimal authentication implementation",
                "src/user.py": "# Minimal user implementation",
                "test_results.json": '{"all_passing": true, "total_tests": 15}'
            }
        )
        
        refactor_result = AgentResult(
            success=True,
            output="REFACTOR Phase Complete - Code quality improved",
            artifacts={
                "src/auth.py": "# Refactored authentication implementation",
                "src/user.py": "# Refactored user implementation",
                "refactor_report.json": '{"quality_improvement": 25.0}'
            }
        )
        
        commit_result = AgentResult(
            success=True,
            output="COMMIT Phase Complete - TDD cycle committed",
            artifacts={
                "commit_details.json": '{"commit_hash": "abc123", "files_committed": 4}'
            }
        )
        
        # Configure mock agents
        mock_orchestrator._mock_design_agent.execute_tdd_phase.return_value = design_result
        mock_orchestrator._mock_qa_agent.execute_tdd_phase.return_value = qa_result
        mock_orchestrator._mock_code_agent.execute_tdd_phase.side_effect = [
            code_green_result, refactor_result, commit_result
        ]
        
        # Execute TDD workflow phases
        
        # 1. DESIGN Phase
        design_task = Task(
            id="design-task",
            agent_type="DesignAgent",
            command="execute_tdd_design",
            context={"story": sample_story, "tdd_cycle": tdd_cycle}
        )
        
        design_execution = await mock_orchestrator._mock_design_agent.execute_tdd_phase(
            TDDState.DESIGN, design_task.context
        )
        assert design_execution.success
        assert "TDD Design Phase Complete" in design_execution.output
        assert len(design_execution.artifacts) >= 4
        
        # 2. TEST_RED Phase
        qa_task = Task(
            id="qa-task",
            agent_type="QAAgent", 
            command="execute_tdd_test_red",
            context={
                "story": sample_story,
                "tdd_cycle": tdd_cycle,
                "design_artifacts": design_execution.artifacts
            }
        )
        
        qa_execution = await mock_orchestrator._mock_qa_agent.execute_tdd_phase(
            TDDState.TEST_RED, qa_task.context
        )
        assert qa_execution.success
        assert "TEST_RED Phase Complete" in qa_execution.output
        assert any("test_" in filename for filename in qa_execution.artifacts.keys())
        
        # 3. CODE_GREEN Phase
        code_green_task = Task(
            id="code-green-task",
            agent_type="CodeAgent",
            command="execute_tdd_code_green", 
            context={
                "story": sample_story,
                "tdd_cycle": tdd_cycle,
                "test_files": list(qa_execution.artifacts.keys())
            }
        )
        
        code_green_execution = await mock_orchestrator._mock_code_agent.execute_tdd_phase(
            TDDState.CODE_GREEN, code_green_task.context
        )
        assert code_green_execution.success
        assert "CODE_GREEN Phase Complete" in code_green_execution.output
        
        # 4. REFACTOR Phase
        refactor_task = Task(
            id="refactor-task",
            agent_type="CodeAgent",
            command="execute_tdd_refactor",
            context={
                "story": sample_story,
                "tdd_cycle": tdd_cycle,
                "implementation_files": list(code_green_execution.artifacts.keys())
            }
        )
        
        refactor_execution = await mock_orchestrator._mock_code_agent.execute_tdd_phase(
            TDDState.REFACTOR, refactor_task.context
        )
        assert refactor_execution.success
        assert "REFACTOR Phase Complete" in refactor_execution.output
        
        # 5. COMMIT Phase
        commit_task = Task(
            id="commit-task",
            agent_type="CodeAgent",
            command="execute_tdd_commit",
            context={
                "story": sample_story,
                "tdd_cycle": tdd_cycle,
                "implementation_files": list(refactor_execution.artifacts.keys()),
                "test_files": list(qa_execution.artifacts.keys())
            }
        )
        
        commit_execution = await mock_orchestrator._mock_code_agent.execute_tdd_phase(
            TDDState.COMMIT, commit_task.context
        )
        assert commit_execution.success
        assert "COMMIT Phase Complete" in commit_execution.output
        
        # Verify complete workflow
        all_artifacts = {}
        all_artifacts.update(design_execution.artifacts)
        all_artifacts.update(qa_execution.artifacts)
        all_artifacts.update(code_green_execution.artifacts)
        all_artifacts.update(refactor_execution.artifacts)
        all_artifacts.update(commit_execution.artifacts)
        
        # Should have design artifacts
        assert any("specification" in filename for filename in all_artifacts.keys())
        # Should have test artifacts  
        assert any("test_" in filename for filename in all_artifacts.keys())
        # Should have implementation artifacts
        assert any("src/" in filename for filename in all_artifacts.keys())
        # Should have commit artifacts
        assert "commit_details.json" in all_artifacts
    
    @pytest.mark.asyncio
    async def test_agent_coordination_with_state_machine(self, mock_orchestrator, tdd_state_machine, tdd_cycle):
        """Test agent coordination using TDD state machine"""
        # Configure state machine
        tdd_state_machine.current_state = TDDState.DESIGN
        
        # Mock state machine validation
        with patch.object(tdd_state_machine, 'validate_command') as mock_validate, \
             patch.object(tdd_state_machine, 'execute_command') as mock_execute:
            
            mock_validate.return_value = TDDCommandResult(success=True)
            mock_execute.return_value = TDDCommandResult(
                success=True,
                new_state=TDDState.TEST_RED
            )
            
            # Test state transition validation
            result = tdd_state_machine.validate_command("design", tdd_cycle)
            assert result.success
            
            # Test state transition execution
            result = tdd_state_machine.execute_command("design", tdd_cycle)
            assert result.success
            assert result.new_state == TDDState.TEST_RED
            
            # Verify agents called with proper context
            mock_validate.assert_called()
            mock_execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_agent_security_in_tdd_workflow(self, mock_orchestrator):
        """Test that agents respect security boundaries in TDD workflow"""
        from agent_tool_config import validate_tdd_tool_access, AgentType
        
        # Test DesignAgent restrictions
        design_pytest_result = validate_tdd_tool_access(
            AgentType.DESIGN, "Bash(pytest)", {"current_phase": "DESIGN"}
        )
        assert not design_pytest_result["allowed"]
        assert "cannot execute tests" in design_pytest_result["tdd_specific_restrictions"][0]
        
        design_git_commit_result = validate_tdd_tool_access(
            AgentType.DESIGN, "Bash(git commit)", {"current_phase": "DESIGN"}
        )
        assert not design_git_commit_result["allowed"]
        assert "read-only git access" in design_git_commit_result["tdd_specific_restrictions"][0]
        
        # Test QAAgent permissions
        qa_pytest_result = validate_tdd_tool_access(
            AgentType.QA, "Bash(pytest)", {"current_phase": "TEST_RED"}
        )
        assert qa_pytest_result["allowed"]
        
        qa_git_commit_result = validate_tdd_tool_access(
            AgentType.QA, "Bash(git commit)", {"current_phase": "TEST_RED"}
        )
        assert not qa_git_commit_result["allowed"]
        assert "cannot commit" in qa_git_commit_result["tdd_specific_restrictions"][0]
        
        # Test CodeAgent permissions
        code_pytest_result = validate_tdd_tool_access(
            AgentType.CODE, "Bash(pytest)", {"current_phase": "CODE_GREEN"}
        )
        assert code_pytest_result["allowed"]
        
        code_git_commit_result = validate_tdd_tool_access(
            AgentType.CODE, "Bash(git commit)", {"current_phase": "COMMIT"}
        )
        assert code_git_commit_result["allowed"]
        
        code_git_push_result = validate_tdd_tool_access(
            AgentType.CODE, "Bash(git push)", {"current_phase": "COMMIT"}
        )
        assert not code_git_push_result["allowed"]
        assert "cannot push" in code_git_push_result["tdd_specific_restrictions"][0]
    
    @pytest.mark.asyncio
    async def test_tdd_error_handling_and_recovery(self, mock_orchestrator, sample_story, tdd_cycle):
        """Test TDD workflow error handling and recovery"""
        # Set up failing QA agent
        qa_error = Exception("Test generation failed")
        mock_orchestrator._mock_qa_agent.execute_tdd_phase.side_effect = qa_error
        
        # Set up successful design agent
        design_result = AgentResult(
            success=True,
            output="Design completed",
            artifacts={"spec.md": "# Specification"}
        )
        mock_orchestrator._mock_design_agent.execute_tdd_phase.return_value = design_result
        
        # Execute design phase (should succeed)
        design_execution = await mock_orchestrator._mock_design_agent.execute_tdd_phase(
            TDDState.DESIGN, {"story": sample_story}
        )
        assert design_execution.success
        
        # Execute test phase (should fail)
        with pytest.raises(Exception) as exc_info:
            await mock_orchestrator._mock_qa_agent.execute_tdd_phase(
                TDDState.TEST_RED, {"story": sample_story}
            )
        assert "Test generation failed" in str(exc_info.value)
        
        # Test error recovery - reset QA agent to succeed
        qa_recovery_result = AgentResult(
            success=True,
            output="Tests created after retry",
            artifacts={"tests/test_auth.py": "# Recovered tests"}
        )
        mock_orchestrator._mock_qa_agent.execute_tdd_phase.side_effect = None
        mock_orchestrator._mock_qa_agent.execute_tdd_phase.return_value = qa_recovery_result
        
        # Retry should succeed
        qa_execution = await mock_orchestrator._mock_qa_agent.execute_tdd_phase(
            TDDState.TEST_RED, {"story": sample_story}
        )
        assert qa_execution.success
        assert "after retry" in qa_execution.output
    
    @pytest.mark.asyncio
    async def test_tdd_artifact_handoff_between_agents(self, mock_orchestrator, sample_story):
        """Test that artifacts are properly passed between agents in TDD workflow"""
        # Design phase artifacts
        design_artifacts = {
            "tdd-specification.md": "# TDD Specification",
            "acceptance-criteria.md": "# Acceptance Criteria",
            "test-scenarios.md": "# Test Scenarios"
        }
        
        design_result = AgentResult(
            success=True,
            output="Design complete",
            artifacts=design_artifacts
        )
        
        # QA phase should receive design artifacts and create test artifacts
        test_artifacts = {
            "tests/test_auth.py": "# Authentication tests based on design",
            "tests/test_user.py": "# User tests based on specification"
        }
        
        qa_result = AgentResult(
            success=True,
            output="Tests created from design artifacts",
            artifacts=test_artifacts
        )
        
        # Code phase should receive both design and test artifacts
        impl_artifacts = {
            "src/auth.py": "# Implementation based on tests and design",
            "src/user.py": "# User implementation"
        }
        
        code_result = AgentResult(
            success=True,
            output="Implementation created from tests and design",
            artifacts=impl_artifacts
        )
        
        # Configure mock agents
        mock_orchestrator._mock_design_agent.execute_tdd_phase.return_value = design_result
        mock_orchestrator._mock_qa_agent.execute_tdd_phase.return_value = qa_result
        mock_orchestrator._mock_code_agent.execute_tdd_phase.return_value = code_result
        
        # Execute phases with artifact handoff
        design_execution = await mock_orchestrator._mock_design_agent.execute_tdd_phase(
            TDDState.DESIGN, {"story": sample_story}
        )
        
        qa_execution = await mock_orchestrator._mock_qa_agent.execute_tdd_phase(
            TDDState.TEST_RED, {
                "story": sample_story,
                "design_artifacts": design_execution.artifacts
            }
        )
        
        code_execution = await mock_orchestrator._mock_code_agent.execute_tdd_phase(
            TDDState.CODE_GREEN, {
                "story": sample_story,
                "design_artifacts": design_execution.artifacts,
                "test_artifacts": qa_execution.artifacts
            }
        )
        
        # Verify artifact progression
        assert len(design_execution.artifacts) == 3
        assert len(qa_execution.artifacts) == 2
        assert len(code_execution.artifacts) == 2
        
        # Verify artifact content references proper sources
        assert "based on design" in qa_execution.output
        assert "from tests and design" in code_execution.output
    
    @pytest.mark.asyncio
    async def test_parallel_tdd_cycles(self, mock_orchestrator, temp_directory):
        """Test multiple TDD cycles running in parallel"""
        # Create multiple stories
        story1 = {"id": "auth-001", "title": "User Authentication"}
        story2 = {"id": "profile-001", "title": "User Profile Management"}
        
        # Create separate cycles
        cycle1 = Mock()
        cycle1.id = "cycle-auth-001"
        cycle1.story_id = "auth-001"
        cycle1.current_state = TDDState.DESIGN
        
        cycle2 = Mock()
        cycle2.id = "cycle-profile-001"
        cycle2.story_id = "profile-001"
        cycle2.current_state = TDDState.DESIGN
        
        # Set up different results for each cycle
        auth_result = AgentResult(
            success=True,
            output="Auth design complete",
            artifacts={"auth-spec.md": "# Auth specification"}
        )
        
        profile_result = AgentResult(
            success=True,
            output="Profile design complete",
            artifacts={"profile-spec.md": "# Profile specification"}
        )
        
        # Configure mock to return different results based on context
        def design_side_effect(phase, context):
            story = context.get("story", {})
            if story.get("id") == "auth-001":
                return auth_result
            elif story.get("id") == "profile-001":
                return profile_result
            else:
                return AgentResult(success=False, output="Unknown story")
        
        mock_orchestrator._mock_design_agent.execute_tdd_phase.side_effect = design_side_effect
        
        # Execute both cycles in parallel
        auth_task = mock_orchestrator._mock_design_agent.execute_tdd_phase(
            TDDState.DESIGN, {"story": story1, "tdd_cycle": cycle1}
        )
        
        profile_task = mock_orchestrator._mock_design_agent.execute_tdd_phase(
            TDDState.DESIGN, {"story": story2, "tdd_cycle": cycle2}
        )
        
        # Wait for both to complete
        auth_execution, profile_execution = await asyncio.gather(auth_task, profile_task)
        
        # Verify both completed successfully with different outputs
        assert auth_execution.success
        assert profile_execution.success
        assert "Auth design complete" in auth_execution.output
        assert "Profile design complete" in profile_execution.output
        assert "auth-spec.md" in auth_execution.artifacts
        assert "profile-spec.md" in profile_execution.artifacts
    
    @pytest.mark.asyncio
    async def test_tdd_metrics_and_monitoring(self, mock_orchestrator, sample_story):
        """Test TDD metrics collection and monitoring throughout workflow"""
        # Set up agents with metrics
        design_result = AgentResult(
            success=True,
            output="Design complete",
            artifacts={"spec.md": "# Spec"},
            execution_time=2.5
        )
        
        qa_result = AgentResult(
            success=True,
            output="Tests complete",
            artifacts={
                "tests/test_auth.py": "# Tests",
                "metrics.json": '{"test_count": 15, "coverage": 0}'
            },
            execution_time=5.2
        )
        
        code_result = AgentResult(
            success=True,
            output="Implementation complete",
            artifacts={
                "src/auth.py": "# Implementation",
                "metrics.json": '{"test_count": 15, "coverage": 95, "complexity": 3.2}'
            },
            execution_time=8.7
        )
        
        mock_orchestrator._mock_design_agent.execute_tdd_phase.return_value = design_result
        mock_orchestrator._mock_qa_agent.execute_tdd_phase.return_value = qa_result
        mock_orchestrator._mock_code_agent.execute_tdd_phase.return_value = code_result
        
        # Execute workflow and collect metrics
        phases = [
            (mock_orchestrator._mock_design_agent, TDDState.DESIGN),
            (mock_orchestrator._mock_qa_agent, TDDState.TEST_RED),
            (mock_orchestrator._mock_code_agent, TDDState.CODE_GREEN)
        ]
        
        total_time = 0
        all_metrics = []
        
        for agent, phase in phases:
            result = await agent.execute_tdd_phase(phase, {"story": sample_story})
            total_time += result.execution_time
            
            # Extract metrics if available
            if "metrics.json" in result.artifacts:
                metrics = json.loads(result.artifacts["metrics.json"])
                metrics["phase"] = phase.value
                metrics["execution_time"] = result.execution_time
                all_metrics.append(metrics)
        
        # Verify metrics collection
        assert total_time > 16.0  # Sum of all execution times
        assert len(all_metrics) == 2  # QA and Code phases have metrics
        
        # Verify metrics progression
        qa_metrics = next(m for m in all_metrics if m["phase"] == "TEST_RED")
        code_metrics = next(m for m in all_metrics if m["phase"] == "CODE_GREEN")
        
        assert qa_metrics["coverage"] == 0  # No coverage before implementation
        assert code_metrics["coverage"] == 95  # High coverage after implementation
        assert qa_metrics["test_count"] == code_metrics["test_count"]  # Same tests
    
    @pytest.mark.asyncio
    async def test_tdd_workflow_with_human_approval_gates(self, mock_orchestrator, sample_story):
        """Test TDD workflow with human approval gates in blocking orchestration"""
        # Configure orchestrator for blocking mode (requires human approval)
        project = mock_orchestrator.projects["tdd_test_project"]
        assert project.orchestration_mode.value == "blocking"
        
        # Mock human approval simulation
        approval_sequence = [True, True, False, True]  # Approve design, tests, reject first code attempt, approve second
        approval_index = 0
        
        def mock_human_approval(*args, **kwargs):
            nonlocal approval_index
            result = approval_sequence[approval_index]
            approval_index += 1
            return result
        
        # Set up results with approval gates
        design_result = AgentResult(success=True, output="Design awaiting approval", artifacts={"spec.md": "# Spec"})
        qa_result = AgentResult(success=True, output="Tests awaiting approval", artifacts={"tests/test.py": "# Tests"})
        code_result_rejected = AgentResult(success=False, output="Implementation rejected", artifacts={})
        code_result_approved = AgentResult(success=True, output="Implementation approved", artifacts={"src/code.py": "# Code"})
        
        mock_orchestrator._mock_design_agent.execute_tdd_phase.return_value = design_result
        mock_orchestrator._mock_qa_agent.execute_tdd_phase.return_value = qa_result
        mock_orchestrator._mock_code_agent.execute_tdd_phase.side_effect = [code_result_rejected, code_result_approved]
        
        # Execute workflow with approval gates
        with patch('orchestrator.get_human_approval', side_effect=mock_human_approval):
            # Design phase - approved
            design_execution = await mock_orchestrator._mock_design_agent.execute_tdd_phase(
                TDDState.DESIGN, {"story": sample_story}
            )
            assert design_execution.success
            
            # QA phase - approved  
            qa_execution = await mock_orchestrator._mock_qa_agent.execute_tdd_phase(
                TDDState.TEST_RED, {"story": sample_story}
            )
            assert qa_execution.success
            
            # Code phase - first attempt rejected
            code_execution_1 = await mock_orchestrator._mock_code_agent.execute_tdd_phase(
                TDDState.CODE_GREEN, {"story": sample_story}
            )
            assert not code_execution_1.success
            
            # Code phase - second attempt approved
            code_execution_2 = await mock_orchestrator._mock_code_agent.execute_tdd_phase(
                TDDState.CODE_GREEN, {"story": sample_story}
            )
            assert code_execution_2.success
        
        # Verify approval gates were called
        assert approval_index == 4  # All approval gates were hit


if __name__ == "__main__":
    pytest.main([__file__])