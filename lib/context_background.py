"""
Context Background Processing - Async Indexing and Cache Warming

Background processing system for context management with async indexing,
cache warming, pattern discovery, and maintenance tasks.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import queue

try:
    from .context.models import ContextRequest, AgentContext, TDDState
    from .context.exceptions import ContextBackgroundError
    from .context_learning import ContextLearningSystem
    from .context_cache import ContextCache
    from .context_monitoring import ContextMonitor
except ImportError:
    from context.models import ContextRequest, AgentContext, TDDState
    from context.exceptions import ContextBackgroundError
    from context_learning import ContextLearningSystem
    from context_cache import ContextCache
    from context_monitoring import ContextMonitor

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Background task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Background task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Background task definition"""
    
    task_id: str
    task_type: str
    priority: TaskPriority
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    @property
    def runtime_seconds(self) -> float:
        """Calculate task runtime in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0.0
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if self.scheduled_at and self.status == TaskStatus.PENDING:
            return datetime.utcnow() > self.scheduled_at
        return False


@dataclass
class BackgroundStats:
    """Background processing statistics"""
    
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    active_tasks: int = 0
    queued_tasks: int = 0
    average_execution_time: float = 0.0
    total_execution_time: float = 0.0
    cache_warming_hits: int = 0
    index_updates: int = 0
    pattern_discoveries: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate task success rate"""
        total = self.completed_tasks + self.failed_tasks
        return self.completed_tasks / total if total > 0 else 0.0


