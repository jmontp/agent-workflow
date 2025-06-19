"""
Resource Allocation and Scheduling System

Advanced resource management for multi-project orchestration with
intelligent scheduling, load balancing, and dynamic resource allocation.
"""

import asyncio
import logging
import time
import heapq
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import math

from .multi_project_config import ProjectConfig, ProjectPriority, ProjectStatus, ResourceLimits

logger = logging.getLogger(__name__)


class SchedulingStrategy(Enum):
    """Resource scheduling strategies"""
    FAIR_SHARE = "fair_share"           # Equal distribution
    PRIORITY_BASED = "priority_based"   # Based on project priority
    DYNAMIC = "dynamic"                 # Adaptive based on usage
    DEADLINE_AWARE = "deadline_aware"   # Consider project deadlines
    EFFICIENCY_OPTIMIZED = "efficiency_optimized"  # Optimize for resource efficiency


class ResourceType(Enum):
    """Types of resources to manage"""
    CPU = "cpu"
    MEMORY = "memory"
    AGENTS = "agents"
    DISK = "disk"
    NETWORK = "network"


class TaskPriority(Enum):
    """Priority levels for tasks"""
    CRITICAL = 1    # Production issues, blocking bugs
    HIGH = 2        # Important features, sprint goals
    NORMAL = 3      # Regular development work
    LOW = 4         # Maintenance, documentation
    BACKGROUND = 5  # Cleanup, optimization


@dataclass
class ResourceQuota:
    """Resource quota for a project"""
    cpu_cores: float = 1.0
    memory_mb: int = 1024
    max_agents: int = 3
    disk_mb: int = 2048
    network_bandwidth_mbps: float = 100.0
    
    def __post_init__(self):
        """Validate quota values for actual allocations"""
        # Only validate if this appears to be an actual resource allocation
        # (not a calculation intermediate like available resources)
        if hasattr(self, '_skip_validation'):
            return
            
        if self.cpu_cores <= 0:
            raise ValueError("CPU cores must be positive")
        if self.memory_mb <= 0:
            raise ValueError("Memory must be positive")
        if self.max_agents <= 0:
            raise ValueError("Max agents must be positive")
    
    @classmethod
    def create_unvalidated(cls, cpu_cores=0.0, memory_mb=0, max_agents=0, disk_mb=0, network_bandwidth_mbps=0.0):
        """Create a ResourceQuota without validation for internal calculations"""
        quota = cls.__new__(cls)
        quota.cpu_cores = cpu_cores
        quota.memory_mb = memory_mb
        quota.max_agents = max_agents
        quota.disk_mb = disk_mb
        quota.network_bandwidth_mbps = network_bandwidth_mbps
        quota._skip_validation = True
        return quota


@dataclass
class ResourceUsage:
    """Current resource usage"""
    cpu_usage: float = 0.0      # Current CPU usage (0.0 to cpu_cores)
    memory_usage_mb: int = 0    # Current memory usage in MB
    active_agents: int = 0      # Currently active agents
    disk_usage_mb: int = 0      # Current disk usage in MB
    network_usage_mbps: float = 0.0  # Current network usage
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def utilization_ratio(self, quota: ResourceQuota) -> Dict[str, float]:
        """Calculate utilization ratio for each resource type"""
        return {
            "cpu": self.cpu_usage / quota.cpu_cores if quota.cpu_cores > 0 else 0.0,
            "memory": self.memory_usage_mb / quota.memory_mb if quota.memory_mb > 0 else 0.0,
            "agents": self.active_agents / quota.max_agents if quota.max_agents > 0 else 0.0,
            "disk": self.disk_usage_mb / quota.disk_mb if quota.disk_mb > 0 else 0.0,
            "network": self.network_usage_mbps / quota.network_bandwidth_mbps if quota.network_bandwidth_mbps > 0 else 0.0
        }


