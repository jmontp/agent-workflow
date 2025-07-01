"""
Async utility functions for the visualizer package.

Provides shared async operations to reduce code duplication.
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional, Dict
from functools import wraps

logger = logging.getLogger(__name__)


def run_async_operation(coro: Coroutine, timeout: Optional[float] = None) -> Any:
    """
    Run an async operation in a synchronous context.
    
    Handles event loop creation and cleanup automatically.
    Used to eliminate the duplicate async pattern found throughout the codebase.
    
    Args:
        coro: The coroutine to execute
        timeout: Optional timeout in seconds
        
    Returns:
        The result of the coroutine execution
        
    Raises:
        asyncio.TimeoutError: If timeout is exceeded
        Exception: Any exception raised by the coroutine
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to use run_coroutine_threadsafe
            # This is a common pattern in web applications
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=timeout)
        else:
            # Loop exists but not running - safe to use run_until_complete
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists - create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def async_timeout(seconds: float):
    """
    Decorator to add timeout to async functions.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function with timeout
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper
    return decorator


def handle_async_errors(default_return: Any = None, log_errors: bool = True):
    """
    Decorator to handle async function errors gracefully.
    
    Args:
        default_return: Value to return on error
        log_errors: Whether to log errors
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator


class AsyncContextManager:
    """
    Context manager for async operations in sync context.
    
    Automatically handles event loop lifecycle.
    """
    
    def __init__(self):
        self.loop = None
        self.loop_created = False
    
    def __enter__(self):
        try:
            self.loop = asyncio.get_event_loop()
            if self.loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError:
            # Create new event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop_created = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.loop_created and self.loop and not self.loop.is_closed():
            self.loop.close()
    
    def run(self, coro: Coroutine, timeout: Optional[float] = None) -> Any:
        """Run a coroutine in this context."""
        if timeout:
            return self.loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
        return self.loop.run_until_complete(coro)


__all__ = [
    'run_async_operation',
    'async_timeout', 
    'handle_async_errors',
    'AsyncContextManager'
]