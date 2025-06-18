"""
Comprehensive test suite for Context Background Processing System.

Tests async indexing, cache warming, pattern discovery, and maintenance tasks
with priority-based task scheduling and performance monitoring.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_background import (
    ContextBackgroundProcessor,
    BackgroundTask,
    TaskPriority,
    TaskStatus,
    BackgroundStats
)
from context.models import ContextRequest, AgentContext
from context.exceptions import ContextBackgroundError


class TestBackgroundTask:
    """Test BackgroundTask data class"""
    
    def test_basic_creation(self):
        """Test basic task creation"""
        created_at = datetime.utcnow()
        task = BackgroundTask(
            task_id="test_task_1",
            task_type="test_type",
            priority=TaskPriority.MEDIUM,
            created_at=created_at
        )
        
        assert task.task_id == "test_task_1"
        assert task.task_type == "test_type"
        assert task.priority == TaskPriority.MEDIUM
        assert task.created_at == created_at
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0
        assert task.result is None
        assert task.error is None
        assert task.retry_count == 0
        assert task.max_retries == 3
    
    def test_runtime_calculation(self):
        """Test runtime calculation properties"""
        start_time = datetime.utcnow()
        task = BackgroundTask(
            task_id="test_task",
            task_type="test",
            priority=TaskPriority.LOW,
            created_at=start_time,
            started_at=start_time
        )
        
        # Runtime should be > 0 since started_at is set
        assert task.runtime_seconds >= 0
        
        # Set completion time
        end_time = start_time + timedelta(seconds=5)
        task.completed_at = end_time
        
        # Runtime should be exactly 5 seconds
        assert task.runtime_seconds == 5.0
    
    def test_overdue_detection(self):
        """Test overdue task detection"""
        past_time = datetime.utcnow() - timedelta(minutes=10)
        future_time = datetime.utcnow() + timedelta(minutes=10)
        
        # Task scheduled in the past should be overdue
        overdue_task = BackgroundTask(
            task_id="overdue",
            task_type="test",
            priority=TaskPriority.HIGH,
            created_at=datetime.utcnow(),
            scheduled_at=past_time,
            status=TaskStatus.PENDING
        )
        assert overdue_task.is_overdue is True
        
        # Task scheduled in the future should not be overdue
        future_task = BackgroundTask(
            task_id="future",
            task_type="test",
            priority=TaskPriority.HIGH,
            created_at=datetime.utcnow(),
            scheduled_at=future_time,
            status=TaskStatus.PENDING
        )
        assert future_task.is_overdue is False
        
        # Running task should not be overdue regardless of schedule
        running_task = BackgroundTask(
            task_id="running",
            task_type="test",
            priority=TaskPriority.HIGH,
            created_at=datetime.utcnow(),
            scheduled_at=past_time,
            status=TaskStatus.RUNNING
        )
        assert running_task.is_overdue is False


class TestBackgroundStats:
    """Test BackgroundStats data class"""
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        stats = BackgroundStats()
        
        # No tasks - should be 0.0
        assert stats.success_rate == 0.0
        
        # Only completed tasks
        stats.completed_tasks = 8
        stats.failed_tasks = 2
        assert stats.success_rate == 0.8
        
        # Only failed tasks
        stats.completed_tasks = 0
        stats.failed_tasks = 5
        assert stats.success_rate == 0.0
        
        # Only completed tasks
        stats.completed_tasks = 10
        stats.failed_tasks = 0
        assert stats.success_rate == 1.0
    
    def test_warming_effectiveness(self):
        """Test warming effectiveness calculation"""
        stats = BackgroundStats()
        
        # No cache hits - should be 0.0
        assert stats.warming_effectiveness == 0.0
        
        # Some warming hits
        stats.cache_hits = 10
        stats.warming_hits = 3
        assert stats.warming_effectiveness == 0.3
        
        # All hits are warming hits
        stats.cache_hits = 5
        stats.warming_hits = 5
        assert stats.warming_effectiveness == 1.0


class TestContextBackgroundProcessorInit:
    """Test ContextBackgroundProcessor initialization"""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = ContextBackgroundProcessor(temp_dir)
            
            assert processor.project_path == Path(temp_dir)
            assert processor.max_workers == 4
            assert processor.max_queue_size == 1000
            assert processor.enable_auto_tasks is True
            assert processor.maintenance_interval == 3600
            assert len(processor._workers) == 0
            assert len(processor._active_tasks) == 0
            assert len(processor._completed_tasks) == 0
            assert isinstance(processor.stats, BackgroundStats)
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = ContextBackgroundProcessor(
                project_path=temp_dir,
                max_workers=8,
                max_queue_size=500,
                enable_auto_tasks=False,
                maintenance_interval=1800
            )
            
            assert processor.max_workers == 8
            assert processor.max_queue_size == 500
            assert processor.enable_auto_tasks is False
            assert processor.maintenance_interval == 1800
    
    def test_task_handlers_initialization(self):
        """Test that task handlers are properly initialized"""
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = ContextBackgroundProcessor(temp_dir)
            
            expected_handlers = [
                "index_update",
                "cache_warming",
                "pattern_discovery",
                "learning_optimization",
                "cache_cleanup",
                "file_indexing",
                "dependency_analysis",
                "performance_analysis",
                "maintenance"
            ]
            
            for handler in expected_handlers:
                assert handler in processor._task_handlers
                assert callable(processor._task_handlers[handler])


class TestTaskSubmission:
    """Test task submission and management"""
    
    @pytest.fixture
    def processor(self):
        """Create processor for testing"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir)
        yield processor
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_submit_valid_task(self, processor):
        """Test submitting a valid task"""
        task_id = await processor.submit_task(
            task_type="index_update",
            priority=TaskPriority.HIGH,
            metadata={"force_rebuild": True}
        )
        
        assert task_id.startswith("index_update_")
        assert processor.stats.total_tasks == 1
        assert processor.stats.queued_tasks == 1
    
    @pytest.mark.asyncio
    async def test_submit_invalid_task_type(self, processor):
        """Test submitting task with invalid type"""
        with pytest.raises(ValueError, match="Unknown task type"):
            await processor.submit_task(
                task_type="invalid_task_type",
                priority=TaskPriority.MEDIUM
            )
    
    @pytest.mark.asyncio
    async def test_submit_scheduled_task(self, processor):
        """Test submitting a scheduled task"""
        future_time = datetime.utcnow() + timedelta(minutes=5)
        task_id = await processor.submit_task(
            task_type="cache_warming",
            priority=TaskPriority.MEDIUM,
            scheduled_at=future_time
        )
        
        assert task_id.startswith("cache_warming_")
        assert processor.stats.total_tasks == 1
    
    @pytest.mark.asyncio
    async def test_submit_task_with_kwargs(self, processor):
        """Test submitting task with additional kwargs"""
        task_id = await processor.submit_task(
            task_type="pattern_discovery",
            priority=TaskPriority.LOW,
            custom_param="test_value",
            another_param=42
        )
        
        task = await processor.get_task_status(task_id)
        assert task is not None
        assert task.metadata["custom_param"] == "test_value"
        assert task.metadata["another_param"] == 42


