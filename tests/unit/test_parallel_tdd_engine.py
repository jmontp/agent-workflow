"""
Unit tests for Parallel TDD Engine.

Tests the unified integration layer that coordinates all parallel TDD components
including context-aware execution, conflict resolution, and performance optimization.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.parallel_tdd_engine import (
    ParallelTDDEngine, ParallelTDDConfiguration, ParallelExecutionMetrics,
    ParallelExecutionStatus
)
from lib.tdd_models import TDDState, TDDCycle, TDDTask


class TestParallelTDDConfiguration:
    """Test the ParallelTDDConfiguration dataclass."""
    
    def test_configuration_creation(self):
        """Test creating a ParallelTDDConfiguration instance."""
        from lib.parallel_tdd_coordinator import ParallelExecutionMode
        from lib.agent_pool import AgentPoolStrategy, LoadBalancingAlgorithm
        
        config = ParallelTDDConfiguration(
            max_parallel_cycles=8,
            execution_mode=ParallelExecutionMode.AGGRESSIVE,
            enable_predictive_scheduling=False,
            enable_conflict_prevention=False,
            enable_auto_resolution=False,
            enable_resource_locking=False,
            enable_coordination_events=False,
            agent_pool_strategy=AgentPoolStrategy.STATIC,
            load_balancing=LoadBalancingAlgorithm.ROUND_ROBIN,
            enable_auto_scaling=False,
            resource_timeout_minutes=60,
            coordination_check_interval=10.0,
            health_check_interval=60.0,
            enable_performance_monitoring=False,
            enable_context_isolation=False,
            enable_shared_context_optimization=False
        )
        
        assert config.max_parallel_cycles == 8
        assert config.execution_mode == ParallelExecutionMode.AGGRESSIVE
        assert config.enable_predictive_scheduling is False
        assert config.enable_conflict_prevention is False
        assert config.enable_auto_resolution is False
        assert config.enable_resource_locking is False
        assert config.enable_coordination_events is False
        assert config.agent_pool_strategy == AgentPoolStrategy.STATIC
        assert config.load_balancing == LoadBalancingAlgorithm.ROUND_ROBIN
        assert config.enable_auto_scaling is False
        assert config.resource_timeout_minutes == 60
        assert config.coordination_check_interval == 10.0
        assert config.health_check_interval == 60.0
        assert config.enable_performance_monitoring is False
        assert config.enable_context_isolation is False
        assert config.enable_shared_context_optimization is False

    def test_configuration_defaults(self):
        """Test ParallelTDDConfiguration with default values."""
        from lib.parallel_tdd_coordinator import ParallelExecutionMode
        from lib.agent_pool import AgentPoolStrategy, LoadBalancingAlgorithm
        
        config = ParallelTDDConfiguration()
        
        assert config.max_parallel_cycles == 4
        assert config.execution_mode == ParallelExecutionMode.BALANCED
        assert config.enable_predictive_scheduling is True
        assert config.enable_conflict_prevention is True
        assert config.enable_auto_resolution is True
        assert config.enable_resource_locking is True
        assert config.enable_coordination_events is True
        assert config.agent_pool_strategy == AgentPoolStrategy.DYNAMIC
        assert config.load_balancing == LoadBalancingAlgorithm.CAPABILITY_BASED
        assert config.enable_auto_scaling is True
        assert config.resource_timeout_minutes == 30
        assert config.coordination_check_interval == 5.0
        assert config.health_check_interval == 30.0
        assert config.enable_performance_monitoring is True
        assert config.enable_context_isolation is True
        assert config.enable_shared_context_optimization is True


class TestParallelExecutionMetrics:
    """Test the ParallelExecutionMetrics dataclass."""
    
    def test_metrics_creation(self):
        """Test creating a ParallelExecutionMetrics instance."""
        metrics = ParallelExecutionMetrics(
            engine_uptime=3600.0,
            total_cycles_executed=50,
            parallel_cycles_executed=30,
            average_cycle_time=120.5,
            throughput_cycles_per_hour=25.0,
            conflicts_detected=5,
            conflicts_resolved=4,
            auto_resolutions=3,
            human_escalations=1,
            coordination_events=15,
            peak_parallel_cycles=6,
            average_resource_utilization=75.5,
            resource_conflicts=2,
            context_preparation_time=5.2,
            context_cache_hit_rate=85.0,
            cross_story_insights=8,
            test_preservation_rate=98.5,
            parallel_quality_score=92.0
        )
        
        assert metrics.engine_uptime == 3600.0
        assert metrics.total_cycles_executed == 50
        assert metrics.parallel_cycles_executed == 30
        assert metrics.average_cycle_time == 120.5
        assert metrics.throughput_cycles_per_hour == 25.0
        assert metrics.conflicts_detected == 5
        assert metrics.conflicts_resolved == 4
        assert metrics.auto_resolutions == 3
        assert metrics.human_escalations == 1
        assert metrics.coordination_events == 15
        assert metrics.peak_parallel_cycles == 6
        assert metrics.average_resource_utilization == 75.5
        assert metrics.resource_conflicts == 2
        assert metrics.context_preparation_time == 5.2
        assert metrics.context_cache_hit_rate == 85.0
        assert metrics.cross_story_insights == 8
        assert metrics.test_preservation_rate == 98.5
        assert metrics.parallel_quality_score == 92.0

    def test_metrics_defaults(self):
        """Test ParallelExecutionMetrics with default values."""
        metrics = ParallelExecutionMetrics()
        
        assert metrics.engine_uptime == 0.0
        assert metrics.total_cycles_executed == 0
        assert metrics.parallel_cycles_executed == 0
        assert metrics.average_cycle_time == 0.0
        assert metrics.throughput_cycles_per_hour == 0.0
        assert metrics.conflicts_detected == 0
        assert metrics.conflicts_resolved == 0
        assert metrics.auto_resolutions == 0
        assert metrics.human_escalations == 0
        assert metrics.coordination_events == 0
        assert metrics.peak_parallel_cycles == 0
        assert metrics.average_resource_utilization == 0.0
        assert metrics.resource_conflicts == 0
        assert metrics.context_preparation_time == 0.0
        assert metrics.context_cache_hit_rate == 0.0
        assert metrics.cross_story_insights == 0
        assert metrics.test_preservation_rate == 100.0
        assert metrics.parallel_quality_score == 0.0


@pytest.fixture
def mock_context_manager():
    """Create a mock context manager."""
    manager = Mock()
    manager.prepare_context = AsyncMock(return_value={"context": "data", "preparation_time": 1.0, "cache_hit": True})
    return manager


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_coordinator():
    """Create a mock parallel TDD coordinator."""
    coordinator = Mock()
    coordinator.start = AsyncMock()
    coordinator.stop = AsyncMock()
    coordinator.submit_cycle = AsyncMock(return_value="cycle-1")
    coordinator.get_cycle_status = AsyncMock(return_value={
        "status": "completed",
        "execution_time": 120.0,
        "metrics": {}
    })
    coordinator.get_parallel_status = AsyncMock(return_value={
        "cycle_summary": {"active_cycles": 2, "blocked_cycles": 0},
        "performance_stats": {"conflicts_detected": 1}
    })
    coordinator.optimize_scheduling = AsyncMock(return_value="optimization_result")
    coordinator._paused = False
    return coordinator


@pytest.fixture
def mock_agent_pool():
    """Create a mock agent pool."""
    pool = Mock()
    pool.start = AsyncMock()
    pool.stop = AsyncMock()
    pool.get_pool_status = AsyncMock(return_value={
        "agent_types": {
            "code_agent": {"average_load": 0.6},
            "design_agent": {"average_load": 0.9}
        },
        "pool_summary": {"failed_agents": 1}
    })
    pool.scale_pool = AsyncMock(return_value="scaling_result")
    return pool


@pytest.fixture
def mock_conflict_resolver():
    """Create a mock conflict resolver."""
    resolver = Mock()
    resolver.start = AsyncMock()
    resolver.stop = AsyncMock()
    resolver.register_file_modification = AsyncMock()
    resolver.get_resolution_statistics = AsyncMock(return_value={
        "resolved_conflicts": 5,
        "auto_resolved": 4,
        "escalated": 1
    })
    return resolver


@pytest.fixture
def mock_state_machine():
    """Create a mock TDD state machine."""
    machine = Mock()
    machine.register_parallel_cycle = Mock()
    machine.add_cycle_dependency = Mock()
    machine.cleanup_expired_resources = Mock(return_value=3)
    machine.get_parallel_status = Mock(return_value={"parallel_cycles": 2})
    return machine


@pytest_asyncio.fixture
async def parallel_engine(mock_context_manager, temp_project_dir):
    """Create a ParallelTDDEngine instance for testing."""
    config = ParallelTDDConfiguration(
        enable_performance_monitoring=False  # Disable for simpler testing
    )
    
    with patch('lib.parallel_tdd_engine.ParallelTDDCoordinator') as mock_coord_class, \
         patch('lib.parallel_tdd_engine.AgentPool') as mock_pool_class, \
         patch('lib.parallel_tdd_engine.ConflictResolver') as mock_resolver_class, \
         patch('lib.parallel_tdd_engine.TDDStateMachine') as mock_machine_class:
        
        # Configure mocks
        mock_coord_class.return_value = Mock()
        mock_pool_class.return_value = Mock()
        mock_resolver_class.return_value = Mock()
        mock_machine_class.return_value = Mock()
        
        # Add async methods
        for mock_obj in [mock_coord_class.return_value, mock_pool_class.return_value, mock_resolver_class.return_value]:
            mock_obj.start = AsyncMock()
            mock_obj.stop = AsyncMock()
        
        # Add coordinator-specific async methods
        mock_coord_class.return_value.submit_cycle = AsyncMock(return_value="cycle-1")
        mock_coord_class.return_value.get_cycle_status = AsyncMock(return_value={
            "status": "completed",
            "execution_time": 120.0,
            "metrics": {}
        })
        mock_coord_class.return_value.get_parallel_status = AsyncMock(return_value={
            "cycle_summary": {"active_cycles": 2, "blocked_cycles": 0},
            "performance_stats": {"conflicts_detected": 1}
        })
        mock_coord_class.return_value.optimize_scheduling = AsyncMock(return_value="optimization_result")
        mock_coord_class.return_value._paused = False
        
        # Add agent pool-specific async methods
        mock_pool_class.return_value.get_pool_status = AsyncMock(return_value={
            "agent_types": {
                "code_agent": {"average_load": 0.6},
                "design_agent": {"average_load": 0.9}
            },
            "pool_summary": {"failed_agents": 1}
        })
        mock_pool_class.return_value.scale_pool = AsyncMock(return_value="scaling_result")
        
        # Add conflict resolver-specific async methods
        mock_resolver_class.return_value.register_file_modification = AsyncMock()
        mock_resolver_class.return_value.get_resolution_statistics = AsyncMock(return_value={
            "resolved_conflicts": 5,
            "auto_resolved": 4,
            "escalated": 1
        })
        
        engine = ParallelTDDEngine(
            context_manager=mock_context_manager,
            project_path=temp_project_dir,
            config=config
        )
        
        yield engine


class TestParallelTDDEngine:
    """Test the ParallelTDDEngine class."""
    
    def test_engine_initialization(self, mock_context_manager, temp_project_dir):
        """Test ParallelTDDEngine initialization."""
        config = ParallelTDDConfiguration(max_parallel_cycles=8)
        
        with patch('lib.parallel_tdd_engine.ParallelTDDCoordinator') as mock_coord, \
             patch('lib.parallel_tdd_engine.AgentPool') as mock_pool, \
             patch('lib.parallel_tdd_engine.ConflictResolver') as mock_resolver, \
             patch('lib.parallel_tdd_engine.TDDStateMachine') as mock_machine:
            
            engine = ParallelTDDEngine(
                context_manager=mock_context_manager,
                project_path=temp_project_dir,
                config=config
            )
            
            assert engine.context_manager == mock_context_manager
            assert engine.project_path == temp_project_dir
            assert engine.config == config
            assert engine.status == ParallelExecutionStatus.STOPPED
            assert engine.start_time is None
            assert isinstance(engine.metrics, ParallelExecutionMetrics)
            assert engine.active_executions == {}
            assert engine.execution_history == []
            
            # Check that components were initialized
            mock_coord.assert_called_once()
            mock_pool.assert_called_once()
            mock_resolver.assert_called_once()
            mock_machine.assert_called_once()

    def test_engine_initialization_default_config(self, mock_context_manager, temp_project_dir):
        """Test ParallelTDDEngine initialization with default config."""
        with patch('lib.parallel_tdd_engine.ParallelTDDCoordinator') as mock_coord, \
             patch('lib.parallel_tdd_engine.AgentPool') as mock_pool, \
             patch('lib.parallel_tdd_engine.ConflictResolver') as mock_resolver, \
             patch('lib.parallel_tdd_engine.TDDStateMachine') as mock_machine:
            
            engine = ParallelTDDEngine(
                context_manager=mock_context_manager,
                project_path=temp_project_dir
            )
            
            assert isinstance(engine.config, ParallelTDDConfiguration)
            assert engine.config.max_parallel_cycles == 4  # Default value

    @pytest.mark.asyncio
    async def test_start_engine(self, parallel_engine):
        """Test starting the parallel TDD engine."""
        assert parallel_engine.status == ParallelExecutionStatus.STOPPED
        
        await parallel_engine.start()
        
        assert parallel_engine.status == ParallelExecutionStatus.RUNNING
        assert parallel_engine.start_time is not None
        
        # Components should be started
        parallel_engine.coordinator.start.assert_called_once()
        parallel_engine.agent_pool.start.assert_called_once()
        parallel_engine.conflict_resolver.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_engine_with_monitoring(self, mock_context_manager, temp_project_dir):
        """Test starting engine with performance monitoring enabled."""
        config = ParallelTDDConfiguration(enable_performance_monitoring=True)
        
        with patch('lib.parallel_tdd_engine.ParallelTDDCoordinator') as mock_coord, \
             patch('lib.parallel_tdd_engine.AgentPool') as mock_pool, \
             patch('lib.parallel_tdd_engine.ConflictResolver') as mock_resolver, \
             patch('lib.parallel_tdd_engine.TDDStateMachine') as mock_machine:
            
            # Configure mocks
            for mock_obj in [mock_coord.return_value, mock_pool.return_value, mock_resolver.return_value]:
                mock_obj.start = AsyncMock()
                mock_obj.stop = AsyncMock()
            
            engine = ParallelTDDEngine(
                context_manager=mock_context_manager,
                project_path=temp_project_dir,
                config=config
            )
            
            await engine.start()
            
            assert engine.status == ParallelExecutionStatus.RUNNING
            assert engine._monitoring_task is not None
            assert engine._optimization_task is not None
            
            await engine.stop()

    @pytest.mark.asyncio
    async def test_start_engine_already_running(self, parallel_engine):
        """Test starting engine when already running."""
        await parallel_engine.start()
        assert parallel_engine.status == ParallelExecutionStatus.RUNNING
        
        # Starting again should not change status
        await parallel_engine.start()
        assert parallel_engine.status == ParallelExecutionStatus.RUNNING

    @pytest.mark.asyncio
    async def test_start_engine_exception(self, parallel_engine):
        """Test handling exceptions during engine start."""
        parallel_engine.coordinator.start.side_effect = Exception("Start failed")
        
        with pytest.raises(Exception, match="Start failed"):
            await parallel_engine.start()
        
        assert parallel_engine.status == ParallelExecutionStatus.ERROR

    @pytest.mark.asyncio
    async def test_stop_engine(self, parallel_engine):
        """Test stopping the parallel TDD engine."""
        await parallel_engine.start()
        assert parallel_engine.status == ParallelExecutionStatus.RUNNING
        
        await parallel_engine.stop()
        
        assert parallel_engine.status == ParallelExecutionStatus.STOPPED
        
        # Components should be stopped
        parallel_engine.coordinator.stop.assert_called_once()
        parallel_engine.agent_pool.stop.assert_called_once()
        parallel_engine.conflict_resolver.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_engine_not_running(self, parallel_engine):
        """Test stopping engine when not running."""
        assert parallel_engine.status == ParallelExecutionStatus.STOPPED
        
        # Should not raise exception
        await parallel_engine.stop()
        assert parallel_engine.status == ParallelExecutionStatus.STOPPED

    @pytest.mark.asyncio
    async def test_stop_engine_exception(self, parallel_engine):
        """Test handling exceptions during engine stop."""
        await parallel_engine.start()
        
        parallel_engine.coordinator.stop.side_effect = Exception("Stop failed")
        
        await parallel_engine.stop()
        
        # Should still set status to ERROR even with exception
        assert parallel_engine.status == ParallelExecutionStatus.ERROR

    @pytest.mark.asyncio
    async def test_pause_and_resume_engine(self, parallel_engine):
        """Test pausing and resuming the engine."""
        await parallel_engine.start()
        assert parallel_engine.status == ParallelExecutionStatus.RUNNING
        
        await parallel_engine.pause()
        assert parallel_engine.status == ParallelExecutionStatus.PAUSED
        assert parallel_engine.coordinator._paused is True
        
        await parallel_engine.resume()
        assert parallel_engine.status == ParallelExecutionStatus.RUNNING
        assert parallel_engine.coordinator._paused is False

    @pytest.mark.asyncio
    async def test_pause_engine_not_running(self, parallel_engine):
        """Test pausing engine when not running."""
        assert parallel_engine.status == ParallelExecutionStatus.STOPPED
        
        await parallel_engine.pause()
        # Status should not change
        assert parallel_engine.status == ParallelExecutionStatus.STOPPED

    @pytest.mark.asyncio
    async def test_resume_engine_not_paused(self, parallel_engine):
        """Test resuming engine when not paused."""
        await parallel_engine.start()
        assert parallel_engine.status == ParallelExecutionStatus.RUNNING
        
        await parallel_engine.resume()
        # Status should remain running
        assert parallel_engine.status == ParallelExecutionStatus.RUNNING

    @pytest.mark.asyncio
    async def test_execute_parallel_cycles(self, parallel_engine):
        """Test executing parallel TDD cycles."""
        await parallel_engine.start()
        
        # Create test cycles
        cycle1 = TDDCycle(id="cycle-1", story_id="STORY-1", current_state=TDDState.DESIGN)
        cycle2 = TDDCycle(id="cycle-2", story_id="STORY-2", current_state=TDDState.DESIGN)
        cycles = [cycle1, cycle2]
        
        # Mock cycle completion
        parallel_engine.coordinator.get_cycle_status.side_effect = [
            {"status": "completed", "execution_time": 120.0, "metrics": {}},
            {"status": "completed", "execution_time": 100.0, "metrics": {}}
        ]
        
        result = await parallel_engine.execute_parallel_cycles(cycles)
        
        assert result["success"] is True
        assert result["cycles_completed"] == 2
        assert result["cycles_failed"] == 0
        assert "execution_time" in result
        assert "results" in result
        assert "performance_metrics" in result
        
        # Check that cycles were submitted
        assert parallel_engine.coordinator.submit_cycle.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_parallel_cycles_with_dependencies(self, parallel_engine):
        """Test executing cycles with dependencies."""
        await parallel_engine.start()
        
        cycle1 = TDDCycle(id="cycle-1", story_id="STORY-1", current_state=TDDState.DESIGN)
        cycle2 = TDDCycle(id="cycle-2", story_id="STORY-2", current_state=TDDState.DESIGN)
        cycles = [cycle1, cycle2]
        
        dependencies = {"cycle-2": ["cycle-1"]}
        priorities = {"cycle-1": 10, "cycle-2": 5}
        estimated_durations = {
            "cycle-1": timedelta(minutes=30),
            "cycle-2": timedelta(minutes=45)
        }
        
        # Mock cycle completion
        parallel_engine.coordinator.get_cycle_status.side_effect = [
            {"status": "completed", "execution_time": 30.0, "metrics": {}},
            {"status": "completed", "execution_time": 45.0, "metrics": {}}
        ]
        
        result = await parallel_engine.execute_parallel_cycles(
            cycles,
            dependencies=dependencies,
            priorities=priorities,
            estimated_durations=estimated_durations
        )
        
        assert result["success"] is True
        
        # Check that state machine dependencies were set
        parallel_engine.state_machine.add_cycle_dependency.assert_called_once_with("cycle-2", "cycle-1")

    @pytest.mark.asyncio
    async def test_execute_parallel_cycles_engine_not_running(self, parallel_engine):
        """Test executing cycles when engine is not running."""
        cycle = TDDCycle(id="cycle-1", story_id="STORY-1", current_state=TDDState.DESIGN)
        
        with pytest.raises(RuntimeError, match="Engine not running"):
            await parallel_engine.execute_parallel_cycles([cycle])

    @pytest.mark.asyncio
    async def test_execute_parallel_cycles_exception(self, parallel_engine):
        """Test handling exceptions during cycle execution."""
        await parallel_engine.start()
        
        cycle = TDDCycle(id="cycle-1", story_id="STORY-1", current_state=TDDState.DESIGN)
        parallel_engine.coordinator.submit_cycle.side_effect = Exception("Submit failed")
        
        result = await parallel_engine.execute_parallel_cycles([cycle])
        
        assert result["success"] is False
        assert "Submit failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_engine_status(self, parallel_engine):
        """Test getting comprehensive engine status."""
        await parallel_engine.start()
        
        # Set up mock responses
        parallel_engine.coordinator.get_parallel_status.return_value = {"coord": "status"}
        parallel_engine.agent_pool.get_pool_status.return_value = {"pool": "status"}
        parallel_engine.conflict_resolver.get_resolution_statistics.return_value = {"conflict": "stats"}
        parallel_engine.state_machine.get_parallel_status.return_value = {"state": "status"}
        
        status = await parallel_engine.get_engine_status()
        
        assert "engine_status" in status
        assert "active_executions" in status
        assert "total_executions" in status
        assert "performance_metrics" in status
        assert "components" in status
        
        engine_status = status["engine_status"]
        assert engine_status["status"] == "running"
        assert "uptime_seconds" in engine_status
        assert "configuration" in engine_status
        
        components = status["components"]
        assert "coordinator" in components
        assert "agent_pool" in components
        assert "conflict_resolver" in components
        assert "state_machine" in components

    @pytest.mark.asyncio
    async def test_optimize_performance(self, parallel_engine):
        """Test performance optimization."""
        await parallel_engine.start()
        
        # Mock optimization results
        parallel_engine.coordinator.optimize_scheduling.return_value = "coordinator_optimization"
        parallel_engine.agent_pool.get_pool_status.return_value = {
            "agent_types": {
                "design_agent": {"average_load": 0.9},  # High load
                "code_agent": {"average_load": 0.5}     # Normal load
            }
        }
        parallel_engine.agent_pool.scale_pool.return_value = "scaling_result"
        parallel_engine.state_machine.cleanup_expired_resources.return_value = 5
        
        result = await parallel_engine.optimize_performance()
        
        assert "optimization_time" in result
        assert "optimizations_applied" in result
        assert "performance_improvement" in result
        
        optimizations = result["optimizations_applied"]
        assert len(optimizations) >= 2  # At least coordinator and state machine optimizations
        
        # Check that high-load agent was scaled
        parallel_engine.agent_pool.scale_pool.assert_called_once_with("design_agent")

    @pytest.mark.asyncio
    async def test_handle_context_request_with_isolation(self, parallel_engine):
        """Test handling context request with isolation enabled."""
        context = await parallel_engine.handle_context_request(
            agent_type="code_agent",
            story_id="STORY-1",
            task={"task": "data"},
            max_tokens=1000,
            isolation_mode=True
        )
        
        assert context is not None
        
        # Should have called prepare_context with parallel_isolation=True
        parallel_engine.context_manager.prepare_context.assert_called_once()
        call_kwargs = parallel_engine.context_manager.prepare_context.call_args[1]
        assert call_kwargs.get("parallel_isolation") is True
        assert call_kwargs.get("story_id") == "STORY-1"

    @pytest.mark.asyncio
    async def test_handle_context_request_without_isolation(self, parallel_engine):
        """Test handling context request without isolation."""
        parallel_engine.config.enable_context_isolation = False
        
        context = await parallel_engine.handle_context_request(
            agent_type="design_agent",
            story_id="STORY-2",
            task={"task": "data"},
            isolation_mode=False
        )
        
        assert context is not None
        
        # Should have called prepare_context without parallel_isolation
        call_kwargs = parallel_engine.context_manager.prepare_context.call_args[1]
        assert "parallel_isolation" not in call_kwargs or call_kwargs.get("parallel_isolation") is not True

    @pytest.mark.asyncio
    async def test_handle_context_request_updates_metrics(self, parallel_engine):
        """Test that context requests update performance metrics."""
        initial_cache_hit_rate = parallel_engine.metrics.context_cache_hit_rate
        
        await parallel_engine.handle_context_request(
            agent_type="qa_agent",
            story_id="STORY-3",
            task={"task": "data"}
        )
        
        # Metrics should be updated
        assert parallel_engine.metrics.context_preparation_time > 0
        # Cache hit rate should be updated (mock returns cache_hit=True)
        assert parallel_engine.metrics.context_cache_hit_rate > initial_cache_hit_rate

    @pytest.mark.asyncio
    async def test_monitor_execution(self, parallel_engine):
        """Test monitoring execution until completion."""
        cycle_ids = ["cycle-1", "cycle-2"]
        
        # Mock cycle status progression
        status_responses = [
            # First call - cycle-1 running, cycle-2 not started
            {"status": "running", "execution_time": None, "metrics": {}},
            None,  # cycle-2 not found yet
            # Second call - both running
            {"status": "running", "execution_time": None, "metrics": {}},
            {"status": "running", "execution_time": None, "metrics": {}},
            # Third call - cycle-1 completed, cycle-2 still running
            {"status": "completed", "execution_time": 120.0, "metrics": {}},
            {"status": "running", "execution_time": None, "metrics": {}},
            # Fourth call - both completed
            {"status": "completed", "execution_time": 120.0, "metrics": {}},
            {"status": "completed", "execution_time": 100.0, "metrics": {}}
        ]
        
        parallel_engine.coordinator.get_cycle_status.side_effect = status_responses
        
        results = await parallel_engine._monitor_execution("exec-1", cycle_ids)
        
        assert len(results) == 2
        assert results["cycle-1"]["success"] is True
        assert results["cycle-1"]["execution_time"] == 120.0
        assert results["cycle-2"]["success"] is True
        assert results["cycle-2"]["execution_time"] == 100.0

    @pytest.mark.asyncio
    async def test_monitor_execution_with_failures(self, parallel_engine):
        """Test monitoring execution with cycle failures."""
        cycle_ids = ["cycle-1", "cycle-2"]
        
        # Mock one successful, one failed
        status_responses = [
            {"status": "completed", "execution_time": 120.0, "metrics": {}},
            {"status": "failed", "execution_time": 50.0, "metrics": {}}
        ]
        
        parallel_engine.coordinator.get_cycle_status.side_effect = status_responses
        
        results = await parallel_engine._monitor_execution("exec-1", cycle_ids)
        
        assert len(results) == 2
        assert results["cycle-1"]["success"] is True
        assert results["cycle-2"]["success"] is False

    @pytest.mark.asyncio
    async def test_collect_performance_metrics(self, parallel_engine):
        """Test collecting performance metrics from components."""
        await parallel_engine.start()
        
        # Mock component responses
        parallel_engine.coordinator.get_parallel_status.return_value = {
            "performance_stats": {"conflicts_detected": 3},
            "cycle_summary": {"active_cycles": 2}
        }
        parallel_engine.conflict_resolver.get_resolution_statistics.return_value = {
            "resolved_conflicts": 5,
            "auto_resolved": 4,
            "escalated": 1
        }
        
        await parallel_engine._collect_performance_metrics()
        
        # Metrics should be updated
        assert parallel_engine.metrics.engine_uptime > 0
        assert parallel_engine.metrics.conflicts_detected == 3
        assert parallel_engine.metrics.conflicts_resolved == 5
        assert parallel_engine.metrics.auto_resolutions == 4
        assert parallel_engine.metrics.human_escalations == 1
        assert parallel_engine.metrics.peak_parallel_cycles == 2

    @pytest.mark.asyncio
    async def test_check_engine_health(self, parallel_engine):
        """Test checking overall engine health."""
        # Mock unhealthy conditions
        parallel_engine.coordinator.get_parallel_status.return_value = {
            "cycle_summary": {"blocked_cycles": 5}  # High number of blocked cycles
        }
        parallel_engine.agent_pool.get_pool_status.return_value = {
            "pool_summary": {"failed_agents": 3}  # Multiple agent failures
        }
        
        # Should not raise exception, just log warnings
        await parallel_engine._check_engine_health()

    def test_update_throughput_metrics(self, parallel_engine):
        """Test updating throughput metrics."""
        # Update with execution data
        parallel_engine._update_throughput_metrics(cycles_completed=10, execution_time=3600.0)  # 1 hour
        
        assert parallel_engine.metrics.throughput_cycles_per_hour == 10.0
        assert parallel_engine.metrics.average_cycle_time == 360.0  # 3600/10
        
        # Update again with new data (should use weighted average)
        parallel_engine._update_throughput_metrics(cycles_completed=5, execution_time=1800.0)  # 30 minutes
        
        # Should use weighted average
        expected_throughput = 10.0 * 0.9 + 10.0 * 0.1  # 10 cycles/hour
        expected_cycle_time = 360.0 * 0.9 + 360.0 * 0.1  # 360 seconds
        
        assert abs(parallel_engine.metrics.throughput_cycles_per_hour - expected_throughput) < 0.1
        assert abs(parallel_engine.metrics.average_cycle_time - expected_cycle_time) < 0.1

    def test_update_throughput_metrics_zero_time(self, parallel_engine):
        """Test updating throughput metrics with zero execution time."""
        parallel_engine._update_throughput_metrics(cycles_completed=5, execution_time=0.0)
        
        # Should not cause division by zero
        assert parallel_engine.metrics.throughput_cycles_per_hour == 0.0

    def test_update_throughput_metrics_zero_cycles(self, parallel_engine):
        """Test updating throughput metrics with zero cycles."""
        parallel_engine._update_throughput_metrics(cycles_completed=0, execution_time=3600.0)
        
        # Average cycle time should be 0
        assert parallel_engine.metrics.average_cycle_time == 0.0

    @pytest.mark.asyncio
    async def test_get_execution_metrics(self, parallel_engine):
        """Test getting metrics for specific execution."""
        execution_id = "exec-123"
        execution_info = {
            "execution_time": 120.0,
            "total_cycles": 5
        }
        parallel_engine.active_executions[execution_id] = execution_info
        
        # Mock component responses
        parallel_engine.coordinator.get_parallel_status.return_value = {"coord": "metrics"}
        parallel_engine.agent_pool.get_pool_status.return_value = {"pool": "metrics"}
        parallel_engine.conflict_resolver.get_resolution_statistics.return_value = {"conflict": "metrics"}
        
        metrics = await parallel_engine._get_execution_metrics(execution_id)
        
        assert metrics["execution_time"] == 120.0
        assert metrics["total_cycles"] == 5
        assert "coordinator_metrics" in metrics
        assert "agent_pool_metrics" in metrics
        assert "conflict_metrics" in metrics

    @pytest.mark.asyncio
    async def test_get_execution_metrics_not_found(self, parallel_engine):
        """Test getting metrics for non-existent execution."""
        metrics = await parallel_engine._get_execution_metrics("nonexistent")
        assert metrics == {}

    @pytest.mark.asyncio
    async def test_estimate_performance_improvement(self, parallel_engine):
        """Test estimating performance improvement."""
        improvement = await parallel_engine._estimate_performance_improvement()
        
        assert "throughput_improvement" in improvement
        assert "conflict_reduction" in improvement
        assert "resource_efficiency" in improvement
        
        # Should return reasonable estimates
        assert 0.0 <= improvement["throughput_improvement"] <= 100.0
        assert 0.0 <= improvement["conflict_reduction"] <= 100.0
        assert 0.0 <= improvement["resource_efficiency"] <= 100.0

    @pytest.mark.asyncio
    async def test_monitoring_loop_lifecycle(self, mock_context_manager, temp_project_dir):
        """Test the monitoring loop lifecycle."""
        config = ParallelTDDConfiguration(
            enable_performance_monitoring=True,
            health_check_interval=0.1  # Fast for testing
        )
        
        with patch('lib.parallel_tdd_engine.ParallelTDDCoordinator') as mock_coord, \
             patch('lib.parallel_tdd_engine.AgentPool') as mock_pool, \
             patch('lib.parallel_tdd_engine.ConflictResolver') as mock_resolver, \
             patch('lib.parallel_tdd_engine.TDDStateMachine') as mock_machine:
            
            # Configure mocks
            for mock_obj in [mock_coord.return_value, mock_pool.return_value, mock_resolver.return_value]:
                mock_obj.start = AsyncMock()
                mock_obj.stop = AsyncMock()
                mock_obj.get_parallel_status = AsyncMock(return_value={})
                mock_obj.get_pool_status = AsyncMock(return_value={"pool_summary": {}})
                mock_obj.get_resolution_statistics = AsyncMock(return_value={})
            
            engine = ParallelTDDEngine(
                context_manager=mock_context_manager,
                project_path=temp_project_dir,
                config=config
            )
            
            await engine.start()
            
            # Let monitoring run briefly
            await asyncio.sleep(0.15)
            
            await engine.stop()
            
            # Tasks should be cancelled
            assert engine._monitoring_task.cancelled()
            assert engine._optimization_task.cancelled()

    @pytest.mark.asyncio
    async def test_optimization_loop_lifecycle(self, mock_context_manager, temp_project_dir):
        """Test the optimization loop lifecycle."""
        config = ParallelTDDConfiguration(enable_performance_monitoring=True)
        
        with patch('lib.parallel_tdd_engine.ParallelTDDCoordinator') as mock_coord, \
             patch('lib.parallel_tdd_engine.AgentPool') as mock_pool, \
             patch('lib.parallel_tdd_engine.ConflictResolver') as mock_resolver, \
             patch('lib.parallel_tdd_engine.TDDStateMachine') as mock_machine:
            
            # Configure mocks
            for mock_obj in [mock_coord.return_value, mock_pool.return_value, mock_resolver.return_value]:
                mock_obj.start = AsyncMock()
                mock_obj.stop = AsyncMock()
                mock_obj.optimize_scheduling = AsyncMock(return_value="result")
                mock_obj.get_pool_status = AsyncMock(return_value={"agent_types": {}})
                mock_obj.cleanup_expired_resources = Mock(return_value=0)
            
            engine = ParallelTDDEngine(
                context_manager=mock_context_manager,
                project_path=temp_project_dir,
                config=config
            )
            
            # Mock the optimization method to avoid delays
            engine.optimize_performance = AsyncMock()
            
            await engine.start()
            await engine.stop()
            
            # Tasks should be properly cancelled
            assert engine._optimization_task.cancelled()

    @pytest.mark.asyncio
    async def test_component_integration(self, parallel_engine):
        """Test that components are properly integrated."""
        # Check that coordinator has references to other components
        assert parallel_engine.coordinator.agent_pool == parallel_engine.agent_pool
        assert parallel_engine.coordinator.conflict_resolver == parallel_engine.conflict_resolver

    def test_execution_tracking(self, parallel_engine):
        """Test execution tracking functionality."""
        execution_id = str(uuid.uuid4())
        execution_info = {
            "execution_id": execution_id,
            "cycle_ids": ["cycle-1", "cycle-2"],
            "start_time": datetime.utcnow(),
            "status": "running",
            "total_cycles": 2
        }
        
        # Add to active executions
        parallel_engine.active_executions[execution_id] = execution_info
        
        assert execution_id in parallel_engine.active_executions
        assert len(parallel_engine.active_executions) == 1
        
        # Move to history
        parallel_engine.execution_history.append(execution_info)
        del parallel_engine.active_executions[execution_id]
        
        assert execution_id not in parallel_engine.active_executions
        assert len(parallel_engine.execution_history) == 1

    def test_parallel_execution_status_enum(self):
        """Test ParallelExecutionStatus enum values."""
        assert ParallelExecutionStatus.STOPPED.value == "stopped"
        assert ParallelExecutionStatus.STARTING.value == "starting"
        assert ParallelExecutionStatus.RUNNING.value == "running"
        assert ParallelExecutionStatus.PAUSING.value == "pausing"
        assert ParallelExecutionStatus.PAUSED.value == "paused"
        assert ParallelExecutionStatus.STOPPING.value == "stopping"
        assert ParallelExecutionStatus.ERROR.value == "error"

    @pytest.mark.asyncio
    async def test_engine_error_recovery(self, parallel_engine):
        """Test engine behavior after encountering errors."""
        await parallel_engine.start()
        
        # Simulate error condition
        parallel_engine.status = ParallelExecutionStatus.ERROR
        
        # Engine should handle error state gracefully
        status = await parallel_engine.get_engine_status()
        assert status["engine_status"]["status"] == "error"
        
        # Should be able to stop from error state
        await parallel_engine.stop()

    @pytest.mark.asyncio
    async def test_context_request_with_tdd_task(self, parallel_engine):
        """Test context request with TDDTask object."""
        task = TDDTask(
            id="task-1",
            description="Test task",
            acceptance_criteria=["Criterion 1"]
        )
        
        context = await parallel_engine.handle_context_request(
            agent_type="code_agent",
            story_id="STORY-1",
            task=task
        )
        
        assert context is not None
        parallel_engine.context_manager.prepare_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_request_no_context_returned(self, parallel_engine):
        """Test context request when no context is returned."""
        parallel_engine.context_manager.prepare_context.return_value = None
        
        context = await parallel_engine.handle_context_request(
            agent_type="code_agent",
            story_id="STORY-1",
            task={"task": "data"}
        )
        
        assert context is None
        # Metrics should not be updated when no context is returned
        assert parallel_engine.metrics.context_preparation_time == 0.0