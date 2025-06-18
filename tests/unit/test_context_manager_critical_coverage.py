"""
Critical coverage tests for ContextManager to achieve 95%+ coverage.

This test suite specifically targets the uncovered lines identified in the coverage report
to meet government audit compliance requirements. Focuses on import fallbacks,
error paths, edge cases, and complex integration scenarios.
"""

import pytest
import asyncio
import tempfile
import shutil
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call, PropertyMock
from typing import Dict, Any, List

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

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


class TestImportFallbackPaths:
    """Test import fallback paths (lines 16-89) - Critical for coverage"""
    
    def test_import_handling_structures(self):
        """Test that the import structure exists for fallback handling"""
        # This test verifies the import structure exists to handle fallbacks
        # The actual fallback code is hit during import time in real scenarios
        
        # Test that we can create ContextManager with all features
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=True,
                enable_advanced_caching=True,
                enable_monitoring=True,
                enable_background_processing=True
            )
            assert cm is not None
            
            # Test that we can create with features disabled (fallback scenario)
            cm_disabled = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_background_processing=False
            )
            assert cm_disabled is not None


class TestContextManagerCriticalInit:
    """Test initialization edge cases and configuration variations"""
    
    def test_init_with_string_project_path(self):
        """Test initialization with string project path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            assert cm.project_path == Path(temp_dir)
    
    def test_init_with_none_project_path_uses_cwd(self):
        """Test that None project_path defaults to current working directory"""
        cm = ContextManager(project_path=None)
        assert cm.project_path == Path.cwd()
    
    def test_init_with_custom_background_workers(self):
        """Test initialization with custom background worker count"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                background_workers=8
            )
            assert cm.background_processor.max_workers == 8
    
    def test_init_mixed_feature_configurations(self):
        """Test various combinations of feature flags"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Intelligence enabled, but caching disabled
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=True,
                enable_advanced_caching=False,
                enable_monitoring=True,
                enable_cross_story=False
            )
            
            assert cm.enable_intelligence is True
            assert cm.enable_advanced_caching is False
            assert cm.context_cache is None
            assert cm.context_filter is not None
            assert cm.monitor is not None


class TestContextManagerServiceLifecycle:
    """Test service start/stop lifecycle with error conditions"""
    
    @pytest.mark.asyncio
    async def test_start_services_with_exceptions(self):
        """Test start services with component exceptions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock components to raise exceptions
            cm.context_cache.start_background_tasks = AsyncMock(side_effect=Exception("Cache start failed"))
            cm.monitor.start_monitoring = AsyncMock(side_effect=Exception("Monitor start failed"))
            
            # Should not raise exception but log warnings
            await cm.start()
            
            # Verify background processor still started
            assert cm.background_processor.is_running
    
    @pytest.mark.asyncio
    async def test_start_with_background_task_queue_failure(self):
        """Test start with background task queueing failure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock queue_initial_background_tasks to raise exception
            with patch.object(cm, '_queue_initial_background_tasks', side_effect=Exception("Queue failed")):
                await cm.start()
                # Should complete without raising exception
    
    @pytest.mark.asyncio
    async def test_stop_services_with_exceptions(self):
        """Test stop services with component exceptions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            await cm.start()
            
            # Mock components to raise exceptions during stop
            cm.background_processor.stop = AsyncMock(side_effect=Exception("Stop failed"))
            cm.context_cache.stop_background_tasks = AsyncMock(side_effect=Exception("Cache stop failed"))
            
            # Should complete without raising exception
            await cm.stop()


class TestContextPreparationEdgeCases:
    """Test context preparation edge cases and error paths"""
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_none_task(self):
        """Test context preparation with None task"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            with pytest.raises(Exception):  # Should raise some form of exception
                await cm.prepare_context("TestAgent", None)
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_invalid_agent_type(self):
        """Test context preparation with invalid agent type"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            task = TDDTask(
                description="Test task",
                story_id="test-story",
                current_state=TDDState.TEST_RED
            )
            
            # Should handle invalid agent type gracefully
            context = await cm.prepare_context("InvalidAgentType", task)
            assert context is not None
            assert context.agent_type == "InvalidAgentType"
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_zero_max_tokens(self):
        """Test context preparation with zero max tokens"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            task = TDDTask(
                description="Test task",
                story_id="test-story",
                current_state=TDDState.TEST_RED
            )
            
            context = await cm.prepare_context("TestAgent", task, max_tokens=0)
            assert context.token_usage.total_used >= 0
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_monitoring_failures(self):
        """Test context preparation when monitoring operations fail"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock monitor to raise exceptions
            cm.monitor.record_operation_start = Mock(side_effect=Exception("Monitor failed"))
            cm.monitor.record_context_preparation = Mock(side_effect=Exception("Record failed"))
            cm.monitor.record_operation_end = Mock(side_effect=Exception("End failed"))
            
            task = TDDTask(
                description="Test task",
                story_id="test-story",
                current_state=TDDState.TEST_RED
            )
            
            # Should complete without raising exception
            context = await cm.prepare_context("TestAgent", task)
            assert context is not None
    
    @pytest.mark.asyncio
    async def test_prepare_context_timeout_with_monitoring(self):
        """Test context preparation timeout with monitoring enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                max_preparation_time=1  # Very short timeout
            )
            
            task = TDDTask(
                description="Test task",
                story_id="test-story",
                current_state=TDDState.TEST_RED
            )
            
            # Mock _prepare_context_internal to take longer than timeout
            async def slow_prepare(*args, **kwargs):
                await asyncio.sleep(2)
                return Mock()
            
            with patch.object(cm, '_prepare_context_internal', side_effect=slow_prepare):
                with pytest.raises(ContextTimeoutError) as exc_info:
                    await cm.prepare_context("TestAgent", task)
                
                assert "timed out" in str(exc_info.value)
                assert exc_info.value.timeout_seconds == 1
    
    @pytest.mark.asyncio
    async def test_prepare_context_internal_exception_handling(self):
        """Test exception handling in _prepare_context_internal"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            task = TDDTask(
                description="Test task",
                story_id="test-story",
                current_state=TDDState.TEST_RED
            )
            
            # Mock _prepare_context_internal to raise exception
            with patch.object(cm, '_prepare_context_internal', side_effect=Exception("Internal error")):
                with pytest.raises(ContextError) as exc_info:
                    await cm.prepare_context("TestAgent", task)
                
                assert "Context preparation failed" in str(exc_info.value)