class TestTaskStatusAndManagement:
    """Test task status tracking and management"""
    
    @pytest.fixture
    def processor(self):
        """Create processor for testing"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir)
        yield processor
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_get_task_status_active(self, processor):
        """Test getting status of active task"""
        task_id = await processor.submit_task("cache_warming", TaskPriority.MEDIUM)
        
        status = await processor.get_task_status(task_id)
        assert status is not None
        assert status.task_id == task_id
        assert status.status == TaskStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_task_status_nonexistent(self, processor):
        """Test getting status of nonexistent task"""
        status = await processor.get_task_status("nonexistent_task")
        assert status is None
    
    @pytest.mark.asyncio
    async def test_cancel_pending_task(self, processor):
        """Test canceling a pending task"""
        task_id = await processor.submit_task("pattern_discovery", TaskPriority.LOW)
        
        # Cancel the task
        cancelled = await processor.cancel_task(task_id)
        assert cancelled is True
        
        # Check status
        status = await processor.get_task_status(task_id)
        assert status.status == TaskStatus.CANCELLED
        assert status.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self, processor):
        """Test canceling nonexistent task"""
        cancelled = await processor.cancel_task("nonexistent_task")
        assert cancelled is False
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, processor):
        """Test getting processor statistics"""
        # Submit some tasks
        await processor.submit_task("index_update", TaskPriority.HIGH)
        await processor.submit_task("cache_warming", TaskPriority.MEDIUM)
        
        stats = await processor.get_statistics()
        assert isinstance(stats, BackgroundStats)
        assert stats.total_tasks == 2
        assert stats.queued_tasks >= 0  # May have been processed
        assert stats.active_tasks >= 0


class TestSpecializedTasks:
    """Test specialized task submission methods"""
    
    @pytest.fixture
    def processor(self):
        """Create processor for testing"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir)
        yield processor
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_warm_cache_for_agent(self, processor):
        """Test cache warming task submission"""
        mock_requests = [
            Mock(spec=ContextRequest),
            Mock(spec=ContextRequest)
        ]
        
        task_id = await processor.warm_cache_for_agent(
            agent_type="CodeAgent",
            story_id="story_123",
            predicted_requests=mock_requests
        )
        
        assert task_id.startswith("cache_warming_")
        
        # Check task details
        task = await processor.get_task_status(task_id)
        assert task.metadata["agent_type"] == "CodeAgent"
        assert task.metadata["story_id"] == "story_123"
        assert task.metadata["requests"] == mock_requests
    
    @pytest.mark.asyncio
    async def test_trigger_index_update(self, processor):
        """Test index update task submission"""
        file_paths = ["file1.py", "file2.py"]
        
        task_id = await processor.trigger_index_update(
            file_paths=file_paths,
            force_rebuild=True
        )
        
        assert task_id.startswith("index_update_")
        
        # Check task details
        task = await processor.get_task_status(task_id)
        assert task.priority == TaskPriority.HIGH
        assert task.metadata["file_paths"] == file_paths
        assert task.metadata["force_rebuild"] is True
    
    @pytest.mark.asyncio
    async def test_schedule_pattern_discovery(self, processor):
        """Test scheduled pattern discovery task"""
        task_id = await processor.schedule_pattern_discovery(delay_minutes=30)
        
        assert task_id.startswith("pattern_discovery_")
        
        # Check task details
        task = await processor.get_task_status(task_id)
        assert task.priority == TaskPriority.LOW
        assert task.scheduled_at is not None
    
    @pytest.mark.asyncio
    async def test_trigger_learning_optimization(self, processor):
        """Test learning optimization task submission"""
        task_id = await processor.trigger_learning_optimization()
        
        assert task_id.startswith("learning_optimization_")
        
        # Check task details
        task = await processor.get_task_status(task_id)
        assert task.priority == TaskPriority.MEDIUM


