"""
Unit tests for Mock Agent.

Tests the mock implementation of agents used for NO-AGENT mode testing
and state machine validation without making actual AI calls.
"""

import pytest
import asyncio
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agents.mock_agent import (
    MockAgent, MockDesignAgent, MockQAAgent, MockCodeAgent, 
    MockDataAgent, create_mock_agent
)
from lib.agents import Task, AgentResult, TDDState
from lib.agent_tool_config import AgentType


class TestMockAgent:
    """Test the MockAgent base class."""
    
    @pytest.fixture
    def mock_context_manager(self):
        """Create a mock context manager."""
        return Mock()
    
    @pytest.fixture
    def mock_agent(self, mock_context_manager):
        """Create a MockAgent for testing."""
        return MockAgent(
            agent_type="TestAgent",
            capabilities=["test_capability", "mock_execution"],
            context_manager=mock_context_manager
        )
    
    def test_mock_agent_init(self, mock_agent, mock_context_manager):
        """Test MockAgent initialization."""
        assert mock_agent.name == "MockTestAgent"
        assert mock_agent.agent_type == "TestAgent"
        assert mock_agent.execution_count == 0
        assert mock_agent.failure_rate == 0.1
        assert mock_agent.context_manager == mock_context_manager
        
        # Check capabilities
        expected_capabilities = ["test_capability", "mock_execution"]
        for capability in expected_capabilities:
            assert capability in mock_agent.capabilities

    def test_mock_agent_init_default_capabilities(self):
        """Test MockAgent initialization with default capabilities."""
        agent = MockAgent("CustomAgent")
        
        assert agent.name == "MockCustomAgent"
        assert agent.agent_type == "CustomAgent"
        expected_capabilities = [
            "mock_customagent_task",
            "mock_execution", 
            "mock_validation"
        ]
        for capability in expected_capabilities:
            assert capability in agent.capabilities

    @pytest.mark.asyncio
    async def test_run_success_dry_run(self, mock_agent):
        """Test successful mock execution in dry run mode."""
        task = Task(
            id="test-1",
            agent_type="TestAgent",
            command="test operation",
            context={"test": "data"}
        )
        
        result = await mock_agent.run(task, dry_run=True)
        
        assert result.success
        assert "MockTestAgent: Task 'test operation' completed successfully" in result.output
        assert "mock_data.json" in result.artifacts
        assert result.execution_time >= 0
        assert mock_agent.execution_count == 1

    @pytest.mark.asyncio
    async def test_run_success_normal(self, mock_agent):
        """Test successful mock execution in normal mode."""
        task = Task(
            id="test-2",
            agent_type="TestAgent",
            command="design architecture",
            context={"requirements": "test system"}
        )
        
        # Patch random to ensure no failure
        with patch('random.random', return_value=0.0):  # Below failure rate
            result = await mock_agent.run(task, dry_run=False)
        
        assert result.success
        assert "test system" in result.output
        assert "mock_data.json" in result.artifacts
        assert result.execution_time > 0  # Should have processing delay
        
        # Check artifact content
        artifact_data = json.loads(result.artifacts["mock_data.json"])
        assert artifact_data["mock_execution"] is True
        assert artifact_data["agent_type"] == "TestAgent"
        assert artifact_data["execution_count"] == 1

    @pytest.mark.asyncio
    async def test_run_simulated_failure(self, mock_agent):
        """Test simulated failure scenario."""
        task = Task(
            id="test-3",
            agent_type="TestAgent",
            command="test operation",
            context={}
        )
        
        # Patch random to force failure
        with patch('random.random', return_value=0.95):  # Above failure rate
            result = await mock_agent.run(task, dry_run=False)
        
        assert not result.success
        assert "MockTestAgent:" in result.error
        assert "mock_failure.json" in result.artifacts
        assert result.execution_time > 0
        
        # Check failure artifact
        failure_data = json.loads(result.artifacts["mock_failure.json"])
        assert failure_data["mock_execution"] is True
        assert failure_data["failure_simulation"] is True

    @pytest.mark.asyncio
    async def test_run_exception_handling(self, mock_agent):
        """Test exception handling in mock execution."""
        task = Task(
            id="test-4",
            agent_type="TestAgent",
            command="test operation",
            context={}
        )
        
        # Patch to raise exception
        with patch.object(mock_agent, '_generate_mock_response', side_effect=Exception("Test exception")):
            result = await mock_agent.run(task, dry_run=False)
        
        assert not result.success
        assert "Mock execution error: Test exception" in result.error
        assert "mock_error.json" in result.artifacts
        assert result.execution_time >= 0

    def test_get_processing_time_design(self, mock_agent):
        """Test processing time for design commands."""
        time_val = mock_agent._get_processing_time("design architecture")
        assert 1.5 <= time_val <= 3.0

    def test_get_processing_time_test(self, mock_agent):
        """Test processing time for test commands."""
        time_val = mock_agent._get_processing_time("write tests")
        assert 2.0 <= time_val <= 4.0

    def test_get_processing_time_code(self, mock_agent):
        """Test processing time for code commands."""
        time_val = mock_agent._get_processing_time("implement feature")
        assert 3.0 <= time_val <= 6.0

    def test_get_processing_time_refactor(self, mock_agent):
        """Test processing time for refactor commands."""
        time_val = mock_agent._get_processing_time("refactor code")
        assert 2.0 <= time_val <= 4.0

    def test_get_processing_time_analyze(self, mock_agent):
        """Test processing time for analysis commands."""
        time_val = mock_agent._get_processing_time("analyze performance")
        assert 1.0 <= time_val <= 2.5

    def test_get_processing_time_default(self, mock_agent):
        """Test processing time for unknown commands."""
        time_val = mock_agent._get_processing_time("unknown command")
        assert 1.0 <= time_val <= 3.0

    def test_create_failure_result(self, mock_agent):
        """Test failure result creation."""
        task = Task(id="test", agent_type="TestAgent", command="test", context={})
        
        result = mock_agent._create_failure_result(task, 2.5)
        
        assert not result.success
        assert "MockTestAgent:" in result.error
        assert "mock_failure.json" in result.artifacts
        assert result.execution_time == 2.5
        
        # Check failure artifact
        failure_data = json.loads(result.artifacts["mock_failure.json"])
        assert failure_data["processing_time"] == 2.5

    def test_generate_mock_response_design(self, mock_agent):
        """Test mock response generation for design commands."""
        task = Task(id="test", agent_type="TestAgent", command="design system", 
                   context={"story_id": "STORY-123"})
        
        response = mock_agent._generate_mock_response(task)
        
        assert "MockDesignAgent" in response
        assert "STORY-123" in response
        assert "Mock Technical Specification" in response
        assert "Acceptance Criteria" in response

    def test_generate_mock_response_test_red(self, mock_agent):
        """Test mock response generation for test RED commands."""
        task = Task(id="test", agent_type="TestAgent", command="test red phase",
                   context={"story_id": "STORY-456"})
        
        response = mock_agent._generate_mock_response(task)
        
        assert "MockQAAgent" in response
        assert "STORY-456" in response
        assert "Failing tests created" in response
        assert "RED State" in response

    def test_generate_mock_response_implement(self, mock_agent):
        """Test mock response generation for implementation commands."""
        task = Task(id="test", agent_type="TestAgent", command="implement feature",
                   context={"story_id": "STORY-789"})
        
        response = mock_agent._generate_mock_response(task)
        
        assert "MockCodeAgent" in response
        assert "STORY-789" in response
        assert "Implementation completed" in response
        assert "GREEN State" in response

    def test_generate_mock_response_refactor(self, mock_agent):
        """Test mock response generation for refactor commands."""
        task = Task(id="test", agent_type="TestAgent", command="refactor implementation",
                   context={"story_id": "STORY-101"})
        
        response = mock_agent._generate_mock_response(task)
        
        assert "MockCodeAgent" in response
        assert "STORY-101" in response
        assert "Refactoring completed" in response
        assert "Still GREEN" in response

    def test_generate_mock_response_analyze(self, mock_agent):
        """Test mock response generation for analysis commands."""
        task = Task(id="test", agent_type="TestAgent", command="analyze quality", context={})
        
        response = mock_agent._generate_mock_response(task)
        
        assert "MockTestAgent" in response
        assert "Analysis completed" in response
        assert "Quality Metrics" in response
        assert "mock" in response.lower()

    def test_generate_mock_response_default(self, mock_agent):
        """Test mock response generation for default commands."""
        task = Task(id="test", agent_type="TestAgent", command="unknown operation", context={})
        
        response = mock_agent._generate_mock_response(task)
        
        assert "MockTestAgent: Task 'unknown operation' completed successfully" == response

    def test_mock_design_response(self, mock_agent):
        """Test design-specific mock response."""
        context = {"story_id": "USER-123"}
        
        response = mock_agent._mock_design_response(context)
        
        assert "MockDesignAgent" in response
        assert "USER-123" in response
        assert "Design specifications completed" in response
        assert "Mock Technical Specification" in response
        assert "API Design" in response
        assert "def mock_function():" in response

    def test_mock_test_red_response(self, mock_agent):
        """Test test RED-specific mock response."""
        context = {"story_id": "AUTH-456"}
        
        response = mock_agent._mock_test_red_response(context)
        
        assert "MockQAAgent" in response
        assert "AUTH-456" in response
        assert "Failing tests created" in response
        assert "5 failed, 0 passed" in response
        assert "Ready for implementation" in response

    def test_mock_code_response(self, mock_agent):
        """Test code implementation mock response."""
        context = {"story_id": "PAYMENT-789"}
        
        response = mock_agent._mock_code_response(context)
        
        assert "MockCodeAgent" in response
        assert "PAYMENT-789" in response
        assert "Implementation completed" in response
        assert "5 passed, 0 failed" in response
        assert "Ready for REFACTOR phase" in response

    def test_mock_refactor_response(self, mock_agent):
        """Test refactor mock response."""
        context = {"story_id": "REFACTOR-101"}
        
        response = mock_agent._mock_refactor_response(context)
        
        assert "MockCodeAgent" in response
        assert "REFACTOR-101" in response
        assert "Refactoring completed" in response
        assert "Code quality improved" in response
        assert "Ready for COMMIT phase" in response

    def test_mock_analysis_response(self, mock_agent):
        """Test analysis mock response."""
        context = {}
        
        response = mock_agent._mock_analysis_response(context)
        
        assert "MockTestAgent" in response
        assert "Analysis completed" in response
        assert "Quality Metrics" in response
        assert "95%" in response
        assert "mock" in response.lower()


