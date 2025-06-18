"""
Comprehensive test suite for AgentMemory persistence functionality.

Tests the persistent storage of agent decisions and artifacts with context handoffs
between TDD phases, including memory retrieval based on relevance and recency.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
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


class TestFileBasedAgentMemoryInit:
    """Test FileBasedAgentMemory initialization"""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = FileBasedAgentMemory(base_path=temp_dir)
            
            assert memory.base_path == Path(temp_dir)
            assert memory.memory_dir == Path(temp_dir) / "agent_memory"
            assert memory.memory_dir.exists()
            assert len(memory._memory_cache) == 0
            assert memory._cache_ttl.total_seconds() == 1800  # 30 minutes
    
    def test_init_creates_directories(self):
        """Test that initialization creates required directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "test_memory"
            memory = FileBasedAgentMemory(base_path=str(base_path))
            
            expected_dir = base_path / "agent_memory"
            assert expected_dir.exists()
            assert expected_dir.is_dir()


class TestMemoryBasicOperations:
    """Test basic memory operations (get, store, update, clear)"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.fixture
    def sample_memory(self):
        """Create a sample agent memory"""
        return AgentMemory(
            agent_type="DesignAgent",
            story_id="story_1"
        )
    
    @pytest.mark.asyncio
    async def test_get_memory_nonexistent(self, agent_memory):
        """Test getting non-existent memory"""
        result = await agent_memory.get_memory("DesignAgent", "nonexistent_story")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_store_and_get_memory(self, agent_memory, sample_memory):
        """Test storing and retrieving memory"""
        # Store memory
        await agent_memory.store_memory(sample_memory)
        
        # Retrieve memory
        retrieved = await agent_memory.get_memory("DesignAgent", "story_1")
        
        assert retrieved is not None
        assert retrieved.agent_type == "DesignAgent"
        assert retrieved.story_id == "story_1"
        assert retrieved.created_at == sample_memory.created_at
        assert retrieved.updated_at >= sample_memory.updated_at
    
    @pytest.mark.asyncio
    async def test_memory_file_creation(self, agent_memory, sample_memory):
        """Test that memory files are created correctly"""
        await agent_memory.store_memory(sample_memory)
        
        expected_file = agent_memory.memory_dir / "DesignAgent" / "story_1.json"
        assert expected_file.exists()
        
        # Verify file content
        with open(expected_file, 'r') as f:
            data = json.load(f)
        
        assert data["agent_type"] == "DesignAgent"
        assert data["story_id"] == "story_1"
    
    @pytest.mark.asyncio
    async def test_memory_caching(self, agent_memory, sample_memory):
        """Test memory caching functionality"""
        # Store memory (this adds to cache)
        await agent_memory.store_memory(sample_memory)
        
        # Clear cache to test actual cache miss
        agent_memory._memory_cache.clear()
        
        # First get should miss cache (loads from file)
        retrieved1 = await agent_memory.get_memory("DesignAgent", "story_1")
        assert agent_memory._cache_misses == 1
        
        # Second get should hit cache
        retrieved2 = await agent_memory.get_memory("DesignAgent", "story_1")
        assert agent_memory._cache_hits == 1
        
        # Both should be equal (content-wise)
        assert retrieved1 == retrieved2
    
    @pytest.mark.asyncio
    async def test_memory_cache_expiration(self, agent_memory, sample_memory):
        """Test memory cache expiration"""
        # Set very short TTL
        agent_memory._cache_ttl = timedelta(milliseconds=1)
        
        await agent_memory.store_memory(sample_memory)
        
        # First get
        await agent_memory.get_memory("DesignAgent", "story_1")
        
        # Wait for cache to expire
        await asyncio.sleep(0.01)
        
        # Second get should miss cache due to expiration
        initial_misses = agent_memory._cache_misses
        await agent_memory.get_memory("DesignAgent", "story_1")
        assert agent_memory._cache_misses > initial_misses
    
    @pytest.mark.asyncio
    async def test_update_memory_existing(self, agent_memory, sample_memory):
        """Test updating existing memory"""
        # Store initial memory
        await agent_memory.store_memory(sample_memory)
        
        # Update memory
        updates = {
            "metadata": {"test_key": "test_value"},
            "new_field": "new_value"
        }
        await agent_memory.update_memory("DesignAgent", "story_1", updates)
        
        # Retrieve and verify updates
        retrieved = await agent_memory.get_memory("DesignAgent", "story_1")
        assert retrieved.metadata["test_key"] == "test_value"
        assert retrieved.metadata["new_field"] == "new_value"
    
    @pytest.mark.asyncio
    async def test_update_memory_nonexistent(self, agent_memory):
        """Test updating non-existent memory creates new memory"""
        updates = {"metadata": {"key": "value"}}
        await agent_memory.update_memory("NewAgent", "new_story", updates)
        
        # Should create new memory
        retrieved = await agent_memory.get_memory("NewAgent", "new_story")
        assert retrieved is not None
        assert retrieved.agent_type == "NewAgent"
        assert retrieved.story_id == "new_story"
        assert retrieved.metadata["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_clear_memory_specific_story(self, agent_memory, sample_memory):
        """Test clearing memory for specific story"""
        await agent_memory.store_memory(sample_memory)
        
        # Store another memory for the same agent but different story
        other_memory = AgentMemory(agent_type="DesignAgent", story_id="story_2")
        await agent_memory.store_memory(other_memory)
        
        # Clear specific story
        await agent_memory.clear_memory("DesignAgent", "story_1")
        
        # First memory should be gone
        retrieved1 = await agent_memory.get_memory("DesignAgent", "story_1")
        assert retrieved1 is None
        
        # Second memory should still exist
        retrieved2 = await agent_memory.get_memory("DesignAgent", "story_2")
        assert retrieved2 is not None
    
    @pytest.mark.asyncio
    async def test_clear_memory_all_agent_stories(self, agent_memory, sample_memory):
        """Test clearing all memories for an agent"""
        await agent_memory.store_memory(sample_memory)
        
        # Store another memory for same agent
        other_memory = AgentMemory(agent_type="DesignAgent", story_id="story_2")
        await agent_memory.store_memory(other_memory)
        
        # Store memory for different agent
        different_agent_memory = AgentMemory(agent_type="CodeAgent", story_id="story_1")
        await agent_memory.store_memory(different_agent_memory)
        
        # Clear all memories for DesignAgent
        await agent_memory.clear_memory("DesignAgent")
        
        # DesignAgent memories should be gone
        assert await agent_memory.get_memory("DesignAgent", "story_1") is None
        assert await agent_memory.get_memory("DesignAgent", "story_2") is None
        
        # CodeAgent memory should still exist
        assert await agent_memory.get_memory("CodeAgent", "story_1") is not None


class TestDecisionManagement:
    """Test decision recording and retrieval"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.fixture
    def sample_decision(self):
        """Create a sample decision"""
        return Decision(
            agent_type="DesignAgent",
            description="Test decision",
            rationale="Test rationale",
            outcome="Test outcome",
            confidence=0.8,
            artifacts={"file1.py": "content"}
        )
    
    @pytest.mark.asyncio
    async def test_add_decision(self, agent_memory, sample_decision):
        """Test adding decisions to memory"""
        await agent_memory.add_decision("DesignAgent", "story_1", sample_decision)
        
        # Retrieve and verify
        decisions = await agent_memory.get_recent_decisions("DesignAgent", "story_1")
        assert len(decisions) == 1
        assert decisions[0].id == sample_decision.id
        assert decisions[0].description == "Test decision"
        assert decisions[0].confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_add_multiple_decisions(self, agent_memory):
        """Test adding multiple decisions"""
        decisions_data = [
            ("Decision 1", 0.7),
            ("Decision 2", 0.8),
            ("Decision 3", 0.9)
        ]
        
        for desc, conf in decisions_data:
            decision = Decision(
                agent_type="DesignAgent",
                description=desc,
                confidence=conf
            )
            await agent_memory.add_decision("DesignAgent", "story_1", decision)
        
        # Retrieve and verify order (most recent first)
        decisions = await agent_memory.get_recent_decisions("DesignAgent", "story_1")
        assert len(decisions) == 3
        assert decisions[0].description == "Decision 3"  # Most recent first
        assert decisions[1].description == "Decision 2"
        assert decisions[2].description == "Decision 1"
    
    @pytest.mark.asyncio
    async def test_get_recent_decisions_limit(self, agent_memory):
        """Test limiting recent decisions"""
        # Add 15 decisions
        for i in range(15):
            decision = Decision(
                agent_type="DesignAgent",
                description=f"Decision {i}",
                confidence=0.5
            )
            await agent_memory.add_decision("DesignAgent", "story_1", decision)
        
        # Get with limit
        decisions = await agent_memory.get_recent_decisions("DesignAgent", "story_1", limit=5)
        assert len(decisions) == 5
        
        # Should be most recent ones
        assert decisions[0].description == "Decision 14"
        assert decisions[4].description == "Decision 10"
    
    @pytest.mark.asyncio
    async def test_get_recent_decisions_nonexistent_memory(self, agent_memory):
        """Test getting decisions from non-existent memory"""
        decisions = await agent_memory.get_recent_decisions("NonExistentAgent", "story_1")
        assert decisions == []


