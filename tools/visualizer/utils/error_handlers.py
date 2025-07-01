"""
Error handling utilities for the visualizer package.

Provides shared error handling decorators and utilities to reduce code duplication.
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple
from flask import jsonify, request

logger = logging.getLogger(__name__)


def handle_api_error(
    default_message: str = "An error occurred",
    status_code: int = 500,
    log_errors: bool = True,
    return_traceback: bool = False
):
    """
    Decorator to handle API endpoint errors consistently.
    
    This replaces the many duplicate try/catch blocks throughout the codebase
    with a standardized error handling approach.
    
    Args:
        default_message: Default error message if none provided
        status_code: HTTP status code to return on error
        log_errors: Whether to log the error
        return_traceback: Whether to include traceback in response (dev mode)
        
    Returns:
        Decorated function with consistent error handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e) if str(e) else default_message
                
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {error_msg}")
                    logger.error(f"Request path: {getattr(request, 'path', 'unknown')}")
                    logger.error(f"Request method: {getattr(request, 'method', 'unknown')}")
                
                response_data = {
                    "success": False,
                    "error": error_msg,
                    "endpoint": func.__name__
                }
                
                if return_traceback:
                    import traceback
                    response_data["traceback"] = traceback.format_exc()
                
                return jsonify(response_data), status_code
        return wrapper
    return decorator


def handle_websocket_error(
    default_message: str = "WebSocket error occurred",
    emit_error: bool = True,
    log_errors: bool = True
):
    """
    Decorator to handle WebSocket event errors consistently.
    
    Args:
        default_message: Default error message
        emit_error: Whether to emit error event to client
        log_errors: Whether to log the error
        
    Returns:
        Decorated function with WebSocket error handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e) if str(e) else default_message
                
                if log_errors:
                    logger.error(f"WebSocket error in {func.__name__}: {error_msg}")
                
                if emit_error:
                    # Import here to avoid circular imports
                    from flask_socketio import emit
                    emit('error', {
                        'message': error_msg,
                        'event': func.__name__,
                        'timestamp': __import__('time').time()
                    })
                
                return None
        return wrapper
    return decorator


def log_and_return_error(
    error: Exception,
    context: str = "",
    default_message: str = "An error occurred",
    status_code: int = 500
) -> Tuple[Dict[str, Any], int]:
    """
    Log an error and return a standardized JSON response.
    
    Args:
        error: The exception that occurred
        context: Additional context information
        default_message: Default message if error string is empty
        status_code: HTTP status code to return
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    error_msg = str(error) if str(error) else default_message
    
    if context:
        logger.error(f"Error in {context}: {error_msg}")
    else:
        logger.error(f"Error: {error_msg}")
    
    return {
        "success": False,
        "error": error_msg,
        "context": context
    }, status_code


def safe_json_response(
    data: Any,
    success: bool = True,
    message: str = None,
    status_code: int = 200
) -> Tuple[Dict[str, Any], int]:
    """
    Create a safe JSON response with consistent structure.
    
    Args:
        data: Data to include in response
        success: Whether the operation was successful
        message: Optional message
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "success": success,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return response, status_code


class ErrorContext:
    """
    Context manager for consistent error handling and logging.
    """
    
    def __init__(
        self,
        operation: str,
        log_entry: bool = True,
        log_exit: bool = True,
        suppress_errors: bool = False
    ):
        self.operation = operation
        self.log_entry = log_entry
        self.log_exit = log_exit
        self.suppress_errors = suppress_errors
        self.error = None
    
    def __enter__(self):
        if self.log_entry:
            logger.info(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            logger.error(f"Error in operation '{self.operation}': {exc_val}")
            
            if self.suppress_errors:
                return True  # Suppress the exception
        else:
            if self.log_exit:
                logger.info(f"Completed operation: {self.operation}")
        
        return False


__all__ = [
    'handle_api_error',
    'handle_websocket_error', 
    'log_and_return_error',
    'safe_json_response',
    'ErrorContext'
]