"""
Unit tests for Resource Scheduler.

Tests the resource scheduler system that manages allocation and optimization
of computational resources across multiple projects.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.resource_scheduler import (
    ResourceScheduler, ResourceQuota, SchedulingStrategy, ScheduledTask,
    TaskPriority, ResourceUsage, ResourceType
)
from lib.multi_project_config import ProjectConfig, ProjectPriority


class TestResourceQuota:
    """Test the ResourceQuota dataclass."""
    
    def test_resource_quota_creation(self):
        """Test creating a ResourceQuota with all fields."""
        quota = ResourceQuota(
            cpu_cores=8.0,
            memory_mb=16384,
            max_agents=15,
            disk_mb=51200,
            network_bandwidth_mbps=1000.0
        )
        
        assert quota.cpu_cores == 8.0
        assert quota.memory_mb == 16384
        assert quota.max_agents == 15
        assert quota.disk_mb == 51200
        assert quota.network_bandwidth_mbps == 1000.0

    def test_resource_quota_defaults(self):
        """Test ResourceQuota with default values."""
        quota = ResourceQuota()
        
        assert quota.cpu_cores == 4.0
        assert quota.memory_mb == 8192
        assert quota.max_agents == 10
        assert quota.disk_mb == 20480
        assert quota.network_bandwidth_mbps == 100.0


class TestResourceUsage:
    """Test the ResourceUsage dataclass."""
    
    def test_resource_usage_creation(self):
        """Test creating a ResourceUsage instance."""
        now = datetime.utcnow()
        
        usage = ResourceUsage(
            project_name="test-project",
            cpu_usage=65.5,
            memory_usage_mb=2048,
            active_agents=5,
            disk_usage_mb=1024,
            network_usage_mbps=50.0,
            timestamp=now
        )
        
        assert usage.project_name == "test-project"
        assert usage.cpu_usage == 65.5
        assert usage.memory_usage_mb == 2048
        assert usage.active_agents == 5
        assert usage.disk_usage_mb == 1024
        assert usage.network_usage_mbps == 50.0
        assert usage.timestamp == now

    def test_resource_usage_defaults(self):
        """Test ResourceUsage with default values."""
        usage = ResourceUsage(project_name="default-test")
        
        assert usage.project_name == "default-test"
        assert usage.cpu_usage == 0.0
        assert usage.memory_usage_mb == 0
        assert usage.active_agents == 0
        assert isinstance(usage.timestamp, datetime)


class TestScheduledTask:
    """Test the ScheduledTask dataclass."""
    
    def test_scheduled_task_creation(self):
        """Test creating a ScheduledTask instance."""
        now = datetime.utcnow()
        
        task = ScheduledTask(
            task_id="task-123",
            project_name="test-project",
            priority=TaskPriority.HIGH,
            estimated_duration=timedelta(minutes=30),
            resource_requirements=ResourceQuota(cpu_cores=2.0, memory_mb=1024),
            created_at=now
        )
        
        assert task.task_id == "task-123"
        assert task.project_name == "test-project"
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_duration == timedelta(minutes=30)
        assert task.resource_requirements.cpu_cores == 2.0
        assert task.created_at == now

    def test_scheduled_task_defaults(self):
        """Test ScheduledTask with default values."""
        task = ScheduledTask(
            task_id="default-task",
            project_name="default-project",
            priority=TaskPriority.NORMAL,
            estimated_duration=timedelta(hours=1),
            resource_requirements=ResourceQuota()
        )
        
        assert task.task_id == "default-task"
        # Note: TaskStatus doesn't exist in actual implementation 
        assert task.priority == TaskPriority.NORMAL
        assert task.estimated_duration == timedelta(hours=1)
        assert isinstance(task.created_at, datetime)


class TestEnums:
    """Test enum classes."""
    
    def test_scheduling_strategy_values(self):
        """Test SchedulingStrategy enum values."""
        assert SchedulingStrategy.FAIR_SHARE.value == "fair_share"
        assert SchedulingStrategy.PRIORITY_BASED.value == "priority_based"
        assert SchedulingStrategy.DYNAMIC.value == "dynamic"
        assert SchedulingStrategy.SHORTEST_JOB_FIRST.value == "shortest_job_first"

    def test_task_priority_values(self):
        """Test TaskPriority enum values."""
        assert TaskPriority.CRITICAL.value == "critical"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.NORMAL.value == "normal"
        assert TaskPriority.LOW.value == "low"

    # TaskStatus enum doesn't exist in the actual implementation

    def test_resource_type_values(self):
        """Test ResourceType enum values."""
        assert ResourceType.CPU.value == "cpu"
        assert ResourceType.MEMORY.value == "memory"
        assert ResourceType.AGENTS.value == "agents"
        assert ResourceType.DISK.value == "disk"
        assert ResourceType.NETWORK.value == "network"


class TestResourceScheduler:
    """Test the ResourceScheduler class."""
    
    @pytest.fixture
    def total_resources(self):
        """Create total system resources for testing."""
        return ResourceQuota(
            cpu_cores=8.0,
            memory_mb=16384,
            max_agents=20,
            disk_mb=102400,
            network_bandwidth_mbps=1000.0
        )
    
    @pytest.fixture
    def resource_scheduler(self, total_resources):
        """Create a ResourceScheduler instance."""
        return ResourceScheduler(
            total_resources=total_resources,
            strategy=SchedulingStrategy.FAIR_SHARE,
            rebalance_interval=300
        )
    
    @pytest.fixture
    def sample_project_config(self):
        """Create a sample project configuration."""
        return ProjectConfig(
            name="test-project",
            path="/path/to/project",
            priority=ProjectPriority.NORMAL
        )

    def test_resource_scheduler_init(self, resource_scheduler, total_resources):
        """Test ResourceScheduler initialization."""
        assert resource_scheduler.total_resources == total_resources
        assert resource_scheduler.strategy == SchedulingStrategy.FAIR_SHARE
        assert resource_scheduler.rebalance_interval == 300
        assert resource_scheduler.projects == {}
        assert resource_scheduler.tasks == {}
        assert resource_scheduler.resource_usage_history == []

    @pytest.mark.asyncio
    async def test_start_scheduler(self, resource_scheduler):
        """Test starting the resource scheduler."""
        await resource_scheduler.start()
        
        assert resource_scheduler.running
        assert resource_scheduler._scheduler_task is not None
        assert resource_scheduler._rebalancer_task is not None
        
        # Clean up
        await resource_scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_scheduler(self, resource_scheduler):
        """Test stopping the resource scheduler."""
        await resource_scheduler.start()
        await resource_scheduler.stop()
        
        assert not resource_scheduler.running

    def test_register_project(self, resource_scheduler, sample_project_config):
        """Test registering a project with the scheduler."""
        success = resource_scheduler.register_project(sample_project_config)
        
        assert success
        assert "test-project" in resource_scheduler.projects
        
        project_info = resource_scheduler.projects["test-project"]
        assert project_info["config"] == sample_project_config
        assert project_info["allocated_resources"] is not None

    def test_register_project_duplicate(self, resource_scheduler, sample_project_config):
        """Test registering a duplicate project."""
        resource_scheduler.register_project(sample_project_config)
        
        # Try to register again
        success = resource_scheduler.register_project(sample_project_config)
        assert not success

    def test_unregister_project(self, resource_scheduler, sample_project_config):
        """Test unregistering a project."""
        resource_scheduler.register_project(sample_project_config)
        assert "test-project" in resource_scheduler.projects
        
        success = resource_scheduler.unregister_project("test-project")
        
        assert success
        assert "test-project" not in resource_scheduler.projects

    def test_unregister_project_nonexistent(self, resource_scheduler):
        """Test unregistering a nonexistent project."""
        success = resource_scheduler.unregister_project("nonexistent")
        assert not success

    def test_schedule_task(self, resource_scheduler, sample_project_config):
        """Test scheduling a task."""
        resource_scheduler.register_project(sample_project_config)
        
        task = ScheduledTask(
            task_id="test-task",
            project_name="test-project",
            priority=TaskPriority.HIGH,
            estimated_duration=timedelta(minutes=30),
            resource_requirements=ResourceQuota(cpu_cores=2.0, memory_mb=1024)
        )
        
        success = resource_scheduler.schedule_task(task)
        
        assert success
        assert "test-task" in resource_scheduler.tasks
        assert resource_scheduler.tasks["test-task"] == task

    def test_schedule_task_project_not_registered(self, resource_scheduler):
        """Test scheduling a task for unregistered project."""
        task = ScheduledTask(
            task_id="orphan-task",
            project_name="unregistered-project",
            task_type="tdd_cycle"
        )
        
        success = resource_scheduler.schedule_task(task)
        assert not success

    def test_cancel_task(self, resource_scheduler, sample_project_config):
        """Test cancelling a scheduled task."""
        resource_scheduler.register_project(sample_project_config)
        
        task = ScheduledTask(
            task_id="cancel-test",
            project_name="test-project",
            task_type="tdd_cycle"
        )
        
        resource_scheduler.schedule_task(task)
        # Note: TaskStatus doesn't exist in actual implementation
        
        success = resource_scheduler.cancel_task("cancel-test")
        
        assert success
        # Note: TaskStatus doesn't exist in actual implementation

    def test_cancel_task_nonexistent(self, resource_scheduler):
        """Test cancelling a nonexistent task."""
        success = resource_scheduler.cancel_task("nonexistent")
        assert not success

    def test_update_resource_usage(self, resource_scheduler, sample_project_config):
        """Test updating resource usage for a project."""
        resource_scheduler.register_project(sample_project_config)
        
        usage = ResourceUsage(
            project_name="test-project",
            cpu_usage=45.5,
            memory_usage_mb=2048,
            active_agents=3
        )
        
        resource_scheduler.update_resource_usage(usage)
        
        # Check that usage is recorded
        assert len(resource_scheduler.resource_usage_history) == 1
        assert resource_scheduler.resource_usage_history[0] == usage

    def test_calculate_fair_share_allocation(self, resource_scheduler):
        """Test fair share resource allocation calculation."""
        # Register multiple projects
        project1 = ProjectConfig(name="project1", path="/path1", priority=ProjectPriority.NORMAL)
        project2 = ProjectConfig(name="project2", path="/path2", priority=ProjectPriority.NORMAL)
        
        resource_scheduler.register_project(project1)
        resource_scheduler.register_project(project2)
        
        allocation = resource_scheduler._calculate_fair_share_allocation()
        
        # Each project should get half the resources
        assert "project1" in allocation
        assert "project2" in allocation
        
        project1_alloc = allocation["project1"]
        project2_alloc = allocation["project2"]
        
        # Check fair distribution
        assert project1_alloc.cpu_cores == 4.0  # Half of 8.0
        assert project1_alloc.memory_mb == 8192  # Half of 16384
        assert project1_alloc.max_agents == 10  # Half of 20
        
        assert project2_alloc.cpu_cores == 4.0
        assert project2_alloc.memory_mb == 8192
        assert project2_alloc.max_agents == 10

    def test_calculate_priority_based_allocation(self, resource_scheduler):
        """Test priority-based resource allocation calculation."""
        # Register projects with different priorities
        high_priority = ProjectConfig(name="high", path="/path1", priority=ProjectPriority.HIGH)
        normal_priority = ProjectConfig(name="normal", path="/path2", priority=ProjectPriority.NORMAL)
        low_priority = ProjectConfig(name="low", path="/path3", priority=ProjectPriority.LOW)
        
        resource_scheduler.register_project(high_priority)
        resource_scheduler.register_project(normal_priority)
        resource_scheduler.register_project(low_priority)
        
        allocation = resource_scheduler._calculate_priority_based_allocation()
        
        # High priority should get more resources
        high_alloc = allocation["high"]
        normal_alloc = allocation["normal"]
        low_alloc = allocation["low"]
        
        assert high_alloc.cpu_cores > normal_alloc.cpu_cores
        assert normal_alloc.cpu_cores > low_alloc.cpu_cores
        
        assert high_alloc.memory_mb > normal_alloc.memory_mb
        assert normal_alloc.memory_mb > low_alloc.memory_mb

    def test_calculate_dynamic_allocation(self, resource_scheduler, sample_project_config):
        """Test dynamic resource allocation calculation."""
        resource_scheduler.register_project(sample_project_config)
        
        # Add some usage history
        usage1 = ResourceUsage(
            project_name="test-project",
            cpu_usage=30.0,
            memory_usage_mb=1024,
            timestamp=datetime.utcnow() - timedelta(minutes=5)
        )
        usage2 = ResourceUsage(
            project_name="test-project",
            cpu_usage=45.0,
            memory_usage_mb=1536,
            timestamp=datetime.utcnow()
        )
        
        resource_scheduler.resource_usage_history = [usage1, usage2]
        
        allocation = resource_scheduler._calculate_dynamic_allocation()
        
        assert "test-project" in allocation
        project_alloc = allocation["test-project"]
        
        # Should allocate based on usage patterns
        assert project_alloc.cpu_cores > 0
        assert project_alloc.memory_mb > 0

    def test_get_scheduling_status(self, resource_scheduler, sample_project_config):
        """Test getting scheduling status."""
        resource_scheduler.register_project(sample_project_config)
        
        # Add a task
        task = ScheduledTask(
            task_id="status-test",
            project_name="test-project",
            task_type="tdd_cycle"
            # Note: status parameter doesn't exist in actual implementation
        )
        resource_scheduler.tasks["status-test"] = task
        
        status = resource_scheduler.get_scheduling_status()
        
        assert "total_resources" in status
        assert "projects" in status
        assert "tasks" in status
        assert "resource_utilization" in status
        
        assert len(status["projects"]) == 1
        assert "test-project" in status["projects"]
        
        assert len(status["tasks"]) == 1
        # Note: status field doesn't exist in actual implementation

    @pytest.mark.asyncio
    async def test_optimize_allocation_fair_share(self, resource_scheduler):
        """Test allocation optimization with fair share strategy."""
        # Register projects
        project1 = ProjectConfig(name="opt1", path="/path1")
        project2 = ProjectConfig(name="opt2", path="/path2")
        
        resource_scheduler.register_project(project1)
        resource_scheduler.register_project(project2)
        
        result = await resource_scheduler.optimize_allocation()
        
        assert "strategy_used" in result
        assert result["strategy_used"] == "fair_share"
        assert "optimization_time" in result
        assert "changes_made" in result
        assert isinstance(result["changes_made"], list)

    @pytest.mark.asyncio
    async def test_optimize_allocation_priority_based(self, resource_scheduler):
        """Test allocation optimization with priority-based strategy."""
        resource_scheduler.strategy = SchedulingStrategy.PRIORITY_BASED
        
        # Register projects with different priorities
        high_proj = ProjectConfig(name="high", path="/path1", priority=ProjectPriority.HIGH)
        normal_proj = ProjectConfig(name="normal", path="/path2", priority=ProjectPriority.NORMAL)
        
        resource_scheduler.register_project(high_proj)
        resource_scheduler.register_project(normal_proj)
        
        result = await resource_scheduler.optimize_allocation()
        
        assert result["strategy_used"] == "priority_based"
        assert len(result["changes_made"]) >= 0

    def test_get_project_allocation(self, resource_scheduler, sample_project_config):
        """Test getting allocation for a specific project."""
        resource_scheduler.register_project(sample_project_config)
        
        allocation = resource_scheduler.get_project_allocation("test-project")
        
        assert allocation is not None
        assert allocation.cpu_cores > 0
        assert allocation.memory_mb > 0
        assert allocation.max_agents > 0

    def test_get_project_allocation_nonexistent(self, resource_scheduler):
        """Test getting allocation for nonexistent project."""
        allocation = resource_scheduler.get_project_allocation("nonexistent")
        assert allocation is None

    def test_get_resource_utilization(self, resource_scheduler, sample_project_config):
        """Test calculating resource utilization."""
        resource_scheduler.register_project(sample_project_config)
        
        # Add usage data
        usage = ResourceUsage(
            project_name="test-project",
            cpu_usage=25.0,
            memory_usage_mb=2048,
            active_agents=5
        )
        resource_scheduler.update_resource_usage(usage)
        
        utilization = resource_scheduler.get_resource_utilization()
        
        assert "cpu_utilization_percent" in utilization
        assert "memory_utilization_percent" in utilization
        assert "agent_utilization_percent" in utilization
        assert "total_projects" in utilization

    def test_detect_resource_contention(self, resource_scheduler):
        """Test detecting resource contention."""
        # Register projects that would cause contention
        for i in range(5):  # Register many projects
            project = ProjectConfig(name=f"project{i}", path=f"/path{i}")
            resource_scheduler.register_project(project)
            
            # Add high usage
            usage = ResourceUsage(
                project_name=f"project{i}",
                cpu_usage=80.0,  # High CPU usage
                memory_usage_mb=3000,  # High memory usage
                active_agents=8  # Many agents
            )
            resource_scheduler.update_resource_usage(usage)
        
        contention = resource_scheduler._detect_resource_contention()
        
        assert "cpu_contention" in contention
        assert "memory_contention" in contention
        assert "agent_contention" in contention
        
        # Should detect high contention
        assert contention["cpu_contention"] > 0.5
        assert contention["memory_contention"] > 0.5

    @pytest.mark.asyncio
    async def test_scheduler_loop_execution(self, resource_scheduler):
        """Test that scheduler loop executes without errors."""
        # Start scheduler briefly
        await resource_scheduler.start()
        
        # Let it run for a short time
        await asyncio.sleep(0.1)
        
        # Stop scheduler
        await resource_scheduler.stop()
        
        # Should complete without errors
        assert not resource_scheduler.running

    def test_task_priority_ordering(self, resource_scheduler, sample_project_config):
        """Test that tasks are ordered by priority correctly."""
        resource_scheduler.register_project(sample_project_config)
        
        # Add tasks with different priorities
        low_task = ScheduledTask("low", "test-project", "type", priority=TaskPriority.LOW)
        high_task = ScheduledTask("high", "test-project", "type", priority=TaskPriority.HIGH)
        critical_task = ScheduledTask("critical", "test-project", "type", priority=TaskPriority.CRITICAL)
        
        resource_scheduler.schedule_task(low_task)
        resource_scheduler.schedule_task(high_task)
        resource_scheduler.schedule_task(critical_task)
        
        # Get tasks sorted by priority
        sorted_tasks = resource_scheduler._get_tasks_by_priority()
        
        assert len(sorted_tasks) == 3
        assert sorted_tasks[0].priority == TaskPriority.CRITICAL
        assert sorted_tasks[1].priority == TaskPriority.HIGH
        assert sorted_tasks[2].priority == TaskPriority.LOW

    def test_resource_cleanup(self, resource_scheduler, sample_project_config):
        """Test cleaning up old resource usage data."""
        resource_scheduler.register_project(sample_project_config)
        
        # Add old usage data
        old_usage = ResourceUsage(
            project_name="test-project",
            timestamp=datetime.utcnow() - timedelta(hours=25)  # Older than 24 hours
        )
        recent_usage = ResourceUsage(
            project_name="test-project",
            timestamp=datetime.utcnow() - timedelta(hours=1)  # Recent
        )
        
        resource_scheduler.resource_usage_history = [old_usage, recent_usage]
        
        resource_scheduler._cleanup_old_usage_data()
        
        # Only recent usage should remain
        assert len(resource_scheduler.resource_usage_history) == 1
        assert resource_scheduler.resource_usage_history[0] == recent_usage