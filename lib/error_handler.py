"""
Standardized Error Handling Utilities

Provides consistent error handling patterns, logging, and recovery mechanisms
across the agent-workflow system.
"""

import logging
import traceback
import functools
from typing import Any, Dict, Optional, Callable, Type, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .context.exceptions import (
    ContextError, AgentPoolError, StateMachineError, 
    OrchestrationError, RecoveryError
)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Error recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    FAIL_FAST = "fail_fast"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class ErrorContext:
    """Standardized error context for debugging"""
    operation: str
    component: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "operation": self.operation,
            "component": self.component,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "recovery_strategy": self.recovery_strategy.value,
            "metadata": self.metadata
        }


class StandardizedErrorHandler:
    """Centralized error handling with consistent patterns"""
    
    def __init__(self, component_name: str, logger: Optional[logging.Logger] = None):
        self.component_name = component_name
        self.logger = logger or logging.getLogger(component_name)
        self.error_history: list = []
        self.recovery_attempts: Dict[str, int] = {}
    
    def handle_error(
        self,
        error: Exception,
        operation: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        **metadata
    ) -> ErrorContext:
        """
        Handle an error with standardized logging and context creation.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            severity: Error severity level
            recovery_strategy: Suggested recovery strategy
            **metadata: Additional context metadata
            
        Returns:
            ErrorContext with standardized error information
        """
        context = ErrorContext(
            operation=operation,
            component=self.component_name,
            severity=severity,
            recovery_strategy=recovery_strategy,
            metadata={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                **metadata
            }
        )
        
        # Log with appropriate level based on severity
        log_message = f"{operation} failed: {str(error)}"
        log_data = context.to_dict()
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=log_data)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=log_data)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=log_data)
        else:
            self.logger.info(log_message, extra=log_data)
        
        # Store in error history for analysis
        self.error_history.append(context)
        if len(self.error_history) > 1000:  # Limit history size
            self.error_history = self.error_history[-500:]
        
        return context
    
    def with_error_handling(
        self,
        operation: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        reraise: bool = True,
        **metadata
    ):
        """
        Decorator for automatic error handling.
        
        Args:
            operation: Description of the operation
            severity: Error severity level
            recovery_strategy: Recovery strategy to suggest
            reraise: Whether to reraise the exception after handling
            **metadata: Additional context metadata
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    context = self.handle_error(
                        e, operation, severity, recovery_strategy, **metadata
                    )
                    if reraise:
                        raise
                    return None
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    context = self.handle_error(
                        e, operation, severity, recovery_strategy, **metadata
                    )
                    if reraise:
                        raise
                    return None
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def attempt_recovery(
        self,
        operation_id: str,
        recovery_func: Callable,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0
    ) -> bool:
        """
        Attempt recovery with exponential backoff.
        
        Args:
            operation_id: Unique identifier for the operation
            recovery_func: Function to call for recovery
            max_attempts: Maximum recovery attempts
            backoff_seconds: Base backoff time in seconds
            
        Returns:
            True if recovery successful, False otherwise
        """
        import time
        
        attempt_count = self.recovery_attempts.get(operation_id, 0)
        
        if attempt_count >= max_attempts:
            self.logger.error(
                f"Recovery abandoned for {operation_id} after {attempt_count} attempts"
            )
            return False
        
        self.recovery_attempts[operation_id] = attempt_count + 1
        
        try:
            # Exponential backoff
            if attempt_count > 0:
                delay = backoff_seconds * (2 ** (attempt_count - 1))
                time.sleep(delay)
            
            recovery_func()
            
            # Reset counter on success
            self.recovery_attempts[operation_id] = 0
            self.logger.info(f"Recovery successful for {operation_id}")
            return True
            
        except Exception as e:
            self.handle_error(
                e,
                f"Recovery attempt {attempt_count + 1} for {operation_id}",
                ErrorSeverity.HIGH,
                RecoveryStrategy.RETRY,
                operation_id=operation_id,
                attempt_count=attempt_count + 1
            )
            return False
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors for monitoring"""
        if not self.error_history:
            return {"total_errors": 0, "recent_errors": []}
        
        recent_errors = self.error_history[-10:]  # Last 10 errors
        error_types = {}
        
        for error_ctx in self.error_history:
            error_type = error_ctx.metadata.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": [ctx.to_dict() for ctx in recent_errors],
            "error_types": error_types,
            "recovery_attempts": dict(self.recovery_attempts)
        }


def create_domain_error(
    base_exception: Type[ContextError],
    message: str,
    operation: str,
    component: str,
    **kwargs
) -> ContextError:
    """
    Create a domain-specific error with standardized context.
    
    Args:
        base_exception: Base exception class to use
        message: Error message
        operation: Operation that failed
        component: Component where error occurred
        **kwargs: Additional context for the specific exception type
        
    Returns:
        Configured domain-specific exception
    """
    details = {
        "operation": operation,
        "component": component,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    return base_exception(message, details=details, **kwargs)


# Convenience functions for common error patterns

def create_agent_pool_error(message: str, agent_id: str = None, **kwargs) -> AgentPoolError:
    """Create standardized agent pool error"""
    return create_domain_error(AgentPoolError, message, "agent_pool_operation", "AgentPool", agent_id=agent_id, **kwargs)


def create_state_machine_error(message: str, current_state: str = None, transition: str = None, **kwargs) -> StateMachineError:
    """Create standardized state machine error"""
    return create_domain_error(StateMachineError, message, "state_transition", "StateMachine", current_state=current_state, transition=transition, **kwargs)


def create_orchestration_error(message: str, project_id: str = None, phase: str = None, **kwargs) -> OrchestrationError:
    """Create standardized orchestration error"""
    return create_domain_error(OrchestrationError, message, "orchestration", "Orchestrator", project_id=project_id, orchestration_phase=phase, **kwargs)


def create_recovery_error(message: str, recovery_type: str = None, attempt_count: int = 0, **kwargs) -> RecoveryError:
    """Create standardized recovery error"""
    return create_domain_error(RecoveryError, message, "error_recovery", "RecoverySystem", recovery_type=recovery_type, attempt_count=attempt_count, **kwargs)