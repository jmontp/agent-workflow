"""
Async Test Fixtures Framework

Enterprise-grade async testing infrastructure providing standardized fixtures,
patterns, and utilities for comprehensive async testing across the system.

Provides:
- Async fixture factory with configurable scopes
- Event loop management and cleanup
- Async context managers for testing
- Performance timing and monitoring
- Error injection and recovery testing
- Resource leak detection

Designed for government audit compliance with 95%+ test coverage requirements.
"""

import asyncio
import functools
import logging
import time
import weakref
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, TypeVar, Union
from unittest.mock import AsyncMock, Mock

import pytest

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncFixtureRegistry:
    """Registry for tracking async fixtures and their lifecycles"""
    
    def __init__(self):
        self._fixtures: Dict[str, Dict] = {}
        self._cleanup_callbacks: List[Callable] = []
        self._resource_tracker: Dict[str, Any] = {}
        
    def register_fixture(self, name: str, fixture_obj: Any, scope: str = "function"):
        """Register an async fixture"""
        self._fixtures[name] = {
            'object': fixture_obj,
            'scope': scope,
            'created_at': datetime.now(timezone.utc),
            'usage_count': 0
        }
        logger.debug(f"Registered async fixture: {name} (scope: {scope})")
        
    def get_fixture(self, name: str) -> Optional[Any]:
        """Get registered fixture"""
        if name in self._fixtures:
            self._fixtures[name]['usage_count'] += 1
            return self._fixtures[name]['object']
        return None
        
    def add_cleanup_callback(self, callback: Callable):
        """Add cleanup callback"""
        self._cleanup_callbacks.append(callback)
        
    async def cleanup_all(self):
        """Clean up all registered resources"""
        logger.debug(f"Cleaning up {len(self._cleanup_callbacks)} async fixtures")
        
        for callback in reversed(self._cleanup_callbacks):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.warning(f"Cleanup callback failed: {e}")
                
        self._fixtures.clear()
        self._cleanup_callbacks.clear()
        self._resource_tracker.clear()
        
    def get_stats(self) -> Dict:
        """Get fixture usage statistics"""
        return {
            'total_fixtures': len(self._fixtures),
            'fixture_details': {
                name: {
                    'scope': info['scope'],
                    'usage_count': info['usage_count'],
                    'created_at': info['created_at'].isoformat()
                }
                for name, info in self._fixtures.items()
            },
            'cleanup_callbacks': len(self._cleanup_callbacks)
        }


# Global fixture registry
_fixture_registry = AsyncFixtureRegistry()


class AsyncPerformanceMonitor:
    """Monitor async operation performance for testing"""
    
    def __init__(self):
        self._timings: Dict[str, List[float]] = {}
        self._start_times: Dict[str, float] = {}
        
    def start_timing(self, operation: str):
        """Start timing an operation"""
        self._start_times[operation] = time.perf_counter()
        
    def end_timing(self, operation: str) -> float:
        """End timing and record duration"""
        if operation not in self._start_times:
            return 0.0
            
        duration = time.perf_counter() - self._start_times[operation]
        
        if operation not in self._timings:
            self._timings[operation] = []
        self._timings[operation].append(duration)
        
        del self._start_times[operation]
        return duration
        
    def get_stats(self, operation: str = None) -> Dict:
        """Get performance statistics"""
        if operation:
            timings = self._timings.get(operation, [])
            if not timings:
                return {'operation': operation, 'count': 0}
                
            return {
                'operation': operation,
                'count': len(timings),
                'total_time': sum(timings),
                'average_time': sum(timings) / len(timings),
                'min_time': min(timings),
                'max_time': max(timings)
            }
        else:
            return {
                op: self.get_stats(op) 
                for op in self._timings.keys()
            }
            
    def reset(self):
        """Reset all timing data"""
        self._timings.clear()
        self._start_times.clear()


# Global performance monitor
_performance_monitor = AsyncPerformanceMonitor()


@asynccontextmanager
async def async_timing_context(operation: str):
    """Async context manager for timing operations"""
    _performance_monitor.start_timing(operation)
    try:
        yield
    finally:
        duration = _performance_monitor.end_timing(operation)
        logger.debug(f"Async operation '{operation}' took {duration:.4f}s")