class TestPatternManagement:
    """Test pattern recording and retrieval"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.fixture
    def sample_pattern(self):
        """Create a sample pattern"""
        return Pattern(
            pattern_type="design_approach",
            description="Use modular design for complex features",
            context_conditions=["high complexity", "multiple components"],
            success_rate=0.85,
            usage_count=5,
            examples=["feature A", "feature B"]
        )
    
    @pytest.mark.asyncio
    async def test_add_pattern(self, agent_memory, sample_pattern):
        """Test adding patterns to memory"""
        await agent_memory.add_pattern("DesignAgent", "story_1", sample_pattern)
        
        # Retrieve and verify
        patterns = await agent_memory.get_patterns_by_type("DesignAgent", "story_1", "design_approach")
        assert len(patterns) == 1
        assert patterns[0].id == sample_pattern.id
        assert patterns[0].description == "Use modular design for complex features"
        assert patterns[0].success_rate == 0.85
    
    @pytest.mark.asyncio
    async def test_get_patterns_by_type(self, agent_memory):
        """Test getting patterns by type"""
        # Add patterns of different types
        pattern1 = Pattern(pattern_type="design", description="Design pattern")
        pattern2 = Pattern(pattern_type="testing", description="Testing pattern")
        pattern3 = Pattern(pattern_type="design", description="Another design pattern")
        
        await agent_memory.add_pattern("DesignAgent", "story_1", pattern1)
        await agent_memory.add_pattern("DesignAgent", "story_1", pattern2)
        await agent_memory.add_pattern("DesignAgent", "story_1", pattern3)
        
        # Get design patterns only
        design_patterns = await agent_memory.get_patterns_by_type("DesignAgent", "story_1", "design")
        assert len(design_patterns) == 2
        
        # Get testing patterns only
        testing_patterns = await agent_memory.get_patterns_by_type("DesignAgent", "story_1", "testing")
        assert len(testing_patterns) == 1
    
    @pytest.mark.asyncio
    async def test_get_patterns_nonexistent_memory(self, agent_memory):
        """Test getting patterns from non-existent memory"""
        patterns = await agent_memory.get_patterns_by_type("NonExistentAgent", "story_1", "any_type")
        assert patterns == []


class TestPhaseHandoffManagement:
    """Test phase handoff recording and retrieval"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.fixture
    def sample_handoff(self):
        """Create a sample phase handoff"""
        return PhaseHandoff(
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            from_agent="DesignAgent",
            to_agent="QAAgent",
            artifacts={"design.md": "design content"},
            context_summary="Design completed",
            handoff_notes="Ready for test writing"
        )
    
    @pytest.mark.asyncio
    async def test_add_phase_handoff(self, agent_memory, sample_handoff):
        """Test adding phase handoffs to memory"""
        await agent_memory.add_phase_handoff("DesignAgent", "story_1", sample_handoff)
        
        # Retrieve and verify
        handoffs = await agent_memory.get_phase_handoffs("DesignAgent", "story_1")
        assert len(handoffs) == 1
        assert handoffs[0].id == sample_handoff.id
        assert handoffs[0].from_phase == TDDState.DESIGN
        assert handoffs[0].to_phase == TDDState.TEST_RED
        assert handoffs[0].context_summary == "Design completed"
    
    @pytest.mark.asyncio
    async def test_get_phase_handoffs_filtered(self, agent_memory):
        """Test getting filtered phase handoffs"""
        # Add handoffs for different phases
        handoff1 = PhaseHandoff(from_phase=TDDState.DESIGN, to_phase=TDDState.TEST_RED)
        handoff2 = PhaseHandoff(from_phase=TDDState.TEST_RED, to_phase=TDDState.CODE_GREEN)
        handoff3 = PhaseHandoff(from_phase=TDDState.DESIGN, to_phase=TDDState.CODE_GREEN)
        
        await agent_memory.add_phase_handoff("DesignAgent", "story_1", handoff1)
        await agent_memory.add_phase_handoff("DesignAgent", "story_1", handoff2)
        await agent_memory.add_phase_handoff("DesignAgent", "story_1", handoff3)
        
        # Filter by from_phase
        design_handoffs = await agent_memory.get_phase_handoffs(
            "DesignAgent", "story_1", from_phase=TDDState.DESIGN
        )
        assert len(design_handoffs) == 2
        
        # Filter by to_phase
        test_handoffs = await agent_memory.get_phase_handoffs(
            "DesignAgent", "story_1", to_phase=TDDState.TEST_RED
        )
        assert len(test_handoffs) == 1
        
        # Filter by both
        specific_handoffs = await agent_memory.get_phase_handoffs(
            "DesignAgent", "story_1", 
            from_phase=TDDState.DESIGN, 
            to_phase=TDDState.CODE_GREEN
        )
        assert len(specific_handoffs) == 1
    
    @pytest.mark.asyncio
    async def test_phase_handoffs_chronological_order(self, agent_memory):
        """Test that phase handoffs are returned in chronological order"""
        # Add handoffs with delays to ensure different timestamps
        handoff1 = PhaseHandoff(context_summary="First handoff")
        await agent_memory.add_phase_handoff("DesignAgent", "story_1", handoff1)
        
        await asyncio.sleep(0.01)  # Small delay
        
        handoff2 = PhaseHandoff(context_summary="Second handoff")
        await agent_memory.add_phase_handoff("DesignAgent", "story_1", handoff2)
        
        # Should be in reverse chronological order (most recent first)
        handoffs = await agent_memory.get_phase_handoffs("DesignAgent", "story_1")
        assert len(handoffs) == 2
        assert handoffs[0].context_summary == "Second handoff"
        assert handoffs[1].context_summary == "First handoff"


