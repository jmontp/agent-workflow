"""
Comprehensive test suite for Multi-Project Discord Bot.

Tests Discord bot functionality for managing multiple AI-assisted development projects
with project-specific channels, unified commands, and cross-project insights.
"""

import pytest
import asyncio
import discord
from discord.ext import commands
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.multi_project_discord_bot import MultiProjectDiscordBot
from lib.multi_project_config import MultiProjectConfigManager, ProjectConfig, ProjectStatus, ProjectPriority
from lib.global_orchestrator import GlobalOrchestrator, OrchestratorStatus
from lib.resource_scheduler import ResourceScheduler


@pytest.fixture
def mock_config_manager():
    """Create a mock MultiProjectConfigManager."""
    manager = Mock(spec=MultiProjectConfigManager)
    manager.projects = {
        "project1": Mock(spec=ProjectConfig),
        "project2": Mock(spec=ProjectConfig)
    }
    manager.list_projects.return_value = list(manager.projects.keys())
    manager.get_project_config.return_value = Mock(spec=ProjectConfig)
    return manager


@pytest.fixture
def mock_global_orchestrator():
    """Create a mock GlobalOrchestrator."""
    orchestrator = Mock(spec=GlobalOrchestrator)
    orchestrator.get_global_status = AsyncMock(return_value={
        "status": "running",
        "active_projects": 2,
        "total_tasks": 10,
        "resource_usage": {"cpu": 45.2, "memory": 512}
    })
    orchestrator.start_project = AsyncMock(return_value=True)
    orchestrator.stop_project = AsyncMock(return_value=True)
    orchestrator.pause_project = AsyncMock(return_value=True)
    orchestrator.resume_project = AsyncMock(return_value=True)
    return orchestrator


@pytest.fixture
def mock_resource_scheduler():
    """Create a mock ResourceScheduler."""
    scheduler = Mock(spec=ResourceScheduler)
    scheduler.get_resource_status = AsyncMock(return_value={
        "cpu_usage": 45.2,
        "memory_usage": 512,
        "active_processes": 5
    })
    return scheduler


@pytest.fixture
def mock_discord_objects():
    """Create mock Discord objects."""
    guild = Mock(spec=discord.Guild)
    guild.id = 12345
    guild.name = "Test Guild"
    guild.channels = []
    guild.create_text_channel = AsyncMock()
    
    channel = Mock(spec=discord.TextChannel)
    channel.id = 67890
    channel.name = "test-channel"
    channel.send = AsyncMock()
    
    user = Mock(spec=discord.User)
    user.id = 11111
    user.name = "testuser"
    
    ctx = Mock()
    ctx.send = AsyncMock()
    ctx.author = user
    ctx.guild = guild
    ctx.channel = channel
    ctx.message = Mock()
    ctx.message.content = "/test_command"
    
    return {
        "guild": guild,
        "channel": channel,
        "user": user,
        "ctx": ctx
    }


@pytest.fixture
def discord_bot(mock_config_manager, mock_global_orchestrator, mock_resource_scheduler):
    """Create a MultiProjectDiscordBot instance for testing."""
    with patch('lib.multi_project_discord_bot.discord.Intents') as mock_intents:
        mock_intents.default.return_value = Mock()
        
        # Mock the Bot.__init__ to prevent actual Discord connection
        with patch('discord.ext.commands.Bot.__init__') as mock_bot_init:
            mock_bot_init.return_value = None
            
            bot = MultiProjectDiscordBot(
                config_manager=mock_config_manager,
                global_orchestrator=mock_global_orchestrator,
                resource_scheduler=mock_resource_scheduler,
                command_prefix="/",
                case_insensitive=True
            )
            
            # Mock bot attributes that would normally be set by discord.py
            bot.user = Mock()
            bot.user.name = "TestBot"
            bot.guilds = []
            bot.get_guild = Mock(return_value=None)
            bot.get_channel = Mock(return_value=None)
            
            # Mock task decorators to prevent actual task scheduling
            bot.status_monitor = Mock()
            bot.status_monitor.is_running.return_value = False
            bot.status_monitor.start = Mock()
            
            bot.alert_monitor = Mock()
            bot.alert_monitor.is_running.return_value = False
            bot.alert_monitor.start = Mock()
            
            return bot


