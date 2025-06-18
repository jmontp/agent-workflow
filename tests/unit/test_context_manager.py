"""
Comprehensive test suite for ContextManager core functionality.

Tests the central coordination engine for context management operations,
including context pipeline orchestration, token budget management, and agent handoffs.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_manager import ContextManager
from context.models import (
    ContextRequest, AgentContext, TokenBudget, TokenUsage,
    CompressionLevel, ContextType, Decision, PhaseHandoff,
    ContextSnapshot, RelevanceScore
)
from context.exceptions import (
    ContextError, TokenBudgetExceededError, ContextNotFoundError,
    ContextTimeoutError
)
from tdd_models import TDDState, TDDTask, TDDCycle


class TestContextManagerInit:
    """Test ContextManager initialization"""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        cm = ContextManager()
        
        assert cm.project_path == Path.cwd()
        assert cm.max_tokens == 200000
        assert cm.cache_ttl_seconds == 300
        assert cm.max_preparation_time == 30
        assert cm.token_calculator is not None
        assert cm.agent_memory is not None
        assert len(cm._context_cache) == 0
        assert len(cm._active_contexts) == 0
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                max_tokens=100000,
                cache_ttl_seconds=600,
                max_preparation_time=60
            )
            
            assert cm.project_path == Path(temp_dir)
            assert cm.max_tokens == 100000
            assert cm.cache_ttl_seconds == 600
            assert cm.max_preparation_time == 60
    
    def test_init_creates_required_directories(self):
        """Test that initialization creates required directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            cm = ContextManager(project_path=str(project_path))
            
            # Check that .orch-state directory was created
            orch_state_dir = project_path / ".orch-state"
            assert orch_state_dir.exists()


class TestContextPreparation:
    """Test context preparation functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample TDD task"""
        return TDDTask(
            id="test_task_1",
            description="Test task description",
            cycle_id="cycle_1",
            current_state=TDDState.DESIGN
        )
    
    @pytest.mark.asyncio
    async def test_prepare_context_basic(self, context_manager, sample_task):
        """Test basic context preparation"""
        context = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=sample_task,
            max_tokens=50000,
            story_id="story_1"
        )
        
        assert isinstance(context, AgentContext)
        assert context.agent_type == "DesignAgent"
        assert context.story_id == "story_1"
        assert context.tdd_phase == TDDState.DESIGN
        assert context.token_budget is not None
        assert context.token_usage is not None
        assert context.preparation_time > 0
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_dict_task(self, context_manager):
        """Test context preparation with dict task"""
        task_dict = {
            "description": "Test task from dict",
            "story_id": "story_2",
            "current_state": "DESIGN"
        }
        
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=task_dict,
            story_id="story_2"
        )
        
        assert isinstance(context, AgentContext)
        assert context.agent_type == "CodeAgent"
        assert context.story_id == "story_2"
    
    @pytest.mark.asyncio
    async def test_prepare_context_caching(self, context_manager, sample_task):
        """Test context caching functionality"""
        # First call should miss cache
        context1 = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=sample_task,
            story_id="story_1"
        )
        assert not context1.cache_hit
        
        # Second call should hit cache
        context2 = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=sample_task,
            story_id="story_1"
        )
        assert context2.cache_hit
        
        # Check cache statistics
        metrics = context_manager.get_performance_metrics()
        assert metrics["context_manager"]["cache_hits"] == 1
        assert metrics["context_manager"]["cache_misses"] == 1
    
    @pytest.mark.asyncio
    async def test_prepare_context_timeout(self, context_manager, sample_task):
        """Test context preparation timeout"""
        # Set very short timeout
        context_manager.max_preparation_time = 0.001
        
        with pytest.raises(ContextTimeoutError):
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=sample_task,
                story_id="story_1"
            )
    
    @pytest.mark.asyncio
    async def test_prepare_context_token_budget_exceeded(self, context_manager, sample_task):
        """Test handling of token budget exceeded scenario"""
        # This should trigger compression when content exceeds budget
        context = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=sample_task,
            max_tokens=1000,  # Very small budget
            story_id="story_1"
        )
        
        # Should still succeed but with compression applied
        assert isinstance(context, AgentContext)
        assert context.token_usage.total_used <= 1000 or context.compression_applied