class TestContextSnapshotManagement:
    """Test context snapshot recording and retrieval"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.fixture
    def sample_snapshot(self):
        """Create a sample context snapshot"""
        return ContextSnapshot(
            agent_type="DesignAgent",
            story_id="story_1",
            tdd_phase=TDDState.DESIGN,
            context_summary="Design phase snapshot",
            file_list=["design.md", "requirements.txt"],
            token_usage=TokenUsage(
                context_id="test",
                total_used=1000,
                core_task_used=600,
                historical_used=400
            )
        )
    
    @pytest.mark.asyncio
    async def test_add_context_snapshot(self, agent_memory, sample_snapshot):
        """Test adding context snapshots to memory"""
        await agent_memory.add_context_snapshot("DesignAgent", "story_1", sample_snapshot)
        
        # Retrieve and verify
        history = await agent_memory.get_context_history("DesignAgent", "story_1")
        assert len(history) == 1
        assert history[0].id == sample_snapshot.id
        assert history[0].context_summary == "Design phase snapshot"
        assert history[0].tdd_phase == TDDState.DESIGN
    
    @pytest.mark.asyncio
    async def test_get_context_history_filtered(self, agent_memory):
        """Test getting filtered context history"""
        # Add snapshots for different phases
        snapshot1 = ContextSnapshot(
            agent_type="DesignAgent", story_id="story_1",
            tdd_phase=TDDState.DESIGN, context_summary="Design snapshot"
        )
        snapshot2 = ContextSnapshot(
            agent_type="DesignAgent", story_id="story_1",
            tdd_phase=TDDState.TEST_RED, context_summary="Test snapshot"
        )
        
        await agent_memory.add_context_snapshot("DesignAgent", "story_1", snapshot1)
        await agent_memory.add_context_snapshot("DesignAgent", "story_1", snapshot2)
        
        # Filter by TDD phase
        design_history = await agent_memory.get_context_history(
            "DesignAgent", "story_1", tdd_phase=TDDState.DESIGN
        )
        assert len(design_history) == 1
        assert design_history[0].context_summary == "Design snapshot"
    
    @pytest.mark.asyncio
    async def test_context_history_limit(self, agent_memory):
        """Test context history limit"""
        # Add multiple snapshots
        for i in range(25):
            snapshot = ContextSnapshot(
                agent_type="DesignAgent", story_id="story_1",
                context_summary=f"Snapshot {i}"
            )
            await agent_memory.add_context_snapshot("DesignAgent", "story_1", snapshot)
        
        # Should be limited by parameter
        history = await agent_memory.get_context_history("DesignAgent", "story_1", limit=5)
        assert len(history) == 5
        
        # Should be most recent first
        assert history[0].context_summary == "Snapshot 24"


class TestMemoryAnalysisAndInsights:
    """Test memory analysis and insight generation"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_get_memory_summary_nonexistent(self, agent_memory):
        """Test memory summary for non-existent memory"""
        summary = await agent_memory.get_memory_summary("NonExistentAgent", "story_1")
        
        assert summary["exists"] is False
        assert summary["agent_type"] == "NonExistentAgent"
        assert summary["story_id"] == "story_1"
    
    @pytest.mark.asyncio
    async def test_get_memory_summary_with_data(self, agent_memory):
        """Test memory summary with data"""
        # Create memory with various data
        memory = AgentMemory(agent_type="DesignAgent", story_id="story_1")
        memory.add_decision(Decision(description="Test decision"))
        memory.add_pattern(Pattern(pattern_type="test", description="Test pattern"))
        memory.add_context_snapshot(ContextSnapshot(
            agent_type="DesignAgent", story_id="story_1",
            context_summary="Test snapshot"
        ))
        memory.add_phase_handoff(PhaseHandoff(context_summary="Test handoff"))
        memory.artifacts["test.py"] = "test content"
        memory.metadata["test_key"] = "test_value"
        
        await agent_memory.store_memory(memory)
        
        # Get summary
        summary = await agent_memory.get_memory_summary("DesignAgent", "story_1")
        
        assert summary["exists"] is True
        assert summary["agent_type"] == "DesignAgent"
        assert summary["story_id"] == "story_1"
        assert summary["decisions_count"] == 1
        assert summary["patterns_count"] == 1
        assert summary["handoffs_count"] == 1
        assert summary["context_snapshots_count"] == 1
        assert summary["artifacts_count"] == 1
        assert "test_key" in summary["metadata_keys"]
        assert "recent_activity" in summary
    
    @pytest.mark.asyncio
    async def test_analyze_agent_patterns(self, agent_memory):
        """Test agent pattern analysis"""
        # Create memory with patterns and decisions
        memory = AgentMemory(agent_type="DesignAgent", story_id="story_1")
        
        # Add patterns
        pattern1 = Pattern(
            pattern_type="design", description="Pattern 1",
            success_rate=0.8, usage_count=5
        )
        pattern2 = Pattern(
            pattern_type="testing", description="Pattern 2",
            success_rate=0.9, usage_count=3
        )
        memory.add_pattern(pattern1)
        memory.add_pattern(pattern2)
        
        # Add decisions
        decision1 = Decision(description="Decision 1", confidence=0.7)
        decision2 = Decision(description="Decision 2", confidence=0.9)
        memory.add_decision(decision1)
        memory.add_decision(decision2)
        
        # Add handoffs
        handoff = PhaseHandoff(from_phase=TDDState.DESIGN, to_phase=TDDState.TEST_RED)
        memory.add_phase_handoff(handoff)
        
        await agent_memory.store_memory(memory)
        
        # Analyze patterns
        analysis = await agent_memory.analyze_agent_patterns("DesignAgent", "story_1")
        
        assert isinstance(analysis, dict)
        assert "pattern_types" in analysis
        assert "decision_confidence_avg" in analysis
        assert "successful_patterns" in analysis
        assert "phase_transitions" in analysis
        
        # Check pattern types analysis
        assert "design" in analysis["pattern_types"]
        assert "testing" in analysis["pattern_types"]
        
        # Check decision confidence
        assert analysis["decision_confidence_avg"] == 0.8  # (0.7 + 0.9) / 2
        
        # Check phase transitions (lowercase as implemented)
        transition_key = "design -> test_red"
        assert transition_key in analysis["phase_transitions"]
        assert analysis["phase_transitions"][transition_key] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_agent_patterns_nonexistent(self, agent_memory):
        """Test pattern analysis for non-existent memory"""
        analysis = await agent_memory.analyze_agent_patterns("NonExistentAgent", "story_1")
        
        assert analysis["analysis"] == "No memory available"


