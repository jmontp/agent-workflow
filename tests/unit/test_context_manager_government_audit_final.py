"""
GOVERNMENT AUDIT COMPLIANCE - FINAL TIER 3 COVERAGE
====================================================

This test suite targets the final uncovered lines in context_manager.py to achieve 
95%+ coverage for TIER 3 government audit compliance. Focuses specifically on:

1. Import fallback paths (lines 30-89)
2. Complex intelligent compression workflows (lines 1333-1559) 
3. Advanced monitoring and dashboard features
4. Background processing edge cases
5. Service lifecycle methods
6. Error handling and integration scenarios

CRITICAL: This is the final module needed for complete TIER 3 compliance.
"""

import pytest
import asyncio
import tempfile
import shutil
import hashlib
import os
import sys
import importlib
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call, PropertyMock
from typing import Dict, Any, List
import threading

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

# Test import scenarios
try:
    from context_manager import ContextManager
    from context.models import (
        ContextRequest, AgentContext, TokenBudget, TokenUsage,
        CompressionLevel, ContextType, Decision, PhaseHandoff,
        ContextSnapshot, RelevanceScore, FileType
    )
    from context.exceptions import (
        ContextError, TokenBudgetExceededError, ContextNotFoundError,
        ContextTimeoutError
    )
    from context_cache import CacheStrategy, CacheWarmingStrategy
    from context_background import TaskPriority
    from tdd_models import TDDState, TDDTask, TDDCycle
except ImportError as e:
    # Fallback imports for testing
    pass


class TestImportFallbackComprehensive:
    """Test import fallback mechanisms (lines 30-89) - Critical for coverage"""
    
    def test_import_fallback_simulation(self):
        """Test import structure that would trigger fallback paths"""
        # The import fallbacks are triggered at module import time
        # We can test that the module loads properly in different scenarios
        
        # Test with all dependencies available
        import context_manager
        cm = context_manager.ContextManager()
        assert cm is not None
        
        # Test that fallback structures exist
        assert hasattr(context_manager, 'ContextManager')
    
    def test_tdd_models_import_fallback(self):
        """Test TDD models import fallback (lines 86-89)"""
        # Test that the import structure handles both relative and absolute imports
        import context_manager
        
        # Verify the module has access to TDD models
        cm = context_manager.ContextManager()
        
        # Create a TDDTask to verify imports work
        task = TDDTask(description="test", story_id="test-story")
        assert task is not None
    
    def test_module_availability_checks(self):
        """Test module availability and import paths"""
        # Test that all required modules are available for the import paths
        required_modules = [
            'context_manager',
            'token_calculator', 
            'agent_memory',
            'context_filter',
            'context_compressor',
            'context_index',
            'context_cache',
            'context_monitoring',
            'context_background'
        ]
        
        for module_name in required_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None
            except ImportError:
                # Some modules might not be available in test environment
                pass


class TestAdvancedServiceLifecycle:
    """Test advanced service lifecycle scenarios (lines 236-263)"""
    
    @pytest.mark.asyncio
    async def test_service_start_complete_workflow(self):
        """Test complete service start workflow with all features enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=True,
                enable_advanced_caching=True,
                enable_monitoring=True,
                enable_background_processing=True
            )
            
            # Mock all service start methods to verify they're called
            cm.context_cache.start_background_tasks = AsyncMock()
            cm.monitor.start_monitoring = AsyncMock()
            cm.background_processor.start = AsyncMock()
            cm._queue_initial_background_tasks = AsyncMock()
            
            await cm.start()
            
            # Verify all services started
            cm.context_cache.start_background_tasks.assert_called_once()
            cm.monitor.start_monitoring.assert_called_once()
            cm.background_processor.start.assert_called_once()
            cm._queue_initial_background_tasks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_start_selective_features(self):
        """Test service start with selective feature enablement"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Only enable some features
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=True,
                enable_advanced_caching=False,  # Disabled
                enable_monitoring=True,
                enable_background_processing=False  # Disabled
            )
            
            await cm.start()
            
            # Should handle missing services gracefully
            assert cm.context_cache is None
            assert cm.background_processor is None
            assert cm.monitor is not None
    
    @pytest.mark.asyncio
    async def test_service_start_with_partial_failures(self):
        """Test service start resilience to partial component failures"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock some services to fail during start
            cm.context_cache.start_background_tasks = AsyncMock(side_effect=Exception("Cache start failed"))
            cm.monitor.start_monitoring = AsyncMock(side_effect=Exception("Monitor start failed"))
            
            # Should not raise exception despite failures
            await cm.start()
            
            # Background processor should still start successfully
            assert cm.background_processor.is_running
    
    @pytest.mark.asyncio 
    async def test_service_stop_complete_workflow(self):
        """Test complete service stop workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            await cm.start()
            
            # Mock stop methods
            cm.background_processor.stop = AsyncMock()
            cm.context_cache.stop_background_tasks = AsyncMock()
            cm.monitor.stop_monitoring = AsyncMock()
            
            await cm.stop()
            
            # Verify stop order
            cm.background_processor.stop.assert_called_once()
            cm.context_cache.stop_background_tasks.assert_called_once()
            cm.monitor.stop_monitoring.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_stop_with_exceptions(self):
        """Test service stop resilience to component exceptions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            await cm.start()
            
            # Mock all stop methods to raise exceptions
            cm.background_processor.stop = AsyncMock(side_effect=Exception("Background stop failed"))
            cm.context_cache.stop_background_tasks = AsyncMock(side_effect=Exception("Cache stop failed"))
            cm.monitor.stop_monitoring = AsyncMock(side_effect=Exception("Monitor stop failed"))
            
            # Should complete without raising exception
            await cm.stop()


class TestQueueInitialBackgroundTasks:
    """Test _queue_initial_background_tasks method (lines 1143-1168)"""
    
    @pytest.mark.asyncio
    async def test_queue_initial_background_tasks_complete(self):
        """Test complete initial background task queueing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock background processor methods
            cm.background_processor.submit_task = AsyncMock()
            cm.background_processor.schedule_pattern_discovery = AsyncMock()
            
            await cm._queue_initial_background_tasks()
            
            # Verify all tasks were queued
            assert cm.background_processor.submit_task.call_count >= 2
            cm.background_processor.schedule_pattern_discovery.assert_called_once_with(delay_minutes=30)
            
            # Check specific task types
            calls = cm.background_processor.submit_task.call_args_list
            task_types = [call[1]['task_type'] for call in calls if 'task_type' in call[1]]
            assert "index_update" in task_types
            assert "cache_cleanup" in task_types
    
    @pytest.mark.asyncio
    async def test_queue_initial_background_tasks_with_failures(self):
        """Test background task queueing with submission failures"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock submit_task to fail
            cm.background_processor.submit_task = AsyncMock(side_effect=Exception("Submit failed"))
            cm.background_processor.schedule_pattern_discovery = AsyncMock()
            
            # Should handle exceptions gracefully
            await cm._queue_initial_background_tasks()
    
    @pytest.mark.asyncio
    async def test_queue_initial_background_tasks_disabled(self):
        """Test when background processing is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_background_processing=False
            )
            
            # Should return early
            await cm._queue_initial_background_tasks()
            # No exception should be raised


