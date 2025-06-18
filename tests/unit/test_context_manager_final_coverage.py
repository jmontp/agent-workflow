"""
FINAL CRITICAL COVERAGE TEST - GOVERNMENT AUDIT COMPLIANCE

This test file contains the most critical tests to push ContextManager coverage from 66% to 95%+.
Focused on the specific uncovered lines identified in the coverage analysis.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_manager import ContextManager
from context.models import (
    ContextRequest, AgentContext, TokenBudget, TokenUsage,
    CompressionLevel, FileType
)
from context.exceptions import ContextError, ContextTimeoutError
from tdd_models import TDDState, TDDTask


class TestCriticalMissingLines:
    """Target the specific missing lines for 95% coverage"""
    
    @pytest.mark.asyncio
    async def test_prepare_context_timeout_monitoring_path(self):
        """Test timeout error with monitoring (lines 382-389)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, max_preparation_time=1)
            cm.monitor = Mock()
            cm.monitor.record_operation_start = Mock(return_value="op123")
            cm.monitor.record_operation_end = Mock()
            
            # Mock slow preparation
            async def slow_prep(*args):
                await asyncio.sleep(2)
                return Mock()
            
            with patch.object(cm, '_prepare_context_internal', slow_prep):
                with pytest.raises(ContextTimeoutError):
                    await cm.prepare_context("TestAgent", {"desc": "test"})
                    
                cm.monitor.record_operation_end.assert_called_with("op123", False)
    
    @pytest.mark.asyncio
    async def test_prepare_context_error_monitoring_path(self):
        """Test generic error with monitoring (line 399)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            cm.monitor = Mock()
            cm.monitor.record_operation_start = Mock(return_value="op456")
            cm.monitor.record_operation_end = Mock()
            
            with patch.object(cm, '_prepare_context_internal', side_effect=Exception("test error")):
                with pytest.raises(ContextError):
                    await cm.prepare_context("TestAgent", {"desc": "test"})
                    
                cm.monitor.record_operation_end.assert_called_with("op456", False)
    
    def test_intelligence_disabled_paths(self):
        """Test all intelligence-disabled warning paths (lines 768-769, 794-795, 806-807)"""
        cm = ContextManager(enable_intelligence=False)
        
        # Test all the intelligence-disabled paths
        request = ContextRequest(
            agent_type="TestAgent",
            story_id="test-story", 
            task={"description": "test"},
            max_tokens=1000
        )
        
        # These should all return error messages
        result1 = asyncio.run(cm.get_file_relevance_explanation("test.py", request))
        assert result1 == {"error": "Context filter not available"}
        
        result2 = asyncio.run(cm.estimate_compression_potential("content", FileType.PYTHON, CompressionLevel.MODERATE))
        assert result2 == {"error": "Context compressor not available"}
        
        result3 = asyncio.run(cm.get_project_statistics())
        assert result3 == {"error": "Context index not available"}
    
    @pytest.mark.asyncio 
    async def test_background_processing_disabled_paths(self):
        """Test background processing disabled paths (lines 1111, 1124)"""
        cm = ContextManager(enable_background_processing=False)
        
        result1 = await cm.warm_cache_for_context("TestAgent", "story1", [])
        assert result1 is None
        
        result2 = await cm.schedule_learning_optimization()
        assert result2 is None
    
    @pytest.mark.asyncio
    async def test_load_file_contents_error_paths(self):
        """Test file loading error paths (lines 1612-1626)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create large file that exceeds token limit
            large_file = Path(temp_dir) / "large.py"
            large_file.write_text("x" * 100000)
            
            # Mock token calculator to return high estimate
            cm.token_calculator.estimate_tokens = AsyncMock(return_value=15000)
            
            contents = await cm._load_file_contents([str(large_file)])
            # Large file should be skipped
            assert str(large_file) not in contents
    
    def test_should_include_file_size_limit(self):
        """Test file size limit (lines 1601-1603)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Create file that exceeds 100KB limit
            large_file = Path(temp_dir) / "large.py"
            with open(large_file, 'w') as f:
                f.write("x" * 200000)  # 200KB
            
            assert not cm._should_include_file(large_file)
            
            # Test OSError path
            nonexistent = Path("/nonexistent/file.py")
            assert not cm._should_include_file(nonexistent)
    
    @pytest.mark.asyncio
    async def test_format_core_context_basic(self):
        """Test basic core context formatting (lines 1635-1658)"""
        cm = ContextManager(enable_intelligence=False)
        
        file_contents = {
            "file1.py": "x" * 1000,
            "file2.py": "y" * 2000
        }
        
        # Test with truncation
        result = cm._format_core_context(file_contents, 100)
        assert "### file1.py" in result
        assert "[truncated]" in result
    
    @pytest.mark.asyncio
    async def test_format_agent_memory_full_workflow(self):
        """Test agent memory formatting full workflow (lines 1672-1706)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock memory with all components
            mock_memory = Mock()
            mock_memory.get_recent_decisions = Mock(return_value=[
                Mock(description="decision1", outcome="success")
            ])
            mock_memory.learned_patterns = [
                Mock(pattern_type="pattern1", description="desc1")
            ]
            mock_memory.phase_handoffs = [
                Mock(from_phase=TDDState.TEST_RED, to_phase=TDDState.CODE_GREEN, context_summary="handoff1")
            ]
            
            cm.agent_memory.get_memory = AsyncMock(return_value=mock_memory)
            
            result = await cm._format_agent_memory_context("TestAgent", "story1", 2000)
            
            assert "### Agent Memory" in result
            assert "#### Recent Decisions:" in result
            assert "#### Learned Patterns:" in result
            assert "#### Recent Phase Handoffs:" in result
    
    @pytest.mark.asyncio
    async def test_apply_basic_compression_full(self):
        """Test basic compression complete workflow (lines 1751-1783)"""
        cm = ContextManager()
        
        context = AgentContext(
            request_id="test",
            agent_type="TestAgent",
            story_id="story1"
        )
        
        # Set all content types
        context.core_context = "core" * 1000
        context.historical_context = "hist" * 500  
        context.dependencies = "deps" * 300
        context.agent_memory = "mem" * 200
        
        context.token_usage = TokenUsage(context_id="test", total_used=5000)
        
        result = await cm._apply_basic_compression(context, 1000)
        
        assert result.compression_applied is True
        assert "[compressed]" in result.core_context
        assert "[compressed]" in result.historical_context
        assert "[compressed]" in result.dependencies
        assert "[compressed]" in result.agent_memory
    
    def test_extract_story_id_edge_case(self):
        """Test story ID extraction edge case (line 1806)"""
        cm = ContextManager()
        
        # Test with non-string story_id
        task = Mock()
        task.story_id = 12345
        assert cm._extract_story_id(task) == 12345
    
    def test_extract_tdd_phase_error_case(self):
        """Test TDD phase extraction error (line 1820)"""
        cm = ContextManager()
        
        # Test invalid string state
        task = {"current_state": "INVALID_STATE"}
        assert cm._extract_tdd_phase(task) is None
    
    @pytest.mark.asyncio
    async def test_cross_story_metadata_injection(self):
        """Test cross-story metadata injection (line 1863)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir, enable_cross_story=True)
            
            # Set up conflicting stories
            await cm.register_story("story1")
            await cm.register_story("story2")
            cm._active_stories["story2"]["file_modifications"] = {"/shared/file.py"}
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="story1",
                task={"file_paths": ["/shared/file.py"]},
                max_tokens=1000
            )
            
            await cm._handle_cross_story_preparation(request)
            
            # Should inject metadata
            assert hasattr(request, 'metadata')
            assert 'cross_story_context' in request.metadata
    
    @pytest.mark.asyncio
    async def test_gather_candidate_files_error(self):
        """Test candidate file gathering with errors (lines 1317-1322)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(project_path=temp_dir)
            
            # Mock rglob to raise exception
            with patch.object(Path, 'rglob', side_effect=PermissionError("Access denied")):
                files = await cm._gather_candidate_files("CodeAgent")
                assert isinstance(files, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])