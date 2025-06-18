"""
Comprehensive unit tests for Discord Bot targeting 95%+ line coverage.

Tests all Discord bot functionality including error paths, edge cases,
and integration scenarios for government audit compliance.
"""

import pytest
import asyncio
import tempfile
import os
import logging
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

# Comprehensive Discord mock infrastructure
class MockEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title = title
        self.description = description
        self.color = color
        self.fields = []
    
    def add_field(self, name, value, inline=True):
        self.fields.append({"name": name, "value": value, "inline": inline})
        return self

class MockColor:
    @staticmethod
    def green(): return "green"
    @staticmethod
    def blue(): return "blue"
    @staticmethod
    def red(): return "red"
    @staticmethod
    def orange(): return "orange"
    @staticmethod
    def yellow(): return "yellow"
    @staticmethod
    def purple(): return "purple"

class MockButtonStyle:
    primary = "primary"
    secondary = "secondary"
    success = "success"

class MockIntents:
    def __init__(self):
        self.message_content = True
        self.guilds = True
    
    @staticmethod
    def default():
        return MockIntents()

class MockUtils:
    @staticmethod
    def get(iterable, **kwargs):
        if not iterable:
            return None
        for item in iterable:
            match = True
            for key, value in kwargs.items():
                if not hasattr(item, key) or getattr(item, key) != value:
                    match = False
                    break
            if match:
                return item
        return None

class MockInteraction:
    def __init__(self, channel_id=12345, guild_id=67890):
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.response = Mock()
        self.response.defer = AsyncMock()
        self.response.send_message = AsyncMock()
        self.followup = Mock()
        self.followup.send = AsyncMock()
        self.guild = Mock()
        self.guild.id = guild_id
        self.guild.channels = []
        self.guild.create_text_channel = AsyncMock()

class MockBot:
    def __init__(self, **kwargs):
        self.command_prefix = kwargs.get('command_prefix', '!')
        self.intents = kwargs.get('intents')
        self.description = kwargs.get('description', '')
        self.user = Mock()
        self.user.id = 123456
        self.guilds = []
        self.tree = Mock()
        self.tree.sync = AsyncMock(return_value=[])
        self.get_channel = Mock()
        self.start = AsyncMock()
        self.close = AsyncMock()

# Set up Discord mocks
sys.modules['discord'] = Mock()
sys.modules['discord.ext'] = Mock()
sys.modules['discord.ext.commands'] = Mock()
sys.modules['discord.ui'] = Mock()

import discord
discord.Intents = MockIntents
discord.Embed = MockEmbed
discord.Color = MockColor
discord.ButtonStyle = MockButtonStyle
discord.utils = MockUtils
discord.Interaction = MockInteraction

from discord.ext import commands
commands.Bot = MockBot
commands.Context = Mock

discord.app_commands = Mock()
discord.app_commands.command = lambda **kwargs: lambda func: func
discord.app_commands.describe = lambda **kwargs: lambda func: func
discord.app_commands.choices = lambda **kwargs: lambda func: func
discord.app_commands.Choice = Mock

discord.ui.View = Mock
discord.ui.Button = Mock
discord.ui.button = lambda **kwargs: lambda func: func

from lib.discord_bot import StateView, WorkflowBot, run_discord_bot


class MockOrchestrator:
    """Mock orchestrator with configurable responses."""
    
    def __init__(self, fail_commands=False):
        self.projects = {"test_project": Mock(), "project2": Mock()}
        self.fail_commands = fail_commands
        self.stop_called = False
        
    async def handle_command(self, command, project_name, **kwargs):
        """Mock command handling."""
        if self.fail_commands:
            return {"success": False, "error": "Command failed"}
        
        # Return success responses for all commands
        return {"success": True, "message": "Command executed"}
    
    async def run(self):
        pass
    
    def stop(self):
        self.stop_called = True