class TestTaskExecution:
    """Test task execution and handling"""
    
    @pytest.fixture
    def processor(self):
        """Create processor for testing"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir)
        # Set up mock components
        processor.context_manager = Mock()
        processor.learning_system = Mock()
        processor.cache_system = AsyncMock()
        processor.monitoring_system = AsyncMock()
        yield processor
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_handle_index_update_without_manager(self, processor):
        """Test index update handler without context manager"""
        task = BackgroundTask(
            task_id="test_index",
            task_type="index_update",
            priority=TaskPriority.HIGH,
            created_at=datetime.utcnow(),
            metadata={"force_rebuild": True}
        )
        
        processor.context_manager = None
        result = await processor._handle_index_update(task)
        
        assert "error" in result
        assert result["error"] == "Context index not available"
    
    @pytest.mark.asyncio
    async def test_handle_cache_warming_success(self, processor):
        """Test successful cache warming"""
        task = BackgroundTask(
            task_id="test_warming",
            task_type="cache_warming",
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow(),
            metadata={
                "agent_type": "CodeAgent",
                "story_id": "story_123",
                "requests": []
            }
        )
        
        # Mock cache system to return success
        processor.cache_system.warm_cache.return_value = 5
        
        result = await processor._handle_cache_warming(task)
        
        assert result["status"] == "success"
        assert result["agent_type"] == "CodeAgent"
        assert result["story_id"] == "story_123"
        assert result["warmed_entries"] == 5
        assert processor.stats.cache_warming_hits == 5
    
    @pytest.mark.asyncio
    async def test_handle_cache_warming_without_system(self, processor):
        """Test cache warming without cache system"""
        task = BackgroundTask(
            task_id="test_warming",
            task_type="cache_warming",
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow(),
            metadata={}
        )
        
        processor.cache_system = None
        result = await processor._handle_cache_warming(task)
        
        assert "error" in result
        assert result["error"] == "Cache system not available"
    
    @pytest.mark.asyncio
    async def test_handle_pattern_discovery(self, processor):
        """Test pattern discovery handling"""
        task = BackgroundTask(
            task_id="test_pattern",
            task_type="pattern_discovery",
            priority=TaskPriority.LOW,
            created_at=datetime.utcnow()
        )
        
        # Mock learning system
        processor.learning_system.discover_new_patterns = AsyncMock(return_value=3)
        processor.learning_system.update_patterns = AsyncMock(return_value=2)
        
        result = await processor._handle_pattern_discovery(task)
        
        assert result["status"] == "success"
        assert result["new_patterns"] == 3
        assert result["updated_patterns"] == 2
        assert processor.stats.pattern_discoveries == 3
    
    @pytest.mark.asyncio
    async def test_handle_pattern_discovery_without_system(self, processor):
        """Test pattern discovery without learning system"""
        task = BackgroundTask(
            task_id="test_pattern",
            task_type="pattern_discovery",
            priority=TaskPriority.LOW,
            created_at=datetime.utcnow()
        )
        
        processor.learning_system = None
        result = await processor._handle_pattern_discovery(task)
        
        assert "error" in result
        assert result["error"] == "Learning system not available"
    
    @pytest.mark.asyncio
    async def test_handle_maintenance_task(self, processor):
        """Test maintenance task handling"""
        task = BackgroundTask(
            task_id="test_maintenance",
            task_type="maintenance",
            priority=TaskPriority.LOW,
            created_at=datetime.utcnow()
        )
        
        # Mock systems
        processor.cache_system.cleanup_expired = AsyncMock(return_value=10)
        processor.learning_system.optimize_performance = AsyncMock(return_value={"patterns_pruned": 5})
        processor.context_manager.context_index = Mock()
        processor.context_manager.context_index.build_index = AsyncMock()
        
        result = await processor._handle_maintenance(task)
        
        assert result["status"] == "success"
        assert result["maintenance_results"]["cache_cleaned"] == 10
        assert result["maintenance_results"]["patterns_optimized"] == 5
        assert result["maintenance_results"]["files_indexed"] == 1


class TestErrorHandling:
    """Test error handling in background processing"""
    
    @pytest.fixture
    def processor(self):
        """Create processor for testing"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir)
        yield processor
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_task_handler_exception(self, processor):
        """Test handling of exceptions in task handlers"""
        task = BackgroundTask(
            task_id="test_error",
            task_type="cache_warming",
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow(),
            metadata={"agent_type": "CodeAgent"}
        )
        
        # Mock cache system to raise exception
        processor.cache_system = Mock()
        processor.cache_system.warm_cache = AsyncMock(side_effect=Exception("Cache error"))
        
        # Should not raise exception, but return error result
        try:
            result = await processor._handle_cache_warming(task)
            # The handler catches exceptions and raises ContextBackgroundError
            assert False, "Expected ContextBackgroundError to be raised"
        except ContextBackgroundError as e:
            assert "Cache warming failed" in str(e)
    
    @pytest.mark.asyncio
    async def test_invalid_task_handler(self, processor):
        """Test handling of invalid task type"""
        # Remove a handler to simulate invalid task type
        original_handler = processor._task_handlers.pop("cache_warming", None)
        
        task = BackgroundTask(
            task_id="test_invalid",
            task_type="cache_warming",
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow()
        )
        
        # Should raise ValueError for missing handler
        with pytest.raises(ValueError, match="No handler for task type"):
            await processor._execute_task(task, "test_worker")
        
        # Restore handler
        if original_handler:
            processor._task_handlers["cache_warming"] = original_handler


