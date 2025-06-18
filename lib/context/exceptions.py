"""
Context Management System Exceptions

Custom exception classes for context management operations.
"""

from typing import Optional, Dict, Any


class ContextError(Exception):
    """Base exception for context management errors"""
    
    def __init__(self, message: str, context_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context_id = context_id
        self.details = details or {}


class TokenBudgetExceededError(ContextError):
    """Raised when token budget is exceeded during context preparation"""
    
    def __init__(self, message: str, requested_tokens: int, available_tokens: int, **kwargs):
        super().__init__(message, **kwargs)
        self.requested_tokens = requested_tokens
        self.available_tokens = available_tokens


class ContextNotFoundError(ContextError):
    """Raised when requested context cannot be found or prepared"""
    pass


class ContextCompressionError(ContextError):
    """Raised when context compression fails"""
    
    def __init__(self, message: str, original_size: int, target_size: int, **kwargs):
        super().__init__(message, **kwargs)
        self.original_size = original_size
        self.target_size = target_size


class AgentMemoryError(ContextError):
    """Raised when agent memory operations fail"""
    
    def __init__(self, message: str, agent_type: str, story_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.agent_type = agent_type
        self.story_id = story_id


class ContextFilterError(ContextError):
    """Raised when context filtering operations fail"""
    pass


class ContextIndexError(ContextError):
    """Raised when context indexing operations fail"""
    
    def __init__(self, message: str, index_path: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.index_path = index_path


class ContextStorageError(ContextError):
    """Raised when context storage operations fail"""
    
    def __init__(self, message: str, storage_path: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.storage_path = storage_path


class ContextValidationError(ContextError):
    """Raised when context validation fails"""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []


class ContextTimeoutError(ContextError):
    """Raised when context operations timeout"""
    
    def __init__(self, message: str, operation: str, timeout_seconds: float, **kwargs):
        super().__init__(message, **kwargs)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class ContextCacheError(ContextError):
    """Raised when context cache operations fail"""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.cache_key = cache_key


class ContextMonitoringError(ContextError):
    """Raised when context monitoring operations fail"""
    
    def __init__(self, message: str, metric_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.metric_type = metric_type


class ContextBackgroundError(ContextError):
    """Raised when background context processing operations fail"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.task_id = task_id


class ContextLearningError(ContextError):
    """Raised when context learning operations fail"""
    
    def __init__(self, message: str, learning_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.learning_type = learning_type