class TestMemoryCleanupAndMaintenance:
    """Test memory cleanup and maintenance functionality"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_memories(self, agent_memory):
        """Test cleanup of old memory files"""
        # Create some memory files
        memory1 = AgentMemory(agent_type="Agent1", story_id="story_1")
        memory2 = AgentMemory(agent_type="Agent2", story_id="story_2")
        
        await agent_memory.store_memory(memory1)
        await agent_memory.store_memory(memory2)
        
        # Verify files exist
        file1 = agent_memory.memory_dir / "Agent1" / "story_1.json"
        file2 = agent_memory.memory_dir / "Agent2" / "story_2.json"
        assert file1.exists()
        assert file2.exists()
        
        # Cleanup with very short retention (should delete all)
        deleted_count = await agent_memory.cleanup_old_memories(older_than_days=0)
        
        # All files should be deleted
        assert deleted_count >= 2
        assert not file1.exists()
        assert not file2.exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_preserves_recent_memories(self, agent_memory):
        """Test that cleanup preserves recent memories"""
        # Create recent memory
        memory = AgentMemory(agent_type="RecentAgent", story_id="story_1")
        await agent_memory.store_memory(memory)
        
        # Cleanup with long retention (should preserve recent files)
        deleted_count = await agent_memory.cleanup_old_memories(older_than_days=365)
        
        # No files should be deleted
        assert deleted_count == 0
        
        # Memory should still exist
        retrieved = await agent_memory.get_memory("RecentAgent", "story_1")
        assert retrieved is not None


class TestPerformanceMetrics:
    """Test performance metrics functionality"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_initial(self, agent_memory):
        """Test initial performance metrics"""
        metrics = agent_memory.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert metrics["get_calls"] == 0
        assert metrics["store_calls"] == 0
        assert metrics["cache_hits"] == 0
        assert metrics["cache_misses"] == 0
        assert metrics["cache_hit_rate"] == 0.0
        assert metrics["cached_memories"] == 0
        assert "storage_path" in metrics
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_after_operations(self, agent_memory):
        """Test performance metrics after operations"""
        memory = AgentMemory(agent_type="TestAgent", story_id="story_1")
        
        # Perform operations
        await agent_memory.store_memory(memory)
        # Clear cache to force a miss on first get
        agent_memory._memory_cache.clear()
        await agent_memory.get_memory("TestAgent", "story_1")  # Cache miss (loads from file)
        await agent_memory.get_memory("TestAgent", "story_1")  # Cache hit
        
        metrics = agent_memory.get_performance_metrics()
        
        assert metrics["get_calls"] == 2
        assert metrics["store_calls"] == 1
        assert metrics["cache_hits"] == 1
        assert metrics["cache_misses"] == 1
        assert metrics["cache_hit_rate"] == 0.5
        assert metrics["cached_memories"] == 1


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_handle_corrupted_memory_file(self, agent_memory):
        """Test handling of corrupted memory files"""
        # Create a corrupted JSON file
        memory_file = agent_memory.memory_dir / "CorruptedAgent" / "story_1.json"
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(memory_file, 'w') as f:
            f.write("{ invalid json content")
        
        # Should return None for corrupted file
        result = await agent_memory.get_memory("CorruptedAgent", "story_1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_permission_errors(self, agent_memory):
        """Test handling of permission errors"""
        # This test is platform-dependent and might not work on all systems
        try:
            # Create memory
            memory = AgentMemory(agent_type="PermissionAgent", story_id="story_1")
            await agent_memory.store_memory(memory)
            
            # Change permissions to read-only (Unix-like systems)
            memory_file = agent_memory.memory_dir / "PermissionAgent" / "story_1.json"
            if memory_file.exists():
                memory_file.chmod(0o444)  # Read-only
                
                # Try to store again - should handle gracefully
                memory.metadata["test"] = "value"
                try:
                    await agent_memory.store_memory(memory)
                except PermissionError:
                    # Expected on some systems
                    pass
                
                # Restore permissions for cleanup
                memory_file.chmod(0o644)
        except (OSError, AttributeError):
            # Skip test on systems where chmod doesn't work as expected
            pytest.skip("Permission test not applicable on this system")


class TestConcurrencyAndThreadSafety:
    """Test concurrency and thread safety"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, agent_memory):
        """Test concurrent memory operations"""
        async def store_memory(agent_type, story_id):
            memory = AgentMemory(agent_type=agent_type, story_id=story_id)
            await agent_memory.store_memory(memory)
            return await agent_memory.get_memory(agent_type, story_id)
        
        # Perform concurrent operations
        tasks = [
            store_memory("Agent1", "story_1"),
            store_memory("Agent2", "story_2"),
            store_memory("Agent3", "story_3"),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 3
        assert all(r is not None for r in results)
        assert all(isinstance(r, AgentMemory) for r in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_decision_recording(self, agent_memory):
        """Test concurrent decision recording"""
        async def record_decision(decision_num):
            decision = Decision(
                description=f"Decision {decision_num}",
                confidence=0.5 + decision_num * 0.1
            )
            await agent_memory.add_decision("TestAgent", "story_1", decision)
            return decision.id
        
        # Record decisions concurrently
        tasks = [record_decision(i) for i in range(10)]
        decision_ids = await asyncio.gather(*tasks)
        
        # All should succeed and have unique IDs
        assert len(decision_ids) == 10
        assert len(set(decision_ids)) == 10
        
        # Verify all were recorded
        decisions = await agent_memory.get_recent_decisions("TestAgent", "story_1")
        assert len(decisions) == 10


class TestSanitizationAndSecurity:
    """Test input sanitization and security measures"""
    
    @pytest.fixture
    def agent_memory(self):
        """Create a test agent memory instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_sanitize_story_id_for_filename(self, agent_memory):
        """Test that story IDs are sanitized for safe filenames"""
        # Test with problematic characters
        unsafe_story_id = "story/../../../etc/passwd"
        safe_story_id = "story with spaces and !@#$%^&*()+"
        
        memory1 = AgentMemory(agent_type="TestAgent", story_id=unsafe_story_id)
        memory2 = AgentMemory(agent_type="TestAgent", story_id=safe_story_id)
        
        await agent_memory.store_memory(memory1)
        await agent_memory.store_memory(memory2)
        
        # Should be stored safely
        retrieved1 = await agent_memory.get_memory("TestAgent", unsafe_story_id)
        retrieved2 = await agent_memory.get_memory("TestAgent", safe_story_id)
        
        assert retrieved1 is not None
        assert retrieved2 is not None
        assert retrieved1.story_id == unsafe_story_id
        assert retrieved2.story_id == safe_story_id
    
    @pytest.mark.asyncio
    async def test_empty_story_id_fallback(self, agent_memory):
        """Test fallback for empty story ID"""
        memory = AgentMemory(agent_type="TestAgent", story_id="")
        await agent_memory.store_memory(memory)
        
        # Should be able to retrieve with empty story_id
        retrieved = await agent_memory.get_memory("TestAgent", "")
        assert retrieved is not None
        assert retrieved.story_id == ""
    
    def test_get_memory_file_path_edge_cases(self, agent_memory):
        """Test memory file path generation edge cases"""
        # Test with None story_id
        memory_file = agent_memory._get_memory_file_path("TestAgent", None)
        assert "default.json" in str(memory_file)
        
        # Test with whitespace-only story_id  
        memory_file = agent_memory._get_memory_file_path("TestAgent", "   ")
        assert "default.json" in str(memory_file)
        
        # Test path structure
        memory_file = agent_memory._get_memory_file_path("TestAgent", "valid_story")
        assert memory_file.parent.name == "TestAgent"
        assert memory_file.name == "valid_story.json"
    
    def test_recent_activity_summary_edge_cases(self, agent_memory):
        """Test recent activity summary with edge cases"""
        from datetime import datetime, timedelta
        
        # Create memory with old data (beyond the week threshold)
        old_time = datetime.utcnow() - timedelta(days=10)
        
        memory = AgentMemory(agent_type="TestAgent", story_id="test_story")
        
        # Add old decision
        old_decision = Decision(
            description="Old decision",
            rationale="Old rationale", 
            timestamp=old_time
        )
        memory.decisions.append(old_decision)
        
        # Get summary (should not include old decision)
        summary = agent_memory._get_recent_activity_summary(memory)
        assert summary["recent_decisions"] == 0
        assert summary["recent_patterns"] == 0
        assert summary["recent_handoffs"] == 0
        assert summary["recent_snapshots"] == 0
        
        # Test with no updated_at
        memory.updated_at = None
        summary = agent_memory._get_recent_activity_summary(memory)
        assert summary["last_activity"] is None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])