class TestAgentDecisionRecording:
    """Test agent decision recording functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_record_agent_decision(self, context_manager):
        """Test recording agent decisions"""
        decision_id = await context_manager.record_agent_decision(
            agent_type="DesignAgent",
            story_id="story_1",
            description="Test decision",
            rationale="Test rationale",
            outcome="Test outcome",
            confidence=0.8,
            artifacts={"file1.py": "content"}
        )
        
        assert decision_id is not None
        assert isinstance(decision_id, str)
        
        # Verify decision was stored
        decisions = await context_manager.get_recent_decisions(
            agent_type="DesignAgent",
            story_id="story_1"
        )
        
        assert len(decisions) == 1
        assert decisions[0].id == decision_id
        assert decisions[0].description == "Test decision"
        assert decisions[0].confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_record_multiple_decisions(self, context_manager):
        """Test recording multiple decisions"""
        decision_ids = []
        
        for i in range(3):
            decision_id = await context_manager.record_agent_decision(
                agent_type="CodeAgent",
                story_id="story_1",
                description=f"Decision {i}",
                confidence=0.5 + i * 0.1
            )
            decision_ids.append(decision_id)
        
        # Verify all decisions were stored
        decisions = await context_manager.get_recent_decisions(
            agent_type="CodeAgent",
            story_id="story_1"
        )
        
        assert len(decisions) == 3
        # Should be in reverse chronological order
        assert decisions[0].description == "Decision 2"
        assert decisions[1].description == "Decision 1"
        assert decisions[2].description == "Decision 0"


class TestPhaseHandoffs:
    """Test TDD phase handoff functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_record_phase_handoff(self, context_manager):
        """Test recording phase handoffs"""
        handoff_id = await context_manager.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id="story_1",
            artifacts={"design.md": "design content"},
            context_summary="Design completed",
            handoff_notes="Ready for test writing"
        )
        
        assert handoff_id is not None
        assert isinstance(handoff_id, str)
        
        # Verify handoff was recorded for both agents
        from_handoffs = await context_manager.get_phase_handoffs(
            agent_type="DesignAgent",
            story_id="story_1"
        )
        to_handoffs = await context_manager.get_phase_handoffs(
            agent_type="QAAgent",
            story_id="story_1"
        )
        
        assert len(from_handoffs) == 1
        assert len(to_handoffs) == 1
        assert from_handoffs[0].id == handoff_id
        assert to_handoffs[0].id == handoff_id
    
    @pytest.mark.asyncio
    async def test_get_phase_handoffs_filtered(self, context_manager):
        """Test getting filtered phase handoffs"""
        # Record multiple handoffs
        await context_manager.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id="story_1"
        )
        
        await context_manager.record_phase_handoff(
            from_agent="QAAgent",
            to_agent="CodeAgent",
            from_phase=TDDState.TEST_RED,
            to_phase=TDDState.CODE_GREEN,
            story_id="story_1"
        )
        
        # Test filtering by from_phase
        design_handoffs = await context_manager.get_phase_handoffs(
            agent_type="DesignAgent",
            story_id="story_1",
            from_phase=TDDState.DESIGN
        )
        assert len(design_handoffs) == 1
        
        # Test filtering by to_phase
        test_handoffs = await context_manager.get_phase_handoffs(
            agent_type="QAAgent",
            story_id="story_1",
            to_phase=TDDState.TEST_RED
        )
        assert len(test_handoffs) == 1


