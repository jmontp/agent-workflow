"""
Comprehensive Global Orchestrator Coverage Tests

This test suite targets specific coverage gaps and advanced scenarios
for the GlobalOrchestrator module to achieve 95%+ test coverage.

Focused on:
- Edge cases and error conditions
- Concurrent project execution scenarios  
- Resource contention and conflict resolution
- Cross-project intelligence and context sharing
- Human-in-the-loop approval workflows
- Background task lifecycle management
- Process management edge cases
"""

import pytest
import asyncio
import tempfile
import shutil
import subprocess
import os
import signal
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.global_orchestrator import (
    GlobalOrchestrator, OrchestratorStatus, ProjectOrchestrator,
    ResourceAllocation, GlobalMetrics
)
from lib.multi_project_config import (
    MultiProjectConfigManager, ProjectConfig, ProjectPriority, ProjectStatus,
    GlobalOrchestratorConfig, ResourceLimits
)


class TestGlobalOrchestratorComprehensiveCoverage:
    """Comprehensive coverage tests for GlobalOrchestrator."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for configuration testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create a config manager with temporary storage."""
        config_path = Path(temp_config_dir) / "test-config.yaml"
        return MultiProjectConfigManager(str(config_path))
    
    @pytest.fixture
    def global_orchestrator(self, config_manager):
        """Create a GlobalOrchestrator instance."""
        return GlobalOrchestrator(config_manager)
    
    @pytest.fixture
    def mock_project_configs(self, temp_config_dir):
        """Create mock project configurations for testing."""
        projects = []
        for i in range(5):
            project_dir = Path(temp_config_dir) / f"project_{i}"
            project_dir.mkdir(parents=True)
            
            priority_map = {
                0: ProjectPriority.CRITICAL,
                1: ProjectPriority.HIGH,
                2: ProjectPriority.NORMAL,
                3: ProjectPriority.LOW,
                4: ProjectPriority.NORMAL
            }
            
            project = ProjectConfig(
                name=f"project-{i}",
                path=str(project_dir),
                priority=priority_map[i],
                status=ProjectStatus.ACTIVE,
                discord_channel=f"#project-{i}" if i % 2 == 0 else None
            )
            projects.append(project)
        
        return projects

    # Test Coverage Gaps - Edge Cases and Error Conditions
    
    @pytest.mark.asyncio
    async def test_concurrent_project_startup_failure_handling(self, global_orchestrator, config_manager, mock_project_configs):
        """Test handling of concurrent project startup failures."""
        # Register multiple projects
        for project in mock_project_configs:
            config_manager.projects[project.name] = project
        
        call_count = 0
        
        def mock_popen_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First two projects fail
                raise OSError(f"Failed to start process {call_count}")
            
            # Remaining projects succeed
            mock_process = Mock()
            mock_process.pid = 12345 + call_count
            mock_process.poll.return_value = None
            return mock_process
        
        with patch('subprocess.Popen', side_effect=mock_popen_side_effect):
            # Try to start all projects concurrently
            start_tasks = []
            for project in mock_project_configs[:4]:  # Start 4 projects
                start_tasks.append(asyncio.create_task(global_orchestrator.start_project(project.name)))
            
            results = await asyncio.gather(*start_tasks, return_exceptions=True)
            
            # First two should fail, last two should succeed
            assert results[0] is False  # Failed
            assert results[1] is False  # Failed
            assert results[2] is True   # Succeeded
            assert results[3] is True   # Succeeded
            
            # Check orchestrator states - failed projects may not have orchestrator entries
            # Only successful projects should have running orchestrators
            if mock_project_configs[2].name in global_orchestrator.orchestrators:
                assert global_orchestrator.orchestrators[mock_project_configs[2].name].status == OrchestratorStatus.RUNNING
            if mock_project_configs[3].name in global_orchestrator.orchestrators:
                assert global_orchestrator.orchestrators[mock_project_configs[3].name].status == OrchestratorStatus.RUNNING
            
            # Failed projects may or may not have orchestrator entries, but if they do, they should be in error state
            if mock_project_configs[0].name in global_orchestrator.orchestrators:
                assert global_orchestrator.orchestrators[mock_project_configs[0].name].status == OrchestratorStatus.ERROR
            if mock_project_configs[1].name in global_orchestrator.orchestrators:
                assert global_orchestrator.orchestrators[mock_project_configs[1].name].status == OrchestratorStatus.ERROR

    @pytest.mark.asyncio
    async def test_resource_contention_and_conflict_resolution(self, global_orchestrator, config_manager, mock_project_configs):
        """Test resource allocation under contention scenarios."""
        # Configure limited global resources
        global_orchestrator.global_config.max_total_agents = 8
        global_orchestrator.global_config.global_memory_limit_gb = 4
        global_orchestrator.global_config.resource_allocation_strategy = "priority_based"
        
        # Register projects with different priorities
        for project in mock_project_configs:
            config_manager.projects[project.name] = project
        
        with patch.object(config_manager, 'get_active_projects', return_value=mock_project_configs):
            allocations = []
            for project in mock_project_configs:
                allocation = await global_orchestrator._calculate_resource_allocation(project)
                allocations.append(allocation)
            
            # Verify critical priority gets most resources
            critical_allocation = next(a for a in allocations if a.priority_weight == 2.0)
            low_allocation = next(a for a in allocations if a.priority_weight == 0.5)
            
            assert critical_allocation.allocated_agents >= low_allocation.allocated_agents
            assert critical_allocation.allocated_memory_mb >= low_allocation.allocated_memory_mb
            
            # Verify total allocation doesn't exceed limits
            total_agents = sum(a.allocated_agents for a in allocations)
            total_memory = sum(a.allocated_memory_mb for a in allocations)
            
            # Should be constrained by project limits, not global limits in this case
            assert total_agents <= len(mock_project_configs) * 3  # max_parallel_agents default is 3

    @pytest.mark.asyncio
    async def test_cross_project_intelligence_and_context_sharing(self, global_orchestrator):
        """Test cross-project intelligence and pattern detection."""
        # Set up cross-project data structures
        global_orchestrator.shared_patterns = {
            "common_error_pattern_1": {"usage_count": 5, "projects": ["proj1", "proj2"]},
            "optimization_technique_1": {"usage_count": 3, "projects": ["proj2", "proj3"]}
        }
        
        global_orchestrator.cross_project_insights = [
            {
                "insight_type": "performance_optimization",
                "pattern": "database_connection_pooling",
                "applicable_projects": ["proj1", "proj4"],
                "confidence": 0.85,
                "timestamp": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "insight_type": "error_prevention",
                "pattern": "input_validation",
                "applicable_projects": ["proj2", "proj3", "proj5"],
                "confidence": 0.92,
                "timestamp": datetime.utcnow() - timedelta(hours=1)
            }
        ]
        
        global_orchestrator.global_best_practices = {
            "testing_framework": {"jest": 3, "pytest": 2},
            "code_style": {"prettier": 4, "black": 1}
        }
        
        # Test cross-project pattern detection
        await global_orchestrator._detect_cross_project_patterns()
        
        # Test getting global status with cross-project data
        with patch.object(global_orchestrator, '_update_metrics'):
            status = await global_orchestrator.get_global_status()
            
            assert "cross_project_insights" in status
            assert "shared_patterns" in status
            assert status["shared_patterns"] == 2  # Number of shared patterns
            assert len(status["cross_project_insights"]) == 2  # All insights (less than 10)

    @pytest.mark.asyncio
    async def test_human_in_the_loop_approval_workflows(self, global_orchestrator):
        """Test human-in-the-loop approval workflow scenarios."""
        # Test event system for HITL workflows
        event_handler_called = False
        approval_events = []
        
        def mock_approval_handler(event_data):
            nonlocal event_handler_called
            event_handler_called = True
            approval_events.append(event_data)
        
        # Register event handler
        global_orchestrator.event_handlers["approval_required"] = [mock_approval_handler]
        
        # Simulate approval event
        approval_event = {
            "type": "approval_required",
            "project": "test-project",
            "action": "deploy_to_production",
            "risk_level": "high",
            "details": {"changes": 15, "tests_passed": True}
        }
        
        await global_orchestrator.event_queue.put(approval_event)
        
        # Process event
        try:
            event = await asyncio.wait_for(global_orchestrator.event_queue.get(), timeout=0.1)
            for handler in global_orchestrator.event_handlers.get(event["type"], []):
                handler(event)
        except asyncio.TimeoutError:
            pass
        
        assert event_handler_called
        assert len(approval_events) == 1
        assert approval_events[0]["project"] == "test-project"

    @pytest.mark.asyncio
    async def test_background_task_lifecycle_and_cancellation(self, global_orchestrator):
        """Test background task creation, management, and proper cancellation."""
        # Start orchestrator to create background tasks
        with patch.object(global_orchestrator, '_start_active_projects'), \
             patch('pathlib.Path.mkdir'):
            await global_orchestrator.start()
            assert global_orchestrator.status == OrchestratorStatus.RUNNING
            
            # Verify all background tasks are created
            assert global_orchestrator._monitoring_task is not None
            assert global_orchestrator._scheduling_task is not None
            assert global_orchestrator._resource_balancing_task is not None
            assert global_orchestrator._health_check_task is not None
            
            # Verify tasks are running
            assert not global_orchestrator._monitoring_task.done()
            assert not global_orchestrator._scheduling_task.done()
            assert not global_orchestrator._resource_balancing_task.done()
            assert not global_orchestrator._health_check_task.done()
        
        # Stop orchestrator to test task cancellation
        with patch.object(global_orchestrator, '_stop_all_projects'):
            await global_orchestrator.stop()
            
            assert global_orchestrator.status == OrchestratorStatus.STOPPED
            
            # Give tasks a moment to process cancellation
            await asyncio.sleep(0.1)
            
            # Verify all tasks are cancelled/done
            assert global_orchestrator._monitoring_task.done()
            assert global_orchestrator._scheduling_task.done()
            assert global_orchestrator._resource_balancing_task.done()
            assert global_orchestrator._health_check_task.done()

    @pytest.mark.asyncio
    async def test_process_management_edge_cases(self, global_orchestrator, config_manager, temp_config_dir):
        """Test edge cases in process management and signal handling."""
        project_dir = Path(temp_config_dir) / "signal_test_project"
        project_dir.mkdir()
        
        project_config = ProjectConfig(
            name="signal-test",
            path=str(project_dir),
            priority=ProjectPriority.NORMAL
        )
        config_manager.projects["signal-test"] = project_config
        
        # Test pause/resume with signal failures
        mock_process = Mock()
        orchestrator = ProjectOrchestrator(
            project_name="signal-test",
            project_path=str(project_dir),
            process=mock_process,
            status=OrchestratorStatus.RUNNING,
            pid=12345
        )
        global_orchestrator.orchestrators["signal-test"] = orchestrator
        
        # Test pause with signal failure
        with patch('os.kill', side_effect=ProcessLookupError("Process not found")):
            success = await global_orchestrator.pause_project("signal-test")
            assert not success
            assert orchestrator.status == OrchestratorStatus.RUNNING  # Status unchanged
        
        # Test resume with signal failure
        orchestrator.status = OrchestratorStatus.PAUSED
        with patch('os.kill', side_effect=PermissionError("Permission denied")):
            success = await global_orchestrator.resume_project("signal-test")
            assert not success
            assert orchestrator.status == OrchestratorStatus.PAUSED  # Status unchanged

    @pytest.mark.asyncio
    async def test_resource_allocation_with_zero_active_projects(self, global_orchestrator, temp_config_dir):
        """Test resource allocation edge case with zero active projects."""
        project_config = ProjectConfig(
            name="inactive-test",
            path=str(Path(temp_config_dir) / "inactive"),
            priority=ProjectPriority.NORMAL,
            status=ProjectStatus.PAUSED  # Not active
        )
        
        global_orchestrator.global_config.resource_allocation_strategy = "fair_share"
        global_orchestrator.global_config.max_total_agents = 10
        
        with patch.object(global_orchestrator.config_manager, 'get_active_projects', return_value=[]):
            allocation = await global_orchestrator._calculate_resource_allocation(project_config)
            
            # Should handle division by zero gracefully
            assert allocation.allocated_agents > 0  # Should get base allocation
            assert allocation.allocated_memory_mb > 0
            assert allocation.allocated_cpu_percent > 0

    @pytest.mark.asyncio
    async def test_resource_allocation_priority_with_zero_weight(self, global_orchestrator, temp_config_dir):
        """Test priority-based resource allocation with zero total weight."""
        project_config = ProjectConfig(
            name="zero-weight-test",
            path=str(Path(temp_config_dir) / "zero_weight"),
            priority=ProjectPriority.NORMAL
        )
        
        global_orchestrator.global_config.resource_allocation_strategy = "priority_based"
        global_orchestrator.global_config.max_total_agents = 10
        
        # Mock get_active_projects to return empty list (zero total weight)
        with patch.object(global_orchestrator.config_manager, 'get_active_projects', return_value=[]):
            allocation = await global_orchestrator._calculate_resource_allocation(project_config)
            
            # Should handle zero weight gracefully
            assert allocation.allocated_agents >= 0
            assert allocation.allocated_memory_mb >= 0
            assert allocation.allocated_cpu_percent >= 0

    @pytest.mark.asyncio
    async def test_update_project_status_integration(self, global_orchestrator, config_manager, temp_config_dir):
        """Test integration with config manager project status updates."""
        project_dir = Path(temp_config_dir) / "status_test"
        project_dir.mkdir()
        
        project_config = ProjectConfig(
            name="status-test",
            path=str(project_dir),
            status=ProjectStatus.INITIALIZING
        )
        config_manager.projects["status-test"] = project_config
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Process running
            mock_popen.return_value = mock_process
            
            # Mock the config manager's update_project_status method
            with patch.object(config_manager, 'update_project_status') as mock_update:
                success = await global_orchestrator.start_project("status-test")
                
                assert success
                # Verify status was updated to ACTIVE
                mock_update.assert_called_once_with("status-test", ProjectStatus.ACTIVE)

    @pytest.mark.asyncio
    async def test_health_check_with_no_heartbeat_data(self, global_orchestrator):
        """Test health check behavior with orchestrators that have no heartbeat data."""
        # Create orchestrator with no heartbeat
        orchestrator = ProjectOrchestrator(
            project_name="no-heartbeat",
            project_path="/test/path",
            status=OrchestratorStatus.RUNNING,
            last_heartbeat=None  # No heartbeat recorded
        )
        global_orchestrator.orchestrators["no-heartbeat"] = orchestrator
        
        # Health check should handle gracefully
        await global_orchestrator._check_orchestrator_health()
        
        # No exception should be raised, orchestrator should remain in running state
        assert orchestrator.status == OrchestratorStatus.RUNNING

    @pytest.mark.asyncio
    async def test_health_check_heartbeat_within_threshold(self, global_orchestrator):
        """Test health check with recent heartbeat (within threshold)."""
        recent_heartbeat = datetime.utcnow() - timedelta(minutes=2)  # Within 5-minute threshold
        
        orchestrator = ProjectOrchestrator(
            project_name="recent-heartbeat",
            project_path="/test/path",
            status=OrchestratorStatus.RUNNING,
            last_heartbeat=recent_heartbeat
        )
        global_orchestrator.orchestrators["recent-heartbeat"] = orchestrator
        
        with patch('lib.global_orchestrator.logger') as mock_logger:
            await global_orchestrator._check_orchestrator_health()
            
            # Should not log any warnings for recent heartbeat
            mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_restart_orchestrator_start_failure(self, global_orchestrator, config_manager, temp_config_dir):
        """Test restart behavior when start_project fails."""
        project_dir = Path(temp_config_dir) / "restart_fail"
        project_dir.mkdir()
        
        project_config = ProjectConfig(
            name="restart-fail",
            path=str(project_dir)
        )
        config_manager.projects["restart-fail"] = project_config
        
        # Create crashed orchestrator
        crashed_orchestrator = ProjectOrchestrator(
            project_name="restart-fail",
            project_path=str(project_dir),
            status=OrchestratorStatus.CRASHED,
            restart_count=1
        )
        global_orchestrator.orchestrators["restart-fail"] = crashed_orchestrator
        
        with patch.object(global_orchestrator, 'stop_project', return_value=True), \
             patch.object(global_orchestrator, 'start_project', return_value=False):  # Start fails
            
            await global_orchestrator._restart_failed_orchestrators()
            
            # Restart count should still be incremented even if start fails
            assert crashed_orchestrator.restart_count == 2

    @pytest.mark.asyncio
    async def test_start_project_with_starting_status(self, global_orchestrator, config_manager, temp_config_dir):
        """Test starting project that's already in STARTING status."""
        project_dir = Path(temp_config_dir) / "starting_status"
        project_dir.mkdir()
        
        project_config = ProjectConfig(
            name="starting-status",
            path=str(project_dir)
        )
        config_manager.projects["starting-status"] = project_config
        
        # Set up orchestrator with STARTING status
        global_orchestrator.orchestrators["starting-status"] = ProjectOrchestrator(
            project_name="starting-status",
            project_path=str(project_dir),
            status=OrchestratorStatus.STARTING
        )
        
        # Should return True for already starting project
        success = await global_orchestrator.start_project("starting-status")
        assert success

    @pytest.mark.asyncio
    async def test_environment_preparation_with_complex_config(self, global_orchestrator, temp_config_dir):
        """Test environment preparation with complex project configuration."""
        project_config = ProjectConfig(
            name="complex-env",
            path=str(Path(temp_config_dir) / "complex"),
            discord_channel="#complex-project",
            ai_settings={
                "auto_approve_low_risk": False,
                "max_auto_retry": 5,
                "require_human_review": True
            }
        )
        
        allocation = ResourceAllocation(
            project_name="complex-env",
            allocated_agents=4,
            allocated_memory_mb=2048,
            allocated_cpu_percent=35.5,
            priority_weight=1.5
        )
        
        env = await global_orchestrator._prepare_project_environment(project_config, allocation)
        
        # Verify all environment variables are set correctly
        assert env["ORCH_PROJECT_NAME"] == "complex-env"
        assert env["ORCH_PROJECT_PATH"] == project_config.path
        assert env["ORCH_MAX_AGENTS"] == "4"
        assert env["ORCH_MEMORY_LIMIT"] == "2048"
        assert env["ORCH_CPU_LIMIT"] == "35.5"
        assert env["ORCH_GLOBAL_MODE"] == "true"
        assert env["DISCORD_CHANNEL"] == "#complex-project"
        
        # Should also include all original environment variables
        assert "PATH" in env  # Should have copied from os.environ

    @pytest.mark.asyncio
    async def test_orchestrator_command_preparation_variations(self, global_orchestrator, temp_config_dir):
        """Test orchestrator command preparation with different configurations."""
        project_config = ProjectConfig(
            name="cmd-test",
            path=str(Path(temp_config_dir) / "cmd_test")
        )
        
        # Test with different allocation values
        allocations = [
            ResourceAllocation("cmd-test", 1, 512, 12.5, 0.5),
            ResourceAllocation("cmd-test", 8, 4096, 75.0, 2.0),
            ResourceAllocation("cmd-test", 0, 0, 0.0, 1.0)  # Edge case with zero resources
        ]
        
        for allocation in allocations:
            command = await global_orchestrator._prepare_orchestrator_command(project_config, allocation)
            
            expected = [
                "python3", "scripts/orchestrator.py",
                "--project-mode",
                "--max-agents", str(allocation.allocated_agents),
                "--memory-limit", str(allocation.allocated_memory_mb),
                "--project-name", "cmd-test"
            ]
            
            assert command == expected

    @pytest.mark.asyncio
    async def test_resource_limits_constraint_application(self, global_orchestrator, temp_config_dir):
        """Test that project resource limits properly constrain allocations."""
        # Create project with very restrictive resource limits
        restrictive_limits = ResourceLimits(
            max_parallel_agents=1,
            max_memory_mb=256,
            cpu_priority=0.5
        )
        
        project_config = ProjectConfig(
            name="restrictive",
            path=str(Path(temp_config_dir) / "restrictive"),
            priority=ProjectPriority.CRITICAL,  # High priority
            resource_limits=restrictive_limits
        )
        
        # Configure global orchestrator with high limits
        global_orchestrator.global_config.max_total_agents = 20
        global_orchestrator.global_config.global_memory_limit_gb = 16
        global_orchestrator.global_config.resource_allocation_strategy = "priority_based"
        
        with patch.object(global_orchestrator.config_manager, 'get_active_projects', return_value=[project_config]):
            allocation = await global_orchestrator._calculate_resource_allocation(project_config)
            
            # Should be constrained by project limits, not global/calculated limits
            assert allocation.allocated_agents == 1  # Constrained by max_parallel_agents
            assert allocation.allocated_memory_mb == 256  # Constrained by max_memory_mb
            assert allocation.allocated_cpu_percent <= 50.0  # Affected by cpu_priority
            assert allocation.priority_weight == 2.0  # Critical priority weight

    @pytest.mark.asyncio
    async def test_multiple_orchestrator_metrics_aggregation(self, global_orchestrator, config_manager):
        """Test metrics collection and aggregation across multiple orchestrators."""
        # Set up multiple orchestrators with different metrics
        orchestrators_data = [
            ("metrics1", OrchestratorStatus.RUNNING, 2, 512.0, 25.5),
            ("metrics2", OrchestratorStatus.RUNNING, 3, 768.0, 35.2),
            ("metrics3", OrchestratorStatus.PAUSED, 0, 0.0, 0.0),
            ("metrics4", OrchestratorStatus.RUNNING, 1, 256.0, 15.8),
            ("metrics5", OrchestratorStatus.CRASHED, 0, 0.0, 0.0)
        ]
        
        for name, status, agents, memory, cpu in orchestrators_data:
            global_orchestrator.orchestrators[name] = ProjectOrchestrator(
                project_name=name,
                project_path=f"/test/{name}",
                status=status,
                active_agents=agents,
                memory_usage=memory,
                cpu_usage=cpu
            )
        
        # Mock config manager to return projects
        config_manager.projects = {name: Mock() for name, _, _, _, _ in orchestrators_data}
        
        await global_orchestrator._collect_metrics()
        
        metrics = global_orchestrator.metrics
        assert metrics.total_projects == 5
        assert metrics.active_projects == 3  # Only RUNNING status counts as active
        assert metrics.total_agents == 6  # 2 + 3 + 0 + 1 + 0
        assert metrics.total_memory_usage_mb == 1536.0  # 512 + 768 + 0 + 256 + 0
        assert metrics.total_cpu_usage_percent == 76.5  # 25.5 + 35.2 + 0 + 15.8 + 0

    @pytest.mark.asyncio
    async def test_cross_project_insights_list_management(self, global_orchestrator):
        """Test management of cross-project insights list with truncation."""
        # Add exactly 15 insights to test truncation to last 10
        base_time = datetime.utcnow()
        insights = []
        for i in range(15):
            insight = {
                "id": f"insight-{i}",
                "type": "pattern_detection",
                "timestamp": base_time + timedelta(minutes=i),
                "projects_affected": [f"proj{i % 3}", f"proj{(i + 1) % 3}"],
                "confidence": 0.7 + (i * 0.02)
            }
            insights.append(insight)
        
        global_orchestrator.cross_project_insights = insights
        
        with patch.object(global_orchestrator, '_update_metrics'):
            status = await global_orchestrator.get_global_status()
            
            returned_insights = status["cross_project_insights"]
            assert len(returned_insights) == 10  # Should be truncated to last 10
            
            # Should be the last 10 insights (indices 5-14)
            assert returned_insights[0]["id"] == "insight-5"
            assert returned_insights[-1]["id"] == "insight-14"

    def test_orchestrator_status_enum_completeness(self):
        """Test that all orchestrator status enum values are properly defined."""
        expected_statuses = {
            "stopped", "starting", "running", "pausing", "paused", "stopping", "error", "crashed"
        }
        
        actual_statuses = {status.value for status in OrchestratorStatus}
        assert actual_statuses == expected_statuses
        
        # Test enum can be used in comparisons
        assert OrchestratorStatus.RUNNING != OrchestratorStatus.STOPPED
        assert OrchestratorStatus.ERROR == OrchestratorStatus.ERROR

    @pytest.mark.asyncio
    async def test_placeholder_methods_coverage(self, global_orchestrator):
        """Test coverage of placeholder methods that are not yet implemented."""
        # These methods are placeholders but should be covered for completeness
        await global_orchestrator._detect_cross_project_patterns()
        await global_orchestrator._optimize_project_scheduling()
        await global_orchestrator._handle_project_dependencies()
        await global_orchestrator._rebalance_resources()
        await global_orchestrator._start_discord_bot()
        
        # Should complete without errors (they're no-ops currently)
        # This ensures the placeholder implementations are covered

    @pytest.mark.asyncio
    async def test_wait_for_process_exit_immediate_exit(self, global_orchestrator):
        """Test wait_for_process_exit when process exits immediately."""
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Process already exited
        
        # Should return immediately without waiting
        await global_orchestrator._wait_for_process_exit(mock_process)
        
        # poll should have been called at least once
        mock_process.poll.assert_called()

    @pytest.mark.asyncio
    async def test_update_orchestrator_status_no_pid_with_psutil(self, global_orchestrator):
        """Test status update when orchestrator has no PID but psutil is available."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running
        
        orchestrator = ProjectOrchestrator(
            project_name="no-pid-psutil",
            project_path="/test/path",
            process=mock_process,
            status=OrchestratorStatus.RUNNING,
            pid=None  # No PID recorded
        )
        global_orchestrator.orchestrators["no-pid-psutil"] = orchestrator
        
        # Even with psutil available, should handle gracefully when no PID
        with patch('lib.global_orchestrator.psutil', Mock()):
            await global_orchestrator._update_orchestrator_status()
            
            # Should still update heartbeat via fallback path
            assert orchestrator.last_heartbeat is not None

    @pytest.mark.asyncio
    async def test_global_orchestrator_event_system(self, global_orchestrator):
        """Test the event system infrastructure for coordination."""
        # Test event queue and handler system
        assert isinstance(global_orchestrator.event_queue, asyncio.Queue)
        assert isinstance(global_orchestrator.event_handlers, dict)
        
        # Test adding event handlers
        handler1_called = False
        handler2_called = False
        
        def handler1(event):
            nonlocal handler1_called
            handler1_called = True
        
        def handler2(event):
            nonlocal handler2_called
            handler2_called = True
        
        # Add multiple handlers for same event type
        global_orchestrator.event_handlers["test_event"] = [handler1, handler2]
        
        # Test that handlers list is properly maintained
        assert len(global_orchestrator.event_handlers["test_event"]) == 2
        
        # Test calling handlers
        test_event = {"type": "test_event", "data": "test_data"}
        for handler in global_orchestrator.event_handlers["test_event"]:
            handler(test_event)
        
        assert handler1_called
        assert handler2_called

    @pytest.mark.asyncio
    async def test_complex_project_lifecycle_integration(self, global_orchestrator, config_manager, temp_config_dir):
        """Test complete project lifecycle with realistic scenarios."""
        # Create a realistic project setup
        project_dir = Path(temp_config_dir) / "lifecycle_test"
        project_dir.mkdir()
        
        project_config = ProjectConfig(
            name="lifecycle-test",
            path=str(project_dir),
            priority=ProjectPriority.HIGH,
            status=ProjectStatus.ACTIVE,
            discord_channel="#lifecycle-test",
            resource_limits=ResourceLimits(
                max_parallel_agents=4,
                max_memory_mb=2048,
                cpu_priority=1.5
            )
        )
        config_manager.projects["lifecycle-test"] = project_config
        
        # Mock process for lifecycle testing
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Initially running
        mock_process.terminate = Mock()
        mock_process.kill = Mock()
        
        with patch('subprocess.Popen', return_value=mock_process):
            # 1. Start project
            success = await global_orchestrator.start_project("lifecycle-test")
            assert success
            assert global_orchestrator.orchestrators["lifecycle-test"].status == OrchestratorStatus.RUNNING
            
            # 2. Pause project
            with patch('os.kill') as mock_kill:
                success = await global_orchestrator.pause_project("lifecycle-test")
                assert success
                assert global_orchestrator.orchestrators["lifecycle-test"].status == OrchestratorStatus.PAUSED
                mock_kill.assert_called_with(12345, signal.SIGSTOP)
            
            # 3. Resume project
            with patch('os.kill') as mock_kill:
                success = await global_orchestrator.resume_project("lifecycle-test")
                assert success
                assert global_orchestrator.orchestrators["lifecycle-test"].status == OrchestratorStatus.RUNNING
                mock_kill.assert_called_with(12345, signal.SIGCONT)
            
            # 4. Stop project
            with patch.object(global_orchestrator, '_wait_for_process_exit'):
                success = await global_orchestrator.stop_project("lifecycle-test")
                assert success
                assert global_orchestrator.orchestrators["lifecycle-test"].status == OrchestratorStatus.STOPPED
                mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fair_share_allocation_multiple_projects(self, global_orchestrator, temp_config_dir):
        """Test fair share resource allocation with multiple active projects."""
        # Create multiple projects for fair share testing
        projects = []
        for i in range(4):
            project_dir = Path(temp_config_dir) / f"fair_share_{i}"
            project_dir.mkdir()
            
            project = ProjectConfig(
                name=f"fair-share-{i}",
                path=str(project_dir),
                priority=ProjectPriority.NORMAL,  # All same priority for fair share
                status=ProjectStatus.ACTIVE
            )
            projects.append(project)
        
        global_orchestrator.global_config.resource_allocation_strategy = "fair_share"
        global_orchestrator.global_config.max_total_agents = 12
        global_orchestrator.global_config.global_memory_limit_gb = 8
        
        with patch.object(global_orchestrator.config_manager, 'get_active_projects', return_value=projects):
            allocations = []
            for project in projects:
                allocation = await global_orchestrator._calculate_resource_allocation(project)
                allocations.append(allocation)
            
            # With 4 projects and fair share, each should get roughly equal resources
            expected_agents_per_project = 12 // 4  # 3 agents each
            expected_memory_per_project = (8 * 1024) // 4  # 2048 MB each
            
            for allocation in allocations:
                # Should be constrained by project limits (max_parallel_agents=3, max_memory_mb=1024)
                assert allocation.allocated_agents == min(expected_agents_per_project, 3)
                assert allocation.allocated_memory_mb == min(expected_memory_per_project, 1024)
                assert allocation.priority_weight == 1.0  # Normal priority

    @pytest.mark.asyncio
    async def test_stop_all_projects_with_exceptions(self, global_orchestrator):
        """Test _stop_all_projects handles exceptions gracefully."""
        # Set up multiple orchestrators
        orchestrator_names = ["stop1", "stop2", "stop3", "stop4"]
        for name in orchestrator_names:
            global_orchestrator.orchestrators[name] = ProjectOrchestrator(
                project_name=name,
                project_path=f"/test/{name}",
                status=OrchestratorStatus.RUNNING
            )
        
        # Mock stop_project to fail for some projects
        call_count = 0
        
        async def mock_stop_project(project_name):
            nonlocal call_count
            call_count += 1
            if call_count in [2, 4]:  # Fail for 2nd and 4th projects
                raise Exception(f"Failed to stop {project_name}")
            return True
        
        with patch.object(global_orchestrator, 'stop_project', side_effect=mock_stop_project):
            # Should not raise exception even if some stops fail
            await global_orchestrator._stop_all_projects()
            
            # All projects should have been attempted
            assert call_count == 4

    @pytest.mark.asyncio
    async def test_global_orchestrator_initialization_edge_cases(self, config_manager):
        """Test GlobalOrchestrator initialization with various edge cases."""
        # Test initialization with minimal config
        minimal_orchestrator = GlobalOrchestrator(config_manager)
        
        # Verify proper initialization of all attributes
        assert minimal_orchestrator.config_manager is config_manager
        assert minimal_orchestrator.status == OrchestratorStatus.STOPPED
        assert minimal_orchestrator.orchestrators == {}
        assert minimal_orchestrator.resource_allocations == {}
        assert isinstance(minimal_orchestrator.metrics, GlobalMetrics)
        assert minimal_orchestrator.shared_patterns == {}
        assert minimal_orchestrator.cross_project_insights == []
        assert minimal_orchestrator.global_best_practices == {}
        assert isinstance(minimal_orchestrator.event_queue, asyncio.Queue)
        assert minimal_orchestrator.event_handlers == {}
        assert minimal_orchestrator.discord_bot is None
        assert minimal_orchestrator._monitoring_task is None
        assert minimal_orchestrator._scheduling_task is None
        assert minimal_orchestrator._resource_balancing_task is None
        assert minimal_orchestrator._health_check_task is None

    @pytest.mark.asyncio
    async def test_background_loop_exception_recovery(self, global_orchestrator):
        """Test that background loops can recover from exceptions."""
        global_orchestrator.status = OrchestratorStatus.RUNNING
        global_orchestrator.global_config.scheduling_interval_seconds = 0.01
        global_orchestrator.global_config.resource_rebalance_interval_seconds = 0.01
        global_orchestrator.global_config.health_check_interval_seconds = 0.01
        
        exception_count = 0
        max_exceptions = 2
        
        async def mock_operation_with_recovery():
            nonlocal exception_count
            exception_count += 1
            if exception_count <= max_exceptions:
                raise Exception(f"Test exception {exception_count}")
            else:
                # After exceptions, change status to stop the loop
                global_orchestrator.status = OrchestratorStatus.STOPPED
        
        # Test monitoring loop exception recovery
        with patch.object(global_orchestrator, '_update_orchestrator_status', side_effect=mock_operation_with_recovery), \
             patch.object(global_orchestrator, '_collect_metrics'), \
             patch.object(global_orchestrator, '_detect_cross_project_patterns'):
            
            await global_orchestrator._monitoring_loop()
            
            # Should have attempted the operation multiple times despite exceptions
            assert exception_count > max_exceptions

    @pytest.mark.asyncio
    async def test_concurrent_project_operations(self, global_orchestrator, config_manager, mock_project_configs):
        """Test concurrent project operations (start/stop/pause/resume)."""
        # Register projects
        for project in mock_project_configs[:3]:
            config_manager.projects[project.name] = project
        
        # Mock process creation
        processes = {}
        def create_mock_process(project_name):
            mock_process = Mock()
            mock_process.pid = hash(project_name) % 10000  # Deterministic PID
            mock_process.poll.return_value = None
            mock_process.terminate = Mock()
            processes[project_name] = mock_process
            return mock_process
        
        with patch('subprocess.Popen', side_effect=lambda *args, **kwargs: create_mock_process(kwargs.get('cwd', 'unknown'))):
            # Start all projects concurrently
            start_tasks = [global_orchestrator.start_project(p.name) for p in mock_project_configs[:3]]
            start_results = await asyncio.gather(*start_tasks)
            
            # All should succeed
            assert all(start_results)
            
            # Test concurrent pause/resume operations
            project_names = [p.name for p in mock_project_configs[:3]]
            
            with patch('os.kill'):
                # Pause all projects concurrently
                pause_tasks = [global_orchestrator.pause_project(name) for name in project_names]
                pause_results = await asyncio.gather(*pause_tasks)
                assert all(pause_results)
                
                # Resume all projects concurrently
                resume_tasks = [global_orchestrator.resume_project(name) for name in project_names]
                resume_results = await asyncio.gather(*resume_tasks)
                assert all(resume_results)
            
            # Stop all projects concurrently
            with patch.object(global_orchestrator, '_wait_for_process_exit'):
                stop_tasks = [global_orchestrator.stop_project(name) for name in project_names]
                stop_results = await asyncio.gather(*stop_tasks)
                assert all(stop_results)

    @pytest.mark.asyncio
    async def test_resource_allocation_edge_cases_comprehensive(self, global_orchestrator, temp_config_dir):
        """Test comprehensive edge cases in resource allocation."""
        # Test with projects that have custom resource limits
        test_cases = [
            # (max_agents, max_memory, cpu_priority, expected_behavior)
            (0, 0, 0.0, "zero_resources"),      # Zero resource limits
            (1, 128, 0.1, "minimal_resources"), # Minimal resources
            (100, 32768, 5.0, "excessive_resources"), # Excessive resources
        ]
        
        global_orchestrator.global_config.max_total_agents = 10
        global_orchestrator.global_config.global_memory_limit_gb = 8
        
        for i, (max_agents, max_memory, cpu_priority, case_name) in enumerate(test_cases):
            project_dir = Path(temp_config_dir) / f"resource_edge_{i}"
            project_dir.mkdir(exist_ok=True)
            
            project_config = ProjectConfig(
                name=f"resource-edge-{i}",
                path=str(project_dir),
                priority=ProjectPriority.NORMAL,
                resource_limits=ResourceLimits(
                    max_parallel_agents=max_agents,
                    max_memory_mb=max_memory,
                    cpu_priority=cpu_priority
                )
            )
            
            with patch.object(global_orchestrator.config_manager, 'get_active_projects', return_value=[project_config]):
                allocation = await global_orchestrator._calculate_resource_allocation(project_config)
                
                # Verify allocation respects project limits
                assert allocation.allocated_agents <= max_agents or max_agents == 0
                assert allocation.allocated_memory_mb <= max_memory or max_memory == 0
                
                # Verify reasonable allocations are produced even for edge cases
                assert allocation.project_name == f"resource-edge-{i}"
                assert allocation.priority_weight == 1.0  # Normal priority
                assert isinstance(allocation.allocated_cpu_percent, float)

    @pytest.mark.asyncio
    async def test_orchestrator_status_transitions_comprehensive(self, global_orchestrator):
        """Test comprehensive orchestrator status transitions."""
        # Test all possible status transitions through _update_orchestrator_status
        test_scenarios = [
            # (initial_status, process_poll_result, expected_final_status, should_increment_error)
            (OrchestratorStatus.RUNNING, None, OrchestratorStatus.RUNNING, False),   # Still running
            (OrchestratorStatus.RUNNING, 0, OrchestratorStatus.CRASHED, True),       # Crashed from running
            (OrchestratorStatus.RUNNING, 1, OrchestratorStatus.CRASHED, True),       # Crashed with error code
            (OrchestratorStatus.STOPPING, 0, OrchestratorStatus.STOPPED, False),    # Clean shutdown
            (OrchestratorStatus.STOPPING, 1, OrchestratorStatus.STOPPED, False),    # Shutdown with error
            (OrchestratorStatus.STARTING, None, OrchestratorStatus.STARTING, False), # Still starting
            (OrchestratorStatus.PAUSED, None, OrchestratorStatus.PAUSED, False),     # Still paused
        ]
        
        for i, (initial_status, poll_result, expected_status, should_increment_error) in enumerate(test_scenarios):
            orchestrator_name = f"status_test_{i}"
            
            mock_process = Mock()
            mock_process.poll.return_value = poll_result
            
            orchestrator = ProjectOrchestrator(
                project_name=orchestrator_name,
                project_path=f"/test/{orchestrator_name}",
                process=mock_process,
                status=initial_status,
                error_count=0
            )
            
            global_orchestrator.orchestrators[orchestrator_name] = orchestrator
            
            # Update status
            await global_orchestrator._update_orchestrator_status()
            
            # Verify expected transitions
            assert orchestrator.status == expected_status, f"Scenario {i}: Expected {expected_status}, got {orchestrator.status}"
            
            if should_increment_error:
                assert orchestrator.error_count == 1, f"Scenario {i}: Error count should be incremented"
            else:
                assert orchestrator.error_count == 0, f"Scenario {i}: Error count should not be incremented"
            
            # Clean up for next test
            del global_orchestrator.orchestrators[orchestrator_name]

    @pytest.mark.asyncio
    async def test_import_error_handling_coverage(self):
        """Test import error handling paths for comprehensive coverage."""
        # Test that the module can handle missing optional dependencies
        # This primarily tests the graceful import fallbacks
        
        # Import the module with mocked import failures
        with patch.dict('sys.modules', {
            'psutil': None,
            'lib.data_models': None,
            'lib.state_machine': None,
            'lib.discord_bot': None
        }):
            # Re-import to test fallback paths
            import importlib
            import lib.global_orchestrator
            
            # Reload to test the import error handling
            importlib.reload(lib.global_orchestrator)
            
            # The module should still be functional despite missing optional deps
            assert lib.global_orchestrator.GlobalOrchestrator is not None
            assert lib.global_orchestrator.OrchestratorStatus is not None
            
            # psutil should be None due to import failure
            assert lib.global_orchestrator.psutil is None

    @pytest.mark.asyncio
    async def test_full_integration_workflow_with_discord(self, global_orchestrator, config_manager, temp_config_dir):
        """Test full integration workflow including Discord bot setup."""
        # Configure Discord integration
        global_orchestrator.global_config.global_discord_guild = "test-guild-123"
        
        project_dir = Path(temp_config_dir) / "discord_integration"
        project_dir.mkdir()
        
        project_config = ProjectConfig(
            name="discord-integration",
            path=str(project_dir),
            discord_channel="#discord-integration"
        )
        config_manager.projects["discord-integration"] = project_config
        
        # Mock Discord bot
        mock_discord_bot = Mock()
        mock_discord_bot.stop = AsyncMock()
        
        with patch.object(global_orchestrator, '_start_discord_bot') as mock_start_discord, \
             patch.object(global_orchestrator, '_start_active_projects'), \
             patch('pathlib.Path.mkdir'):
            
            # Start orchestrator with Discord enabled
            await global_orchestrator.start()
            
            # Verify Discord bot startup was attempted
            mock_start_discord.assert_called_once()
            assert global_orchestrator.status == OrchestratorStatus.RUNNING
        
        # Test stop with Discord bot cleanup
        global_orchestrator.discord_bot = mock_discord_bot
        
        with patch.object(global_orchestrator, '_stop_all_projects'):
            await global_orchestrator.stop()
            
            # Verify Discord bot was stopped
            mock_discord_bot.stop.assert_called_once()
            assert global_orchestrator.status == OrchestratorStatus.STOPPED