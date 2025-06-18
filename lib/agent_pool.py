"""
Agent Pool Management System

Dynamic agent spawning, load balancing, and failure isolation for parallel TDD execution.
Manages a pool of agents across multiple concurrent TDD cycles with intelligent resource allocation.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json

# Import agent system
try:
    from .agents import BaseAgent, Task, TaskStatus, AgentResult, create_agent, get_available_agents
    from .tdd_models import TDDState, TDDCycle, TDDTask
    from .tdd_state_machine import TDDStateMachine
    from .context_manager import ContextManager
except ImportError:
    from agents import BaseAgent, Task, TaskStatus, AgentResult, create_agent, get_available_agents
    from tdd_models import TDDState, TDDCycle, TDDTask
    from tdd_state_machine import TDDStateMachine
    from context_manager import ContextManager

logger = logging.getLogger(__name__)


class AgentPoolStrategy(Enum):
    """Agent pool management strategies"""
    STATIC = "static"           # Fixed pool size
    DYNAMIC = "dynamic"         # Dynamic scaling based on load
    BURST = "burst"            # Handle burst workloads
    BALANCED = "balanced"       # Balance between performance and resources


class AgentStatus(Enum):
    """Status of agents in the pool"""
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    STARTING = "starting"
    STOPPING = "stopping"
    RETIRED = "retired"


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CAPABILITY_BASED = "capability_based"
    PRIORITY_WEIGHTED = "priority_weighted"


@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_execution_time: float = 0.0
    last_task_time: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_rate: float = 0.0
    uptime: timedelta = field(default_factory=lambda: timedelta())
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks) * 100
    
    @property
    def load_score(self) -> float:
        """Calculate load score for load balancing"""
        base_load = self.total_tasks * 0.3
        time_factor = 1.0 if not self.last_task_time else (
            (datetime.utcnow() - self.last_task_time).total_seconds() / 60
        )
        error_penalty = self.error_rate * 10
        
        return max(0.0, base_load - time_factor + error_penalty)


@dataclass
class PooledAgent:
    """Agent wrapper with pool-specific metadata"""
    agent: BaseAgent
    agent_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.IDLE
    current_task_id: Optional[str] = None
    assigned_cycles: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    capabilities: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 1
    current_tasks: Set[str] = field(default_factory=set)
    failure_count: int = 0
    recovery_attempts: int = 0
    
    @property
    def is_available(self) -> bool:
        """Check if agent is available for new tasks"""
        return (
            self.status == AgentStatus.IDLE and
            len(self.current_tasks) < self.max_concurrent_tasks
        )
    
    @property
    def load_factor(self) -> float:
        """Calculate current load factor (0.0 to 1.0)"""
        if self.max_concurrent_tasks == 0:
            return 1.0
        return len(self.current_tasks) / self.max_concurrent_tasks
    
    @property
    def uptime(self) -> timedelta:
        """Calculate agent uptime"""
        return datetime.utcnow() - self.created_at


@dataclass
class PoolConfiguration:
    """Configuration for agent pool"""
    min_agents_per_type: Dict[str, int] = field(default_factory=lambda: {
        "DesignAgent": 1,
        "CodeAgent": 2,
        "QAAgent": 1,
        "DataAgent": 1
    })
    max_agents_per_type: Dict[str, int] = field(default_factory=lambda: {
        "DesignAgent": 3,
        "CodeAgent": 5,
        "QAAgent": 3,
        "DataAgent": 2
    })
    scaling_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "scale_up_threshold": 0.8,    # Scale up when 80% loaded
        "scale_down_threshold": 0.3,  # Scale down when 30% loaded
        "burst_threshold": 0.9        # Emergency scaling at 90%
    })
    agent_timeout_minutes: int = 30
    failure_threshold: int = 3
    recovery_delay_seconds: int = 60
    health_check_interval: float = 30.0
    cleanup_interval_minutes: int = 60


@dataclass
class PoolStatistics:
    """Statistics for the agent pool"""
    total_agents: int = 0
    active_agents: int = 0
    idle_agents: int = 0
    failed_agents: int = 0
    total_tasks_processed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_task_time: float = 0.0
    pool_utilization: float = 0.0
    scaling_events: int = 0
    recovery_events: int = 0
    agent_creation_time: float = 0.0
    load_balancing_decisions: int = 0


class AgentPool:
    """
    Agent Pool Management System for Parallel TDD Execution.
    
    Manages a dynamic pool of agents with load balancing, failure recovery,
    and intelligent scaling based on workload patterns.
    """
    
    def __init__(
        self,
        context_manager: ContextManager,
        strategy: AgentPoolStrategy = AgentPoolStrategy.DYNAMIC,
        load_balancing: LoadBalancingAlgorithm = LoadBalancingAlgorithm.CAPABILITY_BASED,
        config: Optional[PoolConfiguration] = None,
        enable_auto_scaling: bool = True,
        enable_health_monitoring: bool = True,
        enable_predictive_scaling: bool = True
    ):
        """
        Initialize Agent Pool Manager.
        
        Args:
            context_manager: Context manager for agent coordination
            strategy: Pool management strategy
            load_balancing: Load balancing algorithm
            config: Pool configuration
            enable_auto_scaling: Enable automatic scaling
            enable_health_monitoring: Enable health monitoring
            enable_predictive_scaling: Enable predictive scaling
        """
        self.context_manager = context_manager
        self.strategy = strategy
        self.load_balancing = load_balancing
        self.config = config or PoolConfiguration()
        self.enable_auto_scaling = enable_auto_scaling
        self.enable_health_monitoring = enable_health_monitoring
        self.enable_predictive_scaling = enable_predictive_scaling
        
        # Agent pool state
        self.agents: Dict[str, PooledAgent] = {}  # agent_id -> PooledAgent
        self.agent_types: Dict[str, List[str]] = defaultdict(list)  # type -> [agent_ids]
        self.task_queue: deque = deque()  # Task queue for load balancing
        self.active_tasks: Dict[str, Task] = {}  # task_id -> Task
        
        # Load balancing state
        self._round_robin_counters: Dict[str, int] = defaultdict(int)
        self._load_balancing_history: List[Dict[str, Any]] = []
        
        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Statistics and metrics
        self.statistics = PoolStatistics()
        self._performance_history: List[Dict[str, Any]] = []
        self._scaling_history: List[Dict[str, Any]] = []
        
        # Predictive scaling
        self._workload_patterns: Dict[str, List[float]] = defaultdict(list)
        self._scaling_predictions: Dict[str, float] = {}
        
        logger.info(
            f"AgentPool initialized with strategy={strategy.value}, "
            f"load_balancing={load_balancing.value}, auto_scaling={enable_auto_scaling}"
        )
    
    async def start(self) -> None:
        """Start the agent pool management system"""
        if self._running:
            logger.warning("Agent pool already running")
            return
        
        self._running = True
        logger.info("Starting agent pool management system")
        
        # Initialize minimum agents
        await self._initialize_minimum_agents()
        
        # Start health monitoring
        if self.enable_health_monitoring:
            self._health_check_task = asyncio.create_task(self._health_monitoring_loop())
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Agent pool management system started successfully")
    
    async def stop(self) -> None:
        """Stop the agent pool management system"""
        if not self._running:
            return
        
        logger.info("Stopping agent pool management system")
        self._running = False
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Shut down all agents gracefully
        await self._shutdown_all_agents()
        
        logger.info("Agent pool management system stopped")
    
    async def submit_task(
        self,
        agent_type: str,
        command: str,
        context: Dict[str, Any],
        priority: int = 5,
        cycle_id: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """
        Submit a task to the agent pool.
        
        Args:
            agent_type: Type of agent required
            command: Command to execute
            context: Task context
            priority: Task priority (1-10, lower is higher priority)
            cycle_id: TDD cycle ID for task association
            max_retries: Maximum retry attempts
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            agent_type=agent_type,
            command=command,
            context=context,
            max_retries=max_retries
        )
        
        # Add task metadata
        task.context.update({
            "priority": priority,
            "cycle_id": cycle_id,
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        self.active_tasks[task_id] = task
        
        # Try to assign immediately or queue
        agent = await self._select_agent(agent_type, task)
        if agent:
            await self._assign_task_to_agent(agent, task)
        else:
            # Queue task for later assignment
            self.task_queue.append(task)
            logger.info(f"Queued task {task_id} for {agent_type} (no available agents)")
        
        return task_id
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[AgentResult]:
        """Get result of a submitted task"""
        if task_id not in self.active_tasks:
            return None
        
        task = self.active_tasks[task_id]
        
        # Wait for task completion with timeout
        start_time = time.time()
        while task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            if timeout and (time.time() - start_time) > timeout:
                logger.warning(f"Task {task_id} timed out after {timeout}s")
                return None
            
            await asyncio.sleep(0.1)
        
        # Return result based on task status
        if task.status == TaskStatus.COMPLETED:
            return AgentResult(success=True, output="Task completed", artifacts={})
        else:
            return AgentResult(
                success=False,
                output="",
                error=f"Task failed with status: {task.status.value}"
            )
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        
        if task.status == TaskStatus.PENDING:
            # Remove from queue
            try:
                self.task_queue.remove(task)
                task.status = TaskStatus.CANCELLED
                return True
            except ValueError:
                pass
        
        elif task.status == TaskStatus.IN_PROGRESS:
            # Find agent executing the task and request cancellation
            for agent in self.agents.values():
                if task_id in agent.current_tasks:
                    agent.current_tasks.discard(task_id)
                    task.status = TaskStatus.CANCELLED
                    return True
        
        return False
    
    async def scale_pool(self, agent_type: str, target_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Scale the pool for a specific agent type.
        
        Args:
            agent_type: Type of agent to scale
            target_count: Target number of agents (auto-calculated if None)
            
        Returns:
            Scaling operation result
        """
        current_count = len(self.agent_types[agent_type])
        
        if target_count is None:
            target_count = await self._calculate_optimal_agent_count(agent_type)
        
        # Ensure within configured limits
        min_count = self.config.min_agents_per_type.get(agent_type, 1)
        max_count = self.config.max_agents_per_type.get(agent_type, 5)
        target_count = max(min_count, min(target_count, max_count))
        
        scaling_result = {
            "agent_type": agent_type,
            "current_count": current_count,
            "target_count": target_count,
            "agents_added": 0,
            "agents_removed": 0,
            "scaling_time": 0.0
        }
        
        start_time = time.time()
        
        if target_count > current_count:
            # Scale up
            agents_to_add = target_count - current_count
            for _ in range(agents_to_add):
                agent = await self._create_agent(agent_type)
                if agent:
                    scaling_result["agents_added"] += 1
        
        elif target_count < current_count:
            # Scale down
            agents_to_remove = current_count - target_count
            removed_count = await self._remove_excess_agents(agent_type, agents_to_remove)
            scaling_result["agents_removed"] = removed_count
        
        scaling_result["scaling_time"] = time.time() - start_time
        
        # Record scaling event
        self.statistics.scaling_events += 1
        self._scaling_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "scale",
            **scaling_result
        })
        
        logger.info(
            f"Scaled {agent_type}: {current_count} -> {target_count} "
            f"(+{scaling_result['agents_added']}, -{scaling_result['agents_removed']})"
        )
        
        return scaling_result
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get comprehensive pool status"""
        agent_status_by_type = {}
        
        for agent_type in get_available_agents():
            agents = [self.agents[aid] for aid in self.agent_types[agent_type]]
            agent_status_by_type[agent_type] = {
                "total": len(agents),
                "idle": len([a for a in agents if a.status == AgentStatus.IDLE]),
                "busy": len([a for a in agents if a.status == AgentStatus.BUSY]),
                "failed": len([a for a in agents if a.status == AgentStatus.FAILED]),
                "average_load": sum(a.load_factor for a in agents) / len(agents) if agents else 0,
                "total_tasks": sum(a.metrics.total_tasks for a in agents),
                "success_rate": sum(a.metrics.success_rate for a in agents) / len(agents) if agents else 0
            }
        
        return {
            "pool_summary": {
                "total_agents": len(self.agents),
                "active_agents": len([a for a in self.agents.values() if a.status in [AgentStatus.IDLE, AgentStatus.BUSY]]),
                "failed_agents": len([a for a in self.agents.values() if a.status == AgentStatus.FAILED]),
                "queued_tasks": len(self.task_queue),
                "active_tasks": len(self.active_tasks),
                "pool_utilization": await self.get_utilization()
            },
            "agent_types": agent_status_by_type,
            "configuration": {
                "strategy": self.strategy.value,
                "load_balancing": self.load_balancing.value,
                "auto_scaling": self.enable_auto_scaling,
                "health_monitoring": self.enable_health_monitoring,
                "predictive_scaling": self.enable_predictive_scaling
            },
            "statistics": {
                "total_tasks_processed": self.statistics.total_tasks_processed,
                "success_rate": (
                    self.statistics.successful_tasks / max(self.statistics.total_tasks_processed, 1) * 100
                ),
                "average_task_time": self.statistics.average_task_time,
                "scaling_events": self.statistics.scaling_events,
                "recovery_events": self.statistics.recovery_events
            }
        }
    
    async def get_utilization(self) -> float:
        """Get overall pool utilization (0.0 to 1.0)"""
        if not self.agents:
            return 0.0
        
        total_capacity = sum(a.max_concurrent_tasks for a in self.agents.values())
        if total_capacity == 0:
            return 0.0
        
        current_load = sum(len(a.current_tasks) for a in self.agents.values())
        return current_load / total_capacity
    
    async def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        
        return {
            "agent_id": agent_id,
            "agent_type": agent.agent_type,
            "status": agent.status.value,
            "current_tasks": len(agent.current_tasks),
            "max_concurrent_tasks": agent.max_concurrent_tasks,
            "load_factor": agent.load_factor,
            "assigned_cycles": list(agent.assigned_cycles),
            "created_at": agent.created_at.isoformat(),
            "uptime": agent.uptime.total_seconds(),
            "last_activity": agent.last_activity.isoformat(),
            "capabilities": agent.capabilities,
            "metrics": {
                "total_tasks": agent.metrics.total_tasks,
                "successful_tasks": agent.metrics.successful_tasks,
                "failed_tasks": agent.metrics.failed_tasks,
                "success_rate": agent.metrics.success_rate,
                "average_execution_time": agent.metrics.average_execution_time,
                "error_rate": agent.metrics.error_rate,
                "load_score": agent.metrics.load_score
            },
            "failure_count": agent.failure_count,
            "recovery_attempts": agent.recovery_attempts
        }
    
    # Private methods for pool management
    
    async def _initialize_minimum_agents(self) -> None:
        """Initialize minimum required agents for each type"""
        for agent_type, min_count in self.config.min_agents_per_type.items():
            for _ in range(min_count):
                await self._create_agent(agent_type)
        
        logger.info(f"Initialized minimum agents: {dict(self.config.min_agents_per_type)}")
    
    async def _create_agent(self, agent_type: str) -> Optional[PooledAgent]:
        """Create a new agent and add it to the pool"""
        creation_start = time.time()
        
        try:
            # Create agent instance
            agent_instance = create_agent(agent_type, context_manager=self.context_manager)
            
            # Create pooled agent wrapper
            agent_id = str(uuid.uuid4())
            pooled_agent = PooledAgent(
                agent=agent_instance,
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=agent_instance.capabilities,
                max_concurrent_tasks=self._get_max_concurrent_tasks(agent_type)
            )
            
            # Add to pool
            self.agents[agent_id] = pooled_agent
            self.agent_types[agent_type].append(agent_id)
            
            # Update statistics
            self.statistics.total_agents += 1
            creation_time = time.time() - creation_start
            self.statistics.agent_creation_time = (
                self.statistics.agent_creation_time * 0.9 + creation_time * 0.1
            )
            
            logger.info(f"Created {agent_type} agent {agent_id} in {creation_time:.2f}s")
            return pooled_agent
            
        except Exception as e:
            logger.error(f"Failed to create {agent_type} agent: {str(e)}")
            return None
    
    async def _remove_excess_agents(self, agent_type: str, count: int) -> int:
        """Remove excess agents of a specific type"""
        agent_ids = self.agent_types[agent_type].copy()
        removed_count = 0
        
        # Sort by load and last activity (remove least active first)
        agents_to_consider = []
        for agent_id in agent_ids:
            agent = self.agents[agent_id]
            if agent.status == AgentStatus.IDLE and not agent.current_tasks:
                agents_to_consider.append((agent_id, agent.last_activity))
        
        # Sort by last activity (oldest first)
        agents_to_consider.sort(key=lambda x: x[1])
        
        for agent_id, _ in agents_to_consider[:count]:
            await self._remove_agent(agent_id)
            removed_count += 1
        
        return removed_count
    
    async def _remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the pool"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        
        # Ensure agent is not busy
        if agent.current_tasks:
            logger.warning(f"Attempting to remove busy agent {agent_id}")
            return
        
        # Remove from tracking structures
        del self.agents[agent_id]
        self.agent_types[agent.agent_type].remove(agent_id)
        
        # Update statistics
        self.statistics.total_agents -= 1
        
        logger.info(f"Removed {agent.agent_type} agent {agent_id}")
    
    async def _select_agent(self, agent_type: str, task: Task) -> Optional[PooledAgent]:
        """Select the best available agent for a task"""
        available_agents = [
            self.agents[aid] for aid in self.agent_types[agent_type]
            if self.agents[aid].is_available
        ]
        
        if not available_agents:
            # Try to scale up if auto-scaling is enabled
            if self.enable_auto_scaling:
                await self._attempt_auto_scale(agent_type)
                # Retry selection after scaling
                available_agents = [
                    self.agents[aid] for aid in self.agent_types[agent_type]
                    if self.agents[aid].is_available
                ]
            
            if not available_agents:
                return None
        
        # Apply load balancing algorithm
        selected_agent = await self._apply_load_balancing(available_agents, task)
        
        # Record load balancing decision
        self.statistics.load_balancing_decisions += 1
        self._load_balancing_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "algorithm": self.load_balancing.value,
            "agent_type": agent_type,
            "selected_agent": selected_agent.agent_id if selected_agent else None,
            "available_agents": len(available_agents),
            "task_id": task.id
        })
        
        return selected_agent
    
    async def _apply_load_balancing(self, agents: List[PooledAgent], task: Task) -> Optional[PooledAgent]:
        """Apply load balancing algorithm to select agent"""
        if not agents:
            return None
        
        if self.load_balancing == LoadBalancingAlgorithm.ROUND_ROBIN:
            agent_type = agents[0].agent_type
            index = self._round_robin_counters[agent_type] % len(agents)
            self._round_robin_counters[agent_type] += 1
            return agents[index]
        
        elif self.load_balancing == LoadBalancingAlgorithm.LEAST_LOADED:
            return min(agents, key=lambda a: a.load_factor)
        
        elif self.load_balancing == LoadBalancingAlgorithm.CAPABILITY_BASED:
            # Score agents based on capabilities and load
            def score_agent(agent: PooledAgent) -> float:
                load_penalty = agent.load_factor * 10
                success_bonus = agent.metrics.success_rate / 10
                recent_activity = 0
                if agent.metrics.last_task_time:
                    time_since = (datetime.utcnow() - agent.metrics.last_task_time).total_seconds()
                    recent_activity = max(0, 10 - time_since / 60)  # Bonus for recent activity
                
                return success_bonus + recent_activity - load_penalty - agent.metrics.error_rate
            
            return max(agents, key=score_agent)
        
        elif self.load_balancing == LoadBalancingAlgorithm.PRIORITY_WEIGHTED:
            task_priority = task.context.get("priority", 5)
            # For high-priority tasks, prefer less loaded agents
            if task_priority <= 3:
                return min(agents, key=lambda a: a.load_factor)
            else:
                return min(agents, key=lambda a: a.metrics.load_score)
        
        # Default to least loaded
        return min(agents, key=lambda a: a.load_factor)
    
    async def _assign_task_to_agent(self, agent: PooledAgent, task: Task) -> None:
        """Assign a task to a specific agent"""
        agent.current_tasks.add(task.id)
        agent.status = AgentStatus.BUSY
        agent.last_activity = datetime.utcnow()
        
        # Update task context with agent information
        task.context.update({
            "assigned_agent_id": agent.agent_id,
            "assigned_agent_type": agent.agent_type,
            "assigned_at": datetime.utcnow().isoformat()
        })
        
        # Start task execution
        asyncio.create_task(self._execute_task(agent, task))
        
        logger.info(f"Assigned task {task.id} to agent {agent.agent_id}")
    
    async def _execute_task(self, agent: PooledAgent, task: Task) -> None:
        """Execute a task on an agent"""
        execution_start = time.time()
        
        try:
            # Execute task with retry logic
            result = await agent.agent._execute_with_retry(task, dry_run=False)
            
            # Update agent metrics
            execution_time = time.time() - execution_start
            agent.metrics.total_tasks += 1
            agent.metrics.last_task_time = datetime.utcnow()
            
            # Update execution time average
            if agent.metrics.average_execution_time == 0:
                agent.metrics.average_execution_time = execution_time
            else:
                agent.metrics.average_execution_time = (
                    agent.metrics.average_execution_time * 0.9 + execution_time * 0.1
                )
            
            if result.success:
                agent.metrics.successful_tasks += 1
                task.status = TaskStatus.COMPLETED
                self.statistics.successful_tasks += 1
            else:
                agent.metrics.failed_tasks += 1
                task.status = TaskStatus.FAILED
                agent.failure_count += 1
                self.statistics.failed_tasks += 1
            
            # Update error rate
            agent.metrics.error_rate = (
                agent.metrics.failed_tasks / agent.metrics.total_tasks * 100
            )
            
            # Update pool statistics
            self.statistics.total_tasks_processed += 1
            self.statistics.average_task_time = (
                self.statistics.average_task_time * 0.9 + execution_time * 0.1
            )
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            task.status = TaskStatus.FAILED
            agent.failure_count += 1
            agent.metrics.failed_tasks += 1
            self.statistics.failed_tasks += 1
        
        finally:
            # Clean up task assignment
            agent.current_tasks.discard(task.id)
            if not agent.current_tasks:
                agent.status = AgentStatus.IDLE
            
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            # Check if agent needs recovery
            if agent.failure_count >= self.config.failure_threshold:
                await self._recover_agent(agent)
            
            # Process queued tasks
            await self._process_task_queue()
    
    async def _process_task_queue(self) -> None:
        """Process queued tasks"""
        while self.task_queue:
            task = self.task_queue.popleft()
            agent = await self._select_agent(task.agent_type, task)
            
            if agent:
                await self._assign_task_to_agent(agent, task)
            else:
                # Put task back in queue if no agent available
                self.task_queue.appendleft(task)
                break
    
    async def _attempt_auto_scale(self, agent_type: str) -> None:
        """Attempt to auto-scale agents for a type"""
        if not self.enable_auto_scaling:
            return
        
        current_count = len(self.agent_types[agent_type])
        max_count = self.config.max_agents_per_type.get(agent_type, 5)
        
        if current_count < max_count:
            await self._create_agent(agent_type)
            logger.info(f"Auto-scaled {agent_type}: {current_count} -> {current_count + 1}")
    
    async def _recover_agent(self, agent: PooledAgent) -> None:
        """Attempt to recover a failed agent"""
        agent.status = AgentStatus.FAILED
        agent.recovery_attempts += 1
        
        logger.warning(
            f"Agent {agent.agent_id} failed (failures: {agent.failure_count}, "
            f"recovery attempts: {agent.recovery_attempts})"
        )
        
        # Attempt recovery after delay
        await asyncio.sleep(self.config.recovery_delay_seconds)
        
        # Reset failure count and status
        agent.failure_count = 0
        agent.status = AgentStatus.IDLE
        agent.last_activity = datetime.utcnow()
        
        self.statistics.recovery_events += 1
        logger.info(f"Recovered agent {agent.agent_id}")
    
    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop"""
        logger.info("Started agent pool health monitoring")
        
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
                await asyncio.sleep(self.config.health_check_interval * 2)
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all agents"""
        for agent in self.agents.values():
            # Check for stuck agents
            if agent.status == AgentStatus.BUSY:
                time_since_activity = datetime.utcnow() - agent.last_activity
                if time_since_activity.total_seconds() > self.config.agent_timeout_minutes * 60:
                    logger.warning(f"Agent {agent.agent_id} appears stuck, attempting recovery")
                    await self._recover_agent(agent)
            
            # Check agent health metrics
            if agent.metrics.error_rate > 50:  # 50% error rate threshold
                logger.warning(f"Agent {agent.agent_id} has high error rate: {agent.metrics.error_rate:.1f}%")
        
        # Auto-scaling based on load
        if self.enable_auto_scaling:
            await self._check_auto_scaling_conditions()
    
    async def _check_auto_scaling_conditions(self) -> None:
        """Check if auto-scaling is needed"""
        for agent_type in get_available_agents():
            utilization = await self._calculate_type_utilization(agent_type)
            
            if utilization > self.config.scaling_thresholds["scale_up_threshold"]:
                await self.scale_pool(agent_type)
            elif utilization < self.config.scaling_thresholds["scale_down_threshold"]:
                current_count = len(self.agent_types[agent_type])
                min_count = self.config.min_agents_per_type.get(agent_type, 1)
                if current_count > min_count:
                    target_count = max(min_count, current_count - 1)
                    await self.scale_pool(agent_type, target_count)
    
    async def _calculate_type_utilization(self, agent_type: str) -> float:
        """Calculate utilization for a specific agent type"""
        agents = [self.agents[aid] for aid in self.agent_types[agent_type]]
        if not agents:
            return 0.0
        
        total_capacity = sum(a.max_concurrent_tasks for a in agents)
        if total_capacity == 0:
            return 0.0
        
        current_load = sum(len(a.current_tasks) for a in agents)
        return current_load / total_capacity
    
    async def _cleanup_loop(self) -> None:
        """Cleanup loop for removing old data"""
        while self._running:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")
    
    async def _perform_cleanup(self) -> None:
        """Perform cleanup of old data"""
        # Clean up old performance history
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        self._performance_history = [
            entry for entry in self._performance_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
        
        self._scaling_history = [
            entry for entry in self._scaling_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
        
        self._load_balancing_history = [
            entry for entry in self._load_balancing_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
        
        logger.debug("Performed periodic cleanup of agent pool data")
    
    async def _shutdown_all_agents(self) -> None:
        """Shutdown all agents gracefully"""
        logger.info(f"Shutting down {len(self.agents)} agents")
        
        for agent in self.agents.values():
            agent.status = AgentStatus.STOPPING
        
        # Wait for active tasks to complete (with timeout)
        timeout = 30  # seconds
        start_time = time.time()
        
        while any(agent.current_tasks for agent in self.agents.values()):
            if time.time() - start_time > timeout:
                logger.warning("Timeout waiting for tasks to complete, forcing shutdown")
                break
            await asyncio.sleep(1)
        
        # Clear all data structures
        self.agents.clear()
        self.agent_types.clear()
        self.active_tasks.clear()
        self.task_queue.clear()
    
    def _get_max_concurrent_tasks(self, agent_type: str) -> int:
        """Get maximum concurrent tasks for agent type"""
        # Different agent types have different concurrency capabilities
        defaults = {
            "DesignAgent": 1,      # Design work is typically sequential
            "CodeAgent": 2,        # Can handle multiple small code tasks
            "QAAgent": 3,          # Can run multiple test suites
            "DataAgent": 2         # Data analysis tasks
        }
        return defaults.get(agent_type, 1)
    
    async def _calculate_optimal_agent_count(self, agent_type: str) -> int:
        """Calculate optimal agent count based on workload"""
        current_count = len(self.agent_types[agent_type])
        utilization = await self._calculate_type_utilization(agent_type)
        queued_tasks = len([t for t in self.task_queue if t.agent_type == agent_type])
        
        # Simple heuristic: scale based on utilization and queue length
        if utilization > 0.8 or queued_tasks > 2:
            return min(current_count + 1, self.config.max_agents_per_type.get(agent_type, 5))
        elif utilization < 0.3 and queued_tasks == 0:
            return max(current_count - 1, self.config.min_agents_per_type.get(agent_type, 1))
        
        return current_count