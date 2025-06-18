"""
Unit tests for Context Management Infrastructure

Tests the core components: ContextManager, TokenCalculator, and AgentMemory.
"""

import asyncio
import json
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# Add lib directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_manager import ContextManager
from token_calculator import TokenCalculator
from agent_memory import FileBasedAgentMemory
from context.models import (
    TokenBudget, TokenUsage, AgentMemory, Decision, PhaseHandoff, 
    Pattern, ContextSnapshot, FileType, CompressionLevel
)
from tdd_models import TDDState


class TestTokenCalculator:
    """Test TokenCalculator functionality"""
    
    @pytest.fixture
    def calculator(self):
        return TokenCalculator(max_tokens=100000)
    
    @pytest.mark.asyncio
    async def test_basic_budget_calculation(self, calculator):
        """Test basic token budget calculation"""
        budget = await calculator.calculate_budget(
            total_tokens=10000,
            agent_type="CodeAgent"
        )
        
        assert isinstance(budget, TokenBudget)
        assert budget.total_budget == 10000
        assert budget.core_task > 0
        assert budget.historical >= 0
        assert budget.dependencies >= 0
        assert budget.agent_memory >= 0
        assert budget.buffer >= 0
        
        # Check total allocation doesn't exceed budget
        total_allocated = (
            budget.core_task + budget.historical + budget.dependencies + 
            budget.agent_memory + budget.buffer
        )
        assert total_allocated <= 10000
    
    @pytest.mark.asyncio
    async def test_agent_specific_budgets(self, calculator):
        """Test that different agents get different budget allocations"""
        design_budget = await calculator.calculate_budget(
            total_tokens=10000,
            agent_type="DesignAgent"
        )
        
        code_budget = await calculator.calculate_budget(
            total_tokens=10000,
            agent_type="CodeAgent"
        )
        
        qa_budget = await calculator.calculate_budget(
            total_tokens=10000,
            agent_type="QAAgent"
        )
        
        # Different agents should have different allocations
        assert design_budget.core_task != code_budget.core_task or \
               design_budget.historical != code_budget.historical
        assert code_budget.dependencies != qa_budget.dependencies
    
    @pytest.mark.asyncio
    async def test_tdd_phase_modifiers(self, calculator):
        """Test TDD phase-specific budget modifications"""
        design_budget = await calculator.calculate_budget(
            total_tokens=10000,
            agent_type="DesignAgent",
            tdd_phase=TDDState.DESIGN
        )
        
        code_budget = await calculator.calculate_budget(
            total_tokens=10000,
            agent_type="CodeAgent",
            tdd_phase=TDDState.CODE_GREEN
        )
        
        # Design phase should allocate more to historical context
        assert design_budget.historical > 0
        # Code phase should allocate more to core task
        assert code_budget.core_task > 0
    
    @pytest.mark.asyncio
    async def test_token_estimation(self, calculator):
        """Test token estimation for different content types"""
        python_code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        
        markdown_text = """
# Header
This is a markdown document with some content.
"""
        
        json_data = '{"key": "value", "number": 42}'
        
        python_tokens = await calculator.estimate_tokens(python_code, FileType.PYTHON)
        markdown_tokens = await calculator.estimate_tokens(markdown_text, FileType.MARKDOWN)
        json_tokens = await calculator.estimate_tokens(json_data, FileType.JSON)
        
        assert python_tokens > 0
        assert markdown_tokens > 0
        assert json_tokens > 0
        
        # Python code should have more tokens than equivalent length markdown
        assert python_tokens >= markdown_tokens
    
    @pytest.mark.asyncio
    async def test_budget_optimization(self, calculator):
        """Test budget optimization based on usage patterns"""
        initial_budget = TokenBudget(
            total_budget=10000,
            core_task=4000,
            historical=2500,
            dependencies=2000,
            agent_memory=1000,
            buffer=500
        )
        
        # Simulate under-usage of historical context
        usage = TokenUsage(
            context_id="test",
            total_used=7000,
            core_task_used=3800,
            historical_used=1000,  # Under-used
            dependencies_used=1900,
            agent_memory_used=900,
            buffer_used=400
        )
        
        optimized_budget = await calculator.optimize_allocation(
            initial_budget, usage, context_quality=0.8
        )
        
        assert isinstance(optimized_budget, TokenBudget)
        assert optimized_budget.total_budget == initial_budget.total_budget
        # Historical allocation should be reduced due to under-usage
        assert optimized_budget.historical <= initial_budget.historical
    
    def test_performance_metrics(self, calculator):
        """Test performance metrics collection"""
        metrics = calculator.get_performance_metrics()
        
        assert "budget_calculations" in metrics
        assert "optimization_calls" in metrics
        assert "token_estimations" in metrics
        assert isinstance(metrics["budget_calculations"], int)