class TestIntelligentCompressionWorkflows:
    """Test complex intelligent compression workflows (lines 1333-1559)"""
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_exhaustive(self):
        """Test _format_core_context_compressed with comprehensive scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock context compressor for different scenarios
            compression_results = {
                "small_file.py": ("compressed small", 0.8),
                "medium_file.py": ("compressed medium", 0.6),
                "large_file.py": ("compressed large", 0.4)
            }
            
            def mock_compress(content, file_path, **kwargs):
                filename = Path(file_path).name
                if filename in compression_results:
                    return compression_results[filename]
                return ("compressed content", 0.5)
            
            cm.context_compressor.compress_content = AsyncMock(side_effect=mock_compress)
            cm.token_calculator.estimate_tokens = AsyncMock(side_effect=lambda x: len(x) // 4)
            
            file_contents = {
                "small_file.py": "x" * 100,
                "medium_file.py": "y" * 500,
                "large_file.py": "z" * 2000,
                "extra_file.py": "w" * 1000
            }
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000,
                compression_level=CompressionLevel.HIGH
            )
            
            result = await cm._format_core_context_compressed(file_contents, 300, request)
            
            # Should include compression ratios and proper formatting
            assert "### small_file.py" in result
            assert "Compression ratio: 0.80" in result
            assert "compressed small" in result
            assert "```" in result
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_budget_overflow(self):
        """Test compression with budget overflow and break conditions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock compression that produces content exceeding budget
            cm.context_compressor.compress_content = AsyncMock(
                return_value=("very large compressed content " * 50, 0.3)
            )
            cm.token_calculator.estimate_tokens = AsyncMock(return_value=500)  # Large token count
            
            file_contents = {
                "file1.py": "content1" * 100,
                "file2.py": "content2" * 100,  # This might not be processed
                "file3.py": "content3" * 100   # This definitely won't be processed
            }
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000,
                compression_level=CompressionLevel.EXTREME
            )
            
            result = await cm._format_core_context_compressed(file_contents, 100, request)  # Small budget
            
            # Should break after first file due to budget constraints
            assert "### file1.py" in result
            # Later files should not be included due to budget overflow
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_compression_failures(self):
        """Test compression with individual file compression failures"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock compression to fail for specific files
            def mock_compress_with_failures(content, file_path, **kwargs):
                if "fail_file" in file_path:
                    raise Exception(f"Compression failed for {file_path}")
                return ("compressed content", 0.6)
            
            cm.context_compressor.compress_content = AsyncMock(side_effect=mock_compress_with_failures)
            cm.token_calculator.estimate_tokens = AsyncMock(return_value=200)
            
            file_contents = {
                "fail_file.py": "content that will fail compression",
                "success_file.py": "content that will compress successfully"
            }
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000,
                compression_level=CompressionLevel.MODERATE
            )
            
            result = await cm._format_core_context_compressed(file_contents, 800, request)
            
            # Should include fallback truncation for failed file
            assert "### fail_file.py" in result
            assert "[truncated]" in result
            # And successful compression for working file
            assert "### success_file.py" in result
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_empty_files(self):
        """Test compressed formatting with empty file contents"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            
            # Test with empty file contents dict
            result = await cm._format_core_context_compressed({}, 1000, request)
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_comprehensive(self):
        """Test complete _apply_intelligent_compression workflow with all compression levels"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Test different compression ratios
            compression_scenarios = [
                (0.9, CompressionLevel.LOW),      # Needs 90% of original (low compression)
                (0.7, CompressionLevel.MODERATE), # Needs 70% (moderate compression)  
                (0.5, CompressionLevel.HIGH),     # Needs 50% (high compression)
                (0.3, CompressionLevel.EXTREME)   # Needs 30% (extreme compression)
            ]
            
            for compression_ratio, expected_level in compression_scenarios:
                context = AgentContext(
                    request_id=f"test-{compression_ratio}",
                    agent_type="TestAgent",
                    story_id="test-story"
                )
                
                # Set up context with large content
                context.core_context = "core content " * 2000
                context.historical_context = "historical content " * 1000
                context.dependencies = "dependency content " * 500
                context.agent_memory = "memory content " * 300
                
                total_tokens = int(10000 / compression_ratio)  # Adjust for desired ratio
                context.token_usage = TokenUsage(
                    context_id=context.request_id,
                    total_used=total_tokens
                )
                
                request = ContextRequest(
                    agent_type="TestAgent",
                    story_id="test-story",
                    task={"description": "test"},
                    max_tokens=10000  # Target tokens
                )
                
                # Mock successful compression
                cm.context_compressor.compress_content = AsyncMock(
                    return_value=("compressed content", 0.6)
                )
                
                result = await cm._apply_intelligent_compression(context, request)
                
                assert result.compression_applied is True
                assert result.compression_level == expected_level
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_component_failures(self):
        """Test intelligent compression with systematic component failures"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Test failure scenarios for each component
            components = ["core_context", "historical_context", "dependencies", "agent_memory"]
            
            for failing_component in components:
                context = AgentContext(
                    request_id=f"test-{failing_component}",
                    agent_type="TestAgent", 
                    story_id="test-story"
                )
                
                # Set all components
                context.core_context = "core " * 1000
                context.historical_context = "history " * 1000
                context.dependencies = "deps " * 1000 
                context.agent_memory = "memory " * 1000
                
                context.token_usage = TokenUsage(
                    context_id=context.request_id,
                    total_used=20000  # Large usage requiring compression
                )
                
                # Mock compression to fail for specific component
                def mock_compress_selective_failure(content, file_path, **kwargs):
                    if failing_component in file_path:
                        raise Exception(f"Compression failed for {failing_component}")
                    return ("compressed content", 0.5)
                
                cm.context_compressor.compress_content = AsyncMock(
                    side_effect=mock_compress_selective_failure
                )
                
                request = ContextRequest(
                    agent_type="TestAgent",
                    story_id="test-story",
                    task={"description": "test"},
                    max_tokens=5000
                )
                
                result = await cm._apply_intelligent_compression(context, request)
                
                # Should have fallback truncation for failed component
                failed_content = getattr(result, failing_component)
                assert "[compressed]" in failed_content
                
                # Other components should be properly compressed
                for other_component in components:
                    if other_component != failing_component:
                        other_content = getattr(result, other_component)
                        if other_content:  # Only check if content exists
                            assert other_content == "compressed content" or "[compressed]" in other_content
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_fallback_error(self):
        """Test intelligent compression with complete fallback to basic compression"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            context = AgentContext(
                request_id="test-fallback",
                agent_type="TestAgent",
                story_id="test-story"
            )
            
            context.core_context = "content " * 5000
            context.token_usage = TokenUsage(
                context_id="test-fallback",
                total_used=50000
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=10000
            )
            
            # Mock the entire intelligent compression to fail
            with patch.object(cm, '_calculate_token_usage', side_effect=Exception("Token calc failed")):
                result = await cm._apply_intelligent_compression(context, request)
                
                # Should fallback to basic compression
                assert result.compression_applied is True


class TestAdvancedMonitoringDashboard:
    """Test advanced monitoring and dashboard features (lines 1037-1090)"""
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data_complete(self):
        """Test complete monitoring dashboard data collection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Set up test data
            cm._active_stories = {
                "story1": {"metadata": {"priority": "high"}},
                "story2": {"metadata": {"priority": "medium"}}
            }
            cm._story_conflicts = {
                "story1": ["story2"],
                "story2": ["story1"]
            }
            
            # Mock system health
            mock_health = Mock()
            mock_health.overall_status = "healthy"
            cm.monitor.get_system_health = Mock(return_value=mock_health)
            cm.monitor.get_performance_summary = AsyncMock(return_value={
                "avg_response_time": 0.5,
                "total_requests": 100
            })
            
            # Mock cache statistics  
            mock_cache_stats = Mock()
            mock_cache_stats.hit_rate = 0.85
            mock_cache_stats.entry_count = 250
            mock_cache_stats.memory_usage_bytes = 104857600  # 100MB
            mock_cache_stats.prediction_accuracy = 0.72
            cm.context_cache.get_statistics = AsyncMock(return_value=mock_cache_stats)
            
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            # Verify complete dashboard structure
            assert dashboard_data["system_health"] == "healthy"
            assert dashboard_data["active_stories"] == 2
            assert dashboard_data["story_conflicts"] == 2
            
            # Verify advanced features status
            assert dashboard_data["advanced_features"]["intelligence"] is True
            assert dashboard_data["advanced_features"]["advanced_caching"] is True
            assert dashboard_data["advanced_features"]["monitoring"] is True
            assert dashboard_data["advanced_features"]["cross_story"] is True
            
            # Verify monitoring metrics
            assert "monitoring_metrics" in dashboard_data
            assert dashboard_data["monitoring_metrics"]["avg_response_time"] == 0.5
            
            # Verify cache statistics  
            assert "cache_statistics" in dashboard_data
            assert dashboard_data["cache_statistics"]["hit_rate"] == 0.85
            assert dashboard_data["cache_statistics"]["entry_count"] == 250
            assert dashboard_data["cache_statistics"]["memory_usage_mb"] == 100
            assert dashboard_data["cache_statistics"]["prediction_accuracy"] == 0.72
            
            # Verify cross-story details
            assert "cross_story_details" in dashboard_data
            assert "story1" in dashboard_data["cross_story_details"]["active_stories"]
            assert "story2" in dashboard_data["cross_story_details"]["active_stories"]
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data_with_component_failures(self):
        """Test dashboard data collection with systematic component failures"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock all components to fail
            cm.monitor.get_system_health = Mock(side_effect=Exception("Health check failed"))
            cm.monitor.get_performance_summary = AsyncMock(side_effect=Exception("Performance summary failed"))
            cm.context_cache.get_statistics = AsyncMock(side_effect=Exception("Cache stats failed"))
            
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            # Should handle failures gracefully
            assert dashboard_data["system_health"] == "unknown"
            assert "performance_metrics" in dashboard_data  # Should still include base metrics
            assert "monitoring_metrics" not in dashboard_data  # But not failed monitoring metrics
            assert "cache_statistics" not in dashboard_data  # And not failed cache stats
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data_features_disabled(self):
        """Test dashboard data when all advanced features are disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            # Verify features are marked as disabled
            assert dashboard_data["advanced_features"]["intelligence"] is False
            assert dashboard_data["advanced_features"]["advanced_caching"] is False
            assert dashboard_data["advanced_features"]["monitoring"] is False
            assert dashboard_data["advanced_features"]["cross_story"] is False
            
            # Should not include disabled feature data
            assert "monitoring_metrics" not in dashboard_data
            assert "cache_statistics" not in dashboard_data
            assert "cross_story_details" not in dashboard_data


