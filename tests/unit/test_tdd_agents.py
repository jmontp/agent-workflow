"""
Tests for TDD-enhanced agent capabilities.

Verifies that all agents have proper TDD-specific functionality
and can execute their designated phases correctly.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add the project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "lib"))

from agents import (
    BaseAgent, Task, AgentResult, TaskStatus
)
from agents.design_agent import DesignAgent
from agents.code_agent import CodeAgent  
from agents.qa_agent import QAAgent
from agents.data_agent import DataAgent
from tdd_models import TDDState, TDDCycle, TDDTask, TestResult
from tdd_state_machine import TDDStateMachine
from agent_tool_config import AgentType


@pytest.mark.unit
class TestBaseAgentTDDCapabilities:
    """Test BaseAgent TDD-specific functionality"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing"""
        agent = DesignAgent()
        return agent
    
    @pytest.fixture
    def mock_tdd_state_machine(self):
        """Create mock TDD state machine"""
        state_machine = Mock(spec=TDDStateMachine)
        state_machine.current_state = TDDState.DESIGN
        state_machine.validate_command.return_value = Mock(success=True)
        state_machine.get_allowed_commands.return_value = ["design", "write_test"]
        return state_machine
    
    @pytest.fixture
    def mock_tdd_cycle(self):
        """Create mock TDD cycle"""
        cycle = Mock(spec=TDDCycle)
        cycle.id = "test-cycle-001"
        cycle.story_id = "story-123"
        cycle.current_state = TDDState.DESIGN
        cycle.tasks = []
        cycle.get_progress_summary.return_value = {"completed": 0, "total": 1}
        return cycle
    
    @pytest.fixture
    def mock_tdd_task(self):
        """Create mock TDD task"""
        task = Mock(spec=TDDTask)
        task.id = "task-001"
        task.description = "Test task"
        task.current_state = TDDState.DESIGN
        task.test_results = []
        task.has_failing_tests.return_value = False
        task.has_passing_tests.return_value = False
        return task
    
    def test_set_tdd_context(self, mock_agent, mock_tdd_state_machine, mock_tdd_cycle, mock_tdd_task):
        """Test setting TDD context on agent"""
        mock_agent.set_tdd_context(mock_tdd_state_machine, mock_tdd_cycle, mock_tdd_task)
        
        assert mock_agent.tdd_state_machine == mock_tdd_state_machine
        assert mock_agent.current_tdd_cycle == mock_tdd_cycle
        assert mock_agent.current_tdd_task == mock_tdd_task
    
    def test_get_tdd_state(self, mock_agent, mock_tdd_cycle):
        """Test getting current TDD state"""
        # Test with cycle
        mock_agent.current_tdd_cycle = mock_tdd_cycle
        assert mock_agent.get_tdd_state() == TDDState.DESIGN
        
        # Test with state machine but no cycle
        mock_agent.current_tdd_cycle = None
        mock_state_machine = Mock()
        mock_state_machine.current_state = TDDState.TEST_RED
        mock_agent.tdd_state_machine = mock_state_machine
        assert mock_agent.get_tdd_state() == TDDState.TEST_RED
        
        # Test with no context
        mock_agent.tdd_state_machine = None
        assert mock_agent.get_tdd_state() is None
    
    def test_validate_tdd_command(self, mock_agent, mock_tdd_state_machine):
        """Test TDD command validation"""
        mock_agent.tdd_state_machine = mock_tdd_state_machine
        
        result = mock_agent.validate_tdd_command("design")
        assert result.success
        mock_tdd_state_machine.validate_command.assert_called_once()
    
    def test_validate_tdd_command_no_state_machine(self, mock_agent):
        """Test TDD command validation without state machine"""
        mock_agent.tdd_state_machine = None
        
        result = mock_agent.validate_tdd_command("design")
        assert not result.success
        assert "No TDD state machine available" in result.error_message
    
    def test_can_execute_tdd_phase(self, mock_agent):
        """Test TDD phase execution validation"""
        # DesignAgent should be able to execute DESIGN phase
        assert mock_agent.can_execute_tdd_phase(TDDState.DESIGN)
        
        # DesignAgent should not be able to execute TEST_RED phase
        assert not mock_agent.can_execute_tdd_phase(TDDState.TEST_RED)
    
    def test_get_tdd_context_info(self, mock_agent, mock_tdd_state_machine, mock_tdd_cycle, mock_tdd_task):
        """Test getting comprehensive TDD context information"""
        mock_agent.set_tdd_context(mock_tdd_state_machine, mock_tdd_cycle, mock_tdd_task)
        
        info = mock_agent.get_tdd_context_info()
        
        assert info["agent_name"] == "DesignAgent"
        assert info["has_tdd_context"] is True
        assert info["current_state"] == TDDState.DESIGN.value
        assert info["cycle_id"] == "test-cycle-001"
        assert info["task_id"] == "task-001"
        assert "tdd_metrics" in info
        assert "cycle_health" in info
        assert "task_health" in info
    
    def test_get_tdd_metrics(self, mock_agent):
        """Test TDD metrics calculation"""
        # Add some mock TDD tasks to history
        tdd_task1 = Mock()
        tdd_task1.context = {"tdd_cycle": "cycle-1"}
        tdd_task1.status = TaskStatus.COMPLETED
        
        tdd_task2 = Mock()
        tdd_task2.context = {"tdd_cycle": "cycle-2"}
        tdd_task2.status = TaskStatus.FAILED
        
        mock_agent.task_history = [tdd_task1, tdd_task2]
        
        metrics = mock_agent._get_tdd_metrics()
        
        assert metrics["total_tdd_tasks"] == 2
        assert metrics["completed_tdd_tasks"] == 1
        assert metrics["failed_tdd_tasks"] == 1
        assert "success_rate" in metrics
        assert "average_execution_time" in metrics
    
    def test_assess_cycle_health(self, mock_agent, mock_tdd_cycle):
        """Test TDD cycle health assessment"""
        mock_agent.current_tdd_cycle = mock_tdd_cycle
        
        # Mock tasks with different states
        completed_task = Mock()
        completed_task.current_state = TDDState.COMMIT
        pending_task = Mock()
        pending_task.current_state = TDDState.DESIGN
        
        mock_tdd_cycle.tasks = [completed_task, pending_task]
        
        health = mock_agent._assess_cycle_health()
        
        assert health["status"] in ["healthy", "needs_attention", "critical"]
        assert "score" in health
        assert health["total_tasks"] == 2
        assert health["completed_tasks"] == 1
    
    def test_assess_task_health(self, mock_agent, mock_tdd_task):
        """Test TDD task health assessment"""
        mock_agent.current_tdd_task = mock_tdd_task
        
        # Mock test results
        passing_test = Mock()
        passing_test.passed = True
        failing_test = Mock()
        failing_test.passed = False
        
        mock_tdd_task.test_results = [passing_test, failing_test]
        mock_tdd_task.current_state = TDDState.TEST_RED
        
        health = mock_agent._assess_task_health()
        
        assert health["status"] in ["healthy", "unhealthy", "needs_attention", "critical"]
        assert "score" in health
        assert health["total_tests"] == 2
        assert health["passing_tests"] == 1
        assert health["pass_rate"] == 50.0
    
    def test_is_tdd_enabled(self, mock_agent, mock_tdd_state_machine):
        """Test TDD mode detection"""
        # Without state machine
        assert not mock_agent.is_tdd_enabled()
        
        # With state machine
        mock_agent.tdd_state_machine = mock_tdd_state_machine
        assert mock_agent.is_tdd_enabled()
    
    def test_log_tdd_action(self, mock_agent, mock_tdd_cycle, mock_tdd_task):
        """Test TDD action logging"""
        mock_agent.set_tdd_context(None, mock_tdd_cycle, mock_tdd_task)
        
        with patch.object(mock_agent.logger, 'info') as mock_log:
            mock_agent.log_tdd_action("test_action", "test details")
            mock_log.assert_called_once()
            args = mock_log.call_args[0][0]
            assert "test_action" in args
            assert "test details" in args
            assert "cycle:test-cycle-001" in args
            assert "task:task-001" in args
    
    @pytest.mark.asyncio
    async def test_handle_tdd_task(self, mock_agent, mock_tdd_cycle):
        """Test TDD task handling"""
        with patch.object(mock_agent, 'validate_tdd_phase') as mock_validate, \
             patch.object(mock_agent, 'get_tdd_context') as mock_get_context, \
             patch.object(mock_agent, 'execute_tdd_phase') as mock_execute:
            
            mock_validate.return_value = AgentResult(success=True, output="Valid")
            mock_get_context.return_value = {"story_id": "story-123"}
            mock_execute.return_value = AgentResult(success=True, output="Executed")
            
            result = await mock_agent.handle_tdd_task(mock_tdd_cycle, TDDState.DESIGN)
            
            assert result.success
            mock_validate.assert_called_once()
            mock_get_context.assert_called_once()
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_tdd_phase_valid_transition(self, mock_agent):
        """Test valid TDD phase transition"""
        result = await mock_agent.validate_tdd_phase(TDDState.DESIGN, TDDState.TEST_RED)
        assert result.success
    
    @pytest.mark.asyncio
    async def test_validate_tdd_phase_invalid_transition(self, mock_agent):
        """Test invalid TDD phase transition"""
        result = await mock_agent.validate_tdd_phase(TDDState.TEST_RED, TDDState.DESIGN)
        assert not result.success
        assert "Invalid TDD phase transition" in result.error
    
    @pytest.mark.asyncio
    async def test_get_tdd_context(self, mock_agent, mock_tdd_cycle, mock_tdd_task):
        """Test TDD context retrieval"""
        mock_agent.set_tdd_context(None, mock_tdd_cycle, mock_tdd_task)
        
        context = await mock_agent.get_tdd_context("story-123")
        
        assert context["story_id"] == "story-123"
        assert context["agent_name"] == "DesignAgent"
        assert context["cycle_id"] == "test-cycle-001"
        assert context["task_id"] == "task-001"
        assert "agent_capabilities" in context
        assert "timestamp" in context
    
    def test_handle_tdd_error(self, mock_agent):
        """Test TDD error handling"""
        error = ValueError("Test error")
        result = mock_agent.handle_tdd_error(error, TDDState.DESIGN, "Custom recovery")
        
        assert not result.success
        assert "Test error" in result.error
        assert "error_report.json" in result.artifacts
        
        # Check error report content
        import json
        error_report = json.loads(result.artifacts["error_report.json"])
        assert error_report["phase"] == TDDState.DESIGN.value
        assert error_report["error_type"] == "ValueError"
        assert error_report["suggested_recovery"] == "Custom recovery"
        assert error_report["agent"] == "DesignAgent"


