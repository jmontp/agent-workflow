"""
Integration test suite for end-to-end context management system.

Tests the complete context management pipeline including context preparation,
agent memory integration, TDD phase handoffs, and orchestrator coordination.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_manager import ContextManager
from token_calculator import TokenCalculator
from agent_memory import FileBasedAgentMemory
from context.models import (
    ContextRequest, AgentContext, TokenBudget, TokenUsage,
    CompressionLevel, Decision, PhaseHandoff, ContextSnapshot
)
from tdd_models import TDDState, TDDTask, TDDCycle


class TestContextManagerIntegration:
    """Test integration between ContextManager and its components"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with sample files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            
            # Create sample project files
            (project_path / "main.py").write_text("""
def main():
    print("Hello, world!")
    return 0

if __name__ == "__main__":
    main()
""")
            
            (project_path / "test_main.py").write_text("""
import pytest
from main import main

def test_main():
    result = main()
    assert result == 0
""")
            
            (project_path / "README.md").write_text("""
# Test Project

This is a test project for context management.

## Features
- Simple hello world application
- Unit tests included
""")
            
            (project_path / "requirements.txt").write_text("""
pytest>=7.0.0
""")
            
            yield project_path
    
    @pytest.fixture
    def context_manager(self, temp_project):
        """Create a context manager for the test project"""
        return ContextManager(project_path=str(temp_project))
    
    @pytest.mark.asyncio
    async def test_full_context_preparation_pipeline(self, context_manager):
        """Test the complete context preparation pipeline"""
        # Create a TDD task
        task = TDDTask(
            id="test_task_1",
            description="Implement hello world feature",
            story_id="story_hello_world",
            current_state=TDDState.DESIGN
        )
        
        # Prepare context
        context = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=task,
            max_tokens=50000,
            story_id="story_hello_world"
        )
        
        # Verify context structure
        assert isinstance(context, AgentContext)
        assert context.agent_type == "DesignAgent"
        assert context.story_id == "story_hello_world"
        assert context.tdd_phase == TDDState.DESIGN
        assert context.token_budget is not None
        assert context.token_usage is not None
        assert context.core_context != ""
        assert context.preparation_time > 0
        
        # Verify token budget allocation
        budget = context.token_budget
        assert budget.total_budget <= 50000
        assert budget.core_task > 0
        assert budget.historical >= 0
        assert budget.dependencies >= 0
        assert budget.agent_memory >= 0
        assert budget.buffer >= 0
        
        # Verify token usage tracking
        usage = context.token_usage
        assert usage.total_used <= budget.total_budget
        assert usage.core_task_used >= 0
        assert usage.context_id == context.request_id
    
    @pytest.mark.asyncio
    async def test_agent_memory_integration(self, context_manager):
        """Test integration with agent memory system"""
        # Record some decisions
        decision_id = await context_manager.record_agent_decision(
            agent_type="DesignAgent",
            story_id="story_test",
            description="Choose modular architecture",
            rationale="Better maintainability and testability",
            outcome="Architecture defined",
            confidence=0.85,
            artifacts={"architecture.md": "design content"}
        )
        
        assert decision_id is not None
        
        # Record a phase handoff
        handoff_id = await context_manager.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id="story_test",
            artifacts={"design.md": "design content"},
            context_summary="Design phase completed",
            handoff_notes="Ready for test writing"
        )
        
        assert handoff_id is not None
        
        # Prepare context that should include agent memory
        task = {"description": "Write tests", "story_id": "story_test"}
        context = await context_manager.prepare_context(
            agent_type="QAAgent",
            task=task,
            story_id="story_test",
            include_agent_memory=True
        )
        
        # Should include agent memory in context
        assert context.agent_memory is not None
        assert "Recent Decisions" in context.agent_memory
        assert "Choose modular architecture" in context.agent_memory
    
    @pytest.mark.asyncio
    async def test_context_snapshot_workflow(self, context_manager):
        """Test context snapshot creation and retrieval workflow"""
        # Prepare initial context
        task = TDDTask(
            id="snapshot_test",
            description="Test snapshot workflow",
            story_id="story_snapshot",
            current_state=TDDState.CODE_GREEN
        )
        
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=task,
            story_id="story_snapshot"
        )
        
        # Create context snapshot
        snapshot_id = await context_manager.create_context_snapshot(
            agent_type="CodeAgent",
            story_id="story_snapshot",
            context=context,
            summary="Context after implementing feature"
        )
        
        assert snapshot_id is not None
        
        # Retrieve context history
        history = await context_manager.get_agent_context_history(
            agent_type="CodeAgent",
            story_id="story_snapshot",
            tdd_phase=TDDState.CODE_GREEN
        )
        
        assert len(history) == 1
        assert history[0].id == snapshot_id
        assert history[0].context_summary == "Context after implementing feature"
        assert history[0].tdd_phase == TDDState.CODE_GREEN
    
    @pytest.mark.asyncio
    async def test_token_budget_optimization_workflow(self, context_manager):
        """Test token budget optimization workflow"""
        # Prepare context
        task = {"description": "Test optimization", "story_id": "story_opt"}
        context = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_opt"
        )
        
        original_budget = context.token_budget
        original_usage = context.token_usage
        
        # Optimize budget based on usage
        optimized_budget = await context_manager.optimize_token_budget(
            context=context,
            actual_usage=original_usage,
            quality_score=0.8
        )
        
        assert isinstance(optimized_budget, TokenBudget)
        assert optimized_budget.total_budget == original_budget.total_budget
        
        # Should have recorded optimization in token calculator
        metrics = context_manager.get_performance_metrics()
        assert metrics["token_calculator"]["optimization_calls"] >= 1


