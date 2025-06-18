"""
Comprehensive unit tests for Discord Bot - targeting 95%+ line coverage.

Tests the Discord bot for AI Agent TDD-Scrum Workflow management,
including slash commands, state visualization, HITL approval processes,
WebSocket integration, and error handling scenarios.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

# Create comprehensive Discord mock structure
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
    def green():
        return "green"
    
    @staticmethod
    def blue():
        return "blue"
    
    @staticmethod
    def red():
        return "red"
    
    @staticmethod
    def orange():
        return "orange"
    
    @staticmethod
    def yellow():
        return "yellow"
    
    @staticmethod
    def purple():
        return "purple"

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
        # Mock implementation for discord.utils.get
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

class MockView:
    def __init__(self, timeout=300):
        self.timeout = timeout

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

# Set up comprehensive Discord mocks
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

# Mock commands
from discord.ext import commands
commands.Bot = MockBot
commands.Context = Mock

# Mock app_commands
discord.app_commands = Mock()
discord.app_commands.command = lambda **kwargs: lambda func: func
discord.app_commands.describe = lambda **kwargs: lambda func: func
discord.app_commands.choices = lambda **kwargs: lambda func: func
discord.app_commands.Choice = Mock

# Mock UI components
discord.ui.View = MockView
discord.ui.Button = Mock
discord.ui.button = lambda **kwargs: lambda func: func

# Now import the Discord bot modules
from lib.discord_bot import StateView, WorkflowBot, run_discord_bot


class MockOrchestrator:
    """Comprehensive mock orchestrator for testing."""
    
    def __init__(self):
        self.projects = {"test_project": Mock(), "project2": Mock()}
        self.run_count = 0
        self.stop_called = False
        
    async def handle_command(self, command, project_name, **kwargs):
        """Mock command handling with comprehensive responses."""
        self.run_count += 1
        
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
                "approved_items": kwargs.get("item_ids", ["STORY-1", "STORY-2"]),
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
                        {"id": "STORY-2", "title": "Data validation", "priority": "medium"},
                        {"id": "STORY-3", "title": "UI improvements", "priority": "low"}
                    ] * 4  # 12 items to test limit
                }
            else:
                return {
                    "success": True,
                    "message": "Backlog updated"
                }
        elif "/tdd" in command:
            return self._handle_tdd_command(command, **kwargs)
        elif "/request_changes" in command:
            return {
                "success": True,
                "message": "Changes requested",
                "next_step": "Review and implement changes"
            }
        elif "/suggest_fix" in command:
            return {
                "success": True, 
                "message": "Fix suggestion recorded",
                "next_step": "Apply suggested fix"
            }
        elif "/skip_task" in command:
            return {
                "success": True,
                "message": "Task skipped",
                "next_step": "Continue with next task"
            }
        elif "/feedback" in command:
            return {
                "success": True,
                "message": "Feedback recorded",
                "next_step": "Start next sprint"
            }
        else:
            return {
                "success": True,
                "message": "Command executed successfully",
                "next_step": "Continue workflow"
            }
    
    def _handle_tdd_command(self, command, **kwargs):
        """Handle TDD-specific commands."""
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
                        "Code implementation started",
                        "Green state achieved",
                        "Refactoring initiated"
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
                    "active_stories": ["STORY-1", "STORY-2", "STORY-3"]
                }
            }
        elif "start" in command:
            return {
                "success": True,
                "message": "TDD cycle started successfully",
                "cycle_id": "cycle-456",
                "story_id": kwargs.get("story_id", "STORY-1"),
                "current_state": "DESIGN",
                "next_step": "Begin with design phase"
            }
        else:
            return {
                "success": True,
                "message": f"TDD {command.split()[-1]} completed",
                "current_state": "CODE_GREEN",
                "next_suggested": "/tdd refactor",
                "next_step": "Continue TDD cycle"
            }
    
    async def run(self):
        """Mock orchestrator run method."""
        pass
    
    def stop(self):
        """Mock orchestrator stop method."""
        self.stop_called = True


class TestStateViewComprehensive:
    """Comprehensive tests for StateView class - all methods and edge cases."""
    
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
    
    def test_state_view_init_default_project(self, mock_orchestrator):
        """Test StateView initialization with default project."""
        view = StateView(mock_orchestrator)
        assert view.project_name == "default"
    
    @pytest.mark.asyncio
    async def test_show_allowed_commands_success(self, state_view):
        """Test showing allowed commands successfully."""
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_allowed_commands(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert call_args[1]["ephemeral"] is True
        assert "embed" in call_args[1]
    
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
    async def test_show_allowed_commands_empty_list(self, state_view):
        """Test showing allowed commands with empty command list."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "state_info": {"allowed_commands": []}
        })
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_allowed_commands(interaction, button)
        
        interaction.response.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_state_diagram_success(self, state_view):
        """Test showing state diagram successfully."""
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_state_diagram(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_show_state_diagram_failure(self, state_view):
        """Test showing state diagram when command fails."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={"success": False})
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_state_diagram(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "❌ Failed to get diagram" in str(call_args[0])
    
    @pytest.mark.asyncio
    async def test_show_project_status_success(self, state_view):
        """Test showing project status successfully."""
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_project_status(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_show_project_status_failure(self, state_view):
        """Test showing project status when command fails."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={"success": False})
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_project_status(interaction, button)
        
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "❌ Failed to get project status" in str(call_args[0])
    
    @pytest.mark.asyncio
    async def test_show_project_status_missing_fields(self, state_view):
        """Test showing project status with missing fields."""
        state_view.orchestrator.handle_command = AsyncMock(return_value={
            "success": True
            # Missing all the expected fields
        })
        interaction = MockInteraction()
        button = Mock()
        
        await state_view.show_project_status(interaction, button)
        
        interaction.response.send_message.assert_called_once()


class TestWorkflowBotComprehensive:
    """Comprehensive tests for WorkflowBot class - all methods and edge cases."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        return MockOrchestrator()
    
    @pytest.fixture
    def workflow_bot(self, mock_orchestrator):
        """Create WorkflowBot for testing."""
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
        assert workflow_bot.command_prefix == "!"
        assert workflow_bot.description == "AI Agent TDD-Scrum Workflow Bot"
    
    @pytest.mark.asyncio
    async def test_setup_hook_success(self, workflow_bot):
        """Test setup hook successful sync."""
        await workflow_bot.setup_hook()
        workflow_bot.tree.sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_hook_sync_failure(self, workflow_bot):
        """Test setup hook when sync fails."""
        workflow_bot.tree.sync.side_effect = Exception("Sync failed")
        
        # Should not raise exception
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
        mock_channel = Mock()
        mock_channel.id = 54321
        mock_guild.create_text_channel = AsyncMock(return_value=mock_channel)
        workflow_bot.guilds = [mock_guild]
        
        with patch('os.getenv', return_value="testhost"), \
             patch('discord.utils.get', return_value=None):
            await workflow_bot._ensure_project_channels()
        
        assert mock_guild.create_text_channel.call_count == 2  # 2 projects in mock
        assert "test_project" in workflow_bot.project_channels
        assert "project2" in workflow_bot.project_channels
    
    @pytest.mark.asyncio
    async def test_ensure_project_channels_existing_channel(self, workflow_bot):
        """Test ensuring project channels when channel exists."""
        mock_channel = Mock()
        mock_channel.id = 98765
        mock_channel.name = "testhost-test_project"
        mock_guild = Mock()
        mock_guild.channels = [mock_channel]
        mock_guild.create_text_channel = AsyncMock()
        workflow_bot.guilds = [mock_guild]
        
        with patch('os.getenv', return_value="testhost"), \
             patch('discord.utils.get', return_value=mock_channel):
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
        
        with patch('os.getenv', return_value="testhost"), \
             patch('discord.utils.get', return_value=None):
            # Should not raise exception
            await workflow_bot._ensure_project_channels()
        
        assert mock_guild.create_text_channel.call_count == 2
    
    @pytest.mark.asyncio
    async def test_ensure_project_channels_no_guilds(self, workflow_bot):
        """Test ensuring project channels with no guilds."""
        workflow_bot.guilds = []
        
        # Should not raise exception
        await workflow_bot._ensure_project_channels()
    
    @pytest.mark.asyncio
    async def test_get_project_from_channel_found(self, workflow_bot):
        """Test getting project name from channel ID."""
        workflow_bot.project_channels = {"project1": 123, "project2": 456}
        
        result = await workflow_bot._get_project_from_channel(123)
        assert result == "project1"
        
        result = await workflow_bot._get_project_from_channel(456)
        assert result == "project2"
    
    @pytest.mark.asyncio
    async def test_get_project_from_channel_not_found(self, workflow_bot):
        """Test getting project name from unknown channel ID."""
        workflow_bot.project_channels = {"project1": 123}
        
        result = await workflow_bot._get_project_from_channel(999)
        assert result == "default"
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self, workflow_bot):
        """Test sending notification to project channel."""
        mock_channel = Mock()
        mock_channel.send = AsyncMock()
        workflow_bot.project_channels = {"test_project": 123}
        workflow_bot.get_channel = Mock(return_value=mock_channel)
        
        embed = MockEmbed(title="Test", description="Test message")
        await workflow_bot._send_notification("test_project", "Test message", embed)
        
        mock_channel.send.assert_called_once_with("Test message", embed=embed)
    
    @pytest.mark.asyncio
    async def test_send_notification_no_channel_id(self, workflow_bot):
        """Test sending notification when project has no channel."""
        workflow_bot.project_channels = {}
        
        # Should not raise exception
        await workflow_bot._send_notification("nonexistent", "Test message")
    
    @pytest.mark.asyncio
    async def test_send_notification_channel_not_found(self, workflow_bot):
        """Test sending notification when channel object not found."""
        workflow_bot.project_channels = {"test_project": 123}
        workflow_bot.get_channel = Mock(return_value=None)
        
        # Should not raise exception
        await workflow_bot._send_notification("test_project", "Test message")
    
    # Epic Command Tests
    @pytest.mark.asyncio
    async def test_epic_command_success(self, workflow_bot):
        """Test successful epic command."""
        interaction = MockInteraction()
        
        await workflow_bot.epic_command(interaction, "Create user management system")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        assert "embed" in call_args[1]
    
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
    async def test_epic_command_no_stories(self, workflow_bot):
        """Test epic command with no proposed stories."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "stories": [],
            "next_step": "Review epic"
        })
        interaction = MockInteraction()
        
        await workflow_bot.epic_command(interaction, "Test epic")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    # Approve Command Tests
    @pytest.mark.asyncio
    async def test_approve_command_with_items(self, workflow_bot):
        """Test approve command with specific items."""
        interaction = MockInteraction()
        
        await workflow_bot.approve_command(interaction, "STORY-1, STORY-2, STORY-3")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_command_empty_items(self, workflow_bot):
        """Test approve command with empty items string."""
        interaction = MockInteraction()
        
        await workflow_bot.approve_command(interaction, "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_command_whitespace_items(self, workflow_bot):
        """Test approve command with whitespace in items."""
        interaction = MockInteraction()
        
        await workflow_bot.approve_command(interaction, " STORY-1 ,  , STORY-2 ")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_command_no_approved_items(self, workflow_bot):
        """Test approve command when no items are approved."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "approved_items": [],
            "next_step": "No items to approve"
        })
        interaction = MockInteraction()
        
        await workflow_bot.approve_command(interaction, "STORY-1")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    # Sprint Command Tests
    @pytest.mark.asyncio
    async def test_sprint_command_status(self, workflow_bot):
        """Test sprint status command."""
        interaction = MockInteraction()
        
        await workflow_bot.sprint_command(interaction, "status", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        assert "embed" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_sprint_command_plan_with_items(self, workflow_bot):
        """Test sprint plan command with items."""
        interaction = MockInteraction()
        
        await workflow_bot.sprint_command(interaction, "plan", "STORY-1, STORY-2")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_plan_without_items(self, workflow_bot):
        """Test sprint plan command without items."""
        interaction = MockInteraction()
        
        await workflow_bot.sprint_command(interaction, "plan", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_other_actions(self, workflow_bot):
        """Test other sprint actions."""
        interaction = MockInteraction()
        
        for action in ["start", "pause", "resume"]:
            interaction.response.defer.reset_mock()
            interaction.followup.send.reset_mock()
            
            await workflow_bot.sprint_command(interaction, action, "")
            
            interaction.response.defer.assert_called_once()
            interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sprint_command_failure_with_hint(self, workflow_bot):
        """Test sprint command failure with hint."""
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
        call_args = interaction.followup.send.call_args
        assert "embed" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_sprint_command_failure_without_hint(self, workflow_bot):
        """Test sprint command failure without hint."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "Generic error"
        })
        interaction = MockInteraction()
        
        await workflow_bot.sprint_command(interaction, "start", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    # Backlog Command Tests
    @pytest.mark.asyncio
    async def test_backlog_command_view_with_items(self, workflow_bot):
        """Test backlog view command with items."""
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
    async def test_backlog_command_add_story_full_params(self, workflow_bot):
        """Test backlog add story with all parameters."""
        interaction = MockInteraction()
        
        await workflow_bot.backlog_command(
            interaction, "add_story", "New story description", "FEATURE-1", "high"
        )
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backlog_command_add_story_minimal_params(self, workflow_bot):
        """Test backlog add story with minimal parameters."""
        interaction = MockInteraction()
        
        await workflow_bot.backlog_command(interaction, "add_story", "Story", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backlog_command_prioritize(self, workflow_bot):
        """Test backlog prioritize command."""
        interaction = MockInteraction()
        
        await workflow_bot.backlog_command(interaction, "prioritize", "", "", "top")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backlog_command_failure(self, workflow_bot):
        """Test backlog command failure."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "Backlog operation failed"
        })
        interaction = MockInteraction()
        
        await workflow_bot.backlog_command(interaction, "view", "", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args[0][0]
        assert "❌" in call_args
    
    # State Command Tests
    @pytest.mark.asyncio
    async def test_state_command_success(self, workflow_bot):
        """Test state command success."""
        interaction = MockInteraction()
        
        await workflow_bot.state_command(interaction)
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        assert "view" in call_args[1]
        assert "embed" in call_args[1]
    
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
    
    # Other Command Tests
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
        
        await workflow_bot.suggest_fix_command(interaction, "Add null checks")
        
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
        
        await workflow_bot.feedback_command(interaction, "Sprint went well")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    # Project Command Tests
    @pytest.mark.asyncio
    async def test_project_command_register_success(self, workflow_bot):
        """Test project register command success."""
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
    async def test_project_command_register_failure(self, workflow_bot):
        """Test project register command failure."""
        interaction = MockInteraction()
        
        with patch.object(workflow_bot, '_handle_project_register', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = {
                "success": False,
                "error": "Project registration failed"
            }
            
            await workflow_bot.project_command(interaction, "register", "/invalid/path", "")
            
            interaction.response.defer.assert_called_once()
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args[0][0]
            assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_project_command_unknown_action(self, workflow_bot):
        """Test project command with unknown action."""
        interaction = MockInteraction()
        
        await workflow_bot.project_command(interaction, "unknown", "/path", "")
        
        interaction.response.defer.assert_called_once()
        call_args = interaction.followup.send.call_args[0][0]
        assert "Unknown project action" in call_args
    
    # Project Registration Tests
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
        """Test project registration with existing project name."""
        mock_guild = Mock()
        
        result = await workflow_bot._handle_project_register(
            "/some/path", "test_project", mock_guild  # Already exists in mock
        )
        
        assert result["success"] is False
        assert "already registered" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_channel_exists(self, workflow_bot):
        """Test project registration when Discord channel exists."""
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
    async def test_handle_project_register_storage_init_failure(self, workflow_bot):
        """Test project registration when storage initialization fails."""
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
        """Test project registration when channel creation fails."""
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
    async def test_handle_project_register_exception_handling(self, workflow_bot):
        """Test project registration exception handling."""
        mock_guild = Mock()
        
        # Cause an exception by mocking Path to raise
        with patch('pathlib.Path', side_effect=Exception("Unexpected error")):
            result = await workflow_bot._handle_project_register(
                "/some/path", "test", mock_guild
            )
        
        assert result["success"] is False
        assert "Failed to register project" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_project_register_default_name(self, workflow_bot):
        """Test project registration with default name from path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "auto_named_project"
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
                    str(project_path), "", mock_guild  # Empty name
                )
                
                assert result["success"] is True
                assert result["project_name"] == "auto_named_project"
    
    # TDD Command Tests
    @pytest.mark.asyncio
    async def test_tdd_command_status_with_cycle_info(self, workflow_bot):
        """Test TDD status command with cycle info."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "status", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_status_no_cycle(self, workflow_bot):
        """Test TDD status command with no active cycle."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "cycle_info": {},
            "allowed_commands": ["/tdd start"],
            "next_suggested": "/tdd start"
        })
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "status", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_logs_with_events(self, workflow_bot):
        """Test TDD logs command with events."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "logs", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_logs_no_events(self, workflow_bot):
        """Test TDD logs command with no events."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "logs_info": {}
        })
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "logs", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_overview_with_data(self, workflow_bot):
        """Test TDD overview command with data."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "overview", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_overview_no_data(self, workflow_bot):
        """Test TDD overview command with no data."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "overview_info": {}
        })
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "overview", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_start_with_params(self, workflow_bot):
        """Test TDD start command with story ID and task description."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "start", "STORY-1", "Implement user auth")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_start_minimal_params(self, workflow_bot):
        """Test TDD start command with minimal parameters."""
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "start", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_other_actions(self, workflow_bot):
        """Test other TDD commands."""
        interaction = MockInteraction()
        
        actions = ["design", "test", "code", "refactor", "commit", "run_tests", "next", "abort"]
        for action in actions:
            interaction.response.defer.reset_mock()
            interaction.followup.send.reset_mock()
            
            await workflow_bot.tdd_command(interaction, action, "", "")
            
            interaction.response.defer.assert_called_once()
            interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tdd_command_failure_comprehensive(self, workflow_bot):
        """Test TDD command failure with all error info."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "No active TDD cycle",
            "hint": "Start a cycle first with /tdd start",
            "current_state": "IDLE",
            "allowed_commands": ["/tdd start", "/tdd overview"]
        })
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "code", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        assert "embed" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_tdd_command_failure_minimal_info(self, workflow_bot):
        """Test TDD command failure with minimal error info."""
        workflow_bot.orchestrator.handle_command = AsyncMock(return_value={
            "success": False,
            "error": "Command failed"
        })
        interaction = MockInteraction()
        
        await workflow_bot.tdd_command(interaction, "test", "", "")
        
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()


