"""
Comprehensive test suite for BaseAgent class in agents/__init__.py

Tests agent initialization, task execution, TDD workflow integration,
context management, error handling, and agent lifecycle.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from agents import (
    BaseAgent, Task, AgentResult, TaskStatus, TDDState, TDDCycle, TDDTask, TestResult,
    create_agent, get_available_agents, AGENT_REGISTRY
)


class TestBaseAgent:
    """Test BaseAgent abstract class functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a concrete implementation for testing
        class TestAgent(BaseAgent):
            async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
                if task.command == "fail":
                    return AgentResult(success=False, output="", error="Simulated failure")
                return AgentResult(success=True, output=f"Executed: {task.command}")
        
        self.test_agent = TestAgent(
            name="TestAgent",
            capabilities=["test_capability", "mock_capability"]
        )
    
    def test_base_agent_initialization(self):
        """Test BaseAgent initialization with required parameters"""
        agent = self.test_agent
        
        assert agent.name == "TestAgent"
        assert agent.capabilities == ["test_capability", "mock_capability"]
        assert agent.task_history == []
        assert agent.logger is not None
        assert agent.tdd_state_machine is None
        assert agent.current_tdd_cycle is None
        assert agent.current_tdd_task is None
        assert agent.context_manager is None
        assert agent._current_context is None
    
    def test_base_agent_initialization_with_context_manager(self):
        """Test BaseAgent initialization with context manager"""
        mock_context_manager = Mock()
        
        class TestAgentWithContext(BaseAgent):
            async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
                return AgentResult(success=True, output="test")
        
        agent = TestAgentWithContext(
            name="TestAgentWithContext",
            capabilities=["test"],
            context_manager=mock_context_manager
        )
        
        assert agent.context_manager == mock_context_manager
    
    def test_validate_task_success(self):
        """Test task validation for correct agent type"""
        task = Task(
            id="test-task",
            agent_type="TestAgent",
            command="test_command",
            context={}
        )
        
        assert self.test_agent.validate_task(task) is True
    
    def test_validate_task_failure(self):
        """Test task validation for incorrect agent type"""
        task = Task(
            id="test-task",
            agent_type="WrongAgent",
            command="test_command",
            context={}
        )
        
        assert self.test_agent.validate_task(task) is False
    
    def test_get_status_empty_history(self):
        """Test get_status with no task history"""
        status = self.test_agent.get_status()
        
        expected = {
            "name": "TestAgent",
            "capabilities": ["test_capability", "mock_capability"],
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0
        }
        
        assert status == expected
    
    def test_get_status_with_history(self):
        """Test get_status with task history"""
        # Add some tasks to history
        completed_task = Task("task1", "TestAgent", "cmd1", {})
        completed_task.status = TaskStatus.COMPLETED
        
        failed_task = Task("task2", "TestAgent", "cmd2", {})
        failed_task.status = TaskStatus.FAILED
        
        pending_task = Task("task3", "TestAgent", "cmd3", {})
        pending_task.status = TaskStatus.PENDING
        
        self.test_agent.task_history = [completed_task, failed_task, pending_task]
        
        status = self.test_agent.get_status()
        
        assert status["total_tasks"] == 3
        assert status["completed_tasks"] == 1
        assert status["failed_tasks"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self):
        """Test _execute_with_retry succeeds on first attempt"""
        task = Task("test-task", "TestAgent", "success_command", {})
        
        result = await self.test_agent._execute_with_retry(task, dry_run=False)
        
        assert result.success is True
        assert "Executed: success_command" in result.output
        assert task.status == TaskStatus.COMPLETED
        assert task.retry_count == 0
        assert task in self.test_agent.task_history
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_failure_exhausts_retries(self):
        """Test _execute_with_retry fails after max retries"""
        task = Task("test-task", "TestAgent", "fail", {}, max_retries=2)
        
        result = await self.test_agent._execute_with_retry(task, dry_run=False)
        
        assert result.success is False
        assert task.status == TaskStatus.FAILED
        assert task.retry_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_exception_handling(self):
        """Test _execute_with_retry handles exceptions"""
        class ExceptionAgent(BaseAgent):
            async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
                raise ValueError("Test exception")
        
        agent = ExceptionAgent("ExceptionAgent", ["test"])
        task = Task("test-task", "ExceptionAgent", "cmd", {}, max_retries=1)
        
        result = await agent._execute_with_retry(task, dry_run=False)
        
        assert result.success is False
        assert "Test exception" in result.error
        assert task.status == TaskStatus.FAILED
    
    def test_log_task_execution(self):
        """Test _log_task_execution method"""
        task = Task("test-task", "TestAgent", "cmd", {})
        result = AgentResult(success=True, output="test", execution_time=1.5)
        
        with patch.object(self.test_agent.logger, 'info') as mock_log:
            self.test_agent._log_task_execution(task, result)
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "test-task" in call_args
            assert "TestAgent" in call_args
            assert "success=True" in call_args
            assert "time=1.50s" in call_args


