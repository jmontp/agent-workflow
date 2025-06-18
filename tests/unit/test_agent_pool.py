"""
Unit tests for Agent Pool Management System.

Tests the dynamic agent spawning, load balancing, and failure isolation
for parallel TDD execution with intelligent resource allocation.
"""

import pytest
import asyncio
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agent_pool import (
    AgentPool, PooledAgent, AgentMetrics, PoolConfiguration, PoolStatistics,
    AgentPoolStrategy, AgentStatus, LoadBalancingAlgorithm
)
from lib.agents import BaseAgent, Task, TaskStatus, AgentResult
from lib.context_manager import ContextManager


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, agent_type="TestAgent"):
        super().__init__(name=agent_type, capabilities=["test", "mock"])
        self.agent_type = agent_type
        self.execution_results = []
        self.fail_next = False
        self.delay_seconds = 0
    
    async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
        """Implementation of abstract run method"""
        return await self._execute_with_retry(task, dry_run)
    
    async def _execute_with_retry(self, task, dry_run=False):
        """Mock task execution"""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)
        
        if self.fail_next:
            self.fail_next = False
            return AgentResult(success=False, error="Mock failure")
        
        result = AgentResult(success=True, output="Mock result", artifacts={})
        self.execution_results.append(result)
        return result


class TestAgentMetrics:
    """Test the AgentMetrics dataclass."""
    
    def test_agent_metrics_creation(self):
        """Test creating AgentMetrics with default values."""
        metrics = AgentMetrics()
        
        assert metrics.total_tasks == 0
        assert metrics.successful_tasks == 0
        assert metrics.failed_tasks == 0
        assert metrics.average_execution_time == 0.0
        assert metrics.last_task_time is None
        assert metrics.cpu_usage == 0.0
        assert metrics.memory_usage == 0.0
        assert metrics.error_rate == 0.0
        assert isinstance(metrics.uptime, timedelta)

    def test_agent_metrics_success_rate(self):
        """Test success rate calculation."""
        metrics = AgentMetrics(total_tasks=10, successful_tasks=8, failed_tasks=2)
        
        assert metrics.success_rate == 80.0
        
        # Test with no tasks
        empty_metrics = AgentMetrics()
        assert empty_metrics.success_rate == 0.0

    def test_agent_metrics_load_score(self):
        """Test load score calculation."""
        now = datetime.utcnow()
        metrics = AgentMetrics(
            total_tasks=5,
            last_task_time=now - timedelta(minutes=5),
            error_rate=0.1
        )
        
        load_score = metrics.load_score
        assert load_score >= 0
        assert isinstance(load_score, float)


