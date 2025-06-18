"""
Unit tests for Discord Bot.

Tests the Discord bot for AI Agent TDD-Scrum Workflow management,
including slash commands, state visualization, and HITL approval processes.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

# Mock discord before importing
sys.modules['discord'] = Mock()
sys.modules['discord.ext'] = Mock()
sys.modules['discord.ext.commands'] = Mock()
sys.modules['discord.ui'] = Mock()

# Mock discord classes
import discord
discord.Intents = Mock()
discord.Intents.default = Mock(return_value=Mock())
discord.Embed = Mock
discord.Color = Mock()
discord.Color.green = Mock(return_value="green")
discord.Color.blue = Mock(return_value="blue")
discord.Color.red = Mock(return_value="red")
discord.Color.orange = Mock(return_value="orange")
discord.Color.yellow = Mock(return_value="yellow")
discord.Color.purple = Mock(return_value="purple")
discord.ButtonStyle = Mock()
discord.ButtonStyle.primary = "primary"
discord.ButtonStyle.secondary = "secondary"
discord.ButtonStyle.success = "success"
discord.utils = Mock()

# Mock commands
from discord.ext import commands
commands.Bot = Mock
commands.Context = Mock

# Mock app_commands
discord.app_commands = Mock()
discord.app_commands.command = lambda **kwargs: lambda func: func
discord.app_commands.describe = lambda **kwargs: lambda func: func
discord.app_commands.choices = lambda **kwargs: lambda func: func
discord.app_commands.Choice = Mock

# Mock UI components
discord.ui.View = Mock
discord.ui.Button = Mock
discord.ui.button = lambda **kwargs: lambda func: func

# Now import the Discord bot modules
from lib.discord_bot import StateView, WorkflowBot, run_discord_bot


class MockOrchestrator:
    """Mock orchestrator for testing."""
    
    def __init__(self):
        self.projects = {"test_project": Mock()}
        
    async def handle_command(self, command, project_name, **kwargs):
        """Mock command handling."""
        if "/state" in command:
            return {
                "success": True,
                "state_info": {
                    "current_state": "IDLE",
                    "allowed_commands": ["/epic", "/approve", "/sprint plan"]
                },
                "project_status": {
                    "orchestration_mode": "blocking",
                    "active_tasks": 3,
                    "pending_approvals": 1
                },
                "mermaid_diagram": "graph TD\n    A[IDLE] --> B[BACKLOG_READY]"
            }
        elif "/epic" in command:
            return {
                "success": True,
                "stories": ["Story 1", "Story 2"],
                "next_step": "Approve stories with /approve"
            }
        elif "/approve" in command:
            return {
                "success": True,
                "approved_items": ["STORY-1", "STORY-2"],
                "next_step": "Plan sprint with /sprint plan"
            }
        elif "/sprint" in command:
            if "status" in command:
                return {
                    "success": True,
                    "total_tasks": 10,
                    "completed_tasks": 7,
                    "failed_tasks": 1,
                    "current_state": "SPRINT_ACTIVE",
                    "pending_approvals": 2
                }
            else:
                return {
                    "success": True,
                    "message": "Sprint action completed",
                    "next_step": "Continue development"
                }
        elif "/backlog" in command:
            if "view" in command:
                return {
                    "success": True,
                    "backlog_type": "product",
                    "items": [
                        {"id": "STORY-1", "title": "User authentication", "priority": "high"},
                        {"id": "STORY-2", "title": "Data validation", "priority": "medium"}
                    ]
                }
            else:
                return {
                    "success": True,
                    "message": "Backlog updated"
                }
        elif "/tdd" in command:
            if "status" in command:
                return {
                    "success": True,
                    "cycle_info": {
                        "cycle_id": "cycle-123",
                        "story_id": "STORY-1",
                        "current_state": "TEST_RED",
                        "progress": "2/5",
                        "total_test_runs": 15,
                        "total_refactors": 3,
                        "current_task_id": "task-456"
                    },
                    "allowed_commands": ["/tdd test", "/tdd code"],
                    "next_suggested": "/tdd code"
                }
            elif "logs" in command:
                return {
                    "success": True,
                    "logs_info": {
                        "cycle_id": "cycle-123",
                        "total_events": 25,
                        "last_activity": "2024-01-01T12:00:00",
                        "recent_events": [
                            "Test created for user validation",
                            "RED state achieved",
                            "Code implementation started"
                        ]
                    }
                }
            elif "overview" in command:
                return {
                    "success": True,
                    "overview_info": {
                        "active_cycles": 2,
                        "completed_cycles": 8,
                        "total_test_runs": 150,
                        "average_coverage": 87.5,
                        "total_refactors": 25,
                        "success_rate": 95.2,
                        "active_stories": ["STORY-1", "STORY-2"]
                    }
                }
            elif "start" in command:
                return {
                    "success": True,
                    "message": "TDD cycle started successfully",
                    "cycle_id": "cycle-456",
                    "story_id": kwargs.get("story_id", "STORY-1"),
                    "current_state": "DESIGN"
                }
            else:
                return {
                    "success": True,
                    "message": f"TDD {command.split()[-1]} completed",
                    "current_state": "CODE_GREEN",
                    "next_suggested": "/tdd refactor"
                }
        else:
            return {
                "success": True,
                "message": "Command executed successfully",
                "next_step": "Continue workflow"
            }


class MockInteraction:
    """Mock Discord interaction for testing."""
    
    def __init__(self, channel_id=12345):
        self.channel_id = channel_id
        self.response = Mock()
        self.response.defer = AsyncMock()
        self.response.send_message = AsyncMock()
        self.followup = Mock()
        self.followup.send = AsyncMock()
        self.guild = Mock()
        self.guild.id = 67890


class TestStateView:
    """Test the StateView class."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        return MockOrchestrator()
    
    @pytest.fixture
    def state_view(self, mock_orchestrator):
        """Create StateView for testing."""
        return StateView(mock_orchestrator, "test_project")
    
    def test_state_view_init(self, state_view, mock_orchestrator):
        """Test StateView initialization."""
        assert state_view.orchestrator == mock_orchestrator
        assert state_view.project_name == "test_project"
        assert state_view.timeout == 300
    
    @pytest.mark.asyncio
    async def test_show_allowed_commands_success(self, state_view):
        """Test showing allowed commands successfully."""
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_allowed_commands(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "ephemeral" in call_args[1]
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_show_allowed_commands_failure(self, state_view):
        """Test showing allowed commands when state fails."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={"success": False})
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_allowed_commands(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "❌ Failed to get state info" in str(call_args[0])
    
    @pytest.mark.asyncio
    async def test_show_state_diagram_success(self, state_view):
        """Test showing state diagram successfully."""
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_state_diagram(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "ephemeral" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_show_project_status_success(self, state_view):
        """Test showing project status successfully."""
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_project_status(interaction, button)
        
        interaction.response.send_message.assert_called_once()


class TestWorkflowBot:
    """Test the WorkflowBot class."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        return MockOrchestrator()
    
    @pytest.fixture
    def workflow_bot(self, mock_orchestrator):
        """Create WorkflowBot for testing."""
        with patch('discord.Intents') as mock_intents:
            mock_intents.default.return_value = Mock()
            with patch('discord.ext.commands.Bot.__init__'):
                bot = WorkflowBot(mock_orchestrator)
                bot.user = Mock()
                bot.user.id = 123456
                bot.guilds = []
                bot.get_channel = Mock(return_value=Mock())
                bot.tree = Mock()
                bot.tree.sync = AsyncMock(return_value=[])
                return bot
    
    def test_workflow_bot_init(self, workflow_bot, mock_orchestrator):
        """Test WorkflowBot initialization."""
        assert workflow_bot.orchestrator == mock_orchestrator
        assert workflow_bot.project_channels == {}
    
    @pytest.mark.asyncio
    async def test_setup_hook(self, workflow_bot):
        """Test setup hook."""
        await workflow_bot.setup_hook()
        
        workflow_bot.tree.sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_hook_sync_failure(self, workflow_bot):
        """Test setup hook when sync fails."""
        workflow_bot.tree.sync.side_effect = Exception("Sync failed")
        
        await workflow_bot.setup_hook()
        
        workflow_bot.tree.sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_on_ready(self, workflow_bot):
        """Test on_ready event."""
        with patch.object(workflow_bot, '_ensure_project_channels', new_callable=AsyncMock):
            await workflow_bot.on_ready()
            
            workflow_bot._ensure_project_channels.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_project_channels_new_channel(self, workflow_bot):
        """Test ensuring project channels when channel doesn't exist."""
        mock_guild = Mock()
        mock_guild.channels = []
        mock_guild.create_text_channel = AsyncMock(return_value=Mock(id=54321))
        workflow_bot.guilds = [mock_guild]
        
        with patch('os.getenv', return_value="testhost"):
            await workflow_bot._ensure_project_channels()
        
        mock_guild.create_text_channel.assert_called_once()
        assert "test_project" in workflow_bot.project_channels
    
    @pytest.mark.asyncio
    async def test_ensure_project_channels_existing_channel(self, workflow_bot):
        """Test ensuring project channels when channel exists."""
        mock_channel = Mock()
        mock_channel.id = 98765
        mock_guild = Mock()
        mock_guild.channels = [mock_channel]
        mock_guild.create_text_channel = AsyncMock()
        workflow_bot.guilds = [mock_guild]
        
        with patch('discord.utils.get', return_value=mock_channel), \
             patch('os.getenv', return_value="testhost"):
            await workflow_bot._ensure_project_channels()
        
        mock_guild.create_text_channel.assert_not_called()
        assert workflow_bot.project_channels["test_project"] == 98765
    
    @pytest.mark.asyncio
    async def test_ensure_project_channels_creation_failure(self, workflow_bot):
        """Test ensuring project channels when creation fails."""
        mock_guild = Mock()
        mock_guild.channels = []
        mock_guild.create_text_channel = AsyncMock(side_effect=Exception("Creation failed"))
        workflow_bot.guilds = [mock_guild]
        
        with patch('os.getenv', return_value="testhost"):
            await workflow_bot._ensure_project_channels()
        
        mock_guild.create_text_channel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_project_from_channel(self, workflow_bot):
        """Test getting project name from channel ID."""
        workflow_bot.project_channels = {"project1": 123, "project2": 456}
        
        result = await workflow_bot._get_project_from_channel(123)
        assert result == "project1"
        
        result = await workflow_bot._get_project_from_channel(999)
        assert result == "default"
    
    @pytest.mark.asyncio
    async def test_send_notification(self, workflow_bot):
        """Test sending notification to project channel."""
        mock_channel = Mock()
        mock_channel.send = AsyncMock()
        workflow_bot.project_channels = {"test_project": 123}
        workflow_bot.get_channel = Mock(return_value=mock_channel)
        
        await workflow_bot._send_notification("test_project", "Test message")
        
        mock_channel.send.assert_called_once_with("Test message", embed=None)
    
    @pytest.mark.asyncio
    async def test_send_notification_no_channel(self, workflow_bot):
        """Test sending notification when channel doesn't exist."""
        workflow_bot.project_channels = {}
        
        await workflow_bot._send_notification("nonexistent", "Test message")
        
        # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_epic_command_success(self, workflow_bot):
        """Test successful epic command."""
        interaction = MockInteraction()
        
        await workflow_bot.epic_command(interaction, "Create user management system")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_epic_command_failure(self, workflow_bot):
        """Test epic command failure."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "Invalid state for epic creation"
        })
        interaction = MockInteraction()
        
        await workflow_bot.epic_command(interaction, "Invalid epic")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args[0][0]
        assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_approve_command_with_items(self, workflow_bot):
        """Test approve command with specific items."""
        interaction = MockInteraction()
        
        await workflow_bot.approve_command(interaction, "STORY-1, STORY-2")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_command_no_items(self, workflow_bot):
        """Test approve command without specific items."""
        interaction = MockInteraction()
        
        await workflow_bot.approve_command(interaction, "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_status(self, workflow_bot):
        """Test sprint status command."""
        interaction = MockInteraction()
        
        await workflow_bot.sprint_command(interaction, "status", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_plan_with_items(self, workflow_bot):
        """Test sprint plan command with items."""
        interaction = MockInteraction()
        
        await workflow_bot.sprint_command(interaction, "plan", "STORY-1, STORY-2")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_failure(self, workflow_bot):
        """Test sprint command failure."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "Cannot start sprint in current state",
            "hint": "Complete backlog first",
            "current_state": "IDLE"
        })
        interaction = MockInteraction()
        
        await workflow_bot.sprint_command(interaction, "start", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backlog_command_view(self, workflow_bot):
        """Test backlog view command."""
        interaction = MockInteraction()
        
        await workflow_bot.backlog_command(interaction, "view", "", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backlog_command_add_story(self, workflow_bot):
        """Test backlog add story command."""
        interaction = MockInteraction()
        
        await workflow_bot.backlog_command(
            interaction, "add_story", "New story description", "FEATURE-1", "high"
        )
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_state_command_success(self, workflow_bot):
        """Test state command success."""
        interaction = MockInteraction()
        
        await workflow_bot.state_command(interaction)
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        # Check that view was passed
        call_kwargs = interaction.followup.send.call_args[1]
        assert "view" in call_kwargs
    
    @pytest.mark.asyncio
    async def test_state_command_failure(self, workflow_bot):
        """Test state command failure."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "State information unavailable"
        })
        interaction = MockInteraction()
        
        await workflow_bot.state_command(interaction)
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args[0][0]
        assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_request_changes_command(self, workflow_bot):
        """Test request changes command."""
        interaction = MockInteraction()
        
        await workflow_bot.request_changes_command(interaction, "Need better error handling")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_suggest_fix_command(self, workflow_bot):
        """Test suggest fix command."""
        interaction = MockInteraction()
        
        await workflow_bot.suggest_fix_command(interaction, "Add null checks to validation")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_skip_task_command(self, workflow_bot):
        """Test skip task command."""
        interaction = MockInteraction()
        
        await workflow_bot.skip_task_command(interaction)
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_feedback_command(self, workflow_bot):
        """Test feedback command."""
        interaction = MockInteraction()
        
        await workflow_bot.feedback_command(interaction, "Sprint went well, good velocity")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_project_command_register(self, workflow_bot):
        """Test project register command."""
        interaction = MockInteraction()
        
        with patch.object(workflow_bot, '_handle_project_register', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = {
                "success": True,
                "project_name": "new_project",
                "path": "/path/to/project",
                "channel": "#testhost-new_project",
                "next_step": "Project ready"
            }
            
            await workflow_bot.project_command(interaction, "register", "/path/to/project", "new_project")
            
            interaction.response.defer.assert_called_once()
            mock_register.assert_called_once_with("/path/to/project", "new_project", interaction.guild)
            interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_project_command_unknown_action(self, workflow_bot):
        """Test project command with unknown action."""
        interaction = MockInteraction()
        
        await workflow_bot.project_command(interaction, "unknown", "/path", "")
        
        interaction.response.defer.assert_called_once()
        call_args = interaction.followup.send.call_args[0][0]
        assert "Unknown project action" in call_args
    
    @pytest.mark.asyncio
    async def test_handle_project_register_success(self, workflow_bot):
        """Test successful project registration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            (project_path / ".git").mkdir()
            
            mock_guild = Mock()
            mock_guild.channels = []
            mock_channel = Mock()
            mock_channel.id = 12345
            mock_guild.create_text_channel = AsyncMock(return_value=mock_channel)
            
            with patch('discord.utils.get', return_value=None), \
                 patch('os.getenv', return_value="testhost"), \
                 patch('lib.discord_bot.ProjectStorage') as mock_storage, \
                 patch('lib.discord_bot.Project'), \
                 patch('lib.discord_bot.OrchestrationMode'), \
                 patch('lib.discord_bot.StateMachine'):
                
                mock_storage_instance = Mock()
                mock_storage_instance.initialize_project = Mock(return_value=True)
                mock_storage.return_value = mock_storage_instance
                
                result = await workflow_bot._handle_project_register(
                    str(project_path), "test_project", mock_guild
                )
                
                assert result["success"] is True
                assert result["project_name"] == "test_project"
                assert "test_project" in workflow_bot.project_channels
    
    @pytest.mark.asyncio
    async def test_handle_project_register_path_not_exists(self, workflow_bot):
        """Test project registration with non-existent path."""
        mock_guild = Mock()
        
        result = await workflow_bot._handle_project_register(
            "/nonexistent/path", "test", mock_guild
        )
        
        assert result["success"] is False
        assert "does not exist" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_not_git_repo(self, workflow_bot):
        """Test project registration with non-git directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_guild = Mock()
            
            result = await workflow_bot._handle_project_register(
                temp_dir, "test", mock_guild
            )
            
            assert result["success"] is False
            assert "not a git repository" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_duplicate_project(self, workflow_bot):
        """Test project registration with duplicate project name."""
        mock_guild = Mock()
        
        result = await workflow_bot._handle_project_register(
            "/some/path", "test_project", mock_guild  # test_project already exists in mock
        )
        
        assert result["success"] is False
        assert "already registered" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_channel_exists(self, workflow_bot):
        """Test project registration when Discord channel already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "new_project"
            project_path.mkdir()
            (project_path / ".git").mkdir()
            
            mock_guild = Mock()
            mock_existing_channel = Mock()
            
            with patch('discord.utils.get', return_value=mock_existing_channel), \
                 patch('os.getenv', return_value="testhost"):
                
                result = await workflow_bot._handle_project_register(
                    str(project_path), "new_project", mock_guild
                )
                
                assert result["success"] is False
                assert "Channel already exists" in result["error"]
    
    @pytest.mark.asyncio
    async def test_tdd_command_status(self, workflow_bot):
        """Test TDD status command."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "status", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_start_with_story(self, workflow_bot):
        """Test TDD start command with story ID."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "start", "STORY-1", "Implement user auth")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_logs(self, workflow_bot):
        """Test TDD logs command."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "logs", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_overview(self, workflow_bot):
        """Test TDD overview command."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "overview", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_other_actions(self, workflow_bot):
        """Test other TDD commands."""
        interaction = MockInteraction()
        
        for action in ["design", "test", "code", "refactor", "commit", "run_tests", "next", "abort"]:
            interaction.response.defer.reset_mock()
            interaction.followup.send.reset_mock()
            
            await workflow_bot.tdd_command(interaction, action, "", "")
            
            interaction.response.defer.assert_called_once()
            interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_failure(self, workflow_bot):
        """Test TDD command failure."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "No active TDD cycle",
            "hint": "Start a cycle first with /tdd start",
            "current_state": "IDLE",
            "allowed_commands": ["/tdd start"]
        })
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "code", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()


class TestModuleFunctions:
    """Test module-level functions."""
    
    @pytest.mark.asyncio
    async def test_run_discord_bot_no_token(self):
        """Test running Discord bot without token."""
        with patch('os.getenv', return_value=None):
            await run_discord_bot()
            # Should return early without error
    
    @pytest.mark.asyncio
    async def test_run_discord_bot_with_token(self):
        """Test running Discord bot with token."""
        mock_orchestrator = Mock()
        mock_orchestrator.run = AsyncMock()
        mock_orchestrator.stop = Mock()
        
        mock_bot = Mock()
        mock_bot.start = AsyncMock()
        mock_bot.close = AsyncMock()
        
        with patch('os.getenv', return_value="fake_token"), \
             patch('lib.discord_bot.Orchestrator', return_value=mock_orchestrator), \
             patch('lib.discord_bot.WorkflowBot', return_value=mock_bot), \
             patch('asyncio.create_task') as mock_create_task:
            
            mock_create_task.return_value = Mock()
            
            await run_discord_bot()
            
            mock_bot.start.assert_called_once_with("fake_token")
            mock_orchestrator.stop.assert_called_once()
            mock_bot.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_discord_bot_keyboard_interrupt(self):
        """Test running Discord bot with keyboard interrupt."""
        mock_orchestrator = Mock()
        mock_orchestrator.run = AsyncMock()
        mock_orchestrator.stop = Mock()
        
        mock_bot = Mock()
        mock_bot.start = AsyncMock(side_effect=KeyboardInterrupt())
        mock_bot.close = AsyncMock()
        
        with patch('os.getenv', return_value="fake_token"), \
             patch('lib.discord_bot.Orchestrator', return_value=mock_orchestrator), \
             patch('lib.discord_bot.WorkflowBot', return_value=mock_bot), \
             patch('asyncio.create_task'):
            
            await run_discord_bot()
            
            mock_orchestrator.stop.assert_called_once()
            mock_bot.close.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_sequence(self):
        """Test complete workflow sequence through Discord commands."""
        orchestrator = MockOrchestrator()
        
        with patch('discord.Intents'), \
             patch('discord.ext.commands.Bot.__init__'):
            
            bot = WorkflowBot(orchestrator)
            bot.project_channels = {"test_project": 12345}
            
            # Simulate epic creation
            interaction = MockInteraction()
            await bot.epic_command(interaction, "User management system")
            
            # Simulate approval
            interaction = MockInteraction()
            await bot.approve_command(interaction, "STORY-1,STORY-2")
            
            # Simulate sprint planning
            interaction = MockInteraction()
            await bot.sprint_command(interaction, "plan", "STORY-1,STORY-2")
            
            # Simulate sprint start
            interaction = MockInteraction()
            await bot.sprint_command(interaction, "start", "")
            
            # Verify all commands executed
            assert True  # If we get here, all commands executed without error
    
    @pytest.mark.asyncio
    async def test_tdd_workflow_sequence(self):
        """Test TDD workflow sequence through Discord commands."""
        orchestrator = MockOrchestrator()
        
        with patch('discord.Intents'), \
             patch('discord.ext.commands.Bot.__init__'):
            
            bot = WorkflowBot(orchestrator)
            bot.project_channels = {"test_project": 12345}
            
            # Start TDD cycle
            interaction = MockInteraction()
            await bot.tdd_command(interaction, "start", "STORY-1", "User auth implementation")
            
            # Check status
            interaction = MockInteraction()
            await bot.tdd_command(interaction, "status", "", "")
            
            # Progress through phases
            for action in ["design", "test", "code", "refactor", "commit"]:
                interaction = MockInteraction()
                await bot.tdd_command(interaction, action, "", "")
            
            # Check overview
            interaction = MockInteraction()
            await bot.tdd_command(interaction, "overview", "", "")
            
            # Verify all TDD commands executed
            assert True
    
    @pytest.mark.asyncio
    async def test_error_handling_chain(self):
        """Test error handling through command chain."""
        orchestrator = MockOrchestrator()
        
        # Set up failure scenarios
        orchestrator.handle_command = AsyncMock(side_effect=[
            {"success": False, "error": "Invalid state"},
            {"success": False, "error": "Missing dependencies", "hint": "Complete epic first"},
            {"success": True, "message": "Recovery successful"}
        ])
        
        with patch('discord.Intents'), \
             patch('discord.ext.commands.Bot.__init__'):
            
            bot = WorkflowBot(orchestrator)
            bot.project_channels = {"test_project": 12345}
            
            # Try commands that fail
            interaction = MockInteraction()
            await bot.sprint_command(interaction, "start", "")
            
            interaction = MockInteraction()
            await bot.epic_command(interaction, "Test epic")
            
            interaction = MockInteraction()
            await bot.state_command(interaction)
            
            # Should handle all errors gracefully
            assert orchestrator.handle_command.call_count == 3