@dataclass
class ScheduledTask:
    """A scheduled task for resource allocation"""
    task_id: str
    project_name: str
    priority: TaskPriority
    estimated_duration: timedelta
    resource_requirements: ResourceQuota
    dependencies: List[str] = field(default_factory=list)
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if task is ready to run (all dependencies completed)"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def is_overdue(self) -> bool:
        """Check if task is past its deadline"""
        return self.deadline and datetime.utcnow() > self.deadline


@dataclass
class ProjectSchedule:
    """Scheduling information for a project"""
    project_name: str
    current_quota: ResourceQuota
    current_usage: ResourceUsage
    pending_tasks: List[ScheduledTask] = field(default_factory=list)
    running_tasks: List[ScheduledTask] = field(default_factory=list)
    completed_tasks: List[ScheduledTask] = field(default_factory=list)
    
    # Performance metrics
    average_utilization: Dict[str, float] = field(default_factory=dict)
    efficiency_score: float = 0.0
    last_allocation_change: Optional[datetime] = None
    allocation_history: List[Tuple[datetime, ResourceQuota]] = field(default_factory=list)


class ResourceScheduler:
    """
    Advanced resource scheduler for multi-project orchestration.
    
    Manages resource allocation, task scheduling, and load balancing
    across multiple projects with intelligent optimization algorithms.
    """
    
    def __init__(
        self,
        total_resources: ResourceQuota,
        strategy: SchedulingStrategy = SchedulingStrategy.DYNAMIC,
        rebalance_interval: int = 300  # 5 minutes
    ):
        """
        Initialize resource scheduler.
        
        Args:
            total_resources: Total available resources in the system
            strategy: Scheduling strategy to use
            rebalance_interval: How often to rebalance resources (seconds)
        """
        self.total_resources = total_resources
        self.strategy = strategy
        self.rebalance_interval = rebalance_interval
        
        # Project scheduling state
        self.project_schedules: Dict[str, ProjectSchedule] = {}
        self.global_task_queue: List[ScheduledTask] = []
        self.completed_tasks: Set[str] = set()
        
        # Resource allocation tracking
        self.allocated_resources: Dict[str, ResourceQuota] = {}
        self.available_resources = ResourceQuota(
            cpu_cores=total_resources.cpu_cores,
            memory_mb=total_resources.memory_mb,
            max_agents=total_resources.max_agents,
            disk_mb=total_resources.disk_mb,
            network_bandwidth_mbps=total_resources.network_bandwidth_mbps
        )
        
        # Performance and optimization
        self.allocation_history: List[Tuple[datetime, Dict[str, ResourceQuota]]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.optimization_callbacks: List[Callable] = []
        
        # Background tasks
        self._scheduler_task: Optional[asyncio.Task] = None
        self._rebalancer_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        logger.info(f"Resource scheduler initialized with strategy: {strategy.value}")
    
    async def start(self) -> None:
        """Start the resource scheduler"""
        self._scheduler_task = asyncio.create_task(self._scheduling_loop())
        self._rebalancer_task = asyncio.create_task(self._rebalancing_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource scheduler started")
    
    async def stop(self) -> None:
        """Stop the resource scheduler"""
        tasks = [self._scheduler_task, self._rebalancer_task, self._monitoring_task]
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        logger.info("Resource scheduler stopped")
    
    def register_project(self, project_config: ProjectConfig) -> bool:
        """
        Register a project for resource scheduling.
        
        Args:
            project_config: Project configuration
            
        Returns:
            True if registered successfully, False otherwise
        """
        if project_config.name in self.project_schedules:
            logger.warning(f"Project '{project_config.name}' already registered")
            return False
        
        # Calculate initial resource allocation
        initial_quota = self._calculate_initial_allocation(project_config)
        
        if not self._can_allocate_resources(initial_quota):
            logger.error(f"Cannot allocate resources for project '{project_config.name}'")
            return False
        
        # Create project schedule
        schedule = ProjectSchedule(
            project_name=project_config.name,
            current_quota=initial_quota,
            current_usage=ResourceUsage()
        )
        
        self.project_schedules[project_config.name] = schedule
        self.allocated_resources[project_config.name] = initial_quota
        self._update_available_resources()
        
        logger.info(f"Registered project '{project_config.name}' with quota: {asdict(initial_quota)}")
        return True
    
    def unregister_project(self, project_name: str) -> bool:
        """
        Unregister a project from resource scheduling.
        
        Args:
            project_name: Name of project to unregister
            
        Returns:
            True if unregistered successfully, False otherwise
        """
        if project_name not in self.project_schedules:
            logger.warning(f"Project '{project_name}' not registered")
            return False
        
        # Cancel all pending tasks for this project
        # Note: global_task_queue stores tuples (priority, created_at, task)
        self.global_task_queue = [
            task_tuple for task_tuple in self.global_task_queue
            if task_tuple[2].project_name != project_name
        ]
        heapq.heapify(self.global_task_queue)  # Restore heap property
        
        # Free up allocated resources
        if project_name in self.allocated_resources:
            del self.allocated_resources[project_name]
        
        del self.project_schedules[project_name]
        self._update_available_resources()
        
        logger.info(f"Unregistered project '{project_name}'")
        return True
    
    def submit_task(self, task: ScheduledTask) -> bool:
        """
        Submit a task for scheduling.
        
        Args:
            task: Task to schedule
            
        Returns:
            True if submitted successfully, False otherwise
        """
        if task.project_name not in self.project_schedules:
            logger.error(f"Project '{task.project_name}' not registered")
            return False
        
        # Add to project's pending tasks
        schedule = self.project_schedules[task.project_name]
        schedule.pending_tasks.append(task)
        
        # Add to global queue for scheduling
        heapq.heappush(self.global_task_queue, (task.priority.value, task.created_at, task))
        
        logger.debug(f"Submitted task '{task.task_id}' for project '{task.project_name}'")
        return True
    
    def update_resource_usage(self, project_name: str, usage: ResourceUsage) -> None:
        """
        Update current resource usage for a project.
        
        Args:
            project_name: Name of project
            usage: Current resource usage
        """
        if project_name not in self.project_schedules:
            return
        
        schedule = self.project_schedules[project_name]
        schedule.current_usage = usage
        
        # Update performance metrics
        self._update_performance_metrics(project_name)
    
    def get_project_allocation(self, project_name: str) -> Optional[ResourceQuota]:
        """Get current resource allocation for a project"""
        return self.allocated_resources.get(project_name)
    
    def get_system_utilization(self) -> Dict[str, float]:
        """Get overall system resource utilization"""
        total_usage = ResourceUsage()
        
        for schedule in self.project_schedules.values():
            usage = schedule.current_usage
            total_usage.cpu_usage += usage.cpu_usage
            total_usage.memory_usage_mb += usage.memory_usage_mb
            total_usage.active_agents += usage.active_agents
            total_usage.disk_usage_mb += usage.disk_usage_mb
            total_usage.network_usage_mbps += usage.network_usage_mbps
        
        return {
            "cpu": total_usage.cpu_usage / self.total_resources.cpu_cores,
            "memory": total_usage.memory_usage_mb / self.total_resources.memory_mb,
            "agents": total_usage.active_agents / self.total_resources.max_agents,
            "disk": total_usage.disk_usage_mb / self.total_resources.disk_mb,
            "network": total_usage.network_usage_mbps / self.total_resources.network_bandwidth_mbps
        }
    
    def get_scheduling_status(self) -> Dict[str, Any]:
        """Get comprehensive scheduling status"""
        return {
            "strategy": self.strategy.value,
            "total_resources": asdict(self.total_resources),
            "available_resources": asdict(self.available_resources),
            "system_utilization": self.get_system_utilization(),
            "active_projects": len(self.project_schedules),
            "pending_tasks": len(self.global_task_queue),
            "completed_tasks": len(self.completed_tasks),
            "projects": {
                name: {
                    "quota": asdict(schedule.current_quota),
                    "usage": asdict(schedule.current_usage),
                    "utilization": schedule.current_usage.utilization_ratio(schedule.current_quota),
                    "pending_tasks": len(schedule.pending_tasks),
                    "running_tasks": len(schedule.running_tasks),
                    "completed_tasks": len(schedule.completed_tasks),
                    "efficiency_score": schedule.efficiency_score
                }
                for name, schedule in self.project_schedules.items()
            },
            "performance_metrics": self.performance_metrics
        }
    
    async def optimize_allocation(self) -> Dict[str, Any]:
        """
        Optimize resource allocation across all projects.
        
        Returns:
            Optimization results and metrics
        """
        optimization_start = time.time()
        changes_made = []
        
        # Collect current state
        current_allocations = self.allocated_resources.copy()
        utilization_data = {}
        
        for name, schedule in self.project_schedules.items():
            utilization = schedule.current_usage.utilization_ratio(schedule.current_quota)
            utilization_data[name] = utilization
        
        # Apply optimization strategy
        if self.strategy == SchedulingStrategy.FAIR_SHARE:
            changes_made = await self._optimize_fair_share()
        elif self.strategy == SchedulingStrategy.PRIORITY_BASED:
            changes_made = await self._optimize_priority_based()
        elif self.strategy == SchedulingStrategy.DYNAMIC:
            changes_made = await self._optimize_dynamic()
        elif self.strategy == SchedulingStrategy.EFFICIENCY_OPTIMIZED:
            changes_made = await self._optimize_efficiency()
        
        optimization_time = time.time() - optimization_start
        
        # Calculate improvement metrics
        improvement_metrics = self._calculate_improvement_metrics(
            current_allocations, utilization_data
        )
        
        logger.info(f"Optimization completed in {optimization_time:.2f}s with {len(changes_made)} changes")
        
        return {
            "optimization_time": optimization_time,
            "changes_made": changes_made,
            "improvement_metrics": improvement_metrics,
            "strategy_used": self.strategy.value
        }
    
    # Private methods
    
    def _calculate_initial_allocation(self, project_config: ProjectConfig) -> ResourceQuota:
        """Calculate initial resource allocation for a project"""
        # Base allocation on project priority and resource limits
        priority_multipliers = {
            ProjectPriority.CRITICAL: 1.5,
            ProjectPriority.HIGH: 1.2,
            ProjectPriority.NORMAL: 1.0,
            ProjectPriority.LOW: 0.7
        }
        
        multiplier = priority_multipliers.get(project_config.priority, 1.0)
        limits = project_config.resource_limits
        
        # Calculate initial allocation, ensuring minimum valid values
        allocated_cpu = min(limits.max_parallel_agents * 0.5 * multiplier, self.available_resources.cpu_cores)
        allocated_memory = min(limits.max_memory_mb * multiplier, self.available_resources.memory_mb)
        allocated_agents = min(limits.max_parallel_agents, self.available_resources.max_agents)
        allocated_disk = min(limits.max_disk_mb, self.available_resources.disk_mb)
        allocated_network = min(100.0 * multiplier, self.available_resources.network_bandwidth_mbps)
        
        # Ensure minimum allocations to pass validation
        allocated_cpu = max(0.1, allocated_cpu)
        allocated_memory = max(1, allocated_memory)
        allocated_agents = max(1, allocated_agents)
        allocated_disk = max(1, allocated_disk)
        allocated_network = max(0.1, allocated_network)
        
        return ResourceQuota(
            cpu_cores=allocated_cpu,
            memory_mb=allocated_memory,
            max_agents=allocated_agents,
            disk_mb=allocated_disk,
            network_bandwidth_mbps=allocated_network
        )
    
    def _can_allocate_resources(self, quota: ResourceQuota) -> bool:
        """Check if resources can be allocated"""
        return (
            quota.cpu_cores <= self.available_resources.cpu_cores and
            quota.memory_mb <= self.available_resources.memory_mb and
            quota.max_agents <= self.available_resources.max_agents and
            quota.disk_mb <= self.available_resources.disk_mb and
            quota.network_bandwidth_mbps <= self.available_resources.network_bandwidth_mbps
        )
    
    def _update_available_resources(self) -> None:
        """Update available resources based on current allocations"""
        # Initialize totals to zero
        total_allocated_cpu = 0.0
        total_allocated_memory = 0
        total_allocated_agents = 0
        total_allocated_disk = 0
        total_allocated_network = 0.0
        
        for quota in self.allocated_resources.values():
            total_allocated_cpu += quota.cpu_cores
            total_allocated_memory += quota.memory_mb
            total_allocated_agents += quota.max_agents
            total_allocated_disk += quota.disk_mb
            total_allocated_network += quota.network_bandwidth_mbps
        
        self.available_resources = ResourceQuota.create_unvalidated(
            cpu_cores=max(0, self.total_resources.cpu_cores - total_allocated_cpu),
            memory_mb=max(0, self.total_resources.memory_mb - total_allocated_memory),
            max_agents=max(0, self.total_resources.max_agents - total_allocated_agents),
            disk_mb=max(0, self.total_resources.disk_mb - total_allocated_disk),
            network_bandwidth_mbps=max(0, self.total_resources.network_bandwidth_mbps - total_allocated_network)
        )
    
    def _update_performance_metrics(self, project_name: str) -> None:
        """Update performance metrics for a project"""
        if project_name not in self.project_schedules:
            return
        
        schedule = self.project_schedules[project_name]
        utilization = schedule.current_usage.utilization_ratio(schedule.current_quota)
        
        # Update running average of utilization
        if not schedule.average_utilization:
            schedule.average_utilization = utilization.copy()
        else:
            alpha = 0.1  # Smoothing factor
            for resource, value in utilization.items():
                schedule.average_utilization[resource] = (
                    schedule.average_utilization[resource] * (1 - alpha) + value * alpha
                )
        
        # Calculate efficiency score (balance between utilization and overprovisioning)
        avg_util = sum(schedule.average_utilization.values()) / len(schedule.average_utilization)
        schedule.efficiency_score = self._calculate_efficiency_score(avg_util)
    
    def _calculate_efficiency_score(self, utilization: float) -> float:
        """Calculate efficiency score based on utilization"""
        # Optimal utilization is around 70-80%
        if 0.7 <= utilization <= 0.8:
            return 1.0
        elif utilization < 0.7:
            # Under-utilized, score decreases linearly
            return utilization / 0.7
        else:
            # Over-utilized, score decreases more sharply
            return max(0.0, 1.0 - (utilization - 0.8) * 5)
    
    async def _scheduling_loop(self) -> None:
        """Main scheduling loop"""
        while True:
            try:
                await self._process_task_queue()
                await asyncio.sleep(10)  # Process every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduling loop error: {str(e)}")
                await asyncio.sleep(30)
    
    async def _rebalancing_loop(self) -> None:
        """Resource rebalancing loop"""
        while True:
            try:
                await self.optimize_allocation()
                await asyncio.sleep(self.rebalance_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rebalancing loop error: {str(e)}")
                await asyncio.sleep(self.rebalance_interval * 2)
    
    async def _monitoring_loop(self) -> None:
        """Performance monitoring loop"""
        while True:
            try:
                self._collect_performance_metrics()
                await asyncio.sleep(60)  # Monitor every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(120)
    
    async def _process_task_queue(self) -> None:
        """Process the global task queue"""
        ready_tasks = []
        
        # Find tasks that are ready to run
        for _, _, task in self.global_task_queue:
            if task.is_ready(self.completed_tasks):
                schedule = self.project_schedules.get(task.project_name)
                if schedule and self._can_run_task(task, schedule):
                    ready_tasks.append(task)
        
        # Start ready tasks
        for task in ready_tasks:
            await self._start_task(task)
    
    def _can_run_task(self, task: ScheduledTask, schedule: ProjectSchedule) -> bool:
        """Check if a task can run given current resource usage"""
        current = schedule.current_usage
        quota = schedule.current_quota
        required = task.resource_requirements
        
        return (
            current.cpu_usage + required.cpu_cores <= quota.cpu_cores and
            current.memory_usage_mb + required.memory_mb <= quota.memory_mb and
            current.active_agents + required.max_agents <= quota.max_agents
        )
    
    async def _start_task(self, task: ScheduledTask) -> None:
        """Start executing a task"""
        schedule = self.project_schedules[task.project_name]
        
        # Move from pending to running
        if task in schedule.pending_tasks:
            schedule.pending_tasks.remove(task)
        schedule.running_tasks.append(task)
        
        # Remove from global queue
        self.global_task_queue = [
            (priority, created, t) for priority, created, t in self.global_task_queue
            if t.task_id != task.task_id
        ]
        
        task.started_at = datetime.utcnow()
        logger.info(f"Started task '{task.task_id}' for project '{task.project_name}'")
    
    def _collect_performance_metrics(self) -> None:
        """Collect system-wide performance metrics"""
        utilization = self.get_system_utilization()
        efficiency_scores = [s.efficiency_score for s in self.project_schedules.values()]
        
        self.performance_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_utilization": utilization,
            "average_efficiency": sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0.0,
            "resource_fragmentation": self._calculate_fragmentation(),
            "pending_tasks": len(self.global_task_queue),
            "active_projects": len([s for s in self.project_schedules.values() if s.running_tasks])
        }
    
    def _calculate_fragmentation(self) -> float:
        """Calculate resource fragmentation score"""
        # High fragmentation = many small unused resource chunks
        # Low fragmentation = resources are well-consolidated
        available = self.available_resources
        total = self.total_resources
        
        fragmentation_score = 0.0
        resource_count = 0
        
        for attr in ['cpu_cores', 'memory_mb', 'max_agents', 'disk_mb']:
            available_val = getattr(available, attr)
            total_val = getattr(total, attr)
            if total_val > 0:
                fragmentation_score += (available_val / total_val) ** 2
                resource_count += 1
        
        return fragmentation_score / resource_count if resource_count > 0 else 0.0
    
    async def _optimize_fair_share(self) -> List[str]:
        """Optimize using fair share strategy"""
        changes = []
        active_projects = len(self.project_schedules)
        
        if active_projects == 0:
            return changes
        
        # Calculate fair share per project
        fair_share = ResourceQuota(
            cpu_cores=self.total_resources.cpu_cores / active_projects,
            memory_mb=self.total_resources.memory_mb // active_projects,
            max_agents=self.total_resources.max_agents // active_projects,
            disk_mb=self.total_resources.disk_mb // active_projects,
            network_bandwidth_mbps=self.total_resources.network_bandwidth_mbps / active_projects
        )
        
        # Adjust allocations toward fair share
        for project_name, current_quota in self.allocated_resources.items():
            new_quota = fair_share
            if new_quota != current_quota:
                self.allocated_resources[project_name] = new_quota
                self.project_schedules[project_name].current_quota = new_quota
                changes.append(f"Adjusted {project_name} to fair share allocation")
        
        self._update_available_resources()
        return changes
    
    async def _optimize_priority_based(self) -> List[str]:
        """Optimize using priority-based strategy"""
        # This would implement priority-based resource allocation
        return []
    
    async def _optimize_dynamic(self) -> List[str]:
        """Optimize using dynamic strategy based on usage patterns"""
        changes = []
        
        # Identify under-utilized and over-utilized projects
        for project_name, schedule in self.project_schedules.items():
            utilization = schedule.current_usage.utilization_ratio(schedule.current_quota)
            avg_util = sum(utilization.values()) / len(utilization)
            
            if avg_util < 0.3:  # Under-utilized
                # Reduce allocation
                current_quota = self.allocated_resources[project_name]
                new_quota = ResourceQuota(
                    cpu_cores=current_quota.cpu_cores * 0.8,
                    memory_mb=int(current_quota.memory_mb * 0.8),
                    max_agents=max(1, int(current_quota.max_agents * 0.8)),
                    disk_mb=int(current_quota.disk_mb * 0.8),
                    network_bandwidth_mbps=current_quota.network_bandwidth_mbps * 0.8
                )
                self.allocated_resources[project_name] = new_quota
                schedule.current_quota = new_quota
                changes.append(f"Reduced allocation for under-utilized project {project_name}")
            
            elif avg_util > 0.9:  # Over-utilized
                # Try to increase allocation if resources are available
                current_quota = self.allocated_resources[project_name]
                requested_increase = ResourceQuota(
                    cpu_cores=current_quota.cpu_cores * 0.2,
                    memory_mb=int(current_quota.memory_mb * 0.2),
                    max_agents=1,
                    disk_mb=int(current_quota.disk_mb * 0.2),
                    network_bandwidth_mbps=current_quota.network_bandwidth_mbps * 0.2
                )
                
                if self._can_allocate_resources(requested_increase):
                    new_quota = ResourceQuota(
                        cpu_cores=current_quota.cpu_cores + requested_increase.cpu_cores,
                        memory_mb=current_quota.memory_mb + requested_increase.memory_mb,
                        max_agents=current_quota.max_agents + requested_increase.max_agents,
                        disk_mb=current_quota.disk_mb + requested_increase.disk_mb,
                        network_bandwidth_mbps=current_quota.network_bandwidth_mbps + requested_increase.network_bandwidth_mbps
                    )
                    self.allocated_resources[project_name] = new_quota
                    schedule.current_quota = new_quota
                    changes.append(f"Increased allocation for over-utilized project {project_name}")
        
        self._update_available_resources()
        return changes
    
    async def _optimize_efficiency(self) -> List[str]:
        """Optimize for maximum resource efficiency"""
        # This would implement efficiency-focused optimization
        return []
    
    def _calculate_improvement_metrics(
        self,
        old_allocations: Dict[str, ResourceQuota],
        old_utilization: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Calculate improvement metrics from optimization"""
        # Calculate efficiency improvement
        old_efficiency = sum(
            self._calculate_efficiency_score(sum(util.values()) / len(util))
            for util in old_utilization.values()
        ) / len(old_utilization) if old_utilization else 0.0
        
        new_efficiency = sum(
            schedule.efficiency_score for schedule in self.project_schedules.values()
        ) / len(self.project_schedules) if self.project_schedules else 0.0
        
        return {
            "efficiency_improvement": new_efficiency - old_efficiency,
            "resource_savings": self._calculate_resource_savings(old_allocations),
            "fragmentation_improvement": 0.0  # Would calculate fragmentation change
        }
    
    def _calculate_resource_savings(self, old_allocations: Dict[str, ResourceQuota]) -> float:
        """Calculate percentage of resources saved through optimization"""
        old_total = sum(
            quota.cpu_cores + quota.memory_mb/1024 + quota.max_agents
            for quota in old_allocations.values()
        )
        
        new_total = sum(
            quota.cpu_cores + quota.memory_mb/1024 + quota.max_agents
            for quota in self.allocated_resources.values()
        )
        
        return ((old_total - new_total) / old_total * 100) if old_total > 0 else 0.0