class TestTDDPhaseHandoffs:
    """Test TDD phase handoff integration"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_design_to_test_handoff(self, context_manager):
        """Test handoff from Design phase to Test phase"""
        story_id = "story_design_test"
        
        # Design phase: Record design decisions
        await context_manager.record_agent_decision(
            agent_type="DesignAgent",
            story_id=story_id,
            description="Define API interface",
            rationale="Clear contract for implementation",
            confidence=0.9
        )
        
        # Record handoff
        handoff_id = await context_manager.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id=story_id,
            artifacts={"api_spec.md": "API specification"},
            context_summary="API design completed",
            handoff_notes="Ready for test-driven development"
        )
        
        # Test phase: Prepare context with handoff information
        test_task = TDDTask(
            id="test_task",
            description="Write tests for API",
            story_id=story_id,
            current_state=TDDState.TEST_RED
        )
        
        context = await context_manager.prepare_context(
            agent_type="QAAgent",
            task=test_task,
            story_id=story_id
        )
        
        # Verify handoff information is available
        handoffs = await context_manager.get_phase_handoffs(
            agent_type="QAAgent",
            story_id=story_id,
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED
        )
        
        assert len(handoffs) == 1
        assert handoffs[0].id == handoff_id
        assert handoffs[0].context_summary == "API design completed"
    
    @pytest.mark.asyncio
    async def test_test_to_code_handoff(self, context_manager):
        """Test handoff from Test phase to Code phase"""
        story_id = "story_test_code"
        
        # Test phase: Record test creation
        await context_manager.record_agent_decision(
            agent_type="QAAgent",
            story_id=story_id,
            description="Create failing tests",
            outcome="Tests written and failing as expected",
            confidence=0.95
        )
        
        # Record handoff
        await context_manager.record_phase_handoff(
            from_agent="QAAgent",
            to_agent="CodeAgent",
            from_phase=TDDState.TEST_RED,
            to_phase=TDDState.CODE_GREEN,
            story_id=story_id,
            artifacts={"test_api.py": "test implementation"},
            context_summary="Failing tests created",
            handoff_notes="Implement to make tests pass"
        )
        
        # Code phase: Prepare context
        code_task = TDDTask(
            id="code_task",
            description="Implement API to pass tests",
            story_id=story_id,
            current_state=TDDState.CODE_GREEN
        )
        
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=code_task,
            story_id=story_id
        )
        
        # Verify context includes test information
        assert context.agent_memory is not None
        assert "Create failing tests" in context.agent_memory
    
    @pytest.mark.asyncio
    async def test_code_to_refactor_handoff(self, context_manager):
        """Test handoff from Code phase to Refactor phase"""
        story_id = "story_code_refactor"
        
        # Code phase completion
        await context_manager.record_agent_decision(
            agent_type="CodeAgent",
            story_id=story_id,
            description="Implement minimal solution",
            outcome="All tests passing",
            confidence=0.8
        )
        
        # Record handoff to refactor
        await context_manager.record_phase_handoff(
            from_agent="CodeAgent",
            to_agent="CodeAgent",  # Same agent for refactor
            from_phase=TDDState.CODE_GREEN,
            to_phase=TDDState.REFACTOR,
            story_id=story_id,
            artifacts={"implementation.py": "working code"},
            context_summary="Tests passing, ready for refactor",
            handoff_notes="Improve code quality and structure"
        )
        
        # Refactor phase
        refactor_task = TDDTask(
            id="refactor_task",
            description="Refactor implementation",
            story_id=story_id,
            current_state=TDDState.REFACTOR
        )
        
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=refactor_task,
            story_id=story_id
        )
        
        # Should have information about previous implementation
        decisions = await context_manager.get_recent_decisions(
            agent_type="CodeAgent",
            story_id=story_id
        )
        
        assert len(decisions) >= 1
        assert any("Implement minimal solution" in d.description for d in decisions)


class TestMultiAgentContextWorkflow:
    """Test multi-agent context sharing and coordination"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_parallel_agent_contexts(self, context_manager):
        """Test parallel context preparation for different agents"""
        story_id = "story_parallel"
        
        # Prepare contexts for different agents in parallel
        async def prepare_agent_context(agent_type, description):
            task = {
                "description": description,
                "story_id": story_id,
                "agent_type": agent_type
            }
            return await context_manager.prepare_context(
                agent_type=agent_type,
                task=task,
                story_id=story_id
            )
        
        contexts = await asyncio.gather(
            prepare_agent_context("DesignAgent", "Design the feature"),
            prepare_agent_context("QAAgent", "Plan testing strategy"),
            prepare_agent_context("DataAgent", "Analyze data requirements")
        )
        
        # All contexts should be prepared successfully
        assert len(contexts) == 3
        assert all(isinstance(ctx, AgentContext) for ctx in contexts)
        
        # Each should have different agent types
        agent_types = [ctx.agent_type for ctx in contexts]
        assert "DesignAgent" in agent_types
        assert "QAAgent" in agent_types
        assert "DataAgent" in agent_types
        
        # All should be for the same story
        assert all(ctx.story_id == story_id for ctx in contexts)
    
    @pytest.mark.asyncio
    async def test_context_sharing_between_agents(self, context_manager):
        """Test context sharing and learning between agents"""
        story_id = "story_sharing"
        
        # DesignAgent records design decisions
        design_decisions = [
            "Choose microservices architecture",
            "Use REST API for communication",
            "Implement event-driven patterns"
        ]
        
        for decision in design_decisions:
            await context_manager.record_agent_decision(
                agent_type="DesignAgent",
                story_id=story_id,
                description=decision,
                confidence=0.8
            )
        
        # QAAgent accesses design context
        qa_context = await context_manager.prepare_context(
            agent_type="QAAgent",
            task={"description": "Plan testing", "story_id": story_id},
            story_id=story_id
        )
        
        # Should include design decisions in agent memory
        assert qa_context.agent_memory is not None
        for decision in design_decisions:
            assert decision in qa_context.agent_memory
        
        # CodeAgent also accesses shared context
        code_context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task={"description": "Implement features", "story_id": story_id},
            story_id=story_id
        )
        
        # Should also have access to design decisions
        assert code_context.agent_memory is not None
    
    @pytest.mark.asyncio
    async def test_cross_agent_learning_patterns(self, context_manager):
        """Test learning patterns across different agents"""
        story_id = "story_learning"
        
        # Multiple agents record their learning
        agents_and_patterns = [
            ("DesignAgent", "Always validate input parameters"),
            ("QAAgent", "Test edge cases first"),
            ("CodeAgent", "Use dependency injection for testability"),
            ("DataAgent", "Validate data quality before processing")
        ]
        
        for agent_type, pattern_desc in agents_and_patterns:
            await context_manager.record_agent_decision(
                agent_type=agent_type,
                story_id=story_id,
                description=f"Apply pattern: {pattern_desc}",
                confidence=0.9
            )
        
        # Each agent should be able to learn from others
        for agent_type, _ in agents_and_patterns:
            analysis = await context_manager.analyze_agent_learning(
                agent_type=agent_type,
                story_id=story_id
            )
            
            assert isinstance(analysis, dict)
            # Should have recorded learning data