class TestModuleFunctionsComprehensive:
    """Comprehensive tests for module-level functions."""
    
    @pytest.mark.asyncio
    async def test_run_discord_bot_no_token(self):
        """Test running Discord bot without token."""
        with patch('os.getenv', return_value=None):
            # Should return early without error
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
        """Test running Discord bot with keyboard interrupt."""
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
    async def test_run_discord_bot_exception_during_start(self):
        """Test running Discord bot with exception during start."""
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


class TestIntegrationScenariosComprehensive:
    """Comprehensive integration scenario tests."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_sequence(self):
        """Test complete workflow sequence through Discord commands."""
        orchestrator = MockOrchestrator()
        bot = WorkflowBot(orchestrator)
        bot.project_channels = {"test_project": 12345}
        
        # Simulate complete workflow
        interaction = MockInteraction()
        
        # Epic creation
        await bot.epic_command(interaction, "User management system")
        
        # Approval
        await bot.approve_command(interaction, "STORY-1,STORY-2")
        
        # Sprint planning
        await bot.sprint_command(interaction, "plan", "STORY-1,STORY-2")
        
        # Sprint start
        await bot.sprint_command(interaction, "start", "")
        
        # Sprint status check
        await bot.sprint_command(interaction, "status", "")
        
        # State check
        await bot.state_command(interaction)
        
        # Verify orchestrator was called multiple times
        assert orchestrator.run_count > 5
    
    @pytest.mark.asyncio
    async def test_tdd_workflow_complete_cycle(self):
        """Test complete TDD workflow cycle."""
        orchestrator = MockOrchestrator()
        bot = WorkflowBot(orchestrator)
        bot.project_channels = {"test_project": 12345}
        
        interaction = MockInteraction()
        
        # Start TDD cycle
        await bot.tdd_command(interaction, "start", "STORY-1", "User auth implementation")
        
        # Progress through all TDD phases
        tdd_actions = ["design", "test", "code", "run_tests", "refactor", "commit"]
        for action in tdd_actions:
            await bot.tdd_command(interaction, action, "", "")
        
        # Check status and logs
        await bot.tdd_command(interaction, "status", "", "")
        await bot.tdd_command(interaction, "logs", "", "")
        await bot.tdd_command(interaction, "overview", "", "")
        
        # Complete cycle
        await bot.tdd_command(interaction, "next", "", "")
        
        assert orchestrator.run_count > 10
    
    @pytest.mark.asyncio
    async def test_error_recovery_sequence(self):
        """Test error handling and recovery sequence."""
        orchestrator = MockOrchestrator()
        
        # Create error scenarios
        error_responses = [
            {"success": False, "error": "Invalid state", "hint": "Complete epic first"},
            {"success": False, "error": "Missing dependencies"},
            {"success": False, "error": "Resource unavailable", "current_state": "BLOCKED"},
            {"success": True, "message": "Recovery successful"}
        ]
        
        orchestrator.handle_command = AsyncMock(side_effect=error_responses)
        
        bot = WorkflowBot(orchestrator)
        bot.project_channels = {"test_project": 12345}
        
        interaction = MockInteraction()
        
        # Try commands that fail, then succeed
        await bot.sprint_command(interaction, "start", "")
        await bot.epic_command(interaction, "Test epic")
        await bot.tdd_command(interaction, "start", "", "")
        await bot.state_command(interaction)
        
        assert orchestrator.handle_command.call_count == 4
    
    @pytest.mark.asyncio
    async def test_multi_project_channel_management(self):
        """Test multi-project channel management."""
        orchestrator = MockOrchestrator()
        bot = WorkflowBot(orchestrator)
        
        # Mock multiple guilds and channels
        mock_guild1 = Mock()
        mock_guild1.channels = []
        mock_guild1.create_text_channel = AsyncMock(side_effect=lambda name, **kwargs: Mock(id=hash(name) % 10000))
        
        mock_guild2 = Mock()
        mock_guild2.channels = []
        mock_guild2.create_text_channel = AsyncMock(side_effect=lambda name, **kwargs: Mock(id=hash(name) % 10000 + 5000))
        
        bot.guilds = [mock_guild1, mock_guild2]
        
        with patch('os.getenv', return_value="testhost"), \
             patch('discord.utils.get', return_value=None):
            
            await bot._ensure_project_channels()
        
        # Should create channels for both projects in both guilds
        assert mock_guild1.create_text_channel.call_count == 2
        assert mock_guild2.create_text_channel.call_count == 2
        assert len(bot.project_channels) == 2
    
    @pytest.mark.asyncio
    async def test_command_parameter_variations(self):
        """Test commands with various parameter combinations."""
        orchestrator = MockOrchestrator()
        bot = WorkflowBot(orchestrator)
        bot.project_channels = {"test_project": 12345}
        
        interaction = MockInteraction()
        
        # Test backlog command variations
        await bot.backlog_command(interaction, "view", "", "", "")
        await bot.backlog_command(interaction, "add_story", "Story 1", "", "")
        await bot.backlog_command(interaction, "add_story", "Story 2", "FEATURE-1", "")
        await bot.backlog_command(interaction, "add_story", "Story 3", "FEATURE-2", "high")
        await bot.backlog_command(interaction, "prioritize", "", "", "top")
        
        # Test sprint command variations
        await bot.sprint_command(interaction, "plan", "")
        await bot.sprint_command(interaction, "plan", "STORY-1")
        await bot.sprint_command(interaction, "plan", "STORY-1,STORY-2,STORY-3")
        
        # Test approve command variations
        await bot.approve_command(interaction, "")
        await bot.approve_command(interaction, "STORY-1")
        await bot.approve_command(interaction, " STORY-1 , STORY-2 , ")
        
        assert orchestrator.run_count > 10
    
    @pytest.mark.asyncio
    async def test_notification_system(self):
        """Test notification system to project channels."""
        orchestrator = MockOrchestrator()
        bot = WorkflowBot(orchestrator)
        
        # Set up mock channels
        mock_channel1 = Mock()
        mock_channel1.send = AsyncMock()
        mock_channel2 = Mock()
        mock_channel2.send = AsyncMock()
        
        bot.project_channels = {"project1": 123, "project2": 456}
        bot.get_channel = Mock(side_effect=lambda cid: mock_channel1 if cid == 123 else mock_channel2)
        
        # Test notifications
        await bot._send_notification("project1", "Test message 1")
        await bot._send_notification("project2", "Test message 2")
        
        embed = MockEmbed(title="Test", description="Test embed")
        await bot._send_notification("project1", "Message with embed", embed)
        
        # Test notification to non-existent project
        await bot._send_notification("nonexistent", "This should not send")
        
        # Verify calls
        mock_channel1.send.assert_has_calls([
            call("Test message 1", embed=None),
            call("Message with embed", embed=embed)
        ])
        mock_channel2.send.assert_called_once_with("Test message 2", embed=None)
    
    @pytest.mark.asyncio
    async def test_edge_case_handling(self):
        """Test various edge cases and boundary conditions."""
        orchestrator = MockOrchestrator()
        bot = WorkflowBot(orchestrator)
        bot.project_channels = {"test_project": 12345}
        
        interaction = MockInteraction()
        
        # Test with very long strings
        long_description = "x" * 2000
        await bot.epic_command(interaction, long_description)
        
        # Test with special characters
        special_chars = "!@#$%^&*()[]{}|;:,.<>?"
        await bot.suggest_fix_command(interaction, special_chars)
        
        # Test with empty/whitespace strings
        await bot.request_changes_command(interaction, "   ")
        await bot.feedback_command(interaction, "\n\t\r")
        
        # Test with None-like values in orchestrator responses
        orchestrator.handle_command = AsyncMock(return_value={
            "success": True,
            "stories": None,
            "next_step": None,
            "message": None
        })
        
        await bot.epic_command(interaction, "Test epic")
        
        assert orchestrator.run_count > 0


class TestStateViewButtonInteractions:
    """Test StateView button interaction edge cases."""
    
    @pytest.fixture
    def state_view(self):
        """Create StateView with mock orchestrator."""
        orchestrator = MockOrchestrator()
        return StateView(orchestrator, "test_project")
    
    @pytest.mark.asyncio
    async def test_button_timeout_handling(self, state_view):
        """Test button view timeout."""
        # StateView has timeout=300
        assert state_view.timeout == 300
    
    @pytest.mark.asyncio
    async def test_concurrent_button_clicks(self, state_view):
        """Test concurrent button interactions."""
        interaction1 = MockInteraction()
        interaction2 = MockInteraction()
        interaction3 = MockInteraction()
        
        button = Mock()
        
        # Simulate concurrent button clicks
        tasks = [
            state_view.show_allowed_commands(interaction1, button),
            state_view.show_state_diagram(interaction2, button),
            state_view.show_project_status(interaction3, button)
        ]
        
        await asyncio.gather(*tasks)
        
        # All interactions should complete
        interaction1.response.send_message.assert_called_once()
        interaction2.response.send_message.assert_called_once()
        interaction3.response.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_button_interaction_exceptions(self, state_view):
        """Test button interactions with orchestrator exceptions."""
        state_view.orchestrator.handle_command = AsyncMock(side_effect=Exception("Orchestrator error"))
        
        interaction = MockInteraction()
        button = Mock()
        
        # Should handle exception gracefully
        await state_view.show_allowed_commands(interaction, button)
        
        # Should still attempt to send response
        interaction.response.send_message.assert_called_once()


class TestWorkflowBotEdgeCases:
    """Test WorkflowBot edge cases and error conditions."""
    
    @pytest.fixture
    def workflow_bot(self):
        """Create WorkflowBot with mock orchestrator."""
        orchestrator = MockOrchestrator()
        bot = WorkflowBot(orchestrator)
        bot.user = Mock()
        bot.user.id = 123456
        bot.guilds = []
        bot.get_channel = Mock()
        bot.tree = Mock()
        bot.tree.sync = AsyncMock(return_value=[])
        return bot
    
    @pytest.mark.asyncio
    async def test_command_with_orchestrator_exception(self, workflow_bot):
        """Test command handling when orchestrator raises exception."""
        workflow_bot.orchestrator.handle_command = AsyncMock(side_effect=Exception("Orchestrator failed"))
        
        interaction = MockInteraction()
        
        # Should handle exception gracefully
        await workflow_bot.epic_command(interaction, "Test epic")
        
        interaction.response.defer.assert_called_once()
        # Should still attempt followup, but may fail
    
    @pytest.mark.asyncio
    async def test_channel_id_variations(self, workflow_bot):
        """Test with various channel ID scenarios."""
        workflow_bot.project_channels = {
            "project1": 0,  # Edge case: zero ID
            "project2": -1,  # Edge case: negative ID
            "project3": 2**63 - 1  # Edge case: max int
        }
        
        # Test each scenario
        result1 = await workflow_bot._get_project_from_channel(0)
        assert result1 == "project1"
        
        result2 = await workflow_bot._get_project_from_channel(-1)
        assert result2 == "project2"
        
        result3 = await workflow_bot._get_project_from_channel(2**63 - 1)
        assert result3 == "project3"
    
    @pytest.mark.asyncio
    async def test_project_registration_race_condition(self, workflow_bot):
        """Test project registration race condition handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "race_project"
            project_path.mkdir()
            (project_path / ".git").mkdir()
            
            mock_guild = Mock()
            mock_channel = Mock()
            mock_channel.id = 12345
            mock_guild.create_text_channel = AsyncMock(return_value=mock_channel)
            
            # Simulate race condition - project gets added during registration
            async def add_project_during_registration(*args, **kwargs):
                workflow_bot.orchestrator.projects["race_project"] = Mock()
                return mock_channel
            
            mock_guild.create_text_channel.side_effect = add_project_during_registration
            
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
                    str(project_path), "race_project", mock_guild
                )
                
                # Should still succeed despite race condition
                assert result["success"] is True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])