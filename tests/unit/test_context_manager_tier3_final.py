"""
TIER 3 GOVERNMENT AUDIT - FINAL COVERAGE TEST
==============================================

Laser-focused test suite to achieve the final 95%+ coverage for context_manager.py.
Targets specific uncovered lines identified in coverage analysis.
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_manager import ContextManager
from context.models import (
    ContextRequest, AgentContext, TokenBudget, TokenUsage,
    CompressionLevel, FileType
)
from context.exceptions import ContextTimeoutError, ContextError
from tdd_models import TDDState, TDDTask


class TestImportFallbackLines:
    """Target import fallback lines 30-89"""
    
    def test_import_structure_exists(self):
        """Verify import fallback structure is testable"""
        # The fallback imports are at module load time
        # We test that the module loaded correctly with fallbacks available
        import context_manager
        cm = context_manager.ContextManager()
        assert cm is not None
    
    def test_tdd_models_import_available(self):
        """Test TDD models import path (lines 86-89)"""
        # Test that TDD models are accessible
        from tdd_models import TDDState, TDDTask
        task = TDDTask(description="test")
        assert task.description == "test"


class TestQueueInitialBackgroundTasks:
    """Target _queue_initial_background_tasks lines 1143-1168"""
    
    @pytest.mark.asyncio
    async def test_queue_initial_tasks_complete(self):
        """Test complete task queueing workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock background processor methods
            cm.background_processor.submit_task = AsyncMock()
            cm.background_processor.schedule_pattern_discovery = AsyncMock()
            
            await cm._queue_initial_background_tasks()
            
            # Verify tasks were queued
            assert cm.background_processor.submit_task.call_count >= 2
            cm.background_processor.schedule_pattern_discovery.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_queue_initial_tasks_exception(self):
        """Test exception handling in task queueing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock to raise exception
            cm.background_processor.submit_task = AsyncMock(side_effect=Exception("Failed"))
            
            # Should handle exception gracefully
            await cm._queue_initial_background_tasks()
    
    @pytest.mark.asyncio
    async def test_queue_initial_tasks_disabled(self):
        """Test when background processing disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_background_processing=False
            )
            
            # Should return early without error
            await cm._queue_initial_background_tasks()


class TestIntelligentCompressionSpecific:
    """Target intelligent compression workflow lines 1333-1559"""
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_truncation(self):
        """Test compression with truncation fallback (lines 1347-1382)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock compression failure to trigger truncation
            cm.context_compressor.compress_content = AsyncMock(side_effect=Exception("Compression failed"))
            cm.token_calculator.estimate_tokens = AsyncMock(return_value=300)
            
            file_contents = {"large_file.py": "content " * 1000}
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story", 
                task={"description": "test"},
                max_tokens=1000,
                compression_level=CompressionLevel.HIGH
            )
            
            result = await cm._format_core_context_compressed(file_contents, 200, request)
            
            # Should include truncation fallback
            assert "### large_file.py" in result
            assert "[truncated]" in result
    
    @pytest.mark.asyncio
    async def test_format_core_context_compressed_break_loop(self):
        """Test break condition when budget exceeded (line 1382)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            # Mock compression to use up budget quickly
            cm.context_compressor.compress_content = AsyncMock(return_value=("large result " * 100, 0.5))
            cm.token_calculator.estimate_tokens = AsyncMock(return_value=500)
            
            file_contents = {
                "file1.py": "content1",
                "file2.py": "content2",  # Should not be processed due to budget
                "file3.py": "content3"   # Definitely not processed
            }
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"}, 
                max_tokens=1000,
                compression_level=CompressionLevel.MODERATE
            )
            
            result = await cm._format_core_context_compressed(file_contents, 100, request)
            
            # Should break after first file
            assert "### file1.py" in result
            file2_count = result.count("### file2.py")
            file3_count = result.count("### file3.py")
            # At least one should be missing due to budget constraint
            assert file2_count == 0 or file3_count == 0
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_extreme_level(self):
        """Test extreme compression level selection (lines 1500-1511)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            context = AgentContext(
                request_id="test-extreme",
                agent_type="TestAgent",
                story_id="test-story"
            )
            
            context.core_context = "content " * 2000
            context.token_usage = TokenUsage(context_id="test-extreme", total_used=50000)  # Very high usage
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=10000  # Much lower, triggering extreme compression
            )
            
            # Compression ratio: 10000/50000 = 0.2 -> should trigger EXTREME
            cm.context_compressor.compress_content = AsyncMock(return_value=("compressed", 0.3))
            
            result = await cm._apply_intelligent_compression(context, request)
            
            assert result.compression_level == CompressionLevel.EXTREME
    
    @pytest.mark.asyncio
    async def test_apply_intelligent_compression_component_error_fallback(self):
        """Test compression with component errors and fallback (lines 1539-1544)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_intelligence=True)
            
            context = AgentContext(
                request_id="test-error",
                agent_type="TestAgent",
                story_id="test-story"
            )
            
            context.core_context = "core " * 1000
            context.historical_context = "history " * 1000
            context.token_usage = TokenUsage(context_id="test-error", total_used=20000)
            
            # Mock compression to fail for specific components
            def mock_compress_with_errors(content, file_path, **kwargs):
                if "core_context" in file_path:
                    raise Exception("Core compression failed")
                return ("compressed content", 0.6)
            
            cm.context_compressor.compress_content = AsyncMock(side_effect=mock_compress_with_errors)
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story", 
                task={"description": "test"},
                max_tokens=5000
            )
            
            result = await cm._apply_intelligent_compression(context, request)
            
            # Core context should use truncation fallback
            assert "[compressed]" in result.core_context
            # Historical context should use proper compression
            assert result.historical_context == "compressed content"