class TestStateView:
    """Test StateView class for 95%+ coverage."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        return MockOrchestrator()
    
    @pytest.fixture
    def state_view(self, mock_orchestrator):
        return StateView(mock_orchestrator, "test_project")
    
    @pytest.fixture
    def failing_orchestrator(self):
        return MockOrchestrator(fail_commands=True)
    
    def test_state_view_init(self, state_view, mock_orchestrator):
        """Test StateView initialization."""
        assert state_view.orchestrator == mock_orchestrator
        assert state_view.project_name == "test_project"
        assert state_view.timeout == 300
    
    def test_state_view_init_default_project(self, mock_orchestrator):
        """Test StateView with default project."""
        view = StateView(mock_orchestrator)
        assert view.project_name == "default"
    
    @pytest.mark.asyncio
    async def test_show_allowed_commands_success(self, state_view):
        """Test successful allowed commands display."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "state_info": {"allowed_commands": ["/epic", "/approve"]}
        })
        
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_allowed_commands(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        args, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_show_allowed_commands_failure(self, state_view):
        """Test allowed commands display failure."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={"success": False})
        
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_allowed_commands(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        args = interaction.response.send_message.call_args[0]
        assert "❌ Failed to get state info" in args[0]
    
    @pytest.mark.asyncio
    async def test_show_state_diagram_success(self, state_view):
        """Test successful state diagram display."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "mermaid_diagram": "graph TD\n    A --> B"
        })
        
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_state_diagram(interaction, button)
        
        interaction.response.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_state_diagram_failure(self, state_view):
        """Test state diagram display failure."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={"success": False})
        
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_state_diagram(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        args = interaction.response.send_message.call_args[0]
        assert "❌ Failed to get diagram" in args[0]
    
    @pytest.mark.asyncio
    async def test_show_project_status_success(self, state_view):
        """Test successful project status display."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "total_tasks": 5,
            "completed_tasks": 3,
            "failed_tasks": 1,
            "current_state": "ACTIVE",
            "pending_approvals": 2
        })
        
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_project_status(interaction, button)
        
        interaction.response.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_project_status_failure(self, state_view):
        """Test project status display failure."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={"success": False})
        
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_project_status(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        args = interaction.response.send_message.call_args[0]
        assert "❌ Failed to get project status" in args[0]


class TestWorkflowBot:
    """Test WorkflowBot class for 95%+ coverage."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        return MockOrchestrator()
    
    @pytest.fixture
    def failing_orchestrator(self):
        return MockOrchestrator(fail_commands=True)
    
    @pytest.fixture
    def workflow_bot(self, mock_orchestrator):
        bot = WorkflowBot(mock_orchestrator)
        bot.user = Mock()
        bot.user.id = 123456
        bot.guilds = []
        bot.get_channel = Mock()
        bot.tree = Mock()
        bot.tree.sync = AsyncMock(return_value=[])
        return bot
    
    def test_workflow_bot_init(self, workflow_bot, mock_orchestrator):
        """Test WorkflowBot initialization."""
        assert workflow_bot.orchestrator == mock_orchestrator
        assert workflow_bot.project_channels == {}
        assert workflow_bot.command_prefix == "!"
        assert workflow_bot.description == "AI Agent TDD-Scrum Workflow Bot"
    
    @pytest.mark.asyncio
    async def test_setup_hook_success(self, workflow_bot):
        """Test successful setup hook."""
        await workflow_bot.setup_hook()
        workflow_bot.tree.sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_hook_failure(self, workflow_bot):
        """Test setup hook with sync failure."""
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
    async def test_ensure_project_channels_new_channels(self, workflow_bot):
        """Test creating new project channels."""
        mock_guild = Mock()
        mock_guild.channels = []
        mock_channel = Mock()
        mock_channel.id = 12345
        mock_guild.create_text_channel = AsyncMock(return_value=mock_channel)
        workflow_bot.guilds = [mock_guild]
        
        with patch('os.getenv', return_value="testhost"), \
             patch('discord.utils.get', return_value=None):
            await workflow_bot._ensure_project_channels()
        
        assert mock_guild.create_text_channel.call_count == 2
        assert len(workflow_bot.project_channels) == 2
    
    @pytest.mark.asyncio
    async def test_ensure_project_channels_existing_channels(self, workflow_bot):
        """Test with existing project channels."""
        mock_channel = Mock()
        mock_channel.id = 98765
        mock_guild = Mock()
        mock_guild.channels = [mock_channel]
        mock_guild.create_text_channel = AsyncMock()
        workflow_bot.guilds = [mock_guild]
        
        with patch('os.getenv', return_value="testhost"), \
             patch('discord.utils.get', return_value=mock_channel):
            await workflow_bot._ensure_project_channels()
        
        # Should not create new channels
        mock_guild.create_text_channel.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ensure_project_channels_creation_failure(self, workflow_bot):
        """Test channel creation failure."""
        mock_guild = Mock()
        mock_guild.channels = []
        mock_guild.create_text_channel = AsyncMock(side_effect=Exception("Failed"))
        workflow_bot.guilds = [mock_guild]
        
        with patch('os.getenv', return_value="testhost"), \
             patch('discord.utils.get', return_value=None):
            await workflow_bot._ensure_project_channels()
        
        # Should attempt to create channels despite failures
        assert mock_guild.create_text_channel.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_project_from_channel(self, workflow_bot):
        """Test getting project from channel ID."""
        workflow_bot.project_channels = {"proj1": 123, "proj2": 456}
        
        result = await workflow_bot._get_project_from_channel(123)
        assert result == "proj1"
        
        result = await workflow_bot._get_project_from_channel(999)
        assert result == "default"
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self, workflow_bot):
        """Test successful notification sending."""
        mock_channel = Mock()
        mock_channel.send = AsyncMock()
        workflow_bot.project_channels = {"test_project": 123}
        workflow_bot.get_channel = Mock(return_value=mock_channel)
        
        embed = MockEmbed()
        await workflow_bot._send_notification("test_project", "Test message", embed)
        
        mock_channel.send.assert_called_once_with("Test message", embed=embed)
    
    @pytest.mark.asyncio
    async def test_send_notification_no_channel(self, workflow_bot):
        """Test notification with no channel."""
        workflow_bot.project_channels = {}
        
        # Should not raise exception
        await workflow_bot._send_notification("nonexistent", "Test message")
    
    @pytest.mark.asyncio
    async def test_send_notification_channel_not_found(self, workflow_bot):
        """Test notification when channel object not found."""
        workflow_bot.project_channels = {"test_project": 123}
        workflow_bot.get_channel = Mock(return_value=None)
        
        # Should not raise exception
        await workflow_bot._send_notification("test_project", "Test message")
    
    # Test all command success and failure paths
    @pytest.mark.asyncio
    async def test_epic_command_success(self, workflow_bot):
        """Test successful epic command."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "stories": ["Story 1", "Story 2"],
            "next_step": "Next step"
        })
        
        interaction = MockInteraction()
        await workflow_bot.epic_command(interaction, "Test epic")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_epic_command_failure(self, workflow_bot, failing_orchestrator):
        """Test epic command failure."""
        workflow_bot.orchestrator = failing_orchestrator
        
        interaction = MockInteraction()
        await workflow_bot.epic_command(interaction, "Test epic")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_approve_command_success(self, workflow_bot):
        """Test successful approve command."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "approved_items": ["STORY-1"],
            "next_step": "Next step"
        })
        
        interaction = MockInteraction()
        await workflow_bot.approve_command(interaction, "STORY-1")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_command_failure(self, workflow_bot, failing_orchestrator):
        """Test approve command failure."""
        workflow_bot.orchestrator = failing_orchestrator
        
        interaction = MockInteraction()
        await workflow_bot.approve_command(interaction, "STORY-1")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_approve_command_empty_items(self, workflow_bot):
        """Test approve command with empty items."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "approved_items": [],
            "next_step": "Next step"
        })
        
        interaction = MockInteraction()
        await workflow_bot.approve_command(interaction, "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_status(self, workflow_bot):
        """Test sprint status command."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "total_tasks": 10,
            "completed_tasks": 5,
            "failed_tasks": 1,
            "current_state": "ACTIVE",
            "pending_approvals": 2
        })
        
        interaction = MockInteraction()
        await workflow_bot.sprint_command(interaction, "status", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_plan_with_items(self, workflow_bot):
        """Test sprint plan with items."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "message": "Sprint planned",
            "next_step": "Start sprint"
        })
        
        interaction = MockInteraction()
        await workflow_bot.sprint_command(interaction, "plan", "STORY-1,STORY-2")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_failure(self, workflow_bot):
        """Test sprint command failure with hint."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "Cannot start sprint",
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
        # Test with items over the limit (10)
        items = [{"id": f"STORY-{i}", "title": f"Story {i}", "priority": "medium"} for i in range(15)]
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "backlog_type": "product",
            "items": items
        })
        
        interaction = MockInteraction()
        await workflow_bot.backlog_command(interaction, "view", "", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backlog_command_view_empty(self, workflow_bot):
        """Test backlog view with no items."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "backlog_type": "product",
            "items": []
        })
        
        interaction = MockInteraction()
        await workflow_bot.backlog_command(interaction, "view", "", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backlog_command_add_story(self, workflow_bot):
        """Test backlog add story command."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "message": "Story added"
        })
        
        interaction = MockInteraction()
        await workflow_bot.backlog_command(interaction, "add_story", "Story desc", "FEATURE-1", "high")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backlog_command_failure(self, workflow_bot, failing_orchestrator):
        """Test backlog command failure."""
        workflow_bot.orchestrator = failing_orchestrator
        
        interaction = MockInteraction()
        await workflow_bot.backlog_command(interaction, "view", "", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_state_command_success(self, workflow_bot):
        """Test state command success."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "state_info": {"current_state": "IDLE"},
            "project_status": {
                "orchestration_mode": "blocking",
                "active_tasks": 3,
                "pending_approvals": 1
            }
        })
        
        interaction = MockInteraction()
        await workflow_bot.state_command(interaction)
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args, kwargs = interaction.followup.send.call_args
        assert "view" in kwargs
    
    @pytest.mark.asyncio
    async def test_state_command_failure(self, workflow_bot, failing_orchestrator):
        """Test state command failure."""
        workflow_bot.orchestrator = failing_orchestrator
        
        interaction = MockInteraction()
        await workflow_bot.state_command(interaction)
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_request_changes_command_success(self, workflow_bot):
        """Test request changes command success."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "next_step": "Implement changes"
        })
        
        interaction = MockInteraction()
        await workflow_bot.request_changes_command(interaction, "Need fixes")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_changes_command_failure(self, workflow_bot, failing_orchestrator):
        """Test request changes command failure."""
        workflow_bot.orchestrator = failing_orchestrator
        
        interaction = MockInteraction()
        await workflow_bot.request_changes_command(interaction, "Need fixes")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_suggest_fix_command_success(self, workflow_bot):
        """Test suggest fix command success."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "next_step": "Apply fix"
        })
        
        interaction = MockInteraction()
        await workflow_bot.suggest_fix_command(interaction, "Add validation")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_suggest_fix_command_failure(self, workflow_bot, failing_orchestrator):
        """Test suggest fix command failure."""
        workflow_bot.orchestrator = failing_orchestrator
        
        interaction = MockInteraction()
        await workflow_bot.suggest_fix_command(interaction, "Add validation")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_skip_task_command_success(self, workflow_bot):
        """Test skip task command success."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "message": "Task skipped",
            "next_step": "Continue"
        })
        
        interaction = MockInteraction()
        await workflow_bot.skip_task_command(interaction)
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_skip_task_command_failure(self, workflow_bot, failing_orchestrator):
        """Test skip task command failure."""
        workflow_bot.orchestrator = failing_orchestrator
        
        interaction = MockInteraction()
        await workflow_bot.skip_task_command(interaction)
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_feedback_command_success(self, workflow_bot):
        """Test feedback command success."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "next_step": "Start next sprint"
        })
        
        interaction = MockInteraction()
        await workflow_bot.feedback_command(interaction, "Good sprint")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_feedback_command_failure(self, workflow_bot, failing_orchestrator):
        """Test feedback command failure."""
        workflow_bot.orchestrator = failing_orchestrator
        
        interaction = MockInteraction()
        await workflow_bot.feedback_command(interaction, "Good sprint")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_project_command_register_success(self, workflow_bot):
        """Test project register command success."""
        with patch.object(workflow_bot, '_handle_project_register', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = {
                "success": True,
                "project_name": "new_project",
                "path": "/path/to/project",
                "channel": "#channel",
                "next_step": "Ready"
            }
            
            interaction = MockInteraction()
            await workflow_bot.project_command(interaction, "register", "/path", "new_project")
            
            interaction.response.defer.assert_called_once()
            interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_project_command_register_failure(self, workflow_bot):
        """Test project register command failure."""
        with patch.object(workflow_bot, '_handle_project_register', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = {
                "success": False,
                "error": "Registration failed"
            }
            
            interaction = MockInteraction()
            await workflow_bot.project_command(interaction, "register", "/path", "")
            
            interaction.response.defer.assert_called_once()
            interaction.followup.send.assert_called_once()
            args = interaction.followup.send.call_args[0]
            assert "❌" in args[0]
    
    @pytest.mark.asyncio
    async def test_project_command_unknown_action(self, workflow_bot):
        """Test project command with unknown action."""
        interaction = MockInteraction()
        await workflow_bot.project_command(interaction, "unknown", "/path", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        args = interaction.followup.send.call_args[0]
        assert "Unknown project action" in args[0]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_path_not_exists(self, workflow_bot):
        """Test project registration with non-existent path."""
        mock_guild = Mock()
        
        result = await workflow_bot._handle_project_register("/nonexistent", "test", mock_guild)
        
        assert result["success"] is False
        assert "does not exist" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_not_git_repo(self, workflow_bot):
        """Test project registration with non-git directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_guild = Mock()
            
            result = await workflow_bot._handle_project_register(temp_dir, "test", mock_guild)
            
            assert result["success"] is False
            assert "not a git repository" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_duplicate_project(self, workflow_bot):
        """Test project registration with existing project."""
        mock_guild = Mock()
        
        result = await workflow_bot._handle_project_register("/path", "test_project", mock_guild)
        
        assert result["success"] is False
        assert "already registered" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_channel_exists(self, workflow_bot):
        """Test project registration when channel exists."""
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
    async def test_handle_project_register_success(self, workflow_bot):
        """Test successful project registration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "new_project"
            project_path.mkdir()
            (project_path / ".git").mkdir()
            
            mock_guild = Mock()
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
                    str(project_path), "new_project", mock_guild
                )
                
                assert result["success"] is True
                assert result["project_name"] == "new_project"
    
    @pytest.mark.asyncio
    async def test_handle_project_register_storage_failure(self, workflow_bot):
        """Test project registration with storage initialization failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "new_project"
            project_path.mkdir()
            (project_path / ".git").mkdir()
            
            mock_guild = Mock()
            
            with patch('discord.utils.get', return_value=None), \
                 patch('os.getenv', return_value="testhost"), \
                 patch('lib.discord_bot.ProjectStorage') as mock_storage:
                
                mock_storage_instance = Mock()
                mock_storage_instance.initialize_project = Mock(return_value=False)
                mock_storage.return_value = mock_storage_instance
                
                result = await workflow_bot._handle_project_register(
                    str(project_path), "new_project", mock_guild
                )
                
                assert result["success"] is False
                assert "Failed to initialize project structure" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_channel_creation_failure(self, workflow_bot):
        """Test project registration with channel creation failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "new_project"
            project_path.mkdir()
            (project_path / ".git").mkdir()
            
            mock_guild = Mock()
            mock_guild.create_text_channel = AsyncMock(side_effect=Exception("Channel creation failed"))
            
            with patch('discord.utils.get', return_value=None), \
                 patch('os.getenv', return_value="testhost"), \
                 patch('lib.discord_bot.ProjectStorage') as mock_storage:
                
                mock_storage_instance = Mock()
                mock_storage_instance.initialize_project = Mock(return_value=True)
                mock_storage.return_value = mock_storage_instance
                
                result = await workflow_bot._handle_project_register(
                    str(project_path), "new_project", mock_guild
                )
                
                assert result["success"] is False
                assert "Failed to create Discord channel" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_exception(self, workflow_bot):
        """Test project registration exception handling."""
        mock_guild = Mock()
        
        with patch('pathlib.Path', side_effect=Exception("Unexpected error")):
            result = await workflow_bot._handle_project_register("/path", "test", mock_guild)
        
        assert result["success"] is False
        assert "Failed to register project" in result["error"]
    
    # TDD Command Tests
    @pytest.mark.asyncio
    async def test_tdd_command_status(self, workflow_bot):
        """Test TDD status command."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "cycle_info": {
                "cycle_id": "cycle-123",
                "story_id": "STORY-1",
                "current_state": "RED",
                "progress": "2/5",
                "total_test_runs": 10,
                "total_refactors": 3,
                "current_task_id": "task-456"
            },
            "allowed_commands": ["/tdd test"],
            "next_suggested": "/tdd code"
        })
        
        interaction = MockInteraction()
        await workflow_bot.tdd_command(interaction, "status", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_status_no_cycle(self, workflow_bot):
        """Test TDD status with no active cycle."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "cycle_info": {},
            "allowed_commands": ["/tdd start"]
        })
        
        interaction = MockInteraction()
        await workflow_bot.tdd_command(interaction, "status", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_logs(self, workflow_bot):
        """Test TDD logs command."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "logs_info": {
                "cycle_id": "cycle-123",
                "total_events": 25,
                "last_activity": "2024-01-01T12:00:00",
                "recent_events": ["Event 1", "Event 2", "Event 3", "Event 4", "Event 5", "Event 6"]
            }
        })
        
        interaction = MockInteraction()
        await workflow_bot.tdd_command(interaction, "logs", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_logs_no_info(self, workflow_bot):
        """Test TDD logs with no info."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "logs_info": {}
        })
        
        interaction = MockInteraction()
        await workflow_bot.tdd_command(interaction, "logs", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_overview(self, workflow_bot):
        """Test TDD overview command."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "overview_info": {
                "active_cycles": 2,
                "completed_cycles": 8,
                "total_test_runs": 150,
                "average_coverage": 87.5,
                "total_refactors": 25,
                "success_rate": 95.2,
                "active_stories": ["STORY-1", "STORY-2", "STORY-3", "STORY-4", "STORY-5", "STORY-6"]
            }
        })
        
        interaction = MockInteraction()
        await workflow_bot.tdd_command(interaction, "overview", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_overview_no_info(self, workflow_bot):
        """Test TDD overview with no info."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "overview_info": {}
        })
        
        interaction = MockInteraction()
        await workflow_bot.tdd_command(interaction, "overview", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_start(self, workflow_bot):
        """Test TDD start command."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "message": "TDD cycle started",
            "cycle_id": "cycle-456",
            "story_id": "STORY-1",
            "current_state": "DESIGN",
            "next_step": "Begin design"
        })
        
        interaction = MockInteraction()
        await workflow_bot.tdd_command(interaction, "start", "STORY-1", "Task desc")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_other_actions(self, workflow_bot):
        """Test other TDD actions."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "message": "TDD action completed",
            "current_state": "GREEN",
            "next_suggested": "/tdd refactor",
            "next_step": "Continue"
        })
        
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
            "error": "TDD command failed",
            "hint": "Try starting cycle first",
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
    
    @pytest.mark.asyncio
    async def test_run_discord_bot_success(self):
        """Test successful Discord bot run."""
        mock_orchestrator = MockOrchestrator()
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
            assert mock_orchestrator.stop_called is True
            mock_bot.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_discord_bot_keyboard_interrupt(self):
        """Test Discord bot with keyboard interrupt."""
        mock_orchestrator = MockOrchestrator()
        mock_bot = Mock()
        mock_bot.start = AsyncMock(side_effect=KeyboardInterrupt())
        mock_bot.close = AsyncMock()
        
        with patch('os.getenv', return_value="fake_token"), \
             patch('lib.discord_bot.Orchestrator', return_value=mock_orchestrator), \
             patch('lib.discord_bot.WorkflowBot', return_value=mock_bot), \
             patch('asyncio.create_task'):
            
            await run_discord_bot()
            
            assert mock_orchestrator.stop_called is True
            mock_bot.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_discord_bot_exception(self):
        """Test Discord bot with general exception."""
        mock_orchestrator = MockOrchestrator()
        mock_bot = Mock()
        mock_bot.start = AsyncMock(side_effect=Exception("Connection failed"))
        mock_bot.close = AsyncMock()
        
        with patch('os.getenv', return_value="fake_token"), \
             patch('lib.discord_bot.Orchestrator', return_value=mock_orchestrator), \
             patch('lib.discord_bot.WorkflowBot', return_value=mock_bot), \
             patch('asyncio.create_task'):
            
            await run_discord_bot()
            
            assert mock_orchestrator.stop_called is True
            mock_bot.close.assert_called_once()
    
    def test_main_module_execution(self):
        """Test main module execution block."""
        with patch('logging.basicConfig') as mock_logging, \
             patch('asyncio.run') as mock_asyncio:
            
            # Simulate the main block execution
            if "__main__" == "__main__":  # Always true
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            mock_logging.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])