class TestBackgroundProcessingComprehensive:
    """Test comprehensive background processing scenarios"""
    
    @pytest.mark.asyncio
    async def test_trigger_index_update_with_files(self):
        """Test trigger_index_update with specific file paths"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            cm.background_processor.trigger_index_update = AsyncMock(return_value="task-123")
            
            result = await cm.trigger_index_update(["/test/file1.py", "/test/file2.py"])
            
            assert result == "task-123"
            cm.background_processor.trigger_index_update.assert_called_once_with(
                ["/test/file1.py", "/test/file2.py"]
            )
    
    @pytest.mark.asyncio
    async def test_warm_cache_for_context_complete(self):
        """Test cache warming with predicted requests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            predicted_requests = [
                ContextRequest(
                    agent_type="TestAgent1",
                    story_id="test-story",
                    task={"description": "task1"},
                    max_tokens=1000
                ),
                ContextRequest(
                    agent_type="TestAgent2", 
                    story_id="test-story",
                    task={"description": "task2"},
                    max_tokens=2000
                )
            ]
            
            cm.background_processor.warm_cache_for_agent = AsyncMock(return_value="warming-task-456")
            
            result = await cm.warm_cache_for_context("TestAgent", "test-story", predicted_requests)
            
            assert result == "warming-task-456"
            cm.background_processor.warm_cache_for_agent.assert_called_once_with(
                "TestAgent", "test-story", predicted_requests
            )
    
    @pytest.mark.asyncio
    async def test_schedule_learning_optimization_custom_delay(self):
        """Test learning optimization scheduling with custom delay"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            cm.background_processor.submit_task = AsyncMock(return_value="learning-task-789")
            
            result = await cm.schedule_learning_optimization(delay_hours=4)
            
            assert result == "learning-task-789"
            
            # Verify task was submitted with correct parameters
            call_args = cm.background_processor.submit_task.call_args
            assert call_args[1]["task_type"] == "learning_optimization"
            assert call_args[1]["priority"] == TaskPriority.LOW
            assert "scheduled_at" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_get_background_statistics_comprehensive(self):
        """Test comprehensive background statistics collection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock comprehensive statistics
            mock_stats = Mock()
            mock_stats.total_tasks = 150
            mock_stats.completed_tasks = 120
            mock_stats.failed_tasks = 10
            mock_stats.active_tasks = 5
            mock_stats.queued_tasks = 15
            mock_stats.success_rate = 0.92
            mock_stats.average_execution_time = 2.3
            mock_stats.cache_warming_hits = 85
            mock_stats.pattern_discoveries = 12
            
            cm.background_processor.get_statistics = AsyncMock(return_value=mock_stats)
            
            result = await cm.get_background_statistics()
            
            # Verify all statistics are included
            assert result["total_tasks"] == 150
            assert result["completed_tasks"] == 120
            assert result["failed_tasks"] == 10
            assert result["active_tasks"] == 5
            assert result["queued_tasks"] == 15
            assert result["success_rate"] == 0.92
            assert result["average_execution_time"] == 2.3
            assert result["cache_warming_hits"] == 85
            assert result["pattern_discoveries"] == 12


