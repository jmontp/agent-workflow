"""
Common type definitions for the visualizer package.

Centralizes all typing imports to reduce redundancy across modules.
"""

from typing import (
    Dict, List, Any, Optional, Union, Tuple, Callable, 
    Set, Awaitable, AsyncGenerator, TypeVar, Generic
)

# Common type aliases used throughout the visualizer
ConfigDict = Dict[str, Any]
StateDict = Dict[str, Any] 
ResponseDict = Dict[str, Any]
ProjectDict = Dict[str, Any]
ChatDict = Dict[str, Any]

# Generic types for flexibility
T = TypeVar('T')
K = TypeVar('K')  
V = TypeVar('V')

__all__ = [
    # Standard typing imports
    'Dict', 'List', 'Any', 'Optional', 'Union', 'Tuple', 'Callable',
    'Set', 'Awaitable', 'AsyncGenerator', 'TypeVar', 'Generic',
    
    # Custom type aliases
    'ConfigDict', 'StateDict', 'ResponseDict', 'ProjectDict', 'ChatDict',
    
    # Generic types
    'T', 'K', 'V'
]