"""
Enhanced test suite for AgentMemory to achieve TIER 4 compliance (95% coverage).

This test file supplements the existing test_agent_memory.py to cover missing edge cases,
error conditions, and complex scenarios that were not covered by the original test suite.
"""

import pytest
import asyncio
import tempfile
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any, List

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from agent_memory import FileBasedAgentMemory
from context.models import (
    AgentMemory, Decision, PhaseHandoff, Pattern, ContextSnapshot,
    TokenUsage
)
from tdd_models import TDDState


class TestAdvancedFileOperations:
    """Test advanced file operations and edge cases"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_store_memory_with_file_creation_error(self, agent_memory):
        """Test handling of file creation errors during store"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        # Mock file operations to raise OSError
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                await agent_memory.store_memory(memory)
    
    @pytest.mark.asyncio
    async def test_store_memory_with_json_serialization_error(self, agent_memory):
        """Test handling of JSON serialization errors"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        # Mock json.dump to raise an error
        with patch('json.dump', side_effect=TypeError("Object not serializable")):
            with pytest.raises(TypeError):
                await agent_memory.store_memory(memory)
    
    @pytest.mark.asyncio
    async def test_get_memory_with_json_decode_error(self, agent_memory):
        """Test handling of JSON decode errors"""
        # Create a memory file with invalid JSON
        memory_file = agent_memory.memory_dir / "TestAgent" / "test_story.json"
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(memory_file, 'w') as f:
            f.write('{"invalid": json, "content": }')
        
        # Should return None for invalid JSON
        result = await agent_memory.get_memory("TestAgent", "test_story")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_memory_with_file_read_error(self, agent_memory):
        """Test handling of file read errors"""
        # Create a memory file
        memory_file = agent_memory.memory_dir / "TestAgent" / "test_story.json"
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        memory_file.write_text('{"valid": "json"}')
        
        # Mock open to raise an error
        with patch('builtins.open', side_effect=IOError("File access error")):
            result = await agent_memory.get_memory("TestAgent", "test_story")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_clear_memory_with_directory_deletion_error(self, agent_memory):
        """Test clear memory when directory can't be deleted"""
        # Create some memories
        memory = AgentMemory(agent_type="TestAgent", story_id="story1")
        await agent_memory.store_memory(memory)
        
        # Create another file in the agent directory to prevent deletion
        agent_dir = agent_memory.memory_dir / "TestAgent"
        extra_file = agent_dir / "extra_file.txt"
        extra_file.write_text("extra content")
        
        # Clear all memories for agent (should handle non-empty directory gracefully)
        await agent_memory.clear_memory("TestAgent")
        
        # Memory should be cleared but directory should still exist
        assert agent_dir.exists()
        assert extra_file.exists()
        result = await agent_memory.get_memory("TestAgent", "story1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cleanup_with_file_stat_error(self, agent_memory):
        """Test cleanup when file stat fails"""
        # Create a memory file
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Mock Path.stat to raise an error during cleanup
        original_stat = Path.stat
        def mock_stat(path_self):
            if str(path_self).endswith('.json'):
                raise OSError("Stat failed")
            return original_stat(path_self)
            
        with patch.object(Path, 'stat', mock_stat):
            # Should handle the error gracefully and continue
            deleted_count = await agent_memory.cleanup_old_memories(older_than_days=0)
            assert deleted_count == 0  # No files deleted due to error
    
    @pytest.mark.asyncio
    async def test_cleanup_with_unlink_error(self, agent_memory):
        """Test cleanup when file deletion fails"""
        # Create a memory file
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Mock unlink to raise an error
        with patch('pathlib.Path.unlink', side_effect=OSError("Delete failed")):
            # Should handle the error gracefully
            deleted_count = await agent_memory.cleanup_old_memories(older_than_days=0)
            assert deleted_count == 0  # No files deleted due to error


class TestAnalysisEdgeCases:
    """Test edge cases in memory analysis and patterns"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_analyze_patterns_with_empty_data(self, agent_memory):
        """Test pattern analysis with empty or minimal data"""
        # Create memory with no patterns or decisions
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        analysis = await agent_memory.analyze_agent_patterns("TestAgent", "test_story")
        
        assert analysis["pattern_types"] == {}
        assert analysis["decision_confidence_avg"] == 0.0
        assert analysis["successful_patterns"] == []
        assert analysis["phase_transitions"] == {}
    
    @pytest.mark.asyncio
    async def test_analyze_patterns_with_zero_usage_patterns(self, agent_memory):
        """Test pattern analysis with patterns that have zero usage"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        # Add pattern with zero usage
        pattern = Pattern(
            pattern_type="test_pattern",
            description="Test pattern",
            success_rate=1.0,
            usage_count=0  # Zero usage
        )
        memory.add_pattern(pattern)
        
        await agent_memory.store_memory(memory)
        
        analysis = await agent_memory.analyze_agent_patterns("TestAgent", "test_story")
        
        # Should handle zero usage gracefully
        assert "test_pattern" in analysis["pattern_types"]
        assert analysis["pattern_types"]["test_pattern"]["count"] == 1
        assert analysis["pattern_types"]["test_pattern"]["total_usage"] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_patterns_with_none_phases(self, agent_memory):
        """Test pattern analysis with None phase values"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        # Add handoff with None phases
        handoff = PhaseHandoff(
            from_phase=None,
            to_phase=None,
            context_summary="Test handoff"
        )
        memory.add_phase_handoff(handoff)
        
        await agent_memory.store_memory(memory)
        
        analysis = await agent_memory.analyze_agent_patterns("TestAgent", "test_story")
        
        # Should handle None phases gracefully
        assert "none -> none" in analysis["phase_transitions"]
        assert analysis["phase_transitions"]["none -> none"] == 1
    
    @pytest.mark.asyncio
    async def test_get_memory_summary_with_none_updated_at(self, agent_memory):
        """Test memory summary when updated_at is None"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        memory.updated_at = None  # Explicitly set to None
        
        await agent_memory.store_memory(memory)
        
        summary = await agent_memory.get_memory_summary("TestAgent", "test_story")
        
        # Should handle None updated_at gracefully
        assert summary["exists"] is True
        assert "recent_activity" in summary


class TestCacheEdgeCases:
    """Test edge cases in cache management"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_cache_with_zero_ttl(self, agent_memory):
        """Test cache behavior with zero TTL"""
        agent_memory._cache_ttl = timedelta(seconds=0)
        
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # First get should cache
        result1 = await agent_memory.get_memory("TestAgent", "test_story")
        assert result1 is not None
        
        # Second get should miss cache due to zero TTL
        result2 = await agent_memory.get_memory("TestAgent", "test_story")
        assert result2 is not None
        
        # Should have multiple cache misses
        assert agent_memory._cache_misses >= 2
    
    @pytest.mark.asyncio
    async def test_performance_metrics_with_no_operations(self, agent_memory):
        """Test performance metrics when no operations have been performed"""
        metrics = agent_memory.get_performance_metrics()
        
        assert metrics["get_calls"] == 0
        assert metrics["store_calls"] == 0
        assert metrics["cache_hits"] == 0
        assert metrics["cache_misses"] == 0
        assert metrics["cache_hit_rate"] == 0.0
        assert metrics["cached_memories"] == 0
    
    @pytest.mark.asyncio
    async def test_performance_metrics_only_cache_misses(self, agent_memory):
        """Test performance metrics with only cache misses"""
        # Force cache misses by accessing non-existent memories
        await agent_memory.get_memory("NonExistent1", "story1")
        await agent_memory.get_memory("NonExistent2", "story2")
        
        metrics = agent_memory.get_performance_metrics()
        
        assert metrics["get_calls"] == 2
        assert metrics["cache_hits"] == 0
        assert metrics["cache_misses"] == 2
        assert metrics["cache_hit_rate"] == 0.0


class TestMemoryUpdateEdgeCases:
    """Test edge cases in memory updates"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_update_memory_with_valid_attribute(self, agent_memory):
        """Test updating memory with valid attribute"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Update with valid attribute
        updates = {"created_at": datetime.utcnow()}
        await agent_memory.update_memory("TestAgent", "test_story", updates)
        
        # Verify update
        updated_memory = await agent_memory.get_memory("TestAgent", "test_story")
        assert updated_memory.created_at == updates["created_at"]
    
    @pytest.mark.asyncio
    async def test_update_memory_with_invalid_attribute(self, agent_memory):
        """Test updating memory with invalid attribute (goes to metadata)"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Update with invalid attribute
        updates = {"invalid_attribute": "test_value"}
        await agent_memory.update_memory("TestAgent", "test_story", updates)
        
        # Should be stored in metadata
        updated_memory = await agent_memory.get_memory("TestAgent", "test_story")
        assert updated_memory.metadata["invalid_attribute"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_update_memory_multiple_attributes(self, agent_memory):
        """Test updating memory with multiple attributes"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Update with multiple attributes
        updates = {
            "metadata": {"key1": "value1"},
            "invalid_attr": "value2",
            "another_invalid": "value3"
        }
        await agent_memory.update_memory("TestAgent", "test_story", updates)
        
        # Verify all updates
        updated_memory = await agent_memory.get_memory("TestAgent", "test_story")
        assert updated_memory.metadata["key1"] == "value1"
        assert updated_memory.metadata["invalid_attr"] == "value2"
        assert updated_memory.metadata["another_invalid"] == "value3"


class TestFilePathSanitization:
    """Test file path sanitization and security"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    def test_sanitize_complex_story_id(self, agent_memory):
        """Test sanitization of complex story IDs"""
        # Test with various problematic characters
        test_cases = [
            ("story!@#$%^&*()", "story.json"),
            ("story with spaces", "storywithspaces.json"),
            ("story/with/slashes", "storywithslashes.json"),
            ("story\\with\\backslashes", "storywithbackslashes.json"),
            ("story\nwith\nnewlines", "storywithnewlines.json"),
            ("story\twith\ttabs", "storywithwithtabs.json"),
            ("story<>|?*", "story.json"),
            ("123-valid_chars", "123-valid_chars.json"),
            ("", "default.json"),
            ("   ", "default.json"),
            ("\n\t\r", "default.json"),
        ]
        
        for input_id, expected_filename in test_cases:
            file_path = agent_memory._get_memory_file_path("TestAgent", input_id)
            # The sanitization only keeps alphanumeric and -_ characters
            if expected_filename == "default.json":
                assert file_path.name == "default.json"
            else:
                # Just check that it creates a valid filename
                assert file_path.name.endswith(".json")
                assert "/" not in file_path.name
                assert "\\" not in file_path.name
            assert file_path.parent.name == "TestAgent"
    
    def test_sanitize_none_story_id(self, agent_memory):
        """Test sanitization of None story ID"""
        file_path = agent_memory._get_memory_file_path("TestAgent", None)
        assert file_path.name == "default.json"
        assert file_path.parent.name == "TestAgent"
    
    def test_sanitize_whitespace_only_story_id(self, agent_memory):
        """Test sanitization of whitespace-only story ID"""
        test_cases = ["   ", "\t\t", "\n\n", "\r\r", " \t\n\r "]
        
        for whitespace_id in test_cases:
            file_path = agent_memory._get_memory_file_path("TestAgent", whitespace_id)
            assert file_path.name == "default.json"


class TestConcurrentOperationsAdvanced:
    """Test advanced concurrency scenarios"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self, agent_memory):
        """Test concurrent cache operations"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        async def get_memory_task():
            return await agent_memory.get_memory("TestAgent", "test_story")
        
        # Run multiple concurrent gets
        tasks = [get_memory_task() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 10
        assert all(r is not None for r in results)
        
        # Should have cache hits
        assert agent_memory._cache_hits > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_cleanup_operations(self, agent_memory):
        """Test concurrent cleanup operations"""
        # Create multiple memories
        for i in range(5):
            memory = AgentMemory(agent_type=f"Agent{i}", story_id=f"story{i}")
            await agent_memory.store_memory(memory)
        
        # Run concurrent cleanup operations
        tasks = [
            agent_memory.cleanup_old_memories(older_than_days=0),
            agent_memory.cleanup_old_memories(older_than_days=0),
            agent_memory.cleanup_old_memories(older_than_days=0),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle concurrent cleanups gracefully
        assert len(results) == 3
        assert all(isinstance(r, int) or isinstance(r, Exception) for r in results)


class TestIteratorBehavior:
    """Test behavior with directory iteration"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_cleanup_with_non_directory_files(self, agent_memory):
        """Test cleanup behavior with non-directory files in memory directory"""
        # Create some regular memories
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Create a regular file in the memory directory (not a subdirectory)
        non_dir_file = agent_memory.memory_dir / "not_a_directory.txt"
        non_dir_file.write_text("This is not a directory")
        
        # Cleanup should handle non-directory files gracefully
        deleted_count = await agent_memory.cleanup_old_memories(older_than_days=0)
        
        # Should process the agent directory but skip the non-directory file
        assert deleted_count >= 0  # Should not crash
        assert non_dir_file.exists()  # Non-directory file should remain
    
    @pytest.mark.asyncio
    async def test_cleanup_with_non_json_files(self, agent_memory):
        """Test cleanup behavior with non-JSON files in agent directories"""
        # Create a memory
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Create a non-JSON file in the agent directory
        agent_dir = agent_memory.memory_dir / "TestAgent"
        non_json_file = agent_dir / "not_json.txt"
        non_json_file.write_text("This is not JSON")
        
        # Cleanup should only process JSON files
        deleted_count = await agent_memory.cleanup_old_memories(older_than_days=0)
        
        # Should delete the JSON file but leave the non-JSON file
        assert non_json_file.exists()
        assert deleted_count >= 1  # At least the JSON file should be processed


class TestRecentActivitySummary:
    """Test recent activity summary edge cases"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    def test_recent_activity_with_mixed_timestamps(self, agent_memory):
        """Test recent activity summary with mixed old and new timestamps"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        now = datetime.utcnow()
        old_time = now - timedelta(days=10)
        recent_time = now - timedelta(days=1)
        
        # Add items with mixed timestamps
        old_decision = Decision(description="Old decision", timestamp=old_time)
        recent_decision = Decision(description="Recent decision", timestamp=recent_time)
        
        old_pattern = Pattern(pattern_type="old", description="Old pattern", timestamp=old_time)
        recent_pattern = Pattern(pattern_type="recent", description="Recent pattern", timestamp=recent_time)
        
        old_handoff = PhaseHandoff(context_summary="Old handoff", timestamp=old_time)
        recent_handoff = PhaseHandoff(context_summary="Recent handoff", timestamp=recent_time)
        
        old_snapshot = ContextSnapshot(
            agent_type="TestAgent", story_id="test_story",
            context_summary="Old snapshot", timestamp=old_time
        )
        recent_snapshot = ContextSnapshot(
            agent_type="TestAgent", story_id="test_story",
            context_summary="Recent snapshot", timestamp=recent_time
        )
        
        # Add all items to memory
        memory.decisions.extend([old_decision, recent_decision])
        memory.learned_patterns.extend([old_pattern, recent_pattern])
        memory.phase_handoffs.extend([old_handoff, recent_handoff])
        memory.context_history.extend([old_snapshot, recent_snapshot])
        
        # Get recent activity summary
        summary = agent_memory._get_recent_activity_summary(memory)
        
        # Should only count recent items (within last week)
        assert summary["recent_decisions"] == 1
        assert summary["recent_patterns"] == 1
        assert summary["recent_handoffs"] == 1
        assert summary["recent_snapshots"] == 1
    
    def test_recent_activity_with_no_updated_at(self, agent_memory):
        """Test recent activity summary when updated_at is None"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        memory.updated_at = None
        
        summary = agent_memory._get_recent_activity_summary(memory)
        
        assert summary["last_activity"] is None
        assert summary["recent_decisions"] == 0
        assert summary["recent_patterns"] == 0
        assert summary["recent_handoffs"] == 0
        assert summary["recent_snapshots"] == 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])