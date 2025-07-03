"""
Unit tests for Agent system.

Tests the complete agent system including base agent functionality,
specialized agent implementations, and agent coordination.
Consolidated from multiple agent-specific test files.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent_workflow.agents import (
    BaseAgent, Task, AgentResult, TaskStatus, TDDState, TDDCycle, TDDTask,
    DesignAgent, CodeAgent, QAAgent, DataAgent, create_agent, get_available_agents,
    AGENT_REGISTRY
)


class TestTaskStatus:
    """Test TaskStatus enum."""
    
    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTask:
    """Test Task dataclass."""
    
    def test_task_creation(self):
        """Test creating a Task instance."""
        task = Task(
            id="task-1",
            agent_type="DesignAgent",
            command="create_architecture",
            context={"project": "test"}
        )
        
        assert task.id == "task-1"
        assert task.agent_type == "DesignAgent"
        assert task.command == "create_architecture"
        assert task.context == {"project": "test"}
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.created_at is not None

    def test_task_post_init(self):
        """Test Task post-initialization."""
        task = Task(
            id="task-2",
            agent_type="CodeAgent", 
            command="implement",
            context={}
        )
        
        assert isinstance(task.created_at, datetime)


class TestAgentResult:
    """Test AgentResult dataclass."""
    
    def test_agent_result_creation(self):
        """Test creating an AgentResult instance."""
        result = AgentResult(
            success=True,
            output="Task completed successfully",
            artifacts={"file1.py": "content"},
            execution_time=2.5
        )
        
        assert result.success is True
        assert result.output == "Task completed successfully"
        assert result.artifacts == {"file1.py": "content"}
        assert result.execution_time == 2.5
        assert result.error is None

    def test_agent_result_post_init(self):
        """Test AgentResult post-initialization."""
        result = AgentResult(success=False, output="", error="Test error")
        
        assert result.artifacts == {}


class TestBaseAgent:
    """Test BaseAgent abstract class."""
    
    @pytest.fixture
    def mock_tdd_state_machine(self):
        """Create a mock TDD state machine."""
        state_machine = Mock()
        state_machine.current_state = TDDState.DESIGN
        state_machine.validate_command.return_value = Mock(success=True)
        state_machine.get_allowed_commands.return_value = ["design", "write_test"]
        return state_machine

    @pytest.fixture
    def mock_context_manager(self):
        """Create a mock context manager."""
        context_manager = Mock()
        context_manager.prepare_context = AsyncMock()
        context_manager.record_agent_decision = AsyncMock(return_value="decision-123")
        context_manager.create_context_snapshot = AsyncMock(return_value="snapshot-123")
        return context_manager

    @pytest.fixture
    def concrete_agent(self, mock_context_manager):
        """Create a concrete implementation of BaseAgent for testing."""
        class TestAgent(BaseAgent):
            async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
                return AgentResult(
                    success=True,
                    output=f"Executed task {task.id}",
                    execution_time=1.0
                )
        
        return TestAgent(
            name="TestAgent",
            capabilities=["test_capability"],
            context_manager=mock_context_manager
        )

    def test_base_agent_init(self, concrete_agent):
        """Test BaseAgent initialization."""
        assert concrete_agent.name == "TestAgent"
        assert concrete_agent.capabilities == ["test_capability"]
        assert concrete_agent.task_history == []
        assert concrete_agent.tdd_state_machine is None
        assert concrete_agent.current_tdd_cycle is None
        assert concrete_agent.current_tdd_task is None

    def test_validate_task(self, concrete_agent):
        """Test task validation."""
        valid_task = Task(
            id="test-1",
            agent_type="TestAgent",
            command="test",
            context={}
        )
        
        invalid_task = Task(
            id="test-2", 
            agent_type="DifferentAgent",
            command="test",
            context={}
        )
        
        assert concrete_agent.validate_task(valid_task) is True
        assert concrete_agent.validate_task(invalid_task) is False

    def test_get_status(self, concrete_agent):
        """Test getting agent status."""
        # Add some mock task history
        completed_task = Task("task-1", "TestAgent", "test", {})
        completed_task.status = TaskStatus.COMPLETED
        
        failed_task = Task("task-2", "TestAgent", "test", {})
        failed_task.status = TaskStatus.FAILED
        
        concrete_agent.task_history = [completed_task, failed_task]
        
        status = concrete_agent.get_status()
        
        assert status["name"] == "TestAgent"
        assert status["capabilities"] == ["test_capability"]
        assert status["total_tasks"] == 2
        assert status["completed_tasks"] == 1
        assert status["failed_tasks"] == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, concrete_agent):
        """Test successful task execution with retry mechanism."""
        task = Task("retry-test", "TestAgent", "test", {})
        
        result = await concrete_agent._execute_with_retry(task)
        
        assert result.success is True
        assert task.status == TaskStatus.COMPLETED
        assert task.retry_count == 0
        assert task in concrete_agent.task_history

    @pytest.mark.asyncio
    async def test_execute_with_retry_failure(self, concrete_agent):
        """Test task execution failure with retry mechanism."""
        class FailingAgent(BaseAgent):
            async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
                return AgentResult(success=False, output="", error="Test failure")
        
        failing_agent = FailingAgent("FailingAgent", ["test"])
        task = Task("fail-test", "FailingAgent", "test", {})
        task.max_retries = 2
        
        result = await failing_agent._execute_with_retry(task)
        
        assert result.success is False
        assert task.status == TaskStatus.FAILED
        assert task.retry_count == 2

    def test_set_tdd_context(self, concrete_agent, mock_tdd_state_machine):
        """Test setting TDD context."""
        mock_cycle = Mock()
        mock_cycle.id = "cycle-1"
        mock_task = Mock()
        
        concrete_agent.set_tdd_context(mock_tdd_state_machine, mock_cycle, mock_task)
        
        assert concrete_agent.tdd_state_machine == mock_tdd_state_machine
        assert concrete_agent.current_tdd_cycle == mock_cycle
        assert concrete_agent.current_tdd_task == mock_task

    def test_get_tdd_state(self, concrete_agent):
        """Test getting TDD state."""
        # Test with no TDD context
        assert concrete_agent.get_tdd_state() is None
        
        # Test with cycle
        mock_cycle = Mock()
        mock_cycle.current_state = TDDState.TEST_RED
        concrete_agent.current_tdd_cycle = mock_cycle
        
        assert concrete_agent.get_tdd_state() == TDDState.TEST_RED
        
        # Test with state machine
        concrete_agent.current_tdd_cycle = None
        mock_state_machine = Mock()
        mock_state_machine.current_state = TDDState.CODE_GREEN
        concrete_agent.tdd_state_machine = mock_state_machine
        
        assert concrete_agent.get_tdd_state() == TDDState.CODE_GREEN

    def test_validate_tdd_command(self, concrete_agent, mock_tdd_state_machine):
        """Test TDD command validation."""
        # Test without state machine
        result = concrete_agent.validate_tdd_command("design")
        assert result.success is False
        assert "No TDD state machine" in result.error_message
        
        # Test with state machine
        concrete_agent.tdd_state_machine = mock_tdd_state_machine
        result = concrete_agent.validate_tdd_command("design")
        assert result.success is True

    def test_can_execute_tdd_phase(self, concrete_agent):
        """Test TDD phase execution permissions."""
        # Test without TDD state
        assert concrete_agent.can_execute_tdd_phase(TDDState.DESIGN) is False
        
        # Test with TDD state but wrong agent type
        concrete_agent.current_tdd_cycle = Mock()
        concrete_agent.current_tdd_cycle.current_state = TDDState.DESIGN
        assert concrete_agent.can_execute_tdd_phase(TDDState.TEST_RED) is False

    @pytest.mark.asyncio
    async def test_get_tdd_context(self, concrete_agent):
        """Test getting TDD context."""
        context = await concrete_agent.get_tdd_context("STORY-1")
        
        assert context["story_id"] == "STORY-1"
        assert context["agent_name"] == "TestAgent"
        assert context["agent_capabilities"] == ["test_capability"]
        assert "timestamp" in context

    @pytest.mark.asyncio
    async def test_prepare_context(self, concrete_agent, mock_context_manager):
        """Test context preparation."""
        mock_context = Mock()
        mock_context.get_total_token_estimate.return_value = 1000
        mock_context_manager.prepare_context.return_value = mock_context
        
        result = await concrete_agent.prepare_context({"task": "test"}, "STORY-1")
        
        assert result == mock_context
        assert concrete_agent._current_context == mock_context
        mock_context_manager.prepare_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_decision(self, concrete_agent, mock_context_manager):
        """Test recording decisions."""
        decision_id = await concrete_agent.record_decision(
            description="Test decision",
            rationale="Test rationale",
            confidence=0.8
        )
        
        assert decision_id == "decision-123"
        mock_context_manager.record_agent_decision.assert_called_once()

    def test_get_current_context_info(self, concrete_agent):
        """Test getting current context info."""
        # Test without context
        info = concrete_agent.get_current_context_info()
        assert info["has_context"] is False
        
        # Test with context
        mock_context = Mock()
        mock_context.request_id = "req-123"
        mock_context.story_id = "STORY-1"
        concrete_agent._current_context = mock_context
        
        info = concrete_agent.get_current_context_info()
        assert info["has_context"] is True
        assert info["request_id"] == "req-123"
        assert info["story_id"] == "STORY-1"


class TestDesignAgent:
    """Test DesignAgent implementation."""
    
    @pytest.fixture
    def design_agent(self):
        """Create a DesignAgent instance for testing."""
        with patch('agent_workflow.agents.design_agent.create_agent_client'):
            return DesignAgent()

    def test_design_agent_init(self, design_agent):
        """Test DesignAgent initialization."""
        assert design_agent.name == "DesignAgent"
        assert "system_architecture" in design_agent.capabilities
        assert "component_design" in design_agent.capabilities

    @pytest.mark.asyncio
    async def test_design_agent_run(self, design_agent):
        """Test DesignAgent task execution."""
        task = Task(
            id="design-task",
            agent_type="DesignAgent",
            command="create_architecture",
            context={"project": "test"}
        )
        
        with patch.object(design_agent, '_create_architecture') as mock_create:
            mock_create.return_value = AgentResult(
                success=True,
                output="Architecture created",
                artifacts={"architecture.md": "content"}
            )
            
            result = await design_agent.run(task)
            
            assert result.success is True
            assert "Architecture created" in result.output


class TestCodeAgent:
    """Test CodeAgent implementation."""
    
    @pytest.fixture
    def code_agent(self):
        """Create a CodeAgent instance for testing."""
        with patch('agent_workflow.agents.code_agent.create_agent_client'):
            return CodeAgent()

    def test_code_agent_init(self, code_agent):
        """Test CodeAgent initialization."""
        assert code_agent.name == "CodeAgent"
        assert "code_implementation" in code_agent.capabilities
        assert "bug_fixing" in code_agent.capabilities

    @pytest.mark.asyncio
    async def test_code_agent_run(self, code_agent):
        """Test CodeAgent task execution."""
        task = Task(
            id="code-task",
            agent_type="CodeAgent", 
            command="implement_feature",
            context={"feature": "login"}
        )
        
        with patch.object(code_agent, '_implement_feature') as mock_implement:
            mock_implement.return_value = AgentResult(
                success=True,
                output="Feature implemented",
                artifacts={"login.py": "implementation"}
            )
            
            result = await code_agent.run(task)
            
            assert result.success is True
            assert "Feature implemented" in result.output


class TestQAAgent:
    """Test QAAgent implementation."""
    
    @pytest.fixture
    def qa_agent(self):
        """Create a QAAgent instance for testing."""
        with patch('agent_workflow.agents.qa_agent.create_agent_client'):
            return QAAgent()

    def test_qa_agent_init(self, qa_agent):
        """Test QAAgent initialization."""
        assert qa_agent.name == "QAAgent"
        assert "test_creation" in qa_agent.capabilities
        assert "test_execution" in qa_agent.capabilities

    @pytest.mark.asyncio
    async def test_qa_agent_run(self, qa_agent):
        """Test QAAgent task execution."""
        task = Task(
            id="qa-task",
            agent_type="QAAgent",
            command="create_tests",
            context={"module": "login"}
        )
        
        with patch.object(qa_agent, '_create_tests') as mock_create:
            mock_create.return_value = AgentResult(
                success=True,
                output="Tests created",
                artifacts={"test_login.py": "test code"}
            )
            
            result = await qa_agent.run(task)
            
            assert result.success is True
            assert "Tests created" in result.output


class TestDataAgent:
    """Test DataAgent implementation."""
    
    @pytest.fixture
    def data_agent(self):
        """Create a DataAgent instance for testing."""
        with patch('agent_workflow.agents.data_agent.create_agent_client'):
            return DataAgent()

    def test_data_agent_init(self, data_agent):
        """Test DataAgent initialization."""
        assert data_agent.name == "DataAgent"
        assert "data_analysis" in data_agent.capabilities
        assert "data_validation" in data_agent.capabilities

    @pytest.mark.asyncio
    async def test_data_agent_run(self, data_agent):
        """Test DataAgent task execution."""
        task = Task(
            id="data-task",
            agent_type="DataAgent",
            command="analyze_data",
            context={"dataset": "user_metrics"}
        )
        
        with patch.object(data_agent, '_analyze_data') as mock_analyze:
            mock_analyze.return_value = AgentResult(
                success=True,
                output="Data analyzed",
                artifacts={"analysis.json": "results"}
            )
            
            result = await data_agent.run(task)
            
            assert result.success is True
            assert "Data analyzed" in result.output


class TestAgentFactory:
    """Test agent factory functions."""
    
    def test_get_available_agents(self):
        """Test getting available agent types."""
        agents = get_available_agents()
        
        assert "DesignAgent" in agents
        assert "CodeAgent" in agents
        assert "QAAgent" in agents
        assert "DataAgent" in agents

    def test_create_agent_success(self):
        """Test successful agent creation."""
        with patch('agent_workflow.agents.design_agent.create_agent_client'):
            agent = create_agent("DesignAgent")
            
            assert isinstance(agent, DesignAgent)
            assert agent.name == "DesignAgent"

    def test_create_agent_invalid_type(self):
        """Test creating agent with invalid type."""
        with pytest.raises(ValueError, match="Unknown agent type"):
            create_agent("InvalidAgent")

    def test_create_agent_with_context_manager(self):
        """Test creating agent with context manager."""
        mock_context_manager = Mock()
        
        with patch('agent_workflow.agents.design_agent.create_agent_client'):
            agent = create_agent("DesignAgent", context_manager=mock_context_manager)
            
            assert agent.context_manager == mock_context_manager

    def test_agent_registry(self):
        """Test agent registry contains expected agents."""
        assert "DesignAgent" in AGENT_REGISTRY
        assert "CodeAgent" in AGENT_REGISTRY
        assert "QAAgent" in AGENT_REGISTRY
        assert "DataAgent" in AGENT_REGISTRY
        
        assert AGENT_REGISTRY["DesignAgent"] == DesignAgent
        assert AGENT_REGISTRY["CodeAgent"] == CodeAgent


class TestMockAgentMode:
    """Test mock agent mode functionality."""
    
    @pytest.mark.asyncio
    async def test_mock_agent_mode_creation(self):
        """Test creating agents in mock mode."""
        with patch.dict('os.environ', {'NO_AGENT_MODE': 'true'}):
            # This would test mock agent creation
            # The actual implementation depends on mock_agent.py
            pass

    def test_mock_agent_capabilities(self):
        """Test mock agent capabilities."""
        # This would test that mock agents have the same interface
        # as real agents but with simulated behavior
        pass


class TestAgentCoordination:
    """Test agent coordination scenarios."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test coordinated workflow between multiple agents."""
        # This would test scenarios where agents work together
        # on a complete feature implementation
        pass

    @pytest.mark.asyncio
    async def test_agent_handoff(self):
        """Test context handoff between agents."""
        # This would test proper context transfer when one agent
        # completes work and hands off to another
        pass

    @pytest.mark.asyncio 
    async def test_agent_error_recovery(self):
        """Test agent error recovery mechanisms."""
        # This would test how agents handle and recover from errors
        pass


class TestTDDIntegration:
    """Test TDD workflow integration with agents."""
    
    @pytest.mark.asyncio
    async def test_tdd_phase_transitions(self):
        """Test TDD phase transitions between agents."""
        # This would test the complete TDD cycle execution
        # across different agent types
        pass

    @pytest.mark.asyncio
    async def test_tdd_context_preservation(self):
        """Test TDD context preservation across agent handoffs."""
        # This would test that TDD state is properly maintained
        # when switching between agents
        pass


if __name__ == "__main__":
    pytest.main([__file__])