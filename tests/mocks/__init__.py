"""
Mock Framework Infrastructure

Enterprise-grade mocking infrastructure for external dependencies used in 
government audit compliance testing. Provides realistic mock implementations
for Discord API, WebSocket communications, GitHub API, and file system operations.

Key Components:
- discord_mocks: Comprehensive Discord API (discord.py) mocking
- websocket_mocks: WebSocket server and client mocking  
- github_mocks: GitHub API (PyGithub) mocking
- filesystem_mocks: File system operation mocking
- async_fixtures: Async test fixtures and patterns

Features:
- Realistic behavior simulation
- Configurable failure rates
- Performance metric tracking
- Cross-module compatibility
- Enterprise security compliance
"""

from .discord_mocks import MockDiscordBot, MockDiscordChannel, MockDiscordUser, MockDiscordMessage
from .websocket_mocks import MockWebSocketServer, MockWebSocketClient
from .github_mocks import MockGitHubRepo, MockGitHubAPI
from .filesystem_mocks import MockFileSystem
from .async_fixtures import async_fixture_factory

__all__ = [
    'MockDiscordBot',
    'MockDiscordChannel', 
    'MockDiscordUser',
    'MockDiscordMessage',
    'MockWebSocketServer',
    'MockWebSocketClient',
    'MockGitHubRepo',
    'MockGitHubAPI',
    'MockFileSystem',
    'async_fixture_factory'
]

__version__ = '1.0.0'