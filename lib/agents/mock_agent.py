"""
Mock Agent Implementation for NO-AGENT Mode

Provides mock implementations of all agent types that simulate agent
execution without making actual AI calls. Used for testing state machine
logic and data flow validation.
"""

import asyncio
import random
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from . import BaseAgent, Task, TaskStatus, AgentResult, TDDState, TDDCycle, TDDTask, TestResult

logger = logging.getLogger(__name__)


class MockAgent(BaseAgent):
    """
    Mock implementation of BaseAgent that simulates real agent behavior
    without making actual AI calls.
    
    Provides realistic delays, success/failure rates, and logging to
    validate state machine execution and data flow.
    """
    
    def __init__(self, agent_type: str, capabilities: List[str] = None, context_manager: Optional[Any] = None):
        super().__init__(
            name=f"Mock{agent_type}",
            capabilities=capabilities or [
                f"mock_{agent_type.lower()}_task",
                "mock_execution", 
                "mock_validation"
            ],
            context_manager=context_manager
        )
        self.agent_type = agent_type
        self.execution_count = 0
        self.failure_rate = 0.1  # 10% simulated failure rate
        self.success_rate = 0.95  # 95% success rate for realistic simulation
        
    async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
        """Execute mock task with realistic simulation"""
        start_time = time.time()
        self.execution_count += 1
        
        logger.info(f"Mock{self.agent_type} executing task: {task.command}")
        
        try:
            # Simulate processing time based on agent type
            processing_time = self._get_processing_time(task.command)
            
            if not dry_run:
                await asyncio.sleep(processing_time)
            
            # Simulate occasional failures for testing
            if random.random() >= self.success_rate:
                return self._create_failure_result(task, processing_time)
            
            # Generate mock response based on task type
            response = self._generate_mock_response(task)
            
            result = AgentResult(
                success=True,
                output=response,
                artifacts={
                    "mock_data.json": f'{{"mock_execution": true, "agent_type": "{self.agent_type}", "execution_count": {self.execution_count}, "processing_time": {processing_time}}}'
                },
                execution_time=time.time() - start_time
            )
            
            logger.info(f"Mock{self.agent_type} completed task successfully")
            return result
            
        except Exception as e:
            logger.error(f"Mock{self.agent_type} error: {str(e)}")
            return AgentResult(
                success=False,
                output="",
                error=f"Mock execution error: {str(e)}",
                artifacts={"mock_error.json": f'{{"mock_execution": true, "agent_type": "{self.agent_type}"}}'}, 
                execution_time=time.time() - start_time
            )
    
    def _get_processing_time(self, command: str) -> float:
        """Get realistic processing time based on command type"""
        command_lower = command.lower()
        
        if "design" in command_lower or "spec" in command_lower:
            return random.uniform(1.5, 3.0)  # Design tasks: 1.5-3s
        elif "test" in command_lower:
            return random.uniform(2.0, 4.0)  # Test tasks: 2-4s
        elif "implement" in command_lower or "code" in command_lower:
            return random.uniform(3.0, 6.0)  # Code tasks: 3-6s
        elif "refactor" in command_lower:
            return random.uniform(2.0, 4.0)  # Refactor tasks: 2-4s
        elif "analyze" in command_lower or "review" in command_lower:
            return random.uniform(1.0, 2.5)  # Analysis tasks: 1-2.5s
        else:
            return random.uniform(1.0, 3.0)  # Default: 1-3s
    
    def _create_failure_result(self, task: Task, processing_time: float) -> AgentResult:
        """Create a realistic failure result for testing"""
        failure_messages = [
            f"Mock{self.agent_type}: Simulated failure for testing",
            f"Mock{self.agent_type}: Temporary resource unavailable",
            f"Mock{self.agent_type}: Validation error in mock execution",
            f"Mock{self.agent_type}: Simulated timeout condition"
        ]
        
        return AgentResult(
            success=False,
            output="",
            error=random.choice(failure_messages),
            artifacts={
                "mock_failure.json": f'{{"mock_execution": true, "agent_type": "{self.agent_type}", "failure_simulation": true, "processing_time": {processing_time}}}'
            },
            execution_time=processing_time
        )
    
    def _generate_mock_response(self, task: Task) -> str:
        """Generate realistic mock response based on task"""
        command = task.command.lower()
        context = task.context or {}
        
        if "design" in command or "spec" in command:
            return self._mock_design_response(context)
        elif "test" in command and "red" in command:
            return self._mock_test_red_response(context)
        elif "refactor" in command:
            return self._mock_refactor_response(context)
        elif "implement" in command or "code" in command:
            return self._mock_code_response(context)
        elif "analyze" in command or "review" in command:
            return self._mock_analysis_response(context)
        else:
            return f"Mock{self.agent_type}: Task '{task.command}' completed successfully"
    
    def _mock_design_response(self, context: Dict[str, Any]) -> str:
        """Generate mock design/specification response"""
        story_id = context.get("story_id", "STORY-XXX")
        requirements = context.get("requirements", "Mock requirements")
        return f"""Mock{self.agent_type}: Design specifications completed for {story_id}

# Mock Technical Specification

## Overview
Mock implementation specifications generated for testing purposes.
Requirements: {requirements}

## Acceptance Criteria
- ✅ Mock criteria 1: Basic functionality validated
- ✅ Mock criteria 2: Error handling specifications
- ✅ Mock criteria 3: Integration requirements defined

## API Design
```python
def mock_function():
    # Mock implementation placeholder
    pass
```

## Implementation Notes
This is a mock design output for state machine validation.
Real design agent would provide detailed technical specifications.
"""
    
    def _mock_test_red_response(self, context: Dict[str, Any]) -> str:
        """Generate mock failing test response"""
        story_id = context.get("story_id", "STORY-XXX")
        return f"""MockQAAgent: Failing tests created for {story_id}

# Mock Test Suite Created

## Test Files Generated
- tests/tdd/{story_id}/test_mock_functionality.py
- tests/tdd/{story_id}/test_mock_integration.py
- tests/tdd/{story_id}/test_mock_edge_cases.py

## Test Results (RED State)
```
===== test session starts =====
collected 5 items

tests/tdd/{story_id}/test_mock_functionality.py FAILED
tests/tdd/{story_id}/test_mock_integration.py FAILED  
tests/tdd/{story_id}/test_mock_edge_cases.py FAILED

===== 5 failed, 0 passed =====
```

Tests are properly failing as expected for TDD RED phase.
Ready for implementation in CODE_GREEN phase.
"""
    
    def _mock_code_response(self, context: Dict[str, Any]) -> str:
        """Generate mock code implementation response"""
        story_id = context.get("story_id", "STORY-XXX")
        return f"""MockCodeAgent: Implementation completed for {story_id}

# Mock Implementation Generated

## Files Modified
- src/mock_module.py (created)
- src/mock_service.py (created)
- src/__init__.py (updated)

## Test Results (GREEN State)
```
===== test session starts =====
collected 5 items

tests/tdd/{story_id}/test_mock_functionality.py PASSED
tests/tdd/{story_id}/test_mock_integration.py PASSED
tests/tdd/{story_id}/test_mock_edge_cases.py PASSED

===== 5 passed, 0 failed =====
```

Minimal implementation created to make all tests pass.
Ready for REFACTOR phase to improve code quality.
"""
    
    def _mock_refactor_response(self, context: Dict[str, Any]) -> str:
        """Generate mock refactoring response"""
        story_id = context.get("story_id", "STORY-XXX") 
        # Use CodeAgent branding for refactor responses as they typically come from code agents
        agent_name = "MockCodeAgent" if self.agent_type != "CodeAgent" else f"Mock{self.agent_type}"
        return f"""{agent_name}: Refactoring completed for {story_id}

# Mock Refactoring Summary

## Improvements Made
- ✅ Code organization and structure improved
- ✅ Error handling enhanced
- ✅ Performance optimizations applied
- ✅ Documentation updated

## Test Results (Still GREEN)
```
===== test session starts =====
collected 5 items

tests/tdd/{story_id}/test_mock_functionality.py PASSED
tests/tdd/{story_id}/test_mock_integration.py PASSED
tests/tdd/{story_id}/test_mock_edge_cases.py PASSED

===== 5 passed, 0 failed =====
```

All tests remain passing after refactoring.
Code quality improved while maintaining functionality.
Ready for COMMIT phase.
"""
    
    def _mock_analysis_response(self, context: Dict[str, Any]) -> str:
        """Generate mock analysis/review response"""
        return f"""Mock{self.agent_type}: Analysis completed

# Mock Analysis Results

## Quality Metrics
- Code coverage: 95% (mock)
- Complexity score: 7.2/10 (mock)
- Security scan: 0 issues (mock)
- Performance: Good (mock)

## Recommendations
- Mock recommendation 1: Consider additional edge cases
- Mock recommendation 2: Add integration tests
- Mock recommendation 3: Update documentation

This is a mock analysis for state machine validation.
"""
    