class TestTaskAndAgentResult:
    """Test Task and AgentResult data classes"""
    
    def test_task_initialization(self):
        """Test Task initialization with required fields"""
        task = Task(
            id="test-task",
            agent_type="TestAgent", 
            command="test_command",
            context={"key": "value"}
        )
        
        assert task.id == "test-task"
        assert task.agent_type == "TestAgent"
        assert task.command == "test_command"
        assert task.context == {"key": "value"}
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert isinstance(task.created_at, datetime)
    
    def test_task_post_init_created_at(self):
        """Test Task __post_init__ sets created_at if not provided"""
        task = Task("id", "agent", "cmd", {})
        assert task.created_at is not None
        assert isinstance(task.created_at, datetime)
        
        # Test with explicit created_at
        explicit_time = datetime(2023, 1, 1, 12, 0, 0)
        task_with_time = Task("id", "agent", "cmd", {}, created_at=explicit_time)
        assert task_with_time.created_at == explicit_time
    
    def test_agent_result_initialization(self):
        """Test AgentResult initialization"""
        result = AgentResult(
            success=True,
            output="Test output",
            artifacts={"file.py": "content"},
            error="Test error",
            execution_time=2.5
        )
        
        assert result.success is True
        assert result.output == "Test output"
        assert result.artifacts == {"file.py": "content"}
        assert result.error == "Test error"
        assert result.execution_time == 2.5
    
    def test_agent_result_post_init_artifacts(self):
        """Test AgentResult __post_init__ sets empty artifacts if None"""
        result = AgentResult(success=True, output="test")
        assert result.artifacts == {}
        
        # Test with explicit artifacts
        result_with_artifacts = AgentResult(success=True, output="test", artifacts={"file": "content"})
        assert result_with_artifacts.artifacts == {"file": "content"}