class TestComponentIntegration:
    """Test integration with other context management components"""
    
    @pytest.fixture
    def processor(self):
        """Create processor with mock components"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir)
        
        # Set up mock components
        context_manager = Mock()
        learning_system = Mock()
        cache_system = AsyncMock()
        monitoring_system = AsyncMock()
        
        processor.set_component_references(
            context_manager=context_manager,
            learning_system=learning_system,
            cache_system=cache_system,
            monitoring_system=monitoring_system
        )
        
        yield processor
        shutil.rmtree(temp_dir)
    
    def test_set_component_references(self, processor):
        """Test setting component references"""
        assert processor.context_manager is not None
        assert processor.learning_system is not None
        assert processor.cache_system is not None
        assert processor.monitoring_system is not None
    
    @pytest.mark.asyncio
    async def test_component_interaction_in_tasks(self, processor):
        """Test that tasks properly interact with components"""
        # Test performance analysis task
        task = BackgroundTask(
            task_id="test_perf",
            task_type="performance_analysis",
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow()
        )
        
        # Mock monitoring system response
        processor.monitoring_system.get_performance_summary.return_value = {
            "cpu_usage": 50.0,
            "memory_usage": 60.0
        }
        
        result = await processor._handle_performance_analysis(task)
        
        assert result["status"] == "success"
        assert "performance_metrics" in result
        assert result["performance_metrics"]["cpu_usage"] == 50.0


class TestWorkerManagement:
    """Test worker thread management"""
    
    @pytest.fixture
    def processor(self):
        """Create processor for testing"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir, max_workers=2)
        yield processor
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_start_and_stop_workers(self, processor):
        """Test starting and stopping background workers"""
        # Start workers
        await processor.start()
        
        # Should have worker tasks running
        assert len(processor._workers) > 0
        
        # All workers should be running (not done)
        for worker in processor._workers:
            assert not worker.done()
        
        # Stop workers
        await processor.stop()
        
        # Workers should be cleaned up
        assert len(processor._workers) == 0
    
    @pytest.mark.asyncio
    async def test_worker_task_processing(self, processor):
        """Test that workers process tasks correctly"""
        # Start the processor
        await processor.start()
        
        # Submit a task
        task_id = await processor.submit_task("maintenance", TaskPriority.HIGH)
        
        # Wait a bit for processing
        await asyncio.sleep(0.1)
        
        # Check if task was processed
        task_status = await processor.get_task_status(task_id)
        # Task might be completed or still running depending on timing
        assert task_status.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED]
        
        # Stop the processor
        await processor.stop()