@pytest.mark.unit
class TestDesignAgentTDDCapabilities:
    """Test DesignAgent TDD-specific functionality"""
    
    @pytest.fixture
    def design_agent(self):
        """Create DesignAgent for testing"""
        return DesignAgent()
    
    @pytest.fixture
    def design_task(self):
        """Create design task for testing"""
        return Task(
            id="design-task-001",
            agent_type="DesignAgent",
            command="tdd_specification",
            context={
                "story": {
                    "id": "story-123",
                    "description": "User authentication system"
                }
            }
        )
    
    @pytest.mark.asyncio
    async def test_create_tdd_specification(self, design_agent, design_task):
        """Test TDD specification creation"""
        result = await design_agent._create_tdd_specification(design_task, dry_run=False)
        
        assert result.success
        assert "TDD specification" in result.output.lower()
        assert "tdd-specification.md" in result.artifacts
        assert "acceptance-criteria.md" in result.artifacts
        assert "test-plan.md" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_define_acceptance_criteria(self, design_agent, design_task):
        """Test acceptance criteria definition"""
        design_task.command = "acceptance_criteria"
        result = await design_agent._define_acceptance_criteria(design_task, dry_run=False)
        
        assert result.success
        assert "acceptance criteria" in result.output.lower()
        assert "acceptance-criteria.md" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_design_test_scenarios(self, design_agent, design_task):
        """Test test scenario design"""
        design_task.command = "test_scenarios"
        design_task.context["acceptance_criteria"] = ["User can log in", "User can log out"]
        
        result = await design_agent._design_test_scenarios(design_task, dry_run=False)
        
        assert result.success
        assert "test scenarios" in result.output.lower()
        assert "test-scenarios.md" in result.artifacts
        assert "edge-cases.md" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_create_api_contracts(self, design_agent, design_task):
        """Test API contract creation"""
        design_task.command = "api_contracts"
        result = await design_agent._create_api_contracts(design_task, dry_run=False)
        
        assert result.success
        assert "api contracts" in result.output.lower()
        assert "api-contracts.md" in result.artifacts
        assert "interface-definitions.json" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_design(self, design_agent):
        """Test executing TDD DESIGN phase"""
        context = {
            "story": {"id": "story-123", "description": "Test story"},
            "task_description": "Create design for authentication",
            "dry_run": False
        }
        
        result = await design_agent.execute_tdd_phase(TDDState.DESIGN, context)
        
        assert result.success
        assert "TDD Design Phase Complete" in result.output
        assert len(result.artifacts) > 0
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_invalid(self, design_agent):
        """Test executing invalid TDD phase for DesignAgent"""
        context = {"story": {"id": "story-123"}}
        
        result = await design_agent.execute_tdd_phase(TDDState.TEST_RED, context)
        
        assert not result.success
        assert "cannot execute TDD phase TEST_RED" in result.error
    
    def test_generate_tdd_spec_fallback(self, design_agent):
        """Test TDD specification generation fallback"""
        spec = design_agent._generate_tdd_spec_fallback("User authentication system")
        
        assert "TDD Specification" in spec
        assert "Testable Requirements" in spec
        assert "API Interface Design" in spec
        assert "Test-First Considerations" in spec
        assert "Edge Cases and Boundary Conditions" in spec
    
    def test_generate_acceptance_criteria(self, design_agent):
        """Test acceptance criteria generation"""
        criteria = design_agent._generate_acceptance_criteria("User can log in with email and password")
        
        assert "Acceptance Criteria" in criteria
        assert "Given-When-Then" in criteria
        assert "Happy Path" in criteria
        assert "Input Validation" in criteria
        assert "Definition of Done" in criteria
    
    def test_generate_test_scenarios(self, design_agent):
        """Test test scenario generation"""
        scenarios = design_agent._generate_test_scenarios("Login functionality", "User can log in")
        
        assert "Test Scenarios" in scenarios
        assert "Functional Tests" in scenarios
        assert "Integration Tests" in scenarios
        assert "Edge Cases" in scenarios
        assert "Performance Tests" in scenarios
        assert "Security Tests" in scenarios
    
    def test_generate_api_contracts(self, design_agent):
        """Test API contract generation"""
        contracts = design_agent._generate_api_contracts("User authentication API")
        
        assert "API Contracts" in contracts
        assert "REST API Design" in contracts
        assert "Data Models" in contracts
        assert "Service Layer Contracts" in contracts
        assert "Error Handling Contracts" in contracts