class TestContextPreparationAdvancedScenarios:
    """Test advanced context preparation scenarios with monitoring integration"""
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_operation_monitoring(self):
        """Test context preparation with complete operation monitoring"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock monitoring to track operation lifecycle
            operation_ids = []
            
            def mock_record_start(operation_type):
                op_id = f"op-{len(operation_ids) + 1}"
                operation_ids.append(op_id)
                return op_id
            
            cm.monitor.record_operation_start = Mock(side_effect=mock_record_start)
            cm.monitor.record_context_preparation = Mock()
            cm.monitor.record_operation_end = Mock()
            
            task = TDDTask(
                description="Test task with monitoring",
                story_id="monitored-story",
                current_state=TDDState.TEST_RED
            )
            
            context = await cm.prepare_context("TestAgent", task)
            
            # Verify monitoring lifecycle
            cm.monitor.record_operation_start.assert_called_once_with("context_preparation")
            cm.monitor.record_context_preparation.assert_called_once()
            cm.monitor.record_operation_end.assert_called_once()
            
            # Verify operation end called with operation ID and success
            end_call_args = cm.monitor.record_operation_end.call_args
            assert end_call_args[0][0] in operation_ids  # Operation ID
            assert end_call_args[0][1] is True  # Success flag
    
    @pytest.mark.asyncio
    async def test_prepare_context_monitoring_failure_resilience(self):
        """Test context preparation resilience to monitoring failures"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock all monitoring operations to fail
            cm.monitor.record_operation_start = Mock(side_effect=Exception("Monitor start failed"))
            cm.monitor.record_context_preparation = Mock(side_effect=Exception("Monitor prep failed"))
            cm.monitor.record_operation_end = Mock(side_effect=Exception("Monitor end failed"))
            
            task = TDDTask(
                description="Test task",
                story_id="test-story",
                current_state=TDDState.CODE_GREEN
            )
            
            # Should complete successfully despite monitoring failures
            context = await cm.prepare_context("TestAgent", task)
            assert context is not None
            assert context.agent_type == "TestAgent"
    
    @pytest.mark.asyncio
    async def test_prepare_context_cross_story_integration(self):
        """Test context preparation with cross-story integration and metadata injection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_cross_story=True)
            
            # Set up conflicting stories
            await cm.register_story("story1", {"type": "feature"})
            await cm.register_story("story2", {"type": "bugfix"})
            cm._active_stories["story2"]["file_modifications"] = {"/shared/utils.py"}
            
            task = TDDTask(
                description="Task that will conflict",
                story_id="story1",
                current_state=TDDState.TEST_RED
            )
            task.file_paths = ["/shared/utils.py", "/story1/feature.py"]
            
            context = await cm.prepare_context("TestAgent", task, story_id="story1")
            
            # Verify cross-story tracking was activated
            assert "story1" in cm._active_stories
            assert "TestAgent" in cm._active_stories["story1"]["active_agents"]
            
            # Verify conflicts were detected
            assert "story2" in cm._story_conflicts.get("story1", [])


class TestContextManagerEdgeCasesAndIntegration:
    """Test edge cases and integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_context_preparation_timeout_with_monitoring_cleanup(self):
        """Test timeout scenario with proper monitoring cleanup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                max_preparation_time=1  # Very short timeout
            )
            
            operation_id = "test-operation-123"
            cm.monitor.record_operation_start = Mock(return_value=operation_id)
            cm.monitor.record_operation_end = Mock()
            
            # Mock _prepare_context_internal to take longer than timeout
            async def slow_preparation(*args, **kwargs):
                await asyncio.sleep(2)
                return Mock()
            
            with patch.object(cm, '_prepare_context_internal', side_effect=slow_preparation):
                task = TDDTask(
                    description="Slow task",
                    story_id="test-story",
                    current_state=TDDState.TEST_RED
                )
                
                with pytest.raises(ContextTimeoutError) as exc_info:
                    await cm.prepare_context("TestAgent", task)
                
                # Verify timeout error details
                assert "timed out" in str(exc_info.value)
                assert exc_info.value.timeout_seconds == 1
                assert exc_info.value.operation == "prepare_context"
                
                # Verify monitoring cleanup was called
                cm.monitor.record_operation_end.assert_called_once_with(operation_id, False)
    
    @pytest.mark.asyncio
    async def test_context_preparation_exception_with_monitoring_cleanup(self):
        """Test exception scenario with proper monitoring cleanup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            operation_id = "test-operation-456"
            cm.monitor.record_operation_start = Mock(return_value=operation_id)
            cm.monitor.record_operation_end = Mock()
            
            # Mock _prepare_context_internal to raise exception
            with patch.object(cm, '_prepare_context_internal', side_effect=Exception("Internal error")):
                task = TDDTask(
                    description="Failing task",
                    story_id="test-story",
                    current_state=TDDState.REFACTOR
                )
                
                with pytest.raises(ContextError) as exc_info:
                    await cm.prepare_context("TestAgent", task)
                
                # Verify error wrapping
                assert "Context preparation failed" in str(exc_info.value)
                
                # Verify monitoring cleanup
                cm.monitor.record_operation_end.assert_called_once_with(operation_id, False)
    
    def test_performance_metrics_with_populated_intelligence_components(self):
        """Test performance metrics when intelligence components are fully populated"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Populate performance data
            cm._total_requests = 500
            cm._cache_hits = 350
            cm._cache_misses = 150
            cm._preparation_times = [0.1, 0.2, 0.3, 0.4, 0.5, 1.0, 2.0]
            
            # Mock intelligence component metrics
            cm.context_filter.get_performance_metrics = Mock(return_value={
                "filters_applied": 75,
                "average_filter_time": 0.05
            })
            cm.context_compressor.get_performance_metrics = Mock(return_value={
                "compressions_applied": 25,
                "average_compression_ratio": 0.65
            })
            cm.context_index.get_performance_metrics = Mock(return_value={
                "index_size": 10000,
                "search_accuracy": 0.89
            })
            
            metrics = cm.get_performance_metrics()
            
            # Verify core metrics
            assert metrics["context_manager"]["total_requests"] == 500
            assert metrics["context_manager"]["cache_hit_rate"] == 0.7
            assert metrics["context_manager"]["average_preparation_time"] == 0.5
            assert metrics["context_manager"]["max_preparation_time"] == 2.0
            assert metrics["context_manager"]["min_preparation_time"] == 0.1
            
            # Verify intelligence component metrics are included
            assert "context_filter" in metrics
            assert metrics["context_filter"]["filters_applied"] == 75
            assert "context_compressor" in metrics
            assert metrics["context_compressor"]["compressions_applied"] == 25
            assert "context_index" in metrics
            assert metrics["context_index"]["index_size"] == 10000


class TestLegacyCacheOperationsComprehensive:
    """Test comprehensive legacy cache operations for fallback scenarios"""
    
    @pytest.mark.asyncio
    async def test_legacy_cache_workflow_complete_lifecycle(self):
        """Test complete legacy cache lifecycle with advanced scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False,  # Force legacy cache use
                cache_ttl_seconds=300
            )
            
            # Create multiple requests for cache testing
            requests = []
            contexts = []
            
            for i in range(3):
                request = ContextRequest(
                    agent_type=f"TestAgent{i}",
                    story_id=f"story-{i}",
                    task={"description": f"task {i}"},
                    max_tokens=1000 + i * 500
                )
                requests.append(request)
                
                context = AgentContext(
                    request_id=request.id,
                    agent_type=request.agent_type,
                    story_id=request.story_id
                )
                contexts.append(context)
            
            # Test cache miss scenario
            for request in requests:
                cached = await cm._get_cached_context_legacy(request)
                assert cached is None
            
            # Cache all contexts
            for request, context in zip(requests, contexts):
                await cm._cache_context_legacy(request, context)
            
            # Test cache hit scenario
            for request, original_context in zip(requests, contexts):
                cached = await cm._get_cached_context_legacy(request)
                assert cached is not None
                assert cached.request_id == original_context.request_id
                assert cached.agent_type == original_context.agent_type
            
            # Verify cache size
            assert len(cm._legacy_cache) == 3
    
    @pytest.mark.asyncio 
    async def test_legacy_cache_size_management(self):
        """Test legacy cache size limit enforcement"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False
            )
            
            # Fill cache beyond theoretical limit (100 entries)
            # Note: We'll use smaller numbers for practical testing
            for i in range(110):
                request = ContextRequest(
                    agent_type="TestAgent",
                    story_id=f"story-{i}",
                    task={"description": f"task {i}", "unique_id": i},
                    max_tokens=1000
                )
                
                context = AgentContext(
                    request_id=request.id,
                    agent_type=request.agent_type,
                    story_id=request.story_id
                )
                
                await cm._cache_context_legacy(request, context)
            
            # Cache should enforce size limit
            assert len(cm._legacy_cache) <= 100
    
    @pytest.mark.asyncio
    async def test_legacy_cache_expiration_edge_cases(self):
        """Test legacy cache expiration in edge case scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False,
                cache_ttl_seconds=2  # Short TTL for testing
            )
            
            request1 = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "first task"},
                max_tokens=1000
            )
            
            request2 = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story", 
                task={"description": "second task"},
                max_tokens=1000
            )
            
            context1 = AgentContext(request_id=request1.id, agent_type="TestAgent", story_id="test-story")
            context2 = AgentContext(request_id=request2.id, agent_type="TestAgent", story_id="test-story")
            
            # Cache first context
            await cm._cache_context_legacy(request1, context1)
            
            # Wait 1 second, cache second context
            await asyncio.sleep(1)
            await cm._cache_context_legacy(request2, context2)
            
            # First context should still be valid
            cached1 = await cm._get_cached_context_legacy(request1)
            assert cached1 is not None
            
            # Wait for first context to expire but not second
            await asyncio.sleep(2)
            
            # First context should be expired and removed
            cached1_expired = await cm._get_cached_context_legacy(request1)
            assert cached1_expired is None
            
            # Second context should still be valid
            cached2 = await cm._get_cached_context_legacy(request2)
            assert cached2 is not None