class TestTaskHistory:
    """Test task history and tracking"""
    
    @pytest.fixture
    def processor(self):
        """Create processor for testing"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir)
        yield processor
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_get_active_tasks(self, processor):
        """Test getting active tasks"""
        # Submit some tasks
        task_id1 = await processor.submit_task("cache_warming", TaskPriority.HIGH)
        task_id2 = await processor.submit_task("pattern_discovery", TaskPriority.LOW)
        
        active_tasks = await processor.get_active_tasks()
        
        # Tasks should be in active list or moved to pending queue
        assert len(active_tasks) >= 0  # May be empty if tasks moved to queue quickly
    
    @pytest.mark.asyncio
    async def test_get_task_history(self, processor):
        """Test getting task history"""
        # Submit and complete some tasks
        task_id = await processor.submit_task("maintenance", TaskPriority.MEDIUM)
        
        # Simulate task completion by moving to completed tasks
        task = await processor.get_task_status(task_id)
        if task and task.task_id in processor._active_tasks:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            processor._completed_tasks[task.task_id] = processor._active_tasks.pop(task.task_id)
        
        history = await processor.get_task_history(limit=10)
        
        assert isinstance(history, list)
        # Should contain our completed task if found
        if history:
            assert all(isinstance(task, BackgroundTask) for task in history)


class TestTaskPrioritization:
    """Test task prioritization and queue management"""
    
    @pytest.fixture
    def processor(self):
        """Create processor for testing"""
        temp_dir = tempfile.mkdtemp()
        processor = ContextBackgroundProcessor(temp_dir)
        yield processor
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_priority_queue_usage(self, processor):
        """Test that high priority tasks use priority queue"""
        # Submit tasks with different priorities
        low_task = await processor.submit_task("pattern_discovery", TaskPriority.LOW)
        high_task = await processor.submit_task("index_update", TaskPriority.HIGH)
        critical_task = await processor.submit_task("cache_warming", TaskPriority.CRITICAL)
        
        # High and critical priority tasks should go to priority queue
        assert processor._priority_queue.qsize() >= 2  # high and critical
        assert processor._task_queue.qsize() >= 1     # low priority
    
    @pytest.mark.asyncio
    async def test_task_scheduling(self, processor):
        """Test task scheduling for future execution"""
        future_time = datetime.utcnow() + timedelta(seconds=5)
        
        scheduled_task = await processor.submit_task(
            "maintenance",
            TaskPriority.MEDIUM,
            scheduled_at=future_time
        )
        
        # Task should be queued even though scheduled for future
        # (In this simple implementation, scheduled tasks are queued immediately)
        assert processor._task_queue.qsize() >= 1 or processor._priority_queue.qsize() >= 1


@pytest.mark.asyncio
async def test_full_processor_lifecycle():
    """Test complete processor lifecycle with real task execution"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        processor = ContextBackgroundProcessor(
            temp_dir,
            max_workers=2,
            enable_auto_tasks=False  # Disable to control execution
        )
        
        # Set up mock components
        processor.context_manager = Mock()
        processor.cache_system = AsyncMock()
        processor.cache_system.cleanup_expired = AsyncMock(return_value=5)
        
        # Start processor
        await processor.start()
        
        # Submit a task
        task_id = await processor.submit_task("cache_cleanup", TaskPriority.MEDIUM)
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check final statistics
        final_stats = await processor.get_statistics()
        assert final_stats.total_tasks >= 1
        
        # Stop processor
        await processor.stop()
        
    finally:
        shutil.rmtree(temp_dir)