"""
Global Multi-Project Orchestrator

Manages multiple project orchestrators, resource allocation, scheduling,
and coordination across the entire portfolio of AI-assisted development projects.
"""

import asyncio
import logging
import subprocess
import signal
import os

# Graceful fallback for psutil
try:
    import psutil
except ImportError:
    psutil = None
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json
import yaml

from .multi_project_config import (
    MultiProjectConfigManager, ProjectConfig, GlobalOrchestratorConfig,
    ProjectStatus, ProjectPriority, ResourceLimits
)

# Import existing components
try:
    from .data_models import Epic, Story, Sprint
    from .state_machine import StateMachine, State
    from .discord_bot import DiscordBot
except ImportError:
    # Graceful fallback for testing
    pass

logger = logging.getLogger(__name__)


class OrchestratorStatus(Enum):
    """Status of project orchestrators"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    CRASHED = "crashed"


@dataclass
class ProjectOrchestrator:
    """Information about a running project orchestrator"""
    project_name: str
    project_path: str
    process: Optional[subprocess.Popen] = None
    status: OrchestratorStatus = OrchestratorStatus.STOPPED
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_agents: int = 0
    current_sprint: Optional[str] = None
    backlog_size: int = 0
    error_count: int = 0
    restart_count: int = 0


@dataclass
class ResourceAllocation:
    """Resource allocation for a project"""
    project_name: str
    allocated_agents: int
    allocated_memory_mb: int
    allocated_cpu_percent: float
    priority_weight: float
    usage_history: List[Tuple[datetime, Dict[str, float]]] = field(default_factory=list)


@dataclass
class GlobalMetrics:
    """Global orchestration metrics"""
    total_projects: int = 0
    active_projects: int = 0
    total_agents: int = 0
    total_memory_usage_mb: float = 0.0
    total_cpu_usage_percent: float = 0.0
    total_stories_in_progress: int = 0
    total_stories_completed: int = 0
    average_cycle_time_hours: float = 0.0
    cross_project_insights: int = 0
    resource_efficiency: float = 0.0


class GlobalOrchestrator:
    """
    Global orchestrator that manages multiple project orchestrators.
    
    Handles resource allocation, scheduling, cross-project coordination,
    monitoring, and provides a unified interface for multi-project management.
    """
    
    def __init__(self, config_manager: MultiProjectConfigManager):
        """
        Initialize global orchestrator.
        
        Args:
            config_manager: Multi-project configuration manager
        """
        self.config_manager = config_manager
        self.global_config = config_manager.global_config
        
        # Project orchestrator management
        self.orchestrators: Dict[str, ProjectOrchestrator] = {}
        self.resource_allocations: Dict[str, ResourceAllocation] = {}
        
        # Global state and coordination
        self.status = OrchestratorStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.metrics = GlobalMetrics()
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._scheduling_task: Optional[asyncio.Task] = None
        self._resource_balancing_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Cross-project knowledge and insights
        self.shared_patterns: Dict[str, Any] = {}
        self.cross_project_insights: List[Dict[str, Any]] = []
        self.global_best_practices: Dict[str, Any] = {}
        
        # Event system for coordination
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.event_handlers: Dict[str, List[callable]] = {}
        
        # Discord integration
        self.discord_bot: Optional[DiscordBot] = None
        
        logger.info("Global orchestrator initialized")
    
    async def start(self) -> None:
        """Start the global orchestrator"""
        if self.status != OrchestratorStatus.STOPPED:
            logger.warning("Global orchestrator already running")
            return
        
        self.status = OrchestratorStatus.STARTING
        logger.info("Starting global orchestrator")
        
        try:
            # Initialize global state directory
            global_state_path = Path(self.global_config.global_state_path)
            global_state_path.mkdir(exist_ok=True)
            
            # Start background tasks
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._scheduling_task = asyncio.create_task(self._scheduling_loop())
            self._resource_balancing_task = asyncio.create_task(self._resource_balancing_loop())
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            # Start Discord bot if configured
            if self.global_config.global_discord_guild:
                await self._start_discord_bot()
            
            # Start active projects
            await self._start_active_projects()
            
            self.status = OrchestratorStatus.RUNNING
            self.start_time = datetime.utcnow()
            
            logger.info("Global orchestrator started successfully")
            
        except Exception as e:
            self.status = OrchestratorStatus.ERROR
            logger.error(f"Failed to start global orchestrator: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the global orchestrator"""
        if self.status == OrchestratorStatus.STOPPED:
            return
        
        self.status = OrchestratorStatus.STOPPING
        logger.info("Stopping global orchestrator")
        
        try:
            # Stop all project orchestrators
            await self._stop_all_projects()
            
            # Cancel background tasks
            tasks = [
                self._monitoring_task,
                self._scheduling_task,
                self._resource_balancing_task,
                self._health_check_task
            ]
            
            for task in tasks:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Stop Discord bot
            if self.discord_bot:
                await self.discord_bot.stop()
            
            self.status = OrchestratorStatus.STOPPED
            logger.info("Global orchestrator stopped")
            
        except Exception as e:
            self.status = OrchestratorStatus.ERROR
            logger.error(f"Error stopping global orchestrator: {str(e)}")
    
    async def start_project(self, project_name: str) -> bool:
        """
        Start orchestrator for a specific project.
        
        Args:
            project_name: Name of project to start
            
        Returns:
            True if started successfully, False otherwise
        """
        project_config = self.config_manager.get_project(project_name)
        if not project_config:
            logger.error(f"Project '{project_name}' not found")
            return False
        
        if project_name in self.orchestrators:
            current_status = self.orchestrators[project_name].status
            if current_status in [OrchestratorStatus.RUNNING, OrchestratorStatus.STARTING]:
                logger.warning(f"Project '{project_name}' is already running")
                return True
        
        try:
            # Calculate resource allocation
            allocation = await self._calculate_resource_allocation(project_config)
            self.resource_allocations[project_name] = allocation
            
            # Prepare orchestrator command
            orchestrator_cmd = await self._prepare_orchestrator_command(project_config, allocation)
            
            # Start project orchestrator subprocess
            process = subprocess.Popen(
                orchestrator_cmd,
                cwd=project_config.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=await self._prepare_project_environment(project_config, allocation)
            )
            
            # Create orchestrator tracking object
            orchestrator = ProjectOrchestrator(
                project_name=project_name,
                project_path=project_config.path,
                process=process,
                status=OrchestratorStatus.STARTING,
                pid=process.pid,
                start_time=datetime.utcnow()
            )
            
            self.orchestrators[project_name] = orchestrator
            
            # Wait a moment to check if process started successfully
            await asyncio.sleep(2)
            
            if process.poll() is None:  # Process is still running
                orchestrator.status = OrchestratorStatus.RUNNING
                logger.info(f"Started project orchestrator for '{project_name}' (PID: {process.pid})")
                
                # Update project status
                self.config_manager.update_project_status(project_name, ProjectStatus.ACTIVE)
                
                return True
            else:
                # Process died immediately
                orchestrator.status = OrchestratorStatus.CRASHED
                logger.error(f"Project orchestrator for '{project_name}' crashed immediately")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start project '{project_name}': {str(e)}")
            if project_name in self.orchestrators:
                self.orchestrators[project_name].status = OrchestratorStatus.ERROR
            return False
    
    async def stop_project(self, project_name: str) -> bool:
        """
        Stop orchestrator for a specific project.
        
        Args:
            project_name: Name of project to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        if project_name not in self.orchestrators:
            logger.warning(f"Project '{project_name}' is not running")
            return True
        
        orchestrator = self.orchestrators[project_name]
        
        try:
            orchestrator.status = OrchestratorStatus.STOPPING
            
            if orchestrator.process and orchestrator.process.poll() is None:
                # Try graceful shutdown first
                orchestrator.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(self._wait_for_process_exit(orchestrator.process)),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    # Force kill if graceful shutdown failed
                    logger.warning(f"Force killing project '{project_name}' orchestrator")
                    orchestrator.process.kill()
                    await asyncio.create_task(self._wait_for_process_exit(orchestrator.process))
            
            orchestrator.status = OrchestratorStatus.STOPPED
            
            # Clean up resource allocation
            if project_name in self.resource_allocations:
                del self.resource_allocations[project_name]
            
            logger.info(f"Stopped project orchestrator for '{project_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop project '{project_name}': {str(e)}")
            orchestrator.status = OrchestratorStatus.ERROR
            return False
    
    async def pause_project(self, project_name: str) -> bool:
        """Pause a project orchestrator"""
        if project_name not in self.orchestrators:
            return False
        
        orchestrator = self.orchestrators[project_name]
        if orchestrator.status != OrchestratorStatus.RUNNING:
            return False
        
        try:
            # Send SIGSTOP to pause the process
            if orchestrator.process and orchestrator.pid:
                os.kill(orchestrator.pid, signal.SIGSTOP)
                orchestrator.status = OrchestratorStatus.PAUSED
                logger.info(f"Paused project '{project_name}'")
                return True
        except Exception as e:
            logger.error(f"Failed to pause project '{project_name}': {str(e)}")
        
        return False
    
    async def resume_project(self, project_name: str) -> bool:
        """Resume a paused project orchestrator"""
        if project_name not in self.orchestrators:
            return False
        
        orchestrator = self.orchestrators[project_name]
        if orchestrator.status != OrchestratorStatus.PAUSED:
            return False
        
        try:
            # Send SIGCONT to resume the process
            if orchestrator.process and orchestrator.pid:
                os.kill(orchestrator.pid, signal.SIGCONT)
                orchestrator.status = OrchestratorStatus.RUNNING
                logger.info(f"Resumed project '{project_name}'")
                return True
        except Exception as e:
            logger.error(f"Failed to resume project '{project_name}': {str(e)}")
        
        return False
    
    async def get_global_status(self) -> Dict[str, Any]:
        """Get comprehensive global orchestration status"""
        await self._update_metrics()
        
        return {
            "global_orchestrator": {
                "status": self.status.value,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
                "configuration": {
                    "max_total_agents": self.global_config.max_total_agents,
                    "max_concurrent_projects": self.global_config.max_concurrent_projects,
                    "resource_allocation_strategy": self.global_config.resource_allocation_strategy
                }
            },
            "projects": {
                name: {
                    "status": orch.status.value,
                    "pid": orch.pid,
                    "uptime_seconds": (datetime.utcnow() - orch.start_time).total_seconds() if orch.start_time else 0,
                    "cpu_usage": orch.cpu_usage,
                    "memory_usage": orch.memory_usage,
                    "active_agents": orch.active_agents,
                    "current_sprint": orch.current_sprint,
                    "backlog_size": orch.backlog_size,
                    "error_count": orch.error_count,
                    "restart_count": orch.restart_count
                }
                for name, orch in self.orchestrators.items()
            },
            "resource_allocations": {
                name: {
                    "allocated_agents": alloc.allocated_agents,
                    "allocated_memory_mb": alloc.allocated_memory_mb,
                    "allocated_cpu_percent": alloc.allocated_cpu_percent,
                    "priority_weight": alloc.priority_weight
                }
                for name, alloc in self.resource_allocations.items()
            },
            "global_metrics": {
                "total_projects": self.metrics.total_projects,
                "active_projects": self.metrics.active_projects,
                "total_agents": self.metrics.total_agents,
                "total_memory_usage_mb": self.metrics.total_memory_usage_mb,
                "total_cpu_usage_percent": self.metrics.total_cpu_usage_percent,
                "total_stories_in_progress": self.metrics.total_stories_in_progress,
                "total_stories_completed": self.metrics.total_stories_completed,
                "average_cycle_time_hours": self.metrics.average_cycle_time_hours,
                "cross_project_insights": self.metrics.cross_project_insights,
                "resource_efficiency": self.metrics.resource_efficiency
            },
            "cross_project_insights": self.cross_project_insights[-10:],  # Last 10 insights
            "shared_patterns": len(self.shared_patterns)
        }
    
    # Private methods for background operations
    
    async def _start_active_projects(self) -> None:
        """Start orchestrators for all active projects"""
        active_projects = self.config_manager.get_active_projects()
        
        for project in active_projects:
            try:
                await self.start_project(project.name)
            except Exception as e:
                logger.error(f"Failed to start project '{project.name}': {str(e)}")
    
    async def _stop_all_projects(self) -> None:
        """Stop all running project orchestrators"""
        stop_tasks = []
        for project_name in list(self.orchestrators.keys()):
            stop_tasks.append(asyncio.create_task(self.stop_project(project_name)))
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        logger.info("Started global monitoring loop")
        
        while self.status in [OrchestratorStatus.RUNNING, OrchestratorStatus.PAUSED]:
            try:
                await self._update_orchestrator_status()
                await self._collect_metrics()
                await self._detect_cross_project_patterns()
                await asyncio.sleep(self.global_config.scheduling_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(self.global_config.scheduling_interval_seconds * 2)
    
    async def _scheduling_loop(self) -> None:
        """Background scheduling and coordination loop"""
        logger.info("Started global scheduling loop")
        
        while self.status in [OrchestratorStatus.RUNNING, OrchestratorStatus.PAUSED]:
            try:
                await self._optimize_project_scheduling()
                await self._handle_project_dependencies()
                await asyncio.sleep(self.global_config.scheduling_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduling loop error: {str(e)}")
    
    async def _resource_balancing_loop(self) -> None:
        """Background resource balancing loop"""
        logger.info("Started resource balancing loop")
        
        while self.status in [OrchestratorStatus.RUNNING, OrchestratorStatus.PAUSED]:
            try:
                await self._rebalance_resources()
                await asyncio.sleep(self.global_config.resource_rebalance_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource balancing error: {str(e)}")
    
    async def _health_check_loop(self) -> None:
        """Background health check loop"""
        logger.info("Started health check loop")
        
        while self.status in [OrchestratorStatus.RUNNING, OrchestratorStatus.PAUSED]:
            try:
                await self._check_orchestrator_health()
                await self._restart_failed_orchestrators()
                await asyncio.sleep(self.global_config.health_check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
    
    async def _calculate_resource_allocation(self, project_config: ProjectConfig) -> ResourceAllocation:
        """Calculate resource allocation for a project"""
        # Priority-based allocation
        priority_weights = {
            ProjectPriority.CRITICAL: 2.0,
            ProjectPriority.HIGH: 1.5,
            ProjectPriority.NORMAL: 1.0,
            ProjectPriority.LOW: 0.5
        }
        
        priority_weight = priority_weights.get(project_config.priority, 1.0)
        
        # Calculate base allocation
        total_active = len(self.config_manager.get_active_projects())
        
        if self.global_config.resource_allocation_strategy == "fair_share":
            base_agents = self.global_config.max_total_agents // max(total_active, 1)
            base_memory = (self.global_config.global_memory_limit_gb * 1024) // max(total_active, 1)
            base_cpu = 100.0 / max(total_active, 1)
        else:  # priority_based
            total_weight = sum(priority_weights.get(p.priority, 1.0) for p in self.config_manager.get_active_projects())
            weight_ratio = priority_weight / max(total_weight, 1.0)
            base_agents = int(self.global_config.max_total_agents * weight_ratio)
            base_memory = int(self.global_config.global_memory_limit_gb * 1024 * weight_ratio)
            base_cpu = 100.0 * weight_ratio
        
        # Apply project-specific limits
        allocated_agents = min(base_agents, project_config.resource_limits.max_parallel_agents)
        allocated_memory = min(base_memory, project_config.resource_limits.max_memory_mb)
        allocated_cpu = min(base_cpu, 100.0) * project_config.resource_limits.cpu_priority
        
        return ResourceAllocation(
            project_name=project_config.name,
            allocated_agents=allocated_agents,
            allocated_memory_mb=allocated_memory,
            allocated_cpu_percent=allocated_cpu,
            priority_weight=priority_weight
        )
    
    async def _prepare_orchestrator_command(
        self,
        project_config: ProjectConfig,
        allocation: ResourceAllocation
    ) -> List[str]:
        """Prepare command to start project orchestrator"""
        # This would be the command to start the existing orchestrator.py
        # with project-specific parameters
        return [
            "python3", "scripts/orchestrator.py",
            "--project-mode",
            "--max-agents", str(allocation.allocated_agents),
            "--memory-limit", str(allocation.allocated_memory_mb),
            "--project-name", project_config.name
        ]
    
    async def _prepare_project_environment(
        self,
        project_config: ProjectConfig,
        allocation: ResourceAllocation
    ) -> Dict[str, str]:
        """Prepare environment variables for project orchestrator"""
        env = os.environ.copy()
        
        # Set project-specific environment
        env.update({
            "ORCH_PROJECT_NAME": project_config.name,
            "ORCH_PROJECT_PATH": project_config.path,
            "ORCH_MAX_AGENTS": str(allocation.allocated_agents),
            "ORCH_MEMORY_LIMIT": str(allocation.allocated_memory_mb),
            "ORCH_CPU_LIMIT": str(allocation.allocated_cpu_percent),
            "ORCH_GLOBAL_MODE": "true"
        })
        
        # Add Discord channel if configured
        if project_config.discord_channel:
            env["DISCORD_CHANNEL"] = project_config.discord_channel
        
        return env
    
    async def _wait_for_process_exit(self, process: subprocess.Popen) -> None:
        """Wait for process to exit"""
        while process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def _update_orchestrator_status(self) -> None:
        """Update status of all orchestrators"""
        for name, orchestrator in self.orchestrators.items():
            if orchestrator.process:
                if orchestrator.process.poll() is not None:
                    # Process has exited
                    if orchestrator.status == OrchestratorStatus.STOPPING:
                        orchestrator.status = OrchestratorStatus.STOPPED
                    else:
                        orchestrator.status = OrchestratorStatus.CRASHED
                        orchestrator.error_count += 1
                        logger.warning(f"Project orchestrator '{name}' crashed")
                else:
                    # Update resource usage if process is running
                    if orchestrator.pid and psutil:
                        try:
                            process = psutil.Process(orchestrator.pid)
                            orchestrator.cpu_usage = process.cpu_percent()
                            orchestrator.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                            orchestrator.last_heartbeat = datetime.utcnow()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    elif orchestrator.pid:
                        # Fallback when psutil is not available
                        orchestrator.last_heartbeat = datetime.utcnow()
    
    async def _collect_metrics(self) -> None:
        """Collect global metrics"""
        self.metrics.total_projects = len(self.config_manager.projects)
        self.metrics.active_projects = len([
            o for o in self.orchestrators.values()
            if o.status == OrchestratorStatus.RUNNING
        ])
        self.metrics.total_agents = sum(o.active_agents for o in self.orchestrators.values())
        self.metrics.total_memory_usage_mb = sum(o.memory_usage for o in self.orchestrators.values())
        self.metrics.total_cpu_usage_percent = sum(o.cpu_usage for o in self.orchestrators.values())
    
    async def _detect_cross_project_patterns(self) -> None:
        """Detect patterns that could be shared across projects"""
        # This would analyze patterns across projects and identify reusable insights
        # For now, this is a placeholder
        pass
    
    async def _optimize_project_scheduling(self) -> None:
        """Optimize scheduling across projects"""
        # This would implement intelligent scheduling based on dependencies and priorities
        pass
    
    async def _handle_project_dependencies(self) -> None:
        """Handle inter-project dependencies"""
        # This would coordinate projects that depend on each other
        pass
    
    async def _rebalance_resources(self) -> None:
        """Rebalance resources across projects"""
        # This would dynamically adjust resource allocations based on usage patterns
        pass
    
    async def _check_orchestrator_health(self) -> None:
        """Check health of all orchestrators"""
        current_time = datetime.utcnow()
        
        for name, orchestrator in self.orchestrators.items():
            if orchestrator.status == OrchestratorStatus.RUNNING:
                # Check for heartbeat timeout
                if orchestrator.last_heartbeat:
                    time_since_heartbeat = current_time - orchestrator.last_heartbeat
                    if time_since_heartbeat > timedelta(minutes=5):
                        logger.warning(f"No heartbeat from project '{name}' for {time_since_heartbeat}")
    
    async def _restart_failed_orchestrators(self) -> None:
        """Restart orchestrators that have failed"""
        for name, orchestrator in self.orchestrators.items():
            if orchestrator.status == OrchestratorStatus.CRASHED:
                if orchestrator.restart_count < 3:  # Max 3 restart attempts
                    logger.info(f"Attempting to restart crashed orchestrator for '{name}'")
                    orchestrator.restart_count += 1
                    await self.stop_project(name)
                    await asyncio.sleep(5)  # Wait before restart
                    await self.start_project(name)
    
    async def _start_discord_bot(self) -> None:
        """Start Discord bot for multi-project interface"""
        # This would start an enhanced Discord bot that handles multiple projects
        # For now, this is a placeholder
        pass
    
    async def _update_metrics(self) -> None:
        """Update all metrics"""
        await self._collect_metrics()
        # Additional metric calculations would go here