class TestContextSnapshots:
    """Test context snapshot functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.fixture
    def sample_context(self):
        """Create a sample agent context"""
        return AgentContext(
            request_id="req_1",
            agent_type="DesignAgent",
            story_id="story_1",
            core_context="Core context content",
            tdd_phase=TDDState.DESIGN,
            token_usage=TokenUsage(
                context_id="req_1",
                total_used=1000,
                core_task_used=600,
                historical_used=200,
                dependencies_used=150,
                agent_memory_used=50
            )
        )
    
    @pytest.mark.asyncio
    async def test_create_context_snapshot(self, context_manager, sample_context):
        """Test creating context snapshots"""
        snapshot_id = await context_manager.create_context_snapshot(
            agent_type="DesignAgent",
            story_id="story_1",
            context=sample_context,
            summary="Test snapshot"
        )
        
        assert snapshot_id is not None
        assert isinstance(snapshot_id, str)
        
        # Verify snapshot was stored
        history = await context_manager.get_agent_context_history(
            agent_type="DesignAgent",
            story_id="story_1"
        )
        
        assert len(history) == 1
        assert history[0].id == snapshot_id
        assert history[0].context_summary == "Test snapshot"
    
    @pytest.mark.asyncio
    async def test_get_context_history_filtered(self, context_manager, sample_context):
        """Test getting filtered context history"""
        # Create snapshots for different phases
        sample_context.tdd_phase = TDDState.DESIGN
        await context_manager.create_context_snapshot(
            agent_type="DesignAgent",
            story_id="story_1",
            context=sample_context,
            summary="Design snapshot"
        )
        
        sample_context.tdd_phase = TDDState.TEST_RED
        await context_manager.create_context_snapshot(
            agent_type="DesignAgent",
            story_id="story_1",
            context=sample_context,
            summary="Test snapshot"
        )
        
        # Test filtering by TDD phase
        design_history = await context_manager.get_agent_context_history(
            agent_type="DesignAgent",
            story_id="story_1",
            tdd_phase=TDDState.DESIGN
        )
        assert len(design_history) == 1
        assert design_history[0].context_summary == "Design snapshot"
        
        # Test limit parameter
        limited_history = await context_manager.get_agent_context_history(
            agent_type="DesignAgent",
            story_id="story_1",
            limit=1
        )
        assert len(limited_history) == 1


class TestTokenBudgetOptimization:
    """Test token budget optimization functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_optimize_token_budget(self, context_manager):
        """Test token budget optimization"""
        # Create sample budget and usage
        budget = TokenBudget(
            total_budget=10000,
            core_task=4000,
            historical=2500,
            dependencies=2000,
            agent_memory=1000,
            buffer=500
        )
        
        usage = TokenUsage(
            context_id="test",
            total_used=8000,
            core_task_used=5000,  # Over budget
            historical_used=1000,  # Under budget
            dependencies_used=1500,
            agent_memory_used=500
        )
        
        # Create context with budget
        context = AgentContext(
            request_id="test",
            agent_type="TestAgent",
            story_id="story_1",
            token_budget=budget,
            token_usage=usage
        )
        
        # Optimize budget
        optimized = await context_manager.optimize_token_budget(
            context=context,
            actual_usage=usage,
            quality_score=0.8
        )
        
        assert isinstance(optimized, TokenBudget)
        assert optimized.total_budget == budget.total_budget
        # Should have adjusted allocations based on usage patterns
        assert optimized.core_task != budget.core_task or optimized.historical != budget.historical