@pytest.mark.unit
class TestQAAgentTDDCapabilities:
    """Test QAAgent TDD-specific functionality"""
    
    @pytest.fixture
    def qa_agent(self):
        """Create QAAgent for testing"""
        return QAAgent()
    
    @pytest.fixture
    def qa_task(self):
        """Create QA task for testing"""
        return Task(
            id="qa-task-001",
            agent_type="QAAgent",
            command="write_failing_tests",
            context={
                "story": {"id": "story-123", "description": "User authentication"},
                "acceptance_criteria": ["User can log in", "User can log out"],
                "test_scenarios": ["Happy path login", "Invalid credentials"]
            }
        )
    
    @pytest.mark.asyncio
    async def test_write_failing_tests(self, qa_agent, qa_task):
        """Test failing test creation for TDD"""
        result = await qa_agent._write_failing_tests(qa_task, dry_run=False)
        
        assert result.success
        assert "failing tests" in result.output.lower()
        assert any("test_" in filename for filename in result.artifacts.keys())
    
    @pytest.mark.asyncio
    async def test_validate_test_red_state(self, qa_agent, qa_task):
        """Test RED state validation"""
        qa_task.command = "validate_test_red_state"
        qa_task.context["test_files"] = ["tests/test_auth.py", "tests/test_login.py"]
        
        result = await qa_agent._validate_test_red_state(qa_task, dry_run=False)
        
        assert result.success
        assert "RED state" in result.output
    
    @pytest.mark.asyncio
    async def test_organize_test_files(self, qa_agent, qa_task):
        """Test test file organization"""
        qa_task.command = "organize_test_files"
        qa_task.context["test_files"] = ["test_auth.py", "test_user.py"]
        
        result = await qa_agent._organize_test_files(qa_task, dry_run=False)
        
        assert result.success
        assert "organized" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_check_test_coverage(self, qa_agent, qa_task):
        """Test coverage checking"""
        qa_task.command = "check_test_coverage"
        qa_task.context["source_files"] = ["src/auth.py", "src/user.py"]
        
        result = await qa_agent._check_test_coverage(qa_task, dry_run=False)
        
        assert result.success
        assert "coverage" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_test_red(self, qa_agent):
        """Test executing TDD TEST_RED phase"""
        context = {
            "story": {"id": "story-123", "description": "Authentication"},
            "acceptance_criteria": ["User can log in"],
            "test_scenarios": ["Happy path"],
            "dry_run": False
        }
        
        result = await qa_agent.execute_tdd_phase(TDDState.TEST_RED, context)
        
        assert result.success
        assert "TEST_RED Phase Complete" in result.output
        assert len(result.artifacts) > 0
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_invalid(self, qa_agent):
        """Test executing invalid TDD phase for QAAgent"""
        context = {"story": {"id": "story-123"}}
        
        result = await qa_agent.execute_tdd_phase(TDDState.CODE_GREEN, context)
        
        assert not result.success
        assert "cannot execute TDD phase CODE_GREEN" in result.error