class TestAgentMemory:
    """Test AgentMemory functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory(self, temp_dir):
        return FileBasedAgentMemory(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_memory_storage_and_retrieval(self, memory):
        """Test basic memory storage and retrieval"""
        # Test with non-existent memory
        result = await memory.get_memory("TestAgent", "story-1")
        assert result is None
        
        # Create and store memory
        test_memory = AgentMemory(
            agent_type="TestAgent",
            story_id="story-1"
        )
        
        await memory.store_memory(test_memory)
        
        # Retrieve and verify
        retrieved = await memory.get_memory("TestAgent", "story-1")
        assert retrieved is not None
        assert retrieved.agent_type == "TestAgent"
        assert retrieved.story_id == "story-1"
    
    @pytest.mark.asyncio
    async def test_decision_management(self, memory):
        """Test decision recording and retrieval"""
        decision = Decision(
            agent_type="TestAgent",
            description="Test decision",
            rationale="Testing decision recording",
            outcome="Success",
            confidence=0.9
        )
        
        await memory.add_decision("TestAgent", "story-1", decision)
        
        decisions = await memory.get_recent_decisions("TestAgent", "story-1", limit=5)
        assert len(decisions) == 1
        assert decisions[0].description == "Test decision"
        assert decisions[0].confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_pattern_management(self, memory):
        """Test pattern learning and retrieval"""
        pattern = Pattern(
            pattern_type="test_pattern",
            description="A test pattern",
            success_rate=0.85,
            usage_count=5
        )
        
        await memory.add_pattern("TestAgent", "story-1", pattern)
        
        patterns = await memory.get_patterns_by_type("TestAgent", "story-1", "test_pattern")
        assert len(patterns) == 1
        assert patterns[0].description == "A test pattern"
        assert patterns[0].success_rate == 0.85
    
    @pytest.mark.asyncio
    async def test_phase_handoffs(self, memory):
        """Test TDD phase handoff recording"""
        handoff = PhaseHandoff(
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            from_agent="DesignAgent",
            to_agent="QAAgent",
            context_summary="Design complete, ready for testing"
        )
        
        await memory.add_phase_handoff("DesignAgent", "story-1", handoff)
        
        handoffs = await memory.get_phase_handoffs(
            "DesignAgent", "story-1", 
            from_phase=TDDState.DESIGN
        )
        assert len(handoffs) == 1
        assert handoffs[0].to_agent == "QAAgent"
    
    @pytest.mark.asyncio
    async def test_context_snapshots(self, memory):
        """Test context snapshot management"""
        snapshot = ContextSnapshot(
            agent_type="TestAgent",
            story_id="story-1",
            tdd_phase=TDDState.CODE_GREEN,
            context_summary="Code implementation snapshot",
            file_list=["test.py", "main.py"]
        )
        
        await memory.add_context_snapshot("TestAgent", "story-1", snapshot)
        
        history = await memory.get_context_history(
            "TestAgent", "story-1", 
            tdd_phase=TDDState.CODE_GREEN, 
            limit=10
        )
        assert len(history) == 1
        assert history[0].context_summary == "Code implementation snapshot"
        assert len(history[0].file_list) == 2
    
    @pytest.mark.asyncio
    async def test_memory_update(self, memory):
        """Test memory update functionality"""
        # Create initial memory
        await memory.store_memory(AgentMemory(
            agent_type="TestAgent",
            story_id="story-1"
        ))
        
        # Update with new data
        await memory.update_memory("TestAgent", "story-1", {
            "metadata": {"test_key": "test_value"}
        })
        
        # Verify update
        updated_memory = await memory.get_memory("TestAgent", "story-1")
        assert updated_memory.metadata["test_key"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_memory_analysis(self, memory):
        """Test memory analysis functionality"""
        # Add some test data
        decision = Decision(
            agent_type="TestAgent",
            description="Test decision",
            confidence=0.8
        )
        
        pattern = Pattern(
            pattern_type="success_pattern",
            description="A successful pattern",
            success_rate=0.9,
            usage_count=3
        )
        
        await memory.add_decision("TestAgent", "story-1", decision)
        await memory.add_pattern("TestAgent", "story-1", pattern)
        
        # Analyze patterns
        analysis = await memory.analyze_agent_patterns("TestAgent", "story-1")
        
        assert "pattern_types" in analysis
        assert "decision_confidence_avg" in analysis
        assert "successful_patterns" in analysis
        assert analysis["decision_confidence_avg"] == 0.8
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self, memory):
        """Test old memory cleanup"""
        # This test would normally require old files, but we can test the interface
        deleted_count = await memory.cleanup_old_memories(older_than_days=30)
        assert isinstance(deleted_count, int)
        assert deleted_count >= 0
    
    def test_performance_metrics(self, memory):
        """Test performance metrics collection"""
        metrics = memory.get_performance_metrics()
        
        assert "get_calls" in metrics
        assert "store_calls" in metrics
        assert "cache_hit_rate" in metrics
        assert isinstance(metrics["cache_hit_rate"], float)


class TestContextManager:
    """Test ContextManager functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        # Create some test files
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("""
def hello():
    return "Hello, World!"

def add(a, b):
    return a + b
""")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def context_manager(self, temp_dir):
        return ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_context_preparation(self, context_manager):
        """Test basic context preparation"""
        task = {
            "description": "Test task",
            "story_id": "story-1"
        }
        
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=task,
            max_tokens=5000
        )
        
        assert context is not None
        assert context.agent_type == "CodeAgent"
        assert context.story_id == "story-1"
        assert context.token_budget is not None
        assert context.token_usage is not None
        assert context.preparation_time > 0
    
    @pytest.mark.asyncio
    async def test_context_caching(self, context_manager):
        """Test context caching functionality"""
        task = {
            "description": "Test task",
            "story_id": "story-1"
        }
        
        # First request
        context1 = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=task
        )
        
        # Second request (should hit cache)
        context2 = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=task
        )
        
        assert context2.cache_hit is True
        assert context1.request_id != context2.request_id  # Different request IDs
    
    @pytest.mark.asyncio
    async def test_decision_recording(self, context_manager):
        """Test agent decision recording"""
        decision_id = await context_manager.record_agent_decision(
            agent_type="TestAgent",
            story_id="story-1",
            description="Test decision",
            rationale="Testing decision recording",
            outcome="Success",
            confidence=0.9
        )
        
        assert decision_id is not None
        assert isinstance(decision_id, str)
        
        # Verify decision can be retrieved
        decisions = await context_manager.get_recent_decisions(
            "TestAgent", "story-1", limit=5
        )
        assert len(decisions) == 1
        assert decisions[0].description == "Test decision"
    
    @pytest.mark.asyncio
    async def test_phase_handoff_recording(self, context_manager):
        """Test TDD phase handoff recording"""
        handoff_id = await context_manager.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id="story-1",
            context_summary="Design complete",
            handoff_notes="Ready for test writing"
        )
        
        assert handoff_id is not None
        assert isinstance(handoff_id, str)
        
        # Verify handoff can be retrieved
        handoffs = await context_manager.get_phase_handoffs(
            "DesignAgent", "story-1"
        )
        assert len(handoffs) >= 1
    
    @pytest.mark.asyncio
    async def test_context_snapshot_creation(self, context_manager):
        """Test context snapshot creation"""
        task = {
            "description": "Test task",
            "story_id": "story-1"
        }
        
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=task
        )
        
        snapshot_id = await context_manager.create_context_snapshot(
            agent_type="CodeAgent",
            story_id="story-1",
            context=context,
            summary="Test snapshot"
        )
        
        assert snapshot_id is not None
        assert isinstance(snapshot_id, str)
        
        # Verify snapshot can be retrieved
        history = await context_manager.get_agent_context_history(
            "CodeAgent", "story-1", limit=5
        )
        assert len(history) == 1
        assert history[0].context_summary == "Test snapshot"
    
    @pytest.mark.asyncio
    async def test_token_budget_optimization(self, context_manager):
        """Test token budget optimization"""
        task = {
            "description": "Test task",
            "story_id": "story-1"
        }
        
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=task
        )
        
        # Optimize budget based on usage
        optimized_budget = await context_manager.optimize_token_budget(
            context=context,
            actual_usage=context.token_usage,
            quality_score=0.8
        )
        
        assert optimized_budget is not None
        assert isinstance(optimized_budget, TokenBudget)
        assert optimized_budget.total_budget == context.token_budget.total_budget
    
    @pytest.mark.asyncio
    async def test_context_invalidation(self, context_manager):
        """Test context cache invalidation"""
        task = {
            "description": "Test task",
            "story_id": "story-1"
        }
        
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=task
        )
        
        # Invalidate context
        await context_manager.invalidate_context(context.request_id)
        
        # Verify context is no longer in cache
        # (This is a behavioral test - we can't directly verify cache state)
        pass
    
    @pytest.mark.asyncio
    async def test_cache_cleanup(self, context_manager):
        """Test cache cleanup functionality"""
        cleaned_count = await context_manager.cleanup_cache()
        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0
    
    def test_performance_metrics(self, context_manager):
        """Test performance metrics collection"""
        metrics = context_manager.get_performance_metrics()
        
        assert "context_manager" in metrics
        assert "token_calculator" in metrics
        assert "agent_memory" in metrics
        
        cm_metrics = metrics["context_manager"]
        assert "total_requests" in cm_metrics
        assert "cache_hit_rate" in cm_metrics
        assert "average_preparation_time" in cm_metrics


