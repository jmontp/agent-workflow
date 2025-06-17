"""
Claude Code Integration Client

Provides integration with Claude Code for AI agent capabilities.
Uses subprocess to execute claude commands for AI-powered tasks.
Includes security boundaries through tool access restrictions per agent type.
"""

import subprocess
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# Handle both relative and absolute imports
try:
    from .agent_tool_config import AgentType, get_claude_tool_args
except ImportError:
    from agent_tool_config import AgentType, get_claude_tool_args

logger = logging.getLogger(__name__)


class ClaudeCodeClient:
    """
    Client for integrating with Claude Code command-line interface.
    
    This client executes claude commands to provide AI capabilities
    for the agent workflow system with security boundaries per agent type.
    """
    
    def __init__(self, timeout: int = 300, agent_type: Optional[AgentType] = None):
        """
        Initialize Claude Code client.
        
        Args:
            timeout: Command timeout in seconds (default: 5 minutes)
            agent_type: Type of agent using this client (for tool restrictions)
        """
        self.timeout = timeout
        self.agent_type = agent_type
        self.available = self._check_claude_availability()
        
        if self.available:
            logger.info("Claude Code integration available")
            if agent_type:
                logger.info(f"Tool restrictions enabled for {agent_type.value}")
        else:
            logger.warning("Claude Code not available - using placeholder implementations")
    
    def _check_claude_availability(self) -> bool:
        """Check if claude command is available"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False
    
    async def generate_code(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Generate code using Claude Code.
        
        Args:
            prompt: Description of what code to generate
            context: Additional context for code generation
            
        Returns:
            Generated code as string
        """
        if not self.available:
            return self._placeholder_code_generation(prompt)
        
        try:
            # Prepare the prompt with context
            full_prompt = self._prepare_code_prompt(prompt, context or {})
            
            # Execute claude command
            result = await self._execute_claude_command(full_prompt)
            
            return result
            
        except Exception as e:
            logger.error(f"Claude Code generation failed: {e}")
            return self._placeholder_code_generation(prompt)
    
    async def analyze_code(self, code: str, analysis_type: str = "review") -> str:
        """
        Analyze code using Claude Code.
        
        Args:
            code: Code to analyze
            analysis_type: Type of analysis (review, quality, security, etc.)
            
        Returns:
            Analysis results as string
        """
        if not self.available:
            return self._placeholder_code_analysis(code, analysis_type)
        
        try:
            prompt = self._prepare_analysis_prompt(code, analysis_type)
            result = await self._execute_claude_command(prompt)
            return result
            
        except Exception as e:
            logger.error(f"Claude Code analysis failed: {e}")
            return self._placeholder_code_analysis(code, analysis_type)
    
    async def generate_tests(self, code: str, test_type: str = "unit") -> str:
        """
        Generate tests for code using Claude Code.
        
        Args:
            code: Code to generate tests for
            test_type: Type of tests (unit, integration, e2e)
            
        Returns:
            Generated test code as string
        """
        if not self.available:
            return self._placeholder_test_generation(code, test_type)
        
        try:
            prompt = self._prepare_test_prompt(code, test_type)
            result = await self._execute_claude_command(prompt)
            return result
            
        except Exception as e:
            logger.error(f"Claude Code test generation failed: {e}")
            return self._placeholder_test_generation(code, test_type)
    
    async def create_architecture(self, requirements: str) -> str:
        """
        Create system architecture using Claude Code.
        
        Args:
            requirements: System requirements description
            
        Returns:
            Architecture documentation as string
        """
        if not self.available:
            return self._placeholder_architecture(requirements)
        
        try:
            prompt = self._prepare_architecture_prompt(requirements)
            result = await self._execute_claude_command(prompt)
            return result
            
        except Exception as e:
            logger.error(f"Claude Code architecture generation failed: {e}")
            return self._placeholder_architecture(requirements)
    
    async def analyze_data(self, data_description: str, analysis_goals: str) -> str:
        """
        Analyze data using Claude Code.
        
        Args:
            data_description: Description of the data
            analysis_goals: What insights to generate
            
        Returns:
            Data analysis results as string
        """
        if not self.available:
            return self._placeholder_data_analysis(data_description, analysis_goals)
        
        try:
            prompt = self._prepare_data_prompt(data_description, analysis_goals)
            result = await self._execute_claude_command(prompt)
            return result
            
        except Exception as e:
            logger.error(f"Claude Code data analysis failed: {e}")
            return self._placeholder_data_analysis(data_description, analysis_goals)
    
    async def _execute_claude_command(self, prompt: str) -> str:
        """
        Execute claude command with given prompt and tool restrictions.
        
        Args:
            prompt: Prompt to send to Claude
            
        Returns:
            Claude's response
        """
        try:
            # Build command with tool restrictions if agent type is set
            cmd_args = ['claude']
            
            if self.agent_type:
                tool_args = get_claude_tool_args(self.agent_type)
                cmd_args.extend(tool_args)
                logger.debug(f"Using tool restrictions for {self.agent_type.value}: {tool_args}")
            
            # Execute claude command with prompt as stdin
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=prompt.encode()),
                timeout=self.timeout
            )
            
            if process.returncode != 0:
                logger.error(f"Claude command failed: {stderr.decode()}")
                raise subprocess.CalledProcessError(process.returncode, 'claude')
            
            return stdout.decode().strip()
                
        except asyncio.TimeoutError:
            logger.error(f"Claude command timed out after {self.timeout}s")
            raise
        except Exception as e:
            logger.error(f"Error executing claude command: {e}")
            raise
    
    def _prepare_code_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Prepare prompt for code generation"""
        context_str = ""
        if context.get("language"):
            context_str += f"Language: {context['language']}\n"
        if context.get("framework"):
            context_str += f"Framework: {context['framework']}\n"
        if context.get("style_guide"):
            context_str += f"Style Guide: {context['style_guide']}\n"
        
        return f"""