class TestContextInvalidation:
    """Test context invalidation and cleanup functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_invalidate_context(self, context_manager):
        """Test context invalidation"""
        # Prepare a context first
        task = {"description": "test", "story_id": "story_1"}
        context = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_1"
        )
        
        # Verify context is cached
        assert len(context_manager._context_cache) > 0
        assert context.request_id in context_manager._active_contexts
        
        # Invalidate context
        await context_manager.invalidate_context(context.request_id)
        
        # Verify context is removed
        assert context.request_id not in context_manager._active_contexts
    
    @pytest.mark.asyncio
    async def test_cleanup_cache(self, context_manager):
        """Test cache cleanup functionality"""
        # Prepare a context
        task = {"description": "test", "story_id": "story_1"}
        await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_1"
        )
        
        # Verify cache has entries
        assert len(context_manager._context_cache) > 0
        
        # Set very short TTL to force expiration
        context_manager.cache_ttl_seconds = 0
        
        # Wait a moment and cleanup
        await asyncio.sleep(0.1)
        cleaned_count = await context_manager.cleanup_cache()
        
        assert cleaned_count > 0
        assert len(context_manager._context_cache) == 0


class TestAgentLearningAnalysis:
    """Test agent learning analysis functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_analyze_agent_learning(self, context_manager):
        """Test agent learning analysis"""
        # Record some decisions first
        await context_manager.record_agent_decision(
            agent_type="DesignAgent",
            story_id="story_1",
            description="Decision 1",
            confidence=0.8
        )
        
        await context_manager.record_agent_decision(
            agent_type="DesignAgent",
            story_id="story_1",
            description="Decision 2",
            confidence=0.9
        )
        
        # Analyze learning patterns
        analysis = await context_manager.analyze_agent_learning(
            agent_type="DesignAgent",
            story_id="story_1"
        )
        
        assert isinstance(analysis, dict)
        # Should contain analysis results based on recorded decisions


class TestPerformanceMetrics:
    """Test performance metrics functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, context_manager):
        """Test performance metrics collection"""
        # Perform some operations to generate metrics
        task = {"description": "test", "story_id": "story_1"}
        await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_1"
        )
        
        # Get metrics
        metrics = context_manager.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert "context_manager" in metrics
        assert "token_calculator" in metrics
        assert "agent_memory" in metrics
        
        cm_metrics = metrics["context_manager"]
        assert "total_requests" in cm_metrics
        assert "cache_hits" in cm_metrics
        assert "cache_misses" in cm_metrics
        assert "cache_hit_rate" in cm_metrics
        assert "average_preparation_time" in cm_metrics
        
        assert cm_metrics["total_requests"] >= 1


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_prepare_context_invalid_task(self, context_manager):
        """Test error handling with invalid task"""
        with pytest.raises(ContextError):
            await context_manager.prepare_context(
                agent_type="InvalidAgent",
                task=None,  # Invalid task
                story_id="story_1"
            )
    
    @pytest.mark.asyncio
    async def test_prepare_context_zero_tokens(self, context_manager):
        """Test error handling with zero tokens"""
        task = {"description": "test", "story_id": "story_1"}
        
        with pytest.raises(Exception):  # Should raise ValueError from TokenCalculator
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=task,
                max_tokens=0,
                story_id="story_1"
            )


class TestConcurrencyAndThreadSafety:
    """Test concurrency and thread safety"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a test context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_concurrent_context_preparation(self, context_manager):
        """Test concurrent context preparation"""
        async def prepare_context(agent_type, story_id):
            task = {"description": f"test for {agent_type}", "story_id": story_id}
            return await context_manager.prepare_context(
                agent_type=agent_type,
                task=task,
                story_id=story_id
            )
        
        # Prepare multiple contexts concurrently
        tasks = [
            prepare_context("DesignAgent", "story_1"),
            prepare_context("CodeAgent", "story_2"),
            prepare_context("QAAgent", "story_3"),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 3
        assert all(isinstance(r, AgentContext) for r in results)
        
        # Should have different request IDs
        request_ids = [r.request_id for r in results]
        assert len(set(request_ids)) == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_decision_recording(self, context_manager):
        """Test concurrent decision recording"""
        async def record_decision(agent_type, story_id, decision_num):
            return await context_manager.record_agent_decision(
                agent_type=agent_type,
                story_id=story_id,
                description=f"Decision {decision_num}",
                confidence=0.5 + decision_num * 0.1
            )
        
        # Record multiple decisions concurrently
        tasks = [
            record_decision("DesignAgent", "story_1", i)
            for i in range(5)
        ]
        
        decision_ids = await asyncio.gather(*tasks)
        
        # All should succeed and have unique IDs
        assert len(decision_ids) == 5
        assert len(set(decision_ids)) == 5
        
        # Verify all were recorded
        decisions = await context_manager.get_recent_decisions(
            agent_type="DesignAgent",
            story_id="story_1"
        )
        assert len(decisions) == 5


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])