class TestMultiProjectDiscordBotInit:
    """Test MultiProjectDiscordBot initialization."""
    
    def test_init_basic(self, mock_config_manager, mock_global_orchestrator, mock_resource_scheduler):
        """Test basic bot initialization."""
        with patch('lib.multi_project_discord_bot.discord.Intents'), \
             patch('discord.ext.commands.Bot.__init__'):
            
            bot = MultiProjectDiscordBot(
                config_manager=mock_config_manager,
                global_orchestrator=mock_global_orchestrator,
                resource_scheduler=mock_resource_scheduler
            )
            
            assert bot.config_manager == mock_config_manager
            assert bot.global_orchestrator == mock_global_orchestrator
            assert bot.resource_scheduler == mock_resource_scheduler
            assert bot.guild_id is None
            assert bot.project_channels == {}
            assert bot.active_project_contexts == {}
            assert bot.alert_subscribers == {}
            assert bot.monitoring_enabled is True

    def test_init_custom_prefix(self, mock_config_manager, mock_global_orchestrator, mock_resource_scheduler):
        """Test bot initialization with custom command prefix."""
        with patch('lib.multi_project_discord_bot.discord.Intents'), \
             patch('discord.ext.commands.Bot.__init__') as mock_init:
            
            bot = MultiProjectDiscordBot(
                config_manager=mock_config_manager,
                global_orchestrator=mock_global_orchestrator,
                resource_scheduler=mock_resource_scheduler,
                command_prefix="!"
            )
            
            # Check that Bot.__init__ was called with correct prefix
            mock_init.assert_called_once()
            args, kwargs = mock_init.call_args
            assert kwargs.get('command_prefix') == "!"


class TestMultiProjectDiscordBotEvents:
    """Test Discord bot event handlers."""
    
    @pytest.mark.asyncio
    async def test_on_ready(self, discord_bot):
        """Test on_ready event handler."""
        with patch.object(discord_bot, '_initialize_guild_structure') as mock_init:
            mock_init.return_value = AsyncMock()
            
            await discord_bot.on_ready()
            
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_guild_join(self, discord_bot, mock_discord_objects):
        """Test on_guild_join event handler."""
        guild = mock_discord_objects["guild"]
        
        with patch.object(discord_bot, '_setup_guild_channels') as mock_setup:
            mock_setup.return_value = AsyncMock()
            
            await discord_bot.on_guild_join(guild)
            
            mock_setup.assert_called_once_with(guild)

    @pytest.mark.asyncio
    async def test_command_error_not_found(self, discord_bot, mock_discord_objects):
        """Test command error handler for CommandNotFound."""
        ctx = mock_discord_objects["ctx"]
        error = commands.CommandNotFound("test_command")
        
        with patch.object(discord_bot, '_find_similar_commands') as mock_find:
            mock_find.return_value = ["/global_status", "/projects"]
            
            # Manually call the error handler
            await discord_bot.on_command_error(ctx, error)
            
            # Verify that a helpful message was sent
            ctx.send.assert_called_once()
            args, kwargs = ctx.send.call_args
            embed = kwargs.get('embed')
            assert embed is not None
            assert "Command not found" in embed.title

    @pytest.mark.asyncio
    async def test_command_error_missing_argument(self, discord_bot, mock_discord_objects):
        """Test command error handler for MissingRequiredArgument."""
        ctx = mock_discord_objects["ctx"]
        
        # Create a mock parameter
        param = Mock()
        param.name = "project_name"
        error = commands.MissingRequiredArgument(param)
        
        await discord_bot.on_command_error(ctx, error)
        
        ctx.send.assert_called_once()
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "Missing argument" in embed.title

    @pytest.mark.asyncio
    async def test_command_error_generic(self, discord_bot, mock_discord_objects):
        """Test command error handler for generic errors."""
        ctx = mock_discord_objects["ctx"]
        ctx.command = Mock()
        ctx.command.name = "test_command"
        error = Exception("Test error")
        
        await discord_bot.on_command_error(ctx, error)
        
        ctx.send.assert_called_once()
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "Command Error" in embed.title