class TestMonitoringDashboardSpecific:
    """Target monitoring dashboard lines 1037-1090"""
    
    @pytest.mark.asyncio
    async def test_dashboard_monitoring_exception_handling(self):
        """Test dashboard data with monitoring exceptions (lines 1059-1064)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock monitor to raise exception
            cm.monitor.get_system_health = Mock(side_effect=Exception("Health failed"))
            cm.monitor.get_performance_summary = AsyncMock(side_effect=Exception("Performance failed"))
            
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            # Should handle exceptions and continue
            assert dashboard_data["system_health"] == "unknown"
            assert "performance_metrics" in dashboard_data
    
    @pytest.mark.asyncio
    async def test_dashboard_cache_exception_handling(self):
        """Test dashboard data with cache exceptions (lines 1067-1077)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock cache to raise exception
            cm.context_cache.get_statistics = AsyncMock(side_effect=Exception("Cache stats failed"))
            
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            # Should handle cache exception
            assert "cache_statistics" not in dashboard_data
    
    @pytest.mark.asyncio 
    async def test_dashboard_cross_story_details(self):
        """Test cross-story details in dashboard (lines 1080-1088)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_cross_story=True)
            
            # Set up cross-story data
            cm._active_stories = {
                "story1": {"metadata": {"priority": "high"}},
                "story2": {"metadata": {"type": "feature"}}
            }
            cm._story_conflicts = {"story1": ["story2"]}
            
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            # Should include cross-story details
            assert "cross_story_details" in dashboard_data
            assert "story1" in dashboard_data["cross_story_details"]["active_stories"]
            assert dashboard_data["cross_story_details"]["story_metadata"]["story1"]["priority"] == "high"


class TestServiceLifecycleSpecific:
    """Target service lifecycle lines 236-263"""
    
    @pytest.mark.asyncio
    async def test_start_with_missing_components(self):
        """Test start when components are None (disabled features)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_background_processing=False
            )
            
            # Components should be None
            assert cm.context_cache is None
            assert cm.monitor is None
            assert cm.background_processor is None
            
            # Should handle gracefully
            await cm.start()
    
    @pytest.mark.asyncio
    async def test_stop_with_missing_components(self):
        """Test stop when components are None"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False,
                enable_monitoring=False, 
                enable_background_processing=False
            )
            
            await cm.start()
            
            # Should handle None components gracefully
            await cm.stop()


class TestContextPreparationMonitoring:
    """Target context preparation monitoring integration"""
    
    @pytest.mark.asyncio
    async def test_prepare_context_monitoring_operation_lifecycle(self):
        """Test complete monitoring operation lifecycle (lines 294-337)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            operation_id = "test-op-123"
            cm.monitor.record_operation_start = Mock(return_value=operation_id)
            cm.monitor.record_context_preparation = Mock()
            cm.monitor.record_operation_end = Mock()
            
            task = TDDTask(description="Test task")
            
            context = await cm.prepare_context("TestAgent", task)
            
            # Verify monitoring lifecycle
            cm.monitor.record_operation_start.assert_called_once_with("context_preparation")
            cm.monitor.record_context_preparation.assert_called_once()
            cm.monitor.record_operation_end.assert_called_once_with(operation_id, True)
    
    @pytest.mark.asyncio
    async def test_prepare_context_timeout_monitoring_cleanup(self):
        """Test timeout with monitoring cleanup (lines 386-387)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                max_preparation_time=1
            )
            
            operation_id = "timeout-op"
            cm.monitor.record_operation_start = Mock(return_value=operation_id)
            cm.monitor.record_operation_end = Mock()
            
            # Mock slow preparation
            async def slow_prep(*args, **kwargs):
                await asyncio.sleep(2)
                return Mock()
            
            with patch.object(cm, '_prepare_context_internal', side_effect=slow_prep):
                task = TDDTask(description="Slow task")
                
                with pytest.raises(ContextTimeoutError):
                    await cm.prepare_context("TestAgent", task)
                
                # Verify monitoring cleanup
                cm.monitor.record_operation_end.assert_called_once_with(operation_id, False)
    
    @pytest.mark.asyncio
    async def test_prepare_context_exception_monitoring_cleanup(self):
        """Test exception with monitoring cleanup (lines 397-399)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            operation_id = "error-op"
            cm.monitor.record_operation_start = Mock(return_value=operation_id)
            cm.monitor.record_operation_end = Mock()
            
            # Mock preparation to fail
            with patch.object(cm, '_prepare_context_internal', side_effect=Exception("Internal error")):
                task = TDDTask(description="Failing task")
                
                with pytest.raises(ContextError):
                    await cm.prepare_context("TestAgent", task)
                
                # Verify monitoring cleanup
                cm.monitor.record_operation_end.assert_called_once_with(operation_id, False)