class MockDesignAgent(MockAgent):
    """Mock Design Agent specialized for TDD DESIGN phase"""
    
    def __init__(self, context_manager: Optional[Any] = None):
        super().__init__(
            "DesignAgent",
            capabilities=[
                "tdd_specification",
                "acceptance_criteria", 
                "technical_design",
                "api_design",
                "mock_design"
            ],
            context_manager=context_manager
        )


class MockQAAgent(MockAgent):
    """Mock QA Agent specialized for TDD TEST_RED phase"""
    
    def __init__(self, context_manager: Optional[Any] = None):
        super().__init__(
            "QAAgent", 
            capabilities=[
                "failing_test_creation",
                "test_validation",
                "red_state_verification",
                "test_organization",
                "mock_testing"
            ],
            context_manager=context_manager
        )


class MockCodeAgent(MockAgent):
    """Mock Code Agent specialized for TDD CODE_GREEN and REFACTOR phases"""
    
    def __init__(self, context_manager: Optional[Any] = None):
        super().__init__(
            "CodeAgent",
            capabilities=[
                "minimal_implementation",
                "test_green_validation", 
                "code_refactoring",
                "tdd_commits",
                "mock_implementation"
            ],
            context_manager=context_manager
        )


class MockDataAgent(MockAgent):
    """Mock Data/Analytics Agent for cross-story analysis"""
    
    def __init__(self, context_manager: Optional[Any] = None):
        super().__init__(
            "DataAgent",
            capabilities=[
                "tdd_metrics_analysis",
                "performance_tracking",
                "quality_reporting",
                "mock_analytics"
            ],
            context_manager=context_manager
        )


def create_mock_agent(agent_type: str, context_manager: Optional[Any] = None) -> MockAgent:
    """Factory function to create appropriate mock agent"""
    agent_type_lower = agent_type.lower()
    
    if "design" in agent_type_lower:
        return MockDesignAgent(context_manager=context_manager)
    elif "qa" in agent_type_lower or "test" in agent_type_lower:
        return MockQAAgent(context_manager=context_manager)
    elif "code" in agent_type_lower:
        return MockCodeAgent(context_manager=context_manager)
    elif "data" in agent_type_lower or "analytics" in agent_type_lower:
        return MockDataAgent(context_manager=context_manager)
    else:
        return MockAgent(agent_type, context_manager=context_manager)


# Export for easy importing
__all__ = [
    'MockAgent',
    'MockDesignAgent', 
    'MockQAAgent',
    'MockCodeAgent',
    'MockDataAgent',
    'create_mock_agent'
]