class TestTDDIntegration:
    """Test TDD-specific functionality in BaseAgent"""
    
    def setup_method(self):
        """Set up test fixtures for TDD tests"""
        class TDDTestAgent(BaseAgent):
            async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
                return AgentResult(success=True, output="test")
        
        self.agent = TDDTestAgent("TDDTestAgent", ["tdd_capability"])
        
        # Mock TDD objects
        self.mock_state_machine = Mock()
        self.mock_cycle = Mock()
        self.mock_cycle.id = "cycle-1"
        self.mock_cycle.story_id = "story-1"
        self.mock_cycle.current_state = TDDState.DESIGN
        self.mock_cycle.tasks = []
        self.mock_cycle.get_progress_summary.return_value = {"progress": "50%"}
        
        self.mock_task = Mock()
        self.mock_task.id = "task-1"
        self.mock_task.description = "Test task"
        self.mock_task.current_state = TDDState.TEST_RED
        self.mock_task.test_results = []
        self.mock_task.has_failing_tests.return_value = True
        self.mock_task.has_passing_tests.return_value = False
    
    def test_set_tdd_context(self):
        """Test setting TDD context"""
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle, self.mock_task)
        
        assert self.agent.tdd_state_machine == self.mock_state_machine
        assert self.agent.current_tdd_cycle == self.mock_cycle
        assert self.agent.current_tdd_task == self.mock_task
    
    def test_set_tdd_context_with_logging(self):
        """Test TDD context setting with logging"""
        with patch.object(self.agent.logger, 'info') as mock_log:
            self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle, self.mock_task)
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "cycle=cycle-1" in call_args
            assert "state=DESIGN" in call_args
    
    def test_get_tdd_state_from_cycle(self):
        """Test getting TDD state from current cycle"""
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        state = self.agent.get_tdd_state()
        assert state == TDDState.DESIGN
    
    def test_get_tdd_state_from_state_machine(self):
        """Test getting TDD state from state machine when no cycle"""
        self.mock_state_machine.current_state = TDDState.CODE_GREEN
        self.agent.set_tdd_context(self.mock_state_machine)
        
        state = self.agent.get_tdd_state()
        assert state == TDDState.CODE_GREEN
    
    def test_get_tdd_state_none(self):
        """Test getting TDD state when no context set"""
        state = self.agent.get_tdd_state()
        assert state is None
    
    def test_validate_tdd_command_no_state_machine(self):
        """Test validating TDD command without state machine"""
        result = self.agent.validate_tdd_command("test_command")
        
        assert result.success is False
        assert "No TDD state machine available" in result.error_message
        assert "Set TDD context" in result.hint
    
    def test_validate_tdd_command_with_state_machine(self):
        """Test validating TDD command with state machine"""
        mock_result = Mock()
        mock_result.success = True
        self.mock_state_machine.validate_command.return_value = mock_result
        
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        result = self.agent.validate_tdd_command("test_command")
        
        assert result == mock_result
        self.mock_state_machine.validate_command.assert_called_once_with("test_command", self.mock_cycle)
    
    def test_can_execute_tdd_phase_design_agent(self):
        """Test TDD phase execution permissions for design phase"""
        # Override class name for this test
        self.agent.__class__.__name__ = "DesignAgent"
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        assert self.agent.can_execute_tdd_phase(TDDState.DESIGN) is True
        assert self.agent.can_execute_tdd_phase(TDDState.TEST_RED) is False
        assert self.agent.can_execute_tdd_phase(TDDState.CODE_GREEN) is False
    
    def test_can_execute_tdd_phase_qa_agent(self):
        """Test TDD phase execution permissions for QA agent"""
        self.agent.__class__.__name__ = "QAAgent"
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        assert self.agent.can_execute_tdd_phase(TDDState.DESIGN) is False
        assert self.agent.can_execute_tdd_phase(TDDState.TEST_RED) is True
        assert self.agent.can_execute_tdd_phase(TDDState.CODE_GREEN) is False
    
    def test_can_execute_tdd_phase_code_agent(self):
        """Test TDD phase execution permissions for code agent"""
        self.agent.__class__.__name__ = "CodeAgent"
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        assert self.agent.can_execute_tdd_phase(TDDState.DESIGN) is False
        assert self.agent.can_execute_tdd_phase(TDDState.TEST_RED) is False
        assert self.agent.can_execute_tdd_phase(TDDState.CODE_GREEN) is True
        assert self.agent.can_execute_tdd_phase(TDDState.REFACTOR) is True
        assert self.agent.can_execute_tdd_phase(TDDState.COMMIT) is True
    
    def test_can_execute_tdd_phase_orchestrator(self):
        """Test TDD phase execution permissions for orchestrator"""
        self.agent.__class__.__name__ = "OrchestratorAgent"
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        # Orchestrator can execute any phase
        for phase in TDDState:
            assert self.agent.can_execute_tdd_phase(phase) is True
    
    def test_can_execute_tdd_phase_no_state(self):
        """Test TDD phase execution with no current state"""
        result = self.agent.can_execute_tdd_phase(TDDState.DESIGN)
        assert result is False
    
    def test_get_tdd_context_info_minimal(self):
        """Test getting TDD context info with minimal context"""
        info = self.agent.get_tdd_context_info()
        
        expected_keys = [
            "agent_name", "has_tdd_context", "current_state", "cycle_id", 
            "task_id", "allowed_commands", "tdd_metrics"
        ]
        
        for key in expected_keys:
            assert key in info
        
        assert info["agent_name"] == "TDDTestAgent"
        assert info["has_tdd_context"] is False
        assert info["current_state"] is None
        assert info["cycle_id"] is None
        assert info["task_id"] is None
    
    def test_get_tdd_context_info_full(self):
        """Test getting TDD context info with full context"""
        # Set up full TDD context
        self.mock_state_machine.get_allowed_commands.return_value = ["design", "write_test"]
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle, self.mock_task)
        
        info = self.agent.get_tdd_context_info()
        
        assert info["has_tdd_context"] is True
        assert info["current_state"] == "DESIGN"
        assert info["cycle_id"] == "cycle-1"
        assert info["task_id"] == "task-1"
        assert info["allowed_commands"] == ["design", "write_test"]
        assert "cycle_progress" in info
        assert "task_description" in info
    
    def test_get_tdd_metrics(self):
        """Test _get_tdd_metrics method"""
        # Add some TDD tasks to history
        tdd_task1 = Task("tdd-1", "TDDTestAgent", "cmd1", {"tdd_cycle": "cycle-1"})
        tdd_task1.status = TaskStatus.COMPLETED
        
        tdd_task2 = Task("tdd-2", "TDDTestAgent", "cmd2", {"tdd_cycle": "cycle-1"})
        tdd_task2.status = TaskStatus.FAILED
        
        non_tdd_task = Task("regular", "TDDTestAgent", "cmd3", {})
        non_tdd_task.status = TaskStatus.COMPLETED
        
        self.agent.task_history = [tdd_task1, tdd_task2, non_tdd_task]
        
        metrics = self.agent._get_tdd_metrics()
        
        assert metrics["total_tdd_tasks"] == 2
        assert metrics["completed_tdd_tasks"] == 1
        assert metrics["failed_tdd_tasks"] == 1
        assert "average_execution_time" in metrics
        assert "success_rate" in metrics
    
    def test_assess_cycle_health_no_cycle(self):
        """Test cycle health assessment with no cycle"""
        health = self.agent._assess_cycle_health()
        
        assert health["status"] == "no_cycle"
        assert health["score"] == 0
    
    def test_assess_cycle_health_with_cycle(self):
        """Test cycle health assessment with cycle"""
        # Set up cycle with tasks
        completed_task = Mock()
        completed_task.current_state = TDDState.COMMIT
        
        in_progress_task = Mock()
        in_progress_task.current_state = TDDState.CODE_GREEN
        
        self.mock_cycle.tasks = [completed_task, in_progress_task]
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        health = self.agent._assess_cycle_health()
        
        assert health["total_tasks"] == 2
        assert health["completed_tasks"] == 1
        assert health["score"] == 50.0
        assert health["status"] == "needs_attention"
        assert health["current_state"] == "DESIGN"
    
    def test_assess_task_health_no_task(self):
        """Test task health assessment with no task"""
        health = self.agent._assess_task_health()
        
        assert health["status"] == "no_task"
        assert health["score"] == 0
    
    def test_assess_task_health_no_tests(self):
        """Test task health assessment with no tests"""
        self.mock_task.test_results = []
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle, self.mock_task)
        
        health = self.agent._assess_task_health()
        
        assert health["status"] == "no_tests"
        assert health["score"] == 0
    
    def test_assess_task_health_red_phase(self):
        """Test task health assessment in RED phase"""
        # Set up test results for RED phase
        failing_test = Mock()
        failing_test.passed = False
        
        passing_test = Mock()
        passing_test.passed = True
        
        self.mock_task.test_results = [failing_test, failing_test, failing_test, passing_test]
        self.mock_task.current_state = TDDState.TEST_RED
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle, self.mock_task)
        
        health = self.agent._assess_task_health()
        
        assert health["total_tests"] == 4
        assert health["passing_tests"] == 1
        assert health["pass_rate"] == 25.0
        assert health["status"] == "healthy"  # Low pass rate is good in RED phase
        assert health["score"] == 75.0  # 100 - pass_rate
        assert health["current_state"] == "TEST_RED"
    
    def test_assess_task_health_green_phase(self):
        """Test task health assessment in GREEN phase"""
        # Set up test results for GREEN phase
        passing_test = Mock()
        passing_test.passed = True
        
        failing_test = Mock()
        failing_test.passed = False
        
        self.mock_task.test_results = [passing_test, passing_test, passing_test, failing_test]
        self.mock_task.current_state = TDDState.CODE_GREEN
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle, self.mock_task)
        
        health = self.agent._assess_task_health()
        
        assert health["total_tests"] == 4
        assert health["passing_tests"] == 3
        assert health["pass_rate"] == 75.0
        assert health["status"] == "needs_attention"  # Need high pass rate in GREEN phase
        assert health["score"] == 75.0  # Same as pass_rate in GREEN phase
    
    def test_calculate_average_execution_time(self):
        """Test _calculate_average_execution_time method"""
        # Test with empty list
        avg_time = self.agent._calculate_average_execution_time([])
        assert avg_time == 0.0
        
        # Test with tasks having execution_time
        task1 = Mock()
        task1.execution_time = 2.0
        
        task2 = Mock()
        task2.execution_time = 4.0
        
        task3 = Mock()  # No execution_time attribute
        
        avg_time = self.agent._calculate_average_execution_time([task1, task2, task3])
        assert avg_time == 2.0  # (2.0 + 4.0 + 0) / 3
    
    def test_calculate_success_rate(self):
        """Test _calculate_success_rate method"""
        # Test with empty list
        success_rate = self.agent._calculate_success_rate([])
        assert success_rate == 0.0
        
        # Test with mixed task statuses
        completed_task = Mock()
        completed_task.status = TaskStatus.COMPLETED
        
        failed_task = Mock()
        failed_task.status = TaskStatus.FAILED
        
        pending_task = Mock()
        pending_task.status = TaskStatus.PENDING
        
        tasks = [completed_task, completed_task, failed_task, pending_task]
        success_rate = self.agent._calculate_success_rate(tasks)
        assert success_rate == 50.0  # 2 completed out of 4 total
    
    def test_is_tdd_enabled(self):
        """Test is_tdd_enabled method"""
        assert self.agent.is_tdd_enabled() is False
        
        self.agent.set_tdd_context(self.mock_state_machine)
        assert self.agent.is_tdd_enabled() is True
    
    def test_log_tdd_action(self):
        """Test log_tdd_action method"""
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle, self.mock_task)
        
        with patch.object(self.agent.logger, 'info') as mock_log:
            self.agent.log_tdd_action("test_action", "test details")
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "TDD test_action" in call_args
            assert "[cycle:cycle-1]" in call_args
            assert "[task:task-1]" in call_args
            assert "[state:TEST_RED]" in call_args
            assert "test details" in call_args
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_default_implementation(self):
        """Test default execute_tdd_phase implementation"""
        self.agent.__class__.__name__ = "DesignAgent"
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        result = await self.agent.execute_tdd_phase(TDDState.DESIGN, {})
        
        assert result.success is True
        assert "DesignAgent executed TDD phase DESIGN" in result.output
        assert result.artifacts == {}
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_unauthorized(self):
        """Test execute_tdd_phase with unauthorized agent"""
        self.agent.__class__.__name__ = "QAAgent"  # QA can't execute DESIGN
        
        result = await self.agent.execute_tdd_phase(TDDState.DESIGN, {})
        
        assert result.success is False
        assert "cannot execute TDD phase DESIGN" in result.error
    
    @pytest.mark.asyncio
    async def test_handle_tdd_task_success(self):
        """Test handle_tdd_task successful execution"""
        # Mock validation and context methods
        self.agent.validate_tdd_phase = AsyncMock(return_value=AgentResult(success=True, output="valid"))
        self.agent.get_tdd_context = AsyncMock(return_value={"context": "data"})
        self.agent.execute_tdd_phase = AsyncMock(return_value=AgentResult(success=True, output="executed"))
        
        result = await self.agent.handle_tdd_task(self.mock_cycle, TDDState.DESIGN)
        
        assert result.success is True
        assert "executed" in result.output
        assert self.agent.current_tdd_cycle == self.mock_cycle
        self.agent.validate_tdd_phase.assert_called_once()
        self.agent.get_tdd_context.assert_called_once()
        self.agent.execute_tdd_phase.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_tdd_task_validation_failure(self):
        """Test handle_tdd_task with validation failure"""
        self.agent.validate_tdd_phase = AsyncMock(return_value=AgentResult(success=False, error="validation failed"))
        
        result = await self.agent.handle_tdd_task(self.mock_cycle, TDDState.DESIGN)
        
        assert result.success is False
        assert "validation failed" in result.error
    
    @pytest.mark.asyncio
    async def test_handle_tdd_task_exception(self):
        """Test handle_tdd_task with exception"""
        self.agent.validate_tdd_phase = AsyncMock(side_effect=Exception("Test exception"))
        
        result = await self.agent.handle_tdd_task(self.mock_cycle, TDDState.DESIGN)
        
        assert result.success is False
        assert "TDD task execution failed" in result.error
        assert "Test exception" in result.error
    
    @pytest.mark.asyncio
    async def test_validate_tdd_phase_unauthorized_agent(self):
        """Test validate_tdd_phase with unauthorized agent"""
        self.agent.__class__.__name__ = "QAAgent"
        
        result = await self.agent.validate_tdd_phase(TDDState.DESIGN, TDDState.DESIGN)
        
        assert result.success is False
        assert "cannot execute TDD phase DESIGN" in result.error
    
    @pytest.mark.asyncio
    async def test_validate_tdd_phase_invalid_transition(self):
        """Test validate_tdd_phase with invalid transition"""
        self.agent.__class__.__name__ = "DesignAgent"
        
        # Invalid transition: DESIGN -> CODE_GREEN (should go through TEST_RED)
        result = await self.agent.validate_tdd_phase(TDDState.DESIGN, TDDState.CODE_GREEN)
        
        assert result.success is False
        assert "Invalid TDD phase transition" in result.error
    
    @pytest.mark.asyncio
    async def test_validate_tdd_phase_valid_transition(self):
        """Test validate_tdd_phase with valid transition"""
        self.agent.__class__.__name__ = "DesignAgent"
        
        result = await self.agent.validate_tdd_phase(TDDState.DESIGN, TDDState.TEST_RED)
        
        assert result.success is True
        assert "Valid phase transition" in result.output
    
    @pytest.mark.asyncio
    async def test_validate_tdd_phase_with_state_machine_validation(self):
        """Test validate_tdd_phase using state machine validation"""
        self.agent.__class__.__name__ = "DesignAgent"
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle)
        
        # Mock state machine validation failure
        validation_result = Mock()
        validation_result.success = False
        validation_result.error_message = "State machine validation failed"
        self.mock_state_machine.validate_command.return_value = validation_result
        
        result = await self.agent.validate_tdd_phase(TDDState.DESIGN, TDDState.TEST_RED)
        
        assert result.success is False
        assert "Invalid phase transition: State machine validation failed" in result.error
    
    @pytest.mark.asyncio
    async def test_get_tdd_context(self):
        """Test get_tdd_context method"""
        self.agent.set_tdd_context(self.mock_state_machine, self.mock_cycle, self.mock_task)
        
        context = await self.agent.get_tdd_context("story-123")
        
        assert context["story_id"] == "story-123"
        assert context["agent_name"] == "TDDTestAgent"
        assert context["agent_capabilities"] == ["tdd_capability"]
        assert context["tdd_state"] == "TEST_RED"
        assert context["has_tdd_context"] is True
        assert "timestamp" in context
        assert context["cycle_id"] == "cycle-1"
        assert context["task_id"] == "task-1"
    
    @pytest.mark.asyncio
    async def test_get_tdd_context_minimal(self):
        """Test get_tdd_context with minimal setup"""
        context = await self.agent.get_tdd_context("story-123")
        
        assert context["story_id"] == "story-123"
        assert context["agent_name"] == "TDDTestAgent"
        assert context["tdd_state"] is None
        assert context["has_tdd_context"] is False
    
    @pytest.mark.asyncio
    async def test_get_agent_specific_tdd_context(self):
        """Test _get_agent_specific_tdd_context default implementation"""
        context = await self.agent._get_agent_specific_tdd_context("story-123")
        assert context == {}


