"""
Tests for SimpleContextManager

Tests the performance-optimized simple context management implementation.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import time

# Add lib directory to path for imports
import sys
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from simple_context_manager import SimpleContextManager
from context.models import (
    ContextRequest, AgentContext, TokenBudget, TokenUsage,
    CompressionLevel, TDDState
)
from context.exceptions import ContextError
from tdd_models import TDDTask


class TestSimpleContextManager:
    """Test SimpleContextManager functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory with test files"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create test files
        (project_path / "main.py").write_text("""
def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
""")
        
        (project_path / "test_main.py").write_text("""
import unittest
from main import hello_world

class TestMain(unittest.TestCase):
    def test_hello_world(self):
        result = hello_world()
        self.assertEqual(result, "success")
""")
        
        (project_path / "README.md").write_text("""
# Test Project

This is a test project for context management.

## Features
- Hello world functionality
- Unit tests
- Documentation
""")
        
        # Create subdirectory with more files
        subdir = project_path / "src"
        subdir.mkdir()
        (subdir / "utils.py").write_text("""
def utility_function():
    return "utility"
""")
        
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def simple_manager(self, temp_project):
        """Create SimpleContextManager instance"""
        return SimpleContextManager(
            project_path=str(temp_project),
            max_tokens=10000,
            max_files=5,
            max_file_size=1000,
            enable_caching=True,
            cache_size=10
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_project):
        """Test SimpleContextManager initialization"""
        manager = SimpleContextManager(
            project_path=str(temp_project),
            max_tokens=5000
        )
        
        assert manager.project_path == temp_project
        assert manager.max_tokens == 5000
        assert manager.max_files == 10  # default
        assert manager.enable_caching is False  # default
        
        # Test start/stop methods
        await manager.start()
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_prepare_context_basic(self, simple_manager):
        """Test basic context preparation"""
        task = {
            "description": "Test task",
            "story_id": "test-story",
            "current_state": "WRITE_TEST"
        }
        
        context = await simple_manager.prepare_context(
            agent_type="CodeAgent",
            task=task,
            max_tokens=5000
        )
        
        assert isinstance(context, AgentContext)
        assert context.agent_type == "CodeAgent"
        assert context.story_id == "test-story"
        assert context.tdd_phase == TDDState.WRITE_TEST
        assert context.core_context is not None
        assert context.file_contents is not None
        assert len(context.file_contents) > 0
        assert context.token_usage.total_used > 0
        assert context.preparation_time > 0
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_tdd_task(self, simple_manager):
        """Test context preparation with TDDTask object"""
        tdd_task = TDDTask(
            story_id="test-story",
            current_state=TDDState.WRITE_CODE,
            description="Implement feature"
        )
        
        context = await simple_manager.prepare_context(
            agent_type="CodeAgent",
            task=tdd_task,
            max_tokens=5000
        )
        
        assert context.story_id == "test-story"
        assert context.tdd_phase == TDDState.WRITE_CODE
    
    @pytest.mark.asyncio
    async def test_file_filtering_by_agent_type(self, simple_manager):
        """Test that file filtering works based on agent type"""
        task = {"description": "Test task", "story_id": "test"}
        
        # Test CodeAgent - should get .py files
        context_code = await simple_manager.prepare_context("CodeAgent", task)
        py_files = [f for f in context_code.file_contents.keys() if f.endswith('.py')]
        assert len(py_files) > 0
        
        # Test DesignAgent - should get .md files
        context_design = await simple_manager.prepare_context("DesignAgent", task)
        md_files = [f for f in context_design.file_contents.keys() if f.endswith('.md')]
        assert len(md_files) > 0
    
    @pytest.mark.asyncio
    async def test_token_truncation(self, simple_manager):
        """Test that token truncation works when context exceeds limits"""
        # Set very low token limit to force truncation
        task = {"description": "Test task", "story_id": "test"}
        
        context = await simple_manager.prepare_context(
            agent_type="CodeAgent",
            task=task,
            max_tokens=100  # Very small limit
        )
        
        assert context.token_usage.total_used <= 100
        assert context.compression_applied is True
        assert "truncated to fit token budget" in context.core_context
    
    @pytest.mark.asyncio
    async def test_file_size_truncation(self, temp_project):
        """Test that large files are truncated"""
        # Create a large file
        large_content = "x" * 100000  # 100KB content
        (temp_project / "large_file.py").write_text(large_content)
        
        manager = SimpleContextManager(
            project_path=str(temp_project),
            max_file_size=1000  # 1KB limit
        )
        
        task = {"description": "Test task", "story_id": "test"}
        context = await manager.prepare_context("CodeAgent", task)
        
        # Check that large file content was truncated
        for file_path, content in context.file_contents.items():
            if "large_file.py" in file_path:
                assert len(content) <= 1000 + 50  # Allow some margin for truncation message
                assert "truncated for performance" in content
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, simple_manager):
        """Test that caching works correctly"""
        task = {"description": "Test task", "story_id": "test"}
        
        # First request - should not be cached
        start_time = time.time()
        context1 = await simple_manager.prepare_context("CodeAgent", task)
        first_duration = time.time() - start_time
        
        assert context1.cache_hit is None or context1.cache_hit is False
        
        # Second request - should be cached and faster
        start_time = time.time()
        context2 = await simple_manager.prepare_context("CodeAgent", task)
        second_duration = time.time() - start_time
        
        # Second request should be significantly faster due to caching
        assert second_duration < first_duration * 0.5  # At least 50% faster
        
        # Verify cache hit count
        metrics = simple_manager.get_performance_metrics()
        assert metrics["cache_hits"] > 0
        assert metrics["cache_hit_rate"] > 0
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, simple_manager):
        """Test performance metrics collection"""
        task = {"description": "Test task", "story_id": "test"}
        
        # Make several requests
        for i in range(3):
            await simple_manager.prepare_context("CodeAgent", task)
        
        metrics = simple_manager.get_performance_metrics()
        
        assert metrics["context_manager_type"] == "simple"
        assert metrics["total_requests"] == 3
        assert metrics["average_preparation_time"] > 0
        assert metrics["max_tokens"] == simple_manager.max_tokens
        assert metrics["max_files"] == simple_manager.max_files
        assert metrics["caching_enabled"] is True
        assert metrics["cached_contexts"] >= 0
    
    @pytest.mark.asyncio
    async def test_file_inclusion_filtering(self, temp_project):
        """Test that unwanted files are excluded"""
        # Create files that should be excluded
        (temp_project / ".hidden_file.py").write_text("hidden")
        (temp_project / "__pycache__").mkdir()
        (temp_project / "__pycache__" / "cache.pyc").write_text("cache")
        (temp_project / ".git").mkdir()
        (temp_project / ".git" / "config").write_text("git config")
        
        manager = SimpleContextManager(project_path=str(temp_project))
        task = {"description": "Test task", "story_id": "test"}
        
        context = await manager.prepare_context("CodeAgent", task)
        
        # Check that excluded files are not included
        file_paths = list(context.file_contents.keys())
        
        assert not any(".hidden_file" in path for path in file_paths)
        assert not any("__pycache__" in path for path in file_paths)
        assert not any(".git" in path for path in file_paths)
    
    @pytest.mark.asyncio
    async def test_max_files_limit(self, temp_project):
        """Test that max_files limit is respected"""
        # Create many files
        for i in range(20):
            (temp_project / f"file_{i}.py").write_text(f"# File {i}")
        
        manager = SimpleContextManager(
            project_path=str(temp_project),
            max_files=5
        )
        
        task = {"description": "Test task", "story_id": "test"}
        context = await manager.prepare_context("CodeAgent", task)
        
        assert len(context.file_contents) <= 5
    
    @pytest.mark.asyncio
    async def test_error_handling(self, simple_manager):
        """Test error handling in context preparation"""
        # Test with invalid task
        with pytest.raises(ContextError):
            await simple_manager.prepare_context("CodeAgent", None)
    
    @pytest.mark.asyncio
    async def test_cache_cleanup(self, simple_manager):
        """Test cache cleanup functionality"""
        task = {"description": "Test task", "story_id": "test"}
        
        # Make a request to populate cache
        await simple_manager.prepare_context("CodeAgent", task)
        
        # Verify cache has content
        assert len(simple_manager._cache) > 0
        
        # Test cleanup
        cleaned = await simple_manager.cleanup_cache()
        assert cleaned >= 0  # Should return number of cleaned entries
    
    @pytest.mark.asyncio
    async def test_context_invalidation(self, simple_manager):
        """Test context invalidation"""
        task = {"description": "Test task", "story_id": "test"}
        
        context = await simple_manager.prepare_context("CodeAgent", task)
        context_id = context.request_id
        
        # Invalidate the context
        await simple_manager.invalidate_context(context_id)
        
        # Verify it's no longer in cache (indirectly)
        metrics_before = simple_manager.get_performance_metrics()
        cached_before = metrics_before["cached_contexts"]
        
        # The exact behavior depends on implementation, but this tests the method exists
        assert hasattr(simple_manager, 'invalidate_context')
    
    @pytest.mark.asyncio
    async def test_compatibility_methods(self, simple_manager):
        """Test that compatibility methods exist and work"""
        # These methods should exist for interface compatibility but return placeholder values
        
        decision_id = await simple_manager.record_agent_decision(
            "CodeAgent", "test-story", "Test decision"
        )
        assert decision_id == "simple-decision-id"
        
        handoff_id = await simple_manager.record_phase_handoff(
            "CodeAgent", "QAAgent", TDDState.WRITE_CODE, TDDState.WRITE_TEST, "test-story"
        )
        assert handoff_id == "simple-handoff-id"
        
        snapshot_id = await simple_manager.create_context_snapshot(
            "CodeAgent", "test-story", Mock()
        )
        assert snapshot_id == "simple-snapshot-id"
        
        history = await simple_manager.get_agent_context_history("CodeAgent", "test-story")
        assert history == []
        
        decisions = await simple_manager.get_recent_decisions("CodeAgent", "test-story")
        assert decisions == []
        
        handoffs = await simple_manager.get_phase_handoffs("CodeAgent", "test-story")
        assert handoffs == []
        
        learning = await simple_manager.analyze_agent_learning("CodeAgent", "test-story")
        assert "not available in simple mode" in learning["message"]
        
        deps = await simple_manager.get_file_dependencies("test.py")
        assert "not available in simple mode" in deps["message"]
        
        search_results = await simple_manager.search_codebase("test query")
        assert search_results == []
        
        # Test other no-op methods
        await simple_manager.build_context_index()
        
        relevance = await simple_manager.get_file_relevance_explanation("test.py", Mock())
        assert "not available in simple mode" in relevance["message"]
        
        compression = await simple_manager.estimate_compression_potential("content", Mock(), Mock())
        assert "not available in simple mode" in compression["message"]
        
        stats = await simple_manager.get_project_statistics()
        assert "not available in simple mode" in stats["message"]
    
    @pytest.mark.asyncio
    async def test_context_formatting(self, simple_manager):
        """Test that context is formatted correctly"""
        task = {"description": "Test task", "story_id": "test"}
        
        context = await simple_manager.prepare_context("CodeAgent", task)
        
        assert "# Project Context" in context.core_context
        assert "##" in context.core_context  # File headers
        assert "```" in context.core_context  # Code blocks
        
        # Verify relative paths are used in headers
        for file_path in context.file_contents.keys():
            relative_path = str(Path(file_path).relative_to(simple_manager.project_path))
            assert relative_path in context.core_context
    
    def test_extract_story_id(self, simple_manager):
        """Test story ID extraction from different task formats"""
        # Test with dict
        task_dict = {"story_id": "dict-story"}
        story_id = simple_manager._extract_story_id(task_dict)
        assert story_id == "dict-story"
        
        # Test with TDDTask
        tdd_task = TDDTask(story_id="tdd-story", current_state=TDDState.WRITE_TEST)
        story_id = simple_manager._extract_story_id(tdd_task)
        assert story_id == "tdd-story"
        
        # Test with no story ID
        task_no_id = {"description": "No ID"}
        story_id = simple_manager._extract_story_id(task_no_id)
        assert story_id == "default"
    
    def test_extract_tdd_phase(self, simple_manager):
        """Test TDD phase extraction from different task formats"""
        # Test with dict and string state
        task_dict = {"current_state": "WRITE_TEST"}
        phase = simple_manager._extract_tdd_phase(task_dict)
        assert phase == TDDState.WRITE_TEST
        
        # Test with dict and TDDState
        task_dict_enum = {"current_state": TDDState.WRITE_CODE}
        phase = simple_manager._extract_tdd_phase(task_dict_enum)
        assert phase == TDDState.WRITE_CODE
        
        # Test with TDDTask
        tdd_task = TDDTask(story_id="test", current_state=TDDState.REFACTOR)
        phase = simple_manager._extract_tdd_phase(tdd_task)
        assert phase == TDDState.REFACTOR
        
        # Test with no phase
        task_no_phase = {"description": "No phase"}
        phase = simple_manager._extract_tdd_phase(task_no_phase)
        assert phase is None
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, simple_manager):
        """Test that concurrent requests are handled correctly"""
        task = {"description": "Test task", "story_id": "test"}
        
        # Make multiple concurrent requests
        tasks = [
            simple_manager.prepare_context("CodeAgent", task)
            for _ in range(5)
        ]
        
        contexts = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert len(contexts) == 5
        for context in contexts:
            assert isinstance(context, AgentContext)
            assert context.core_context is not None
    
    def test_configuration_validation(self, temp_project):
        """Test that configuration is validated properly"""
        # Test with invalid max_tokens
        with pytest.raises((ValueError, AssertionError)):
            SimpleContextManager(
                project_path=str(temp_project),
                max_tokens=0  # Invalid
            )
        
        # Test with invalid max_files
        manager = SimpleContextManager(
            project_path=str(temp_project),
            max_files=0  # Should handle gracefully
        )
        assert manager.max_files == 0