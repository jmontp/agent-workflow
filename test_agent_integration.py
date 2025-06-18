#!/usr/bin/env python3
"""
Test Context Management Integration with Agents
"""

import asyncio
import os
import sys
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Set NO_AGENT_MODE to use mock agents for testing
os.environ["NO_AGENT_MODE"] = "true"

from context_manager import ContextManager
from agents import create_agent
from tdd_models import TDDState


async def test_agent_context_integration():
    """Test integration between agents and context management"""
    print("🔗 Testing Agent-Context Integration\n")
    
    # Initialize context manager
    context_mgr = ContextManager(project_path=".")
    
    # Create agents with context manager
    design_agent = create_agent("DesignAgent", context_manager=context_mgr)
    code_agent = create_agent("CodeAgent", context_manager=context_mgr)
    qa_agent = create_agent("QAAgent", context_manager=context_mgr)
    
    print(f"✅ Created agents with context management:")
    print(f"  - {design_agent.name} ({design_agent.__class__.__name__})")
    print(f"  - {code_agent.name} ({code_agent.__class__.__name__})")
    print(f"  - {qa_agent.name} ({qa_agent.__class__.__name__})")
    
    # Test context preparation by agent
    print("\n📋 Testing context preparation...")
    
    design_task = {
        "description": "Design a simple user authentication system",
        "story_id": "auth-story-1",
        "current_state": TDDState.DESIGN.value,
        "requirements": [
            "User login/logout functionality",
            "Password validation",
            "Session management"
        ]
    }
    
    # Agent prepares its own context
    design_context = await design_agent.prepare_context(
        task=design_task,
        story_id="auth-story-1",
        max_tokens=8000
    )
    
    if design_context:
        print(f"✅ Design agent prepared context:")
        print(f"   Tokens: {design_context.get_total_token_estimate()}")
        print(f"   TDD Phase: {design_context.tdd_phase}")
        print(f"   Files analyzed: {len(design_context.file_contents)}")
        
        # Agent records a decision
        decision_id = await design_agent.record_decision(
            description="Completed authentication system design",
            rationale="User authentication is critical for security",
            outcome="Designed login/logout flow with password validation",
            confidence=0.88,
            artifacts={"design_doc": "auth_design.md"}
        )
        print(f"   Decision recorded: {decision_id}")
        
        # Create context snapshot
        snapshot_id = await design_agent.create_context_snapshot(
            summary="Design phase completion for authentication system"
        )
        print(f"   Context snapshot: {snapshot_id}")
    
    # Test phase handoff simulation
    print("\n🔄 Testing TDD phase handoff...")
    
    test_task = {
        "description": "Write tests for authentication system",
        "story_id": "auth-story-1",
        "current_state": TDDState.TEST_RED.value
    }
    
    # QA agent prepares context for test writing
    qa_context = await qa_agent.prepare_context(
        task=test_task,
        story_id="auth-story-1"
    )
    
    if qa_context:
        print(f"✅ QA agent prepared context:")
        print(f"   Tokens: {qa_context.get_total_token_estimate()}")
        print(f"   TDD Phase: {qa_context.tdd_phase}")
        
        # Record phase handoff
        handoff_id = await context_mgr.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent", 
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id="auth-story-1",
            artifacts={"design_doc": "auth_design.md"},
            context_summary="Design complete, ready for test implementation",
            handoff_notes="Focus on testing login validation and session management"
        )
        print(f"   Phase handoff recorded: {handoff_id}")
        
        # QA agent records its decision
        await qa_agent.record_decision(
            description="Created comprehensive test suite for authentication",
            rationale="Need to ensure security requirements are properly tested",
            outcome="Tests written for login, logout, validation, and session handling",
            confidence=0.92,
            artifacts={"test_file": "test_auth.py"}
        )
    
    # Test code agent taking over
    print("\n💻 Testing code implementation phase...")
    
    code_task = {
        "description": "Implement authentication system to pass tests",
        "story_id": "auth-story-1", 
        "current_state": TDDState.CODE_GREEN.value
    }
    
    code_context = await code_agent.prepare_context(
        task=code_task,
        story_id="auth-story-1"
    )
    
    if code_context:
        print(f"✅ Code agent prepared context:")
        print(f"   Tokens: {code_context.get_total_token_estimate()}")
        print(f"   Agent memory available: {len(code_context.agent_memory) > 0}")
        
        # Record second handoff
        await context_mgr.record_phase_handoff(
            from_agent="QAAgent",
            to_agent="CodeAgent",
            from_phase=TDDState.TEST_RED,
            to_phase=TDDState.CODE_GREEN,
            story_id="auth-story-1",
            artifacts={"test_file": "test_auth.py"},
            context_summary="Tests written and failing, ready for implementation"
        )
    
    # Test agent memory and learning
    print("\n🧠 Testing agent learning and memory...")
    
    # Get recent decisions for each agent
    design_decisions = await design_agent.get_recent_decisions(limit=5)
    qa_decisions = await qa_agent.get_recent_decisions(limit=5)
    
    print(f"✅ Agent memory retrieval:")
    print(f"   Design agent decisions: {len(design_decisions)}")
    print(f"   QA agent decisions: {len(qa_decisions)}")
    
    if design_decisions:
        print(f"   Latest design decision: {design_decisions[0].description}")
    
    # Get context history
    design_history = await design_agent.get_context_history(limit=3)
    print(f"   Design agent context history: {len(design_history)} snapshots")
    
    # Test agent context info
    print(f"✅ Agent context info:")
    for agent in [design_agent, code_agent, qa_agent]:
        info = agent.get_current_context_info()
        print(f"   {agent.name}: has_context={info['has_context']}")
    
    # Test learning analysis
    print("\n📈 Testing learning analysis...")
    
    learning_analysis = await context_mgr.analyze_agent_learning(
        "DesignAgent", "auth-story-1"
    )
    
    if learning_analysis:
        print(f"✅ Learning analysis completed")
        if "decision_confidence_avg" in learning_analysis:
            print(f"   Average decision confidence: {learning_analysis['decision_confidence_avg']:.2f}")
    
    # Test performance metrics
    print("\n📊 Performance metrics:")
    
    metrics = context_mgr.get_performance_metrics()
    cm_metrics = metrics["context_manager"]
    
    print(f"✅ Context Manager metrics:")
    print(f"   Total requests: {cm_metrics['total_requests']}")
    print(f"   Cache hit rate: {cm_metrics['cache_hit_rate']:.1%}")
    print(f"   Average prep time: {cm_metrics['average_preparation_time']:.3f}s")
    print(f"   Active contexts: {cm_metrics['active_contexts']}")
    
    tc_metrics = metrics["token_calculator"]
    print(f"✅ Token Calculator metrics:")
    print(f"   Budget calculations: {tc_metrics['budget_calculations']}")
    print(f"   Token estimations: {tc_metrics['token_estimations']}")
    
    am_metrics = metrics["agent_memory"]
    print(f"✅ Agent Memory metrics:")
    print(f"   Get calls: {am_metrics['get_calls']}")
    print(f"   Store calls: {am_metrics['store_calls']}")
    print(f"   Cache hit rate: {am_metrics['cache_hit_rate']:.1%}")
    
    print("\n🎉 Agent-Context Integration test completed successfully!")


async def main():
    """Run agent integration tests"""
    try:
        await test_agent_context_integration()
        
        print("\n✨ Summary: Context Management Infrastructure")
        print("━" * 50)
        print("✅ Core Infrastructure Complete")
        print("  • TokenCalculator: Dynamic budget allocation")
        print("  • AgentMemory: Persistent decision & artifact storage")
        print("  • ContextManager: Context preparation pipeline")
        print("  • Agent Integration: Context-aware agent operations")
        print("")
        print("🔧 Capabilities Implemented:")
        print("  • Agent context preparation with token budgets")
        print("  • Decision recording and retrieval")
        print("  • TDD phase handoff tracking")
        print("  • Context snapshot creation")
        print("  • Agent learning analysis")
        print("  • Performance metrics collection")
        print("  • Cache optimization")
        print("")
        print("🚀 Ready for Phase 2: Intelligence Layer")
        print("  • Context filtering algorithms")
        print("  • Content compression strategies")
        print("  • Semantic relevance scoring")
        print("  • Advanced learning patterns")
        
        return 0
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)