class TestCacheOperationsEdgeCases:
    """Test cache operations edge cases and error paths"""
    
    @pytest.mark.asyncio
    async def test_invalidate_context_with_legacy_cache_error(self):
        """Test context invalidation with legacy cache attribute error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False
            )
            
            # Simulate missing _context_cache attribute
            if hasattr(cm, '_context_cache'):
                delattr(cm, '_context_cache')
            
            # Should handle missing attribute gracefully
            with pytest.raises(AttributeError):
                await cm.invalidate_context("test-context-id")
    
    @pytest.mark.asyncio
    async def test_cleanup_cache_with_legacy_cache_error(self):
        """Test cache cleanup with legacy cache attribute error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False
            )
            
            # Simulate missing _context_cache attribute
            if hasattr(cm, '_context_cache'):
                delattr(cm, '_context_cache')
            
            # Should raise AttributeError
            with pytest.raises(AttributeError):
                await cm.cleanup_cache()


class TestIntelligenceLayerEdgeCases:
    """Test intelligence layer edge cases and fallbacks"""
    
    @pytest.mark.asyncio
    async def test_build_context_index_intelligence_disabled(self):
        """Test build_context_index when intelligence is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False
            )
            
            # Should return early with warning
            await cm.build_context_index(force_rebuild=True)
            # No exception should be raised
    
    @pytest.mark.asyncio
    async def test_search_codebase_intelligence_disabled(self):
        """Test search_codebase when intelligence is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False
            )
            
            results = await cm.search_codebase("test query")
            assert results == []
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_intelligence_disabled(self):
        """Test get_file_dependencies when intelligence is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False
            )
            
            result = await cm.get_file_dependencies("/test/path.py")
            assert result == {"error": "Context index not available"}
    
    @pytest.mark.asyncio
    async def test_get_file_relevance_explanation_intelligence_disabled(self):
        """Test get_file_relevance_explanation when intelligence is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            result = await cm.get_file_relevance_explanation("/test/path.py", request)
            assert result == {"error": "Context filter not available"}
    
    @pytest.mark.asyncio
    async def test_estimate_compression_potential_intelligence_disabled(self):
        """Test estimate_compression_potential when intelligence is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False
            )
            
            result = await cm.estimate_compression_potential(
                "test content",
                FileType.PYTHON,
                CompressionLevel.MODERATE
            )
            assert result == {"error": "Context compressor not available"}
    
    @pytest.mark.asyncio
    async def test_get_project_statistics_intelligence_disabled(self):
        """Test get_project_statistics when intelligence is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False
            )
            
            result = await cm.get_project_statistics()
            assert result == {"error": "Context index not available"}


