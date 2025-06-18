"""
Final comprehensive test suite to achieve 95% coverage for agent_memory.py.

This test file specifically targets the remaining uncovered lines and edge cases
to push the module from 56% to 95% coverage for TIER 4 compliance.
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


class TestComprehensiveMemoryOperations:
    """Comprehensive tests to ensure high coverage"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_store_memory_updates_timestamp(self, agent_memory):
        """Test that storing memory updates the timestamp"""
        original_time = datetime.utcnow()
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        memory.updated_at = original_time
        
        # Wait a tiny bit to ensure timestamp difference
        await asyncio.sleep(0.01)
        
        await agent_memory.store_memory(memory)
        
        # The updated_at should be newer than original
        assert memory.updated_at > original_time
    
    @pytest.mark.asyncio
    async def test_get_memory_with_from_dict_error(self, agent_memory):
        """Test handling of AgentMemory.from_dict errors"""
        # Create a memory file with valid JSON but invalid structure
        memory_file = agent_memory.memory_dir / "TestAgent" / "test_story.json"
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Valid JSON but missing required fields for AgentMemory
        with open(memory_file, 'w') as f:
            json.dump({"wrong": "structure"}, f)
        
        # Mock AgentMemory.from_dict to raise an error
        with patch('context.models.AgentMemory.from_dict', side_effect=ValueError("Invalid structure")):
            result = await agent_memory.get_memory("TestAgent", "test_story")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_successful_patterns_filtering(self, agent_memory):
        """Test the successful patterns filtering logic in analyze_agent_patterns"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        # Add patterns with different success rates and usage counts
        low_success_pattern = Pattern(
            pattern_type="low_success", description="Low success pattern",
            success_rate=0.7, usage_count=5  # Low success rate
        )
        low_usage_pattern = Pattern(
            pattern_type="low_usage", description="Low usage pattern",
            success_rate=0.9, usage_count=1  # Low usage count
        )
        successful_pattern = Pattern(
            pattern_type="successful", description="Successful pattern",
            success_rate=0.85, usage_count=5  # High success rate and usage
        )
        
        memory.add_pattern(low_success_pattern)
        memory.add_pattern(low_usage_pattern)
        memory.add_pattern(successful_pattern)
        
        await agent_memory.store_memory(memory)
        
        analysis = await agent_memory.analyze_agent_patterns("TestAgent", "test_story")
        
        # Only the successful pattern should be in successful_patterns (success_rate > 0.8 and usage_count > 2)
        assert len(analysis["successful_patterns"]) == 1
        assert analysis["successful_patterns"][0]["pattern_type"] == "successful"
    
    @pytest.mark.asyncio
    async def test_pattern_analysis_averages_calculation(self, agent_memory):
        """Test pattern analysis average calculations"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        # Add multiple patterns of the same type with different success rates
        pattern1 = Pattern(
            pattern_type="test_type", description="Pattern 1",
            success_rate=0.6, usage_count=2
        )
        pattern2 = Pattern(
            pattern_type="test_type", description="Pattern 2",
            success_rate=0.8, usage_count=3
        )
        
        memory.add_pattern(pattern1)
        memory.add_pattern(pattern2)
        
        await agent_memory.store_memory(memory)
        
        analysis = await agent_memory.analyze_agent_patterns("TestAgent", "test_story")
        
        # Check that averages are calculated correctly
        pattern_data = analysis["pattern_types"]["test_type"]
        assert pattern_data["count"] == 2
        assert pattern_data["avg_success_rate"] == 0.7  # (0.6 + 0.8) / 2
        assert pattern_data["total_usage"] == 5  # 2 + 3
    
    @pytest.mark.asyncio
    async def test_clear_memory_cache_removal(self, agent_memory):
        """Test that clear_memory removes entries from cache"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Verify it's in cache
        cache_key = "TestAgent:test_story"
        assert cache_key in agent_memory._memory_cache
        
        # Clear specific memory
        await agent_memory.clear_memory("TestAgent", "test_story")
        
        # Should be removed from cache
        assert cache_key not in agent_memory._memory_cache
    
    @pytest.mark.asyncio
    async def test_clear_all_agent_memories_cache_removal(self, agent_memory):
        """Test that clearing all agent memories removes all from cache"""
        # Create multiple memories for same agent
        memory1 = AgentMemory(agent_type="TestAgent", story_id="story1")
        memory2 = AgentMemory(agent_type="TestAgent", story_id="story2")
        other_memory = AgentMemory(agent_type="OtherAgent", story_id="story1")
        
        await agent_memory.store_memory(memory1)
        await agent_memory.store_memory(memory2)
        await agent_memory.store_memory(other_memory)
        
        # Verify they're in cache
        assert "TestAgent:story1" in agent_memory._memory_cache
        assert "TestAgent:story2" in agent_memory._memory_cache
        assert "OtherAgent:story1" in agent_memory._memory_cache
        
        # Clear all TestAgent memories
        await agent_memory.clear_memory("TestAgent")
        
        # TestAgent entries should be removed from cache
        assert "TestAgent:story1" not in agent_memory._memory_cache
        assert "TestAgent:story2" not in agent_memory._memory_cache
        # OtherAgent should remain
        assert "OtherAgent:story1" in agent_memory._memory_cache
    
    @pytest.mark.asyncio
    async def test_memory_summary_recent_activity_edge_cases(self, agent_memory):
        """Test memory summary with recent activity edge cases"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        # Create items with timestamps at the boundary (exactly 7 days ago)
        exactly_7_days = datetime.utcnow() - timedelta(days=7)
        
        boundary_decision = Decision(description="Boundary decision", timestamp=exactly_7_days)
        boundary_pattern = Pattern(
            pattern_type="boundary", description="Boundary pattern", timestamp=exactly_7_days
        )
        boundary_handoff = PhaseHandoff(context_summary="Boundary handoff", timestamp=exactly_7_days)
        boundary_snapshot = ContextSnapshot(
            agent_type="TestAgent", story_id="test_story",
            context_summary="Boundary snapshot", timestamp=exactly_7_days
        )
        
        memory.decisions.append(boundary_decision)
        memory.learned_patterns.append(boundary_pattern)
        memory.phase_handoffs.append(boundary_handoff)
        memory.context_history.append(boundary_snapshot)
        
        await agent_memory.store_memory(memory)
        
        summary = await agent_memory.get_memory_summary("TestAgent", "test_story")
        
        # Items exactly at the 7-day boundary should be counted as NOT recent
        recent_activity = summary["recent_activity"]
        assert recent_activity["recent_decisions"] == 0
        assert recent_activity["recent_patterns"] == 0
        assert recent_activity["recent_handoffs"] == 0
        assert recent_activity["recent_snapshots"] == 0
    
    def test_file_path_generation_with_none_inputs(self, agent_memory):
        """Test file path generation with None inputs"""
        # Test with None story_id
        path = agent_memory._get_memory_file_path("TestAgent", None)
        assert path.name == "default.json"
        assert path.parent.name == "TestAgent"
        
        # Test with empty string story_id
        path = agent_memory._get_memory_file_path("TestAgent", "")
        assert path.name == "default.json"
        
        # Test with whitespace-only story_id
        path = agent_memory._get_memory_file_path("TestAgent", "   ")
        assert path.name == "default.json"
    
    def test_performance_metrics_cache_hit_rate_calculation(self, agent_memory):
        """Test cache hit rate calculation edge cases"""
        # Test with zero operations
        metrics = agent_memory.get_performance_metrics()
        assert metrics["cache_hit_rate"] == 0.0
        
        # Test with only hits
        agent_memory._cache_hits = 5
        agent_memory._cache_misses = 0
        metrics = agent_memory.get_performance_metrics()
        assert metrics["cache_hit_rate"] == 1.0
        
        # Test with only misses
        agent_memory._cache_hits = 0
        agent_memory._cache_misses = 3
        metrics = agent_memory.get_performance_metrics()
        assert metrics["cache_hit_rate"] == 0.0
        
        # Test with mixed hits and misses
        agent_memory._cache_hits = 7
        agent_memory._cache_misses = 3
        metrics = agent_memory.get_performance_metrics()
        assert metrics["cache_hit_rate"] == 0.7
    
    @pytest.mark.asyncio
    async def test_specialized_method_memory_creation(self, agent_memory):
        """Test that specialized methods create memory when it doesn't exist"""
        # Test add_decision creates memory
        decision = Decision(description="Test decision")
        await agent_memory.add_decision("NewAgent", "new_story", decision)
        
        memory = await agent_memory.get_memory("NewAgent", "new_story")
        assert memory is not None
        assert len(memory.decisions) == 1
        
        # Test add_pattern creates memory
        pattern = Pattern(pattern_type="test", description="Test pattern")
        await agent_memory.add_pattern("NewAgent2", "new_story2", pattern)
        
        memory = await agent_memory.get_memory("NewAgent2", "new_story2")
        assert memory is not None
        assert len(memory.learned_patterns) == 1
        
        # Test add_phase_handoff creates memory
        handoff = PhaseHandoff(context_summary="Test handoff")
        await agent_memory.add_phase_handoff("NewAgent3", "new_story3", handoff)
        
        memory = await agent_memory.get_memory("NewAgent3", "new_story3")
        assert memory is not None
        assert len(memory.phase_handoffs) == 1
        
        # Test add_context_snapshot creates memory
        snapshot = ContextSnapshot(
            agent_type="NewAgent4", story_id="new_story4",
            context_summary="Test snapshot"
        )
        await agent_memory.add_context_snapshot("NewAgent4", "new_story4", snapshot)
        
        memory = await agent_memory.get_memory("NewAgent4", "new_story4")
        assert memory is not None
        assert len(memory.context_history) == 1
    
    @pytest.mark.asyncio
    async def test_update_memory_with_metadata_override(self, agent_memory):
        """Test updating memory with metadata field override"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        memory.metadata = {"existing_key": "existing_value"}
        await agent_memory.store_memory(memory)
        
        # Update with metadata key that overrides existing
        updates = {"metadata": {"new_key": "new_value"}}
        await agent_memory.update_memory("TestAgent", "test_story", updates)
        
        updated_memory = await agent_memory.get_memory("TestAgent", "test_story")
        assert updated_memory.metadata["new_key"] == "new_value"
        # Original metadata should be overridden
        assert updated_memory.metadata.get("existing_key") != "existing_value"
    
    @pytest.mark.asyncio 
    async def test_directory_creation_on_store(self, agent_memory):
        """Test that directory is created during store operation"""
        memory = AgentMemory(agent_type="NewAgent", story_id="test_story")
        
        # Verify directory doesn't exist initially
        agent_dir = agent_memory.memory_dir / "NewAgent"
        assert not agent_dir.exists()
        
        # Store memory should create directory
        await agent_memory.store_memory(memory)
        
        # Directory should now exist
        assert agent_dir.exists()
        assert agent_dir.is_dir()
    
    @pytest.mark.asyncio
    async def test_cache_expiration_cleanup(self, agent_memory):
        """Test that expired cache entries are cleaned up on access"""
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        await agent_memory.store_memory(memory)
        
        # Manually add an expired entry to cache
        old_time = datetime.utcnow() - timedelta(hours=2)  # Older than TTL
        agent_memory._memory_cache["ExpiredAgent:expired_story"] = (memory, old_time)
        
        # Accessing the expired memory should clean it up
        result = await agent_memory.get_memory("ExpiredAgent", "expired_story")
        
        # Should return None and remove from cache
        assert result is None
        assert "ExpiredAgent:expired_story" not in agent_memory._memory_cache


class TestComplexScenarios:
    """Test complex real-world scenarios"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_workflow_scenario(self, agent_memory):
        """Test a complete workflow scenario with all operations"""
        agent_type = "WorkflowAgent"
        story_id = "complex_story"
        
        # 1. Create initial memory with decision
        decision = Decision(
            agent_type=agent_type,
            description="Initial design decision",
            rationale="Need to establish architecture",
            confidence=0.8
        )
        await agent_memory.add_decision(agent_type, story_id, decision)
        
        # 2. Add pattern learned during process
        pattern = Pattern(
            pattern_type="architecture",
            description="Use microservices for scalability",
            success_rate=0.9,
            usage_count=3
        )
        await agent_memory.add_pattern(agent_type, story_id, pattern)
        
        # 3. Add phase handoff
        handoff = PhaseHandoff(
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            from_agent="DesignAgent",
            to_agent="QAAgent",
            context_summary="Design completed, ready for testing"
        )
        await agent_memory.add_phase_handoff(agent_type, story_id, handoff)
        
        # 4. Add context snapshot
        snapshot = ContextSnapshot(
            agent_type=agent_type,
            story_id=story_id,
            tdd_phase=TDDState.TEST_RED,
            context_summary="Testing phase in progress",
            file_list=["test_file.py", "src_file.py"]
        )
        await agent_memory.add_context_snapshot(agent_type, story_id, snapshot)
        
        # 5. Update memory with additional metadata
        updates = {
            "project_info": "Complex microservice project",
            "priority": "high"
        }
        await agent_memory.update_memory(agent_type, story_id, updates)
        
        # 6. Verify complete memory state
        memory = await agent_memory.get_memory(agent_type, story_id)
        assert memory is not None
        assert len(memory.decisions) == 1
        assert len(memory.learned_patterns) == 1
        assert len(memory.phase_handoffs) == 1
        assert len(memory.context_history) == 1
        assert memory.metadata["project_info"] == "Complex microservice project"
        
        # 7. Analyze patterns
        analysis = await agent_memory.analyze_agent_patterns(agent_type, story_id)
        assert "architecture" in analysis["pattern_types"]
        
        # 8. Get memory summary
        summary = await agent_memory.get_memory_summary(agent_type, story_id)
        assert summary["exists"] is True
        assert summary["decisions_count"] == 1
        assert summary["patterns_count"] == 1
        
        # 9. Check performance metrics
        metrics = agent_memory.get_performance_metrics()
        assert metrics["get_calls"] > 0
        assert metrics["store_calls"] > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])