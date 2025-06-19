"""
Agent Interface Management System

Provides different agent interface implementations for the web visualizer:
- Claude Code Interface (default)
- Anthropic API Interface (direct API key)
- Mock Interface (for testing/demo)
"""

import asyncio
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading
import time

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Add lib directory to path for agent imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

try:
    from claude_client import ClaudeCodeClient
    from agent_tool_config import AgentType
except ImportError:
    # Fallback for when lib imports are not available
    ClaudeCodeClient = None
    class AgentType(Enum):
        ORCHESTRATOR = "Orchestrator"
        DESIGN = "DesignAgent"
        CODE = "CodeAgent"
        QA = "QAAgent"
        DATA = "DataAgent"

logger = logging.getLogger(__name__)


class InterfaceType(Enum):
    """Types of agent interfaces available"""
    CLAUDE_CODE = "claude_code"
    ANTHROPIC_API = "anthropic_api"
    MOCK = "mock"


class InterfaceStatus(Enum):
    """Status of an agent interface"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONFIGURING = "configuring"
    TESTING = "testing"


@dataclass
class InterfaceConfig:
    """Configuration for an agent interface"""
    interface_type: str
    enabled: bool = True
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    timeout: int = 300
    max_tokens: int = 4000
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.7
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_settings is None:
            self.custom_settings = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterfaceConfig':
        """Create from dictionary"""
        return cls(**data)
    
    def mask_sensitive_data(self) -> Dict[str, Any]:
        """Return config dict with sensitive data masked"""
        data = self.to_dict()
        if data.get('api_key'):
            data['api_key'] = f"sk-...{data['api_key'][-8:]}" if len(data['api_key']) > 8 else "sk-***"
        return data


class BaseAgentInterface(ABC):
    """Base class for agent interfaces"""
    
    def __init__(self, config: InterfaceConfig):
        self.config = config
        self.status = InterfaceStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.connection_time: Optional[float] = None
        self.request_count = 0
        self.error_count = 0
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the interface connection"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test the interface connection and return status"""
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str, agent_type: AgentType, context: Dict[str, Any] = None) -> str:
        """Generate a response using the interface"""
        pass
    
    @abstractmethod
    async def analyze_code(self, code: str, analysis_type: str = "review", agent_type: AgentType = AgentType.CODE) -> str:
        """Analyze code using the interface"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Clean shutdown of the interface"""
        pass
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current status information"""
        return {
            "interface_type": self.config.interface_type,
            "status": self.status.value,
            "last_error": self.last_error,
            "connection_time": self.connection_time,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "uptime": time.time() - self.connection_time if self.connection_time else None
        }


class ClaudeCodeInterface(BaseAgentInterface):
    """Interface using Claude Code CLI"""
    
    def __init__(self, config: InterfaceConfig):
        super().__init__(config)
        self.claude_client: Optional[ClaudeCodeClient] = None
        
    async def initialize(self) -> bool:
        """Initialize Claude Code interface"""
        try:
            self.status = InterfaceStatus.CONFIGURING
            
            if ClaudeCodeClient is None:
                raise ImportError("Claude Code client not available")
            
            # Test Claude Code availability
            self.claude_client = ClaudeCodeClient(timeout=self.config.timeout)
            
            if not self.claude_client.available:
                raise RuntimeError("Claude Code CLI not available or not working")
            
            self.status = InterfaceStatus.CONNECTED
            self.connection_time = time.time()
            self.last_error = None
            
            logger.info("Claude Code interface initialized successfully")
            return True
            
        except Exception as e:
            self.status = InterfaceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Failed to initialize Claude Code interface: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Claude Code connection"""
        try:
            self.status = InterfaceStatus.TESTING
            
            if not self.claude_client:
                raise RuntimeError("Interface not initialized")
            
            # Simple test prompt
            test_response = await self.claude_client.generate_code(
                "Write a simple hello world function in Python",
                {"language": "python"}
            )
            
            if not test_response or len(test_response.strip()) < 10:
                raise RuntimeError("Invalid response from Claude Code")
            
            self.status = InterfaceStatus.CONNECTED
            return {
                "success": True,
                "response_length": len(test_response),
                "message": "Claude Code interface working correctly"
            }
            
        except Exception as e:
            self.status = InterfaceStatus.ERROR
            self.last_error = str(e)
            self.error_count += 1
            return {
                "success": False,
                "error": str(e),
                "message": "Claude Code interface test failed"
            }
    
    async def generate_response(self, prompt: str, agent_type: AgentType, context: Dict[str, Any] = None) -> str:
        """Generate response using Claude Code"""
        try:
            if not self.claude_client:
                raise RuntimeError("Interface not initialized")
            
            # Create agent-specific client with tool restrictions
            agent_client = ClaudeCodeClient(
                timeout=self.config.timeout,
                agent_type=agent_type
            )
            
            response = await agent_client.generate_code(prompt, context or {})
            self.request_count += 1
            return response
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Claude Code generation failed: {e}")
            raise
    
    async def analyze_code(self, code: str, analysis_type: str = "review", agent_type: AgentType = AgentType.CODE) -> str:
        """Analyze code using Claude Code"""
        try:
            if not self.claude_client:
                raise RuntimeError("Interface not initialized")
            
            # Create agent-specific client
            agent_client = ClaudeCodeClient(
                timeout=self.config.timeout,
                agent_type=agent_type
            )
            
            response = await agent_client.analyze_code(code, analysis_type)
            self.request_count += 1
            return response
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Claude Code analysis failed: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown Claude Code interface"""
        self.status = InterfaceStatus.DISCONNECTED
        self.claude_client = None
        logger.info("Claude Code interface shut down")


class AnthropicAPIInterface(BaseAgentInterface):
    """Interface using Anthropic API directly"""
    
    def __init__(self, config: InterfaceConfig):
        super().__init__(config)
        self.client: Optional[anthropic.AsyncAnthropic] = None
        
    async def initialize(self) -> bool:
        """Initialize Anthropic API interface"""
        try:
            self.status = InterfaceStatus.CONFIGURING
            
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic SDK not available. Install with: pip install anthropic")
            
            if not self.config.api_key:
                raise ValueError("API key required for Anthropic API interface")
            
            # Initialize Anthropic client
            self.client = anthropic.AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            
            self.status = InterfaceStatus.CONNECTED
            self.connection_time = time.time()
            self.last_error = None
            
            logger.info("Anthropic API interface initialized successfully")
            return True
            
        except Exception as e:
            self.status = InterfaceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Failed to initialize Anthropic API interface: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Anthropic API connection"""
        try:
            self.status = InterfaceStatus.TESTING
            
            if not self.client:
                raise RuntimeError("Interface not initialized")
            
            # Simple test message
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=100,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": "Respond with exactly 'API connection test successful'"}
                ]
            )
            
            if not response.content or not response.content[0].text:
                raise RuntimeError("Empty response from Anthropic API")
            
            self.status = InterfaceStatus.CONNECTED
            return {
                "success": True,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "message": "Anthropic API interface working correctly"
            }
            
        except Exception as e:
            self.status = InterfaceStatus.ERROR
            self.last_error = str(e)
            self.error_count += 1
            return {
                "success": False,
                "error": str(e),
                "message": "Anthropic API interface test failed"
            }
    
    async def generate_response(self, prompt: str, agent_type: AgentType, context: Dict[str, Any] = None) -> str:
        """Generate response using Anthropic API"""
        try:
            if not self.client:
                raise RuntimeError("Interface not initialized")
            
            # Build system message with agent context
            system_message = self._build_system_message(agent_type, context or {})
            
            # Generate response
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if not response.content or not response.content[0].text:
                raise RuntimeError("Empty response from Anthropic API")
            
            self.request_count += 1
            return response.content[0].text
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Anthropic API generation failed: {e}")
            raise
    
    async def analyze_code(self, code: str, analysis_type: str = "review", agent_type: AgentType = AgentType.CODE) -> str:
        """Analyze code using Anthropic API"""
        try:
            if not self.client:
                raise RuntimeError("Interface not initialized")
            
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(code, analysis_type)
            system_message = self._build_system_message(agent_type, {"task": "code_analysis"})
            
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_message,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            if not response.content or not response.content[0].text:
                raise RuntimeError("Empty response from Anthropic API")
            
            self.request_count += 1
            return response.content[0].text
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Anthropic API analysis failed: {e}")
            raise
    
    def _build_system_message(self, agent_type: AgentType, context: Dict[str, Any]) -> str:
        """Build system message based on agent type"""
        base_message = f"You are a {agent_type.value} in an AI agent workflow system."
        
        role_descriptions = {
            AgentType.ORCHESTRATOR: "You coordinate and manage the overall workflow, with full system access.",
            AgentType.DESIGN: "You create system architecture and technical specifications. You have read-only access and cannot modify existing code.",
            AgentType.CODE: "You implement features and write code. You can edit files and commit changes but cannot push to remote repositories.",
            AgentType.QA: "You create and run tests to ensure quality. You can create test files but cannot modify implementation code.",
            AgentType.DATA: "You analyze data and generate insights. You have read-only access to code and can create analysis reports."
        }
        
        role_desc = role_descriptions.get(agent_type, "You are an AI assistant.")
        
        constraints = []
        if agent_type == AgentType.DESIGN:
            constraints.append("- You CANNOT modify existing code files")
            constraints.append("- You can only create documentation and architecture files")
        elif agent_type == AgentType.QA:
            constraints.append("- You can create test files but CANNOT modify implementation code")
            constraints.append("- You CANNOT commit or push changes")
        elif agent_type == AgentType.DATA:
            constraints.append("- You have read-only access to code")
            constraints.append("- You can create analysis reports and visualizations")
        elif agent_type == AgentType.CODE:
            constraints.append("- You can edit files and commit changes")
            constraints.append("- You CANNOT push to remote repositories")
        
        system_message = f"{base_message}\n\n{role_desc}"
        
        if constraints:
            system_message += f"\n\nIMPORTANT CONSTRAINTS:\n" + "\n".join(constraints)
        
        if context.get("task"):
            system_message += f"\n\nCurrent task: {context['task']}"
        
        return system_message
    
    def _build_analysis_prompt(self, code: str, analysis_type: str) -> str:
        """Build code analysis prompt"""
        return f"""
Please perform a {analysis_type} analysis of the following code:

```
{code}
```

Please analyze for:
- Code quality and maintainability
- Potential bugs or issues
- Performance considerations
- Security vulnerabilities
- Best practice adherence
- Suggestions for improvement

Provide a detailed analysis with specific recommendations.
"""
    
    async def shutdown(self):
        """Shutdown Anthropic API interface"""
        self.status = InterfaceStatus.DISCONNECTED
        if self.client:
            await self.client.close()
        self.client = None
        logger.info("Anthropic API interface shut down")