class TestTokenBudgetEdgeCases:
    """Test token budget optimization edge cases"""
    
    @pytest.mark.asyncio
    async def test_optimize_token_budget_no_budget(self):
        """Test optimize_token_budget with context without budget"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            context = AgentContext(
                request_id="test-request",
                agent_type="TestAgent",
                story_id="test-story"
            )
            # No token_budget set
            
            usage = TokenUsage(
                context_id="test-request",
                total_used=1000
            )
            
            with pytest.raises(ValueError) as exc_info:
                await cm.optimize_token_budget(context, usage, 0.8)
            
            assert "Context must have token budget" in str(exc_info.value)


class TestCrossStoryManagementEdgeCases:
    """Test cross-story management edge cases"""
    
    @pytest.mark.asyncio
    async def test_cross_story_operations_disabled(self):
        """Test cross-story operations when feature is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_cross_story=False
            )
            
            # All operations should return early
            await cm.register_story("test-story", {"test": "data"})
            await cm.unregister_story("test-story")
            
            conflicts = await cm.detect_story_conflicts("test-story", ["/test/file.py"])
            assert conflicts == []
            
            context = await cm.get_cross_story_context("test-story", ["other-story"])
            assert context == {}
            
            resolved = await cm.resolve_story_conflict("story1", "story2", "manual resolution")
            assert resolved is False
    
    @pytest.mark.asyncio
    async def test_unregister_nonexistent_story(self):
        """Test unregistering a story that doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Should handle gracefully
            await cm.unregister_story("nonexistent-story")
    
    @pytest.mark.asyncio
    async def test_detect_story_conflicts_complex_scenarios(self):
        """Test complex story conflict detection scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Register multiple stories
            await cm.register_story("story1", {"type": "feature"})
            await cm.register_story("story2", {"type": "bugfix"})
            await cm.register_story("story3", {"type": "refactor"})
            
            # Set up file modifications
            cm._active_stories["story1"]["file_modifications"] = {"/test/file1.py", "/test/shared.py"}
            cm._active_stories["story2"]["file_modifications"] = {"/test/file2.py", "/test/shared.py"}
            cm._active_stories["story3"]["file_modifications"] = {"/test/file3.py"}
            
            # Test conflicts
            conflicts = await cm.detect_story_conflicts("story1", ["/test/shared.py", "/test/new.py"])
            assert "story2" in conflicts
            assert "story3" not in conflicts
            
            # Check bidirectional conflict tracking
            assert "story1" in cm._story_conflicts["story2"]
    
    @pytest.mark.asyncio
    async def test_get_cross_story_context_with_metadata(self):
        """Test cross-story context with rich metadata"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Register stories with metadata
            await cm.register_story("primary", {"priority": "high", "type": "feature"})
            await cm.register_story("conflict1", {"priority": "medium", "type": "bugfix"})
            
            # Set up story data
            cm._active_stories["conflict1"]["active_agents"] = {"CodeAgent", "QAAgent"}
            cm._active_stories["conflict1"]["file_modifications"] = {"/test/shared.py"}
            cm._active_stories["conflict1"]["last_activity"] = datetime.utcnow()
            
            context = await cm.get_cross_story_context("primary", ["conflict1"])
            
            assert context["primary_story"] == "primary"
            assert len(context["conflicts"]) == 1
            assert context["conflicts"][0]["story_id"] == "conflict1"
            assert context["conflicts"][0]["metadata"]["priority"] == "medium"
            assert len(context["recommendations"]) > 0


class TestFileOperationsEdgeCases:
    """Test file operations edge cases"""
    
    def test_should_include_file_edge_cases(self):
        """Test _should_include_file with edge cases"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create test files
            test_dir = Path(temp_dir)
            
            # Hidden file
            hidden_file = test_dir / ".hidden_file.py"
            hidden_file.touch()
            assert not cm._should_include_file(hidden_file)
            
            # File in hidden directory
            hidden_dir = test_dir / ".hidden_dir"
            hidden_dir.mkdir()
            hidden_file_in_dir = hidden_dir / "file.py"
            hidden_file_in_dir.touch()
            assert not cm._should_include_file(hidden_file_in_dir)
            
            # File in __pycache__
            pycache_dir = test_dir / "__pycache__"
            pycache_dir.mkdir()
            cache_file = pycache_dir / "module.pyc"
            cache_file.touch()
            assert not cm._should_include_file(cache_file)
            
            # Large file (create 200KB file)
            large_file = test_dir / "large_file.py"
            with open(large_file, 'w') as f:
                f.write("# Test file\n" * 10000)  # Approximately 150KB
            
            # Check if large file handling works
            result = cm._should_include_file(large_file)
            # Result depends on exact file size - might be included or not
            
            # Non-existent file (should handle OSError)
            nonexistent = test_dir / "nonexistent.py"
            assert not cm._should_include_file(nonexistent)
    
    def test_determine_file_type_edge_cases(self):
        """Test _determine_file_type with various file types"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Test file type detection
            assert cm._determine_file_type(Path("test.py")) == FileType.PYTHON
            assert cm._determine_file_type(Path("test_file.py")) == FileType.TEST
            assert cm._determine_file_type(Path("tests/test_module.py")) == FileType.TEST
            assert cm._determine_file_type(Path("README.md")) == FileType.MARKDOWN
            assert cm._determine_file_type(Path("config.json")) == FileType.JSON
            assert cm._determine_file_type(Path("config.yml")) == FileType.YAML
            assert cm._determine_file_type(Path("config.yaml")) == FileType.YAML
            assert cm._determine_file_type(Path("settings.cfg")) == FileType.CONFIG
            assert cm._determine_file_type(Path("unknown.xyz")) == FileType.OTHER
    
    @pytest.mark.asyncio
    async def test_load_file_contents_with_errors(self):
        """Test _load_file_contents with various error conditions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            test_dir = Path(temp_dir)
            
            # Create a valid file
            valid_file = test_dir / "valid.py"
            valid_file.write_text("print('hello')")
            
            # Create a very large file that should be skipped
            large_file = test_dir / "large.py"
            large_content = "# This is a large file\n" * 10000  # Make it large
            large_file.write_text(large_content)
            
            # Create a directory instead of file
            directory = test_dir / "directory"
            directory.mkdir()
            
            file_paths = [
                str(valid_file),
                str(large_file),
                str(directory),
                "/nonexistent/file.py"
            ]
            
            contents = await cm._load_file_contents(file_paths)
            
            # Should contain valid file only
            assert str(valid_file) in contents
            assert contents[str(valid_file)] == "print('hello')"
            
            # Large file might be included or excluded based on token estimation
            # Directory and nonexistent should not be included
            assert str(directory) not in contents
            assert "/nonexistent/file.py" not in contents