Please generate code for the following requirement:

{prompt}

{context_str}

Requirements:
- Write clean, maintainable code
- Include appropriate error handling
- Add docstrings for functions and classes
- Follow best practices for the language/framework
- Include usage examples if appropriate

Please provide only the code implementation.
"""
    
    def _prepare_analysis_prompt(self, code: str, analysis_type: str) -> str:
        """Prepare prompt for code analysis"""
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
    
    def _prepare_test_prompt(self, code: str, test_type: str) -> str:
        """Prepare prompt for test generation"""
        return f"""
Please generate comprehensive {test_type} tests for the following code:

```
{code}
```

Requirements:
- Cover all major code paths
- Include edge cases and error conditions
- Use appropriate testing framework (pytest, unittest, etc.)
- Include setup and teardown as needed
- Add descriptive test names and docstrings
- Test both positive and negative scenarios

Please provide complete test code that can be run immediately.
"""
    
    def _prepare_architecture_prompt(self, requirements: str) -> str:
        """Prepare prompt for architecture generation"""
        return f"""
Please create a system architecture for the following requirements:

{requirements}

Please provide:
- High-level system architecture
- Component breakdown and responsibilities
- Data flow and interactions
- Technology stack recommendations
- Scalability considerations
- Security considerations
- Deployment architecture

Format the response as clear, structured documentation.
"""
    
    def _prepare_data_prompt(self, data_description: str, analysis_goals: str) -> str:
        """Prepare prompt for data analysis"""
        return f"""
Please analyze the following data and provide insights:

Data Description:
{data_description}

Analysis Goals:
{analysis_goals}

Please provide:
- Data quality assessment
- Key insights and patterns
- Statistical analysis (if applicable)
- Recommendations for action
- Visualization suggestions
- Data processing pipeline recommendations

