#!/usr/bin/env python3
"""
Simple test runner for AI Agent TDD-Scrum Workflow system.
Validates core functionality without external dependencies.
"""

import sys
import asyncio
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_imports():
    """Test that all core modules can be imported"""
    print("Testing imports...")
    
    try:
        from state_machine import StateMachine, State, CommandResult
        print("✓ State machine imports successful")
    except Exception as e:
        print(f"✗ State machine import failed: {e}")
        return False
    
    try:
        from agents import BaseAgent, Task, TaskStatus, AgentResult
        print("✓ Agents import successful")
    except Exception as e:
        print(f"✗ Agents import failed: {e}")
        return False
    
    try:
        from claude_client import ClaudeCodeClient
        print("✓ Claude client import successful")
    except Exception as e:
        print(f"✗ Claude client import failed: {e}")
        return False
    
    try:
        from orchestrator import Orchestrator
        print("✓ Orchestrator import successful")
    except Exception as e:
        print(f"✗ Orchestrator import failed: {e}")
        return False
    
    return True

def test_state_machine():
    """Test basic state machine functionality"""
    print("\nTesting state machine...")
    
    try:
        from state_machine import StateMachine, State
        
        sm = StateMachine()
        
        # Test initial state
        assert sm.current_state == State.IDLE, f"Expected IDLE, got {sm.current_state}"
        print("✓ Initial state is IDLE")
        
        # Test valid transition
        result = sm.transition("/epic")
        assert result.success, f"Epic transition failed: {result.error_message}"
        assert sm.current_state == State.BACKLOG_READY, f"Expected BACKLOG_READY, got {sm.current_state}"
        print("✓ Epic transition successful")
        
        # Test invalid transition
        result = sm.validate_command("/sprint start")
        assert not result.success, "Sprint start should be invalid from BACKLOG_READY"
        print("✓ Invalid transition properly rejected")
        
        # Test allowed commands
        allowed = sm.get_allowed_commands()
        assert "/approve" in allowed, "/approve should be allowed in BACKLOG_READY"
        assert "/sprint plan" in allowed, "/sprint plan should be allowed in BACKLOG_READY"
        print("✓ Allowed commands correct")
        
        return True
        
    except Exception as e:
        print(f"✗ State machine test failed: {e}")
        return False

def test_agents():
    """Test basic agent functionality"""
    print("\nTesting agents...")
    
    try:
        from agents import DesignAgent, CodeAgent, QAAgent, DataAgent, Task, TaskStatus
        
        # Test agent creation
        design_agent = DesignAgent()
        assert design_agent.name == "DesignAgent"
        print("✓ DesignAgent created successfully")
        
        code_agent = CodeAgent()
        assert code_agent.name == "CodeAgent"
        print("✓ CodeAgent created successfully")
        
        qa_agent = QAAgent()
        assert qa_agent.name == "QAAgent"
        print("✓ QAAgent created successfully")
        
        data_agent = DataAgent()
        assert data_agent.name == "DataAgent"
        print("✓ DataAgent created successfully")
        
        # Test task creation
        task = Task(
            id="test-task",
            agent_type="DesignAgent",
            command="Test command",
            context={"test": "value"}
        )
        assert task.status == TaskStatus.PENDING
        print("✓ Task created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Agents test failed: {e}")
        return False

async def test_claude_client():
    """Test Claude Code client"""
    print("\nTesting Claude Code client...")
    
    try:
        from claude_client import ClaudeCodeClient
        
        client = ClaudeCodeClient()
        print(f"✓ Claude client created (available: {client.available})")
        
        # Test code generation (will use fallback if Claude not available)
        result = await client.generate_code("Create a simple hello world function")
        assert isinstance(result, str), "Code generation should return string"
        assert len(result) > 0, "Code generation should return non-empty string"
        print("✓ Code generation works (with fallback if needed)")
        
        return True
        
    except Exception as e:
        print(f"✗ Claude client test failed: {e}")
        return False

async def test_orchestrator():
    """Test basic orchestrator functionality"""
    print("\nTesting orchestrator...")
    
    try:
        from orchestrator import Orchestrator
        
        # Create orchestrator with default config
        orch = Orchestrator()
        assert len(orch.projects) > 0, "Should have at least default project"
        print("✓ Orchestrator created with projects")
        
        # Test command handling
        result = await orch.handle_command("/state", "default")
        assert result["success"], f"State command failed: {result.get('error')}"
        print("✓ State command successful")
        
        # Test epic command
        result = await orch.handle_command("/epic", "default", description="Test epic")
        assert result["success"], f"Epic command failed: {result.get('error')}"
        print("✓ Epic command successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Orchestrator test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("AI Agent TDD-Scrum Workflow - System Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 5
    
    # Test imports
    if test_imports():
        tests_passed += 1
    
    # Test state machine
    if test_state_machine():
        tests_passed += 1
    
    # Test agents
    if test_agents():
        tests_passed += 1
    
    # Test Claude client
    if await test_claude_client():
        tests_passed += 1
    
    # Test orchestrator
    if await test_orchestrator():
        tests_passed += 1
    
    print(f"\n{'=' * 50}")
    print(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! System is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)