class MockInterface(BaseAgentInterface):
    """Mock interface for testing and demonstrations"""
    
    def __init__(self, config: InterfaceConfig):
        super().__init__(config)
        self.response_delay = config.custom_settings.get("response_delay", 1.0)
        self.failure_rate = config.custom_settings.get("failure_rate", 0.0)
        
    async def initialize(self) -> bool:
        """Initialize mock interface"""
        try:
            self.status = InterfaceStatus.CONFIGURING
            await asyncio.sleep(0.5)  # Simulate initialization time
            
            self.status = InterfaceStatus.CONNECTED
            self.connection_time = time.time()
            self.last_error = None
            
            logger.info("Mock interface initialized successfully")
            return True
            
        except Exception as e:
            self.status = InterfaceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Failed to initialize mock interface: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test mock connection"""
        try:
            self.status = InterfaceStatus.TESTING
            await asyncio.sleep(0.5)  # Simulate test time
            
            # Simulate random failures based on failure rate
            import random
            if random.random() < self.failure_rate:
                raise RuntimeError("Simulated connection test failure")
            
            self.status = InterfaceStatus.CONNECTED
            return {
                "success": True,
                "message": "Mock interface test successful",
                "simulated": True
            }
            
        except Exception as e:
            self.status = InterfaceStatus.ERROR
            self.last_error = str(e)
            self.error_count += 1
            return {
                "success": False,
                "error": str(e),
                "message": "Mock interface test failed"
            }
    
    async def generate_response(self, prompt: str, agent_type: AgentType, context: Dict[str, Any] = None) -> str:
        """Generate mock response"""
        try:
            await asyncio.sleep(self.response_delay)  # Simulate processing time
            
            # Simulate random failures
            import random
            if random.random() < self.failure_rate:
                raise RuntimeError("Simulated generation failure")
            
            # Generate context-aware mock response
            mock_response = self._generate_mock_response(prompt, agent_type, context or {})
            self.request_count += 1
            return mock_response
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Mock generation failed: {e}")
            raise
    
    async def analyze_code(self, code: str, analysis_type: str = "review", agent_type: AgentType = AgentType.CODE) -> str:
        """Analyze code using mock interface"""
        try:
            await asyncio.sleep(self.response_delay)
            
            import random
            if random.random() < self.failure_rate:
                raise RuntimeError("Simulated analysis failure")
            
            mock_analysis = self._generate_mock_analysis(code, analysis_type, agent_type)
            self.request_count += 1
            return mock_analysis
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Mock analysis failed: {e}")
            raise
    
    def _generate_mock_response(self, prompt: str, agent_type: AgentType, context: Dict[str, Any]) -> str:
        """Generate contextual mock response"""
        responses = {
            AgentType.DESIGN: f"""# Design Response (Mock)

