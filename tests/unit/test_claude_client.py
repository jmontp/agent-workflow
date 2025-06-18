"""
Unit tests for Claude Code Integration Client.

Tests the integration with Claude Code CLI for AI-powered capabilities,
including security boundaries and tool access restrictions per agent type.
"""

import pytest
import asyncio
import subprocess
from unittest.mock import Mock, patch, AsyncMock

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.claude_client import ClaudeCodeClient, claude_client, create_agent_client
from lib.agent_tool_config import AgentType


class TestClaudeCodeClient:
    """Test the ClaudeCodeClient class."""
    
    @pytest.fixture
    def mock_subprocess_run(self):
        """Mock subprocess.run for testing."""
        with patch('subprocess.run') as mock_run:
            yield mock_run
    
    @pytest.fixture
    def client_available(self, mock_subprocess_run):
        """Create client with Claude available."""
        mock_subprocess_run.return_value.returncode = 0
        return ClaudeCodeClient(timeout=30)
    
    @pytest.fixture
    def client_unavailable(self, mock_subprocess_run):
        """Create client with Claude unavailable."""
        mock_subprocess_run.side_effect = FileNotFoundError()
        return ClaudeCodeClient(timeout=30)
    
    @pytest.fixture
    def agent_client(self, mock_subprocess_run):
        """Create client with agent restrictions."""
        mock_subprocess_run.return_value.returncode = 0
        return ClaudeCodeClient(timeout=30, agent_type=AgentType.CODE)

    def test_client_init_available(self, client_available):
        """Test client initialization when Claude is available."""
        assert client_available.timeout == 30
        assert client_available.agent_type is None
        assert client_available.available is True

    def test_client_init_unavailable(self, client_unavailable):
        """Test client initialization when Claude is unavailable."""
        assert client_unavailable.timeout == 30
        assert client_unavailable.available is False

    def test_client_init_with_agent_type(self, agent_client):
        """Test client initialization with agent type."""
        assert agent_client.agent_type == AgentType.CODE
        assert agent_client.available is True

    def test_check_claude_availability_success(self, mock_subprocess_run):
        """Test checking Claude availability when command succeeds."""
        mock_subprocess_run.return_value.returncode = 0
        
        client = ClaudeCodeClient()
        
        assert client.available is True
        mock_subprocess_run.assert_called_once_with(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

    def test_check_claude_availability_failure(self, mock_subprocess_run):
        """Test checking Claude availability when command fails."""
        mock_subprocess_run.return_value.returncode = 1
        
        client = ClaudeCodeClient()
        
        assert client.available is False

    def test_check_claude_availability_not_found(self, mock_subprocess_run):
        """Test checking Claude availability when command not found."""
        mock_subprocess_run.side_effect = FileNotFoundError()
        
        client = ClaudeCodeClient()
        
        assert client.available is False

    def test_check_claude_availability_timeout(self, mock_subprocess_run):
        """Test checking Claude availability when command times out."""
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("claude", 10)
        
        client = ClaudeCodeClient()
        
        assert client.available is False

    @pytest.mark.asyncio
    async def test_generate_code_available(self, client_available):
        """Test code generation when Claude is available."""
        with patch.object(client_available, '_execute_claude_command', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "def test_function(): pass"
            
            result = await client_available.generate_code("Create a test function")
            
            assert result == "def test_function(): pass"
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_code_unavailable(self, client_unavailable):
        """Test code generation when Claude is unavailable."""
        result = await client_unavailable.generate_code("Create a test function")
        
        assert "# Generated code for: Create a test function" in result
        assert "def generated_function():" in result
        assert "class GeneratedClass:" in result

    @pytest.mark.asyncio
    async def test_generate_code_with_context(self, client_available):
        """Test code generation with context."""
        context = {
            "language": "python",
            "framework": "fastapi",
            "style_guide": "pep8"
        }
        
        with patch.object(client_available, '_execute_claude_command', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "# Generated FastAPI code"
            
            result = await client_available.generate_code("Create API endpoint", context)
            
            assert result == "# Generated FastAPI code"
            # Check that context was included in prompt
            call_args = mock_execute.call_args[0][0]
            assert "Language: python" in call_args
            assert "Framework: fastapi" in call_args
            assert "Style Guide: pep8" in call_args

    @pytest.mark.asyncio
    async def test_generate_code_error_fallback(self, client_available):
        """Test code generation fallback on error."""
        with patch.object(client_available, '_execute_claude_command', side_effect=Exception("Network error")):
            result = await client_available.generate_code("Create a function")
            
            # Should fall back to placeholder
            assert "# Generated code for: Create a function" in result
            assert "def generated_function():" in result

    @pytest.mark.asyncio
    async def test_analyze_code_available(self, client_available):
        """Test code analysis when Claude is available."""
        code = "def example(): return True"
        
        with patch.object(client_available, '_execute_claude_command', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "Code analysis results"
            
            result = await client_available.analyze_code(code, "quality")
            
            assert result == "Code analysis results"
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_code_unavailable(self, client_unavailable):
        """Test code analysis when Claude is unavailable."""
        code = "def example(): return True"
        
        result = await client_unavailable.analyze_code(code, "security")
        
        assert "# Code Analysis Report (security)" in result
        assert "Lines of code: 1" in result
        assert "Analysis type: security" in result

    @pytest.mark.asyncio
    async def test_generate_tests_available(self, client_available):
        """Test test generation when Claude is available."""
        code = "def add(a, b): return a + b"
        
        with patch.object(client_available, '_execute_claude_command', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "import unittest\nclass TestAdd(unittest.TestCase): pass"
            
            result = await client_available.generate_tests(code, "unit")
            
            assert result == "import unittest\nclass TestAdd(unittest.TestCase): pass"
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_tests_unavailable(self, client_unavailable):
        """Test test generation when Claude is unavailable."""
        code = "def multiply(a, b): return a * b"
        
        result = await client_unavailable.generate_tests(code, "integration")
        
        assert "# Generated integration tests" in result
        assert "import unittest" in result
        assert "class TestGenerated(unittest.TestCase):" in result

    @pytest.mark.asyncio
    async def test_create_architecture_available(self, client_available):
        """Test architecture creation when Claude is available."""
        requirements = "E-commerce platform with user management"
        
        with patch.object(client_available, '_execute_claude_command', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "# System Architecture\n\n## Components\n- User Service\n- Product Service"
            
            result = await client_available.create_architecture(requirements)
            
            assert "# System Architecture" in result
            assert "## Components" in result
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_architecture_unavailable(self, client_unavailable):
        """Test architecture creation when Claude is unavailable."""
        requirements = "Blog management system"
        
        result = await client_unavailable.create_architecture(requirements)
        
        assert "# System Architecture (Placeholder)" in result
        assert requirements in result
        assert "## Components" in result
        assert "Component A: Main application logic" in result

    @pytest.mark.asyncio
    async def test_analyze_data_available(self, client_available):
        """Test data analysis when Claude is available."""
        data_description = "User activity logs from web application"
        analysis_goals = "Identify usage patterns and optimization opportunities"
        
        with patch.object(client_available, '_execute_claude_command', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "# Data Analysis\n\n## Key Insights\n- Peak usage at 2PM"
            
            result = await client_available.analyze_data(data_description, analysis_goals)
            
            assert "# Data Analysis" in result
            assert "## Key Insights" in result
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_data_unavailable(self, client_unavailable):
        """Test data analysis when Claude is unavailable."""
        data_description = "Sales transaction data"
        analysis_goals = "Revenue trends and customer segmentation"
        
        result = await client_unavailable.analyze_data(data_description, analysis_goals)
        
        assert "# Data Analysis Report (Placeholder)" in result
        assert data_description in result
        assert analysis_goals in result
        assert "## Key Findings" in result

    @pytest.mark.asyncio
    async def test_execute_claude_command_success(self, agent_client):
        """Test successful Claude command execution."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            # Mock process
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success output", b""))
            mock_exec.return_value = mock_process
            
            # Mock asyncio.wait_for
            with patch('asyncio.wait_for', new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = (b"Success output", b"")
                
                result = await agent_client._execute_claude_command("Test prompt")
                
                assert result == "Success output"
                mock_exec.assert_called_once()
                # Check that tool args were included for agent type
                call_args = mock_exec.call_args[0]
                assert 'claude' in call_args

    @pytest.mark.asyncio
    async def test_execute_claude_command_failure(self, client_available):
        """Test Claude command execution failure."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = Mock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"Error output"))
            mock_exec.return_value = mock_process
            
            with patch('asyncio.wait_for', new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = (b"", b"Error output")
                
                with pytest.raises(subprocess.CalledProcessError):
                    await client_available._execute_claude_command("Test prompt")

    @pytest.mark.asyncio
    async def test_execute_claude_command_timeout(self, client_available):
        """Test Claude command execution timeout."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = Mock()
            mock_exec.return_value = mock_process
            
            with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                with pytest.raises(asyncio.TimeoutError):
                    await client_available._execute_claude_command("Test prompt")

    def test_prepare_code_prompt(self, client_available):
        """Test code prompt preparation."""
        prompt = "Create a user class"
        context = {
            "language": "python",
            "framework": "django",
            "style_guide": "black"
        }
        
        result = client_available._prepare_code_prompt(prompt, context)
        
        assert "Create a user class" in result
        assert "Language: python" in result
        assert "Framework: django" in result
        assert "Style Guide: black" in result
        assert "clean, maintainable code" in result

    def test_prepare_code_prompt_no_context(self, client_available):
        """Test code prompt preparation without context."""
        prompt = "Create a function"
        context = {}
        
        result = client_available._prepare_code_prompt(prompt, context)
        
        assert "Create a function" in result
        assert "Language:" not in result
        assert "clean, maintainable code" in result

    def test_prepare_analysis_prompt(self, client_available):
        """Test analysis prompt preparation."""
        code = "def test(): pass"
        analysis_type = "security"
        
        result = client_available._prepare_analysis_prompt(code, analysis_type)
        
        assert "security analysis" in result
        assert "def test(): pass" in result
        assert "Code quality and maintainability" in result
        assert "Security vulnerabilities" in result

    def test_prepare_test_prompt(self, client_available):
        """Test test prompt preparation."""
        code = "def calculate(x, y): return x + y"
        test_type = "unit"
        
        result = client_available._prepare_test_prompt(code, test_type)
        
        assert "unit tests" in result
        assert "def calculate(x, y): return x + y" in result
        assert "Cover all major code paths" in result
        assert "pytest, unittest" in result

    def test_prepare_architecture_prompt(self, client_available):
        """Test architecture prompt preparation."""
        requirements = "Real-time chat application"
        
        result = client_available._prepare_architecture_prompt(requirements)
        
        assert "Real-time chat application" in result
        assert "High-level system architecture" in result
        assert "Component breakdown" in result
        assert "Scalability considerations" in result

    def test_prepare_data_prompt(self, client_available):
        """Test data analysis prompt preparation."""
        data_description = "Customer purchase history"
        analysis_goals = "Identify buying patterns"
        
        result = client_available._prepare_data_prompt(data_description, analysis_goals)
        
        assert "Customer purchase history" in result
        assert "Identify buying patterns" in result
        assert "Data quality assessment" in result
        assert "Statistical analysis" in result

    def test_placeholder_code_generation(self, client_unavailable):
        """Test placeholder code generation."""
        prompt = "Create authentication system"
        
        result = client_unavailable._placeholder_code_generation(prompt)
        
        assert f"# Generated code for: {prompt}" in result
        assert "def generated_function():" in result
        assert "class GeneratedClass:" in result
        assert "placeholder = True" in result

    def test_placeholder_code_analysis(self, client_unavailable):
        """Test placeholder code analysis."""
        code = "def example():\n    return True"
        analysis_type = "quality"
        
        result = client_unavailable._placeholder_code_analysis(code, analysis_type)
        
        assert "# Code Analysis Report (quality)" in result
        assert "Lines of code: 2" in result
        assert "Analysis type: quality" in result
        assert "Placeholder Recommendations" in result

    def test_placeholder_test_generation(self, client_unavailable):
        """Test placeholder test generation."""
        code = "def add(a, b): return a + b"
        test_type = "unit"
        
        result = client_unavailable._placeholder_test_generation(code, test_type)
        
        assert f"# Generated {test_type} tests" in result
        assert "import unittest" in result
        assert "class TestGenerated(unittest.TestCase):" in result
        assert "def test_placeholder(self):" in result

    def test_placeholder_architecture(self, client_unavailable):
        """Test placeholder architecture generation."""
        requirements = "Microservices platform"
        
        result = client_unavailable._placeholder_architecture(requirements)
        
        assert "# System Architecture (Placeholder)" in result
        assert requirements in result
        assert "## Components" in result
        assert "## Technology Stack" in result

    def test_placeholder_data_analysis(self, client_unavailable):
        """Test placeholder data analysis."""
        data_description = "Website analytics data"
        analysis_goals = "Traffic optimization"
        
        result = client_unavailable._placeholder_data_analysis(data_description, analysis_goals)
        
        assert "# Data Analysis Report (Placeholder)" in result
        assert data_description in result
        assert analysis_goals in result
        assert "## Key Findings" in result


class TestModuleFunctions:
    """Test module-level functions and variables."""
    
    def test_global_claude_client(self):
        """Test global Claude client instance."""
        assert isinstance(claude_client, ClaudeCodeClient)
        assert claude_client.agent_type is None  # No restrictions

    def test_create_agent_client(self):
        """Test creating agent-specific client."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            client = create_agent_client(AgentType.DESIGN, timeout=60)
            
            assert isinstance(client, ClaudeCodeClient)
            assert client.agent_type == AgentType.DESIGN
            assert client.timeout == 60

    def test_create_agent_client_defaults(self):
        """Test creating agent client with defaults."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            client = create_agent_client(AgentType.QA)
            
            assert client.agent_type == AgentType.QA
            assert client.timeout == 300  # Default timeout


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_code_generation_workflow(self, mock_subprocess_run):
        """Test complete code generation workflow."""
        mock_subprocess_run.return_value.returncode = 0
        
        client = ClaudeCodeClient(agent_type=AgentType.CODE)
        
        with patch.object(client, '_execute_claude_command', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = """
def authenticate_user(username, password):
    '''Authenticate user with username and password'''
    if not username or not password:
        raise ValueError("Username and password required")
    # Authentication logic here
    return True
"""
            
            context = {
                "language": "python",
                "framework": "flask"
            }
            
            result = await client.generate_code("Create user authentication function", context)
            
            assert "def authenticate_user" in result
            assert "Authentication logic" in result
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_type_tool_restrictions(self, mock_subprocess_run):
        """Test that agent types apply correct tool restrictions."""
        mock_subprocess_run.return_value.returncode = 0
        
        client = ClaudeCodeClient(agent_type=AgentType.DESIGN)
        
        with patch('asyncio.create_subprocess_exec') as mock_exec, \
             patch('lib.agent_tool_config.get_claude_tool_args') as mock_get_args:
            
            mock_get_args.return_value = ['--disallowedTools', 'Edit,Write']
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Architecture doc", b""))
            mock_exec.return_value = mock_process
            
            with patch('asyncio.wait_for', new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = (b"Architecture doc", b"")
                
                await client._execute_claude_command("Design system architecture")
                
                # Verify tool restrictions were applied
                mock_get_args.assert_called_once_with(AgentType.DESIGN)
                call_args = mock_exec.call_args[0]
                assert 'claude' in call_args
                assert '--disallowedTools' in call_args

    @pytest.mark.asyncio 
    async def test_error_recovery_chain(self):
        """Test error recovery through fallback chain."""
        # Start with available client
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            client = ClaudeCodeClient()
        
        # Simulate Claude command failure, should fallback to placeholder
        with patch.object(client, '_execute_claude_command', side_effect=Exception("Claude failed")):
            result = await client.generate_code("Create API endpoint")
            
            # Should get placeholder implementation
            assert "# Generated code for: Create API endpoint" in result
            assert "def generated_function():" in result
            assert "class GeneratedClass:" in result

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_subprocess_run):
        """Test handling concurrent requests."""
        mock_subprocess_run.return_value.returncode = 0
        client = ClaudeCodeClient()
        
        with patch.object(client, '_execute_claude_command', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = [
                "Code result 1",
                "Code result 2", 
                "Code result 3"
            ]
            
            # Make concurrent requests
            tasks = [
                client.generate_code("Create function 1"),
                client.generate_code("Create function 2"),
                client.generate_code("Create function 3")
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert results == ["Code result 1", "Code result 2", "Code result 3"]
            assert mock_execute.call_count == 3