class TestContextManagement:
    """Test context management functionality in BaseAgent"""
    
    def setup_method(self):
        """Set up test fixtures for context management tests"""
        class ContextTestAgent(BaseAgent):
            async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
                return AgentResult(success=True, output="test")
        
        self.mock_context_manager = AsyncMock()
        self.agent = ContextTestAgent(
            "ContextTestAgent", 
            ["context_capability"],
            context_manager=self.mock_context_manager
        )
    
    @pytest.mark.asyncio
    async def test_prepare_context_success(self):
        """Test prepare_context with successful context preparation"""
        mock_context = Mock()
        mock_context.get_total_token_estimate.return_value = 1000
        self.mock_context_manager.prepare_context.return_value = mock_context
        
        task = {"description": "test task"}
        result = await self.agent.prepare_context(task, story_id="story-1", max_tokens=2000)
        
        assert result == mock_context
        assert self.agent._current_context == mock_context
        self.mock_context_manager.prepare_context.assert_called_once_with(
            agent_type="ContextTestAgent",
            task=task,
            max_tokens=2000,
            story_id="story-1"
        )
    
    @pytest.mark.asyncio
    async def test_prepare_context_no_manager(self):
        """Test prepare_context without context manager"""
        agent = type(self.agent)("TestAgent", ["test"])  # No context manager
        
        with patch.object(agent.logger, 'warning') as mock_warn:
            result = await agent.prepare_context({"task": "data"})
            
            assert result is None
            mock_warn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_context_exception(self):
        """Test prepare_context with exception"""
        self.mock_context_manager.prepare_context.side_effect = Exception("Context error")
        
        with patch.object(self.agent.logger, 'error') as mock_error:
            result = await self.agent.prepare_context({"task": "data"})
            
            assert result is None
            mock_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_decision_success(self):
        """Test record_decision with successful recording"""
        self.mock_context_manager.record_agent_decision.return_value = "decision-123"
        mock_context = Mock()
        mock_context.story_id = "story-456"
        self.agent._current_context = mock_context
        
        decision_id = await self.agent.record_decision(
            description="Test decision",
            rationale="Test rationale",
            outcome="Success",
            confidence=0.8,
            artifacts={"file": "content"}
        )
        
        assert decision_id == "decision-123"
        self.mock_context_manager.record_agent_decision.assert_called_once_with(
            agent_type="ContextTestAgent",
            story_id="story-456",
            description="Test decision",
            rationale="Test rationale",
            outcome="Success",
            confidence=0.8,
            artifacts={"file": "content"}
        )
    
    @pytest.mark.asyncio
    async def test_record_decision_no_manager(self):
        """Test record_decision without context manager"""
        agent = type(self.agent)("TestAgent", ["test"])  # No context manager
        
        result = await agent.record_decision("Test decision")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_record_decision_with_story_id_parameter(self):
        """Test record_decision with explicit story_id parameter"""
        self.mock_context_manager.record_agent_decision.return_value = "decision-456"
        
        decision_id = await self.agent.record_decision(
            description="Test decision",
            story_id="explicit-story"
        )
        
        assert decision_id == "decision-456"
        self.mock_context_manager.record_agent_decision.assert_called_once_with(
            agent_type="ContextTestAgent",
            story_id="explicit-story",
            description="Test decision",
            rationale="",
            outcome="",
            confidence=0.0,
            artifacts=None
        )
    
    @pytest.mark.asyncio
    async def test_record_decision_exception(self):
        """Test record_decision with exception"""
        self.mock_context_manager.record_agent_decision.side_effect = Exception("Record error")
        
        with patch.object(self.agent.logger, 'error') as mock_error:
            result = await self.agent.record_decision("Test decision")
            
            assert result is None
            mock_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_context_snapshot_success(self):
        """Test create_context_snapshot with successful creation"""
        self.mock_context_manager.create_context_snapshot.return_value = "snapshot-123"
        mock_context = Mock()
        mock_context.story_id = "story-789"
        self.agent._current_context = mock_context
        
        snapshot_id = await self.agent.create_context_snapshot("Test summary")
        
        assert snapshot_id == "snapshot-123"
        self.mock_context_manager.create_context_snapshot.assert_called_once_with(
            agent_type="ContextTestAgent",
            story_id="story-789",
            context=mock_context,
            summary="Test summary"
        )
    
    @pytest.mark.asyncio
    async def test_create_context_snapshot_no_context(self):
        """Test create_context_snapshot without current context"""
        result = await self.agent.create_context_snapshot()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_context_snapshot_default_summary(self):
        """Test create_context_snapshot with default summary"""
        self.mock_context_manager.create_context_snapshot.return_value = "snapshot-456"
        mock_context = Mock()
        mock_context.story_id = "story-default"
        self.agent._current_context = mock_context
        
        snapshot_id = await self.agent.create_context_snapshot()
        
        assert snapshot_id == "snapshot-456"
        # Check that default summary was used
        call_args = self.mock_context_manager.create_context_snapshot.call_args
        assert "Context snapshot during ContextTestAgent execution" in call_args[1]["summary"]
    
    @pytest.mark.asyncio
    async def test_get_context_history_success(self):
        """Test get_context_history with successful retrieval"""
        mock_history = [{"snapshot": "1"}, {"snapshot": "2"}]
        self.mock_context_manager.get_agent_context_history.return_value = mock_history
        
        history = await self.agent.get_context_history(
            story_id="story-history",
            tdd_phase=TDDState.DESIGN,
            limit=5
        )
        
        assert history == mock_history
        self.mock_context_manager.get_agent_context_history.assert_called_once_with(
            agent_type="ContextTestAgent",
            story_id="story-history",
            tdd_phase=TDDState.DESIGN,
            limit=5
        )
    
    @pytest.mark.asyncio
    async def test_get_context_history_no_manager(self):
        """Test get_context_history without context manager"""
        agent = type(self.agent)("TestAgent", ["test"])  # No context manager
        
        result = await agent.get_context_history()
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_context_history_from_current_context(self):
        """Test get_context_history extracting story_id from current context"""
        mock_history = [{"snapshot": "current"}]
        self.mock_context_manager.get_agent_context_history.return_value = mock_history
        mock_context = Mock()
        mock_context.story_id = "current-story"
        self.agent._current_context = mock_context
        
        history = await self.agent.get_context_history()
        
        assert history == mock_history
        # Verify story_id was extracted from current context
        call_args = self.mock_context_manager.get_agent_context_history.call_args
        assert call_args[1]["story_id"] == "current-story"
    
    @pytest.mark.asyncio
    async def test_get_recent_decisions_success(self):
        """Test get_recent_decisions with successful retrieval"""
        mock_decisions = [{"decision": "1"}, {"decision": "2"}]
        self.mock_context_manager.get_recent_decisions.return_value = mock_decisions
        
        decisions = await self.agent.get_recent_decisions(story_id="story-decisions", limit=10)
        
        assert decisions == mock_decisions
        self.mock_context_manager.get_recent_decisions.assert_called_once_with(
            agent_type="ContextTestAgent",
            story_id="story-decisions",
            limit=10
        )
    
    @pytest.mark.asyncio
    async def test_get_recent_decisions_exception(self):
        """Test get_recent_decisions with exception"""
        self.mock_context_manager.get_recent_decisions.side_effect = Exception("Decisions error")
        
        with patch.object(self.agent.logger, 'error') as mock_error:
            result = await self.agent.get_recent_decisions()
            
            assert result == []
            mock_error.assert_called_once()
    
    def test_get_current_context_info_no_context(self):
        """Test get_current_context_info without current context"""
        info = self.agent.get_current_context_info()
        assert info == {"has_context": False}
    
    def test_get_current_context_info_with_context(self):
        """Test get_current_context_info with current context"""
        mock_context = Mock()
        mock_context.request_id = "req-123"
        mock_context.story_id = "story-456"
        mock_context.tdd_phase = TDDState.DESIGN
        mock_context.token_usage = {"total": 1000}
        mock_context.preparation_time = 2.5
        mock_context.cache_hit = True
        mock_context.compression_applied = False
        
        self.agent._current_context = mock_context
        
        info = self.agent.get_current_context_info()
        
        expected = {
            "has_context": True,
            "request_id": "req-123",
            "story_id": "story-456",
            "tdd_phase": TDDState.DESIGN,
            "token_usage": {"total": 1000},
            "preparation_time": 2.5,
            "cache_hit": True,
            "compression_applied": False
        }
        
        assert info == expected