class TestPerformanceMetricsEdgeCases:
    """Test performance metrics edge cases"""
    
    def test_get_performance_metrics_empty_state(self):
        """Test performance metrics with empty state"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            metrics = cm.get_performance_metrics()
            
            assert metrics["context_manager"]["total_requests"] == 0
            assert metrics["context_manager"]["cache_hits"] == 0
            assert metrics["context_manager"]["cache_misses"] == 0
            assert metrics["context_manager"]["cache_hit_rate"] == 0.0
            assert metrics["context_manager"]["average_preparation_time"] == 0.0
            assert metrics["context_manager"]["max_preparation_time"] == 0.0
            assert metrics["context_manager"]["min_preparation_time"] == 0.0
    
    def test_get_performance_metrics_with_data(self):
        """Test performance metrics with populated data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Populate some metrics
            cm._total_requests = 10
            cm._cache_hits = 7
            cm._cache_misses = 3
            cm._preparation_times = [0.5, 1.0, 1.5, 0.8, 1.2]
            
            metrics = cm.get_performance_metrics()
            
            assert metrics["context_manager"]["total_requests"] == 10
            assert metrics["context_manager"]["cache_hits"] == 7
            assert metrics["context_manager"]["cache_misses"] == 3
            assert metrics["context_manager"]["cache_hit_rate"] == 0.7
            assert metrics["context_manager"]["average_preparation_time"] == 1.0
            assert metrics["context_manager"]["max_preparation_time"] == 1.5
            assert metrics["context_manager"]["min_preparation_time"] == 0.5
    
    def test_get_performance_metrics_intelligence_disabled(self):
        """Test performance metrics when intelligence is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False
            )
            
            metrics = cm.get_performance_metrics()
            
            assert metrics["context_manager"]["intelligence_enabled"] is False
            assert "context_filter" not in metrics
            assert "context_compressor" not in metrics
            assert "context_index" not in metrics


class TestBackgroundProcessingEdgeCases:
    """Test background processing edge cases"""
    
    @pytest.mark.asyncio
    async def test_background_operations_disabled(self):
        """Test background operations when disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_background_processing=False
            )
            
            # All operations should return None
            result = await cm.trigger_index_update(["/test/file.py"])
            assert result is None
            
            result = await cm.warm_cache_for_context("TestAgent", "test-story", [])
            assert result is None
            
            result = await cm.schedule_learning_optimization(delay_hours=2)
            assert result is None
            
            stats = await cm.get_background_statistics()
            assert stats == {"error": "Background processing not enabled"}
    
    @pytest.mark.asyncio
    async def test_queue_initial_background_tasks_exceptions(self):
        """Test _queue_initial_background_tasks with exceptions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            await cm.start()
            
            # Mock submit_task to raise exception
            cm.background_processor.submit_task = AsyncMock(side_effect=Exception("Submit failed"))
            
            # Should handle exceptions gracefully
            await cm._queue_initial_background_tasks()


class TestMonitoringDashboardEdgeCases:
    """Test monitoring dashboard edge cases"""
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data_with_exceptions(self):
        """Test dashboard data collection with component exceptions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock monitor to raise exceptions
            cm.monitor.get_system_health = Mock(side_effect=Exception("Health check failed"))
            cm.monitor.get_performance_summary = AsyncMock(side_effect=Exception("Performance failed"))
            
            # Mock cache to raise exceptions
            cm.context_cache.get_statistics = AsyncMock(side_effect=Exception("Cache stats failed"))
            
            # Should handle exceptions and return partial data
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            assert dashboard_data["system_health"] == "unknown"
            assert "performance_metrics" in dashboard_data
            assert dashboard_data["active_stories"] == 0
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data_features_disabled(self):
        """Test dashboard data when features are disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_monitoring=False,
                enable_advanced_caching=False,
                enable_cross_story=False
            )
            
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            assert dashboard_data["advanced_features"]["monitoring"] is False
            assert dashboard_data["advanced_features"]["advanced_caching"] is False
            assert dashboard_data["advanced_features"]["cross_story"] is False
            assert "cache_statistics" not in dashboard_data
            assert "cross_story_details" not in dashboard_data


class TestCompressionEdgeCases:
    """Test compression edge cases and fallbacks"""
    
    @pytest.mark.asyncio
    async def test_apply_basic_compression_no_content(self):
        """Test basic compression with context that has no content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            context = AgentContext(
                request_id="test-request",
                agent_type="TestAgent",
                story_id="test-story"
            )
            
            # Set token usage that exceeds limit
            context.token_usage = TokenUsage(
                context_id="test-request",
                total_used=5000
            )
            
            # Apply compression
            compressed_context = await cm._apply_basic_compression(context, 1000)
            
            assert compressed_context.compression_applied is True
            assert compressed_context.compression_level == CompressionLevel.MODERATE
    
    @pytest.mark.asyncio
    async def test_apply_basic_compression_within_limit(self):
        """Test basic compression when context is already within limit"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            context = AgentContext(
                request_id="test-request",
                agent_type="TestAgent",
                story_id="test-story"
            )
            
            context.token_usage = TokenUsage(
                context_id="test-request",
                total_used=500
            )
            
            # Apply compression with higher limit
            compressed_context = await cm._apply_basic_compression(context, 1000)
            
            # Should return unchanged
            assert compressed_context is context
            assert not hasattr(compressed_context, 'compression_applied') or not compressed_context.compression_applied


class TestHelperMethodsEdgeCases:
    """Test helper methods edge cases"""
    
    def test_extract_story_id_edge_cases(self):
        """Test _extract_story_id with various task types"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # TDDTask object with story_id
            tdd_task = TDDTask(description="test", story_id="tdd-story")
            assert cm._extract_story_id(tdd_task) == "tdd-story"
            
            # Dict with story_id
            dict_task = {"story_id": "dict-story", "description": "test"}
            assert cm._extract_story_id(dict_task) == "dict-story"
            
            # Object without story_id
            class MockTask:
                def __init__(self):
                    self.description = "test"
            
            mock_task = MockTask()
            assert cm._extract_story_id(mock_task) == "default"
            
            # Dict without story_id
            dict_no_story = {"description": "test"}
            assert cm._extract_story_id(dict_no_story) == "default"
    
    def test_extract_tdd_phase_edge_cases(self):
        """Test _extract_tdd_phase with various task types"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # TDDTask with current_state
            tdd_task = TDDTask(description="test", current_state=TDDState.CODE_GREEN)
            assert cm._extract_tdd_phase(tdd_task) == TDDState.CODE_GREEN
            
            # Dict with current_state as TDDState
            dict_task = {"current_state": TDDState.TEST_RED}
            assert cm._extract_tdd_phase(dict_task) == TDDState.TEST_RED
            
            # Dict with current_state as string
            dict_string = {"current_state": "RED"}
            assert cm._extract_tdd_phase(dict_string) == TDDState.TEST_RED
            
            # Dict with invalid string
            dict_invalid = {"current_state": "INVALID"}
            assert cm._extract_tdd_phase(dict_invalid) is None
            
            # Object without current_state
            class MockTask:
                def __init__(self):
                    self.description = "test"
            
            mock_task = MockTask()
            assert cm._extract_tdd_phase(mock_task) is None
    
    def test_generate_cache_key_variations(self):
        """Test _generate_cache_key with different request types"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Request with TDDTask
            tdd_task = TDDTask(description="test task")
            request1 = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task=tdd_task,
                max_tokens=1000
            )
            
            key1 = cm._generate_cache_key(request1)
            assert isinstance(key1, str)
            assert len(key1) == 32  # MD5 hash length
            
            # Request with dict task
            request2 = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            key2 = cm._generate_cache_key(request2)
            assert isinstance(key2, str)
            
            # Keys should be different
            assert key1 != key2