class TestSpecializedMockAgents:
    """Test specialized mock agent implementations."""
    
    @pytest.fixture
    def mock_context_manager(self):
        """Create a mock context manager."""
        return Mock()
    
    def test_mock_design_agent_init(self, mock_context_manager):
        """Test MockDesignAgent initialization."""
        agent = MockDesignAgent(context_manager=mock_context_manager)
        
        assert agent.name == "MockDesignAgent"
        assert agent.agent_type == "DesignAgent"
        assert agent.context_manager == mock_context_manager
        
        expected_capabilities = [
            "tdd_specification",
            "acceptance_criteria", 
            "technical_design",
            "api_design",
            "mock_design"
        ]
        for capability in expected_capabilities:
            assert capability in agent.capabilities

    def test_mock_qa_agent_init(self, mock_context_manager):
        """Test MockQAAgent initialization."""
        agent = MockQAAgent(context_manager=mock_context_manager)
        
        assert agent.name == "MockQAAgent"
        assert agent.agent_type == "QAAgent"
        
        expected_capabilities = [
            "failing_test_creation",
            "test_validation",
            "red_state_verification",
            "test_organization",
            "mock_testing"
        ]
        for capability in expected_capabilities:
            assert capability in agent.capabilities

    def test_mock_code_agent_init(self, mock_context_manager):
        """Test MockCodeAgent initialization."""
        agent = MockCodeAgent(context_manager=mock_context_manager)
        
        assert agent.name == "MockCodeAgent"
        assert agent.agent_type == "CodeAgent"
        
        expected_capabilities = [
            "minimal_implementation",
            "test_green_validation", 
            "code_refactoring",
            "tdd_commits",
            "mock_implementation"
        ]
        for capability in expected_capabilities:
            assert capability in agent.capabilities

    def test_mock_data_agent_init(self, mock_context_manager):
        """Test MockDataAgent initialization."""
        agent = MockDataAgent(context_manager=mock_context_manager)
        
        assert agent.name == "MockDataAgent"
        assert agent.agent_type == "DataAgent"
        
        expected_capabilities = [
            "tdd_metrics_analysis",
            "performance_tracking",
            "quality_reporting",
            "mock_analytics"
        ]
        for capability in expected_capabilities:
            assert capability in agent.capabilities

    @pytest.mark.asyncio
    async def test_mock_design_agent_execution(self, mock_context_manager):
        """Test MockDesignAgent execution."""
        agent = MockDesignAgent(context_manager=mock_context_manager)
        task = Task(id="test", agent_type="DesignAgent", command="create specification", 
                   context={"story_id": "DESIGN-123"})
        
        with patch('random.random', return_value=0.0):  # Ensure success
            result = await agent.run(task, dry_run=False)
        
        assert result.success
        assert "DESIGN-123" in result.output
        assert "Mock Technical Specification" in result.output

    @pytest.mark.asyncio
    async def test_mock_qa_agent_execution(self, mock_context_manager):
        """Test MockQAAgent execution."""
        agent = MockQAAgent(context_manager=mock_context_manager)
        task = Task(id="test", agent_type="QAAgent", command="test red validation",
                   context={"story_id": "QA-456"})
        
        with patch('random.random', return_value=0.0):  # Ensure success
            result = await agent.run(task, dry_run=False)
        
        assert result.success
        assert "QA-456" in result.output
        assert "RED State" in result.output

    @pytest.mark.asyncio
    async def test_mock_code_agent_execution(self, mock_context_manager):
        """Test MockCodeAgent execution."""
        agent = MockCodeAgent(context_manager=mock_context_manager)
        task = Task(id="test", agent_type="CodeAgent", command="implement minimal",
                   context={"story_id": "CODE-789"})
        
        with patch('random.random', return_value=0.0):  # Ensure success
            result = await agent.run(task, dry_run=False)
        
        assert result.success
        assert "CODE-789" in result.output
        assert "GREEN State" in result.output

    @pytest.mark.asyncio
    async def test_mock_data_agent_execution(self, mock_context_manager):
        """Test MockDataAgent execution."""
        agent = MockDataAgent(context_manager=mock_context_manager)
        task = Task(id="test", agent_type="DataAgent", command="analyze metrics",
                   context={})
        
        with patch('random.random', return_value=0.0):  # Ensure success
            result = await agent.run(task, dry_run=False)
        
        assert result.success
        assert "Analysis completed" in result.output
        assert "Quality Metrics" in result.output