class TestErrorHandling:
    """Test error handling functionality in BaseAgent"""
    
    def setup_method(self):
        """Set up test fixtures for error handling tests"""
        class ErrorTestAgent(BaseAgent):
            async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
                return AgentResult(success=True, output="test")
        
        self.agent = ErrorTestAgent("ErrorTestAgent", ["error_handling"])
    
    def test_handle_tdd_error_design_phase(self):
        """Test TDD error handling for DESIGN phase"""
        error = ValueError("Design validation failed")
        
        result = self.agent.handle_tdd_error(error, TDDState.DESIGN)
        
        assert result.success is False
        assert "Design validation failed" in result.error
        assert "design_review" in result.artifacts
        
        # Check error report artifact
        error_report = json.loads(result.artifacts["error_report.json"])
        assert error_report["phase"] == "DESIGN"
        assert error_report["error_type"] == "ValueError"
        assert error_report["is_recoverable"] is True
        assert "Review requirements" in error_report["suggested_recovery"]
    
    def test_handle_tdd_error_test_red_phase(self):
        """Test TDD error handling for TEST_RED phase"""
        error = SyntaxError("Invalid test syntax")
        
        result = self.agent.handle_tdd_error(error, TDDState.TEST_RED)
        
        assert result.success is False
        error_report = json.loads(result.artifacts["error_report.json"])
        assert error_report["phase"] == "TEST_RED"
        assert error_report["error_type"] == "SyntaxError"
        assert "Verify test syntax" in error_report["suggested_recovery"]
    
    def test_handle_tdd_error_code_green_phase(self):
        """Test TDD error handling for CODE_GREEN phase"""
        error = ImportError("Module not found")
        
        result = self.agent.handle_tdd_error(error, TDDState.CODE_GREEN)
        
        error_report = json.loads(result.artifacts["error_report.json"])
        assert error_report["phase"] == "CODE_GREEN"
        assert error_report["error_type"] == "ImportError"
        assert "Implement minimal solution" in error_report["suggested_recovery"]
    
    def test_handle_tdd_error_refactor_phase(self):
        """Test TDD error handling for REFACTOR phase"""
        error = RuntimeError("Refactoring broke tests")
        
        result = self.agent.handle_tdd_error(error, TDDState.REFACTOR)
        
        error_report = json.loads(result.artifacts["error_report.json"])
        assert error_report["phase"] == "REFACTOR"
        assert error_report["suggested_recovery"] == "Revert to working state and apply smaller refactoring steps"
    
    def test_handle_tdd_error_commit_phase(self):
        """Test TDD error handling for COMMIT phase"""
        error = Exception("Git conflict detected")
        
        result = self.agent.handle_tdd_error(error, TDDState.COMMIT)
        
        error_report = json.loads(result.artifacts["error_report.json"])
        assert error_report["phase"] == "COMMIT"
        assert "Resolve conflicts" in error_report["suggested_recovery"]
    
    def test_handle_tdd_error_with_custom_recovery(self):
        """Test TDD error handling with custom recovery action"""
        error = Exception("Custom error")
        
        result = self.agent.handle_tdd_error(error, TDDState.DESIGN, "Custom recovery action")
        
        error_report = json.loads(result.artifacts["error_report.json"])
        assert error_report["suggested_recovery"] == "Custom recovery action"
    
    def test_handle_tdd_error_recoverable_vs_unrecoverable(self):
        """Test TDD error handling distinguishes recoverable vs unrecoverable errors"""
        # Recoverable error
        recoverable_error = ImportError("Module missing")
        result1 = self.agent.handle_tdd_error(recoverable_error, TDDState.CODE_GREEN)
        error_report1 = json.loads(result1.artifacts["error_report.json"])
        assert error_report1["is_recoverable"] is True
        
        # Unrecoverable error (not in recoverable list)
        unrecoverable_error = KeyboardInterrupt("User interrupted")
        result2 = self.agent.handle_tdd_error(unrecoverable_error, TDDState.CODE_GREEN)
        error_report2 = json.loads(result2.artifacts["error_report.json"])
        assert error_report2["is_recoverable"] is False
    
    def test_handle_tdd_error_logging(self):
        """Test TDD error handling includes proper logging"""
        error = ValueError("Test error")
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            self.agent.handle_tdd_error(error, TDDState.DESIGN)
            
            mock_log.assert_called_once_with("error_handling", "phase: DESIGN, error: Test error")


