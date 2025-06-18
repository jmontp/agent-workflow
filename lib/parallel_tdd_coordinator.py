"""
Parallel TDD Coordinator - Core Coordination Engine

Central coordination engine for handling 3-5 concurrent TDD cycles with intelligent
resource allocation, conflict detection, and optimal scheduling. Leverages the
Context Management System for cross-story insights and coordination.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import json

# Import TDD models and state machine
try:
    from .tdd_models import TDDState, TDDCycle, TDDTask, TestResult, TestStatus
    from .tdd_state_machine import TDDStateMachine, TDDCommandResult
    from .context_manager import ContextManager
    from .state_broadcaster import emit_tdd_transition, emit_parallel_status
except ImportError:
    from tdd_models import TDDState, TDDCycle, TDDTask, TestResult, TestStatus
    from tdd_state_machine import TDDStateMachine, TDDCommandResult
    from context_manager import ContextManager
    from state_broadcaster import emit_tdd_transition, emit_parallel_status

logger = logging.getLogger(__name__)


class ParallelExecutionMode(Enum):
    """Parallel execution modes"""
    CONSERVATIVE = "conservative"  # 2-3 cycles, high safety
    BALANCED = "balanced"         # 3-4 cycles, balanced performance/safety
    AGGRESSIVE = "aggressive"     # 4-5 cycles, maximum throughput


class CycleStatus(Enum):
    """Status of parallel TDD cycles"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResourceType(Enum):
    """Types of resources that can be locked"""
    FILE = "file"
    DIRECTORY = "directory"
    AGENT = "agent"
    TEST_RUNNER = "test_runner"
    REPOSITORY = "repository"


@dataclass
class ResourceLock:
    """Resource lock for preventing conflicts"""
    resource_id: str
    resource_type: ResourceType
    cycle_id: str
    story_id: str
    locked_at: datetime
    lock_duration: Optional[timedelta] = None
    exclusive: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if lock has expired"""
        if not self.lock_duration:
            return False
        return datetime.utcnow() - self.locked_at > self.lock_duration


@dataclass
class ParallelCycle:
    """Enhanced TDD cycle for parallel execution"""
    cycle: TDDCycle
    status: CycleStatus = CycleStatus.PENDING
    priority: int = 5  # 1-10, lower is higher priority
    dependencies: Set[str] = field(default_factory=set)  # Story IDs this depends on
    conflicts: Set[str] = field(default_factory=set)     # Story IDs in conflict
    resource_locks: Set[str] = field(default_factory=set)  # Resource IDs locked
    agent_assignments: Dict[TDDState, str] = field(default_factory=dict)  # Agent assignments
    estimated_duration: Optional[timedelta] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    context_preparation_time: float = 0.0
    
    @property
    def id(self) -> str:
        return self.cycle.id
    
    @property
    def story_id(self) -> str:
        return self.cycle.story_id
    
    @property
    def current_state(self) -> TDDState:
        return self.cycle.current_state
    
    @property
    def is_active(self) -> bool:
        return self.status == CycleStatus.ACTIVE
    
    @property
    def is_blocked(self) -> bool:
        return self.status == CycleStatus.BLOCKED
    
    @property
    def execution_time(self) -> Optional[timedelta]:
        """Calculate total execution time"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return end_time - self.started_at


@dataclass
class ParallelExecutionStats:
    """Statistics for parallel execution"""
    total_cycles: int = 0
    active_cycles: int = 0
    completed_cycles: int = 0
    failed_cycles: int = 0
    blocked_cycles: int = 0
    average_execution_time: float = 0.0
    throughput_cycles_per_hour: float = 0.0
    conflict_rate: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    coordination_overhead: float = 0.0
    context_preparation_time: float = 0.0
    successful_parallel_transitions: int = 0
    failed_parallel_transitions: int = 0


