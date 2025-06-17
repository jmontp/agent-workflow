"""
Pytest configuration and shared fixtures for test suite.

Provides common test utilities, fixtures, and configuration
for the AI Agent TDD-Scrum Workflow test suite.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import sys

# Add project paths to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(project_root / "scripts"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client"""
    mock_client = Mock()
    mock_client.messages = Mock()
    mock_client.messages.create = AsyncMock(return_value=Mock(
        content=[Mock(text="Mocked AI response")]
    ))
    return mock_client


@pytest.fixture
def mock_discord_interaction():
    """Mock Discord interaction object"""
    mock_interaction = Mock()
    mock_interaction.response = Mock()
    mock_interaction.response.defer = AsyncMock()
    mock_interaction.response.send_message = AsyncMock()
    mock_interaction.followup = Mock()
    mock_interaction.followup.send = AsyncMock()
    mock_interaction.channel_id = 123456789
    mock_interaction.user = Mock()
    mock_interaction.user.id = 987654321
    return mock_interaction


@pytest.fixture
def test_project_config(temp_directory):
    """Create test project configuration"""
    config = {
        "projects": [
            {
                "name": "test_project",
                "path": str(temp_directory / "test_project"),
                "orchestration": "blocking"
            },
            {
                "name": "autonomous_project", 
                "path": str(temp_directory / "autonomous_project"),
                "orchestration": "autonomous"
            }
        ]
    }
    
    # Create project directories
    for project in config["projects"]:
        Path(project["path"]).mkdir(parents=True, exist_ok=True)
    
    # Save config to file
    import yaml
    config_file = temp_directory / "test_projects.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return config_file


@pytest.fixture
def mock_orchestrator(test_project_config):
    """Create mock orchestrator with test configuration"""
    from orchestrator import Orchestrator
    
    # Mock agent initialization to avoid external dependencies
    with pytest.mock.patch('orchestrator.create_agent') as mock_create:
        mock_agent = Mock()
        mock_agent._execute_with_retry = AsyncMock(return_value=Mock(
            success=True,
            output="Mock agent result",
            artifacts={},
            error=None
        ))
        mock_create.return_value = mock_agent
        
        orchestrator = Orchestrator(str(test_project_config))
        yield orchestrator


@pytest.fixture
def sample_task():
    """Create sample task for testing"""
    from agents import Task, TaskStatus
    
    return Task(
        id="test-task-001",
        agent_type="DesignAgent",
        command="Create system architecture",
        context={"requirements": "Build authentication system"},
        status=TaskStatus.PENDING
    )


@pytest.fixture
def mock_state_machine():
    """Create mock state machine"""
    from state_machine import StateMachine, State
    
    state_machine = StateMachine()
    return state_machine


@pytest.fixture
def mock_discord_bot(mock_orchestrator):
    """Create mock Discord bot with orchestrator"""
    from lib.discord_bot import WorkflowBot
    
    # Mock Discord client initialization
    with pytest.mock.patch('discord.ext.commands.Bot.__init__'):
        bot = WorkflowBot(mock_orchestrator)
        bot.user = Mock()
        bot.user.id = 123456789
        bot.guilds = []
        return bot


class TestHelpers:
    """Helper utilities for tests"""
    
    @staticmethod
    def create_mock_agent_result(success=True, output="Mock output", error=None):
        """Create mock agent result"""
        from agents import AgentResult
        return AgentResult(
            success=success,
            output=output,
            artifacts={},
            error=error,
            execution_time=0.1
        )
    
    @staticmethod
    def create_mock_command_result(success=True, new_state=None, error=None, hint=None):
        """Create mock command result"""
        from state_machine import CommandResult, State
        return CommandResult(
            success=success,
            new_state=new_state,
            error_message=error,
            hint=hint
        )
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
        """Wait for a condition to become true"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(interval)
        
        return False


@pytest.fixture
def test_helpers():
    """Provide test helper utilities"""
    return TestHelpers


# Mark all tests as asyncio tests by default
# pytest_plugins = ['pytest_asyncio']  # Disabled - pytest-asyncio not available


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on location"""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


# Fixtures for specific test scenarios
@pytest.fixture
def blocking_project_setup(mock_orchestrator):
    """Set up project in blocking orchestration mode"""
    project = mock_orchestrator.projects["test_project"]
    assert project.orchestration_mode.value == "blocking"
    return project


@pytest.fixture
def autonomous_project_setup(mock_orchestrator):
    """Set up project in autonomous orchestration mode"""
    project = mock_orchestrator.projects["autonomous_project"]
    assert project.orchestration_mode.value == "autonomous"
    return project


@pytest.fixture
def sprint_active_state(mock_orchestrator):
    """Set up project in SPRINT_ACTIVE state"""
    from state_machine import State
    
    project = mock_orchestrator.projects["test_project"]
    project.state_machine.force_state(State.SPRINT_ACTIVE)
    return project


@pytest.fixture
def sprint_review_state(mock_orchestrator):
    """Set up project in SPRINT_REVIEW state"""
    from state_machine import State
    
    project = mock_orchestrator.projects["test_project"]
    project.state_machine.force_state(State.SPRINT_REVIEW)
    return project