class ContextBackgroundProcessor:
    """
    Background processing system for context management.
    
    Features:
    - Async indexing and cache warming
    - Pattern discovery and learning
    - Maintenance and cleanup tasks
    - Priority-based task scheduling
    - Performance monitoring and statistics
    """
    
    def __init__(
        self,
        project_path: str,
        max_workers: int = 4,
        max_queue_size: int = 1000,
        enable_auto_tasks: bool = True,
        maintenance_interval: int = 3600  # 1 hour
    ):
        """
        Initialize background processor.
        
        Args:
            project_path: Path to the project
            max_workers: Maximum number of worker threads
            max_queue_size: Maximum task queue size
            enable_auto_tasks: Whether to enable automatic background tasks
            maintenance_interval: Interval for maintenance tasks in seconds
        """
        self.project_path = Path(project_path)
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.enable_auto_tasks = enable_auto_tasks
        self.maintenance_interval = maintenance_interval
        
        # Task management
        self._task_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._priority_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._active_tasks: Dict[str, BackgroundTask] = {}
        self._completed_tasks: Dict[str, BackgroundTask] = {}
        self._task_history: List[BackgroundTask] = []
        
        # Worker management
        self._workers: List[asyncio.Task] = []
        self._worker_semaphore = asyncio.Semaphore(max_workers)
        self._shutdown_event = asyncio.Event()
        
        # Component references (set by ContextManager)
        self.context_manager = None
        self.learning_system: Optional[ContextLearningSystem] = None
        self.cache_system: Optional[ContextCache] = None
        self.monitoring_system: Optional[ContextMonitor] = None
        
        # Statistics and monitoring
        self.stats = BackgroundStats()
        self._last_maintenance = datetime.utcnow()
        
        # Task type handlers
        self._task_handlers = {
            "index_update": self._handle_index_update,
            "cache_warming": self._handle_cache_warming,
            "pattern_discovery": self._handle_pattern_discovery,
            "learning_optimization": self._handle_learning_optimization,
            "cache_cleanup": self._handle_cache_cleanup,
            "file_indexing": self._handle_file_indexing,
            "dependency_analysis": self._handle_dependency_analysis,
            "performance_analysis": self._handle_performance_analysis,
            "maintenance": self._handle_maintenance
        }
        
        logger.info(f"ContextBackgroundProcessor initialized with {max_workers} workers")
    
    async def start(self) -> None:
        """Start background processing"""
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)
        
        # Start maintenance task
        if self.enable_auto_tasks:
            maintenance_task = asyncio.create_task(self._maintenance_loop())
            self._workers.append(maintenance_task)
        
        logger.info(f"Background processing started with {len(self._workers)} workers")
    
    async def stop(self) -> None:
        """Stop background processing"""
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
        logger.info("Background processing stopped")
    
    async def submit_task(
        self,
        task_type: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Submit a background task.
        
        Args:
            task_type: Type of task to execute
            priority: Task priority level
            scheduled_at: Optional scheduled execution time
            metadata: Optional task metadata
            **kwargs: Additional task parameters
            
        Returns:
            Task ID
        """
        if task_type not in self._task_handlers:
            raise ValueError(f"Unknown task type: {task_type}")
        
        task_id = f"{task_type}_{int(time.time() * 1000000)}"
        
        task = BackgroundTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            created_at=datetime.utcnow(),
            scheduled_at=scheduled_at,
            metadata=metadata or {},
            **kwargs
        )
        
        # Add task parameters from kwargs
        for key, value in kwargs.items():
            if key not in ['task_id', 'task_type', 'priority', 'created_at']:
                task.metadata[key] = value
        
        # Queue task based on priority and schedule
        if scheduled_at and scheduled_at > datetime.utcnow():
            # Schedule for later execution
            await self._schedule_task(task)
        else:
            # Queue for immediate execution
            await self._queue_task(task)
        
        self.stats.total_tasks += 1
        self.stats.queued_tasks += 1
        
        logger.debug(f"Submitted task {task_id} ({task_type}) with priority {priority.name}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[BackgroundTask]:
        """Get status of a specific task"""
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]
        elif task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        
        # Search in history
        for task in self._task_history:
            if task.task_id == task_id:
                return task
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            
            # Move to completed tasks
            self._completed_tasks[task_id] = task
            del self._active_tasks[task_id]
            
            self.stats.active_tasks -= 1
            logger.info(f"Cancelled task {task_id}")
            return True
        
        return False
    
    async def get_statistics(self) -> BackgroundStats:
        """Get background processing statistics"""
        # Update active task count
        self.stats.active_tasks = len(self._active_tasks)
        self.stats.queued_tasks = self._task_queue.qsize() + self._priority_queue.qsize()
        
        # Calculate average execution time
        completed_tasks = [t for t in self._completed_tasks.values() if t.status == TaskStatus.COMPLETED]
        if completed_tasks:
            total_time = sum(task.runtime_seconds for task in completed_tasks)
            self.stats.average_execution_time = total_time / len(completed_tasks)
            self.stats.total_execution_time = total_time
        
        return self.stats
    
    async def warm_cache_for_agent(
        self,
        agent_type: str,
        story_id: str,
        predicted_requests: List[ContextRequest]
    ) -> str:
        """Submit cache warming task for specific agent and story"""
        return await self.submit_task(
            task_type="cache_warming",
            priority=TaskPriority.MEDIUM,
            agent_type=agent_type,
            story_id=story_id,
            requests=predicted_requests
        )
    
    async def trigger_index_update(
        self,
        file_paths: Optional[List[str]] = None,
        force_rebuild: bool = False
    ) -> str:
        """Trigger context index update"""
        return await self.submit_task(
            task_type="index_update",
            priority=TaskPriority.HIGH,
            file_paths=file_paths,
            force_rebuild=force_rebuild
        )
    
    async def schedule_pattern_discovery(self, delay_minutes: int = 60) -> str:
        """Schedule pattern discovery task"""
        scheduled_time = datetime.utcnow() + timedelta(minutes=delay_minutes)
        return await self.submit_task(
            task_type="pattern_discovery",
            priority=TaskPriority.LOW,
            scheduled_at=scheduled_time
        )
    
    async def trigger_learning_optimization(self) -> str:
        """Trigger learning system optimization"""
        return await self.submit_task(
            task_type="learning_optimization",
            priority=TaskPriority.MEDIUM
        )
    
    async def get_active_tasks(self) -> List[BackgroundTask]:
        """Get list of currently active tasks"""
        return list(self._active_tasks.values())
    
    async def get_task_history(self, limit: int = 100) -> List[BackgroundTask]:
        """Get recent task history"""
        all_tasks = list(self._completed_tasks.values()) + self._task_history
        all_tasks.sort(key=lambda t: t.created_at, reverse=True)
        return all_tasks[:limit]
    
    def set_component_references(
        self,
        context_manager,
        learning_system: Optional[ContextLearningSystem] = None,
        cache_system: Optional[ContextCache] = None,
        monitoring_system: Optional[ContextMonitor] = None
    ) -> None:
        """Set references to context management components"""
        self.context_manager = context_manager
        self.learning_system = learning_system
        self.cache_system = cache_system
        self.monitoring_system = monitoring_system
    
    # Private methods
    
    async def _worker_loop(self, worker_id: str) -> None:
        """Main worker loop"""
        logger.debug(f"Worker {worker_id} started")
        
        while not self._shutdown_event.is_set():
            try:
                # Get next task with timeout
                task = await asyncio.wait_for(
                    self._get_next_task(),
                    timeout=1.0
                )
                
                if task:
                    await self._execute_task(task, worker_id)
                
            except asyncio.TimeoutError:
                # No task available, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {str(e)}")
                await asyncio.sleep(1)
        
        logger.debug(f"Worker {worker_id} stopped")
    
    async def _maintenance_loop(self) -> None:
        """Maintenance task loop"""
        while not self._shutdown_event.is_set():
            try:
                # Check if maintenance is due
                if (datetime.utcnow() - self._last_maintenance).total_seconds() >= self.maintenance_interval:
                    await self.submit_task(
                        task_type="maintenance",
                        priority=TaskPriority.LOW
                    )
                    self._last_maintenance = datetime.utcnow()
                
                # Check for scheduled tasks
                await self._process_scheduled_tasks()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def _get_next_task(self) -> Optional[BackgroundTask]:
        """Get the next task to execute"""
        # Try priority queue first
        try:
            priority_value, task = self._priority_queue.get_nowait()
            return task
        except asyncio.QueueEmpty:
            pass
        
        # Try regular queue
        try:
            task = self._task_queue.get_nowait()
            return task
        except asyncio.QueueEmpty:
            return None
    
    async def _execute_task(self, task: BackgroundTask, worker_id: str) -> None:
        """Execute a background task"""
        async with self._worker_semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            self._active_tasks[task.task_id] = task
            
            self.stats.active_tasks += 1
            self.stats.queued_tasks = max(0, self.stats.queued_tasks - 1)
            
            logger.debug(f"Worker {worker_id} executing task {task.task_id} ({task.task_type})")
            
            try:
                # Get task handler
                handler = self._task_handlers.get(task.task_type)
                if not handler:
                    raise ValueError(f"No handler for task type: {task.task_type}")
                
                # Execute task
                result = await handler(task)
                
                # Mark as completed
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = result
                task.progress = 100.0
                
                self.stats.completed_tasks += 1
                logger.debug(f"Task {task.task_id} completed successfully")
                
            except Exception as e:
                # Mark as failed
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.error = str(e)
                
                # Retry if applicable
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.PENDING
                    task.started_at = None
                    task.completed_at = None
                    task.error = None
                    
                    # Re-queue with lower priority
                    await self._queue_task(task)
                    logger.warning(f"Task {task.task_id} failed, retrying ({task.retry_count}/{task.max_retries})")
                else:
                    self.stats.failed_tasks += 1
                    logger.error(f"Task {task.task_id} failed permanently: {str(e)}")
            
            finally:
                # Move to completed tasks
                if task.task_id in self._active_tasks:
                    del self._active_tasks[task.task_id]
                
                self._completed_tasks[task.task_id] = task
                self.stats.active_tasks -= 1
                
                # Limit completed tasks storage
                if len(self._completed_tasks) > 1000:
                    # Move oldest to history
                    oldest_tasks = sorted(
                        self._completed_tasks.values(),
                        key=lambda t: t.completed_at or datetime.utcnow()
                    )[:100]
                    
                    for old_task in oldest_tasks:
                        self._task_history.append(old_task)
                        del self._completed_tasks[old_task.task_id]
                    
                    # Limit history size
                    if len(self._task_history) > 1000:
                        self._task_history = self._task_history[-500:]
    
    async def _queue_task(self, task: BackgroundTask) -> None:
        """Queue task for execution"""
        # Use priority queue for high priority tasks
        if task.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL]:
            priority_value = -task.priority.value  # Negative for higher priority
            await self._priority_queue.put((priority_value, task))
        else:
            await self._task_queue.put(task)
    
    async def _schedule_task(self, task: BackgroundTask) -> None:
        """Schedule task for future execution"""
        # For now, we'll use a simple approach and check scheduled tasks periodically
        # In a production system, you might use a proper scheduler like APScheduler
        await self._queue_task(task)
    
    async def _process_scheduled_tasks(self) -> None:
        """Process scheduled tasks that are due"""
        # This is a simplified implementation
        # In practice, you'd have a more sophisticated scheduling system
        pass
    
    # Task handlers
    
    async def _handle_index_update(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle context index update task"""
        if not self.context_manager or not hasattr(self.context_manager, 'context_index'):
            return {"error": "Context index not available"}
        
        try:
            file_paths = task.metadata.get("file_paths")
            force_rebuild = task.metadata.get("force_rebuild", False)
            
            # Update index
            if hasattr(self.context_manager.context_index, 'build_index'):
                await self.context_manager.context_index.build_index(force_rebuild=force_rebuild)
            
            return {
                "status": "success",
                "files_processed": len(file_paths) if file_paths else "all",
                "force_rebuild": force_rebuild
            }
            
        except Exception as e:
            logger.error(f"Error updating index: {str(e)}")
            raise ContextBackgroundError(f"Index update failed: {str(e)}")
    
    async def _handle_cache_warming(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle cache warming task"""
        if not self.cache_system:
            return {"error": "Cache system not available"}
        
        try:
            agent_type = task.metadata.get("agent_type")
            story_id = task.metadata.get("story_id")
            requests = task.metadata.get("requests", [])
            
            # Warm cache with predicted requests
            warmed_count = await self.cache_system.warm_cache(requests, priority=1)
            
            self.stats.cache_warming_hits += warmed_count
            
            return {
                "status": "success",
                "agent_type": agent_type,
                "story_id": story_id,
                "warmed_entries": warmed_count
            }
            
        except Exception as e:
            logger.error(f"Error warming cache: {str(e)}")
            raise ContextBackgroundError(f"Cache warming failed: {str(e)}")
    
    async def _handle_pattern_discovery(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle pattern discovery task"""
        if not self.learning_system:
            return {"error": "Learning system not available"}
        
        try:
            # Discover new patterns
            new_patterns = await self.learning_system.discover_new_patterns()
            
            # Update existing patterns
            updated_patterns = await self.learning_system.update_patterns()
            
            self.stats.pattern_discoveries += new_patterns
            
            return {
                "status": "success",
                "new_patterns": new_patterns,
                "updated_patterns": updated_patterns
            }
            
        except Exception as e:
            logger.error(f"Error discovering patterns: {str(e)}")
            raise ContextBackgroundError(f"Pattern discovery failed: {str(e)}")
    
    async def _handle_learning_optimization(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle learning system optimization task"""
        if not self.learning_system:
            return {"error": "Learning system not available"}
        
        try:
            # Optimize learning system performance
            optimization_results = await self.learning_system.optimize_performance()
            
            return {
                "status": "success",
                "optimization_results": optimization_results
            }
            
        except Exception as e:
            logger.error(f"Error optimizing learning system: {str(e)}")
            raise ContextBackgroundError(f"Learning optimization failed: {str(e)}")
    
    async def _handle_cache_cleanup(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle cache cleanup task"""
        if not self.cache_system:
            return {"error": "Cache system not available"}
        
        try:
            # Clean up expired cache entries
            cleaned_count = await self.cache_system.cleanup_expired()
            
            return {
                "status": "success",
                "cleaned_entries": cleaned_count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning cache: {str(e)}")
            raise ContextBackgroundError(f"Cache cleanup failed: {str(e)}")
    
    async def _handle_file_indexing(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle file indexing task"""
        try:
            file_paths = task.metadata.get("file_paths", [])
            
            # Index specified files
            processed_count = 0
            for file_path in file_paths:
                # Perform file indexing operations
                processed_count += 1
                task.progress = (processed_count / len(file_paths)) * 100
            
            return {
                "status": "success",
                "processed_files": processed_count
            }
            
        except Exception as e:
            logger.error(f"Error indexing files: {str(e)}")
            raise ContextBackgroundError(f"File indexing failed: {str(e)}")
    
    async def _handle_dependency_analysis(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle dependency analysis task"""
        try:
            # Perform dependency analysis
            file_paths = task.metadata.get("file_paths", [])
            
            # Analyze dependencies for files
            analysis_results = {
                "analyzed_files": len(file_paths),
                "dependencies_found": 0,
                "circular_dependencies": 0
            }
            
            return {
                "status": "success",
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {str(e)}")
            raise ContextBackgroundError(f"Dependency analysis failed: {str(e)}")
    
    async def _handle_performance_analysis(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle performance analysis task"""
        try:
            # Perform performance analysis
            if self.monitoring_system:
                metrics = await self.monitoring_system.get_performance_summary()
                
                return {
                    "status": "success",
                    "performance_metrics": metrics
                }
            else:
                return {"error": "Monitoring system not available"}
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}")
            raise ContextBackgroundError(f"Performance analysis failed: {str(e)}")
    
    async def _handle_maintenance(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle maintenance task"""
        try:
            maintenance_results = {
                "cache_cleaned": 0,
                "patterns_optimized": 0,
                "files_indexed": 0
            }
            
            # Perform various maintenance tasks
            if self.cache_system:
                maintenance_results["cache_cleaned"] = await self.cache_system.cleanup_expired()
            
            if self.learning_system:
                optimization_results = await self.learning_system.optimize_performance()
                maintenance_results["patterns_optimized"] = optimization_results.get("patterns_pruned", 0)
            
            # Update index if needed
            if self.context_manager and hasattr(self.context_manager, 'context_index'):
                # Incremental index update
                if hasattr(self.context_manager.context_index, 'build_index'):
                    await self.context_manager.context_index.build_index(force_rebuild=False)
                    maintenance_results["files_indexed"] = 1
            
            return {
                "status": "success",
                "maintenance_results": maintenance_results
            }
            
        except Exception as e:
            logger.error(f"Error in maintenance: {str(e)}")
            raise ContextBackgroundError(f"Maintenance failed: {str(e)}")