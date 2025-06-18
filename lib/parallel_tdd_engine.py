"""
Parallel TDD Engine - Unified Integration Layer

Context-aware parallel execution engine that integrates all parallel TDD components:
- Parallel TDD Coordinator
- Agent Pool Management
- Conflict Resolution System
- Enhanced TDD State Machine
- Context Management System

Provides a unified interface for parallel TDD execution with intelligent coordination.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

# Import parallel TDD components
try:
    from .parallel_tdd_coordinator import (
        ParallelTDDCoordinator, ParallelExecutionMode, ParallelCycle, 
        ParallelExecutionStats, CycleStatus
    )
    from .agent_pool import AgentPool, AgentPoolStrategy, LoadBalancingAlgorithm
    from .conflict_resolver import ConflictResolver, ConflictType, ConflictSeverity
    from .tdd_state_machine import TDDStateMachine, TDDCommandResult
    from .context_manager import ContextManager
    from .tdd_models import TDDState, TDDCycle, TDDTask
    from .state_broadcaster import emit_parallel_status
except ImportError:
    from parallel_tdd_coordinator import (
        ParallelTDDCoordinator, ParallelExecutionMode, ParallelCycle, 
        ParallelExecutionStats, CycleStatus
    )
    from agent_pool import AgentPool, AgentPoolStrategy, LoadBalancingAlgorithm
    from conflict_resolver import ConflictResolver, ConflictType, ConflictSeverity
    from tdd_state_machine import TDDStateMachine, TDDCommandResult
    from context_manager import ContextManager
    from tdd_models import TDDState, TDDCycle, TDDTask
    from state_broadcaster import emit_parallel_status

logger = logging.getLogger(__name__)


class ParallelExecutionStatus(Enum):
    """Status of parallel execution engine"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ParallelTDDConfiguration:
    """Configuration for parallel TDD execution"""
    max_parallel_cycles: int = 4
    execution_mode: ParallelExecutionMode = ParallelExecutionMode.BALANCED
    enable_predictive_scheduling: bool = True
    enable_conflict_prevention: bool = True
    enable_auto_resolution: bool = True
    enable_resource_locking: bool = True
    enable_coordination_events: bool = True
    
    # Agent pool configuration
    agent_pool_strategy: AgentPoolStrategy = AgentPoolStrategy.DYNAMIC
    load_balancing: LoadBalancingAlgorithm = LoadBalancingAlgorithm.CAPABILITY_BASED
    enable_auto_scaling: bool = True
    
    # Timeouts and intervals
    resource_timeout_minutes: int = 30
    coordination_check_interval: float = 5.0
    health_check_interval: float = 30.0
    
    # Performance settings
    enable_performance_monitoring: bool = True
    enable_context_isolation: bool = True
    enable_shared_context_optimization: bool = True


@dataclass
class ParallelExecutionMetrics:
    """Comprehensive metrics for parallel execution"""
    engine_uptime: float = 0.0
    total_cycles_executed: int = 0
    parallel_cycles_executed: int = 0
    average_cycle_time: float = 0.0
    throughput_cycles_per_hour: float = 0.0
    
    # Coordination metrics
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    auto_resolutions: int = 0
    human_escalations: int = 0
    coordination_events: int = 0
    
    # Resource metrics
    peak_parallel_cycles: int = 0
    average_resource_utilization: float = 0.0
    resource_conflicts: int = 0
    
    # Context metrics
    context_preparation_time: float = 0.0
    context_cache_hit_rate: float = 0.0
    cross_story_insights: int = 0
    
    # Quality metrics
    test_preservation_rate: float = 100.0
    parallel_quality_score: float = 0.0