class TestPooledAgent:
    """Test the PooledAgent dataclass."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        return MockAgent("TestAgent")
    
    def test_pooled_agent_creation(self, mock_agent):
        """Test creating a PooledAgent."""
        pooled_agent = PooledAgent(
            agent=mock_agent,
            agent_id="test-123",
            agent_type="TestAgent"
        )
        
        assert pooled_agent.agent == mock_agent
        assert pooled_agent.agent_id == "test-123"
        assert pooled_agent.agent_type == "TestAgent"
        assert pooled_agent.status == AgentStatus.IDLE
        assert pooled_agent.current_task_id is None
        assert isinstance(pooled_agent.assigned_cycles, set)
        assert isinstance(pooled_agent.created_at, datetime)
        assert isinstance(pooled_agent.metrics, AgentMetrics)

    def test_pooled_agent_is_available(self, mock_agent):
        """Test availability check."""
        pooled_agent = PooledAgent(
            agent=mock_agent,
            agent_id="test-123",
            agent_type="TestAgent",
            max_concurrent_tasks=2
        )
        
        # Available when idle and no tasks
        assert pooled_agent.is_available
        
        # Not available when busy
        pooled_agent.status = AgentStatus.BUSY
        assert not pooled_agent.is_available
        
        # Not available when at max tasks
        pooled_agent.status = AgentStatus.IDLE
        pooled_agent.current_tasks.add("task1")
        pooled_agent.current_tasks.add("task2")
        assert not pooled_agent.is_available

    def test_pooled_agent_load_factor(self, mock_agent):
        """Test load factor calculation."""
        pooled_agent = PooledAgent(
            agent=mock_agent,
            agent_id="test-123",
            agent_type="TestAgent",
            max_concurrent_tasks=4
        )
        
        # No tasks
        assert pooled_agent.load_factor == 0.0
        
        # Half capacity
        pooled_agent.current_tasks.add("task1")
        pooled_agent.current_tasks.add("task2")
        assert pooled_agent.load_factor == 0.5
        
        # Full capacity
        pooled_agent.current_tasks.add("task3")
        pooled_agent.current_tasks.add("task4")
        assert pooled_agent.load_factor == 1.0

    def test_pooled_agent_uptime(self, mock_agent):
        """Test uptime calculation."""
        created_time = datetime.utcnow() - timedelta(hours=2)
        pooled_agent = PooledAgent(
            agent=mock_agent,
            agent_id="test-123",
            agent_type="TestAgent",
            created_at=created_time
        )
        
        uptime = pooled_agent.uptime
        assert uptime.total_seconds() >= 7200  # At least 2 hours
        assert isinstance(uptime, timedelta)


class TestPoolConfiguration:
    """Test the PoolConfiguration dataclass."""
    
    def test_pool_configuration_defaults(self):
        """Test default pool configuration."""
        config = PoolConfiguration()
        
        assert config.min_agents_per_type["DesignAgent"] == 1
        assert config.min_agents_per_type["CodeAgent"] == 2
        assert config.max_agents_per_type["CodeAgent"] == 5
        assert config.scaling_thresholds["scale_up_threshold"] == 0.8
        assert config.agent_timeout_minutes == 30
        assert config.failure_threshold == 3

    def test_pool_configuration_custom(self):
        """Test custom pool configuration."""
        config = PoolConfiguration(
            min_agents_per_type={"TestAgent": 5},
            max_agents_per_type={"TestAgent": 10},
            agent_timeout_minutes=60,
            failure_threshold=5
        )
        
        assert config.min_agents_per_type["TestAgent"] == 5
        assert config.max_agents_per_type["TestAgent"] == 10
        assert config.agent_timeout_minutes == 60
        assert config.failure_threshold == 5


class TestPoolStatistics:
    """Test the PoolStatistics dataclass."""
    
    def test_pool_statistics_defaults(self):
        """Test default pool statistics."""
        stats = PoolStatistics()
        
        assert stats.total_agents == 0
        assert stats.active_agents == 0
        assert stats.idle_agents == 0
        assert stats.failed_agents == 0
        assert stats.total_tasks_processed == 0
        assert stats.successful_tasks == 0
        assert stats.failed_tasks == 0
        assert stats.average_task_time == 0.0
        assert stats.pool_utilization == 0.0
        assert stats.scaling_events == 0


class TestAgentPool:
    """Test the AgentPool class."""
    
    @pytest.fixture
    def mock_context_manager(self):
        """Create a mock context manager."""
        mock_cm = Mock(spec=ContextManager)
        mock_cm.get_context = AsyncMock(return_value={})
        mock_cm.update_context = AsyncMock()
        return mock_cm
    
    @pytest.fixture
    def pool_config(self):
        """Create a test pool configuration."""
        return PoolConfiguration(
            min_agents_per_type={"TestAgent": 1},
            max_agents_per_type={"TestAgent": 3},
            health_check_interval=0.1,  # Fast for testing
            cleanup_interval_minutes=1
        )
    
    @pytest.fixture
    def agent_pool(self, mock_context_manager, pool_config):
        """Create an agent pool for testing."""
        return AgentPool(
            context_manager=mock_context_manager,
            strategy=AgentPoolStrategy.DYNAMIC,
            load_balancing=LoadBalancingAlgorithm.LEAST_LOADED,
            config=pool_config,
            enable_auto_scaling=True,
            enable_health_monitoring=False,  # Disable for most tests
            enable_predictive_scaling=False
        )

    def test_agent_pool_init(self, agent_pool, mock_context_manager, pool_config):
        """Test agent pool initialization."""
        assert agent_pool.context_manager == mock_context_manager
        assert agent_pool.strategy == AgentPoolStrategy.DYNAMIC
        assert agent_pool.load_balancing == LoadBalancingAlgorithm.LEAST_LOADED
        assert agent_pool.config == pool_config
        assert agent_pool.enable_auto_scaling is True
        assert agent_pool.enable_health_monitoring is False
        
        assert agent_pool.agents == {}
        assert len(agent_pool.agent_types) == 0
        assert len(agent_pool.task_queue) == 0
        assert agent_pool.active_tasks == {}
        assert isinstance(agent_pool.statistics, PoolStatistics)

    @pytest.mark.asyncio
    async def test_start_and_stop_pool(self, agent_pool):
        """Test starting and stopping the agent pool."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Start pool
            await agent_pool.start()
            assert agent_pool._running is True
            
            # Stop pool
            await agent_pool.stop()
            assert agent_pool._running is False

    @pytest.mark.asyncio
    async def test_create_agent(self, agent_pool):
        """Test creating an agent."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_agent = MockAgent("TestAgent")
            mock_create_agent.return_value = mock_agent
            
            pooled_agent = await agent_pool._create_agent("TestAgent")
            
            assert pooled_agent is not None
            assert pooled_agent.agent_type == "TestAgent"
            assert pooled_agent.agent == mock_agent
            assert pooled_agent.agent_id in agent_pool.agents
            assert pooled_agent.agent_id in agent_pool.agent_types["TestAgent"]
            assert agent_pool.statistics.total_agents == 1

    @pytest.mark.asyncio
    async def test_create_agent_failure(self, agent_pool):
        """Test handling agent creation failure."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.side_effect = Exception("Creation failed")
            
            pooled_agent = await agent_pool._create_agent("TestAgent")
            
            assert pooled_agent is None
            assert len(agent_pool.agents) == 0

    @pytest.mark.asyncio
    async def test_remove_agent(self, agent_pool):
        """Test removing an agent from the pool."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Create agent
            pooled_agent = await agent_pool._create_agent("TestAgent")
            agent_id = pooled_agent.agent_id
            
            # Remove agent
            await agent_pool._remove_agent(agent_id)
            
            assert agent_id not in agent_pool.agents
            assert agent_id not in agent_pool.agent_types["TestAgent"]
            assert agent_pool.statistics.total_agents == 0

    @pytest.mark.asyncio
    async def test_submit_task(self, agent_pool):
        """Test submitting a task to the pool."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_agent = MockAgent("TestAgent")
            mock_create_agent.return_value = mock_agent
            
            # Create agent first
            await agent_pool._create_agent("TestAgent")
            
            # Submit task
            task_id = await agent_pool.submit_task(
                agent_type="TestAgent",
                command="test_command",
                context={"test": "data"},
                priority=5
            )
            
            assert task_id is not None
            assert task_id in agent_pool.active_tasks
            
            task = agent_pool.active_tasks[task_id]
            assert task.agent_type == "TestAgent"
            assert task.command == "test_command"
            assert task.context["test"] == "data"
            assert task.context["priority"] == 5

    @pytest.mark.asyncio
    async def test_submit_task_no_available_agents(self, agent_pool):
        """Test submitting task when no agents are available."""
        # Submit task without creating agents
        task_id = await agent_pool.submit_task(
            agent_type="TestAgent",
            command="test_command",
            context={}
        )
        
        assert task_id is not None
        assert len(agent_pool.task_queue) == 1  # Task should be queued

    @pytest.mark.asyncio
    async def test_get_task_result_completed(self, agent_pool):
        """Test getting result of a completed task."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_agent = MockAgent("TestAgent")
            mock_create_agent.return_value = mock_agent
            
            await agent_pool._create_agent("TestAgent")
            
            # Submit and wait for task
            task_id = await agent_pool.submit_task(
                agent_type="TestAgent",
                command="test_command",
                context={}
            )
            
            # Wait a bit for task to complete
            await asyncio.sleep(0.1)
            
            result = await agent_pool.get_task_result(task_id, timeout=1.0)
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_task_result_timeout(self, agent_pool):
        """Test getting result with timeout."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_agent = MockAgent("TestAgent")
            mock_agent.delay_seconds = 2  # Make task take longer than timeout
            mock_create_agent.return_value = mock_agent
            
            await agent_pool._create_agent("TestAgent")
            
            task_id = await agent_pool.submit_task(
                agent_type="TestAgent",
                command="slow_command",
                context={}
            )
            
            result = await agent_pool.get_task_result(task_id, timeout=0.1)
            assert result is None  # Should timeout

    @pytest.mark.asyncio
    async def test_cancel_task_pending(self, agent_pool):
        """Test cancelling a pending task."""
        # Submit task without agents to keep it pending
        task_id = await agent_pool.submit_task(
            agent_type="TestAgent",
            command="test_command",
            context={}
        )
        
        # Task should be in queue
        assert len(agent_pool.task_queue) == 1
        
        # Cancel task
        cancelled = await agent_pool.cancel_task(task_id)
        assert cancelled is True
        
        # Task should be removed from queue
        assert len(agent_pool.task_queue) == 0
        
        task = agent_pool.active_tasks[task_id]
        assert task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_task_in_progress(self, agent_pool):
        """Test cancelling a task in progress."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_agent = MockAgent("TestAgent")
            mock_agent.delay_seconds = 1  # Make task run for a bit
            mock_create_agent.return_value = mock_agent
            
            await agent_pool._create_agent("TestAgent")
            
            task_id = await agent_pool.submit_task(
                agent_type="TestAgent",
                command="slow_command",
                context={}
            )
            
            # Wait a bit for task to start
            await asyncio.sleep(0.05)
            
            # Cancel task
            cancelled = await agent_pool.cancel_task(task_id)
            assert cancelled is True

    @pytest.mark.asyncio
    async def test_scale_pool_up(self, agent_pool):
        """Test scaling pool up."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Initial agent count
            initial_count = len(agent_pool.agent_types["TestAgent"])
            
            # Scale up to 2 agents
            result = await agent_pool.scale_pool("TestAgent", target_count=2)
            
            assert result["agent_type"] == "TestAgent"
            assert result["current_count"] == initial_count
            assert result["target_count"] == 2
            assert result["agents_added"] == 2
            assert result["agents_removed"] == 0
            assert len(agent_pool.agent_types["TestAgent"]) == 2

    @pytest.mark.asyncio
    async def test_scale_pool_down(self, agent_pool):
        """Test scaling pool down."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Create 3 agents
            for _ in range(3):
                await agent_pool._create_agent("TestAgent")
            
            # Scale down to 1 agent
            result = await agent_pool.scale_pool("TestAgent", target_count=1)
            
            assert result["target_count"] == 1
            assert result["agents_removed"] == 2
            assert len(agent_pool.agent_types["TestAgent"]) == 1

    @pytest.mark.asyncio
    async def test_get_pool_status(self, agent_pool):
        """Test getting comprehensive pool status."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent, \
             patch('lib.agent_pool.get_available_agents') as mock_get_agents:
            
            mock_create_agent.return_value = MockAgent("TestAgent")
            mock_get_agents.return_value = ["TestAgent"]
            
            # Create some agents
            await agent_pool._create_agent("TestAgent")
            await agent_pool._create_agent("TestAgent")
            
            status = await agent_pool.get_pool_status()
            
            assert "pool_summary" in status
            assert "agent_types" in status
            assert "configuration" in status
            assert "statistics" in status
            
            pool_summary = status["pool_summary"]
            assert pool_summary["total_agents"] == 2
            assert pool_summary["active_agents"] == 2
            assert pool_summary["failed_agents"] == 0
            
            agent_types = status["agent_types"]
            assert "TestAgent" in agent_types
            assert agent_types["TestAgent"]["total"] == 2
            assert agent_types["TestAgent"]["idle"] == 2

    @pytest.mark.asyncio
    async def test_get_utilization(self, agent_pool):
        """Test getting pool utilization."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # No agents
            utilization = await agent_pool.get_utilization()
            assert utilization == 0.0
            
            # Create agent with some load
            pooled_agent = await agent_pool._create_agent("TestAgent")
            pooled_agent.max_concurrent_tasks = 2
            pooled_agent.current_tasks.add("task1")
            
            utilization = await agent_pool.get_utilization()
            assert utilization == 0.5  # 1 task out of 2 capacity

    @pytest.mark.asyncio
    async def test_get_agent_details(self, agent_pool):
        """Test getting detailed agent information."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            pooled_agent = await agent_pool._create_agent("TestAgent")
            agent_id = pooled_agent.agent_id
            
            details = await agent_pool.get_agent_details(agent_id)
            
            assert details is not None
            assert details["agent_id"] == agent_id
            assert details["agent_type"] == "TestAgent"
            assert details["status"] == "idle"
            assert details["current_tasks"] == 0
            assert details["load_factor"] == 0.0
            assert "capabilities" in details
            assert "metrics" in details
            assert "uptime" in details

    @pytest.mark.asyncio
    async def test_get_agent_details_nonexistent(self, agent_pool):
        """Test getting details for nonexistent agent."""
        details = await agent_pool.get_agent_details("nonexistent")
        assert details is None

    @pytest.mark.asyncio
    async def test_load_balancing_round_robin(self, agent_pool):
        """Test round-robin load balancing."""
        agent_pool.load_balancing = LoadBalancingAlgorithm.ROUND_ROBIN
        
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Create multiple agents
            agents = []
            for _ in range(3):
                pooled_agent = await agent_pool._create_agent("TestAgent")
                agents.append(pooled_agent)
            
            # Create mock task
            task = Task(id="test", agent_type="TestAgent", command="test", context={})
            
            # Test round-robin selection
            selected1 = await agent_pool._apply_load_balancing(agents, task)
            selected2 = await agent_pool._apply_load_balancing(agents, task)
            selected3 = await agent_pool._apply_load_balancing(agents, task)
            selected4 = await agent_pool._apply_load_balancing(agents, task)
            
            # Should cycle through agents
            assert selected1 != selected2 != selected3
            assert selected1 == selected4  # Should wrap around

    @pytest.mark.asyncio
    async def test_load_balancing_least_loaded(self, agent_pool):
        """Test least-loaded load balancing."""
        agent_pool.load_balancing = LoadBalancingAlgorithm.LEAST_LOADED
        
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Create agents with different loads
            agent1 = await agent_pool._create_agent("TestAgent")
            agent2 = await agent_pool._create_agent("TestAgent")
            
            # Give agent1 more load
            agent1.current_tasks.add("task1")
            agent1.max_concurrent_tasks = 2
            agent2.max_concurrent_tasks = 2
            
            agents = [agent1, agent2]
            task = Task(id="test", agent_type="TestAgent", command="test", context={})
            
            # Should select less loaded agent (agent2)
            selected = await agent_pool._apply_load_balancing(agents, task)
            assert selected == agent2

    @pytest.mark.asyncio
    async def test_load_balancing_priority_weighted(self, agent_pool):
        """Test priority-weighted load balancing."""
        agent_pool.load_balancing = LoadBalancingAlgorithm.PRIORITY_WEIGHTED
        
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            agents = []
            for _ in range(2):
                pooled_agent = await agent_pool._create_agent("TestAgent")
                agents.append(pooled_agent)
            
            # High priority task should prefer least loaded
            high_priority_task = Task(
                id="high",
                agent_type="TestAgent",
                command="test",
                context={"priority": 1}
            )
            
            selected = await agent_pool._apply_load_balancing(agents, high_priority_task)
            assert selected in agents

    @pytest.mark.asyncio
    async def test_task_execution_success(self, agent_pool):
        """Test successful task execution."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_agent = MockAgent("TestAgent")
            mock_create_agent.return_value = mock_agent
            
            pooled_agent = await agent_pool._create_agent("TestAgent")
            
            # Create and execute task
            task = Task(id="test", agent_type="TestAgent", command="test", context={})
            agent_pool.active_tasks[task.id] = task
            
            await agent_pool._execute_task(pooled_agent, task)
            
            # Check metrics updated
            assert pooled_agent.metrics.total_tasks == 1
            assert pooled_agent.metrics.successful_tasks == 1
            assert pooled_agent.metrics.failed_tasks == 0
            assert task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_task_execution_failure(self, agent_pool):
        """Test failed task execution."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_agent = MockAgent("TestAgent")
            mock_agent.fail_next = True
            mock_create_agent.return_value = mock_agent
            
            pooled_agent = await agent_pool._create_agent("TestAgent")
            
            # Create and execute task
            task = Task(id="test", agent_type="TestAgent", command="test", context={})
            agent_pool.active_tasks[task.id] = task
            
            await agent_pool._execute_task(pooled_agent, task)
            
            # Check metrics updated for failure
            assert pooled_agent.metrics.total_tasks == 1
            assert pooled_agent.metrics.successful_tasks == 0
            assert pooled_agent.metrics.failed_tasks == 1
            assert pooled_agent.failure_count == 1
            assert task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_agent_recovery(self, agent_pool):
        """Test agent recovery after failures."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            pooled_agent = await agent_pool._create_agent("TestAgent")
            pooled_agent.failure_count = agent_pool.config.failure_threshold
            
            # Trigger recovery
            await agent_pool._recover_agent(pooled_agent)
            
            assert pooled_agent.status == AgentStatus.IDLE
            assert pooled_agent.failure_count == 0
            assert pooled_agent.recovery_attempts == 1
            assert agent_pool.statistics.recovery_events == 1

    @pytest.mark.asyncio
    async def test_auto_scaling_trigger(self, agent_pool):
        """Test auto-scaling trigger."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Enable auto-scaling
            agent_pool.enable_auto_scaling = True
            
            # Try to scale when no agents available
            await agent_pool._attempt_auto_scale("TestAgent")
            
            # Should create one agent
            assert len(agent_pool.agent_types["TestAgent"]) == 1

    @pytest.mark.asyncio
    async def test_health_monitoring_stuck_agent(self, agent_pool):
        """Test health monitoring detects stuck agents."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            pooled_agent = await agent_pool._create_agent("TestAgent")
            
            # Make agent appear stuck
            pooled_agent.status = AgentStatus.BUSY
            pooled_agent.last_activity = datetime.utcnow() - timedelta(hours=2)
            
            await agent_pool._perform_health_checks()
            
            # Agent should be recovered
            assert pooled_agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, agent_pool):
        """Test cleanup of old performance data."""
        # Add old entries
        old_time = (datetime.utcnow() - timedelta(days=2)).isoformat()
        agent_pool._performance_history.append({"timestamp": old_time, "data": "old"})
        agent_pool._scaling_history.append({"timestamp": old_time, "data": "old"})
        
        # Add recent entries
        recent_time = datetime.utcnow().isoformat()
        agent_pool._performance_history.append({"timestamp": recent_time, "data": "recent"})
        agent_pool._scaling_history.append({"timestamp": recent_time, "data": "recent"})
        
        await agent_pool._perform_cleanup()
        
        # Old entries should be removed
        assert len(agent_pool._performance_history) == 1
        assert len(agent_pool._scaling_history) == 1
        assert agent_pool._performance_history[0]["data"] == "recent"

    @pytest.mark.asyncio
    async def test_shutdown_all_agents(self, agent_pool):
        """Test graceful shutdown of all agents."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Create some agents
            await agent_pool._create_agent("TestAgent")
            await agent_pool._create_agent("TestAgent")
            
            assert len(agent_pool.agents) == 2
            
            await agent_pool._shutdown_all_agents()
            
            # All agents should be removed
            assert len(agent_pool.agents) == 0
            assert len(agent_pool.agent_types["TestAgent"]) == 0

    def test_get_max_concurrent_tasks(self, agent_pool):
        """Test getting max concurrent tasks for agent types."""
        assert agent_pool._get_max_concurrent_tasks("DesignAgent") == 1
        assert agent_pool._get_max_concurrent_tasks("CodeAgent") == 2
        assert agent_pool._get_max_concurrent_tasks("QAAgent") == 3
        assert agent_pool._get_max_concurrent_tasks("DataAgent") == 2
        assert agent_pool._get_max_concurrent_tasks("UnknownAgent") == 1

    @pytest.mark.asyncio
    async def test_calculate_optimal_agent_count(self, agent_pool):
        """Test calculating optimal agent count."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Create one agent
            pooled_agent = await agent_pool._create_agent("TestAgent")
            
            # Test high utilization scenario
            pooled_agent.current_tasks.add("task1")
            pooled_agent.max_concurrent_tasks = 1  # 100% utilization
            
            optimal_count = await agent_pool._calculate_optimal_agent_count("TestAgent")
            assert optimal_count >= 1  # Should suggest scaling up or maintaining

    @pytest.mark.asyncio
    async def test_calculate_type_utilization(self, agent_pool):
        """Test calculating utilization for specific agent type."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # No agents
            utilization = await agent_pool._calculate_type_utilization("TestAgent")
            assert utilization == 0.0
            
            # Create agent with load
            pooled_agent = await agent_pool._create_agent("TestAgent")
            pooled_agent.max_concurrent_tasks = 2
            pooled_agent.current_tasks.add("task1")
            
            utilization = await agent_pool._calculate_type_utilization("TestAgent")
            assert utilization == 0.5

    @pytest.mark.asyncio
    async def test_process_task_queue(self, agent_pool):
        """Test processing queued tasks."""
        with patch('lib.agent_pool.create_agent') as mock_create_agent:
            mock_create_agent.return_value = MockAgent("TestAgent")
            
            # Add task to queue
            task = Task(id="queued", agent_type="TestAgent", command="test", context={})
            agent_pool.task_queue.append(task)
            agent_pool.active_tasks[task.id] = task
            
            # Create agent
            await agent_pool._create_agent("TestAgent")
            
            # Process queue
            await agent_pool._process_task_queue()
            
            # Queue should be empty
            assert len(agent_pool.task_queue) == 0

    @pytest.mark.asyncio
    async def test_enums_and_constants(self):
        """Test enum values and constants."""
        # Test AgentPoolStrategy enum
        assert AgentPoolStrategy.STATIC.value == "static"
        assert AgentPoolStrategy.DYNAMIC.value == "dynamic"
        assert AgentPoolStrategy.BURST.value == "burst"
        assert AgentPoolStrategy.BALANCED.value == "balanced"
        
        # Test AgentStatus enum
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.STARTING.value == "starting"
        assert AgentStatus.STOPPING.value == "stopping"
        assert AgentStatus.RETIRED.value == "retired"
        
        # Test LoadBalancingAlgorithm enum
        assert LoadBalancingAlgorithm.ROUND_ROBIN.value == "round_robin"
        assert LoadBalancingAlgorithm.LEAST_LOADED.value == "least_loaded"
        assert LoadBalancingAlgorithm.CAPABILITY_BASED.value == "capability_based"
        assert LoadBalancingAlgorithm.PRIORITY_WEIGHTED.value == "priority_weighted"