class TestMockAgentFactory:
    """Test the mock agent factory function."""
    
    def test_create_mock_agent_design(self):
        """Test creating mock design agent."""
        agent = create_mock_agent("DesignAgent")
        
        assert isinstance(agent, MockDesignAgent)
        assert agent.agent_type == "DesignAgent"

    def test_create_mock_agent_design_lowercase(self):
        """Test creating mock design agent with lowercase."""
        agent = create_mock_agent("designagent")
        
        assert isinstance(agent, MockDesignAgent)
        assert agent.agent_type == "DesignAgent"

    def test_create_mock_agent_qa(self):
        """Test creating mock QA agent."""
        agent = create_mock_agent("QAAgent")
        
        assert isinstance(agent, MockQAAgent)
        assert agent.agent_type == "QAAgent"

    def test_create_mock_agent_qa_test(self):
        """Test creating mock QA agent with 'test' in name."""
        agent = create_mock_agent("TestAgent")
        
        assert isinstance(agent, MockQAAgent)
        assert agent.agent_type == "QAAgent"

    def test_create_mock_agent_code(self):
        """Test creating mock code agent."""
        agent = create_mock_agent("CodeAgent")
        
        assert isinstance(agent, MockCodeAgent)
        assert agent.agent_type == "CodeAgent"

    def test_create_mock_agent_data(self):
        """Test creating mock data agent."""
        agent = create_mock_agent("DataAgent")
        
        assert isinstance(agent, MockDataAgent)
        assert agent.agent_type == "DataAgent"

    def test_create_mock_agent_analytics(self):
        """Test creating mock data agent with 'analytics' in name."""
        agent = create_mock_agent("AnalyticsAgent")
        
        assert isinstance(agent, MockDataAgent)
        assert agent.agent_type == "DataAgent"

    def test_create_mock_agent_unknown(self):
        """Test creating mock agent for unknown type."""
        agent = create_mock_agent("UnknownAgent")
        
        assert isinstance(agent, MockAgent)
        assert agent.agent_type == "UnknownAgent"

    def test_create_mock_agent_with_context(self):
        """Test creating mock agent with context manager."""
        mock_context = Mock()
        agent = create_mock_agent("DesignAgent", context_manager=mock_context)
        
        assert isinstance(agent, MockDesignAgent)
        assert agent.context_manager == mock_context