class AsyncErrorInjector:
    """Inject errors into async operations for robustness testing"""
    
    def __init__(self):
        self._error_patterns: Dict[str, Dict] = {}
        self._injection_count: Dict[str, int] = {}
        
    def register_error_pattern(self, operation: str, error_type: type, 
                             frequency: float = 0.1, max_injections: int = None):
        """Register an error injection pattern"""
        self._error_patterns[operation] = {
            'error_type': error_type,
            'frequency': frequency,
            'max_injections': max_injections,
            'message': f"Injected {error_type.__name__} for testing"
        }
        self._injection_count[operation] = 0
        
    def should_inject_error(self, operation: str) -> bool:
        """Check if error should be injected"""
        if operation not in self._error_patterns:
            return False
            
        pattern = self._error_patterns[operation]
        count = self._injection_count[operation]
        
        # Check max injections limit
        if pattern['max_injections'] and count >= pattern['max_injections']:
            return False
            
        # Check frequency
        import random
        if random.random() < pattern['frequency']:
            self._injection_count[operation] += 1
            return True
            
        return False
        
    def inject_error(self, operation: str):
        """Inject error for operation"""
        if operation not in self._error_patterns:
            return
            
        pattern = self._error_patterns[operation]
        error = pattern['error_type'](pattern['message'])
        logger.debug(f"Injecting error for operation '{operation}': {error}")
        raise error
        
    def reset(self):
        """Reset error injection state"""
        self._error_patterns.clear()
        self._injection_count.clear()


# Global error injector
_error_injector = AsyncErrorInjector()


def async_fixture_factory(scope: str = "function", params: List = None):
    """
    Factory function to create async fixtures with proper lifecycle management.
    
    Args:
        scope: Fixture scope ("function", "class", "module", "session")
        params: List of parameters for parametrized fixtures
        
    Returns:
        Decorator function for creating async fixtures
    """
    
    def decorator(func: Callable) -> Callable:
        fixture_name = func.__name__
        
        @pytest.fixture(scope=scope, params=params)
        async def async_fixture(*args, **kwargs):
            logger.debug(f"Creating async fixture: {fixture_name}")
            
            # Check for existing fixture in registry
            existing = _fixture_registry.get_fixture(fixture_name)
            if existing and scope in ("class", "module", "session"):
                return existing
                
            # Create new fixture
            with async_timing_context(f"fixture_creation_{fixture_name}"):
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
            # Register fixture
            _fixture_registry.register_fixture(fixture_name, result, scope)
            
            # Add cleanup if result has cleanup method
            if hasattr(result, 'cleanup') and callable(result.cleanup):
                _fixture_registry.add_cleanup_callback(result.cleanup)
            elif hasattr(result, 'close') and callable(result.close):
                _fixture_registry.add_cleanup_callback(result.close)
                
            return result
            
        # Preserve original function metadata
        async_fixture.__name__ = func.__name__
        async_fixture.__doc__ = func.__doc__
        async_fixture.__module__ = func.__module__
        
        return async_fixture
        
    return decorator


