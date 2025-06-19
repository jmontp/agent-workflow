"""
Comprehensive test coverage for agent_memory.py module.

Tests cover all classes, methods, and edge cases to achieve 95%+ coverage.
"""

import asyncio
import json
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, mock_open
from typing import Dict, Any, List

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from agent_memory import FileBasedAgentMemory
from context.models import AgentMemory, Decision, PhaseHandoff, Pattern, ContextSnapshot
from context.interfaces import IAgentMemory
from tdd_models import TDDState, TDDTask, TDDCycle


class TestFileBasedAgentMemory:
    """Test FileBasedAgentMemory class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_manager(self, temp_dir):
        """Create a FileBasedAgentMemory instance for testing"""
        return FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.fixture
    def mock_agent_memory(self):
        """Create a mock AgentMemory for testing"""
        memory = Mock(spec=AgentMemory)
        memory.agent_type = "test_agent"
        memory.story_id = "story-123"
        memory.created_at = datetime.utcnow()
        memory.updated_at = datetime.utcnow()
        memory.decisions = []
        memory.learned_patterns = []
        memory.phase_handoffs = []
        memory.context_history = []
        memory.artifacts = {}
        memory.metadata = {}
        memory.to_dict.return_value = {
            "agent_type": "test_agent",
            "story_id": "story-123",
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
            "decisions": [],
            "learned_patterns": [],
            "phase_handoffs": [],
            "context_history": [],
            "artifacts": {},
            "metadata": {}
        }
        return memory
    
    @pytest.fixture
    def mock_decision(self):
        """Create a mock Decision for testing"""
        decision = Mock(spec=Decision)
        decision.id = "decision-123"
        decision.description = "Test decision"
        decision.confidence = 0.85
        decision.timestamp = datetime.utcnow()
        return decision
    
    @pytest.fixture
    def mock_pattern(self):
        """Create a mock Pattern for testing"""
        pattern = Mock(spec=Pattern)
        pattern.id = "pattern-123"
        pattern.pattern_type = "test_pattern"
        pattern.description = "Test pattern"
        pattern.success_rate = 0.9
        pattern.usage_count = 5
        pattern.timestamp = datetime.utcnow()
        return pattern
    
    @pytest.fixture
    def mock_phase_handoff(self):
        """Create a mock PhaseHandoff for testing"""
        handoff = Mock(spec=PhaseHandoff)
        handoff.id = "handoff-123"
        handoff.from_phase = TDDState.RED
        handoff.to_phase = TDDState.GREEN
        handoff.timestamp = datetime.utcnow()
        return handoff
    
    @pytest.fixture
    def mock_context_snapshot(self):
        """Create a mock ContextSnapshot for testing"""
        snapshot = Mock(spec=ContextSnapshot)
        snapshot.id = "snapshot-123"
        snapshot.tdd_phase = TDDState.RED
        snapshot.timestamp = datetime.utcnow()
        return snapshot
    
    def test_initialization(self, temp_dir):
        """Test FileBasedAgentMemory initialization"""
        memory_manager = FileBasedAgentMemory(base_path=temp_dir)
        
        assert memory_manager.base_path == Path(temp_dir)
        assert memory_manager.memory_dir == Path(temp_dir) / "agent_memory"
        assert memory_manager.memory_dir.exists()
        assert len(memory_manager._memory_cache) == 0
        assert memory_manager._cache_ttl == timedelta(minutes=30)
        assert memory_manager._get_calls == 0
        assert memory_manager._store_calls == 0
        assert memory_manager._cache_hits == 0
        assert memory_manager._cache_misses == 0
    
    def test_initialization_default_path(self):
        """Test FileBasedAgentMemory with default path"""
        memory_manager = FileBasedAgentMemory()
        
        assert memory_manager.base_path == Path(".orch-state")
        assert memory_manager.memory_dir == Path(".orch-state") / "agent_memory"
    
    def test_inheritance_from_interface(self, memory_manager):
        """Test that FileBasedAgentMemory implements IAgentMemory interface"""
        assert isinstance(memory_manager, IAgentMemory)
        
        # Check that required methods exist
        assert hasattr(memory_manager, 'get_memory')
        assert hasattr(memory_manager, 'store_memory')
        assert hasattr(memory_manager, 'update_memory')
        assert hasattr(memory_manager, 'clear_memory')
    
    @pytest.mark.asyncio
    async def test_get_memory_nonexistent(self, memory_manager):
        """Test getting memory for non-existent agent/story"""
        result = await memory_manager.get_memory("nonexistent_agent", "nonexistent_story")
        
        assert result is None
        assert memory_manager._get_calls == 1
        assert memory_manager._cache_misses == 1
        assert memory_manager._cache_hits == 0
    
    @pytest.mark.asyncio
    async def test_store_and_get_memory(self, memory_manager, mock_agent_memory):
        """Test storing and retrieving memory"""
        # Store memory
        await memory_manager.store_memory(mock_agent_memory)
        
        assert memory_manager._store_calls == 1
        
        # Verify file was created
        memory_file = memory_manager._get_memory_file_path(
            mock_agent_memory.agent_type, 
            mock_agent_memory.story_id
        )
        assert memory_file.exists()
        
        # Get memory back
        retrieved = await memory_manager.get_memory(
            mock_agent_memory.agent_type, 
            mock_agent_memory.story_id
        )
        
        assert retrieved is not None
        assert memory_manager._get_calls == 1
        assert memory_manager._cache_hits == 1  # Should hit cache
    
    @pytest.mark.asyncio
    async def test_memory_caching(self, memory_manager, mock_agent_memory):
        """Test memory caching behavior"""
        # Store memory
        await memory_manager.store_memory(mock_agent_memory)
        
        # First get - cache miss, loads from file
        retrieved1 = await memory_manager.get_memory(
            mock_agent_memory.agent_type, 
            mock_agent_memory.story_id
        )
        
        # Second get - cache hit
        retrieved2 = await memory_manager.get_memory(
            mock_agent_memory.agent_type, 
            mock_agent_memory.story_id
        )
        
        assert retrieved1 is not None
        assert retrieved2 is not None
        assert memory_manager._get_calls == 2
        assert memory_manager._cache_hits == 2  # Both should be cache hits after store
        assert memory_manager._cache_misses == 0
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, memory_manager, mock_agent_memory):
        """Test cache expiration functionality"""
        # Set very short cache TTL
        memory_manager._cache_ttl = timedelta(milliseconds=50)
        
        # Store memory
        await memory_manager.store_memory(mock_agent_memory)
        
        # Wait for cache to expire
        await asyncio.sleep(0.1)
        
        # Get memory - should reload from file due to expiration
        retrieved = await memory_manager.get_memory(
            mock_agent_memory.agent_type, 
            mock_agent_memory.story_id
        )
        
        assert retrieved is not None
        # Cache should have been cleared due to expiration
        cache_key = f"{mock_agent_memory.agent_type}:{mock_agent_memory.story_id}"
        assert cache_key not in memory_manager._memory_cache
    
    @pytest.mark.asyncio
    async def test_update_memory_existing(self, memory_manager, mock_agent_memory):
        """Test updating existing memory"""
        # Store initial memory
        await memory_manager.store_memory(mock_agent_memory)
        
        # Update memory
        updates = {
            "metadata": {"updated": True, "version": 2}
        }
        
        await memory_manager.update_memory(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id,
            updates
        )
        
        # Memory should be updated
        assert memory_manager._store_calls == 2  # Initial store + update
    
    @pytest.mark.asyncio
    async def test_update_memory_create_new(self, memory_manager):
        """Test updating memory that doesn't exist (creates new)"""
        updates = {
            "metadata": {"new_memory": True}
        }
        
        # Mock AgentMemory creation
        with patch('agent_memory.AgentMemory') as mock_memory_class:
            mock_memory = Mock()
            mock_memory.agent_type = "new_agent"
            mock_memory.story_id = "new_story"
            mock_memory.metadata = {}
            mock_memory.to_dict.return_value = {"test": "data"}
            mock_memory_class.return_value = mock_memory
            
            await memory_manager.update_memory("new_agent", "new_story", updates)
            
            # Should have created new memory
            mock_memory_class.assert_called_once_with(
                agent_type="new_agent",
                story_id="new_story"
            )
            assert memory_manager._store_calls == 1
    
    @pytest.mark.asyncio
    async def test_update_memory_with_unknown_attribute(self, memory_manager, mock_agent_memory):
        """Test updating memory with unknown attribute (goes to metadata)"""
        await memory_manager.store_memory(mock_agent_memory)
        
        updates = {
            "unknown_attribute": "should_go_to_metadata"
        }
        
        await memory_manager.update_memory(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id,
            updates
        )
        
        # Should have updated metadata since unknown_attribute doesn't exist
        # The mock's metadata should be updated
        assert memory_manager._store_calls == 2
    
    @pytest.mark.asyncio
    async def test_clear_memory_specific_story(self, memory_manager, mock_agent_memory):
        """Test clearing memory for specific story"""
        # Store memory
        await memory_manager.store_memory(mock_agent_memory)
        
        memory_file = memory_manager._get_memory_file_path(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id
        )
        assert memory_file.exists()
        
        # Clear specific story memory
        await memory_manager.clear_memory(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id
        )
        
        # File should be deleted
        assert not memory_file.exists()
        
        # Cache should be cleared
        cache_key = f"{mock_agent_memory.agent_type}:{mock_agent_memory.story_id}"
        assert cache_key not in memory_manager._memory_cache
    
    @pytest.mark.asyncio
    async def test_clear_memory_all_for_agent(self, memory_manager, mock_agent_memory):
        """Test clearing all memory for an agent"""
        # Store memories for multiple stories
        await memory_manager.store_memory(mock_agent_memory)
        
        memory2 = Mock(spec=AgentMemory)
        memory2.agent_type = mock_agent_memory.agent_type
        memory2.story_id = "story-456"
        memory2.updated_at = datetime.utcnow()
        memory2.to_dict.return_value = {"agent_type": memory2.agent_type, "story_id": memory2.story_id}
        
        await memory_manager.store_memory(memory2)
        
        # Clear all memories for agent
        await memory_manager.clear_memory(mock_agent_memory.agent_type, story_id=None)
        
        # Agent directory should be cleaned up
        agent_dir = memory_manager.memory_dir / mock_agent_memory.agent_type
        # Directory might still exist if it has subdirectories, but should be empty of JSON files
        if agent_dir.exists():
            json_files = list(agent_dir.glob("*.json"))
            assert len(json_files) == 0
        
        # Cache should be cleared for both stories
        cache_key1 = f"{mock_agent_memory.agent_type}:{mock_agent_memory.story_id}"
        cache_key2 = f"{memory2.agent_type}:{memory2.story_id}"
        assert cache_key1 not in memory_manager._memory_cache
        assert cache_key2 not in memory_manager._memory_cache
    
    @pytest.mark.asyncio
    async def test_add_decision(self, memory_manager, mock_decision):
        """Test adding decision to memory"""
        agent_type = "test_agent"
        story_id = "story-123"
        
        with patch('agent_memory.AgentMemory') as mock_memory_class:
            mock_memory = Mock()
            mock_memory.agent_type = agent_type
            mock_memory.story_id = story_id
            mock_memory.add_decision = Mock()
            mock_memory.to_dict.return_value = {"test": "data"}
            mock_memory_class.return_value = mock_memory
            
            await memory_manager.add_decision(agent_type, story_id, mock_decision)
            
            # Should have created memory and added decision
            mock_memory.add_decision.assert_called_once_with(mock_decision)
            assert memory_manager._store_calls == 1
    
    @pytest.mark.asyncio
    async def test_add_pattern(self, memory_manager, mock_pattern):
        """Test adding pattern to memory"""
        agent_type = "test_agent"
        story_id = "story-123"
        
        with patch('agent_memory.AgentMemory') as mock_memory_class:
            mock_memory = Mock()
            mock_memory.agent_type = agent_type
            mock_memory.story_id = story_id
            mock_memory.add_pattern = Mock()
            mock_memory.to_dict.return_value = {"test": "data"}
            mock_memory_class.return_value = mock_memory
            
            await memory_manager.add_pattern(agent_type, story_id, mock_pattern)
            
            # Should have created memory and added pattern
            mock_memory.add_pattern.assert_called_once_with(mock_pattern)
            assert memory_manager._store_calls == 1
    
    @pytest.mark.asyncio
    async def test_add_phase_handoff(self, memory_manager, mock_phase_handoff):
        """Test adding phase handoff to memory"""
        agent_type = "test_agent"
        story_id = "story-123"
        
        with patch('agent_memory.AgentMemory') as mock_memory_class:
            mock_memory = Mock()
            mock_memory.agent_type = agent_type
            mock_memory.story_id = story_id
            mock_memory.add_phase_handoff = Mock()
            mock_memory.to_dict.return_value = {"test": "data"}
            mock_memory_class.return_value = mock_memory
            
            await memory_manager.add_phase_handoff(agent_type, story_id, mock_phase_handoff)
            
            # Should have created memory and added handoff
            mock_memory.add_phase_handoff.assert_called_once_with(mock_phase_handoff)
            assert memory_manager._store_calls == 1
    
    @pytest.mark.asyncio
    async def test_add_context_snapshot(self, memory_manager, mock_context_snapshot):
        """Test adding context snapshot to memory"""
        agent_type = "test_agent"
        story_id = "story-123"
        
        with patch('agent_memory.AgentMemory') as mock_memory_class:
            mock_memory = Mock()
            mock_memory.agent_type = agent_type
            mock_memory.story_id = story_id
            mock_memory.add_context_snapshot = Mock()
            mock_memory.to_dict.return_value = {"test": "data"}
            mock_memory_class.return_value = mock_memory
            
            await memory_manager.add_context_snapshot(agent_type, story_id, mock_context_snapshot)
            
            # Should have created memory and added snapshot
            mock_memory.add_context_snapshot.assert_called_once_with(mock_context_snapshot)
            assert memory_manager._store_calls == 1
    
    @pytest.mark.asyncio
    async def test_get_recent_decisions(self, memory_manager, mock_agent_memory):
        """Test getting recent decisions"""
        mock_decisions = [Mock(), Mock(), Mock()]
        mock_agent_memory.get_recent_decisions.return_value = mock_decisions
        
        await memory_manager.store_memory(mock_agent_memory)
        
        decisions = await memory_manager.get_recent_decisions(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id,
            limit=5
        )
        
        assert len(decisions) == 3
    
    @pytest.mark.asyncio
    async def test_get_recent_decisions_no_memory(self, memory_manager):
        """Test getting recent decisions when no memory exists"""
        decisions = await memory_manager.get_recent_decisions(
            "nonexistent_agent",
            "nonexistent_story"
        )
        
        assert decisions == []
    
    @pytest.mark.asyncio
    async def test_get_patterns_by_type(self, memory_manager, mock_agent_memory):
        """Test getting patterns by type"""
        mock_patterns = [Mock(), Mock()]
        mock_agent_memory.get_patterns_by_type.return_value = mock_patterns
        
        await memory_manager.store_memory(mock_agent_memory)
        
        patterns = await memory_manager.get_patterns_by_type(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id,
            "test_pattern"
        )
        
        assert len(patterns) == 2
        mock_agent_memory.get_patterns_by_type.assert_called_once_with("test_pattern")
    
    @pytest.mark.asyncio
    async def test_get_patterns_by_type_no_memory(self, memory_manager):
        """Test getting patterns by type when no memory exists"""
        patterns = await memory_manager.get_patterns_by_type(
            "nonexistent_agent",
            "nonexistent_story",
            "test_pattern"
        )
        
        assert patterns == []
    
    @pytest.mark.asyncio
    async def test_get_phase_handoffs(self, memory_manager, mock_agent_memory):
        """Test getting phase handoffs"""
        # Create mock handoffs
        handoff1 = Mock()
        handoff1.from_phase = TDDState.RED
        handoff1.to_phase = TDDState.GREEN
        handoff1.timestamp = datetime.utcnow()
        
        handoff2 = Mock()
        handoff2.from_phase = TDDState.GREEN
        handoff2.to_phase = TDDState.REFACTOR
        handoff2.timestamp = datetime.utcnow() - timedelta(minutes=1)
        
        mock_agent_memory.phase_handoffs = [handoff1, handoff2]
        
        await memory_manager.store_memory(mock_agent_memory)
        
        # Test getting all handoffs
        handoffs = await memory_manager.get_phase_handoffs(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id
        )
        
        assert len(handoffs) == 2
        # Should be sorted by timestamp (most recent first)
        assert handoffs[0].timestamp > handoffs[1].timestamp
        
        # Test filtering by from_phase
        handoffs_from_red = await memory_manager.get_phase_handoffs(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id,
            from_phase=TDDState.RED
        )
        
        assert len(handoffs_from_red) == 1
        assert handoffs_from_red[0].from_phase == TDDState.RED
        
        # Test filtering by to_phase
        handoffs_to_green = await memory_manager.get_phase_handoffs(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id,
            to_phase=TDDState.GREEN
        )
        
        assert len(handoffs_to_green) == 1
        assert handoffs_to_green[0].to_phase == TDDState.GREEN
    
    @pytest.mark.asyncio
    async def test_get_phase_handoffs_no_memory(self, memory_manager):
        """Test getting phase handoffs when no memory exists"""
        handoffs = await memory_manager.get_phase_handoffs(
            "nonexistent_agent",
            "nonexistent_story"
        )
        
        assert handoffs == []
    
    @pytest.mark.asyncio
    async def test_get_context_history(self, memory_manager, mock_agent_memory):
        """Test getting context history"""
        # Create mock snapshots
        snapshot1 = Mock()
        snapshot1.tdd_phase = TDDState.RED
        snapshot1.timestamp = datetime.utcnow()
        
        snapshot2 = Mock()
        snapshot2.tdd_phase = TDDState.GREEN
        snapshot2.timestamp = datetime.utcnow() - timedelta(minutes=1)
        
        snapshot3 = Mock()
        snapshot3.tdd_phase = TDDState.RED
        snapshot3.timestamp = datetime.utcnow() - timedelta(minutes=2)
        
        mock_agent_memory.context_history = [snapshot1, snapshot2, snapshot3]
        
        await memory_manager.store_memory(mock_agent_memory)
        
        # Test getting all history
        history = await memory_manager.get_context_history(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id
        )
        
        assert len(history) == 3
        # Should be sorted by timestamp (most recent first)
        assert history[0].timestamp > history[1].timestamp > history[2].timestamp
        
        # Test filtering by TDD phase
        red_history = await memory_manager.get_context_history(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id,
            tdd_phase=TDDState.RED
        )
        
        assert len(red_history) == 2
        assert all(h.tdd_phase == TDDState.RED for h in red_history)
        
        # Test limiting results
        limited_history = await memory_manager.get_context_history(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id,
            limit=2
        )
        
        assert len(limited_history) == 2
    
    @pytest.mark.asyncio
    async def test_get_context_history_no_memory(self, memory_manager):
        """Test getting context history when no memory exists"""
        history = await memory_manager.get_context_history(
            "nonexistent_agent",
            "nonexistent_story"
        )
        
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_memory_summary_exists(self, memory_manager, mock_agent_memory):
        """Test getting memory summary for existing memory"""
        # Setup mock memory with various counts
        mock_agent_memory.decisions = [Mock(), Mock()]
        mock_agent_memory.learned_patterns = [Mock()]
        mock_agent_memory.phase_handoffs = []
        mock_agent_memory.context_history = [Mock(), Mock(), Mock()]
        mock_agent_memory.artifacts = {"test_artifact": "data"}
        mock_agent_memory.metadata = {"version": 1, "type": "test"}
        
        await memory_manager.store_memory(mock_agent_memory)
        
        summary = await memory_manager.get_memory_summary(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id
        )
        
        assert summary["exists"] is True
        assert summary["agent_type"] == mock_agent_memory.agent_type
        assert summary["story_id"] == mock_agent_memory.story_id
        assert summary["decisions_count"] == 2
        assert summary["patterns_count"] == 1
        assert summary["handoffs_count"] == 0
        assert summary["context_snapshots_count"] == 3
        assert summary["artifacts_count"] == 1
        assert "version" in summary["metadata_keys"]
        assert "type" in summary["metadata_keys"]
        assert "recent_activity" in summary
    
    @pytest.mark.asyncio
    async def test_get_memory_summary_not_exists(self, memory_manager):
        """Test getting memory summary for non-existent memory"""
        summary = await memory_manager.get_memory_summary(
            "nonexistent_agent",
            "nonexistent_story"
        )
        
        assert summary["exists"] is False
        assert summary["agent_type"] == "nonexistent_agent"
        assert summary["story_id"] == "nonexistent_story"
    
    @pytest.mark.asyncio
    async def test_analyze_agent_patterns(self, memory_manager, mock_agent_memory):
        """Test analyzing agent patterns"""
        # Create mock patterns with different types and success rates
        pattern1 = Mock()
        pattern1.pattern_type = "type_a"
        pattern1.success_rate = 0.9
        pattern1.usage_count = 10
        
        pattern2 = Mock()
        pattern2.pattern_type = "type_a"
        pattern2.success_rate = 0.8
        pattern2.usage_count = 5
        
        pattern3 = Mock()
        pattern3.pattern_type = "type_b"
        pattern3.success_rate = 0.95
        pattern3.usage_count = 3
        
        mock_agent_memory.learned_patterns = [pattern1, pattern2, pattern3]
        
        # Create mock decisions
        decision1 = Mock()
        decision1.confidence = 0.85
        decision2 = Mock()
        decision2.confidence = 0.75
        
        mock_agent_memory.decisions = [decision1, decision2]
        
        # Create mock handoffs
        handoff1 = Mock()
        handoff1.from_phase = TDDState.RED
        handoff1.to_phase = TDDState.GREEN
        
        mock_agent_memory.phase_handoffs = [handoff1]
        
        await memory_manager.store_memory(mock_agent_memory)
        
        analysis = await memory_manager.analyze_agent_patterns(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id
        )
        
        assert "pattern_types" in analysis
        assert "decision_confidence_avg" in analysis
        assert "successful_patterns" in analysis
        assert "phase_transitions" in analysis
        
        # Check pattern type analysis
        assert "type_a" in analysis["pattern_types"]
        assert analysis["pattern_types"]["type_a"]["count"] == 2
        assert analysis["pattern_types"]["type_a"]["avg_success_rate"] == 0.85  # (0.9 + 0.8) / 2
        
        # Check decision confidence
        assert analysis["decision_confidence_avg"] == 0.8  # (0.85 + 0.75) / 2
        
        # Check successful patterns (success_rate > 0.8 and usage_count > 2)
        successful = analysis["successful_patterns"]
        assert len(successful) == 2  # pattern1 and pattern3 meet criteria
    
    @pytest.mark.asyncio
    async def test_analyze_agent_patterns_no_memory(self, memory_manager):
        """Test analyzing patterns when no memory exists"""
        analysis = await memory_manager.analyze_agent_patterns(
            "nonexistent_agent",
            "nonexistent_story"
        )
        
        assert analysis["analysis"] == "No memory available"
    
    @pytest.mark.asyncio
    async def test_cleanup_old_memories(self, memory_manager, temp_dir):
        """Test cleaning up old memory files"""
        # Create old and new memory files
        agent_dir = memory_manager.memory_dir / "test_agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        old_file = agent_dir / "old_story.json"
        new_file = agent_dir / "new_story.json"
        
        # Create files with different modification times
        old_file.write_text('{"test": "old"}')
        new_file.write_text('{"test": "new"}')
        
        # Manually set old file's modification time
        old_time = (datetime.utcnow() - timedelta(days=100)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        # Clean up files older than 30 days
        deleted_count = await memory_manager.cleanup_old_memories(older_than_days=30)
        
        assert deleted_count == 1
        assert not old_file.exists()
        assert new_file.exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_memories_error_handling(self, memory_manager):
        """Test cleanup error handling"""
        # Mock file operations to raise exception
        with patch('pathlib.Path.stat', side_effect=OSError("Permission denied")):
            # Should not raise exception
            deleted_count = await memory_manager.cleanup_old_memories()
            assert deleted_count == 0
    
    def test_get_performance_metrics(self, memory_manager):
        """Test getting performance metrics"""
        # Set some values to test
        memory_manager._get_calls = 10
        memory_manager._store_calls = 5
        memory_manager._cache_hits = 8
        memory_manager._cache_misses = 2
        
        metrics = memory_manager.get_performance_metrics()
        
        assert metrics["get_calls"] == 10
        assert metrics["store_calls"] == 5
        assert metrics["cache_hits"] == 8
        assert metrics["cache_misses"] == 2
        assert metrics["cache_hit_rate"] == 0.8  # 8 / (8 + 2)
        assert metrics["cached_memories"] == 0
        assert "storage_path" in metrics
    
    def test_get_performance_metrics_zero_division(self, memory_manager):
        """Test performance metrics with zero cache operations"""
        metrics = memory_manager.get_performance_metrics()
        
        assert metrics["cache_hit_rate"] == 0.0
    
    def test_get_memory_file_path(self, memory_manager):
        """Test memory file path generation"""
        # Normal case
        path = memory_manager._get_memory_file_path("test_agent", "story-123")
        expected = memory_manager.memory_dir / "test_agent" / "story-123.json"
        assert path == expected
        
        # Empty story ID
        path = memory_manager._get_memory_file_path("test_agent", "")
        expected = memory_manager.memory_dir / "test_agent" / "default.json"
        assert path == expected
        
        # None story ID
        path = memory_manager._get_memory_file_path("test_agent", None)
        expected = memory_manager.memory_dir / "test_agent" / "default.json"
        assert path == expected
        
        # Story ID with special characters
        path = memory_manager._get_memory_file_path("test_agent", "story/with\\special:chars")
        expected = memory_manager.memory_dir / "test_agent" / "storywithspecialchars.json"
        assert path == expected
        
        # Story ID with only special characters
        path = memory_manager._get_memory_file_path("test_agent", "!@#$%^&*()")
        expected = memory_manager.memory_dir / "test_agent" / "default.json"
        assert path == expected
    
    def test_get_recent_activity_summary(self, memory_manager, mock_agent_memory):
        """Test recent activity summary generation"""
        # Create mock items with different timestamps
        now = datetime.utcnow()
        last_week = now - timedelta(days=7)
        old_date = now - timedelta(days=10)
        
        # Recent items (within last week)
        recent_decision = Mock()
        recent_decision.timestamp = now - timedelta(days=3)
        
        recent_pattern = Mock()
        recent_pattern.timestamp = now - timedelta(days=2)
        
        recent_handoff = Mock()
        recent_handoff.timestamp = now - timedelta(days=1)
        
        recent_snapshot = Mock()
        recent_snapshot.timestamp = now
        
        # Old items (older than last week)
        old_decision = Mock()
        old_decision.timestamp = old_date
        
        old_pattern = Mock()
        old_pattern.timestamp = old_date
        
        # Setup mock memory
        mock_agent_memory.decisions = [recent_decision, old_decision]
        mock_agent_memory.learned_patterns = [recent_pattern, old_pattern]
        mock_agent_memory.phase_handoffs = [recent_handoff]
        mock_agent_memory.context_history = [recent_snapshot]
        mock_agent_memory.updated_at = now
        
        summary = memory_manager._get_recent_activity_summary(mock_agent_memory)
        
        assert summary["recent_decisions"] == 1
        assert summary["recent_patterns"] == 1
        assert summary["recent_handoffs"] == 1
        assert summary["recent_snapshots"] == 1
        assert summary["last_activity"] == now.isoformat()
    
    def test_get_recent_activity_summary_no_updated_at(self, memory_manager, mock_agent_memory):
        """Test recent activity summary with no updated_at"""
        mock_agent_memory.decisions = []
        mock_agent_memory.learned_patterns = []
        mock_agent_memory.phase_handoffs = []
        mock_agent_memory.context_history = []
        mock_agent_memory.updated_at = None
        
        summary = memory_manager._get_recent_activity_summary(mock_agent_memory)
        
        assert summary["last_activity"] is None
    
    @pytest.mark.asyncio
    async def test_file_operations_error_handling(self, memory_manager):
        """Test error handling in file operations"""
        
        # Test store_memory with file write error
        mock_memory = Mock(spec=AgentMemory)
        mock_memory.agent_type = "test_agent"
        mock_memory.story_id = "test_story"
        mock_memory.updated_at = datetime.utcnow()
        mock_memory.to_dict.side_effect = Exception("Serialization error")
        
        with pytest.raises(Exception):
            await memory_manager.store_memory(mock_memory)
        
        # Test get_memory with file read error
        # Create a file with invalid JSON
        memory_file = memory_manager._get_memory_file_path("error_agent", "error_story")
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        memory_file.write_text("invalid json {")
        
        result = await memory_manager.get_memory("error_agent", "error_story")
        assert result is None  # Should return None on error
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, memory_manager):
        """Test concurrent memory operations"""
        
        async def store_memory_task(agent_id, story_id):
            memory = Mock(spec=AgentMemory)
            memory.agent_type = f"agent_{agent_id}"
            memory.story_id = f"story_{story_id}"
            memory.updated_at = datetime.utcnow()
            memory.to_dict.return_value = {
                "agent_type": memory.agent_type,
                "story_id": memory.story_id
            }
            await memory_manager.store_memory(memory)
        
        async def get_memory_task(agent_id, story_id):
            return await memory_manager.get_memory(f"agent_{agent_id}", f"story_{story_id}")
        
        # Run concurrent store operations
        store_tasks = [store_memory_task(i, j) for i in range(3) for j in range(2)]
        await asyncio.gather(*store_tasks)
        
        # Run concurrent get operations
        get_tasks = [get_memory_task(i, j) for i in range(3) for j in range(2)]
        results = await asyncio.gather(*get_tasks)
        
        # All gets should succeed
        assert all(result is not None for result in results)
        assert memory_manager._store_calls == 6  # 3 agents x 2 stories
        assert memory_manager._get_calls == 6
    
    @pytest.mark.asyncio
    async def test_memory_with_existing_agent_memory_functions(self, memory_manager, mock_agent_memory):
        """Test interaction with existing AgentMemory methods"""
        # This tests that our FileBasedAgentMemory works with the AgentMemory model
        
        # Store memory and then retrieve and call its methods
        await memory_manager.store_memory(mock_agent_memory)
        
        retrieved = await memory_manager.get_memory(
            mock_agent_memory.agent_type,
            mock_agent_memory.story_id
        )
        
        # Test that we can call AgentMemory methods
        if retrieved:
            # These would normally be called on the AgentMemory instance
            # In our test, these are mocked, but in real usage they'd work
            assert hasattr(retrieved, 'to_dict')
            assert callable(retrieved.to_dict)