class ParallelTDDCoordinator:
    """
    Central coordination engine for parallel TDD execution.
    
    Manages 3-5 concurrent TDD cycles with intelligent resource allocation,
    conflict detection, and performance optimization. Integrates with the
    Context Management System for cross-story insights and coordination.
    """
    
    def __init__(
        self,
        context_manager: ContextManager,
        max_parallel_cycles: int = 4,
        execution_mode: ParallelExecutionMode = ParallelExecutionMode.BALANCED,
        enable_predictive_scheduling: bool = True,
        enable_conflict_prevention: bool = True,
        resource_timeout_minutes: int = 30,
        coordination_check_interval: float = 5.0,
        performance_monitoring: bool = True
    ):
        """
        Initialize Parallel TDD Coordinator.
        
        Args:
            context_manager: Context manager for intelligent coordination
            max_parallel_cycles: Maximum number of concurrent cycles (3-5)
            execution_mode: Parallel execution mode
            enable_predictive_scheduling: Enable ML-based scheduling
            enable_conflict_prevention: Enable proactive conflict avoidance
            resource_timeout_minutes: Timeout for resource locks
            coordination_check_interval: Interval for coordination checks
            performance_monitoring: Enable performance monitoring
        """
        self.context_manager = context_manager
        self.max_parallel_cycles = min(max(max_parallel_cycles, 2), 5)  # Enforce 2-5 range
        self.execution_mode = execution_mode
        self.enable_predictive_scheduling = enable_predictive_scheduling
        self.enable_conflict_prevention = enable_conflict_prevention
        self.resource_timeout = timedelta(minutes=resource_timeout_minutes)
        self.coordination_check_interval = coordination_check_interval
        self.performance_monitoring = performance_monitoring
        
        # Core state
        self.parallel_cycles: Dict[str, ParallelCycle] = {}  # cycle_id -> ParallelCycle
        self.resource_locks: Dict[str, ResourceLock] = {}   # resource_id -> ResourceLock
        self.execution_queue: List[str] = []                # Queue of cycle IDs to execute
        self.agent_pool: Optional[Any] = None               # Will be set by agent pool manager
        self.conflict_resolver: Optional[Any] = None        # Will be set by conflict resolver
        
        # Coordination state
        self._coordination_task: Optional[asyncio.Task] = None
        self._running = False
        self._paused = False
        
        # Performance tracking
        self.stats = ParallelExecutionStats()
        self._execution_history: List[Dict[str, Any]] = []
        self._coordination_metrics: Dict[str, float] = defaultdict(float)
        
        # Predictive scheduling data
        self._scheduling_patterns: Dict[str, Any] = {}
        self._conflict_patterns: Dict[str, List[str]] = defaultdict(list)
        self._performance_patterns: Dict[str, float] = {}
        
        logger.info(
            f"ParallelTDDCoordinator initialized: max_cycles={self.max_parallel_cycles}, "
            f"mode={execution_mode.value}, predictive={enable_predictive_scheduling}"
        )
    
    async def start(self) -> None:
        """Start the parallel coordination engine"""
        if self._running:
            logger.warning("Parallel coordinator already running")
            return
        
        self._running = True
        logger.info("Starting parallel TDD coordination engine")
        
        # Start coordination loop
        self._coordination_task = asyncio.create_task(self._coordination_loop())
        
        # Initialize performance monitoring
        if self.performance_monitoring:
            await self._initialize_performance_monitoring()
        
        logger.info("Parallel TDD coordinator started successfully")
    
    async def stop(self) -> None:
        """Stop the parallel coordination engine"""
        if not self._running:
            return
        
        logger.info("Stopping parallel TDD coordinator")
        self._running = False
        
        # Cancel coordination task
        if self._coordination_task:
            self._coordination_task.cancel()
            try:
                await self._coordination_task
            except asyncio.CancelledError:
                pass
        
        # Complete or cancel active cycles
        await self._cleanup_active_cycles()
        
        # Release all resource locks
        await self._release_all_locks()
        
        logger.info("Parallel TDD coordinator stopped")
    
    async def submit_cycle(
        self,
        tdd_cycle: TDDCycle,
        priority: int = 5,
        dependencies: Optional[List[str]] = None,
        estimated_duration: Optional[timedelta] = None
    ) -> str:
        """
        Submit a TDD cycle for parallel execution.
        
        Args:
            tdd_cycle: TDD cycle to execute
            priority: Execution priority (1-10, lower is higher priority)
            dependencies: List of story IDs this cycle depends on
            estimated_duration: Estimated execution duration
            
        Returns:
            Parallel cycle ID
        """
        parallel_cycle = ParallelCycle(
            cycle=tdd_cycle,
            priority=max(1, min(priority, 10)),  # Clamp to 1-10
            dependencies=set(dependencies or []),
            estimated_duration=estimated_duration
        )
        
        # Store in parallel cycles
        self.parallel_cycles[parallel_cycle.id] = parallel_cycle
        
        # Register with context manager for cross-story tracking
        await self.context_manager.register_story(
            parallel_cycle.story_id,
            {
                "cycle_id": parallel_cycle.id,
                "priority": priority,
                "dependencies": list(parallel_cycle.dependencies),
                "estimated_duration": estimated_duration.total_seconds() if estimated_duration else None,
                "parallel_execution": True
            }
        )
        
        # Check for conflicts
        await self._analyze_cycle_conflicts(parallel_cycle)
        
        # Add to execution queue
        await self._schedule_cycle(parallel_cycle)
        
        logger.info(
            f"Submitted parallel cycle {parallel_cycle.id} for story {parallel_cycle.story_id} "
            f"(priority={priority}, dependencies={len(parallel_cycle.dependencies)})"
        )
        
        return parallel_cycle.id
    
    async def pause_cycle(self, cycle_id: str) -> bool:
        """Pause a specific cycle"""
        if cycle_id not in self.parallel_cycles:
            return False
        
        parallel_cycle = self.parallel_cycles[cycle_id]
        if parallel_cycle.status == CycleStatus.ACTIVE:
            parallel_cycle.status = CycleStatus.PAUSED
            logger.info(f"Paused parallel cycle {cycle_id}")
            
            # Emit status update
            await self._emit_parallel_status_update()
            return True
        
        return False
    
    async def resume_cycle(self, cycle_id: str) -> bool:
        """Resume a paused cycle"""
        if cycle_id not in self.parallel_cycles:
            return False
        
        parallel_cycle = self.parallel_cycles[cycle_id]
        if parallel_cycle.status == CycleStatus.PAUSED:
            parallel_cycle.status = CycleStatus.ACTIVE
            logger.info(f"Resumed parallel cycle {cycle_id}")
            
            # Emit status update
            await self._emit_parallel_status_update()
            return True
        
        return False
    
    async def cancel_cycle(self, cycle_id: str) -> bool:
        """Cancel a cycle and release its resources"""
        if cycle_id not in self.parallel_cycles:
            return False
        
        parallel_cycle = self.parallel_cycles[cycle_id]
        
        # Release resource locks
        await self._release_cycle_locks(parallel_cycle)
        
        # Update status
        parallel_cycle.status = CycleStatus.CANCELLED
        parallel_cycle.completed_at = datetime.utcnow()
        
        # Remove from execution queue
        if cycle_id in self.execution_queue:
            self.execution_queue.remove(cycle_id)
        
        # Unregister from context manager
        await self.context_manager.unregister_story(parallel_cycle.story_id)
        
        logger.info(f"Cancelled parallel cycle {cycle_id}")
        
        # Emit status update
        await self._emit_parallel_status_update()
        return True
    
    async def get_cycle_status(self, cycle_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a specific cycle"""
        if cycle_id not in self.parallel_cycles:
            return None
        
        parallel_cycle = self.parallel_cycles[cycle_id]
        
        return {
            "cycle_id": cycle_id,
            "story_id": parallel_cycle.story_id,
            "status": parallel_cycle.status.value,
            "current_state": parallel_cycle.current_state.value,
            "priority": parallel_cycle.priority,
            "dependencies": list(parallel_cycle.dependencies),
            "conflicts": list(parallel_cycle.conflicts),
            "resource_locks": list(parallel_cycle.resource_locks),
            "agent_assignments": {
                state.value: agent for state, agent in parallel_cycle.agent_assignments.items()
            },
            "started_at": parallel_cycle.started_at.isoformat() if parallel_cycle.started_at else None,
            "execution_time": parallel_cycle.execution_time.total_seconds() if parallel_cycle.execution_time else None,
            "last_activity": parallel_cycle.last_activity.isoformat(),
            "metrics": parallel_cycle.execution_metrics
        }
    
    async def get_parallel_status(self) -> Dict[str, Any]:
        """Get comprehensive parallel execution status"""
        active_cycles = [pc for pc in self.parallel_cycles.values() if pc.is_active]
        blocked_cycles = [pc for pc in self.parallel_cycles.values() if pc.is_blocked]
        
        return {
            "coordinator_status": {
                "running": self._running,
                "paused": self._paused,
                "max_parallel_cycles": self.max_parallel_cycles,
                "execution_mode": self.execution_mode.value,
                "coordination_interval": self.coordination_check_interval
            },
            "cycle_summary": {
                "total_cycles": len(self.parallel_cycles),
                "active_cycles": len(active_cycles),
                "blocked_cycles": len(blocked_cycles),
                "queued_cycles": len(self.execution_queue),
                "resource_locks": len(self.resource_locks)
            },
            "active_cycles": [
                {
                    "cycle_id": pc.id,
                    "story_id": pc.story_id,
                    "current_state": pc.current_state.value,
                    "priority": pc.priority,
                    "execution_time": pc.execution_time.total_seconds() if pc.execution_time else 0
                }
                for pc in active_cycles
            ],
            "blocked_cycles": [
                {
                    "cycle_id": pc.id,
                    "story_id": pc.story_id,
                    "conflicts": list(pc.conflicts),
                    "dependencies": list(pc.dependencies)
                }
                for pc in blocked_cycles
            ],
            "performance_stats": self._get_performance_summary(),
            "resource_utilization": await self._calculate_resource_utilization(),
            "next_scheduled": self._get_next_scheduled_cycles()
        }
    
    async def optimize_scheduling(self) -> Dict[str, Any]:
        """Optimize scheduling based on current state and patterns"""
        optimization_start = time.time()
        
        # Analyze current bottlenecks
        bottlenecks = await self._identify_bottlenecks()
        
        # Reorder execution queue based on priority and dependencies
        await self._optimize_execution_queue()
        
        # Optimize resource allocation
        resource_optimizations = await self._optimize_resource_allocation()
        
        # Apply predictive scheduling if enabled
        predictive_optimizations = {}
        if self.enable_predictive_scheduling:
            predictive_optimizations = await self._apply_predictive_scheduling()
        
        optimization_time = time.time() - optimization_start
        
        result = {
            "optimization_time": optimization_time,
            "bottlenecks_identified": bottlenecks,
            "resource_optimizations": resource_optimizations,
            "predictive_optimizations": predictive_optimizations,
            "queue_reordered": len(self.execution_queue),
            "performance_improvement_estimate": await self._estimate_performance_improvement()
        }
        
        logger.info(f"Scheduling optimization completed in {optimization_time:.2f}s")
        return result
    
    # Private coordination methods
    
    async def _coordination_loop(self) -> None:
        """Main coordination loop for parallel execution"""
        logger.info("Started parallel coordination loop")
        
        while self._running:
            try:
                coordination_start = time.time()
                
                # Skip coordination if paused
                if self._paused:
                    await asyncio.sleep(self.coordination_check_interval)
                    continue
                
                # Perform coordination tasks
                await self._coordinate_parallel_execution()
                
                # Update coordination metrics
                coordination_time = time.time() - coordination_start
                self._coordination_metrics["average_coordination_time"] = (
                    self._coordination_metrics["average_coordination_time"] * 0.9 +
                    coordination_time * 0.1
                )
                
                # Sleep until next coordination cycle
                await asyncio.sleep(self.coordination_check_interval)
                
            except asyncio.CancelledError:
                logger.info("Coordination loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in coordination loop: {str(e)}")
                await asyncio.sleep(self.coordination_check_interval * 2)  # Back-off on error
    
    async def _coordinate_parallel_execution(self) -> None:
        """Coordinate one cycle of parallel execution"""
        # 1. Clean up expired locks
        await self._cleanup_expired_locks()
        
        # 2. Update cycle statuses
        await self._update_cycle_statuses()
        
        # 3. Check for and resolve conflicts
        if self.enable_conflict_prevention:
            await self._check_and_resolve_conflicts()
        
        # 4. Start new cycles if capacity available
        await self._start_pending_cycles()
        
        # 5. Monitor and optimize resource usage
        await self._monitor_resource_usage()
        
        # 6. Update performance statistics
        await self._update_performance_stats()
        
        # 7. Emit status updates for monitoring
        await self._emit_parallel_status_update()
    
    async def _analyze_cycle_conflicts(self, parallel_cycle: ParallelCycle) -> None:
        """Analyze potential conflicts for a new cycle"""
        story_id = parallel_cycle.story_id
        
        # Get file paths that this cycle will modify
        file_paths = await self._extract_file_paths_from_cycle(parallel_cycle.cycle)
        
        if file_paths:
            # Check for conflicts with context manager
            conflicts = await self.context_manager.detect_story_conflicts(story_id, file_paths)
            parallel_cycle.conflicts.update(conflicts)
            
            if conflicts:
                logger.warning(
                    f"Detected conflicts for cycle {parallel_cycle.id}: {conflicts}"
                )
                
                # Mark as blocked if conflicts are unresolvable
                if await self._are_conflicts_blocking(parallel_cycle, conflicts):
                    parallel_cycle.status = CycleStatus.BLOCKED
    
    async def _schedule_cycle(self, parallel_cycle: ParallelCycle) -> None:
        """Add cycle to execution queue with intelligent scheduling"""
        # Check dependencies
        unmet_dependencies = await self._check_dependencies(parallel_cycle)
        if unmet_dependencies:
            parallel_cycle.dependencies.update(unmet_dependencies)
            parallel_cycle.status = CycleStatus.BLOCKED
            logger.info(f"Cycle {parallel_cycle.id} blocked by dependencies: {unmet_dependencies}")
            return
        
        # Add to queue with priority-based insertion
        insertion_index = 0
        for i, queued_cycle_id in enumerate(self.execution_queue):
            queued_cycle = self.parallel_cycles[queued_cycle_id]
            if parallel_cycle.priority < queued_cycle.priority:
                insertion_index = i
                break
            insertion_index = i + 1
        
        self.execution_queue.insert(insertion_index, parallel_cycle.id)
        logger.info(f"Scheduled cycle {parallel_cycle.id} at position {insertion_index}")
    
    async def _start_pending_cycles(self) -> None:
        """Start pending cycles up to maximum capacity"""
        active_count = len([pc for pc in self.parallel_cycles.values() if pc.is_active])
        
        if active_count >= self.max_parallel_cycles:
            return
        
        cycles_to_start = self.max_parallel_cycles - active_count
        started_cycles = []
        
        # Start cycles from the queue
        for _ in range(cycles_to_start):
            if not self.execution_queue:
                break
            
            cycle_id = self.execution_queue.pop(0)
            parallel_cycle = self.parallel_cycles[cycle_id]
            
            # Check if cycle can be started
            if await self._can_start_cycle(parallel_cycle):
                await self._start_cycle(parallel_cycle)
                started_cycles.append(cycle_id)
            else:
                # Put back in queue if can't start yet
                self.execution_queue.insert(0, cycle_id)
                break
        
        if started_cycles:
            logger.info(f"Started {len(started_cycles)} parallel cycles: {started_cycles}")
    
    async def _can_start_cycle(self, parallel_cycle: ParallelCycle) -> bool:
        """Check if a cycle can be started"""
        # Check status
        if parallel_cycle.status not in [CycleStatus.PENDING]:
            return False
        
        # Check dependencies
        unmet_dependencies = await self._check_dependencies(parallel_cycle)
        if unmet_dependencies:
            return False
        
        # Check for blocking conflicts
        if parallel_cycle.conflicts:
            blocking_conflicts = await self._are_conflicts_blocking(parallel_cycle, parallel_cycle.conflicts)
            if blocking_conflicts:
                return False
        
        # Check resource availability
        required_resources = await self._identify_required_resources(parallel_cycle)
        if not await self._are_resources_available(required_resources):
            return False
        
        return True
    
    async def _start_cycle(self, parallel_cycle: ParallelCycle) -> None:
        """Start execution of a parallel cycle"""
        # Update status
        parallel_cycle.status = CycleStatus.ACTIVE
        parallel_cycle.started_at = datetime.utcnow()
        parallel_cycle.last_activity = datetime.utcnow()
        
        # Acquire necessary resource locks
        required_resources = await self._identify_required_resources(parallel_cycle)
        await self._acquire_resource_locks(parallel_cycle, required_resources)
        
        # Prepare context for the cycle
        context_start_time = time.time()
        await self._prepare_cycle_context(parallel_cycle)
        parallel_cycle.context_preparation_time = time.time() - context_start_time
        
        # Update statistics
        self.stats.active_cycles += 1
        
        logger.info(f"Started parallel cycle {parallel_cycle.id} for story {parallel_cycle.story_id}")
        
        # Emit transition event
        try:
            emit_tdd_transition(
                parallel_cycle.story_id,
                TDDState.DESIGN,  # Assuming starting state
                parallel_cycle.current_state,
                "parallel"
            )
        except Exception as e:
            logger.warning(f"Failed to emit transition event: {e}")
    
    async def _update_cycle_statuses(self) -> None:
        """Update status of all active cycles"""
        for parallel_cycle in self.parallel_cycles.values():
            if parallel_cycle.is_active:
                # Update last activity if cycle has made progress
                if await self._has_cycle_progressed(parallel_cycle):
                    parallel_cycle.last_activity = datetime.utcnow()
                
                # Check if cycle is completed
                if await self._is_cycle_completed(parallel_cycle):
                    await self._complete_cycle(parallel_cycle)
                
                # Check if cycle has failed
                elif await self._has_cycle_failed(parallel_cycle):
                    await self._fail_cycle(parallel_cycle)
                
                # Check if cycle is stuck
                elif await self._is_cycle_stuck(parallel_cycle):
                    await self._handle_stuck_cycle(parallel_cycle)
    
    async def _check_and_resolve_conflicts(self) -> None:
        """Check for conflicts and attempt resolution"""
        active_cycles = [pc for pc in self.parallel_cycles.values() if pc.is_active]
        
        for i, cycle1 in enumerate(active_cycles):
            for cycle2 in active_cycles[i+1:]:
                # Check for file conflicts
                conflict_detected = await self._detect_cycle_conflict(cycle1, cycle2)
                
                if conflict_detected:
                    await self._handle_cycle_conflict(cycle1, cycle2)
    
    async def _monitor_resource_usage(self) -> None:
        """Monitor and optimize resource usage"""
        # Calculate current resource utilization
        utilization = await self._calculate_resource_utilization()
        
        # Check for over-utilization
        for resource_type, usage in utilization.items():
            if usage > 0.9:  # 90% utilization threshold
                logger.warning(f"High resource utilization detected: {resource_type} at {usage:.1%}")
                await self._optimize_resource_usage(resource_type)
    
    async def _update_performance_stats(self) -> None:
        """Update performance statistics"""
        active_cycles = [pc for pc in self.parallel_cycles.values() if pc.is_active]
        completed_cycles = [pc for pc in self.parallel_cycles.values() 
                          if pc.status == CycleStatus.COMPLETED]
        failed_cycles = [pc for pc in self.parallel_cycles.values() 
                        if pc.status == CycleStatus.FAILED]
        blocked_cycles = [pc for pc in self.parallel_cycles.values() if pc.is_blocked]
        
        self.stats.total_cycles = len(self.parallel_cycles)
        self.stats.active_cycles = len(active_cycles)
        self.stats.completed_cycles = len(completed_cycles)
        self.stats.failed_cycles = len(failed_cycles)
        self.stats.blocked_cycles = len(blocked_cycles)
        
        # Calculate average execution time
        if completed_cycles:
            total_time = sum(pc.execution_time.total_seconds() for pc in completed_cycles 
                           if pc.execution_time)
            self.stats.average_execution_time = total_time / len(completed_cycles)
        
        # Calculate throughput
        if self.stats.total_cycles > 0:
            total_runtime = datetime.utcnow() - min(pc.started_at for pc in self.parallel_cycles.values() 
                                                  if pc.started_at)
            hours = total_runtime.total_seconds() / 3600
            self.stats.throughput_cycles_per_hour = self.stats.completed_cycles / max(hours, 0.1)
        
        # Calculate conflict rate
        if self.stats.total_cycles > 0:
            cycles_with_conflicts = len([pc for pc in self.parallel_cycles.values() if pc.conflicts])
            self.stats.conflict_rate = cycles_with_conflicts / self.stats.total_cycles
        
        # Update coordination overhead
        self.stats.coordination_overhead = self._coordination_metrics.get("average_coordination_time", 0)
    
    # Resource management methods
    
    async def _acquire_resource_locks(
        self, 
        parallel_cycle: ParallelCycle, 
        resources: List[Tuple[str, ResourceType]]
    ) -> None:
        """Acquire resource locks for a cycle"""
        for resource_id, resource_type in resources:
            lock = ResourceLock(
                resource_id=resource_id,
                resource_type=resource_type,
                cycle_id=parallel_cycle.id,
                story_id=parallel_cycle.story_id,
                locked_at=datetime.utcnow(),
                lock_duration=self.resource_timeout,
                exclusive=True
            )
            
            self.resource_locks[resource_id] = lock
            parallel_cycle.resource_locks.add(resource_id)
    
    async def _release_cycle_locks(self, parallel_cycle: ParallelCycle) -> None:
        """Release all locks held by a cycle"""
        locks_to_release = list(parallel_cycle.resource_locks)
        
        for resource_id in locks_to_release:
            if resource_id in self.resource_locks:
                del self.resource_locks[resource_id]
            parallel_cycle.resource_locks.discard(resource_id)
        
        if locks_to_release:
            logger.debug(f"Released {len(locks_to_release)} locks for cycle {parallel_cycle.id}")
    
    async def _release_all_locks(self) -> None:
        """Release all resource locks"""
        lock_count = len(self.resource_locks)
        self.resource_locks.clear()
        
        for parallel_cycle in self.parallel_cycles.values():
            parallel_cycle.resource_locks.clear()
        
        if lock_count > 0:
            logger.info(f"Released all {lock_count} resource locks")
    
    async def _cleanup_expired_locks(self) -> None:
        """Clean up expired resource locks"""
        expired_locks = []
        
        for resource_id, lock in self.resource_locks.items():
            if lock.is_expired:
                expired_locks.append(resource_id)
        
        for resource_id in expired_locks:
            lock = self.resource_locks[resource_id]
            del self.resource_locks[resource_id]
            
            # Remove from cycle's lock set
            if lock.cycle_id in self.parallel_cycles:
                self.parallel_cycles[lock.cycle_id].resource_locks.discard(resource_id)
            
            logger.warning(f"Released expired lock for resource {resource_id}")
    
    # Helper methods for cycle management
    
    async def _extract_file_paths_from_cycle(self, cycle: TDDCycle) -> List[str]:
        """Extract file paths that will be modified by a TDD cycle"""
        file_paths = []
        
        for task in cycle.tasks:
            # Extract from task metadata
            if hasattr(task, 'file_paths'):
                file_paths.extend(task.file_paths)
            
            # Extract from test files
            file_paths.extend([tf.file_path for tf in task.test_file_objects])
            
            # Extract from implementation files
            if hasattr(task, 'implementation_files'):
                file_paths.extend(task.implementation_files)
        
        return list(set(file_paths))  # Remove duplicates
    
    async def _check_dependencies(self, parallel_cycle: ParallelCycle) -> Set[str]:
        """Check for unmet dependencies"""
        unmet_dependencies = set()
        
        for dependency_story_id in parallel_cycle.dependencies:
            # Check if dependency story is still active
            dependency_active = any(
                pc.story_id == dependency_story_id and pc.is_active
                for pc in self.parallel_cycles.values()
            )
            
            if dependency_active:
                unmet_dependencies.add(dependency_story_id)
        
        return unmet_dependencies
    
    async def _are_conflicts_blocking(
        self, 
        parallel_cycle: ParallelCycle, 
        conflicts: Set[str]
    ) -> bool:
        """Check if conflicts are blocking for a cycle"""
        for conflict_story_id in conflicts:
            # Check if conflicting story is currently active
            conflict_active = any(
                pc.story_id == conflict_story_id and pc.is_active
                for pc in self.parallel_cycles.values()
            )
            
            if conflict_active:
                return True
        
        return False
    
    async def _identify_required_resources(
        self, 
        parallel_cycle: ParallelCycle
    ) -> List[Tuple[str, ResourceType]]:
        """Identify resources required by a cycle"""
        resources = []
        
        # File resources
        file_paths = await self._extract_file_paths_from_cycle(parallel_cycle.cycle)
        for file_path in file_paths:
            resources.append((file_path, ResourceType.FILE))
        
        # Agent resources (will be managed by agent pool)
        # Test runner resources
        resources.append(("test_runner", ResourceType.TEST_RUNNER))
        
        return resources
    
    async def _are_resources_available(
        self, 
        resources: List[Tuple[str, ResourceType]]
    ) -> bool:
        """Check if required resources are available"""
        for resource_id, resource_type in resources:
            if resource_id in self.resource_locks:
                lock = self.resource_locks[resource_id]
                if lock.exclusive and not lock.is_expired:
                    return False
        
        return True
    
    # Status and monitoring methods
    
    async def _emit_parallel_status_update(self) -> None:
        """Emit parallel execution status update for monitoring"""
        try:
            status = await self.get_parallel_status()
            emit_parallel_status(status)
        except Exception as e:
            logger.warning(f"Failed to emit parallel status update: {e}")
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            "average_execution_time": self.stats.average_execution_time,
            "throughput_cycles_per_hour": self.stats.throughput_cycles_per_hour,
            "conflict_rate": self.stats.conflict_rate,
            "coordination_overhead": self.stats.coordination_overhead,
            "context_preparation_time": self.stats.context_preparation_time,
            "success_rate": (
                self.stats.completed_cycles / max(self.stats.total_cycles, 1) * 100
            )
        }
    
    async def _calculate_resource_utilization(self) -> Dict[str, float]:
        """Calculate current resource utilization"""
        utilization = {}
        
        # Calculate file utilization
        total_files = len(set(resource_id for resource_id, lock in self.resource_locks.items() 
                            if lock.resource_type == ResourceType.FILE))
        max_files = 100  # Estimated max files in use
        utilization["files"] = min(total_files / max_files, 1.0)
        
        # Calculate agent utilization (if agent pool is available)
        if self.agent_pool:
            utilization["agents"] = await self.agent_pool.get_utilization()
        
        # Calculate parallel capacity utilization
        utilization["parallel_capacity"] = len([pc for pc in self.parallel_cycles.values() 
                                              if pc.is_active]) / self.max_parallel_cycles
        
        return utilization
    
    def _get_next_scheduled_cycles(self) -> List[Dict[str, Any]]:
        """Get information about next scheduled cycles"""
        next_cycles = []
        
        for cycle_id in self.execution_queue[:3]:  # Show next 3
            if cycle_id in self.parallel_cycles:
                pc = self.parallel_cycles[cycle_id]
                next_cycles.append({
                    "cycle_id": cycle_id,
                    "story_id": pc.story_id,
                    "priority": pc.priority,
                    "dependencies": list(pc.dependencies),
                    "conflicts": list(pc.conflicts),
                    "estimated_duration": (
                        pc.estimated_duration.total_seconds() 
                        if pc.estimated_duration else None
                    )
                })
        
        return next_cycles
    
    # Advanced optimization methods (placeholders for complex implementations)
    
    async def _identify_bottlenecks(self) -> List[str]:
        """Identify current bottlenecks in parallel execution"""
        bottlenecks = []
        
        # Check for resource bottlenecks
        utilization = await self._calculate_resource_utilization()
        for resource, usage in utilization.items():
            if usage > 0.8:
                bottlenecks.append(f"High {resource} utilization: {usage:.1%}")
        
        # Check for dependency bottlenecks
        blocked_count = len([pc for pc in self.parallel_cycles.values() if pc.is_blocked])
        if blocked_count > 2:
            bottlenecks.append(f"Multiple cycles blocked: {blocked_count}")
        
        return bottlenecks
    
    async def _optimize_execution_queue(self) -> None:
        """Optimize the execution queue based on current state"""
        # Sort by priority and dependencies
        def sort_key(cycle_id):
            pc = self.parallel_cycles[cycle_id]
            return (len(pc.dependencies), pc.priority, pc.last_activity)
        
        self.execution_queue.sort(key=sort_key)
    
    async def _optimize_resource_allocation(self) -> Dict[str, Any]:
        """Optimize resource allocation"""
        return {"optimizations_applied": 0, "resources_reallocated": 0}
    
    async def _apply_predictive_scheduling(self) -> Dict[str, Any]:
        """Apply predictive scheduling optimizations"""
        if not self.enable_predictive_scheduling:
            return {}
        
        # Placeholder for ML-based scheduling
        return {"predictions_applied": 0, "accuracy_estimate": 0.0}
    
    async def _estimate_performance_improvement(self) -> Dict[str, float]:
        """Estimate performance improvement from optimizations"""
        return {
            "throughput_improvement": 0.0,
            "conflict_reduction": 0.0,
            "resource_efficiency": 0.0
        }
    
    # Placeholder methods for complex implementations
    
    async def _initialize_performance_monitoring(self) -> None:
        """Initialize performance monitoring"""
        logger.debug("Performance monitoring initialized")
    
    async def _cleanup_active_cycles(self) -> None:
        """Clean up active cycles during shutdown"""
        active_cycles = [pc for pc in self.parallel_cycles.values() if pc.is_active]
        for pc in active_cycles:
            pc.status = CycleStatus.CANCELLED
            await self._release_cycle_locks(pc)
    
    async def _prepare_cycle_context(self, parallel_cycle: ParallelCycle) -> None:
        """Prepare context for cycle execution"""
        # Placeholder for context preparation
        pass
    
    async def _has_cycle_progressed(self, parallel_cycle: ParallelCycle) -> bool:
        """Check if cycle has made progress"""
        # Placeholder - would check for actual progress
        return False
    
    async def _is_cycle_completed(self, parallel_cycle: ParallelCycle) -> bool:
        """Check if cycle is completed"""
        return parallel_cycle.cycle.current_state == TDDState.COMMIT
    
    async def _has_cycle_failed(self, parallel_cycle: ParallelCycle) -> bool:
        """Check if cycle has failed"""
        # Placeholder for failure detection
        return False
    
    async def _is_cycle_stuck(self, parallel_cycle: ParallelCycle) -> bool:
        """Check if cycle is stuck"""
        # Consider stuck if no activity for 30 minutes
        return (datetime.utcnow() - parallel_cycle.last_activity).total_seconds() > 1800
    
    async def _complete_cycle(self, parallel_cycle: ParallelCycle) -> None:
        """Mark cycle as completed"""
        parallel_cycle.status = CycleStatus.COMPLETED
        parallel_cycle.completed_at = datetime.utcnow()
        await self._release_cycle_locks(parallel_cycle)
        logger.info(f"Completed parallel cycle {parallel_cycle.id}")
    
    async def _fail_cycle(self, parallel_cycle: ParallelCycle) -> None:
        """Mark cycle as failed"""
        parallel_cycle.status = CycleStatus.FAILED
        parallel_cycle.completed_at = datetime.utcnow()
        await self._release_cycle_locks(parallel_cycle)
        logger.error(f"Failed parallel cycle {parallel_cycle.id}")
    
    async def _handle_stuck_cycle(self, parallel_cycle: ParallelCycle) -> None:
        """Handle a stuck cycle"""
        logger.warning(f"Cycle {parallel_cycle.id} appears stuck, pausing for review")
        parallel_cycle.status = CycleStatus.PAUSED
    
    async def _detect_cycle_conflict(
        self, 
        cycle1: ParallelCycle, 
        cycle2: ParallelCycle
    ) -> bool:
        """Detect conflict between two cycles"""
        # Check for overlapping resource locks
        return bool(cycle1.resource_locks.intersection(cycle2.resource_locks))
    
    async def _handle_cycle_conflict(
        self, 
        cycle1: ParallelCycle, 
        cycle2: ParallelCycle
    ) -> None:
        """Handle conflict between two cycles"""
        # Simple resolution: pause lower priority cycle
        if cycle1.priority > cycle2.priority:
            await self.pause_cycle(cycle1.id)
        else:
            await self.pause_cycle(cycle2.id)
    
    async def _optimize_resource_usage(self, resource_type: str) -> None:
        """Optimize usage of a specific resource type"""
        logger.info(f"Optimizing {resource_type} resource usage")