@pytest.mark.unit
class TestCodeAgentTDDCapabilities:
    """Test CodeAgent TDD-specific functionality"""
    
    @pytest.fixture
    def code_agent(self):
        """Create CodeAgent for testing"""
        return CodeAgent()
    
    @pytest.fixture
    def code_task(self):
        """Create code task for testing"""
        return Task(
            id="code-task-001",
            agent_type="CodeAgent",
            command="implement_minimal_solution",
            context={
                "story_id": "story-123",
                "failing_tests": ["test_login_success", "test_login_failure"],
                "test_files": ["tests/test_auth.py"]
            }
        )
    
    @pytest.mark.asyncio
    async def test_implement_minimal_solution(self, code_agent, code_task):
        """Test minimal implementation for GREEN phase"""
        result = await code_agent._implement_minimal_solution(code_task, dry_run=False)
        
        assert result.success
        assert "minimal implementation" in result.output.lower()
        assert "test_results.json" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_validate_test_green_state(self, code_agent, code_task):
        """Test GREEN state validation"""
        code_task.command = "validate_test_green_state"
        code_task.context["implementation_files"] = ["src/auth.py"]
        
        result = await code_agent._validate_test_green_state(code_task, dry_run=False)
        
        assert result.success
        assert "GREEN State Validation" in result.output
    
    @pytest.mark.asyncio
    async def test_refactor_implementation(self, code_agent, code_task):
        """Test implementation refactoring"""
        code_task.command = "refactor_implementation"
        code_task.context["implementation_files"] = ["src/auth.py", "src/user.py"]
        code_task.context["refactor_goals"] = ["improve_readability", "reduce_complexity"]
        
        result = await code_agent._refactor_implementation(code_task, dry_run=False)
        
        assert result.success
        assert "refactoring" in result.output.lower()
        assert "refactor_report.json" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_commit_tdd_cycle(self, code_agent, code_task):
        """Test TDD cycle commit"""
        code_task.command = "commit_tdd_cycle"
        code_task.context["implementation_files"] = ["src/auth.py"]
        code_task.context["test_files"] = ["tests/test_auth.py"]
        code_task.context["commit_message"] = "Complete TDD cycle for authentication"
        
        result = await code_agent._commit_tdd_cycle(code_task, dry_run=False)
        
        assert result.success
        assert "commit" in result.output.lower()
        assert "commit_details.json" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_execute_code_green_phase(self, code_agent):
        """Test executing CODE_GREEN phase"""
        context = {
            "test_files": ["tests/test_auth.py"],
            "story_id": "story-123",
            "failing_tests": ["test_login"],
            "dry_run": False
        }
        
        result = await code_agent._execute_code_green_phase(context)
        
        assert result.success
        assert "CODE_GREEN Phase Complete" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_refactor_phase(self, code_agent):
        """Test executing REFACTOR phase"""
        context = {
            "implementation_files": ["src/auth.py"],
            "story_id": "story-123",
            "dry_run": False
        }
        
        result = await code_agent._execute_refactor_phase(context)
        
        assert result.success
        assert "REFACTOR Phase Complete" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_commit_phase(self, code_agent):
        """Test executing COMMIT phase"""
        context = {
            "implementation_files": ["src/auth.py"],
            "test_files": ["tests/test_auth.py"],
            "story_id": "story-123",
            "dry_run": False
        }
        
        result = await code_agent._execute_commit_phase(context)
        
        assert result.success
        assert "COMMIT Phase Complete" in result.output
    
    @pytest.mark.asyncio
    async def test_analyze_failing_tests(self, code_agent):
        """Test failing test analysis"""
        test_files = ["tests/test_auth.py", "tests/test_user.py"]
        analysis = await code_agent._analyze_failing_tests(test_files)
        
        assert isinstance(analysis, dict)
        assert "required_classes" in analysis
        assert "required_methods" in analysis
        assert "required_interfaces" in analysis
    
    @pytest.mark.asyncio
    async def test_generate_minimal_implementation(self, code_agent):
        """Test minimal implementation generation"""
        test_analysis = {
            "required_classes": ["AuthService"],
            "required_methods": ["login", "logout"],
            "data_models": True,
            "requires_persistence": True,
            "requires_api": True
        }
        
        implementation = await code_agent._generate_minimal_implementation(test_analysis, "auth")
        
        assert isinstance(implementation, dict)
        assert any("auth_module.py" in path for path in implementation.keys())
        assert any("auth_models.py" in path for path in implementation.keys())
        assert any("auth_repository.py" in path for path in implementation.keys())
        assert any("auth_api.py" in path for path in implementation.keys())
    
    def test_generate_main_module(self, code_agent):
        """Test main module generation"""
        test_analysis = {"required_classes": ["AuthService"]}
        module_code = code_agent._generate_main_module(test_analysis, "auth")
        
        assert "AuthException" in module_code
        assert "AuthModel" in module_code
        assert "AuthService" in module_code
        assert "create_item" in module_code
        assert "get_item" in module_code
    
    def test_generate_interfaces(self, code_agent):
        """Test interface generation"""
        test_analysis = {"required_interfaces": ["Repository", "EventBus"]}
        interfaces_code = code_agent._generate_interfaces(test_analysis, "auth")
        
        assert "AuthRepository" in interfaces_code
        assert "AuthEventBus" in interfaces_code
        assert "AuthValidator" in interfaces_code
        assert "abstractmethod" in interfaces_code
    
    def test_generate_models(self, code_agent):
        """Test models generation"""
        test_analysis = {"data_models": ["AuthData", "AuthRequest"]}
        models_code = code_agent._generate_models(test_analysis, "auth")
        
        assert "AuthData" in models_code
        assert "AuthRequest" in models_code
        assert "AuthResponse" in models_code
        assert "dataclass" in models_code
    
    def test_generate_repository(self, code_agent):
        """Test repository generation"""
        test_analysis = {"requires_persistence": True}
        repository_code = code_agent._generate_repository(test_analysis, "auth")
        
        assert "AuthFileRepository" in repository_code
        assert "save" in repository_code
        assert "find_by_id" in repository_code
        assert "delete" in repository_code
    
    def test_generate_api_layer(self, code_agent):
        """Test API layer generation"""
        test_analysis = {"requires_api": True}
        api_code = code_agent._generate_api_layer(test_analysis, "auth")
        
        assert "AuthAPI" in api_code
        assert "create" in api_code
        assert "get" in api_code
        assert "update" in api_code
        assert "delete" in api_code


if __name__ == "__main__":
    pytest.main([__file__])