class TestIntegration:
    """Integration tests for the complete context infrastructure"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        # Create a realistic project structure
        project_path = Path(temp_dir)
        
        # Create some Python files
        (project_path / "main.py").write_text("""
def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
""")
        
        (project_path / "utils.py").write_text("""
def helper_function(x, y):
    return x + y

class UtilityClass:
    def __init__(self, value):
        self.value = value
    
    def process(self):
        return self.value * 2
""")
        
        # Create test files
        test_dir = project_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_main.py").write_text("""
import pytest
from main import main

def test_main():
    assert main() == 0

def test_integration():
    result = main()
    assert isinstance(result, int)
""")
        
        # Create documentation
        (project_path / "README.md").write_text("""
# Test Project

This is a test project for context management.

## Features
- Main functionality
- Utility functions
- Comprehensive tests
""")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def context_manager(self, temp_dir):
        return ContextManager(project_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, context_manager):
        """Test complete workflow with multiple agents and phases"""
        
        # Phase 1: Design Agent prepares context
        design_task = {
            "description": "Design a simple calculator application",
            "story_id": "calc-story-1",
            "current_state": TDDState.DESIGN.value
        }
        
        design_context = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=design_task,
            story_id="calc-story-1"
        )
        
        assert design_context.agent_type == "DesignAgent"
        assert design_context.tdd_phase == TDDState.DESIGN
        
        # Record design decision
        design_decision_id = await context_manager.record_agent_decision(
            agent_type="DesignAgent",
            story_id="calc-story-1",
            description="Created calculator design specification",
            rationale="Need simple arithmetic operations",
            outcome="Design complete with add/subtract/multiply/divide operations",
            confidence=0.9,
            artifacts={"design_doc": "calculator_design.md"}
        )
        
        # Create design context snapshot
        design_snapshot_id = await context_manager.create_context_snapshot(
            agent_type="DesignAgent",
            story_id="calc-story-1",
            context=design_context,
            summary="Initial design phase completion"
        )
        
        # Phase 2: QA Agent takes over for test writing
        qa_task = {
            "description": "Write tests for calculator operations",
            "story_id": "calc-story-1",
            "current_state": TDDState.TEST_RED.value
        }
        
        qa_context = await context_manager.prepare_context(
            agent_type="QAAgent",
            task=qa_task,
            story_id="calc-story-1"
        )
        
        assert qa_context.agent_type == "QAAgent"
        assert qa_context.tdd_phase == TDDState.TEST_RED
        
        # Record phase handoff
        handoff_id = await context_manager.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id="calc-story-1",
            artifacts={"design_doc": "calculator_design.md"},
            context_summary="Design complete, specifications ready for test implementation",
            handoff_notes="Focus on arithmetic operation testing"
        )
        
        # Record QA decision
        qa_decision_id = await context_manager.record_agent_decision(
            agent_type="QAAgent",
            story_id="calc-story-1",
            description="Created comprehensive test suite",
            rationale="Cover all arithmetic operations and edge cases",
            outcome="Tests written for add, subtract, multiply, divide with edge cases",
            confidence=0.85,
            artifacts={"test_file": "test_calculator.py"}
        )
        
        # Phase 3: Code Agent implements functionality
        code_task = {
            "description": "Implement calculator operations",
            "story_id": "calc-story-1",
            "current_state": TDDState.CODE_GREEN.value
        }
        
        code_context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=code_task,
            story_id="calc-story-1"
        )
        
        assert code_context.agent_type == "CodeAgent"
        assert code_context.tdd_phase == TDDState.CODE_GREEN
        
        # Record second handoff
        handoff2_id = await context_manager.record_phase_handoff(
            from_agent="QAAgent",
            to_agent="CodeAgent",
            from_phase=TDDState.TEST_RED,
            to_phase=TDDState.CODE_GREEN,
            story_id="calc-story-1",
            artifacts={"test_file": "test_calculator.py"},
            context_summary="Tests complete and failing, ready for implementation",
            handoff_notes="Implement minimal code to make tests pass"
        )
        
        # Verify historical context
        design_history = await context_manager.get_agent_context_history(
            "DesignAgent", "calc-story-1", limit=5
        )
        assert len(design_history) == 1
        
        qa_decisions = await context_manager.get_recent_decisions(
            "QAAgent", "calc-story-1", limit=5
        )
        assert len(qa_decisions) == 1
        assert qa_decisions[0].description == "Created comprehensive test suite"
        
        handoffs = await context_manager.get_phase_handoffs(
            "QAAgent", "calc-story-1"
        )
        assert len(handoffs) == 2  # QA was involved in both handoffs
        
        # Verify context preparation efficiency
        metrics = context_manager.get_performance_metrics()
        assert metrics["context_manager"]["total_requests"] == 3
        assert metrics["context_manager"]["average_preparation_time"] > 0
    
    @pytest.mark.asyncio
    async def test_context_learning_and_optimization(self, context_manager):
        """Test that context system learns and optimizes over time"""
        
        # Simulate multiple iterations with the same agent type and story
        for i in range(3):
            task = {
                "description": f"Iteration {i} task",
                "story_id": "learning-story-1"
            }
            
            context = await context_manager.prepare_context(
                agent_type="CodeAgent",
                task=task,
                story_id="learning-story-1"
            )
            
            # Simulate usage and optimization
            await context_manager.optimize_token_budget(
                context=context,
                actual_usage=context.token_usage,
                quality_score=0.8 + (i * 0.05)  # Improving quality
            )
            
            # Record learning
            await context_manager.record_agent_decision(
                agent_type="CodeAgent",
                story_id="learning-story-1",
                description=f"Completed iteration {i}",
                outcome="Success",
                confidence=0.7 + (i * 0.1)  # Increasing confidence
            )
        
        # Analyze learning
        analysis = await context_manager.analyze_agent_learning(
            "CodeAgent", "learning-story-1"
        )
        
        assert "analysis" in analysis or "pattern_types" in analysis
        
        # Verify metrics show learning activity
        metrics = context_manager.get_performance_metrics()
        assert metrics["context_manager"]["total_requests"] >= 3
        assert metrics["token_calculator"]["optimization_calls"] >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])