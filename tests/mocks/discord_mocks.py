"""
Discord API Mock Framework

Comprehensive mocking infrastructure for discord.py library used in 
discord_bot.py (385 lines) and related Discord integrations.

Provides realistic simulation of:
- Discord Bot lifecycle and events
- Channel operations and interactions
- User management and authentication
- Message handling and responses
- Slash command processing
- Webhook management
- Error conditions and rate limiting

Designed for government audit compliance with 95%+ test coverage requirements.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Union
from unittest.mock import AsyncMock, Mock, MagicMock
from enum import Enum

logger = logging.getLogger(__name__)


class MockDiscordChannelType(Enum):
    """Mock Discord channel types"""
    TEXT = 0
    DM = 1
    VOICE = 2
    GROUP_DM = 3
    CATEGORY = 4
    NEWS = 5
    STORE = 6
    NEWS_THREAD = 10
    PUBLIC_THREAD = 11
    PRIVATE_THREAD = 12
    STAGE_VOICE = 13


class MockDiscordUser:
    """Mock Discord User object with realistic behavior"""
    
    def __init__(self, user_id: int = None, username: str = None, discriminator: str = None):
        self.id = user_id or random.randint(100000000000000000, 999999999999999999)
        self.name = username or f"test_user_{random.randint(1000, 9999)}"
        self.discriminator = discriminator or f"{random.randint(1000, 9999)}"
        self.bot = False
        self.avatar = None
        self.created_at = datetime.now(timezone.utc)
        
    def __str__(self):
        return f"{self.name}#{self.discriminator}"
        
    def mention(self):
        return f"<@{self.id}>"


class MockDiscordMessage:
    """Mock Discord Message object with realistic behavior"""
    
    def __init__(self, content: str = "", author: MockDiscordUser = None, channel=None):
        self.id = random.randint(100000000000000000, 999999999999999999)
        self.content = content
        self.author = author or MockDiscordUser()
        self.channel = channel
        self.guild = channel.guild if channel else None
        self.created_at = datetime.now(timezone.utc)
        self.edited_at = None
        self.reactions = []
        self.attachments = []
        self.embeds = []
        self.mentions = []
        self.mention_everyone = False
        self.pinned = False
        self.type = 0  # DEFAULT
        self._delete_called = False
        self._edit_called = False
        
    async def delete(self, delay: float = None):
        """Mock message deletion"""
        if delay:
            await asyncio.sleep(delay)
        self._delete_called = True
        logger.debug(f"Mock message {self.id} deleted")
        
    async def edit(self, content: str = None, embed=None, embeds=None):
        """Mock message editing"""
        if content:
            self.content = content
        self.edited_at = datetime.now(timezone.utc)
        self._edit_called = True
        logger.debug(f"Mock message {self.id} edited")
        
    async def add_reaction(self, emoji):
        """Mock reaction addition"""
        self.reactions.append(emoji)
        logger.debug(f"Mock reaction {emoji} added to message {self.id}")
        
    async def pin(self):
        """Mock message pinning"""
        self.pinned = True
        logger.debug(f"Mock message {self.id} pinned")


class MockDiscordChannel:
    """Mock Discord Channel object with realistic behavior"""
    
    def __init__(self, channel_id: int = None, name: str = None, guild=None):
        self.id = channel_id or random.randint(100000000000000000, 999999999999999999)
        self.name = name or f"test-channel-{random.randint(1000, 9999)}"
        self.guild = guild
        self.type = MockDiscordChannelType.TEXT
        self.topic = None
        self.position = 0
        self.nsfw = False
        self.slowmode_delay = 0
        self.category = None
        self.created_at = datetime.now(timezone.utc)
        self.permissions_synced = True
        self._message_history = []
        self._send_called = False
        self._typing_started = False
        
    def __str__(self):
        return self.name
        
    def mention(self):
        return f"<#{self.id}>"
        
    async def send(self, content: str = None, embed=None, embeds=None, file=None, 
                   files=None, view=None, ephemeral: bool = False, 
                   reference=None, mention_author: bool = True):
        """Mock message sending with realistic behavior and failure scenarios"""
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Enhanced failure scenarios for better integration testing
        failure_chance = random.random()
        
        # Simulate rate limiting (5% chance)
        if failure_chance < 0.05:
            from discord.errors import HTTPException
            await asyncio.sleep(random.uniform(1.0, 5.0))
            raise HTTPException(response=Mock(status=429), message="Too Many Requests")
        
        # Simulate connection errors (2% chance)
        elif failure_chance < 0.07:
            from discord.errors import ConnectionClosed
            raise ConnectionClosed(Mock(), code=1000)
        
        # Simulate permissions errors (1% chance)
        elif failure_chance < 0.08:
            from discord.errors import Forbidden
            raise Forbidden(response=Mock(status=403), message="Missing Permissions")
        
        # Simulate message too long error (1% chance if content > 1500 chars)
        elif content and len(content) > 1500 and failure_chance < 0.09:
            from discord.errors import HTTPException
            raise HTTPException(response=Mock(status=400), message="Message too long")
            
        message = MockDiscordMessage(
            content=content or "",
            author=MockDiscordUser(username="test_bot", discriminator="0000"),
            channel=self
        )
        
        if embed:
            message.embeds = [embed]
        if embeds:
            message.embeds = embeds
            
        self._message_history.append(message)
        self._send_called = True
        
        logger.debug(f"Mock message sent to channel {self.name}: {content}")
        return message
        
    async def typing(self):
        """Mock typing indicator"""
        self._typing_started = True
        logger.debug(f"Mock typing started in channel {self.name}")
        
    async def trigger_typing(self):
        """Mock typing trigger"""
        return self.typing()
        
    def history(self, limit: int = 100, before=None, after=None, around=None):
        """Mock message history"""
        return MockAsyncIterator(self._message_history[-limit:])
        
    async def purge(self, limit: int = 100, check=None, before=None, after=None):
        """Mock message purging"""
        deleted_count = min(limit, len(self._message_history))
        self._message_history = self._message_history[:-deleted_count]
        logger.debug(f"Mock purged {deleted_count} messages from channel {self.name}")
        return deleted_count


class MockAsyncIterator:
    """Mock async iterator for Discord message history"""
    
    def __init__(self, items: List):
        self.items = items
        self.index = 0
        
    def __aiter__(self):
        return self
        
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


class MockDiscordGuild:
    """Mock Discord Guild (server) object"""
    
    def __init__(self, guild_id: int = None, name: str = None):
        self.id = guild_id or random.randint(100000000000000000, 999999999999999999)
        self.name = name or f"Test Server {random.randint(1000, 9999)}"
        self.owner = MockDiscordUser(username="server_owner")
        self.member_count = random.randint(10, 1000)
        self.created_at = datetime.now(timezone.utc)
        self.channels = []
        self.members = []
        self.roles = []
        
    def get_channel(self, channel_id: int):
        """Get channel by ID"""
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None
        
    def get_member(self, user_id: int):
        """Get member by user ID"""
        for member in self.members:
            if member.id == user_id:
                return member
        return None


class MockDiscordBot:
    """
    Comprehensive Discord Bot mock with realistic behavior simulation.
    
    Provides full simulation of discord.py Bot functionality including:
    - Command handling and registration
    - Event system simulation
    - Channel and guild management
    - User interaction simulation
    - Slash command processing
    - Error handling and rate limiting
    """
    
    def __init__(self, command_prefix: str = "!", intents=None):
        self.command_prefix = command_prefix
        self.intents = intents
        self.user = MockDiscordUser(username="test_bot", discriminator="0000")
        self.user.bot = True
        self.guilds = []
        self.channels = []
        self.users = []
        self.latency = random.uniform(0.05, 0.2)  # Realistic latency
        self.is_ready = False
        self.is_closed = False
        self._commands = {}
        self._slash_commands = {}
        self._event_handlers = {}
        self._command_invocations = []
        self._events_fired = []
        
        # Mock common events
        self.on_ready = AsyncMock()
        self.on_message = AsyncMock()
        self.on_command_error = AsyncMock()
        self.on_guild_join = AsyncMock()
        self.on_guild_remove = AsyncMock()
        
    async def start(self, token: str, reconnect: bool = True):
        """Mock bot startup"""
        await asyncio.sleep(random.uniform(0.5, 2.0))  # Simulate connection time
        self.is_ready = True
        await self.on_ready()
        logger.info("Mock Discord bot started successfully")
        
    async def close(self):
        """Mock bot shutdown"""
        self.is_closed = True
        self.is_ready = False
        logger.info("Mock Discord bot closed")
        
    async def login(self, token: str):
        """Mock login process"""
        await asyncio.sleep(random.uniform(0.2, 0.8))
        logger.info("Mock Discord bot logged in")
        
    async def logout(self):
        """Mock logout process"""
        await asyncio.sleep(random.uniform(0.1, 0.5))
        logger.info("Mock Discord bot logged out")
        
    def command(self, name: str = None, **kwargs):
        """Mock command decorator"""
        def decorator(func):
            cmd_name = name or func.__name__
            self._commands[cmd_name] = func
            logger.debug(f"Mock command registered: {cmd_name}")
            return func
        return decorator
        
    def slash_command(self, name: str = None, **kwargs):
        """Mock slash command decorator"""
        def decorator(func):
            cmd_name = name or func.__name__
            self._slash_commands[cmd_name] = func
            logger.debug(f"Mock slash command registered: {cmd_name}")
            return func
        return decorator
        
    def event(self, func):
        """Mock event decorator"""
        event_name = func.__name__
        self._event_handlers[event_name] = func
        logger.debug(f"Mock event handler registered: {event_name}")
        return func
        
    async def process_commands(self, message: MockDiscordMessage):
        """Mock command processing"""
        if not message.content.startswith(self.command_prefix):
            return
            
        command_name = message.content[len(self.command_prefix):].split()[0]
        if command_name in self._commands:
            self._command_invocations.append({
                'command': command_name,
                'message': message,
                'timestamp': datetime.now(timezone.utc)
            })
            logger.debug(f"Mock command invoked: {command_name}")
            
    def get_channel(self, channel_id: int):
        """Get channel by ID"""
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None
        
    def get_guild(self, guild_id: int):
        """Get guild by ID"""
        for guild in self.guilds:
            if guild.id == guild_id:
                return guild
        return None
        
    def get_user(self, user_id: int):
        """Get user by ID"""
        for user in self.users:
            if user.id == user_id:
                return user
        return None
        
    async def fetch_channel(self, channel_id: int):
        """Mock channel fetching"""
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return self.get_channel(channel_id)
        
    async def fetch_guild(self, guild_id: int):
        """Mock guild fetching"""
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return self.get_guild(guild_id)
        
    async def fetch_user(self, user_id: int):
        """Mock user fetching"""
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return self.get_user(user_id)
        
    def add_mock_guild(self, guild: MockDiscordGuild = None):
        """Add a mock guild for testing"""
        if guild is None:
            guild = MockDiscordGuild()
        self.guilds.append(guild)
        return guild
        
    def add_mock_channel(self, channel: MockDiscordChannel = None, guild: MockDiscordGuild = None):
        """Add a mock channel for testing"""
        if channel is None:
            channel = MockDiscordChannel(guild=guild)
        if guild:
            guild.channels.append(channel)
        self.channels.append(channel)
        return channel
        
    def add_mock_user(self, user: MockDiscordUser = None):
        """Add a mock user for testing"""
        if user is None:
            user = MockDiscordUser()
        self.users.append(user)
        return user
        
    async def simulate_message(self, content: str, channel: MockDiscordChannel = None, 
                              author: MockDiscordUser = None):
        """Simulate receiving a message"""
        if channel is None:
            channel = self.channels[0] if self.channels else self.add_mock_channel()
        if author is None:
            author = MockDiscordUser()
            
        message = MockDiscordMessage(content=content, author=author, channel=channel)
        
        # Process events
        await self.on_message(message)
        await self.process_commands(message)
        
        self._events_fired.append({
            'event': 'message',
            'message': message,
            'timestamp': datetime.now(timezone.utc)
        })
        
        return message
        
    def get_command_invocations(self) -> List[Dict]:
        """Get list of command invocations for testing"""
        return self._command_invocations.copy()
        
    def get_events_fired(self) -> List[Dict]:
        """Get list of events fired for testing"""
        return self._events_fired.copy()
        
    def reset_mock_state(self):
        """Reset mock state for clean testing"""
        self._command_invocations.clear()
        self._events_fired.clear()
        logger.debug("Mock Discord bot state reset")


class MockDiscordContext:
    """Mock Discord command context"""
    
    def __init__(self, bot: MockDiscordBot, message: MockDiscordMessage):
        self.bot = bot
        self.message = message
        self.channel = message.channel
        self.guild = message.guild
        self.author = message.author
        self.command = None
        self.invoked_with = None
        self.prefix = bot.command_prefix
        self._send_called = False
        
    async def send(self, content: str = None, embed=None, embeds=None, 
                   file=None, files=None, view=None, ephemeral: bool = False):
        """Mock context send"""
        self._send_called = True
        return await self.channel.send(content, embed=embed, embeds=embeds, 
                                     file=file, files=files, view=view, 
                                     ephemeral=ephemeral)


def create_mock_discord_bot(command_prefix: str = "!", intents=None) -> MockDiscordBot:
    """Factory function to create a mock Discord bot"""
    bot = MockDiscordBot(command_prefix=command_prefix, intents=intents)
    
    # Add some default mock data
    guild = bot.add_mock_guild(MockDiscordGuild(name="Test Server"))
    channel = bot.add_mock_channel(MockDiscordChannel(name="general"), guild)
    user = bot.add_mock_user(MockDiscordUser(username="test_user"))
    
    return bot


def create_mock_discord_interaction(command_name: str, options: Dict = None):
    """Create a mock Discord slash command interaction"""
    interaction = Mock()
    interaction.command = Mock()
    interaction.command.name = command_name
    interaction.options = options or {}
    interaction.user = MockDiscordUser()
    interaction.guild = MockDiscordGuild()
    interaction.channel = MockDiscordChannel()
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.respond = AsyncMock()
    interaction.defer = AsyncMock()
    
    return interaction


# Export main classes for easy importing
__all__ = [
    'MockDiscordBot',
    'MockDiscordChannel',
    'MockDiscordUser', 
    'MockDiscordMessage',
    'MockDiscordGuild',
    'MockDiscordContext',
    'MockDiscordChannelType',
    'create_mock_discord_bot',
    'create_mock_discord_interaction'
]