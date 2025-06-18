"""
Context Management System for AI Agent TDD-Scrum Workflow

This module provides intelligent context management for agent communication,
token budget optimization, and context filtering to maximize agent effectiveness
while respecting Claude Code's token limitations.
"""

from .models import (
    ContextRequest,
    AgentContext, 
    TokenBudget,
    TokenUsage,
    AgentMemory,
    Decision,
    PhaseHandoff,
    ContextSnapshot,
    Pattern,
    RelevanceScore
)

# Only import available components for Phase 1
from .interfaces import *

# Phase 2 components to be implemented later:
# from .manager import ContextManager
# from .filter import ContextFilter
# from .token_calculator import TokenCalculator
# from .agent_memory import AgentMemoryManager
# from .compressor import ContextCompressor
# from .index import ContextIndex
from .exceptions import (
    ContextError,
    TokenBudgetExceededError,
    ContextNotFoundError,
    ContextCompressionError,
    AgentMemoryError
)

__all__ = [
    # Data Models
    'ContextRequest',
    'AgentContext',
    'TokenBudget',
    'TokenUsage',
    'AgentMemory',
    'Decision',
    'PhaseHandoff',
    'ContextSnapshot',
    'Pattern',
    'RelevanceScore',
    
    # Interfaces
    'IContextFilter',
    'ITokenCalculator',
    'IAgentMemory',
    'IContextCompressor',
    'IContextIndex',
    'IContextStorage',
    
    # Exceptions
    'ContextError',
    'TokenBudgetExceededError',
    'ContextNotFoundError',
    'ContextCompressionError',
    'AgentMemoryError'
]

__version__ = "1.0.0"