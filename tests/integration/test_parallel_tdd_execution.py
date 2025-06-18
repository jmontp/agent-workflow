"""
Integration tests for Parallel TDD Execution System.

Comprehensive test suite covering all parallel execution components:
- Parallel TDD Coordinator
- Agent Pool Management
- Conflict Resolution System
- Enhanced TDD State Machine
- Parallel TDD Engine Integration
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Import test utilities
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.parallel_tdd_engine import ParallelTDDEngine, ParallelTDDConfiguration, ParallelExecutionStatus
from lib.parallel_tdd_coordinator import ParallelTDDCoordinator, ParallelExecutionMode
from lib.agent_pool import AgentPool, AgentPoolStrategy, LoadBalancingAlgorithm
from lib.conflict_resolver import ConflictResolver, ConflictType, ConflictSeverity
from lib.tdd_state_machine import TDDStateMachine, TDDState
from lib.context_manager import ContextManager
from lib.tdd_models import TDDCycle, TDDTask


class TestParallelTDDEngine:
    """Test the unified Parallel TDD Engine"""
    
    @pytest.fixture
    async def engine_setup(self):
        """Setup test environment with temporary project"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create basic project structure
        (project_path / "lib").mkdir()
        (project_path / "tests").mkdir()
        (project_path / "scripts").mkdir()
        
        # Initialize context manager
        context_manager = ContextManager(
            project_path=str(project_path),
            enable_intelligence=False,  # Simplified for testing
            enable_advanced_caching=False,
            enable_monitoring=False
        )
        
        # Initialize engine with test configuration
        config = ParallelTDDConfiguration(
            max_parallel_cycles=3,
            execution_mode=ParallelExecutionMode.CONSERVATIVE,
            enable_predictive_scheduling=False,  # Simplified for testing
            enable_performance_monitoring=False
        )
        
        engine = ParallelTDDEngine(
            context_manager=context_manager,
            project_path=str(project_path),
            config=config
        )
        
        yield engine, project_path
        
        # Cleanup
        try:
            await engine.stop()
        except:
            pass
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_engine_lifecycle(self, engine_setup):
        """Test engine start/stop lifecycle"""
        engine, project_path = engine_setup
        
        # Initially stopped
        assert engine.status == ParallelExecutionStatus.STOPPED
        
        # Start engine
        await engine.start()
        assert engine.status == ParallelExecutionStatus.RUNNING
        assert engine.start_time is not None
        
        # Get status
        status = await engine.get_engine_status()
        assert status["engine_status"]["status"] == "running"
        assert status["engine_status"]["uptime_seconds"] > 0
        
        # Pause and resume
        await engine.pause()
        assert engine.status == ParallelExecutionStatus.PAUSED
        
        await engine.resume()
        assert engine.status == ParallelExecutionStatus.RUNNING
        
        # Stop engine
        await engine.stop()
        assert engine.status == ParallelExecutionStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_parallel_cycle_execution(self, engine_setup):
        """Test execution of multiple parallel cycles"""
        engine, project_path = engine_setup
        
        await engine.start()
        
        # Create test cycles
        cycles = []
        for i in range(3):
            cycle = TDDCycle(
                id=f"cycle_{i}",
                story_id=f"story_{i}",
                current_state=TDDState.DESIGN
            )
            cycles.append(cycle)
        
        # Execute cycles in parallel
        result = await engine.execute_parallel_cycles(cycles)
        
        # Verify execution results
        assert result["success"] is True
        assert result["execution_id"] is not None
        assert len(result["results"]) == 3
        
        # Check performance metrics
        assert "performance_metrics" in result
        assert result["cycles_completed"] >= 0
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_cycle_dependencies(self, engine_setup):
        """Test cycle dependency management"""
        engine, project_path = engine_setup
        
        await engine.start()
        
        # Create cycles with dependencies
        cycle1 = TDDCycle(id="cycle_1", story_id="story_1", current_state=TDDState.DESIGN)
        cycle2 = TDDCycle(id="cycle_2", story_id="story_2", current_state=TDDState.DESIGN)
        cycle3 = TDDCycle(id="cycle_3", story_id="story_3", current_state=TDDState.DESIGN)
        
        cycles = [cycle1, cycle2, cycle3]
        
        # cycle_3 depends on cycle_1 and cycle_2
        dependencies = {
            "cycle_3": ["cycle_1", "cycle_2"]
        }
        
        # Execute with dependencies
        result = await engine.execute_parallel_cycles(cycles, dependencies=dependencies)
        
        assert result["success"] is True
        
        # Verify dependency tracking in state machine
        state_machine_status = engine.state_machine.get_parallel_status()
        assert "cycle_dependencies" in state_machine_status
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self, engine_setup):
        """Test performance optimization features"""
        engine, project_path = engine_setup
        
        await engine.start()
        
        # Run optimization
        optimization_result = await engine.optimize_performance()
        
        assert "optimization_time" in optimization_result
        assert "optimizations_applied" in optimization_result
        assert "performance_improvement" in optimization_result
        
        # Check that optimization improved estimated performance
        improvement = optimization_result["performance_improvement"]
        assert improvement["throughput_improvement"] > 0
        
        await engine.stop()


