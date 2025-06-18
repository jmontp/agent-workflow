#!/usr/bin/env python3
"""
Basic test of context management infrastructure
"""

import asyncio
import sys
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from context_manager import ContextManager
from token_calculator import TokenCalculator
from agent_memory import FileBasedAgentMemory


async def test_token_calculator():
    """Test TokenCalculator basic functionality"""
    print("Testing TokenCalculator...")
    
    calc = TokenCalculator(max_tokens=50000)
    
    # Test budget calculation
    budget = await calc.calculate_budget(
        total_tokens=10000,
        agent_type="CodeAgent"
    )
    
    print(f"Budget allocated: {budget.get_allocation_dict()}")
    print(f"Utilization rate: {budget.get_utilization_rate():.2%}")
    
    # Test token estimation
    test_code = """
def hello_world():
    print("Hello, World!")
    return 42

class TestClass:
    def __init__(self):
        self.value = 100
"""
    
    tokens = await calc.estimate_tokens(test_code)
    print(f"Estimated tokens for code: {tokens}")
    
    print("✅ TokenCalculator test passed\n")


async def test_agent_memory():
    """Test AgentMemory basic functionality"""
    print("Testing AgentMemory...")
    
    memory = FileBasedAgentMemory(base_path=".test_memory")
    
    # Test memory creation and retrieval
    result = await memory.get_memory("TestAgent", "story-1")
    assert result is None, "Should return None for non-existent memory"
    
    # Test decision recording
    from context.models import Decision
    decision = Decision(
        agent_type="TestAgent",
        description="Test decision",
        rationale="Testing memory",
        outcome="Success",
        confidence=0.9
    )
    
    await memory.add_decision("TestAgent", "story-1", decision)
    
    # Retrieve decisions
    decisions = await memory.get_recent_decisions("TestAgent", "story-1", limit=5)
    assert len(decisions) == 1, f"Expected 1 decision, got {len(decisions)}"
    assert decisions[0].description == "Test decision"
    
    print(f"✅ Recorded and retrieved decision: {decisions[0].description}")
    
    # Clean up
    await memory.clear_memory("TestAgent", "story-1")
    print("✅ AgentMemory test passed\n")


async def test_context_manager():
    """Test ContextManager basic functionality"""
    print("Testing ContextManager...")
    
    context_mgr = ContextManager(project_path=".")
    
    # Test context preparation
    task = {
        "description": "Test task for context preparation",
        "story_id": "test-story-1"
    }
    
    context = await context_mgr.prepare_context(
        agent_type="CodeAgent",
        task=task,
        max_tokens=5000
    )
    
    print(f"Context prepared for {context.agent_type}")
    print(f"Token usage: {context.token_usage.total_used} tokens")
    print(f"Preparation time: {context.preparation_time:.3f}s")
    print(f"Cache hit: {context.cache_hit}")
    
    # Test decision recording
    decision_id = await context_mgr.record_agent_decision(
        agent_type="CodeAgent",
        story_id="test-story-1",
        description="Test context decision",
        outcome="Successfully tested context preparation",
        confidence=0.95
    )
    
    print(f"✅ Recorded decision: {decision_id}")
    
    # Test context snapshot
    snapshot_id = await context_mgr.create_context_snapshot(
        agent_type="CodeAgent",
        story_id="test-story-1",
        context=context,
        summary="Test snapshot of context preparation"
    )
    
    print(f"✅ Created context snapshot: {snapshot_id}")
    
    # Test performance metrics
    metrics = context_mgr.get_performance_metrics()
    print(f"Performance metrics: {metrics['context_manager']['total_requests']} requests")
    
    print("✅ ContextManager test passed\n")


async def main():
    """Run all tests"""
    print("🚀 Testing Context Management Infrastructure\n")
    
    try:
        await test_token_calculator()
        await test_agent_memory()
        await test_context_manager()
        
        print("🎉 All context infrastructure tests passed!")
        print("\n📊 Core infrastructure components working:")
        print("  ✅ TokenCalculator - Dynamic budget allocation")
        print("  ✅ AgentMemory - Persistent decision storage")
        print("  ✅ ContextManager - Context preparation pipeline")
        print("\n🔧 Ready for Phase 2: Intelligence Layer")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)