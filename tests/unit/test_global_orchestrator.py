"""
Unit tests for Global Orchestrator.

Tests the global orchestrator system that manages multiple project orchestrators,
resource allocation, and cross-project coordination.
"""

import pytest
import asyncio
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.global_orchestrator import (
    GlobalOrchestrator, OrchestratorStatus, ProjectOrchestrator,
    ResourceAllocation, GlobalMetrics
)
from lib.multi_project_config import (
    MultiProjectConfigManager, ProjectConfig, ProjectPriority, ProjectStatus
)


class TestProjectOrchestrator:
    """Test the ProjectOrchestrator dataclass."""
    
    def test_project_orchestrator_creation(self):
        """Test creating a ProjectOrchestrator instance."""
        now = datetime.utcnow()
        
        orchestrator = ProjectOrchestrator(
            project_name="test-project",
            project_path="/path/to/project",
            status=OrchestratorStatus.RUNNING,
            pid=12345,
            start_time=now
        )
        
        assert orchestrator.project_name == "test-project"
        assert orchestrator.project_path == "/path/to/project"
        assert orchestrator.status == OrchestratorStatus.RUNNING
        assert orchestrator.pid == 12345
        assert orchestrator.start_time == now

    def test_project_orchestrator_defaults(self):
        """Test ProjectOrchestrator with default values."""
        orchestrator = ProjectOrchestrator(
            project_name="default-test",
            project_path="/path/to/project"
        )
        
        assert orchestrator.project_name == "default-test"
        assert orchestrator.status == OrchestratorStatus.STOPPED
        assert orchestrator.process is None
        assert orchestrator.cpu_usage == 0.0
        assert orchestrator.memory_usage == 0.0
        assert orchestrator.active_agents == 0


class TestResourceAllocation:
    """Test the ResourceAllocation dataclass."""
    
    def test_resource_allocation_creation(self):
        """Test creating a ResourceAllocation instance."""
        allocation = ResourceAllocation(
            project_name="test-project",
            allocated_agents=5,
            allocated_memory_mb=2048,
            allocated_cpu_percent=25.0,
            priority_weight=1.5
        )
        
        assert allocation.project_name == "test-project"
        assert allocation.allocated_agents == 5
        assert allocation.allocated_memory_mb == 2048
        assert allocation.allocated_cpu_percent == 25.0
        assert allocation.priority_weight == 1.5
        assert allocation.usage_history == []


class TestGlobalMetrics:
    """Test the GlobalMetrics dataclass."""
    
    def test_global_metrics_creation(self):
        """Test creating GlobalMetrics with custom values."""
        metrics = GlobalMetrics(
            total_projects=5,
            active_projects=3,
            total_agents=12,
            total_memory_usage_mb=4096.0,
            total_cpu_usage_percent=65.5
        )
        
        assert metrics.total_projects == 5
        assert metrics.active_projects == 3
        assert metrics.total_agents == 12
        assert metrics.total_memory_usage_mb == 4096.0
        assert metrics.total_cpu_usage_percent == 65.5

    def test_global_metrics_defaults(self):
        """Test GlobalMetrics with default values."""
        metrics = GlobalMetrics()
        
        assert metrics.total_projects == 0
        assert metrics.active_projects == 0
        assert metrics.total_agents == 0
        assert metrics.resource_efficiency == 0.0


class TestOrchestratorStatus:
    """Test OrchestratorStatus enum."""
    
    def test_orchestrator_status_values(self):
        """Test OrchestratorStatus enum values."""
        assert OrchestratorStatus.STOPPED.value == "stopped"
        assert OrchestratorStatus.STARTING.value == "starting"
        assert OrchestratorStatus.RUNNING.value == "running"
        assert OrchestratorStatus.PAUSING.value == "pausing"
        assert OrchestratorStatus.PAUSED.value == "paused"
        assert OrchestratorStatus.STOPPING.value == "stopping"
        assert OrchestratorStatus.ERROR.value == "error"
        assert OrchestratorStatus.CRASHED.value == "crashed"


