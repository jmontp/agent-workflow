"""
Unit tests for Orchestrator.

Tests the unified orchestrator system that manages both single-project
and multi-project workflows, including resource allocation, HITL approval
gates, and coordination of specialized AI agents.
"""

import pytest
import asyncio
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
import json

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent_workflow.core.orchestrator import (
    GlobalOrchestrator, OrchestratorStatus, ProjectOrchestrator,
    ResourceAllocation, GlobalMetrics, OrchestrationMode, ProjectPriority,
    ResourceLimits, ProjectConfig, Project
)
from agent_workflow.core.models import Epic, Story, Sprint, EpicStatus, StoryStatus, SprintStatus, ProjectData
from agent_workflow.core.state_machine import StateMachine


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


class TestOrchestrationMode:
    """Test OrchestrationMode enum."""
    
    def test_orchestration_mode_values(self):
        """Test OrchestrationMode enum values."""
        assert OrchestrationMode.BLOCKING.value == "blocking"
        assert OrchestrationMode.PARTIAL.value == "partial"
        assert OrchestrationMode.AUTONOMOUS.value == "autonomous"
        assert OrchestrationMode.COLLABORATIVE.value == "collaborative"


class TestProjectPriority:
    """Test ProjectPriority enum."""
    
    def test_project_priority_values(self):
        """Test ProjectPriority enum values."""
        assert ProjectPriority.CRITICAL.value == "critical"
        assert ProjectPriority.HIGH.value == "high"
        assert ProjectPriority.NORMAL.value == "normal"
        assert ProjectPriority.LOW.value == "low"


class TestResourceLimits:
    """Test ResourceLimits dataclass."""
    
    def test_resource_limits_defaults(self):
        """Test ResourceLimits with default values."""
        limits = ResourceLimits()
        
        assert limits.max_parallel_agents == 3
        assert limits.max_memory_mb == 2048
        assert limits.cpu_priority == 1.0

    def test_resource_limits_custom(self):
        """Test ResourceLimits with custom values."""
        limits = ResourceLimits(
            max_parallel_agents=10,
            max_memory_mb=4096,
            cpu_priority=2.0
        )
        
        assert limits.max_parallel_agents == 10
        assert limits.max_memory_mb == 4096
        assert limits.cpu_priority == 2.0


class TestProjectConfig:
    """Test ProjectConfig dataclass."""
    
    def test_project_config_creation(self):
        """Test creating a ProjectConfig instance."""
        config = ProjectConfig(
            name="test-project",
            path="/path/to/project",
            orchestration_mode=OrchestrationMode.AUTONOMOUS,
            priority=ProjectPriority.HIGH,
            discord_channel="#test-channel"
        )
        
        assert config.name == "test-project"
        assert config.path == "/path/to/project"
        assert config.orchestration_mode == OrchestrationMode.AUTONOMOUS
        assert config.priority == ProjectPriority.HIGH
        assert config.discord_channel == "#test-channel"
        assert isinstance(config.resource_limits, ResourceLimits)

    def test_project_config_defaults(self):
        """Test ProjectConfig with default values."""
        config = ProjectConfig(name="default-project", path="/default/path")
        
        assert config.orchestration_mode == OrchestrationMode.BLOCKING
        assert config.priority == ProjectPriority.NORMAL
        assert config.discord_channel is None
        assert isinstance(config.resource_limits, ResourceLimits)