@async_fixture_factory(scope="session")
async def async_event_loop():
    """Async event loop fixture with proper cleanup"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        yield loop
    finally:
        # Clean up pending tasks
        pending = asyncio.all_tasks(loop)
        if pending:
            logger.debug(f"Cancelling {len(pending)} pending tasks")
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            
        loop.close()
        logger.debug("Async event loop cleaned up")


@async_fixture_factory(scope="function")
async def async_mock_manager():
    """Async mock manager for coordinated mock lifecycle"""
    
    class AsyncMockManager:
        def __init__(self):
            self.mocks: List[AsyncMock] = []
            self.patches: List = []
            
        def create_async_mock(self, spec=None, **kwargs) -> AsyncMock:
            mock = AsyncMock(spec=spec, **kwargs)
            self.mocks.append(mock)
            return mock
            
        def add_patch(self, patch_obj):
            self.patches.append(patch_obj)
            return patch_obj.start()
            
        async def cleanup(self):
            # Stop patches
            for patch_obj in reversed(self.patches):
                try:
                    patch_obj.stop()
                except Exception as e:
                    logger.warning(f"Failed to stop patch: {e}")
                    
            # Reset mocks
            for mock in self.mocks:
                try:
                    mock.reset_mock()
                except Exception as e:
                    logger.warning(f"Failed to reset mock: {e}")
                    
            self.mocks.clear()
            self.patches.clear()
            
    manager = AsyncMockManager()
    yield manager
    await manager.cleanup()


@async_fixture_factory(scope="function")
async def async_resource_tracker():
    """Track async resources for leak detection"""
    
    class AsyncResourceTracker:
        def __init__(self):
            self._resources: Dict[str, weakref.WeakSet] = {}
            self._creation_count: Dict[str, int] = {}
            
        def track_resource(self, resource_type: str, resource: Any):
            if resource_type not in self._resources:
                self._resources[resource_type] = weakref.WeakSet()
                self._creation_count[resource_type] = 0
                
            self._resources[resource_type].add(resource)
            self._creation_count[resource_type] += 1
            
        def get_active_resources(self, resource_type: str = None) -> Dict:
            if resource_type:
                return {
                    'type': resource_type,
                    'active_count': len(self._resources.get(resource_type, [])),
                    'total_created': self._creation_count.get(resource_type, 0)
                }
            else:
                return {
                    res_type: self.get_active_resources(res_type)
                    for res_type in self._resources.keys()
                }
                
        def check_for_leaks(self) -> List[str]:
            leaks = []
            for resource_type, resource_set in self._resources.items():
                if len(resource_set) > 0:
                    leaks.append(f"{resource_type}: {len(resource_set)} active resources")
            return leaks
            
    tracker = AsyncResourceTracker()
    yield tracker
    
    # Check for leaks at end of test
    leaks = tracker.check_for_leaks()
    if leaks:
        logger.warning(f"Resource leaks detected: {leaks}")


@async_fixture_factory(scope="function")
async def async_timeout_manager():
    """Manage timeouts for async operations"""
    
    class AsyncTimeoutManager:
        def __init__(self, default_timeout: float = 10.0):
            self.default_timeout = default_timeout
            self._active_timeouts: List[asyncio.Task] = []
            
        @asynccontextmanager
        async def timeout(self, seconds: float = None):
            timeout_duration = seconds or self.default_timeout
            try:
                async with asyncio.timeout(timeout_duration):
                    yield
            except asyncio.TimeoutError:
                logger.error(f"Async operation timed out after {timeout_duration}s")
                raise
                
        async def wait_for(self, coro, timeout: float = None):
            timeout_duration = timeout or self.default_timeout
            return await asyncio.wait_for(coro, timeout=timeout_duration)
            
        async def cleanup(self):
            # Cancel any active timeout tasks
            for task in self._active_timeouts:
                if not task.done():
                    task.cancel()
            self._active_timeouts.clear()
            
    manager = AsyncTimeoutManager()
    yield manager
    await manager.cleanup()


@pytest.fixture(scope="session", autouse=True)
async def async_test_session_cleanup():
    """Auto-cleanup fixture for test session"""
    yield
    
    # Global cleanup
    await _fixture_registry.cleanup_all()
    _performance_monitor.reset()
    _error_injector.reset()
    
    logger.info("Async test session cleanup completed")


def async_test_wrapper(func: Callable) -> Callable:
    """Wrapper for async test functions with enhanced error handling"""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        test_name = func.__name__
        
        with async_timing_context(f"test_{test_name}"):
            try:
                # Check for error injection
                if _error_injector.should_inject_error(test_name):
                    _error_injector.inject_error(test_name)
                    
                # Run test
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                logger.error(f"Async test '{test_name}' failed: {e}")
                raise
                
    return wrapper


def pytest_configure(config):
    """Configure pytest for async testing"""
    # Register custom markers
    config.addinivalue_line(
        "markers", "async_test: mark test as async test with enhanced monitoring"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for async tests"""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.async_test)


# Utility functions for test authors
async def wait_for_condition(condition: Callable, timeout: float = 5.0, 
                           interval: float = 0.1) -> bool:
    """Wait for a condition to become true"""
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            if await condition() if asyncio.iscoroutinefunction(condition) else condition():
                return True
        except Exception:
            pass
        await asyncio.sleep(interval)
        
    return False


async def simulate_async_delay(min_delay: float = 0.01, max_delay: float = 0.1):
    """Simulate realistic async delay"""
    import random
    delay = random.uniform(min_delay, max_delay)
    await asyncio.sleep(delay)


def get_async_test_stats() -> Dict:
    """Get comprehensive async testing statistics"""
    return {
        'fixtures': _fixture_registry.get_stats(),
        'performance': _performance_monitor.get_stats(),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


# Export main components
__all__ = [
    'async_fixture_factory',
    'async_event_loop',
    'async_mock_manager', 
    'async_resource_tracker',
    'async_timeout_manager',
    'async_test_wrapper',
    'async_timing_context',
    'AsyncPerformanceMonitor',
    'AsyncErrorInjector',
    'wait_for_condition',
    'simulate_async_delay',
    'get_async_test_stats'
]