## Analysis of Request
{prompt[:200]}...

## Architecture Recommendations
- Component-based design approach
- Separation of concerns
- Scalable architecture patterns
- Security considerations

## Technical Specifications
- Use modern frameworks and libraries
- Implement proper error handling
- Follow coding best practices
- Include comprehensive documentation

*This is a mock response from the Design Agent interface.*
""",
            AgentType.CODE: f"""# Code Implementation (Mock)

```python
# Generated code for: {prompt[:100]}...
# NOTE: This is a mock implementation

def mock_implementation():
    \"\"\"
    Mock implementation based on the request.
    In a real scenario, this would be actual working code.
    \"\"\"
    # TODO: Replace with actual implementation
    return "Mock response generated successfully"

class MockClass:
    \"\"\"Mock class for demonstration\"\"\"
    
    def __init__(self):
        self.status = "mock"
    
    def execute(self):
        return mock_implementation()

# Usage example
if __name__ == "__main__":
    instance = MockClass()
    result = instance.execute()
    print(result)
```

*This is a mock response from the Code Agent interface.*
""",
            AgentType.QA: f"""# Test Suite (Mock)

```python
# Tests for: {prompt[:100]}...
# NOTE: This is a mock test suite

import unittest
import pytest
from unittest.mock import Mock, patch

class TestMockImplementation(unittest.TestCase):
    \"\"\"Mock test class\"\"\"
    
    def setUp(self):
        \"\"\"Set up test fixtures\"\"\"
        self.test_subject = None  # Would be actual object under test
    
    def test_basic_functionality(self):
        \"\"\"Test basic functionality\"\"\"
        # Mock test implementation
        self.assertTrue(True, "Mock test passes")
    
    def test_error_handling(self):
        \"\"\"Test error handling\"\"\"
        # Mock error test
        with self.assertRaises(Exception):
            pass  # Would test actual error conditions
    
    @pytest.mark.parametrize("input_value,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
    ])
    def test_parameterized(self, input_value, expected):
        \"\"\"Parameterized test example\"\"\"
        # Mock parameterized test
        assert input_value.startswith("test")

if __name__ == "__main__":
    unittest.main()
```

