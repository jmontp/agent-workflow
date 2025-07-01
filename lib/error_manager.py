#!/usr/bin/env python3
"""
Centralized Error Management System for Library Components

This module provides error handling capabilities for the main lib/ directory.
It works in conjunction with the visualizer error manager to provide
comprehensive error handling across the entire system.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime
import json
from pathlib import Path

# Import the comprehensive error manager from visualizer
try:
    from ..tools.visualizer.lib.error_manager import (
        ErrorManager, ErrorCode, SeverityLevel, RecoveryStrategy,
        ErrorContext, ErrorRecord, get_error_manager, handle_errors
    )
    _HAS_VISUALIZER_ERROR_MANAGER = True
except ImportError:
    _HAS_VISUALIZER_ERROR_MANAGER = False

logger = logging.getLogger(__name__)


class LibraryErrorManager:
    """
    Simplified error manager for library components.
    
    This provides a unified interface for error handling in the main lib/
    directory, with fallback behavior when the visualizer error manager
    is not available.
    """
    
    def __init__(self, component_name: str = 'lib'):
        self.component_name = component_name
        
        if _HAS_VISUALIZER_ERROR_MANAGER:
            self.error_manager = get_error_manager(component_name)
        else:
            self.error_manager = None
            
        self.error_history = []
        self.max_history_size = 100
    
    def handle_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle an error with unified error management.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            user_message: Custom user-friendly message
            
        Returns:
            Dict containing error information and recovery details
        """
        if self.error_manager and _HAS_VISUALIZER_ERROR_MANAGER:
            # Use comprehensive error manager
            error_context = ErrorContext(
                component=self.component_name,
                operation=context.get('operation', 'unknown') if context else 'unknown',
                additional_data=context or {}
            )
            
            error_record = self.error_manager.handle_error(
                error, error_context, user_message
            )
            
            return {
                'error_id': error_record.id,
                'error_code': error_record.error_code.value,
                'severity': error_record.severity.value,
                'user_message': error_record.user_message,
                'recovery_attempted': error_record.recovery_result.attempted if error_record.recovery_result else False,
                'recovery_successful': error_record.recovery_result.successful if error_record.recovery_result else False
            }
        else:
            # Fallback error handling
            error_info = {
                'error_id': f"lib_{int(datetime.now().timestamp())}",
                'error_type': type(error).__name__,
                'error_message': str(error),
                'component': self.component_name,
                'context': context or {},
                'timestamp': datetime.now().isoformat(),
                'stack_trace': traceback.format_exc()
            }
            
            self.error_history.append(error_info)
            self._trim_error_history()
            
            # Log the error
            logger.error(f"Error in {self.component_name}: {error}")
            if context:
                logger.error(f"Context: {context}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            return {
                'error_id': error_info['error_id'],
                'error_code': 'UNKNOWN_ERROR',
                'severity': 'error',
                'user_message': user_message or 'An error occurred',
                'recovery_attempted': False,
                'recovery_successful': False
            }
    
    def _trim_error_history(self):
        """Trim error history to prevent memory bloat"""
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        if self.error_manager and _HAS_VISUALIZER_ERROR_MANAGER:
            return self.error_manager.get_error_stats()
        else:
            return {
                'total_errors': len(self.error_history),
                'component': self.component_name,
                'recent_errors': self.error_history[-5:] if self.error_history else []
            }


# Global error manager instances
_error_managers: Dict[str, LibraryErrorManager] = {}


def get_lib_error_manager(component_name: str = 'lib') -> LibraryErrorManager:
    """Get or create error manager for library component"""
    if component_name not in _error_managers:
        _error_managers[component_name] = LibraryErrorManager(component_name)
    return _error_managers[component_name]


def handle_lib_error(
    error: Exception,
    component_name: str = 'lib',
    operation: str = 'unknown',
    user_message: Optional[str] = None,
    **context_data
) -> Dict[str, Any]:
    """
    Convenience function for handling library errors.
    
    Args:
        error: The exception that occurred
        component_name: Name of the component where error occurred
        operation: Operation being performed when error occurred
        user_message: Custom user-friendly message
        **context_data: Additional context data
        
    Returns:
        Dict containing error information and recovery details
    """
    error_manager = get_lib_error_manager(component_name)
    context = {'operation': operation, **context_data}
    return error_manager.handle_error(error, context, user_message)


# Decorator for automatic error handling in library functions
def handle_lib_errors(
    component_name: str = 'lib',
    operation: Optional[str] = None,
    user_message: Optional[str] = None,
    suppress_errors: bool = False
):
    """
    Decorator for automatic error handling in library functions.
    
    Args:
        component_name: Name of the component
        operation: Operation being performed (defaults to function name)
        user_message: Custom user-friendly message
        suppress_errors: Whether to suppress errors (return None on error)
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                op_name = operation or func.__name__
                error_info = handle_lib_error(
                    error, component_name, op_name, user_message
                )
                
                if not suppress_errors:
                    raise  # Re-raise the original exception
                
                logger.warning(f"Suppressed error in {func.__name__}: {error}")
                return None
        return wrapper
    return decorator


# Context manager for error handling
class LibraryErrorContext:
    """Context manager for standardized error handling in library operations"""
    
    def __init__(
        self,
        component_name: str,
        operation: str,
        user_message: Optional[str] = None,
        suppress_errors: bool = False,
        **context_data
    ):
        self.component_name = component_name
        self.operation = operation
        self.user_message = user_message
        self.suppress_errors = suppress_errors
        self.context_data = context_data
        self.error_info = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.error_info = handle_lib_error(
                exc_val,
                self.component_name,
                self.operation,
                self.user_message,
                **self.context_data
            )
            
            if self.suppress_errors:
                return True  # Suppress the exception
        
        return False  # Don't suppress exceptions by default
    
    def get_error_info(self) -> Optional[Dict[str, Any]]:
        """Get error information if an error occurred"""
        return self.error_info


__all__ = [
    'LibraryErrorManager',
    'get_lib_error_manager',
    'handle_lib_error',
    'handle_lib_errors',
    'LibraryErrorContext'
]