Format the response as a structured analysis report.
"""
    
    # Placeholder implementations for when Claude Code is not available
    
    def _placeholder_code_generation(self, prompt: str) -> str:
        """Placeholder code generation when Claude is not available"""
        return f'''# Generated code for: {prompt}
# NOTE: This is a placeholder implementation
# Claude Code integration not available

def generated_function():
    """
    Generated function based on: {prompt}
    """
    # TODO: Implement actual functionality
    pass

class GeneratedClass:
    """Generated class for the requirements"""
    
    def __init__(self):
        self.placeholder = True
    
    def execute(self):
        """Execute the main functionality"""
        return "Placeholder implementation"
'''
    
    def _placeholder_code_analysis(self, code: str, analysis_type: str) -> str:
        """Placeholder code analysis when Claude is not available"""
        return f'''# Code Analysis Report ({analysis_type})

## Summary
This is a placeholder analysis report. Claude Code integration is not available.

## Code Overview
- Lines of code: {len(code.splitlines())}
- Analysis type: {analysis_type}

## Placeholder Recommendations
1. Enable Claude Code integration for detailed analysis
2. Review code manually for quality issues
3. Run static analysis tools (pylint, flake8, etc.)
4. Ensure comprehensive test coverage

## Next Steps
- Install and configure Claude Code CLI
- Re-run analysis with AI assistance
'''
    
    def _placeholder_test_generation(self, code: str, test_type: str) -> str:
        """Placeholder test generation when Claude is not available"""
        return f'''# Generated {test_type} tests
# NOTE: This is a placeholder implementation

import unittest
import pytest

class TestGenerated(unittest.TestCase):
    """Placeholder test class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_subject = None  # Replace with actual object
    
    def test_placeholder(self):
        """Placeholder test method"""
        # TODO: Implement actual tests when Claude Code is available
        self.assertTrue(True, "Placeholder test")
    
    def test_error_handling(self):
        """Test error handling"""
        # TODO: Add error handling tests
        pass

if __name__ == "__main__":
    unittest.main()
'''
    
    def _placeholder_architecture(self, requirements: str) -> str:
        """Placeholder architecture when Claude is not available"""
        return f'''# System Architecture (Placeholder)

## Requirements
{requirements}

## Architecture Overview
This is a placeholder architecture document. Claude Code integration is not available.

## Components
- Component A: Main application logic
- Component B: Data persistence layer
- Component C: User interface layer
- Component D: External integrations

## Technology Stack
- Backend: Python/FastAPI
- Database: PostgreSQL
- Frontend: React/TypeScript
- Deployment: Docker/Kubernetes

## Next Steps
1. Enable Claude Code integration for detailed architecture
2. Review and refine component design
3. Create detailed technical specifications
4. Plan implementation phases
'''
    
    def _placeholder_data_analysis(self, data_description: str, analysis_goals: str) -> str:
        """Placeholder data analysis when Claude is not available"""
        return f'''# Data Analysis Report (Placeholder)

## Data Description
{data_description}

## Analysis Goals
{analysis_goals}

## Summary
This is a placeholder analysis report. Claude Code integration is not available.

## Key Findings
- Placeholder finding 1: Data appears to be well-structured
- Placeholder finding 2: No obvious quality issues detected
- Placeholder finding 3: Further analysis recommended

## Recommendations
1. Enable Claude Code integration for detailed analysis
2. Perform manual data exploration
3. Use standard data analysis tools (pandas, numpy)
4. Create visualization dashboards

## Next Steps
- Install and configure Claude Code CLI
- Re-run analysis with AI assistance
- Implement data processing pipeline
'''


# Global client instance (no restrictions - for backwards compatibility)
claude_client = ClaudeCodeClient()

# Factory function to create agent-specific clients
def create_agent_client(agent_type: AgentType, timeout: int = 300) -> ClaudeCodeClient:
    """Create a Claude client with agent-specific tool restrictions"""
    return ClaudeCodeClient(timeout=timeout, agent_type=agent_type)