*This is a mock response from the QA Agent interface.*
""",
            AgentType.DATA: f"""# Data Analysis Report (Mock)

## Request Analysis
{prompt[:200]}...

## Key Findings
- Data quality appears to be good
- No obvious anomalies detected
- Patterns suggest normal distribution
- Recommendations for further analysis

## Statistical Summary
- Sample size: Mock data (n=1000)
- Mean: 42.5 (mock value)
- Standard deviation: 15.2 (mock value)
- Confidence interval: 95%

## Visualizations Suggested
1. Histogram of main variables
2. Correlation matrix
3. Time series plots (if applicable)
4. Box plots for outlier detection

## Recommendations
1. Collect additional data for better insights
2. Perform deeper statistical analysis
3. Create interactive dashboard
4. Implement data quality monitoring

*This is a mock response from the Data Agent interface.*
""",
            AgentType.ORCHESTRATOR: f"""# Orchestration Plan (Mock)

## Task Analysis
{prompt[:200]}...

## Orchestration Strategy
1. Break down into subtasks
2. Assign appropriate agents
3. Monitor progress and quality
4. Coordinate between agents
5. Ensure deliverable quality

## Agent Assignments
- Design Agent: Architecture and specifications
- Code Agent: Implementation and refactoring
- QA Agent: Testing and quality validation
- Data Agent: Analysis and reporting

## Timeline
- Phase 1: Design and planning (2 hours)
- Phase 2: Implementation (4 hours)
- Phase 3: Testing and validation (2 hours)
- Phase 4: Review and deployment (1 hour)