class TestFileBasedAgentMemoryIntegration:
    """Integration tests for FileBasedAgentMemory"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, temp_dir):
        """Test complete workflow integration"""
        memory_manager = FileBasedAgentMemory(base_path=temp_dir)
        
        agent_type = "integration_agent"
        story_id = "integration_story"
        
        # Test that we start with no memory
        initial_memory = await memory_manager.get_memory(agent_type, story_id)
        assert initial_memory is None
        
        # Create mock AgentMemory with proper structure
        with patch('agent_memory.AgentMemory') as mock_memory_class:
            memory = Mock(spec=AgentMemory)
            memory.agent_type = agent_type
            memory.story_id = story_id
            memory.created_at = datetime.utcnow()
            memory.updated_at = datetime.utcnow()
            memory.decisions = []
            memory.learned_patterns = []
            memory.phase_handoffs = []
            memory.context_history = []
            memory.artifacts = {}
            memory.metadata = {"version": 1}
            memory.add_decision = Mock()
            memory.add_pattern = Mock()
            memory.to_dict.return_value = {
                "agent_type": agent_type,
                "story_id": story_id,
                "metadata": {"version": 1}
            }
            mock_memory_class.return_value = memory
            
            # Add decision
            decision = Mock(spec=Decision)
            decision.id = "dec-1"
            await memory_manager.add_decision(agent_type, story_id, decision)
            
            # Add pattern
            pattern = Mock(spec=Pattern)
            pattern.id = "pat-1"
            await memory_manager.add_pattern(agent_type, story_id, pattern)
            
            # Verify operations were called
            memory.add_decision.assert_called_once_with(decision)
            memory.add_pattern.assert_called_once_with(pattern)
            
            # Get memory summary
            summary = await memory_manager.get_memory_summary(agent_type, story_id)
            assert summary["exists"] is True
            
            # Get performance metrics
            metrics = memory_manager.get_performance_metrics()
            assert metrics["store_calls"] == 2  # One for decision, one for pattern
            
            # Cleanup
            await memory_manager.clear_memory(agent_type, story_id)
    
    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, temp_dir):
        """Test that data persists across different memory manager instances"""
        
        # Create first instance and store data
        memory_manager1 = FileBasedAgentMemory(base_path=temp_dir)
        
        mock_memory = Mock(spec=AgentMemory)
        mock_memory.agent_type = "persistent_agent"
        mock_memory.story_id = "persistent_story"
        mock_memory.updated_at = datetime.utcnow()
        mock_memory.to_dict.return_value = {
            "agent_type": "persistent_agent",
            "story_id": "persistent_story",
            "data": "test_data"
        }
        
        await memory_manager1.store_memory(mock_memory)
        
        # Create second instance and retrieve data
        memory_manager2 = FileBasedAgentMemory(base_path=temp_dir)
        
        # Mock AgentMemory.from_dict to return our expected memory
        with patch('agent_memory.AgentMemory.from_dict') as mock_from_dict:
            mock_from_dict.return_value = mock_memory
            
            retrieved = await memory_manager2.get_memory("persistent_agent", "persistent_story")
            
            assert retrieved is not None
            mock_from_dict.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])