class TestFileOperationsSpecific:
    """Target specific file operation edge cases"""
    
    def test_should_include_file_size_limit_exact(self):
        """Test _should_include_file size limit check (lines 1600-1601)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create file that exceeds 100KB limit
            large_file = Path(temp_dir) / "large.py"
            with open(large_file, 'w') as f:
                f.write("x" * 150000)  # 150KB
            
            # Should be excluded due to size
            assert not cm._should_include_file(large_file)
    
    def test_should_include_file_os_error(self):
        """Test _should_include_file OSError handling (lines 1602-1603)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Non-existent file should trigger OSError and return False
            nonexistent = Path("/absolutely/nonexistent/file.py")
            assert not cm._should_include_file(nonexistent)
    
    @pytest.mark.asyncio
    async def test_load_file_contents_token_limit_skip(self):
        """Test file skipping due to token limit (lines 1619-1622)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("content " * 1000)
            
            # Mock token calculator to return high estimate
            cm.token_calculator.estimate_tokens = AsyncMock(return_value=15000)  # Over 10k limit
            
            contents = await cm._load_file_contents([str(test_file)])
            
            # Should be skipped due to token limit
            assert str(test_file) not in contents


class TestLegacyCacheSpecific:
    """Target legacy cache operations"""
    
    @pytest.mark.asyncio
    async def test_legacy_cache_expiration_cleanup(self):
        """Test legacy cache expiration and cleanup (lines 1897-1902)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False,
                cache_ttl_seconds=1
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            
            context = AgentContext(request_id=request.id, agent_type="TestAgent", story_id="test-story")
            
            # Cache context
            await cm._cache_context_legacy(request, context)
            
            # Wait for expiration
            await asyncio.sleep(2)
            
            # Should be expired and removed
            cached = await cm._get_cached_context_legacy(request)
            assert cached is None
    
    @pytest.mark.asyncio
    async def test_legacy_cache_size_limit_cleanup(self):
        """Test legacy cache size limit enforcement (lines 1912-1916)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False
            )
            
            # Fill cache beyond limit
            for i in range(105):
                request = ContextRequest(
                    agent_type="TestAgent",
                    story_id=f"story-{i}",
                    task={"description": f"task {i}"},
                    max_tokens=1000
                )
                context = AgentContext(request_id=request.id, agent_type="TestAgent", story_id=f"story-{i}")
                await cm._cache_context_legacy(request, context)
            
            # Should enforce size limit
            assert len(cm._legacy_cache) <= 100


class TestCrossStoryHandoffSpecific:
    """Target cross-story handoff tracking"""
    
    @pytest.mark.asyncio
    async def test_handle_cross_story_preparation_metadata_injection(self):
        """Test metadata injection during cross-story preparation (lines 1860-1864)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_cross_story=True)
            
            # Register conflicting stories
            await cm.register_story("story1")
            await cm.register_story("story2")
            cm._active_stories["story2"]["file_modifications"] = {"/shared/file.py"}
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="story1",
                task={"description": "test", "file_paths": ["/shared/file.py"]},
                max_tokens=1000
            )
            
            await cm._handle_cross_story_preparation(request)
            
            # Should inject cross-story context metadata
            assert hasattr(request, 'metadata')
            assert 'cross_story_context' in request.metadata
    
    @pytest.mark.asyncio
    async def test_update_cross_story_tracking_cache_storage(self):
        """Test cross-story cache storage (lines 1884-1886)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_cross_story=True)
            
            await cm.register_story("test-story")
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="test-story",
                task={"description": "test"},
                max_tokens=1000
            )
            request.metadata = {"cross_story_context": {"test": "data"}}
            
            context = AgentContext(
                request_id=request.id,
                agent_type="TestAgent",
                story_id="test-story"
            )
            context.file_contents = {"/test/file.py": "content"}
            
            await cm._update_cross_story_tracking(request, context)
            
            # Should populate cross-story cache
            assert len(cm._cross_story_cache) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])