## Success Criteria
- All tests pass
- Code quality metrics met
- Documentation complete
- Stakeholder approval obtained

*This is a mock response from the Orchestrator Agent interface.*
"""
        }
        
        return responses.get(agent_type, f"Mock response for {agent_type.value}: {prompt[:100]}...")
    
    def _generate_mock_analysis(self, code: str, analysis_type: str, agent_type: AgentType) -> str:
        """Generate mock code analysis"""
        return f"""# Code Analysis Report (Mock - {analysis_type})

## Code Overview
- Lines of code: {len(code.splitlines())}
- Analysis type: {analysis_type}
- Agent: {agent_type.value}

## Quality Assessment
✅ **Good practices found:**
- Proper function structure
- Clear variable names
- Appropriate comments

⚠️ **Areas for improvement:**
- Consider adding more error handling
- Could benefit from additional documentation
- Performance optimizations possible

## Security Analysis
- No obvious security vulnerabilities detected
- Standard security practices appear to be followed
- Recommend security review for production code

## Performance Considerations
- Code appears to be reasonably efficient
- Consider caching for frequently accessed data
- Monitor memory usage for large datasets

## Recommendations
1. Add comprehensive error handling
2. Improve documentation coverage
3. Consider adding unit tests
4. Review for potential optimizations

