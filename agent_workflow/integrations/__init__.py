"""
Integration modules for external services.

This module provides integrations with:
- Discord bot for Human-in-the-Loop commands
- AI providers (Claude, OpenAI, etc.)
- GitHub for version control
- Other external APIs and services
"""

try:
    from .discord.client import DiscordClient
    from .claude.client import ClaudeClient, create_agent_client
    
    __all__ = [
        "DiscordClient",
        "ClaudeClient", 
        "create_agent_client",
    ]
except ImportError:
    __all__ = []