class TestPerformanceAndScalability:
    """Test performance and scalability aspects"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_context_caching_performance(self, context_manager):
        """Test context caching improves performance"""
        task = {"description": "Performance test", "story_id": "story_perf"}
        
        # First preparation (cache miss)
        start_time = datetime.utcnow()
        context1 = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_perf"
        )
        first_duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Second preparation (cache hit)
        start_time = datetime.utcnow()
        context2 = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_perf"
        )
        second_duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Cache hit should be faster
        assert context2.cache_hit
        assert second_duration < first_duration
        
        # Check performance metrics
        metrics = context_manager.get_performance_metrics()
        assert metrics["context_manager"]["cache_hits"] >= 1
        assert metrics["context_manager"]["cache_misses"] >= 1
        assert metrics["context_manager"]["cache_hit_rate"] > 0
    
    @pytest.mark.asyncio
    async def test_memory_usage_efficiency(self, context_manager):
        """Test memory usage remains efficient with many operations"""
        # Perform many context operations
        for i in range(50):
            task = {"description": f"Task {i}", "story_id": f"story_{i}"}
            context = await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=task,
                story_id=f"story_{i}"
            )
            
            # Record decision for each
            await context_manager.record_agent_decision(
                agent_type="DesignAgent",
                story_id=f"story_{i}",
                description=f"Decision for task {i}",
                confidence=0.8
            )
        
        # Check that cache doesn't grow unbounded
        metrics = context_manager.get_performance_metrics()
        cached_contexts = metrics["context_manager"]["cached_contexts"]
        
        # Should have reasonable cache size
        assert cached_contexts <= 100  # Reasonable limit
    
    @pytest.mark.asyncio
    async def test_token_calculation_efficiency(self, context_manager):
        """Test token calculation efficiency"""
        # Create content of varying sizes
        content_sizes = [100, 1000, 10000, 50000]
        
        for size in content_sizes:
            content = "x" * size
            start_time = datetime.utcnow()
            
            tokens = await context_manager.token_calculator.estimate_tokens(content)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Should complete quickly
            assert duration < 1.0  # Less than 1 second
            assert tokens > 0
            
        # Check token calculator metrics
        tc_metrics = context_manager.get_performance_metrics()["token_calculator"]
        assert tc_metrics["token_estimations"] >= len(content_sizes)


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_context_preparation_timeout_recovery(self, context_manager):
        """Test recovery from context preparation timeouts"""
        # Set very short timeout
        original_timeout = context_manager.max_preparation_time
        context_manager.max_preparation_time = 0.001
        
        task = {"description": "Timeout test", "story_id": "story_timeout"}
        
        # Should raise timeout error
        with pytest.raises(Exception):  # ContextTimeoutError or similar
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=task,
                story_id="story_timeout"
            )
        
        # Restore normal timeout and retry
        context_manager.max_preparation_time = original_timeout
        
        # Should succeed now
        context = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_timeout"
        )
        
        assert isinstance(context, AgentContext)
    
    @pytest.mark.asyncio
    async def test_corrupted_memory_recovery(self, context_manager):
        """Test recovery from corrupted memory files"""
        # First, create valid memory
        await context_manager.record_agent_decision(
            agent_type="TestAgent",
            story_id="story_corrupt",
            description="Valid decision",
            confidence=0.8
        )
        
        # Corrupt the memory file
        memory_file = (context_manager.agent_memory.memory_dir / 
                      "TestAgent" / "story_corrupt.json")
        
        if memory_file.exists():
            with open(memory_file, 'w') as f:
                f.write("{ corrupted json content")
        
        # Should handle corruption gracefully
        decisions = await context_manager.get_recent_decisions(
            agent_type="TestAgent",
            story_id="story_corrupt"
        )
        
        # Should return empty list instead of crashing
        assert isinstance(decisions, list)
    
    @pytest.mark.asyncio
    async def test_invalid_task_handling(self, context_manager):
        """Test handling of invalid task inputs"""
        # Test with None task
        with pytest.raises(Exception):
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=None,
                story_id="story_invalid"
            )
        
        # Test with invalid agent type
        task = {"description": "Valid task", "story_id": "story_invalid"}
        
        # Should handle unknown agent types gracefully
        context = await context_manager.prepare_context(
            agent_type="UnknownAgent",
            task=task,
            story_id="story_invalid"
        )
        
        # Should use default profile
        assert isinstance(context, AgentContext)
        assert context.agent_type == "UnknownAgent"


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow scenarios"""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_tdd_cycle_workflow(self, context_manager):
        """Test complete TDD cycle with context management"""
        story_id = "story_complete_cycle"
        
        # Phase 1: Design
        design_task = TDDTask(
            id="design_task",
            description="Design user authentication feature",
            story_id=story_id,
            current_state=TDDState.DESIGN
        )
        
        design_context = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=design_task,
            story_id=story_id
        )
        
        await context_manager.record_agent_decision(
            agent_type="DesignAgent",
            story_id=story_id,
            description="Use JWT tokens for authentication",
            rationale="Stateless and scalable",
            confidence=0.9
        )
        
        design_snapshot = await context_manager.create_context_snapshot(
            agent_type="DesignAgent",
            story_id=story_id,
            context=design_context,
            summary="Design phase completed"
        )
        
        # Handoff to QA
        await context_manager.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id=story_id,
            context_summary="Authentication design ready",
            handoff_notes="Ready for test-driven development"
        )
        
        # Phase 2: Test Writing
        test_task = TDDTask(
            id="test_task",
            description="Write failing tests for authentication",
            story_id=story_id,
            current_state=TDDState.TEST_RED
        )
        
        test_context = await context_manager.prepare_context(
            agent_type="QAAgent",
            task=test_task,
            story_id=story_id
        )
        
        # Should include design decisions
        assert "JWT tokens" in test_context.agent_memory
        
        await context_manager.record_agent_decision(
            agent_type="QAAgent",
            story_id=story_id,
            description="Create comprehensive auth tests",
            outcome="Failing tests written",
            confidence=0.95
        )
        
        # Handoff to Code
        await context_manager.record_phase_handoff(
            from_agent="QAAgent",
            to_agent="CodeAgent",
            from_phase=TDDState.TEST_RED,
            to_phase=TDDState.CODE_GREEN,
            story_id=story_id,
            context_summary="Failing tests created",
            handoff_notes="Implement to make tests pass"
        )
        
        # Phase 3: Implementation
        code_task = TDDTask(
            id="code_task",
            description="Implement authentication to pass tests",
            story_id=story_id,
            current_state=TDDState.CODE_GREEN
        )
        
        code_context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=code_task,
            story_id=story_id
        )
        
        # Should include both design and test context
        assert code_context.agent_memory is not None
        
        await context_manager.record_agent_decision(
            agent_type="CodeAgent",
            story_id=story_id,
            description="Implement JWT authentication",
            outcome="All tests passing",
            confidence=0.85
        )
        
        # Verify complete workflow
        all_decisions = await context_manager.get_recent_decisions(
            agent_type="DesignAgent",
            story_id=story_id
        )
        all_decisions.extend(await context_manager.get_recent_decisions(
            agent_type="QAAgent",
            story_id=story_id
        ))
        all_decisions.extend(await context_manager.get_recent_decisions(
            agent_type="CodeAgent",
            story_id=story_id
        ))
        
        # Should have decisions from all phases
        assert len(all_decisions) >= 3
        
        # Verify handoffs recorded
        handoffs = await context_manager.get_phase_handoffs(
            agent_type="DesignAgent",
            story_id=story_id
        )
        handoffs.extend(await context_manager.get_phase_handoffs(
            agent_type="QAAgent",
            story_id=story_id
        ))
        
        assert len(handoffs) >= 2
        
        # Check final performance metrics
        metrics = context_manager.get_performance_metrics()
        assert metrics["context_manager"]["total_requests"] >= 3
        assert metrics["agent_memory"]["store_calls"] >= 3


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])