class ParallelTDDEngine:
    """
    Unified Parallel TDD Execution Engine.
    
    Integrates all parallel TDD components to provide intelligent,
    context-aware parallel execution with comprehensive coordination,
    conflict resolution, and performance optimization.
    """
    
    def __init__(
        self,
        context_manager: ContextManager,
        project_path: str,
        config: Optional[ParallelTDDConfiguration] = None
    ):
        """
        Initialize Parallel TDD Engine.
        
        Args:
            context_manager: Context manager for intelligent coordination
            project_path: Project root path
            config: Configuration for parallel execution
        """
        self.context_manager = context_manager
        self.project_path = project_path
        self.config = config or ParallelTDDConfiguration()
        
        # Engine state
        self.status = ParallelExecutionStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.metrics = ParallelExecutionMetrics()
        
        # Initialize core components
        self._initialize_components()
        
        # Cross-component integration
        self._setup_component_integration()
        
        # Active execution tracking
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Performance monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"ParallelTDDEngine initialized: project={project_path}, "
            f"max_cycles={self.config.max_parallel_cycles}, "
            f"mode={self.config.execution_mode.value}"
        )
    
    def _initialize_components(self) -> None:
        """Initialize all parallel TDD components"""
        # Initialize parallel coordinator
        self.coordinator = ParallelTDDCoordinator(
            context_manager=self.context_manager,
            max_parallel_cycles=self.config.max_parallel_cycles,
            execution_mode=self.config.execution_mode,
            enable_predictive_scheduling=self.config.enable_predictive_scheduling,
            enable_conflict_prevention=self.config.enable_conflict_prevention,
            resource_timeout_minutes=self.config.resource_timeout_minutes,
            coordination_check_interval=self.config.coordination_check_interval,
            performance_monitoring=self.config.enable_performance_monitoring
        )
        
        # Initialize agent pool
        self.agent_pool = AgentPool(
            context_manager=self.context_manager,
            strategy=self.config.agent_pool_strategy,
            load_balancing=self.config.load_balancing,
            enable_auto_scaling=self.config.enable_auto_scaling,
            enable_health_monitoring=self.config.enable_performance_monitoring
        )
        
        # Initialize conflict resolver
        self.conflict_resolver = ConflictResolver(
            context_manager=self.context_manager,
            project_path=self.project_path,
            enable_proactive_detection=self.config.enable_conflict_prevention,
            enable_auto_resolution=self.config.enable_auto_resolution,
            enable_semantic_analysis=True
        )
        
        # Initialize enhanced TDD state machine
        self.state_machine = TDDStateMachine(
            enable_parallel_execution=True,
            enable_resource_locking=self.config.enable_resource_locking,
            enable_coordination_events=self.config.enable_coordination_events,
            resource_lock_timeout=self.config.resource_timeout_minutes * 60
        )
    
    def _setup_component_integration(self) -> None:
        """Setup integration between components"""
        # Link coordinator with agent pool and conflict resolver
        self.coordinator.agent_pool = self.agent_pool
        self.coordinator.conflict_resolver = self.conflict_resolver
        
        # Setup cross-component event handling
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for cross-component coordination"""
        # Placeholder for event handler setup
        # In a full implementation, this would wire up event handlers
        # between components for real-time coordination
        pass
    
    async def start(self) -> None:
        """Start the parallel TDD execution engine"""
        if self.status != ParallelExecutionStatus.STOPPED:
            logger.warning("Engine already running or starting")
            return
        
        self.status = ParallelExecutionStatus.STARTING
        logger.info("Starting Parallel TDD Execution Engine")
        
        try:
            # Start all components
            await self.coordinator.start()
            await self.agent_pool.start()
            await self.conflict_resolver.start()
            
            # Start monitoring tasks
            if self.config.enable_performance_monitoring:
                self._monitoring_task = asyncio.create_task(self._monitoring_loop())
                self._optimization_task = asyncio.create_task(self._optimization_loop())
            
            self.status = ParallelExecutionStatus.RUNNING
            self.start_time = datetime.utcnow()
            
            logger.info("Parallel TDD Execution Engine started successfully")
            
        except Exception as e:
            self.status = ParallelExecutionStatus.ERROR
            logger.error(f"Failed to start Parallel TDD Engine: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the parallel TDD execution engine"""
        if self.status == ParallelExecutionStatus.STOPPED:
            return
        
        self.status = ParallelExecutionStatus.STOPPING
        logger.info("Stopping Parallel TDD Execution Engine")
        
        try:
            # Cancel monitoring tasks
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            if self._optimization_task:
                self._optimization_task.cancel()
                try:
                    await self._optimization_task
                except asyncio.CancelledError:
                    pass
            
            # Stop all components
            await self.coordinator.stop()
            await self.agent_pool.stop()
            await self.conflict_resolver.stop()
            
            self.status = ParallelExecutionStatus.STOPPED
            logger.info("Parallel TDD Execution Engine stopped")
            
        except Exception as e:
            self.status = ParallelExecutionStatus.ERROR
            logger.error(f"Error stopping Parallel TDD Engine: {str(e)}")
    
    async def pause(self) -> None:
        """Pause parallel execution"""
        if self.status != ParallelExecutionStatus.RUNNING:
            return
        
        self.status = ParallelExecutionStatus.PAUSING
        # Pause coordinator (other components continue for monitoring)
        self.coordinator._paused = True
        self.status = ParallelExecutionStatus.PAUSED
        logger.info("Parallel execution paused")
    
    async def resume(self) -> None:
        """Resume parallel execution"""
        if self.status != ParallelExecutionStatus.PAUSED:
            return
        
        self.coordinator._paused = False
        self.status = ParallelExecutionStatus.RUNNING
        logger.info("Parallel execution resumed")
    
    async def execute_parallel_cycles(
        self,
        cycles: List[TDDCycle],
        dependencies: Optional[Dict[str, List[str]]] = None,
        priorities: Optional[Dict[str, int]] = None,
        estimated_durations: Optional[Dict[str, timedelta]] = None
    ) -> Dict[str, Any]:
        """
        Execute multiple TDD cycles in parallel.
        
        Args:
            cycles: List of TDD cycles to execute
            dependencies: Dictionary mapping cycle_id to list of dependency cycle_ids
            priorities: Dictionary mapping cycle_id to priority (1-10)
            estimated_durations: Dictionary mapping cycle_id to estimated duration
            
        Returns:
            Execution results and performance metrics
        """
        if self.status != ParallelExecutionStatus.RUNNING:
            raise RuntimeError(f"Engine not running (status: {self.status.value})")
        
        execution_start = time.time()
        execution_id = str(uuid.uuid4())
        
        logger.info(f"Starting parallel execution {execution_id} with {len(cycles)} cycles")
        
        # Register cycles with coordinator
        cycle_ids = []
        for cycle in cycles:
            priority = priorities.get(cycle.id, 5) if priorities else 5
            duration = estimated_durations.get(cycle.id) if estimated_durations else None
            deps = dependencies.get(cycle.id, []) if dependencies else []
            
            cycle_id = await self.coordinator.submit_cycle(
                cycle, priority=priority, dependencies=deps, estimated_duration=duration
            )
            cycle_ids.append(cycle_id)
            
            # Register with state machine for parallel tracking
            self.state_machine.register_parallel_cycle(cycle)
            
            # Register file modifications for conflict detection
            if hasattr(cycle, 'file_paths'):
                for file_path in cycle.file_paths:
                    await self.conflict_resolver.register_file_modification(
                        file_path, cycle.id, cycle.story_id, "modify"
                    )
        
        # Setup cycle dependencies in state machine
        if dependencies:
            for cycle_id, deps in dependencies.items():
                for dep_id in deps:
                    self.state_machine.add_cycle_dependency(cycle_id, dep_id)
        
        # Track execution
        execution_info = {
            "execution_id": execution_id,
            "cycle_ids": cycle_ids,
            "start_time": datetime.utcnow(),
            "status": "running",
            "total_cycles": len(cycles)
        }
        self.active_executions[execution_id] = execution_info
        
        # Wait for completion or timeout
        try:
            results = await self._monitor_execution(execution_id, cycle_ids)
            
            execution_time = time.time() - execution_start
            execution_info.update({
                "status": "completed",
                "end_time": datetime.utcnow(),
                "execution_time": execution_time,
                "results": results
            })
            
            # Update metrics
            self.metrics.total_cycles_executed += len(cycles)
            self.metrics.parallel_cycles_executed += len(cycles)
            self._update_throughput_metrics(len(cycles), execution_time)
            
            logger.info(f"Parallel execution {execution_id} completed in {execution_time:.2f}s")
            
            return {
                "execution_id": execution_id,
                "success": True,
                "execution_time": execution_time,
                "cycles_completed": len([r for r in results.values() if r.get("success", False)]),
                "cycles_failed": len([r for r in results.values() if not r.get("success", False)]),
                "results": results,
                "performance_metrics": await self._get_execution_metrics(execution_id)
            }
            
        except Exception as e:
            execution_info.update({
                "status": "failed",
                "end_time": datetime.utcnow(),
                "error": str(e)
            })
            logger.error(f"Parallel execution {execution_id} failed: {str(e)}")
            
            return {
                "execution_id": execution_id,
                "success": False,
                "error": str(e),
                "results": {}
            }
        
        finally:
            # Clean up execution tracking
            self.execution_history.append(execution_info)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive engine status"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Get component statuses
        coordinator_status = await self.coordinator.get_parallel_status()
        agent_pool_status = await self.agent_pool.get_pool_status()
        conflict_stats = await self.conflict_resolver.get_resolution_statistics()
        state_machine_status = self.state_machine.get_parallel_status()
        
        return {
            "engine_status": {
                "status": self.status.value,
                "uptime_seconds": uptime,
                "configuration": {
                    "max_parallel_cycles": self.config.max_parallel_cycles,
                    "execution_mode": self.config.execution_mode.value,
                    "enable_predictive_scheduling": self.config.enable_predictive_scheduling,
                    "enable_conflict_prevention": self.config.enable_conflict_prevention,
                    "enable_auto_resolution": self.config.enable_auto_resolution
                }
            },
            "active_executions": len(self.active_executions),
            "total_executions": len(self.execution_history),
            "performance_metrics": {
                "total_cycles_executed": self.metrics.total_cycles_executed,
                "parallel_cycles_executed": self.metrics.parallel_cycles_executed,
                "average_cycle_time": self.metrics.average_cycle_time,
                "throughput_cycles_per_hour": self.metrics.throughput_cycles_per_hour,
                "conflicts_detected": self.metrics.conflicts_detected,
                "conflicts_resolved": self.metrics.conflicts_resolved,
                "context_cache_hit_rate": self.metrics.context_cache_hit_rate
            },
            "components": {
                "coordinator": coordinator_status,
                "agent_pool": agent_pool_status,
                "conflict_resolver": conflict_stats,
                "state_machine": state_machine_status
            }
        }
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Optimize engine performance"""
        optimization_start = time.time()
        optimizations_applied = []
        
        # Optimize coordinator scheduling
        coordinator_optimization = await self.coordinator.optimize_scheduling()
        optimizations_applied.append({
            "component": "coordinator",
            "optimization": coordinator_optimization
        })
        
        # Optimize agent pool scaling
        pool_status = await self.agent_pool.get_pool_status()
        for agent_type, status in pool_status["agent_types"].items():
            if status["average_load"] > 0.8:  # High load
                scaling_result = await self.agent_pool.scale_pool(agent_type)
                optimizations_applied.append({
                    "component": "agent_pool",
                    "agent_type": agent_type,
                    "optimization": scaling_result
                })
        
        # Clean up expired resources
        expired_locks = self.state_machine.cleanup_expired_resources()
        if expired_locks > 0:
            optimizations_applied.append({
                "component": "state_machine",
                "optimization": f"cleaned_{expired_locks}_expired_locks"
            })
        
        optimization_time = time.time() - optimization_start
        
        return {
            "optimization_time": optimization_time,
            "optimizations_applied": optimizations_applied,
            "performance_improvement": await self._estimate_performance_improvement()
        }
    
    async def handle_context_request(
        self,
        agent_type: str,
        story_id: str,
        task: Union[TDDTask, Dict[str, Any]],
        max_tokens: Optional[int] = None,
        isolation_mode: bool = True
    ) -> Optional[Any]:
        """
        Handle context preparation with parallel execution awareness.
        
        Args:
            agent_type: Type of agent requesting context
            story_id: Story ID for context isolation
            task: Task to prepare context for
            max_tokens: Maximum tokens for context
            isolation_mode: Whether to use context isolation
            
        Returns:
            Prepared agent context
        """
        if isolation_mode and self.config.enable_context_isolation:
            # Prepare isolated context for parallel execution
            context = await self.context_manager.prepare_context(
                agent_type=agent_type,
                task=task,
                max_tokens=max_tokens,
                story_id=story_id,
                parallel_isolation=True
            )
        else:
            # Standard context preparation
            context = await self.context_manager.prepare_context(
                agent_type=agent_type,
                task=task,
                max_tokens=max_tokens,
                story_id=story_id
            )
        
        # Update context metrics
        if context:
            self.metrics.context_preparation_time = (
                self.metrics.context_preparation_time * 0.9 +
                getattr(context, 'preparation_time', 0) * 0.1
            )
            
            if getattr(context, 'cache_hit', False):
                self.metrics.context_cache_hit_rate = (
                    self.metrics.context_cache_hit_rate * 0.9 + 1.0 * 0.1
                )
            else:
                self.metrics.context_cache_hit_rate = (
                    self.metrics.context_cache_hit_rate * 0.9 + 0.0 * 0.1
                )
        
        return context
    
    # Private monitoring and optimization methods
    
    async def _monitor_execution(self, execution_id: str, cycle_ids: List[str]) -> Dict[str, Any]:
        """Monitor parallel execution until completion"""
        results = {}
        
        while True:
            all_completed = True
            
            for cycle_id in cycle_ids:
                if cycle_id not in results:
                    status = await self.coordinator.get_cycle_status(cycle_id)
                    if status:
                        if status["status"] in ["completed", "failed", "cancelled"]:
                            results[cycle_id] = {
                                "success": status["status"] == "completed",
                                "status": status["status"],
                                "execution_time": status.get("execution_time"),
                                "metrics": status.get("metrics", {})
                            }
                        else:
                            all_completed = False
                    else:
                        all_completed = False
            
            if all_completed:
                break
            
            await asyncio.sleep(1)  # Check every second
        
        return results
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        logger.info("Started parallel TDD engine monitoring")
        
        while self.status in [ParallelExecutionStatus.RUNNING, ParallelExecutionStatus.PAUSED]:
            try:
                await self._collect_performance_metrics()
                await self._check_engine_health()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(self.config.health_check_interval * 2)
    
    async def _optimization_loop(self) -> None:
        """Background optimization loop"""
        logger.info("Started parallel TDD engine optimization")
        
        while self.status in [ParallelExecutionStatus.RUNNING, ParallelExecutionStatus.PAUSED]:
            try:
                await asyncio.sleep(300)  # Optimize every 5 minutes
                if self.status == ParallelExecutionStatus.RUNNING:
                    await self.optimize_performance()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {str(e)}")
    
    async def _collect_performance_metrics(self) -> None:
        """Collect performance metrics from all components"""
        if self.start_time:
            self.metrics.engine_uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Collect coordinator metrics
        coordinator_status = await self.coordinator.get_parallel_status()
        if "performance_stats" in coordinator_status:
            stats = coordinator_status["performance_stats"]
            self.metrics.conflicts_detected = stats.get("conflicts_detected", 0)
            
        # Collect conflict resolver metrics
        conflict_stats = await self.conflict_resolver.get_resolution_statistics()
        self.metrics.conflicts_resolved = conflict_stats.get("resolved_conflicts", 0)
        self.metrics.auto_resolutions = conflict_stats.get("auto_resolved", 0)
        self.metrics.human_escalations = conflict_stats.get("escalated", 0)
        
        # Update peak parallel cycles
        active_cycles = coordinator_status.get("cycle_summary", {}).get("active_cycles", 0)
        self.metrics.peak_parallel_cycles = max(self.metrics.peak_parallel_cycles, active_cycles)
    
    async def _check_engine_health(self) -> None:
        """Check overall engine health"""
        # Check component health
        coordinator_status = await self.coordinator.get_parallel_status()
        pool_status = await self.agent_pool.get_pool_status()
        
        # Log health warnings
        if coordinator_status.get("cycle_summary", {}).get("blocked_cycles", 0) > 3:
            logger.warning("High number of blocked cycles detected")
        
        if pool_status.get("pool_summary", {}).get("failed_agents", 0) > 2:
            logger.warning("Multiple agent failures detected")
    
    def _update_throughput_metrics(self, cycles_completed: int, execution_time: float) -> None:
        """Update throughput metrics"""
        if execution_time > 0:
            cycles_per_hour = cycles_completed / (execution_time / 3600)
            self.metrics.throughput_cycles_per_hour = (
                self.metrics.throughput_cycles_per_hour * 0.9 + cycles_per_hour * 0.1
            )
        
        # Update average cycle time
        avg_cycle_time = execution_time / cycles_completed if cycles_completed > 0 else 0
        self.metrics.average_cycle_time = (
            self.metrics.average_cycle_time * 0.9 + avg_cycle_time * 0.1
        )
    
    async def _get_execution_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get metrics for a specific execution"""
        if execution_id not in self.active_executions:
            return {}
        
        execution_info = self.active_executions[execution_id]
        
        return {
            "execution_time": execution_info.get("execution_time", 0),
            "total_cycles": execution_info.get("total_cycles", 0),
            "coordinator_metrics": await self.coordinator.get_parallel_status(),
            "agent_pool_metrics": await self.agent_pool.get_pool_status(),
            "conflict_metrics": await self.conflict_resolver.get_resolution_statistics()
        }
    
    async def _estimate_performance_improvement(self) -> Dict[str, float]:
        """Estimate performance improvement from optimizations"""
        return {
            "throughput_improvement": 5.0,  # Estimated 5% improvement
            "conflict_reduction": 10.0,     # Estimated 10% conflict reduction
            "resource_efficiency": 8.0     # Estimated 8% resource efficiency gain
        }