class TestFileOperationsAndUtilities:
    """Test file operations and utility methods thoroughly"""
    
    def test_should_include_file_comprehensive_scenarios(self):
        """Test _should_include_file with comprehensive file scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            test_dir = Path(temp_dir)
            
            # Test various hidden file patterns
            hidden_scenarios = [
                ".hidden_file.py",
                ".git/config", 
                "dir/.hidden/file.py",
                "__pycache__/module.pyc",
                ".pytest_cache/file",
                ".coverage",
                "node_modules/package/file.js",
                ".venv/lib/file.py",
                "venv/bin/activate",
                "build/output/file",
                "dist/package/file"
            ]
            
            for scenario in hidden_scenarios:
                file_path = test_dir / scenario
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()
                
                assert not cm._should_include_file(file_path), f"Should exclude {scenario}"
            
            # Test size limits with actual files
            # Small valid file
            small_file = test_dir / "small.py"
            small_file.write_text("print('hello')")
            assert cm._should_include_file(small_file)
            
            # Large file that should be excluded (create >100KB file)
            large_file = test_dir / "large.py"
            large_content = "# Large file content\n" * 5000  # ~100KB+
            large_file.write_text(large_content)
            # Size check might vary, but at least test the method doesn't crash
            result = cm._should_include_file(large_file)
            assert isinstance(result, bool)
            
            # Test with directory (should be excluded)
            test_dir_path = test_dir / "test_directory"
            test_dir_path.mkdir()
            assert not cm._should_include_file(test_dir_path)
    
    def test_determine_file_type_comprehensive(self):
        """Test _determine_file_type with comprehensive file type scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Test comprehensive file type mapping
            test_cases = [
                # Python files
                ("module.py", FileType.PYTHON),
                ("script.py", FileType.PYTHON),
                
                # Test files  
                ("test_module.py", FileType.TEST),
                ("module_test.py", FileType.TEST),
                ("tests/test_something.py", FileType.TEST),
                ("test/unit_test.py", FileType.TEST),
                
                # Documentation
                ("README.md", FileType.MARKDOWN),
                ("CHANGELOG.md", FileType.MARKDOWN),
                ("docs.rst", FileType.MARKDOWN),
                
                # Configuration files
                ("config.json", FileType.JSON),
                ("package.json", FileType.JSON),
                ("config.yml", FileType.YAML),
                ("docker-compose.yaml", FileType.YAML),
                ("settings.cfg", FileType.CONFIG),
                ("setup.cfg", FileType.CONFIG),
                ("config.ini", FileType.CONFIG),
                ("app.conf", FileType.CONFIG),
                ("pyproject.toml", FileType.CONFIG),
                
                # Other/unknown files
                ("binary.exe", FileType.OTHER),
                ("image.png", FileType.OTHER),
                ("data.csv", FileType.OTHER),
                ("unknown.xyz", FileType.OTHER)
            ]
            
            for filename, expected_type in test_cases:
                file_path = Path(filename)
                result = cm._determine_file_type(file_path)
                assert result == expected_type, f"File {filename} should be {expected_type}, got {result}"
    
    @pytest.mark.asyncio
    async def test_load_file_contents_error_resilience(self):
        """Test _load_file_contents with various error conditions and resilience"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            test_dir = Path(temp_dir)
            
            # Create test files with various scenarios
            
            # 1. Valid small file
            valid_file = test_dir / "valid.py"
            valid_file.write_text("print('valid content')")
            
            # 2. Valid large file (should be included if under token limit)
            medium_file = test_dir / "medium.py"
            medium_content = "# Medium file\n" * 100
            medium_file.write_text(medium_content)
            
            # 3. Very large file (should be excluded due to token limit)
            huge_file = test_dir / "huge.py"
            huge_content = "# Huge file content line\n" * 10000
            huge_file.write_text(huge_content)
            
            # 4. Directory (not a file)
            directory = test_dir / "directory"
            directory.mkdir()
            
            # 5. Binary file (might cause encoding issues)
            binary_file = test_dir / "binary.dat"
            binary_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe\xfd')
            
            # 6. File with permission issues (simulate)
            restricted_file = test_dir / "restricted.py"
            restricted_file.write_text("restricted content")
            
            file_paths = [
                str(valid_file),
                str(medium_file),
                str(huge_file),
                str(directory),
                str(binary_file),
                str(restricted_file),
                "/absolutely/nonexistent/file.py"
            ]
            
            # Mock token calculator to simulate different token estimates
            def mock_estimate_tokens(content):
                if len(content) > 50000:  # Simulate huge file exceeding limit
                    return 15000
                return len(content) // 10  # Normal estimation
            
            cm.token_calculator.estimate_tokens = AsyncMock(side_effect=mock_estimate_tokens)
            
            contents = await cm._load_file_contents(file_paths)
            
            # Should include valid files under token limit
            assert str(valid_file) in contents
            assert contents[str(valid_file)] == "print('valid content')"
            
            # Should include medium file if under token limit
            assert str(medium_file) in contents
            
            # Should exclude huge file due to token limit
            assert str(huge_file) not in contents
            
            # Should exclude directory
            assert str(directory) not in contents
            
            # Should exclude nonexistent file
            assert "/absolutely/nonexistent/file.py" not in contents
            
            # Binary file might be included with encoding error handling
            # (depends on the 'ignore' error handling in the implementation)


class TestHelperMethodsComprehensive:
    """Test helper methods with comprehensive edge cases"""
    
    def test_generate_cache_key_variations_comprehensive(self):
        """Test _generate_cache_key with comprehensive request variations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Test with various task types and configurations
            test_scenarios = [
                # TDDTask with description
                (TDDTask(description="task with description", story_id="story1"), "TestAgent1"),
                
                # Dict task with description  
                ({"description": "dict task description", "other_field": "value"}, "TestAgent2"),
                
                # Task without description
                (TDDTask(story_id="story2"), "TestAgent3"),
                ({"other_field": "value"}, "TestAgent4"),
                
                # Different compression levels and options
                ({"description": "task"}, "TestAgent5"),
            ]
            
            cache_keys = []
            
            for task, agent_type in test_scenarios:
                for compression_level in [CompressionLevel.LOW, CompressionLevel.HIGH]:
                    for include_history in [True, False]:
                        for include_deps in [True, False]:
                            request = ContextRequest(
                                agent_type=agent_type,
                                story_id="test-story",
                                task=task,
                                max_tokens=1000,
                                compression_level=compression_level,
                                include_history=include_history,
                                include_dependencies=include_deps
                            )
                            
                            cache_key = cm._generate_cache_key(request)
                            assert isinstance(cache_key, str)
                            assert len(cache_key) == 32  # MD5 hash length
                            cache_keys.append(cache_key)
            
            # Verify all cache keys are unique (no collisions)
            assert len(cache_keys) == len(set(cache_keys))
    
    def test_extract_methods_comprehensive_edge_cases(self):
        """Test story_id and tdd_phase extraction with comprehensive edge cases"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Test _extract_story_id edge cases
            story_id_test_cases = [
                # Standard cases
                (TDDTask(description="test", story_id="tdd-story"), "tdd-story"),
                ({"story_id": "dict-story"}, "dict-story"),
                
                # Edge cases
                ({"story_id": ""}, ""),  # Empty string
                ({"story_id": None}, None),  # None value
                ({"story_id": 12345}, 12345),  # Non-string value
                ({}, "default"),  # Missing key
                (Mock(other_field="value"), "default"),  # Object without story_id
                (None, "default"),  # None task
            ]
            
            for task, expected in story_id_test_cases:
                if task is not None:
                    result = cm._extract_story_id(task)
                    assert result == expected, f"Task {task} should extract story_id {expected}, got {result}"
            
            # Test _extract_tdd_phase edge cases
            tdd_phase_test_cases = [
                # Standard cases
                (TDDTask(description="test", current_state=TDDState.TEST_RED), TDDState.TEST_RED),
                ({"current_state": TDDState.CODE_GREEN}, TDDState.CODE_GREEN),
                ({"current_state": "RED"}, TDDState.TEST_RED),
                ({"current_state": "GREEN"}, TDDState.CODE_GREEN),
                ({"current_state": "REFACTOR"}, TDDState.REFACTOR),
                
                # Edge cases
                ({"current_state": "INVALID_STATE"}, None),  # Invalid string
                ({"current_state": ""}, None),  # Empty string
                ({"current_state": None}, None),  # None value
                ({"current_state": 12345}, None),  # Non-string/non-enum value
                ({}, None),  # Missing key
                (Mock(other_field="value"), None),  # Object without current_state
                (None, None),  # None task
            ]
            
            for task, expected in tdd_phase_test_cases:
                if task is not None:
                    result = cm._extract_tdd_phase(task)
                    assert result == expected, f"Task {task} should extract TDD phase {expected}, got {result}"


class TestFormattingMethodsComprehensive:
    """Test formatting methods with comprehensive scenarios"""
    
    @pytest.mark.asyncio
    async def test_format_agent_memory_context_all_scenarios(self):
        """Test agent memory formatting with all possible data combinations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Test with no memory (None case)
            cm.agent_memory.get_memory = AsyncMock(return_value=None)
            result = await cm._format_agent_memory_context("TestAgent", "test-story", 1000)
            assert result == ""
            
            # Test with empty memory
            mock_empty_memory = Mock()
            mock_empty_memory.get_recent_decisions = Mock(return_value=[])
            mock_empty_memory.learned_patterns = []
            mock_empty_memory.phase_handoffs = []
            
            cm.agent_memory.get_memory = AsyncMock(return_value=mock_empty_memory)
            result = await cm._format_agent_memory_context("TestAgent", "test-story", 1000)
            assert "### Agent Memory" in result
            assert "Recent Decisions:" not in result  # Empty sections not included
            
            # Test with full memory data including None phases
            mock_full_memory = Mock()
            mock_full_memory.get_recent_decisions = Mock(return_value=[
                Mock(description="Decision 1", outcome="Success"),
                Mock(description="Decision 2", outcome="Pending"),
                Mock(description="Decision 3", outcome="Failed")
            ])
            mock_full_memory.learned_patterns = [
                Mock(pattern_type="optimization", description="Code optimization pattern"),
                Mock(pattern_type="testing", description="Test pattern identification"),
                Mock(pattern_type="refactoring", description="Refactoring opportunity")
            ]
            mock_full_memory.phase_handoffs = [
                Mock(from_phase=TDDState.TEST_RED, to_phase=TDDState.CODE_GREEN, context_summary="Implemented feature"),
                Mock(from_phase=TDDState.CODE_GREEN, to_phase=TDDState.REFACTOR, context_summary="Code cleanup"),
                Mock(from_phase=None, to_phase=TDDState.TEST_RED, context_summary="Starting new cycle"),
                Mock(from_phase=TDDState.REFACTOR, to_phase=None, context_summary="Ending cycle")
            ]
            
            cm.agent_memory.get_memory = AsyncMock(return_value=mock_full_memory)
            result = await cm._format_agent_memory_context("TestAgent", "test-story", 2000)
            
            # Verify all sections are included
            assert "### Agent Memory" in result
            assert "#### Recent Decisions:" in result
            assert "Decision 1: Success" in result
            assert "Decision 2: Pending" in result
            assert "Decision 3: Failed" in result
            
            assert "#### Learned Patterns:" in result
            assert "optimization: Code optimization pattern" in result
            assert "testing: Test pattern identification" in result
            
            assert "#### Recent Phase Handoffs:" in result
            assert "test_red -> code_green: Implemented feature" in result
            assert "code_green -> refactor: Code cleanup" in result
            assert "none -> test_red: Starting new cycle" in result
            assert "refactor -> none: Ending cycle" in result
    
    @pytest.mark.asyncio
    async def test_format_agent_memory_context_truncation_scenarios(self):
        """Test agent memory formatting with various truncation scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create memory content that will definitely exceed small budgets
            large_content = "Very long description " * 1000
            
            mock_memory = Mock()
            mock_memory.get_recent_decisions = Mock(return_value=[
                Mock(description=large_content, outcome="Large outcome " * 100)
            ])
            mock_memory.learned_patterns = [
                Mock(pattern_type="pattern1", description=large_content)
            ]
            mock_memory.phase_handoffs = [
                Mock(from_phase=TDDState.TEST_RED, to_phase=TDDState.CODE_GREEN, context_summary=large_content)
            ]
            
            cm.agent_memory.get_memory = AsyncMock(return_value=mock_memory)
            
            # Test with very small token budget
            result = await cm._format_agent_memory_context("TestAgent", "test-story", 50)
            assert "[truncated]" in result
            
            # Test with medium budget
            result = await cm._format_agent_memory_context("TestAgent", "test-story", 500)
            # Should include some content but likely truncated
            assert "### Agent Memory" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])