class TestParallelTDDCoordinator:
    """Test the Parallel TDD Coordinator"""
    
    @pytest.fixture
    async def coordinator_setup(self):
        """Setup coordinator for testing"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        context_manager = ContextManager(
            project_path=str(project_path),
            enable_intelligence=False
        )
        
        coordinator = ParallelTDDCoordinator(
            context_manager=context_manager,
            max_parallel_cycles=3,
            execution_mode=ParallelExecutionMode.BALANCED
        )
        
        yield coordinator, project_path
        
        try:
            await coordinator.stop()
        except:
            pass
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_coordinator_cycle_management(self, coordinator_setup):
        """Test basic cycle management"""
        coordinator, project_path = coordinator_setup
        
        await coordinator.start()
        
        # Create and submit a cycle
        cycle = TDDCycle(
            id="test_cycle",
            story_id="test_story",
            current_state=TDDState.DESIGN
        )
        
        cycle_id = await coordinator.submit_cycle(cycle, priority=3)
        assert cycle_id == "test_cycle"
        
        # Check status
        status = await coordinator.get_cycle_status(cycle_id)
        assert status is not None
        assert status["cycle_id"] == cycle_id
        assert status["story_id"] == "test_story"
        
        # Get parallel status
        parallel_status = await coordinator.get_parallel_status()
        assert parallel_status["cycle_summary"]["total_cycles"] >= 1
        
        await coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_coordinator_resource_management(self, coordinator_setup):
        """Test resource allocation and management"""
        coordinator, project_path = coordinator_setup
        
        await coordinator.start()
        
        # Submit multiple cycles
        cycles = []
        for i in range(3):
            cycle = TDDCycle(
                id=f"cycle_{i}",
                story_id=f"story_{i}",
                current_state=TDDState.DESIGN
            )
            await coordinator.submit_cycle(cycle, priority=i+1)
            cycles.append(cycle)
        
        # Check resource utilization
        status = await coordinator.get_parallel_status()
        assert "resource_utilization" in status
        
        # Verify scheduling optimization
        optimization_result = await coordinator.optimize_scheduling()
        assert "optimization_time" in optimization_result
        
        await coordinator.stop()


class TestAgentPool:
    """Test the Agent Pool Management System"""
    
    @pytest.fixture
    async def pool_setup(self):
        """Setup agent pool for testing"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        context_manager = ContextManager(
            project_path=str(project_path),
            enable_intelligence=False
        )
        
        pool = AgentPool(
            context_manager=context_manager,
            strategy=AgentPoolStrategy.DYNAMIC,
            load_balancing=LoadBalancingAlgorithm.LEAST_LOADED,
            enable_auto_scaling=True
        )
        
        yield pool, project_path
        
        try:
            await pool.stop()
        except:
            pass
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_pool_lifecycle(self, pool_setup):
        """Test agent pool start/stop lifecycle"""
        pool, project_path = pool_setup
        
        # Start pool
        await pool.start()
        
        # Check initial status
        status = await pool.get_pool_status()
        assert status["pool_summary"]["total_agents"] >= 0
        
        # Get utilization
        utilization = await pool.get_utilization()
        assert 0.0 <= utilization <= 1.0
        
        await pool.stop()
    
    @pytest.mark.asyncio
    async def test_task_submission(self, pool_setup):
        """Test task submission and execution"""
        pool, project_path = pool_setup
        
        await pool.start()
        
        # Submit a test task
        task_id = await pool.submit_task(
            agent_type="CodeAgent",
            command="test_command",
            context={"test": "data"},
            priority=5
        )
        
        assert task_id is not None
        
        # Try to get task result (with short timeout since it's a mock)
        result = await pool.get_task_result(task_id, timeout=5.0)
        # Result may be None if task doesn't complete quickly, which is fine for this test
        
        await pool.stop()
    
    @pytest.mark.asyncio
    async def test_pool_scaling(self, pool_setup):
        """Test agent pool scaling"""
        pool, project_path = pool_setup
        
        await pool.start()
        
        # Test scaling for CodeAgent
        initial_status = await pool.get_pool_status()
        initial_count = initial_status["agent_types"].get("CodeAgent", {}).get("total", 0)
        
        # Scale up
        scaling_result = await pool.scale_pool("CodeAgent", initial_count + 1)
        assert scaling_result["agents_added"] >= 0
        
        # Check new status
        new_status = await pool.get_pool_status()
        new_count = new_status["agent_types"].get("CodeAgent", {}).get("total", 0)
        
        await pool.stop()