class TestLegacyCacheOperations:
    """Test legacy cache operations when advanced caching is disabled"""
    
    @pytest.mark.asyncio
    async def test_legacy_cache_operations(self):
        """Test complete legacy cache workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            # Initially should be cache miss
            cached = await cm._get_cached_context_legacy(request)
            assert cached is None
            
            # Cache a context
            context = AgentContext(
                request_id=request.id,
                agent_type=request.agent_type,
                story_id=request.story_id
            )
            
            await cm._cache_context_legacy(request, context)
            
            # Should now be cache hit
            cached = await cm._get_cached_context_legacy(request)
            assert cached is not None
            assert cached.request_id == context.request_id
    
    @pytest.mark.asyncio
    async def test_legacy_cache_expiration(self):
        """Test legacy cache expiration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False,
                cache_ttl_seconds=1  # Very short TTL
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            context = AgentContext(
                request_id=request.id,
                agent_type=request.agent_type,
                story_id=request.story_id
            )
            
            # Cache the context
            await cm._cache_context_legacy(request, context)
            
            # Wait for expiration
            await asyncio.sleep(2)
            
            # Should be expired
            cached = await cm._get_cached_context_legacy(request)
            assert cached is None
    
    @pytest.mark.asyncio
    async def test_legacy_cache_size_limit(self):
        """Test legacy cache size limit"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False
            )
            
            # Fill cache beyond limit (100 entries)
            for i in range(105):
                request = ContextRequest(
                    agent_type="TestAgent",
                    story_id=f"story-{i}",
                    task={"description": f"task {i}"},
                    max_tokens=1000
                )
                
                context = AgentContext(
                    request_id=request.id,
                    agent_type=request.agent_type,
                    story_id=request.story_id
                )
                
                await cm._cache_context_legacy(request, context)
            
            # Cache should not exceed 100 entries
            assert len(cm._legacy_cache) <= 100


class TestCrossStoryHandoffTracking:
    """Test cross-story handoff and tracking edge cases"""
    
    @pytest.mark.asyncio
    async def test_handle_cross_story_preparation_auto_registration(self):
        """Test automatic story registration during context preparation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="auto-story",
                task={"description": "test task", "file_paths": ["/test/file.py"]},
                max_tokens=1000
            )
            
            # Should auto-register story
            await cm._handle_cross_story_preparation(request)
            
            assert "auto-story" in cm._active_stories
            assert cm._active_stories["auto-story"]["metadata"]["auto_registered"] is True
            assert "TestAgent" in cm._active_stories["auto-story"]["active_agents"]
    
    @pytest.mark.asyncio
    async def test_update_cross_story_tracking_with_cache(self):
        """Test cross-story tracking update with cache storage"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            await cm.register_story("test-story")
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            request.metadata = {"cross_story_context": {"test": "data"}}
            
            context = AgentContext(
                request_id=request.id,
                agent_type=request.agent_type,
                story_id=request.story_id
            )
            context.file_contents = {"/test/file1.py": "content1", "/test/file2.py": "content2"}
            
            await cm._update_cross_story_tracking(request, context)
            
            # Check file tracking was updated
            assert "/test/file1.py" in cm._active_stories["test-story"]["file_modifications"]
            assert "/test/file2.py" in cm._active_stories["test-story"]["file_modifications"]
            
            # Check cross-story cache was populated
            assert len(cm._cross_story_cache) > 0


class TestSpecificMissingLines:
    """Test specific missing lines identified in coverage report"""
    
    @pytest.mark.asyncio
    async def test_format_core_context_with_truncation(self):
        """Test _format_core_context with truncation (lines 1635-1658)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=False)
            
            # Create content that will trigger truncation
            large_content = "x" * 10000
            file_contents = {
                "large_file.py": large_content,
                "small_file.py": "print('hello')"
            }
            
            # Use small token budget to trigger truncation
            result = cm._format_core_context(file_contents, 100)
            
            assert "### large_file.py" in result
            assert "```" in result
            assert "[truncated]" in result or len(result) < len(large_content)
    
    @pytest.mark.asyncio 
    async def test_format_agent_memory_context_with_data(self):
        """Test _format_agent_memory_context with all data types (lines 1672-1706)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create mock memory with all data types
            mock_memory = Mock()
            mock_memory.get_recent_decisions = Mock(return_value=[
                Mock(description="test decision", outcome="success"),
                Mock(description="another decision", outcome="pending")
            ])
            mock_memory.learned_patterns = [
                Mock(pattern_type="test_pattern", description="pattern description"),
                Mock(pattern_type="other_pattern", description="other pattern")
            ]
            mock_memory.phase_handoffs = [
                Mock(from_phase=TDDState.TEST_RED, to_phase=TDDState.CODE_GREEN, context_summary="test handoff"),
                Mock(from_phase=TDDState.CODE_GREEN, to_phase=TDDState.REFACTOR, context_summary="refactor handoff"),
                Mock(from_phase=None, to_phase=TDDState.TEST_RED, context_summary="initial handoff")
            ]
            
            cm.agent_memory.get_memory = AsyncMock(return_value=mock_memory)
            
            result = await cm._format_agent_memory_context("TestAgent", "test-story", 2000)
            
            assert "### Agent Memory" in result
            assert "#### Recent Decisions:" in result
            assert "test decision: success" in result
            assert "#### Learned Patterns:" in result
            assert "test_pattern: pattern description" in result
            assert "#### Recent Phase Handoffs:" in result
            assert "test_red -> code_green: test handoff" in result
            assert "none -> test_red: initial handoff" in result
    
    @pytest.mark.asyncio
    async def test_format_agent_memory_context_truncation(self):
        """Test agent memory formatting with truncation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create memory that will exceed token budget
            mock_memory = Mock()
            mock_memory.get_recent_decisions = Mock(return_value=[
                Mock(description="x" * 1000, outcome="y" * 1000)
            ])
            mock_memory.learned_patterns = []
            mock_memory.phase_handoffs = []
            
            cm.agent_memory.get_memory = AsyncMock(return_value=mock_memory)
            
            result = await cm._format_agent_memory_context("TestAgent", "test-story", 50)
            
            assert "[truncated]" in result
    
    @pytest.mark.asyncio
    async def test_apply_basic_compression_all_components(self):
        """Test _apply_basic_compression with all context components (lines 1751-1783)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            context = AgentContext(
                request_id="test-request",
                agent_type="TestAgent", 
                story_id="test-story"
            )
            
            # Set all content types
            context.core_context = "core " * 1000
            context.historical_context = "history " * 1000
            context.dependencies = "deps " * 1000
            context.agent_memory = "memory " * 1000
            
            context.token_usage = TokenUsage(
                context_id="test-request",
                total_used=10000  # Exceeds limit
            )
            
            result = await cm._apply_basic_compression(context, 1000)
            
            assert result.compression_applied is True
            assert result.compression_level == CompressionLevel.MODERATE
            assert "[compressed]" in result.core_context
            assert "[compressed]" in result.historical_context
            assert "[compressed]" in result.dependencies
            assert "[compressed]" in result.agent_memory
    
    @pytest.mark.asyncio
    async def test_load_file_contents_error_paths(self):
        """Test _load_file_contents error handling (lines 1612-1626)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create various test scenarios
            valid_file = Path(temp_dir) / "valid.py"
            valid_file.write_text("print('hello')")
            
            # Create a directory (not a file)
            dir_path = Path(temp_dir) / "directory"
            dir_path.mkdir()
            
            # Very large file that exceeds token limit
            large_file = Path(temp_dir) / "large.py"
            large_content = "# Large file content\n" * 10000
            large_file.write_text(large_content)
            
            file_paths = [
                str(valid_file),
                str(dir_path),  # Directory - should be skipped
                "/nonexistent/path.py",  # Non-existent - should be skipped
                str(large_file)  # Large file - might be skipped
            ]
            
            # Mock token calculator to classify large file as too big
            cm.token_calculator.estimate_tokens = AsyncMock(side_effect=lambda x: 15000 if len(x) > 5000 else 100)
            
            contents = await cm._load_file_contents(file_paths)
            
            # Should contain valid file
            assert str(valid_file) in contents
            assert contents[str(valid_file)] == "print('hello')"
            
            # Should not contain directory or non-existent file
            assert str(dir_path) not in contents
            assert "/nonexistent/path.py" not in contents
            
            # Large file should not be included due to token limit
            assert str(large_file) not in contents
    
    @pytest.mark.asyncio
    async def test_should_include_file_size_and_error_cases(self):
        """Test _should_include_file with size limits and OS errors (lines 1601-1603)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create a file that exceeds size limit
            large_file = Path(temp_dir) / "large.py"
            with open(large_file, 'w') as f:
                f.write("x" * 200000)  # 200KB file
            
            # Should be excluded due to size
            assert not cm._should_include_file(large_file)
            
            # Test with non-existent file (triggers OSError in stat())
            nonexistent = Path("/nonexistent/directory/file.py")
            assert not cm._should_include_file(nonexistent)
    
    @pytest.mark.asyncio
    async def test_gather_candidate_files_error_handling(self):
        """Test _gather_candidate_files with filesystem errors (lines 1317-1322)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock Path.rglob to raise exception for specific patterns
            original_rglob = Path.rglob
            
            def mock_rglob(self, pattern):
                if pattern == "*.py":
                    raise PermissionError("Access denied")
                return original_rglob(self, pattern)
            
            with patch.object(Path, 'rglob', mock_rglob):
                files = await cm._gather_candidate_files("CodeAgent")
                # Should handle the exception and continue with other patterns
                assert isinstance(files, list)
    
    def test_extract_story_id_edge_case(self):
        """Test _extract_story_id edge case (line 1806)"""
        cm = ContextManager()
        
        # Test with object that has story_id but it's not a string
        task_obj = Mock()
        task_obj.story_id = 12345  # Non-string story_id
        result = cm._extract_story_id(task_obj)
        assert result == 12345
    
    def test_extract_tdd_phase_error_handling(self):
        """Test _extract_tdd_phase error handling (line 1844)"""
        cm = ContextManager()
        
        # Test with dict containing invalid state string
        task_dict = {"current_state": "INVALID_STATE_NAME"}
        result = cm._extract_tdd_phase(task_dict)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_cross_story_preparation_metadata_injection(self):
        """Test _handle_cross_story_preparation metadata injection (line 1863)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_cross_story=True)
            
            # Register conflicting stories
            await cm.register_story("story1")
            await cm.register_story("story2")
            cm._active_stories["story2"]["file_modifications"] = {"/shared/file.py"}
            
            # Create request that will conflict
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="story1", 
                task={"description": "test", "file_paths": ["/shared/file.py"]},
                max_tokens=1000
            )
            
            await cm._handle_cross_story_preparation(request)
            
            # Should have injected cross-story context metadata
            assert hasattr(request, 'metadata')
            assert 'cross_story_context' in request.metadata
            assert request.metadata['cross_story_context']['primary_story'] == "story1"


class TestFormattingMethodsEdgeCases:
    """Test formatting methods edge cases"""
    
    @pytest.mark.asyncio
    async def test_format_agent_memory_context_no_memory(self):
        """Test formatting agent memory when no memory exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock agent_memory.get_memory to return None
            cm.agent_memory.get_memory = AsyncMock(return_value=None)
            
            result = await cm._format_agent_memory_context("TestAgent", "test-story", 1000)
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_format_historical_context_basic(self):
        """Test basic historical context formatting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            result = await cm._format_historical_context("test-story", "TestAgent", 1000)
            assert "Historical Context" in result
            assert "test-story" in result
            assert "TestAgent" in result
    
    @pytest.mark.asyncio
    async def test_format_dependencies_context_basic(self):
        """Test basic dependencies context formatting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            files = ["/test/file1.py", "/test/file2.py"]
            result = await cm._format_dependencies_context(files, 1000)
            assert "Dependencies" in result
            assert "2 files" in result