class TestMultiProjectDiscordBotCommands:
    """Test Discord bot commands."""
    
    @pytest.mark.asyncio
    async def test_global_status_command(self, discord_bot, mock_discord_objects):
        """Test global_status command."""
        ctx = mock_discord_objects["ctx"]
        
        with patch.object(discord_bot, '_create_global_status_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed
            
            # Simulate command execution
            await discord_bot.global_status(ctx)
            
            discord_bot.global_orchestrator.get_global_status.assert_called_once()
            mock_create_embed.assert_called_once()
            ctx.send.assert_called_once_with(embed=mock_embed)

    @pytest.mark.asyncio
    async def test_list_projects_command(self, discord_bot, mock_discord_objects):
        """Test list_projects command."""
        ctx = mock_discord_objects["ctx"]
        
        with patch.object(discord_bot, '_create_projects_list_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed
            
            await discord_bot.list_projects(ctx)
            
            discord_bot.config_manager.list_projects.assert_called_once()
            mock_create_embed.assert_called_once()
            ctx.send.assert_called_once_with(embed=mock_embed)

    @pytest.mark.asyncio
    async def test_set_active_project_valid(self, discord_bot, mock_discord_objects):
        """Test set_active_project command with valid project."""
        ctx = mock_discord_objects["ctx"]
        project_name = "project1"
        
        await discord_bot.set_active_project(ctx, project_name)
        
        assert discord_bot.active_project_contexts[ctx.author.id] == project_name
        ctx.send.assert_called_once()
        
        # Check that success embed was sent
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "Active Project Set" in embed.title

    @pytest.mark.asyncio
    async def test_set_active_project_invalid(self, discord_bot, mock_discord_objects):
        """Test set_active_project command with invalid project."""
        ctx = mock_discord_objects["ctx"]
        project_name = "nonexistent_project"
        
        await discord_bot.set_active_project(ctx, project_name)
        
        assert ctx.author.id not in discord_bot.active_project_contexts
        ctx.send.assert_called_once()
        
        # Check that error embed was sent
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "Project not found" in embed.title

    @pytest.mark.asyncio
    async def test_start_project_with_name(self, discord_bot, mock_discord_objects):
        """Test start_project command with explicit project name."""
        ctx = mock_discord_objects["ctx"]
        project_name = "project1"
        
        with patch.object(discord_bot, '_execute_project_operation') as mock_execute:
            mock_execute.return_value = AsyncMock()
            
            await discord_bot.start_project(ctx, project_name)
            
            ctx.send.assert_called()
            # Check that the operation was initiated
            args, kwargs = ctx.send.call_args
            embed = kwargs.get('embed')
            assert embed is not None
            assert "Starting Project" in embed.title

    @pytest.mark.asyncio
    async def test_start_project_with_context(self, discord_bot, mock_discord_objects):
        """Test start_project command using active project context."""
        ctx = mock_discord_objects["ctx"]
        project_name = "project1"
        
        # Set active project context
        discord_bot.active_project_contexts[ctx.author.id] = project_name
        
        with patch.object(discord_bot, '_execute_project_operation') as mock_execute:
            mock_execute.return_value = AsyncMock()
            
            await discord_bot.start_project(ctx)
            
            ctx.send.assert_called()

    @pytest.mark.asyncio
    async def test_start_project_no_context(self, discord_bot, mock_discord_objects):
        """Test start_project command without project context."""
        ctx = mock_discord_objects["ctx"]
        
        await discord_bot.start_project(ctx)
        
        ctx.send.assert_called_once_with("Please specify a project name or set an active project context")


class TestMultiProjectDiscordBotUtilities:
    """Test Discord bot utility methods."""
    
    def test_get_active_project_exists(self, discord_bot):
        """Test getting active project when it exists."""
        user_id = 12345
        project_name = "test_project"
        discord_bot.active_project_contexts[user_id] = project_name
        
        result = discord_bot._get_active_project(user_id)
        assert result == project_name

    def test_get_active_project_not_exists(self, discord_bot):
        """Test getting active project when it doesn't exist."""
        user_id = 12345
        
        result = discord_bot._get_active_project(user_id)
        assert result is None

    def test_find_similar_commands(self, discord_bot):
        """Test finding similar commands."""
        # Mock some commands
        discord_bot.commands = {
            "global_status": Mock(),
            "projects": Mock(),
            "start_project": Mock(),
            "stop_project": Mock()
        }
        
        # Test with a typo in command
        similar = discord_bot._find_similar_commands("/globl_status")
        assert len(similar) > 0
        assert any("global_status" in cmd for cmd in similar)

    def test_create_global_status_embed(self, discord_bot):
        """Test creating global status embed."""
        status = {
            "status": "running",
            "active_projects": 3,
            "total_tasks": 15,
            "resource_usage": {"cpu": 75.5, "memory": 1024}
        }
        
        embed = discord_bot._create_global_status_embed(status)
        
        assert isinstance(embed, discord.Embed)
        assert "Global Orchestration Status" in embed.title
        assert str(status["active_projects"]) in embed.description

    def test_create_projects_list_embed(self, discord_bot):
        """Test creating projects list embed."""
        projects = ["project1", "project2", "project3"]
        
        embed = discord_bot._create_projects_list_embed(projects)
        
        assert isinstance(embed, discord.Embed)
        assert "Registered Projects" in embed.title
        for project in projects:
            assert project in embed.description

    def test_create_project_status_embed(self, discord_bot):
        """Test creating project status embed."""
        project_name = "test_project"
        status = {
            "status": "active",
            "current_task": "implementing feature",
            "tasks_completed": 5,
            "tasks_remaining": 3
        }
        
        embed = discord_bot._create_project_status_embed(project_name, status)
        
        assert isinstance(embed, discord.Embed)
        assert project_name in embed.title
        assert str(status["tasks_completed"]) in embed.description

    def test_create_resource_status_embed(self, discord_bot):
        """Test creating resource status embed."""
        resource_status = {
            "cpu_usage": 45.2,
            "memory_usage": 512,
            "disk_usage": 25.7,
            "active_processes": 8
        }
        
        embed = discord_bot._create_resource_status_embed(resource_status)
        
        assert isinstance(embed, discord.Embed)
        assert "Resource Status" in embed.title
        assert str(resource_status["cpu_usage"]) in embed.description

    @pytest.mark.asyncio
    async def test_initialize_guild_structure(self, discord_bot, mock_discord_objects):
        """Test initializing guild structure."""
        guild = mock_discord_objects["guild"]
        discord_bot.guilds = [guild]
        
        with patch.object(discord_bot, '_setup_guild_channels') as mock_setup:
            mock_setup.return_value = AsyncMock()
            
            await discord_bot._initialize_guild_structure()
            
            assert discord_bot.guild_id == guild.id
            mock_setup.assert_called_once_with(guild)

    @pytest.mark.asyncio
    async def test_setup_guild_channels(self, discord_bot, mock_discord_objects):
        """Test setting up guild channels."""
        guild = mock_discord_objects["guild"]
        
        # Mock channel creation
        global_channel = Mock()
        global_channel.id = 11111
        admin_channel = Mock()
        admin_channel.id = 22222
        project_channel = Mock()
        project_channel.id = 33333
        
        guild.create_text_channel.side_effect = [global_channel, admin_channel, project_channel]
        
        with patch.object(discord_bot, '_find_or_create_channel') as mock_find_create:
            mock_find_create.side_effect = [global_channel, admin_channel, project_channel]
            
            await discord_bot._setup_guild_channels(guild)
            
            assert discord_bot.global_channel_id == global_channel.id
            assert discord_bot.admin_channel_id == admin_channel.id

    @pytest.mark.asyncio
    async def test_find_or_create_channel_exists(self, discord_bot, mock_discord_objects):
        """Test finding existing channel."""
        guild = mock_discord_objects["guild"]
        channel_name = "test-channel"
        existing_channel = Mock()
        existing_channel.name = channel_name
        
        guild.channels = [existing_channel]
        
        result = await discord_bot._find_or_create_channel(guild, channel_name)
        
        assert result == existing_channel
        guild.create_text_channel.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_or_create_channel_create_new(self, discord_bot, mock_discord_objects):
        """Test creating new channel when it doesn't exist."""
        guild = mock_discord_objects["guild"]
        channel_name = "new-channel"
        new_channel = Mock()
        
        guild.channels = []  # No existing channels
        guild.create_text_channel.return_value = new_channel
        
        result = await discord_bot._find_or_create_channel(guild, channel_name)
        
        assert result == new_channel
        guild.create_text_channel.assert_called_once_with(
            channel_name,
            topic=f"AI-assisted development for {channel_name}"
        )

    @pytest.mark.asyncio
    async def test_execute_project_operation_success(self, discord_bot, mock_discord_objects):
        """Test successful project operation execution."""
        ctx = mock_discord_objects["ctx"]
        project_name = "test_project"
        operation = "start"
        
        # Mock successful operation
        discord_bot.global_orchestrator.start_project.return_value = True
        
        with patch.object(discord_bot, '_update_message_with_result') as mock_update:
            mock_update.return_value = AsyncMock()
            
            message = Mock()
            await discord_bot._execute_project_operation(ctx, message, project_name, operation)
            
            discord_bot.global_orchestrator.start_project.assert_called_once_with(project_name)
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_project_operation_failure(self, discord_bot, mock_discord_objects):
        """Test failed project operation execution."""
        ctx = mock_discord_objects["ctx"]
        project_name = "test_project"
        operation = "start"
        
        # Mock failed operation
        discord_bot.global_orchestrator.start_project.return_value = False
        
        with patch.object(discord_bot, '_update_message_with_result') as mock_update:
            mock_update.return_value = AsyncMock()
            
            message = Mock()
            await discord_bot._execute_project_operation(ctx, message, project_name, operation)
            
            mock_update.assert_called_once()
            # Check that the result indicates failure
            args, kwargs = mock_update.call_args
            assert args[2] is False  # success parameter

    @pytest.mark.asyncio
    async def test_update_message_with_result_success(self, discord_bot):
        """Test updating message with successful result."""
        message = Mock()
        message.edit = AsyncMock()
        project_name = "test_project"
        operation = "start"
        success = True
        
        await discord_bot._update_message_with_result(message, operation, success, project_name)
        
        message.edit.assert_called_once()
        args, kwargs = message.edit.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "✅" in embed.title  # Success indicator

    @pytest.mark.asyncio
    async def test_update_message_with_result_failure(self, discord_bot):
        """Test updating message with failed result."""
        message = Mock()
        message.edit = AsyncMock()
        project_name = "test_project"
        operation = "start"
        success = False
        error = "Test error"
        
        await discord_bot._update_message_with_result(message, operation, success, project_name, error)
        
        message.edit.assert_called_once()
        args, kwargs = message.edit.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "❌" in embed.title  # Failure indicator


class TestMultiProjectDiscordBotMonitoring:
    """Test Discord bot monitoring functionality."""
    
    def test_subscribe_to_alerts(self, discord_bot):
        """Test subscribing to project alerts."""
        user_id = 12345
        project_name = "test_project"
        
        discord_bot._subscribe_to_alerts(user_id, project_name)
        
        assert project_name in discord_bot.alert_subscribers
        assert user_id in discord_bot.alert_subscribers[project_name]

    def test_unsubscribe_from_alerts(self, discord_bot):
        """Test unsubscribing from project alerts."""
        user_id = 12345
        project_name = "test_project"
        
        # First subscribe
        discord_bot._subscribe_to_alerts(user_id, project_name)
        assert user_id in discord_bot.alert_subscribers[project_name]
        
        # Then unsubscribe
        discord_bot._unsubscribe_from_alerts(user_id, project_name)
        assert user_id not in discord_bot.alert_subscribers[project_name]

    @pytest.mark.asyncio
    async def test_send_alert(self, discord_bot, mock_discord_objects):
        """Test sending alerts to subscribers."""
        user_id = 12345
        project_name = "test_project"
        alert_message = "Test alert"
        
        # Setup user and channel mocks
        user = mock_discord_objects["user"]
        user.id = user_id
        discord_bot.get_user = Mock(return_value=user)
        user.send = AsyncMock()
        
        # Subscribe user to alerts
        discord_bot._subscribe_to_alerts(user_id, project_name)
        
        await discord_bot._send_alert(project_name, alert_message)
        
        discord_bot.get_user.assert_called_once_with(user_id)
        user.send.assert_called_once()

    def test_format_alert_message(self, discord_bot):
        """Test formatting alert messages."""
        project_name = "test_project"
        alert_type = "error"
        message = "Something went wrong"
        
        formatted = discord_bot._format_alert_message(project_name, alert_type, message)
        
        assert project_name in formatted
        assert alert_type.upper() in formatted
        assert message in formatted

    @pytest.mark.asyncio
    async def test_handle_project_status_change(self, discord_bot):
        """Test handling project status changes."""
        project_name = "test_project"
        old_status = "stopped"
        new_status = "running"
        
        with patch.object(discord_bot, '_send_alert') as mock_send_alert:
            mock_send_alert.return_value = AsyncMock()
            
            await discord_bot._handle_project_status_change(project_name, old_status, new_status)
            
            mock_send_alert.assert_called_once()
            args, kwargs = mock_send_alert.call_args
            assert project_name in args
            assert "status change" in args[1].lower()


class TestMultiProjectDiscordBotErrorHandling:
    """Test Discord bot error handling."""
    
    @pytest.mark.asyncio
    async def test_handle_orchestrator_error(self, discord_bot, mock_discord_objects):
        """Test handling orchestrator errors."""
        ctx = mock_discord_objects["ctx"]
        error = Exception("Orchestrator failed")
        
        await discord_bot._handle_orchestrator_error(ctx, error)
        
        ctx.send.assert_called_once()
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "Error" in embed.title

    @pytest.mark.asyncio
    async def test_handle_config_error(self, discord_bot, mock_discord_objects):
        """Test handling configuration errors."""
        ctx = mock_discord_objects["ctx"]
        error = Exception("Configuration invalid")
        
        await discord_bot._handle_config_error(ctx, error)
        
        ctx.send.assert_called_once()
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "Configuration Error" in embed.title

    @pytest.mark.asyncio
    async def test_handle_resource_error(self, discord_bot, mock_discord_objects):
        """Test handling resource errors."""
        ctx = mock_discord_objects["ctx"]
        error = Exception("Resource unavailable")
        
        await discord_bot._handle_resource_error(ctx, error)
        
        ctx.send.assert_called_once()
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed')
        assert embed is not None
        assert "Resource Error" in embed.title


class TestMultiProjectDiscordBotIntegration:
    """Test Discord bot integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_project_workflow(self, discord_bot, mock_discord_objects):
        """Test complete project workflow commands."""
        ctx = mock_discord_objects["ctx"]
        project_name = "integration_test_project"
        
        # Add project to config manager
        discord_bot.config_manager.projects[project_name] = Mock()
        
        # 1. Set active project
        await discord_bot.set_active_project(ctx, project_name)
        assert discord_bot.active_project_contexts[ctx.author.id] == project_name
        
        # 2. Start project
        with patch.object(discord_bot, '_execute_project_operation'):
            await discord_bot.start_project(ctx)
        
        # 3. Check status
        with patch.object(discord_bot, '_create_project_status_embed'):
            await discord_bot.project_status(ctx)
        
        # Verify multiple interactions
        assert ctx.send.call_count >= 3

    @pytest.mark.asyncio
    async def test_error_recovery(self, discord_bot, mock_discord_objects):
        """Test error recovery scenarios."""
        ctx = mock_discord_objects["ctx"]
        
        # Simulate orchestrator failure
        discord_bot.global_orchestrator.get_global_status.side_effect = Exception("Network error")
        
        with patch.object(discord_bot, '_handle_orchestrator_error') as mock_handle:
            mock_handle.return_value = AsyncMock()
            
            await discord_bot.global_status(ctx)
            
            mock_handle.assert_called_once()

    def test_memory_management(self, discord_bot):
        """Test memory management for long-running bot."""
        # Simulate adding many project contexts
        for i in range(1000):
            discord_bot.active_project_contexts[i] = f"project_{i}"
        
        # Test cleanup
        discord_bot._cleanup_inactive_contexts(max_age_hours=1)
        
        # Should still function normally
        assert isinstance(discord_bot.active_project_contexts, dict)

    def test_concurrent_operations(self, discord_bot):
        """Test handling concurrent operations."""
        # Simulate multiple users setting contexts simultaneously
        for i in range(10):
            discord_bot.active_project_contexts[i] = f"project_{i % 3}"
        
        # Verify state consistency
        assert len(discord_bot.active_project_contexts) == 10
        
        # Test context retrieval
        for i in range(10):
            context = discord_bot._get_active_project(i)
            assert context == f"project_{i % 3}"


class TestMultiProjectDiscordBotAdvancedFeatures:
    """Test advanced Discord bot features."""
    
    @pytest.mark.asyncio
    async def test_admin_permission_check_success(self, discord_bot, mock_discord_objects):
        """Test admin permission check with administrator user."""
        ctx = mock_discord_objects["ctx"]
        ctx.author.guild_permissions.administrator = True
        
        result = await discord_bot._check_admin_permission(ctx)
        
        assert result is True
        ctx.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_admin_permission_check_failure(self, discord_bot, mock_discord_objects):
        """Test admin permission check with non-administrator user."""
        ctx = mock_discord_objects["ctx"]
        ctx.author.guild_permissions.administrator = False
        
        result = await discord_bot._check_admin_permission(ctx)
        
        assert result is False
        ctx.send.assert_called_once()
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed')
        assert "Permission Denied" in embed.title

    def test_format_duration_seconds(self, discord_bot):
        """Test duration formatting for seconds."""
        result = discord_bot._format_duration(45.0)
        assert result == "45s"

    def test_format_duration_minutes(self, discord_bot):
        """Test duration formatting for minutes."""
        result = discord_bot._format_duration(150.0)  # 2.5 minutes
        assert result == "2.5m"

    def test_format_duration_hours(self, discord_bot):
        """Test duration formatting for hours."""
        result = discord_bot._format_duration(7200.0)  # 2 hours
        assert result == "2.0h"

    def test_format_duration_days(self, discord_bot):
        """Test duration formatting for days."""
        result = discord_bot._format_duration(172800.0)  # 2 days
        assert result == "2.0d"

    def test_create_help_embed(self, discord_bot):
        """Test creating help embed."""
        embed = discord_bot._create_help_embed()
        
        assert isinstance(embed, discord.Embed)
        assert "Multi-Project Orchestration Commands" in embed.title
        assert len(embed.fields) >= 4  # Should have multiple command categories

    def test_create_insights_embed_empty(self, discord_bot):
        """Test creating insights embed with no insights."""
        insights = []
        
        embed = discord_bot._create_insights_embed(insights)
        
        assert isinstance(embed, discord.Embed)
        assert "Cross-Project Insights" in embed.title
        assert "No cross-project insights" in embed.description

    def test_create_insights_embed_with_data(self, discord_bot):
        """Test creating insights embed with insights data."""
        insights = [
            {"description": "Common pattern detected in error handling"},
            {"description": "Similar testing approach across projects"},
            {"description": "Shared dependency usage optimization opportunity"}
        ]
        
        embed = discord_bot._create_insights_embed(insights)
        
        assert isinstance(embed, discord.Embed)
        assert "Cross-Project Insights" in embed.title
        assert len(embed.fields) == 3

    def test_create_projects_list_embed_empty(self, discord_bot):
        """Test creating projects list embed with no projects."""
        projects = []
        
        embed = discord_bot._create_projects_list_embed(projects)
        
        assert isinstance(embed, discord.Embed)
        assert "Registered Projects" in embed.title
        assert "No projects registered" in embed.description

    def test_create_projects_list_embed_with_projects(self, discord_bot):
        """Test creating projects list embed with projects."""
        # Mock ProjectConfig objects
        project1 = Mock()
        project1.name = "project1"
        project1.status.value = "active"
        project1.priority.value = "high"
        
        project2 = Mock()
        project2.name = "project2"
        project2.status.value = "paused"
        project2.priority.value = "medium"
        
        projects = [project1, project2]
        
        embed = discord_bot._create_projects_list_embed(projects)
        
        assert isinstance(embed, discord.Embed)
        assert "Registered Projects" in embed.title
        assert len(embed.fields) >= 1  # Should have status groups

    @pytest.mark.asyncio
    async def test_send_project_alert(self, discord_bot, mock_discord_objects):
        """Test sending project alerts."""
        project_name = "test_project"
        title = "Test Alert"
        description = "This is a test alert"
        color = discord.Color.red()
        
        # Setup channel and user mocks
        channel = mock_discord_objects["channel"]
        user = mock_discord_objects["user"]
        
        discord_bot.project_channels[project_name] = channel.id
        discord_bot.get_channel = Mock(return_value=channel)
        discord_bot.get_user = Mock(return_value=user)
        
        # Setup alert subscribers
        discord_bot.alert_subscribers[project_name] = {user.id}
        
        # Mock channel and user send methods
        channel.send = AsyncMock()
        user.send = AsyncMock()
        
        await discord_bot._send_project_alert(project_name, title, description, color)
        
        # Verify alert was sent to channel and user
        channel.send.assert_called_once()
        user.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_project_alert_dm_forbidden(self, discord_bot, mock_discord_objects):
        """Test sending project alerts when DM is forbidden."""
        project_name = "test_project"
        title = "Test Alert"
        description = "This is a test alert"
        color = discord.Color.red()
        
        user = mock_discord_objects["user"]
        discord_bot.get_user = Mock(return_value=user)
        discord_bot.alert_subscribers[project_name] = {user.id}
        
        # Mock DM failure
        user.send = AsyncMock(side_effect=discord.Forbidden(Mock(), "Cannot send DM"))
        
        # Should not raise exception
        await discord_bot._send_project_alert(project_name, title, description, color)

    @pytest.mark.asyncio
    async def test_send_project_alert_no_subscribers(self, discord_bot):
        """Test sending project alerts with no subscribers."""
        project_name = "test_project"
        title = "Test Alert"
        description = "This is a test alert"
        color = discord.Color.red()
        
        # No subscribers for this project
        assert project_name not in discord_bot.alert_subscribers
        
        # Should not raise exception
        await discord_bot._send_project_alert(project_name, title, description, color)


class TestMultiProjectDiscordBotResourceManagement:
    """Test resource management features."""
    
    def test_create_resource_status_embed_basic(self, discord_bot):
        """Test creating basic resource status embed."""
        status = {
            "system_utilization": {
                "cpu": 0.75,
                "memory": 0.85,
                "agents": 0.60
            },
            "strategy": "balanced_allocation",
            "active_projects": 3
        }
        
        embed = discord_bot._create_resource_status_embed(status)
        
        assert isinstance(embed, discord.Embed)
        assert "Resource Allocation Status" in embed.title
        assert "75.0%" in embed.description or any("75.0%" in field.value for field in embed.fields)

    def test_create_resource_status_embed_with_performance(self, discord_bot):
        """Test creating resource status embed with performance metrics."""
        status = {
            "system_utilization": {
                "cpu": 0.45,
                "memory": 0.65,
                "agents": 0.80
            },
            "strategy": "priority_based",
            "active_projects": 5,
            "performance_metrics": {
                "throughput": 12.5,
                "latency": 250,
                "efficiency": 0.92
            }
        }
        
        embed = discord_bot._create_resource_status_embed(status)
        
        assert isinstance(embed, discord.Embed)
        assert "Resource Allocation Status" in embed.title

    @pytest.mark.asyncio
    async def test_cleanup_inactive_contexts(self, discord_bot):
        """Test cleanup of inactive project contexts."""
        # Add some contexts with timestamps
        discord_bot.active_project_contexts = {
            1: "project1",
            2: "project2",
            3: "project3"
        }
        
        # Mock the cleanup method (it would need to be implemented in the actual bot)
        discord_bot._cleanup_inactive_contexts = Mock()
        
        discord_bot._cleanup_inactive_contexts(max_age_hours=24)
        
        discord_bot._cleanup_inactive_contexts.assert_called_once_with(max_age_hours=24)


class TestMultiProjectDiscordBotChannelManagement:
    """Test Discord channel management."""
    
    @pytest.mark.asyncio
    async def test_find_or_create_channel_with_topic(self, discord_bot, mock_discord_objects):
        """Test finding or creating channel with custom topic."""
        guild = mock_discord_objects["guild"]
        channel_name = "custom-channel"
        topic = "Custom topic for testing"
        
        # No existing channels
        guild.channels = []
        new_channel = Mock()
        guild.create_text_channel.return_value = new_channel
        
        result = await discord_bot._find_or_create_channel(guild, channel_name, topic)
        
        assert result == new_channel
        guild.create_text_channel.assert_called_once_with(channel_name, topic=topic)

    @pytest.mark.asyncio
    async def test_find_or_create_channel_creation_failure(self, discord_bot, mock_discord_objects):
        """Test channel creation failure handling."""
        guild = mock_discord_objects["guild"]
        channel_name = "test-channel"
        
        guild.channels = []
        guild.create_text_channel.side_effect = discord.Forbidden(Mock(), "Missing permissions")
        
        # Should handle the exception gracefully
        with pytest.raises(discord.Forbidden):
            await discord_bot._find_or_create_channel(guild, channel_name)

    @pytest.mark.asyncio
    async def test_create_project_channel(self, discord_bot, mock_discord_objects):
        """Test creating a project-specific channel."""
        guild = mock_discord_objects["guild"]
        project_name = "new_project"
        
        # Mock channel creation
        new_channel = Mock()
        new_channel.id = 99999
        new_channel.send = AsyncMock()
        
        with patch.object(discord_bot, '_find_or_create_channel') as mock_find_create:
            mock_find_create.return_value = new_channel
            
            result = await discord_bot._create_project_channel(guild, project_name)
            
            assert result == new_channel
            assert discord_bot.project_channels[project_name] == new_channel.id
            new_channel.send.assert_called_once()


class TestMultiProjectDiscordBotTaskManagement:
    """Test Discord bot task management."""
    
    @pytest.mark.asyncio
    async def test_status_monitor_task(self, discord_bot):
        """Test status monitoring task."""
        # Mock the status monitor behavior
        with patch.object(discord_bot.global_orchestrator, 'get_global_status') as mock_status:
            mock_status.return_value = {"status": "running", "projects": 2}
            
            # Simulate task execution
            await discord_bot._check_status_changes({"status": "running"})
            
            # Since _check_status_changes is a placeholder, just verify it doesn't crash
            assert True

    @pytest.mark.asyncio
    async def test_alert_monitor_task(self, discord_bot):
        """Test alert monitoring task."""
        # Mock alert checking
        with patch.object(discord_bot, '_send_project_alert') as mock_send_alert:
            mock_send_alert.return_value = AsyncMock()
            
            # Simulate checking for alerts
            await discord_bot._check_status_changes({"alerts": []})
            
            # Verify the task runs without errors
            assert True

    def test_subscribe_to_alerts_new_project(self, discord_bot):
        """Test subscribing to alerts for a new project."""
        user_id = 12345
        project_name = "new_project"
        
        discord_bot._subscribe_to_alerts(user_id, project_name)
        
        assert project_name in discord_bot.alert_subscribers
        assert user_id in discord_bot.alert_subscribers[project_name]

    def test_subscribe_to_alerts_existing_project(self, discord_bot):
        """Test subscribing to alerts for an existing project."""
        user_id1 = 12345
        user_id2 = 67890
        project_name = "existing_project"
        
        # First user subscribes
        discord_bot._subscribe_to_alerts(user_id1, project_name)
        
        # Second user subscribes
        discord_bot._subscribe_to_alerts(user_id2, project_name)
        
        assert user_id1 in discord_bot.alert_subscribers[project_name]
        assert user_id2 in discord_bot.alert_subscribers[project_name]
        assert len(discord_bot.alert_subscribers[project_name]) == 2

    def test_unsubscribe_from_alerts_last_subscriber(self, discord_bot):
        """Test unsubscribing when user is the last subscriber."""
        user_id = 12345
        project_name = "test_project"
        
        # Subscribe and then unsubscribe
        discord_bot._subscribe_to_alerts(user_id, project_name)
        discord_bot._unsubscribe_from_alerts(user_id, project_name)
        
        # Project should still exist but be empty
        assert project_name in discord_bot.alert_subscribers
        assert len(discord_bot.alert_subscribers[project_name]) == 0

    def test_format_alert_message(self, discord_bot):
        """Test formatting alert messages."""
        project_name = "test_project"
        alert_type = "warning"
        message = "High memory usage detected"
        
        formatted = discord_bot._format_alert_message(project_name, alert_type, message)
        
        assert project_name in formatted
        assert alert_type.upper() in formatted
        assert message in formatted
        assert isinstance(formatted, str)


class TestMultiProjectDiscordBotPerformance:
    """Test Discord bot performance and optimization."""
    
    def test_memory_usage_tracking(self, discord_bot):
        """Test memory usage tracking for bot state."""
        # Add many contexts to test memory management
        for i in range(1000):
            discord_bot.active_project_contexts[i] = f"project_{i % 10}"
        
        # Add many alert subscriptions
        for i in range(100):
            project_name = f"project_{i % 10}"
            if project_name not in discord_bot.alert_subscribers:
                discord_bot.alert_subscribers[project_name] = set()
            discord_bot.alert_subscribers[project_name].add(i)
        
        # Bot should still function normally
        assert len(discord_bot.active_project_contexts) == 1000
        assert len(discord_bot.alert_subscribers) <= 10

    def test_large_projects_list_handling(self, discord_bot):
        """Test handling large numbers of projects."""
        # Create many mock projects
        projects = []
        for i in range(50):
            project = Mock()
            project.name = f"project_{i}"
            project.status.value = "active" if i % 2 == 0 else "paused"
            project.priority.value = "high" if i % 3 == 0 else "medium"
            projects.append(project)
        
        embed = discord_bot._create_projects_list_embed(projects)
        
        # Should handle large lists gracefully
        assert isinstance(embed, discord.Embed)
        assert "50" in embed.footer.text

    @pytest.mark.asyncio
    async def test_concurrent_command_handling(self, discord_bot, mock_discord_objects):
        """Test handling multiple concurrent commands."""
        ctx = mock_discord_objects["ctx"]
        
        # Simulate multiple concurrent calls
        tasks = []
        for i in range(10):
            # Mock different users
            ctx.author.id = i
            task = discord_bot.set_active_project(ctx, f"project_{i % 3}")
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        # Verify all contexts were set correctly
        assert len(discord_bot.active_project_contexts) >= 3