class TestMockAgentRealism:
    """Test the realism of mock agent behavior."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        return MockAgent("TestAgent")
    
    @pytest.mark.asyncio
    async def test_execution_count_increments(self, mock_agent):
        """Test that execution count increments with each run."""
        task = Task(id="test", agent_type="TestAgent", command="test", context={})
        
        assert mock_agent.execution_count == 0
        
        with patch('random.random', return_value=0.0):  # Ensure success
            await mock_agent.run(task, dry_run=False)
            assert mock_agent.execution_count == 1
            
            await mock_agent.run(task, dry_run=False)
            assert mock_agent.execution_count == 2
            
            await mock_agent.run(task, dry_run=False)
            assert mock_agent.execution_count == 3

    @pytest.mark.asyncio
    async def test_processing_time_simulation(self, mock_agent):
        """Test that processing time is realistic."""
        task = Task(id="test", agent_type="TestAgent", command="implement feature", context={})
        
        start_time = time.time()
        with patch('random.random', return_value=0.0):  # Ensure success
            result = await mock_agent.run(task, dry_run=False)
        execution_time = time.time() - start_time
        
        # Should take time due to asyncio.sleep in processing
        assert execution_time >= 3.0  # Minimum for implement commands
        assert result.execution_time >= 3.0
        assert result.success

    @pytest.mark.asyncio
    async def test_no_processing_time_in_dry_run(self, mock_agent):
        """Test that dry run doesn't simulate processing time."""
        task = Task(id="test", agent_type="TestAgent", command="implement feature", context={})
        
        start_time = time.time()
        result = await mock_agent.run(task, dry_run=True)
        execution_time = time.time() - start_time
        
        # Should be very fast in dry run
        assert execution_time < 0.1
        assert result.success

    @pytest.mark.asyncio
    async def test_failure_rate_simulation(self, mock_agent):
        """Test that failure rate is simulated correctly."""
        task = Task(id="test", agent_type="TestAgent", command="test", context={})
        
        # Test multiple runs to check failure rate
        successes = 0
        failures = 0
        
        for i in range(100):
            # Use deterministic random for testing
            with patch('random.random', return_value=0.05 if i < 90 else 0.95):
                result = await mock_agent.run(task, dry_run=False)
                if result.success:
                    successes += 1
                else:
                    failures += 1
        
        # Should have ~90% success rate (10% failure rate)
        assert successes == 90
        assert failures == 10

    @pytest.mark.asyncio
    async def test_artifact_consistency(self, mock_agent):
        """Test that artifacts are consistent and realistic."""
        task = Task(id="test", agent_type="TestAgent", command="design architecture", 
                   context={"story_id": "ARCH-123"})
        
        with patch('random.random', return_value=0.0):  # Ensure success
            result = await mock_agent.run(task, dry_run=False)
        
        assert result.success
        assert "mock_data.json" in result.artifacts
        
        # Check artifact data
        artifact_data = json.loads(result.artifacts["mock_data.json"])
        assert artifact_data["mock_execution"] is True
        assert artifact_data["agent_type"] == "TestAgent"
        assert artifact_data["execution_count"] == 1
        assert "processing_time" in artifact_data

    @pytest.mark.asyncio
    async def test_story_context_preservation(self, mock_agent):
        """Test that story context is preserved in responses."""
        task = Task(id="test", agent_type="TestAgent", command="design specs",
                   context={"story_id": "CONTEXT-999"})
        
        with patch('random.random', return_value=0.0):  # Ensure success
            result = await mock_agent.run(task, dry_run=False)
        
        assert result.success
        assert "CONTEXT-999" in result.output
        # Should contain design-specific mock content
        assert "Mock Technical Specification" in result.output

    @pytest.mark.asyncio
    async def test_command_specific_responses(self, mock_agent):
        """Test that responses vary based on command type."""
        base_task = Task(id="test", agent_type="TestAgent", command="", context={"story_id": "TEST-123"})
        
        with patch('random.random', return_value=0.0):  # Ensure success
            # Test design command
            base_task.command = "design architecture"
            design_result = await mock_agent.run(base_task, dry_run=False)
            
            # Test test command
            base_task.command = "test red phase"
            test_result = await mock_agent.run(base_task, dry_run=False)
            
            # Test code command
            base_task.command = "implement feature"
            code_result = await mock_agent.run(base_task, dry_run=False)
        
        # Each should have different response patterns
        assert "MockDesignAgent" in design_result.output
        assert "MockQAAgent" in test_result.output
        assert "MockCodeAgent" in code_result.output
        
        # All should reference the story
        assert "TEST-123" in design_result.output
        assert "TEST-123" in test_result.output
        assert "TEST-123" in code_result.output