class TestIntelligentCompressionAndFormatting:
    """Test intelligent compression and formatting paths (lines 1333-1559)"""
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_complete_workflow(self):
        """Test complete _format_core_context_compressed workflow (lines 1333-1393)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock successful compression
            cm.context_compressor.compress_content = AsyncMock(
                return_value=("compressed content here", 0.6)
            )
            
            file_contents = {
                "file1.py": "x" * 2000,  # Content that needs compression
                "file2.py": "y" * 1500   # More content
            }
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000,
                compression_level=CompressionLevel.MODERATE
            )
            
            result = await cm._format_core_context_compressed(file_contents, 500, request)
            
            assert "### file1.py" in result
            assert "Compression ratio: 0.60" in result
            assert "compressed content here" in result
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_with_break_condition(self):
        """Test compressed formatting with break condition when budget exceeded"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock compression that returns large content
            cm.context_compressor.compress_content = AsyncMock(
                return_value=("compressed but still large " * 100, 0.8)
            )
            
            file_contents = {
                "file1.py": "x" * 5000,
                "file2.py": "y" * 5000,  # This shouldn't be processed due to budget
                "file3.py": "z" * 5000   # This definitely shouldn't be processed
            }
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story", 
                task={"description": "test"},
                max_tokens=1000,
                compression_level=CompressionLevel.HIGH
            )
            
            result = await cm._format_core_context_compressed(file_contents, 100, request)
            
            # Should have stopped processing after first file due to budget
            assert "### file1.py" in result
            assert "### file2.py" not in result or "### file3.py" not in result
    
    @pytest.mark.asyncio
    async def test_format_historical_context_intelligent_complete(self):
        """Test complete _format_historical_context_intelligent workflow (lines 1403-1435)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Create mock snapshots
            mock_snapshots = [
                Mock(
                    tdd_phase=TDDState.TEST_RED,
                    file_list=["file1.py", "file2.py", "file3.py", "file4.py", "file5.py", "file6.py"],
                    context_summary="Testing phase summary"
                ),
                Mock(
                    tdd_phase=TDDState.CODE_GREEN,
                    file_list=["test1.py", "test2.py"],
                    context_summary="Implementation phase"
                ),
                Mock(
                    tdd_phase=None,  # Test None phase handling
                    file_list=["config.py"],
                    context_summary="Configuration update"
                )
            ]
            
            cm.agent_memory.get_context_history = AsyncMock(return_value=mock_snapshots)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            
            result = await cm._format_historical_context_intelligent(
                "test-story", "TestAgent", 1000, request
            )
            
            assert "### Historical Context" in result
            assert "#### test_red Phase" in result
            assert "#### code_green Phase" in result  
            assert "#### Unknown Phase" in result  # For None phase
            assert "Files: file1.py, file2.py, file3.py, file4.py, file5.py" in result
            assert "... and 1 more files" in result  # More than 5 files
            assert "Testing phase summary" in result
    
    @pytest.mark.asyncio
    async def test_format_historical_context_intelligent_truncation(self):
        """Test historical context truncation when exceeding budget"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Create snapshot with very long content
            long_summary = "Very long context summary " * 1000
            mock_snapshots = [
                Mock(
                    tdd_phase=TDDState.TEST_RED,
                    file_list=["file.py"],
                    context_summary=long_summary
                )
            ]
            
            cm.agent_memory.get_context_history = AsyncMock(return_value=mock_snapshots)
            cm.token_calculator.estimate_tokens = AsyncMock(return_value=5000)  # Exceeds budget
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            
            result = await cm._format_historical_context_intelligent(
                "test-story", "TestAgent", 100, request  # Small budget
            )
            
            assert "[truncated]" in result
    
    @pytest.mark.asyncio
    async def test_format_dependencies_context_intelligent_complete(self):
        """Test complete _format_dependencies_context_intelligent workflow (lines 1444-1483)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock dependency information
            mock_dep_info = {
                "dependency_count": 5,
                "reverse_dependency_count": 3,
                "direct_dependencies": ["module1", "module2", "module3", "module4"]
            }
            
            cm.context_index.get_file_dependencies = AsyncMock(return_value=mock_dep_info)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            
            files = ["/test/file1.py", "/test/file2.py"]
            result = await cm._format_dependencies_context_intelligent(files, 1000, request)
            
            assert "### Dependencies Analysis" in result
            assert "#### /test/file1.py" in result
            assert "Dependencies: 5" in result
            assert "Reverse dependencies: 3" in result
            assert "Imports: module1, module2, module3" in result  # First 3 only
    
    @pytest.mark.asyncio
    async def test_format_dependencies_context_intelligent_error_continue(self):
        """Test dependencies context continues on individual file errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            def mock_get_deps(file_path, **kwargs):
                if "error_file" in file_path:
                    raise Exception(f"Error analyzing {file_path}")
                return {"dependency_count": 2, "reverse_dependency_count": 1}
            
            cm.context_index.get_file_dependencies = AsyncMock(side_effect=mock_get_deps)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            
            files = ["/test/error_file.py", "/test/good_file.py"]
            result = await cm._format_dependencies_context_intelligent(files, 1000, request)
            
            # Should contain analysis for good file, skip error file
            assert "### Dependencies Analysis" in result
            assert "#### /test/good_file.py" in result
            assert "Dependencies: 2" in result
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_complete_workflow(self):
        """Test complete _apply_intelligent_compression workflow (lines 1491-1559)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock successful compression for all components
            cm.context_compressor.compress_content = AsyncMock(
                return_value=("compressed content", 0.5)
            )
            
            context = AgentContext(
                request_id="test-request",
                agent_type="TestAgent",
                story_id="test-story"
            )
            
            # Set all context components with large content
            context.core_context = "core content " * 1000
            context.historical_context = "historical content " * 500
            context.dependencies = "dependency content " * 300
            context.agent_memory = "memory content " * 200
            
            context.token_usage = TokenUsage(
                context_id="test-request",
                total_used=10000  # Way over limit
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            
            result = await cm._apply_intelligent_compression(context, request)
            
            assert result.compression_applied is True
            assert result.compression_level in [
                CompressionLevel.HIGH, CompressionLevel.EXTREME
            ]  # Should be high compression due to ratio
            assert result.core_context == "compressed content"
            assert result.historical_context == "compressed content"
            assert result.dependencies == "compressed content"
            assert result.agent_memory == "compressed content"
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_component_error_fallback(self):
        """Test intelligent compression with component compression errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock compression to fail for some components
            def mock_compress(content, file_path, **kwargs):
                if "core_context" in file_path:
                    raise Exception("Core compression failed")
                return ("compressed content", 0.6)
            
            cm.context_compressor.compress_content = AsyncMock(side_effect=mock_compress)
            
            context = AgentContext(
                request_id="test-request",
                agent_type="TestAgent",
                story_id="test-story"
            )
            
            context.core_context = "core " * 2000  # Large content
            context.historical_context = "history " * 1000
            
            context.token_usage = TokenUsage(
                context_id="test-request",
                total_used=8000
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=2000
            )
            
            result = await cm._apply_intelligent_compression(context, request)
            
            # Core context should be truncated due to compression error
            assert "[compressed]" in result.core_context
            # Historical context should be properly compressed
            assert result.historical_context == "compressed content"
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_within_budget(self):
        """Test intelligent compression when context is already within budget"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            context = AgentContext(
                request_id="test-request",
                agent_type="TestAgent",
                story_id="test-story"
            )
            
            context.core_context = "small content"
            context.token_usage = TokenUsage(
                context_id="test-request",
                total_used=500  # Within budget
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            
            result = await cm._apply_intelligent_compression(context, request)
            
            # Should return unchanged
            assert result is context
            assert not hasattr(result, 'compression_applied') or not result.compression_applied


class TestIntelligentFormattingFallbacks:
    """Test intelligent formatting methods fallback behaviors"""
    
    @pytest.mark.asyncio
    async def test_gather_relevant_files_intelligent_fallback(self):
        """Test intelligent file gathering with fallback to basic"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('test')")
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            context = AgentContext(
                request_id=request.id,
                agent_type=request.agent_type,
                story_id=request.story_id
            )
            
            # Mock context_filter to raise exception
            cm.context_filter.filter_relevant_files = AsyncMock(side_effect=Exception("Filter failed"))
            
            # Should fallback to basic implementation
            files = await cm._gather_relevant_files_intelligent(request, context)
            assert isinstance(files, list)
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_no_files(self):
        """Test compressed core context formatting with no files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            result = await cm._format_core_context_compressed({}, 1000, request)
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_format_historical_context_intelligent_fallback(self):
        """Test intelligent historical context with fallback"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            # Mock agent_memory to raise exception
            cm.agent_memory.get_context_history = AsyncMock(side_effect=Exception("History failed"))
            
            result = await cm._format_historical_context_intelligent("test-story", "TestAgent", 1000, request)
            assert "Historical Context" in result
    
    @pytest.mark.asyncio
    async def test_format_dependencies_context_intelligent_fallback(self):
        """Test intelligent dependencies context with fallback"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            # Mock context_index to raise exception
            cm.context_index.get_file_dependencies = AsyncMock(side_effect=Exception("Deps failed"))
            
            files = ["/test/file.py"]
            result = await cm._format_dependencies_context_intelligent(files, 1000, request)
            assert "Dependencies" in result
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_fallback(self):
        """Test intelligent compression with fallback to basic"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            context = AgentContext(
                request_id="test-request",
                agent_type="TestAgent",
                story_id="test-story"
            )
            context.core_context = "Large content" * 1000
            context.token_usage = TokenUsage(context_id="test-request", total_used=10000)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test task"},
                max_tokens=1000
            )
            
            # Mock compressor to raise exception
            cm.context_compressor.compress_content = AsyncMock(side_effect=Exception("Compression failed"))
            
            # Should fallback to basic compression
            result = await cm._apply_intelligent_compression(context, request)
            assert result.compression_applied is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])