*This is a mock analysis from the {agent_type.value} interface.*
"""
    
    async def shutdown(self):
        """Shutdown mock interface"""
        self.status = InterfaceStatus.DISCONNECTED
        logger.info("Mock interface shut down")


class InterfaceManager:
    """Manages multiple agent interfaces"""
    
    def __init__(self):
        self.interfaces: Dict[str, BaseAgentInterface] = {}
        self.active_interface: Optional[str] = None
        self.configs: Dict[str, InterfaceConfig] = {}
        self.config_file = Path(__file__).parent / "interface_configs.json"
        self._lock = threading.Lock()
        
        # Load configurations
        self.load_configurations()
        
        # Initialize default interfaces
        self._setup_default_interfaces()
    
    def _setup_default_interfaces(self):
        """Setup default interface configurations"""
        default_configs = {
            InterfaceType.CLAUDE_CODE.value: InterfaceConfig(
                interface_type=InterfaceType.CLAUDE_CODE.value,
                enabled=True
            ),
            InterfaceType.ANTHROPIC_API.value: InterfaceConfig(
                interface_type=InterfaceType.ANTHROPIC_API.value,
                enabled=False,  # Requires API key
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ),
            InterfaceType.MOCK.value: InterfaceConfig(
                interface_type=InterfaceType.MOCK.value,
                enabled=True,
                custom_settings={
                    "response_delay": 1.0,
                    "failure_rate": 0.05  # 5% failure rate for testing
                }
            )
        }
        
        # Only add configs that don't already exist
        for interface_type, config in default_configs.items():
            if interface_type not in self.configs:
                self.configs[interface_type] = config
        
        # Set default active interface
        if not self.active_interface:
            if self.configs.get(InterfaceType.CLAUDE_CODE.value, {}).enabled:
                self.active_interface = InterfaceType.CLAUDE_CODE.value
            elif self.configs.get(InterfaceType.MOCK.value, {}).enabled:
                self.active_interface = InterfaceType.MOCK.value
    
    def load_configurations(self):
        """Load interface configurations from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                self.configs = {
                    k: InterfaceConfig.from_dict(v) 
                    for k, v in data.get('configs', {}).items()
                }
                self.active_interface = data.get('active_interface')
                
                logger.info(f"Loaded {len(self.configs)} interface configurations")
            
        except Exception as e:
            logger.error(f"Failed to load interface configurations: {e}")
            self.configs = {}
    
    def save_configurations(self):
        """Save interface configurations to file"""
        try:
            with self._lock:
                data = {
                    'configs': {k: v.to_dict() for k, v in self.configs.items()},
                    'active_interface': self.active_interface
                }
                
                # Ensure directory exists
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.config_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.info("Interface configurations saved")
                
        except Exception as e:
            logger.error(f"Failed to save interface configurations: {e}")
    
    async def initialize_interface(self, interface_type: str) -> bool:
        """Initialize a specific interface"""
        try:
            if interface_type not in self.configs:
                raise ValueError(f"Unknown interface type: {interface_type}")
            
            config = self.configs[interface_type]
            
            # Create interface instance
            if interface_type == InterfaceType.CLAUDE_CODE.value:
                interface = ClaudeCodeInterface(config)
            elif interface_type == InterfaceType.ANTHROPIC_API.value:
                interface = AnthropicAPIInterface(config)
            elif interface_type == InterfaceType.MOCK.value:
                interface = MockInterface(config)
            else:
                raise ValueError(f"Unsupported interface type: {interface_type}")
            
            # Initialize the interface
            success = await interface.initialize()
            
            if success:
                with self._lock:
                    self.interfaces[interface_type] = interface
                logger.info(f"Interface {interface_type} initialized successfully")
            else:
                logger.error(f"Failed to initialize interface {interface_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing interface {interface_type}: {e}")
            return False
    
    async def switch_interface(self, interface_type: str) -> Dict[str, Any]:
        """Switch to a different active interface"""
        try:
            if interface_type not in self.configs:
                return {
                    "success": False,
                    "error": f"Unknown interface type: {interface_type}",
                    "active_interface": self.active_interface
                }
            
            # Initialize interface if not already done
            if interface_type not in self.interfaces:
                success = await self.initialize_interface(interface_type)
                if not success:
                    return {
                        "success": False,
                        "error": f"Failed to initialize interface: {interface_type}",
                        "active_interface": self.active_interface
                    }
            
            # Test the interface before switching
            interface = self.interfaces[interface_type]
            test_result = await interface.test_connection()
            
            if not test_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Interface test failed: {test_result.get('error', 'Unknown error')}",
                    "active_interface": self.active_interface
                }
            
            # Switch to new interface
            old_interface = self.active_interface
            self.active_interface = interface_type
            
            # Save configuration
            self.save_configurations()
            
            logger.info(f"Switched from {old_interface} to {interface_type}")
            
            return {
                "success": True,
                "message": f"Successfully switched to {interface_type}",
                "old_interface": old_interface,
                "active_interface": self.active_interface,
                "test_result": test_result
            }
            
        except Exception as e:
            logger.error(f"Error switching interface: {e}")
            return {
                "success": False,
                "error": str(e),
                "active_interface": self.active_interface
            }
    
    def get_interface_status(self) -> Dict[str, Any]:
        """Get status of all interfaces"""
        status = {
            "active_interface": self.active_interface,
            "interfaces": {}
        }
        
        for interface_type, config in self.configs.items():
            interface_info = {
                "enabled": config.enabled,
                "configured": True
            }
            
            if interface_type in self.interfaces:
                interface = self.interfaces[interface_type]
                interface_info.update(interface.get_status_info())
            else:
                interface_info.update({
                    "status": "not_initialized",
                    "connection_time": None,
                    "request_count": 0,
                    "error_count": 0
                })
            
            status["interfaces"][interface_type] = interface_info
        
        return status
    
    def update_interface_config(self, interface_type: str, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update interface configuration"""
        try:
            if interface_type not in self.configs:
                return {
                    "success": False,
                    "error": f"Unknown interface type: {interface_type}"
                }
            
            # Update configuration
            config = self.configs[interface_type]
            for key, value in config_updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    # Handle custom settings
                    if key.startswith("custom_"):
                        setting_name = key[7:]  # Remove "custom_" prefix
                        config.custom_settings[setting_name] = value
            
            # Save configurations
            self.save_configurations()
            
            # If interface is active, it may need reinitialization
            needs_reinit = interface_type == self.active_interface and interface_type in self.interfaces
            
            return {
                "success": True,
                "message": f"Configuration updated for {interface_type}",
                "needs_reinitialization": needs_reinit,
                "masked_config": config.mask_sensitive_data()
            }
            
        except Exception as e:
            logger.error(f"Error updating interface config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_active_interface(self) -> Optional[BaseAgentInterface]:
        """Get the currently active interface"""
        if not self.active_interface:
            return None
        
        if self.active_interface not in self.interfaces:
            # Try to initialize it
            await self.initialize_interface(self.active_interface)
        
        return self.interfaces.get(self.active_interface)
    
    async def shutdown_all(self):
        """Shutdown all interfaces"""
        for interface in self.interfaces.values():
            try:
                await interface.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down interface: {e}")
        
        self.interfaces.clear()
        logger.info("All interfaces shut down")


# Global interface manager instance
interface_manager = InterfaceManager()