class TestAgentFactory:
    """Test agent factory and registry functionality"""
    
    def test_agent_registry_contents(self):
        """Test AGENT_REGISTRY contains expected agents"""
        expected_agents = ["DesignAgent", "CodeAgent", "QAAgent", "DataAgent"]
        
        for agent_type in expected_agents:
            assert agent_type in AGENT_REGISTRY
            assert callable(AGENT_REGISTRY[agent_type])
    
    def test_get_available_agents(self):
        """Test get_available_agents returns correct list"""
        available_agents = get_available_agents()
        
        expected_agents = ["DesignAgent", "CodeAgent", "QAAgent", "DataAgent"]
        assert all(agent in available_agents for agent in expected_agents)
    
    def test_create_agent_success(self):
        """Test create_agent with valid agent type"""
        with patch.dict('os.environ', {'NO_AGENT_MODE': 'false'}):
            agent = create_agent("DesignAgent", name="TestDesign")
            
            assert agent is not None
            assert agent.__class__.__name__ == "DesignAgent"
    
    def test_create_agent_with_context_manager(self):
        """Test create_agent with context manager"""
        mock_context_manager = Mock()
        
        with patch.dict('os.environ', {'NO_AGENT_MODE': 'false'}):
            agent = create_agent("DesignAgent", context_manager=mock_context_manager)
            
            assert agent.context_manager == mock_context_manager
    
    def test_create_agent_invalid_type(self):
        """Test create_agent with invalid agent type"""
        with pytest.raises(ValueError, match="Unknown agent type"):
            create_agent("InvalidAgent")
    
    def test_create_agent_no_agent_mode(self):
        """Test create_agent in NO_AGENT_MODE"""
        with patch.dict('os.environ', {'NO_AGENT_MODE': 'true'}):
            with patch('agents.create_mock_agent') as mock_create:
                mock_agent = Mock()
                mock_create.return_value = mock_agent
                
                agent = create_agent("DesignAgent", test_param="value")
                
                assert agent == mock_agent
                mock_create.assert_called_once_with(
                    "DesignAgent",
                    context_manager=None
                )


class TestTaskStatus:
    """Test TaskStatus enum"""
    
    def test_task_status_values(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
    
    def test_task_status_membership(self):
        """Test TaskStatus enum membership"""
        all_statuses = [status.value for status in TaskStatus]
        expected_statuses = ["pending", "in_progress", "completed", "failed", "cancelled"]
        
        assert all_statuses == expected_statuses


if __name__ == "__main__":
    pytest.main([__file__])