class TestGlobalOrchestrator:
    """Test the GlobalOrchestrator class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for configuration testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
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
    def sample_project_config(self, temp_config_dir):
        """Create a sample project configuration."""
        project_dir = Path(temp_config_dir) / "sample_project"
        project_dir.mkdir(parents=True)
        
        return ProjectConfig(
            name="sample-project",
            path=str(project_dir),
            priority=ProjectPriority.NORMAL,
            status=ProjectStatus.ACTIVE
        )

    def test_global_orchestrator_init(self, global_orchestrator, config_manager):
        """Test GlobalOrchestrator initialization."""
        assert global_orchestrator.config_manager == config_manager
        assert global_orchestrator.global_config == config_manager.global_config
        assert global_orchestrator.status == OrchestratorStatus.STOPPED
        assert global_orchestrator.orchestrators == {}
        assert global_orchestrator.resource_allocations == {}
        assert isinstance(global_orchestrator.metrics, GlobalMetrics)

    @pytest.mark.asyncio
    async def test_start_global_orchestrator(self, global_orchestrator):
        """Test starting the global orchestrator."""
        with patch.object(global_orchestrator, '_start_active_projects') as mock_start_projects:
            mock_start_projects.return_value = asyncio.Future()
            mock_start_projects.return_value.set_result(None)
            
            await global_orchestrator.start()
            
            assert global_orchestrator.status == OrchestratorStatus.RUNNING
            assert global_orchestrator.start_time is not None
            mock_start_projects.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_global_orchestrator(self, global_orchestrator):
        """Test stopping the global orchestrator."""
        # Set up as running
        global_orchestrator.status = OrchestratorStatus.RUNNING
        
        with patch.object(global_orchestrator, '_stop_all_projects') as mock_stop_projects:
            mock_stop_projects.return_value = asyncio.Future()
            mock_stop_projects.return_value.set_result(None)
            
            await global_orchestrator.stop()
            
            assert global_orchestrator.status == OrchestratorStatus.STOPPED
            mock_stop_projects.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_resource_allocation_fair_share(self, global_orchestrator, sample_project_config):
        """Test fair share resource allocation calculation."""
        # Set up global config for fair share
        global_orchestrator.global_config.resource_allocation_strategy = "fair_share"
        global_orchestrator.global_config.max_total_agents = 10
        global_orchestrator.global_config.global_memory_limit_gb = 8
        
        # Mock get_active_projects to return one project
        with patch.object(global_orchestrator.config_manager, 'get_active_projects') as mock_active:
            mock_active.return_value = [sample_project_config]
            
            allocation = await global_orchestrator._calculate_resource_allocation(sample_project_config)
            
            assert allocation.project_name == "sample-project"
            assert allocation.allocated_agents == 10  # All agents since only one project
            assert allocation.allocated_memory_mb == 8192  # 8GB in MB
            assert allocation.priority_weight == 1.0  # Normal priority

    @pytest.mark.asyncio
    async def test_calculate_resource_allocation_priority_based(self, global_orchestrator, sample_project_config):
        """Test priority-based resource allocation calculation."""
        # Set up global config for priority-based allocation
        global_orchestrator.global_config.resource_allocation_strategy = "priority_based"
        global_orchestrator.global_config.max_total_agents = 10
        global_orchestrator.global_config.global_memory_limit_gb = 8
        
        # Create high priority project
        high_priority_config = ProjectConfig(
            name="high-priority",
            path="/path/to/high",
            priority=ProjectPriority.HIGH
        )
        
        # Mock get_active_projects
        with patch.object(global_orchestrator.config_manager, 'get_active_projects') as mock_active:
            mock_active.return_value = [sample_project_config, high_priority_config]
            
            allocation = await global_orchestrator._calculate_resource_allocation(high_priority_config)
            
            assert allocation.project_name == "high-priority"
            assert allocation.priority_weight == 1.5  # High priority weight
            assert allocation.allocated_agents > 3  # Should get more than normal priority

    @pytest.mark.asyncio
    async def test_prepare_orchestrator_command(self, global_orchestrator, sample_project_config):
        """Test preparing orchestrator command."""
        allocation = ResourceAllocation(
            project_name="test-project",
            allocated_agents=5,
            allocated_memory_mb=2048,
            allocated_cpu_percent=25.0,
            priority_weight=1.0
        )
        
        command = await global_orchestrator._prepare_orchestrator_command(
            sample_project_config, allocation
        )
        
        expected_command = [
            "python3", "scripts/orchestrator.py",
            "--project-mode",
            "--max-agents", "5",
            "--memory-limit", "2048",
            "--project-name", "sample-project"
        ]
        
        assert command == expected_command

    @pytest.mark.asyncio
    async def test_prepare_project_environment(self, global_orchestrator, sample_project_config):
        """Test preparing project environment variables."""
        allocation = ResourceAllocation(
            project_name="test-project",
            allocated_agents=3,
            allocated_memory_mb=1024,
            allocated_cpu_percent=20.0,
            priority_weight=1.0
        )
        
        env = await global_orchestrator._prepare_project_environment(
            sample_project_config, allocation
        )
        
        assert env["ORCH_PROJECT_NAME"] == "sample-project"
        assert env["ORCH_PROJECT_PATH"] == sample_project_config.path
        assert env["ORCH_MAX_AGENTS"] == "3"
        assert env["ORCH_MEMORY_LIMIT"] == "1024"
        assert env["ORCH_CPU_LIMIT"] == "20.0"
        assert env["ORCH_GLOBAL_MODE"] == "true"

    @pytest.mark.asyncio
    async def test_start_project_success(self, global_orchestrator, config_manager, sample_project_config):
        """Test successfully starting a project."""
        # Register the project
        config_manager.projects["sample-project"] = sample_project_config
        
        with patch('subprocess.Popen') as mock_popen:
            # Mock successful process
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process
            
            success = await global_orchestrator.start_project("sample-project")
            
            assert success
            assert "sample-project" in global_orchestrator.orchestrators
            
            orchestrator = global_orchestrator.orchestrators["sample-project"]
            assert orchestrator.status == OrchestratorStatus.RUNNING
            assert orchestrator.pid == 12345

    @pytest.mark.asyncio
    async def test_start_project_not_found(self, global_orchestrator):
        """Test starting a project that doesn't exist."""
        success = await global_orchestrator.start_project("nonexistent")
        
        assert not success
        assert "nonexistent" not in global_orchestrator.orchestrators

    @pytest.mark.asyncio
    async def test_start_project_already_running(self, global_orchestrator, config_manager, sample_project_config):
        """Test starting a project that's already running."""
        # Register and set up running project
        config_manager.projects["running-project"] = sample_project_config
        global_orchestrator.orchestrators["running-project"] = ProjectOrchestrator(
            project_name="running-project",
            project_path=sample_project_config.path,
            status=OrchestratorStatus.RUNNING
        )
        
        success = await global_orchestrator.start_project("running-project")
        
        assert success  # Should return True for already running

    @pytest.mark.asyncio
    async def test_stop_project_success(self, global_orchestrator):
        """Test successfully stopping a project."""
        # Set up running project
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running
        mock_process.terminate = Mock()
        
        orchestrator = ProjectOrchestrator(
            project_name="running-project",
            project_path="/path/to/project",
            process=mock_process,
            status=OrchestratorStatus.RUNNING,
            pid=12345
        )
        global_orchestrator.orchestrators["running-project"] = orchestrator
        
        with patch.object(global_orchestrator, '_wait_for_process_exit') as mock_wait:
            mock_wait.return_value = asyncio.Future()
            mock_wait.return_value.set_result(None)
            
            success = await global_orchestrator.stop_project("running-project")
            
            assert success
            assert orchestrator.status == OrchestratorStatus.STOPPED
            mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_project_not_running(self, global_orchestrator):
        """Test stopping a project that's not running."""
        success = await global_orchestrator.stop_project("not-running")
        
        assert success  # Should return True for not running

    @pytest.mark.asyncio
    async def test_pause_project(self, global_orchestrator):
        """Test pausing a running project."""
        # Set up running project
        orchestrator = ProjectOrchestrator(
            project_name="pause-test",
            project_path="/path/to/project",
            status=OrchestratorStatus.RUNNING,
            pid=12345
        )
        global_orchestrator.orchestrators["pause-test"] = orchestrator
        
        with patch('os.kill') as mock_kill:
            success = await global_orchestrator.pause_project("pause-test")
            
            assert success
            assert orchestrator.status == OrchestratorStatus.PAUSED
            mock_kill.assert_called_once_with(12345, 19)  # SIGSTOP = 19

    @pytest.mark.asyncio
    async def test_resume_project(self, global_orchestrator):
        """Test resuming a paused project."""
        # Set up paused project
        orchestrator = ProjectOrchestrator(
            project_name="resume-test",
            project_path="/path/to/project",
            status=OrchestratorStatus.PAUSED,
            pid=12345
        )
        global_orchestrator.orchestrators["resume-test"] = orchestrator
        
        with patch('os.kill') as mock_kill:
            success = await global_orchestrator.resume_project("resume-test")
            
            assert success
            assert orchestrator.status == OrchestratorStatus.RUNNING
            mock_kill.assert_called_once_with(12345, 18)  # SIGCONT = 18

    @pytest.mark.asyncio
    async def test_get_global_status(self, global_orchestrator):
        """Test getting global orchestration status."""
        # Set up some test data
        global_orchestrator.status = OrchestratorStatus.RUNNING
        global_orchestrator.start_time = datetime.utcnow()
        
        # Add a mock orchestrator
        orchestrator = ProjectOrchestrator(
            project_name="status-test",
            project_path="/path/to/project",
            status=OrchestratorStatus.RUNNING,
            pid=12345,
            start_time=datetime.utcnow(),
            cpu_usage=25.5,
            memory_usage=512.0,
            active_agents=3
        )
        global_orchestrator.orchestrators["status-test"] = orchestrator
        
        # Add resource allocation
        allocation = ResourceAllocation(
            project_name="status-test",
            allocated_agents=3,
            allocated_memory_mb=1024,
            allocated_cpu_percent=30.0,
            priority_weight=1.0
        )
        global_orchestrator.resource_allocations["status-test"] = allocation
        
        with patch.object(global_orchestrator, '_update_metrics') as mock_update:
            mock_update.return_value = asyncio.Future()
            mock_update.return_value.set_result(None)
            
            status = await global_orchestrator.get_global_status()
            
            assert "global_orchestrator" in status
            assert status["global_orchestrator"]["status"] == "running"
            
            assert "projects" in status
            assert "status-test" in status["projects"]
            assert status["projects"]["status-test"]["status"] == "running"
            assert status["projects"]["status-test"]["cpu_usage"] == 25.5
            
            assert "resource_allocations" in status
            assert "status-test" in status["resource_allocations"]
            assert status["resource_allocations"]["status-test"]["allocated_agents"] == 3

    @pytest.mark.asyncio
    async def test_update_orchestrator_status_crashed(self, global_orchestrator):
        """Test updating status when process has crashed."""
        # Set up orchestrator with crashed process
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process exited with error
        
        orchestrator = ProjectOrchestrator(
            project_name="crash-test",
            project_path="/path/to/project",
            process=mock_process,
            status=OrchestratorStatus.RUNNING
        )
        global_orchestrator.orchestrators["crash-test"] = orchestrator
        
        await global_orchestrator._update_orchestrator_status()
        
        assert orchestrator.status == OrchestratorStatus.CRASHED
        assert orchestrator.error_count == 1

    @pytest.mark.asyncio
    async def test_update_orchestrator_status_with_psutil(self, global_orchestrator):
        """Test updating status with psutil available."""
        # Set up orchestrator with running process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process still running
        
        orchestrator = ProjectOrchestrator(
            project_name="psutil-test",
            project_path="/path/to/project",
            process=mock_process,
            status=OrchestratorStatus.RUNNING,
            pid=12345
        )
        global_orchestrator.orchestrators["psutil-test"] = orchestrator
        
        # Mock psutil process
        mock_psutil_process = Mock()
        mock_psutil_process.cpu_percent.return_value = 45.5
        mock_psutil_process.memory_info.return_value.rss = 1024 * 1024 * 512  # 512MB
        
        with patch('lib.global_orchestrator.psutil') as mock_psutil:
            mock_psutil.Process.return_value = mock_psutil_process
            
            await global_orchestrator._update_orchestrator_status()
            
            assert orchestrator.cpu_usage == 45.5
            assert orchestrator.memory_usage == 512.0
            assert orchestrator.last_heartbeat is not None

    @pytest.mark.asyncio
    async def test_collect_metrics(self, global_orchestrator, config_manager):
        """Test collecting global metrics."""
        # Set up test data
        config_manager.projects = {
            "project1": Mock(),
            "project2": Mock(),
            "project3": Mock()
        }
        
        # Add running orchestrators
        global_orchestrator.orchestrators = {
            "project1": ProjectOrchestrator("project1", "/path1", status=OrchestratorStatus.RUNNING, active_agents=2, memory_usage=256.0, cpu_usage=25.0),
            "project2": ProjectOrchestrator("project2", "/path2", status=OrchestratorStatus.RUNNING, active_agents=3, memory_usage=512.0, cpu_usage=35.0),
            "project3": ProjectOrchestrator("project3", "/path3", status=OrchestratorStatus.STOPPED, active_agents=0, memory_usage=0.0, cpu_usage=0.0)
        }
        
        await global_orchestrator._collect_metrics()
        
        metrics = global_orchestrator.metrics
        assert metrics.total_projects == 3
        assert metrics.active_projects == 2  # Only running projects
        assert metrics.total_agents == 5  # 2 + 3 + 0
        assert metrics.total_memory_usage_mb == 768.0  # 256 + 512 + 0
        assert metrics.total_cpu_usage_percent == 60.0  # 25 + 35 + 0

    @pytest.mark.asyncio
    async def test_restart_failed_orchestrators(self, global_orchestrator, config_manager, sample_project_config):
        """Test restarting failed orchestrators."""
        # Set up crashed orchestrator
        config_manager.projects["crashed-project"] = sample_project_config
        crashed_orchestrator = ProjectOrchestrator(
            project_name="crashed-project",
            project_path="/path/to/project",
            status=OrchestratorStatus.CRASHED,
            restart_count=0
        )
        global_orchestrator.orchestrators["crashed-project"] = crashed_orchestrator
        
        with patch.object(global_orchestrator, 'stop_project') as mock_stop, \
             patch.object(global_orchestrator, 'start_project') as mock_start:
            
            mock_stop.return_value = asyncio.Future()
            mock_stop.return_value.set_result(True)
            mock_start.return_value = asyncio.Future()
            mock_start.return_value.set_result(True)
            
            await global_orchestrator._restart_failed_orchestrators()
            
            assert crashed_orchestrator.restart_count == 1
            mock_stop.assert_called_once_with("crashed-project")
            mock_start.assert_called_once_with("crashed-project")

    @pytest.mark.asyncio
    async def test_restart_failed_orchestrators_max_attempts(self, global_orchestrator):
        """Test that orchestrators aren't restarted after max attempts."""
        # Set up orchestrator that has reached max restart attempts
        crashed_orchestrator = ProjectOrchestrator(
            project_name="max-restarts",
            project_path="/path/to/project",
            status=OrchestratorStatus.CRASHED,
            restart_count=3  # Max attempts reached
        )
        global_orchestrator.orchestrators["max-restarts"] = crashed_orchestrator
        
        with patch.object(global_orchestrator, 'stop_project') as mock_stop, \
             patch.object(global_orchestrator, 'start_project') as mock_start:
            
            await global_orchestrator._restart_failed_orchestrators()
            
            # Should not attempt restart
            mock_stop.assert_not_called()
            mock_start.assert_not_called()
            assert crashed_orchestrator.restart_count == 3