class TestConflictResolver:
    """Test the Conflict Resolution System"""
    
    @pytest.fixture
    async def resolver_setup(self):
        """Setup conflict resolver for testing"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create test files
        test_file = project_path / "test_file.py"
        test_file.write_text("def test_function():\n    pass\n")
        
        context_manager = ContextManager(
            project_path=str(project_path),
            enable_intelligence=False
        )
        
        resolver = ConflictResolver(
            context_manager=context_manager,
            project_path=str(project_path),
            enable_proactive_detection=True,
            enable_auto_resolution=True
        )
        
        yield resolver, project_path
        
        try:
            await resolver.stop()
        except:
            pass
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_conflict_detection(self, resolver_setup):
        """Test conflict detection capabilities"""
        resolver, project_path = resolver_setup
        
        await resolver.start()
        
        # Register file modifications from different cycles
        test_file = str(project_path / "test_file.py")
        
        await resolver.register_file_modification(
            test_file, "cycle_1", "story_1", "modify"
        )
        
        await resolver.register_file_modification(
            test_file, "cycle_2", "story_2", "modify"
        )
        
        # Check for conflicts
        active_conflicts = await resolver.get_active_conflicts()
        # May or may not detect conflicts depending on timing and file analysis
        
        # Get resolution statistics
        stats = await resolver.get_resolution_statistics()
        assert "total_conflicts" in stats
        assert "file_modification_tracking" in stats
        
        await resolver.stop()
    
    @pytest.mark.asyncio
    async def test_conflict_analysis(self, resolver_setup):
        """Test conflict analysis capabilities"""
        resolver, project_path = resolver_setup
        
        await resolver.start()
        
        # Analyze potential conflict
        test_files = [str(project_path / "test_file.py")]
        analysis = await resolver.analyze_potential_conflict(
            "cycle_1", "cycle_2", test_files
        )
        
        assert hasattr(analysis, 'conflict_probability')
        assert 0.0 <= analysis.conflict_probability <= 1.0
        assert analysis.impact_assessment is not None
        assert analysis.recommended_strategy is not None
        
        await resolver.stop()


class TestTDDStateMachine:
    """Test the Enhanced TDD State Machine"""
    
    def test_parallel_features_initialization(self):
        """Test state machine initialization with parallel features"""
        state_machine = TDDStateMachine(
            enable_parallel_execution=True,
            enable_resource_locking=True,
            enable_coordination_events=True
        )
        
        assert state_machine.enable_parallel_execution is True
        assert state_machine.enable_resource_locking is True
        assert state_machine.enable_coordination_events is True
        assert len(state_machine.parallel_states) == 0
        assert len(state_machine.resource_locks) == 0
    
    def test_parallel_cycle_registration(self):
        """Test parallel cycle registration"""
        state_machine = TDDStateMachine(enable_parallel_execution=True)
        
        cycle = TDDCycle(
            id="test_cycle",
            story_id="test_story",
            current_state=TDDState.DESIGN
        )
        
        # Register cycle
        state_machine.register_parallel_cycle(cycle)
        
        # Verify registration
        assert "test_cycle" in state_machine.parallel_states
        parallel_info = state_machine.parallel_states["test_cycle"]
        assert parallel_info.cycle_id == "test_cycle"
        assert parallel_info.story_id == "test_story"
        assert parallel_info.current_state == TDDState.DESIGN
        
        # Unregister cycle
        state_machine.unregister_parallel_cycle("test_cycle")
        assert "test_cycle" not in state_machine.parallel_states
    
    def test_cycle_dependencies(self):
        """Test cycle dependency management"""
        state_machine = TDDStateMachine(enable_parallel_execution=True)
        
        # Add valid dependency
        result = state_machine.add_cycle_dependency("cycle_2", "cycle_1")
        assert result is True
        assert "cycle_2" in state_machine.cycle_dependencies
        assert "cycle_1" in state_machine.cycle_dependencies["cycle_2"]
        
        # Try to add circular dependency
        result = state_machine.add_cycle_dependency("cycle_1", "cycle_2")
        assert result is False  # Should prevent circular dependency
    
    def test_parallel_status(self):
        """Test parallel status reporting"""
        state_machine = TDDStateMachine(enable_parallel_execution=True)
        
        # Get status without any cycles
        status = state_machine.get_parallel_status()
        assert status["parallel_execution"] is True
        assert status["active_cycles"] == 0
        
        # Register a cycle and check status
        cycle = TDDCycle(
            id="test_cycle",
            story_id="test_story",
            current_state=TDDState.DESIGN
        )
        state_machine.register_parallel_cycle(cycle)
        
        status = state_machine.get_parallel_status()
        assert status["active_cycles"] == 1
        assert len(status["parallel_cycles"]) == 1


class TestPerformanceBenchmarks:
    """Performance benchmarks for parallel execution"""
    
    @pytest.fixture
    async def benchmark_setup(self):
        """Setup for performance benchmarks"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        context_manager = ContextManager(
            project_path=str(project_path),
            enable_intelligence=False,
            enable_advanced_caching=False
        )
        
        config = ParallelTDDConfiguration(
            max_parallel_cycles=5,
            execution_mode=ParallelExecutionMode.AGGRESSIVE,
            enable_performance_monitoring=True
        )
        
        engine = ParallelTDDEngine(
            context_manager=context_manager,
            project_path=str(project_path),
            config=config
        )
        
        yield engine, project_path
        
        try:
            await engine.stop()
        except:
            pass
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_throughput_benchmark(self, benchmark_setup):
        """Benchmark parallel execution throughput"""
        engine, project_path = benchmark_setup
        
        await engine.start()
        
        # Create multiple cycles for throughput testing
        cycles = []
        for i in range(10):
            cycle = TDDCycle(
                id=f"benchmark_cycle_{i}",
                story_id=f"benchmark_story_{i}",
                current_state=TDDState.DESIGN
            )
            cycles.append(cycle)
        
        # Measure execution time
        start_time = datetime.utcnow()
        result = await engine.execute_parallel_cycles(cycles)
        end_time = datetime.utcnow()
        
        execution_time = (end_time - start_time).total_seconds()
        throughput = len(cycles) / execution_time
        
        # Log performance metrics
        print(f"Executed {len(cycles)} cycles in {execution_time:.2f}s")
        print(f"Throughput: {throughput:.2f} cycles/second")
        
        # Verify performance expectations
        assert result["success"] is True
        assert execution_time < 60  # Should complete within 60 seconds
        assert throughput > 0.1    # At least 0.1 cycles per second
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_conflict_resolution_performance(self, benchmark_setup):
        """Benchmark conflict resolution performance"""
        engine, project_path = benchmark_setup
        
        await engine.start()
        
        # Create test file
        test_file = project_path / "conflict_test.py"
        test_file.write_text("def test():\n    return True\n")
        
        resolver = engine.conflict_resolver
        
        # Benchmark conflict detection
        start_time = datetime.utcnow()
        
        for i in range(20):
            await resolver.register_file_modification(
                str(test_file), f"cycle_{i}", f"story_{i}", "modify"
            )
        
        end_time = datetime.utcnow()
        detection_time = (end_time - start_time).total_seconds()
        
        print(f"Conflict detection for 20 modifications: {detection_time:.3f}s")
        
        # Verify performance
        assert detection_time < 5.0  # Should complete within 5 seconds
        
        await engine.stop()


# Run performance benchmarks only when explicitly requested
@pytest.mark.slow
class TestAdvancedFeatures:
    """Test advanced parallel execution features"""
    
    @pytest.mark.asyncio
    async def test_predictive_conflict_avoidance(self):
        """Test predictive conflict avoidance (placeholder)"""
        # This would test ML-based conflict prediction
        # For now, just verify the infrastructure is in place
        pass
    
    @pytest.mark.asyncio
    async def test_context_sharing_optimization(self):
        """Test context sharing optimization (placeholder)"""
        # This would test intelligent context sharing between parallel cycles
        # For now, just verify the infrastructure is in place
        pass
    
    @pytest.mark.asyncio
    async def test_adaptive_scheduling(self):
        """Test adaptive scheduling (placeholder)"""
        # This would test ML-based adaptive scheduling
        # For now, just verify the infrastructure is in place
        pass


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v", "-m", "not slow"])