class TestProject:
    """Test Project dataclass."""
    
    @pytest.fixture
    def mock_state_machine(self):
        """Create a mock state machine."""
        return Mock(spec=StateMachine)

    @pytest.fixture
    def mock_tdd_state_machine(self):
        """Create a mock TDD state machine."""
        return Mock()

    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage."""
        return Mock()

    def test_project_creation(self, mock_state_machine, mock_tdd_state_machine, mock_storage):
        """Test creating a Project instance."""
        project = Project(
            name="test-project",
            path=Path("/path/to/project"),
            orchestration_mode=OrchestrationMode.BLOCKING,
            priority=ProjectPriority.HIGH,
            state_machine=mock_state_machine,
            tdd_state_machine=mock_tdd_state_machine,
            active_tasks=[],
            pending_approvals=["approval-1"],
            storage=mock_storage,
            discord_channel="#test-channel"
        )
        
        assert project.name == "test-project"
        assert project.path == Path("/path/to/project")
        assert project.orchestration_mode == OrchestrationMode.BLOCKING
        assert project.priority == ProjectPriority.HIGH
        assert project.active_tasks == []
        assert project.pending_approvals == ["approval-1"]
        assert project.discord_channel == "#test-channel"

    def test_project_to_dict(self, mock_state_machine, mock_tdd_state_machine, mock_storage):
        """Test converting Project to dictionary."""
        project = Project(
            name="dict-test",
            path=Path("/dict/path"),
            orchestration_mode=OrchestrationMode.AUTONOMOUS,
            priority=ProjectPriority.NORMAL,
            state_machine=mock_state_machine,
            tdd_state_machine=mock_tdd_state_machine,
            active_tasks=[],
            pending_approvals=[],
            storage=mock_storage
        )
        
        project_dict = project.to_dict()
        
        assert project_dict["name"] == "dict-test"
        assert project_dict["path"] == "/dict/path"
        assert project_dict["orchestration_mode"] == "autonomous"
        assert project_dict["priority"] == "normal"
        assert "active_tasks" in project_dict
        assert "pending_approvals" in project_dict


class TestGlobalOrchestrator:
    """Test the GlobalOrchestrator class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for configuration testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager."""
        config_manager = Mock()
        config_manager.global_config = Mock()
        config_manager.global_config.resource_allocation_strategy = "fair_share"
        config_manager.global_config.max_total_agents = 10
        config_manager.global_config.global_memory_limit_gb = 8
        config_manager.projects = {}
        return config_manager
    
    @pytest.fixture
    def global_orchestrator(self, mock_config_manager):
        """Create a GlobalOrchestrator instance."""
        return GlobalOrchestrator(mock_config_manager)
    
    @pytest.fixture
    def sample_project_config(self, temp_config_dir):
        """Create a sample project configuration."""
        project_dir = Path(temp_config_dir) / "sample_project"
        project_dir.mkdir(parents=True)
        
        return ProjectConfig(
            name="sample-project",
            path=str(project_dir),
            priority=ProjectPriority.NORMAL
        )

    def test_global_orchestrator_init(self, global_orchestrator, mock_config_manager):
        """Test GlobalOrchestrator initialization."""
        assert global_orchestrator.config_manager == mock_config_manager
        assert global_orchestrator.global_config == mock_config_manager.global_config
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
            # Note: allocation is limited by project resource limits (max_parallel_agents=3)
            assert allocation.allocated_agents == 3  # Limited by project config
            assert allocation.allocated_memory_mb == 1024  # Limited by project config
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
            # Note: allocation is still limited by project resource limits
            assert allocation.allocated_agents <= 3  # Limited by project config
            assert allocation.priority_weight == 1.5  # High priority weight

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
    async def test_start_project_success(self, global_orchestrator, mock_config_manager, sample_project_config):
        """Test successfully starting a project."""
        # Register the project
        mock_config_manager.projects["sample-project"] = sample_project_config
        
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
    async def test_start_project_already_running(self, global_orchestrator, mock_config_manager, sample_project_config):
        """Test starting a project that's already running."""
        # Register and set up running project
        mock_config_manager.projects["running-project"] = sample_project_config
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
        # Set up running project with both process and pid
        mock_process = Mock()
        orchestrator = ProjectOrchestrator(
            project_name="pause-test",
            project_path="/path/to/project",
            process=mock_process,
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
        # Set up paused project with both process and pid
        mock_process = Mock()
        orchestrator = ProjectOrchestrator(
            project_name="resume-test",
            project_path="/path/to/project",
            process=mock_process,
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
    async def test_get_project_status(self, global_orchestrator):
        """Test getting project status."""
        # Set up test project
        orchestrator = ProjectOrchestrator(
            project_name="status-test",
            project_path="/path/to/project",
            status=OrchestratorStatus.RUNNING,
            pid=12345,
            cpu_usage=25.5,
            memory_usage=1024.0,
            active_agents=3
        )
        global_orchestrator.orchestrators["status-test"] = orchestrator
        
        status = global_orchestrator.get_project_status("status-test")
        
        assert status["name"] == "status-test"
        assert status["status"] == "running"
        assert status["pid"] == 12345
        assert status["cpu_usage"] == 25.5
        assert status["memory_usage"] == 1024.0
        assert status["active_agents"] == 3

    def test_get_project_status_not_found(self, global_orchestrator):
        """Test getting status for non-existent project."""
        status = global_orchestrator.get_project_status("nonexistent")
        
        assert status is None

    def test_get_global_status(self, global_orchestrator):
        """Test getting global orchestrator status."""
        # Set up some test projects
        global_orchestrator.orchestrators["project1"] = ProjectOrchestrator(
            project_name="project1",
            project_path="/path1",
            status=OrchestratorStatus.RUNNING,
            cpu_usage=20.0,
            memory_usage=512.0,
            active_agents=2
        )
        global_orchestrator.orchestrators["project2"] = ProjectOrchestrator(
            project_name="project2",
            project_path="/path2",
            status=OrchestratorStatus.PAUSED,
            cpu_usage=15.0,
            memory_usage=768.0,
            active_agents=1
        )
        
        status = global_orchestrator.get_global_status()
        
        assert status["status"] == "stopped"  # Global orchestrator status
        assert status["total_projects"] == 2
        assert status["running_projects"] == 1
        assert status["paused_projects"] == 1
        assert status["total_cpu_usage"] == 35.0
        assert status["total_memory_usage"] == 1280.0
        assert status["total_active_agents"] == 3

    @pytest.mark.asyncio
    async def test_update_metrics(self, global_orchestrator):
        """Test updating global metrics."""
        # Set up test projects
        global_orchestrator.orchestrators["active1"] = ProjectOrchestrator(
            project_name="active1",
            project_path="/path1",
            status=OrchestratorStatus.RUNNING,
            cpu_usage=25.0,
            memory_usage=1024.0,
            active_agents=3
        )
        global_orchestrator.orchestrators["stopped1"] = ProjectOrchestrator(
            project_name="stopped1",
            project_path="/path2",
            status=OrchestratorStatus.STOPPED,
            cpu_usage=0.0,
            memory_usage=0.0,
            active_agents=0
        )
        
        await global_orchestrator._update_metrics()
        
        metrics = global_orchestrator.metrics
        assert metrics.total_projects == 2
        assert metrics.active_projects == 1
        assert metrics.total_agents == 3
        assert metrics.total_memory_usage_mb == 1024.0
        assert metrics.total_cpu_usage_percent == 25.0

    @pytest.mark.asyncio 
    async def test_monitor_projects(self, global_orchestrator):
        """Test project monitoring loop."""
        # Set up a crashed project
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process exited with error
        
        orchestrator = ProjectOrchestrator(
            project_name="crashed-project",
            project_path="/path/to/project",
            process=mock_process,
            status=OrchestratorStatus.RUNNING,
            pid=12345
        )
        global_orchestrator.orchestrators["crashed-project"] = orchestrator
        
        # Mock restart functionality
        with patch.object(global_orchestrator, 'start_project') as mock_restart:
            mock_restart.return_value = asyncio.Future()
            mock_restart.return_value.set_result(True)
            
            await global_orchestrator._monitor_projects()
            
            # Check that crashed project was detected and restarted
            assert orchestrator.status == OrchestratorStatus.CRASHED
            mock_restart.assert_called_once_with("crashed-project")

    def test_priority_weights(self, global_orchestrator):
        """Test priority weight calculations."""
        priorities = [
            (ProjectPriority.CRITICAL, 2.0),
            (ProjectPriority.HIGH, 1.5),
            (ProjectPriority.NORMAL, 1.0),
            (ProjectPriority.LOW, 0.5)
        ]
        
        for priority, expected_weight in priorities:
            weight = global_orchestrator._get_priority_weight(priority)
            assert weight == expected_weight

    def test_resource_allocation_fairness(self, global_orchestrator):
        """Test resource allocation fairness across projects."""
        # Create multiple projects with different priorities
        projects = [
            ProjectConfig(name="critical", path="/critical", priority=ProjectPriority.CRITICAL),
            ProjectConfig(name="high", path="/high", priority=ProjectPriority.HIGH),
            ProjectConfig(name="normal", path="/normal", priority=ProjectPriority.NORMAL),
            ProjectConfig(name="low", path="/low", priority=ProjectPriority.LOW)
        ]
        
        # Test that resource allocation respects priority ordering
        allocations = []
        for project in projects:
            weight = global_orchestrator._get_priority_weight(project.priority)
            allocations.append((project.name, weight))
        
        # Sort by weight descending
        allocations.sort(key=lambda x: x[1], reverse=True)
        
        assert allocations[0][0] == "critical"  # Highest priority first
        assert allocations[1][0] == "high"
        assert allocations[2][0] == "normal" 
        assert allocations[3][0] == "low"      # Lowest priority last


class TestSingleProjectOrchestrator:
    """Test single-project orchestrator functionality."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        # Create .git directory to make it look like a valid project
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def project_config(self, temp_project_dir):
        """Create project configuration."""
        return {
            "project_path": temp_project_dir,
            "orchestration_mode": "blocking",
            "discord_channel": "#test-channel"
        }

    def test_project_initialization(self, temp_project_dir, project_config):
        """Test project initialization."""
        from agent_workflow.core.orchestrator import initialize_project
        
        with patch('agent_workflow.core.storage.ProjectStorage') as mock_storage_class:
            mock_storage = Mock()
            mock_storage.initialize_project.return_value = True
            mock_storage.is_initialized.return_value = True
            mock_storage_class.return_value = mock_storage
            
            result = initialize_project(project_config["project_path"])
            
            assert result is True
            mock_storage.initialize_project.assert_called_once()

    def test_hitl_command_processing(self, project_config):
        """Test HITL command processing."""
        from agent_workflow.core.orchestrator import process_hitl_command
        
        # Mock project and state machine
        with patch('agent_workflow.core.orchestrator.load_project') as mock_load:
            mock_project = Mock()
            mock_state_machine = Mock()
            mock_state_machine.handle_command.return_value = Mock(success=True, message="Success")
            mock_project.state_machine = mock_state_machine
            mock_load.return_value = mock_project
            
            result = process_hitl_command("test_project", "/state", {})
            
            assert result.success is True
            mock_state_machine.handle_command.assert_called_once()

    def test_approval_workflow(self, project_config):
        """Test approval workflow functionality."""
        from agent_workflow.core.orchestrator import request_approval, process_approval
        
        # Test requesting approval
        approval_id = request_approval("test_project", "Test approval request", {"task": "data"})
        assert approval_id is not None
        assert isinstance(approval_id, str)
        
        # Test processing approval
        with patch('agent_workflow.core.orchestrator.load_project') as mock_load:
            mock_project = Mock()
            mock_project.pending_approvals = [approval_id]
            mock_load.return_value = mock_project
            
            result = process_approval(approval_id, True, "Approved by user")
            
            assert result is True

    def test_agent_coordination(self, project_config):
        """Test agent coordination functionality."""
        from agent_workflow.core.orchestrator import coordinate_agents
        
        # Mock agents
        with patch('agent_workflow.core.orchestrator.get_available_agents') as mock_agents:
            mock_agent = Mock()
            mock_agent.run = AsyncMock(return_value={"status": "completed"})
            mock_agents.return_value = [mock_agent]
            
            # Test coordination
            result = asyncio.run(coordinate_agents("test_project", ["task1", "task2"]))
            
            assert len(result) > 0

    def test_tdd_cycle_management(self, project_config):
        """Test TDD cycle management."""
        from agent_workflow.core.orchestrator import start_tdd_cycle, complete_tdd_cycle
        
        with patch('agent_workflow.core.storage.ProjectStorage') as mock_storage_class:
            mock_storage = Mock()
            mock_storage.save_tdd_cycle = Mock()
            mock_storage.get_active_tdd_cycle.return_value = None
            mock_storage_class.return_value = mock_storage
            
            # Test starting TDD cycle
            cycle_id = start_tdd_cycle("test_project", "STORY-1")
            assert cycle_id is not None
            
            # Test completing TDD cycle
            result = complete_tdd_cycle("test_project", cycle_id)
            assert result is True

    @pytest.mark.asyncio
    async def test_workflow_execution(self, project_config):
        """Test end-to-end workflow execution."""
        from agent_workflow.core.orchestrator import execute_workflow
        
        workflow_steps = [
            {"type": "epic", "data": {"title": "Test Epic", "description": "Test Description"}},
            {"type": "story", "data": {"title": "Test Story", "epic_id": "EPIC-1"}},
            {"type": "sprint", "data": {"goal": "Test Sprint"}}
        ]
        
        with patch('agent_workflow.core.orchestrator.load_project') as mock_load:
            mock_project = Mock()
            mock_project.storage = Mock()
            mock_project.storage.save_project_data = Mock()
            mock_load.return_value = mock_project
            
            result = await execute_workflow("test_project", workflow_steps)
            
            assert result["success"] is True
            assert "executed_steps" in result


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""
    
    @pytest.mark.asyncio
    async def test_multi_project_coordination(self):
        """Test coordination between multiple projects."""
        # This would test cross-project intelligence and resource sharing
        pass

    @pytest.mark.asyncio 
    async def test_disaster_recovery(self):
        """Test disaster recovery scenarios."""
        # This would test backup/restore and crash recovery
        pass

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance under high load."""
        # This would test resource management and scaling
        pass


if __name__ == "__main__":
    pytest.main([__file__])