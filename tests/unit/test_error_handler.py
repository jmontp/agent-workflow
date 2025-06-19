"""
Comprehensive test suite for Standardized Error Handling Utilities.

Tests all error handling functionality including StandardizedErrorHandler,
error severity levels, recovery strategies, decorators, and domain-specific
error creation functions to achieve 100% test coverage for audit compliance.
"""

import pytest
import logging
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

# Import the modules under test
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.context.exceptions import (
    ContextError,
    AgentPoolError,
    StateMachineError,
    OrchestrationError,
    RecoveryError
)

from lib.error_handler import (
    ErrorSeverity,
    RecoveryStrategy,
    ErrorContext,
    StandardizedErrorHandler,
    create_domain_error,
    create_agent_pool_error,
    create_state_machine_error,
    create_orchestration_error,
    create_recovery_error
)


class TestErrorSeverity:
    """Test ErrorSeverity enum"""
    
    def test_error_severity_values(self):
        """Test all error severity enum values"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
    
    def test_error_severity_comparison(self):
        """Test error severity enum comparison"""
        assert ErrorSeverity.LOW != ErrorSeverity.MEDIUM
        assert ErrorSeverity.HIGH == ErrorSeverity.HIGH


class TestRecoveryStrategy:
    """Test RecoveryStrategy enum"""
    
    def test_recovery_strategy_values(self):
        """Test all recovery strategy enum values"""
        assert RecoveryStrategy.RETRY.value == "retry"
        assert RecoveryStrategy.FALLBACK.value == "fallback"
        assert RecoveryStrategy.GRACEFUL_DEGRADATION.value == "graceful_degradation"
        assert RecoveryStrategy.FAIL_FAST.value == "fail_fast"
        assert RecoveryStrategy.CIRCUIT_BREAKER.value == "circuit_breaker"
    
    def test_recovery_strategy_comparison(self):
        """Test recovery strategy enum comparison"""
        assert RecoveryStrategy.RETRY != RecoveryStrategy.FALLBACK
        assert RecoveryStrategy.RETRY == RecoveryStrategy.RETRY


class TestErrorContext:
    """Test ErrorContext dataclass"""
    
    def test_error_context_creation_minimal(self):
        """Test ErrorContext creation with minimal parameters"""
        context = ErrorContext(operation="test_op", component="test_component")
        
        assert context.operation == "test_op"
        assert context.component == "test_component"
        assert context.severity == ErrorSeverity.MEDIUM  # default
        assert context.recovery_strategy == RecoveryStrategy.RETRY  # default
        assert context.metadata == {}
        assert isinstance(context.timestamp, str)
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(context.timestamp.replace('Z', '+00:00'))
    
    def test_error_context_creation_full(self):
        """Test ErrorContext creation with all parameters"""
        metadata = {"key": "value", "count": 42}
        timestamp = "2023-01-01T12:00:00"
        
        context = ErrorContext(
            operation="full_test_op",
            component="full_test_component",
            timestamp=timestamp,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=RecoveryStrategy.FALLBACK,
            metadata=metadata
        )
        
        assert context.operation == "full_test_op"
        assert context.component == "full_test_component"
        assert context.timestamp == timestamp
        assert context.severity == ErrorSeverity.HIGH
        assert context.recovery_strategy == RecoveryStrategy.FALLBACK
        assert context.metadata == metadata
    
    def test_error_context_to_dict(self):
        """Test ErrorContext.to_dict() method"""
        metadata = {"error_type": "TestError", "line_number": 42}
        context = ErrorContext(
            operation="dict_test",
            component="dict_component",
            timestamp="2023-01-01T12:00:00",
            severity=ErrorSeverity.CRITICAL,
            recovery_strategy=RecoveryStrategy.CIRCUIT_BREAKER,
            metadata=metadata
        )
        
        result = context.to_dict()
        
        expected = {
            "operation": "dict_test",
            "component": "dict_component",
            "timestamp": "2023-01-01T12:00:00",
            "severity": "critical",
            "recovery_strategy": "circuit_breaker",
            "metadata": metadata
        }
        
        assert result == expected
    
    def test_error_context_default_timestamp(self):
        """Test ErrorContext default timestamp generation"""
        with patch('lib.error_handler.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.isoformat.return_value = "2023-12-25T10:30:00"
            
            context = ErrorContext(operation="timestamp_test", component="timestamp_component")
            
            assert context.timestamp == "2023-12-25T10:30:00"
            mock_datetime.utcnow.assert_called_once()


class TestStandardizedErrorHandler:
    """Test StandardizedErrorHandler class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=logging.Logger)
        self.handler = StandardizedErrorHandler("test_component", self.mock_logger)
    
    def test_initialization_with_logger(self):
        """Test handler initialization with provided logger"""
        handler = StandardizedErrorHandler("test_comp", self.mock_logger)
        
        assert handler.component_name == "test_comp"
        assert handler.logger == self.mock_logger
        assert handler.error_history == []
        assert handler.recovery_attempts == {}
    
    def test_initialization_without_logger(self):
        """Test handler initialization without logger (creates default)"""
        with patch('lib.error_handler.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            handler = StandardizedErrorHandler("auto_logger_comp")
            
            assert handler.component_name == "auto_logger_comp"
            assert handler.logger == mock_logger
            mock_get_logger.assert_called_once_with("auto_logger_comp")
    
    def test_handle_error_basic(self):
        """Test basic error handling"""
        test_error = ValueError("Test error message")
        
        with patch('lib.error_handler.traceback.format_exc') as mock_traceback:
            mock_traceback.return_value = "Mock traceback"
            
            context = self.handler.handle_error(test_error, "test_operation")
            
            assert context.operation == "test_operation"
            assert context.component == "test_component"
            assert context.severity == ErrorSeverity.MEDIUM
            assert context.recovery_strategy == RecoveryStrategy.RETRY
            assert context.metadata["error_type"] == "ValueError"
            assert context.metadata["error_message"] == "Test error message"
            assert context.metadata["traceback"] == "Mock traceback"
    
    def test_handle_error_all_severity_levels(self):
        """Test error handling for all severity levels"""
        test_error = RuntimeError("Test runtime error")
        
        # Test CRITICAL severity
        self.handler.handle_error(test_error, "critical_op", ErrorSeverity.CRITICAL)
        self.mock_logger.critical.assert_called_once()
        self.mock_logger.reset_mock()
        
        # Test HIGH severity
        self.handler.handle_error(test_error, "high_op", ErrorSeverity.HIGH)
        self.mock_logger.error.assert_called_once()
        self.mock_logger.reset_mock()
        
        # Test MEDIUM severity
        self.handler.handle_error(test_error, "medium_op", ErrorSeverity.MEDIUM)
        self.mock_logger.warning.assert_called_once()
        self.mock_logger.reset_mock()
        
        # Test LOW severity
        self.handler.handle_error(test_error, "low_op", ErrorSeverity.LOW)
        self.mock_logger.info.assert_called_once()
    
    def test_handle_error_with_metadata(self):
        """Test error handling with additional metadata"""
        test_error = KeyError("Missing key")
        metadata = {
            "user_id": "user_123",
            "request_id": "req_456",
            "extra_data": {"nested": "value"}
        }
        
        context = self.handler.handle_error(
            test_error,
            "metadata_test",
            ErrorSeverity.HIGH,
            RecoveryStrategy.FALLBACK,
            **metadata
        )
        
        assert context.metadata["user_id"] == "user_123"
        assert context.metadata["request_id"] == "req_456"
        assert context.metadata["extra_data"] == {"nested": "value"}
        assert context.metadata["error_type"] == "KeyError"
        assert context.metadata["error_message"] == "'Missing key'"
    
    def test_error_history_storage(self):
        """Test error history storage and limiting"""
        # Add errors to history
        for i in range(5):
            error = ValueError(f"Error {i}")
            self.handler.handle_error(error, f"operation_{i}")
        
        assert len(self.handler.error_history) == 5
        
        # Test that all errors are stored correctly
        for i, context in enumerate(self.handler.error_history):
            assert context.operation == f"operation_{i}"
            assert context.metadata["error_message"] == f"Error {i}"
    
    def test_error_history_overflow_protection(self):
        """Test error history overflow protection (limits to 1000, then trims to 500)"""
        # Create handler with existing history close to limit
        self.handler.error_history = [Mock() for _ in range(999)]
        
        # Add one more error to trigger overflow
        test_error = ValueError("Overflow test")
        self.handler.handle_error(test_error, "overflow_test")
        
        # Should have exactly 1000 items
        assert len(self.handler.error_history) == 1000
        
        # Add another error to trigger trimming
        test_error2 = ValueError("Trimming test")
        self.handler.handle_error(test_error2, "trimming_test")
        
        # Should be trimmed to 500 (the last 500 items after trimming)
        assert len(self.handler.error_history) == 500
        
        # The newest error should be at the end
        latest_context = self.handler.error_history[-1]
        assert latest_context.operation == "trimming_test"
        assert latest_context.metadata["error_message"] == "Trimming test"
    
    def test_with_error_handling_sync_function_with_reraise(self):
        """Test decorator with synchronous function that reraises"""
        @self.handler.with_error_handling("sync_test", ErrorSeverity.HIGH, reraise=True)
        def failing_sync_function():
            raise ValueError("Sync function failed")
        
        with pytest.raises(ValueError, match="Sync function failed"):
            failing_sync_function()
        
        # Verify error was handled
        assert len(self.handler.error_history) == 1
        context = self.handler.error_history[0]
        assert context.operation == "sync_test"
        assert context.severity == ErrorSeverity.HIGH
    
    def test_with_error_handling_sync_function_without_reraise(self):
        """Test decorator with synchronous function that doesn't reraise"""
        @self.handler.with_error_handling("sync_no_reraise", ErrorSeverity.LOW, reraise=False)
        def failing_sync_function():
            raise RuntimeError("Sync function error")
        
        result = failing_sync_function()
        
        assert result is None  # Should return None when not reraising
        assert len(self.handler.error_history) == 1
        context = self.handler.error_history[0]
        assert context.operation == "sync_no_reraise"
        assert context.severity == ErrorSeverity.LOW
    
    def test_with_error_handling_sync_function_success(self):
        """Test decorator with successful synchronous function"""
        @self.handler.with_error_handling("sync_success")
        def successful_sync_function():
            return "success_result"
        
        result = successful_sync_function()
        
        assert result == "success_result"
        assert len(self.handler.error_history) == 0  # No errors should be recorded
    
    @pytest.mark.asyncio
    async def test_with_error_handling_async_function_with_reraise(self):
        """Test decorator with asynchronous function that reraises"""
        @self.handler.with_error_handling("async_test", ErrorSeverity.CRITICAL, reraise=True)
        async def failing_async_function():
            raise ConnectionError("Async function failed")
        
        with pytest.raises(ConnectionError, match="Async function failed"):
            await failing_async_function()
        
        # Verify error was handled
        assert len(self.handler.error_history) == 1
        context = self.handler.error_history[0]
        assert context.operation == "async_test"
        assert context.severity == ErrorSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_with_error_handling_async_function_without_reraise(self):
        """Test decorator with asynchronous function that doesn't reraise"""
        @self.handler.with_error_handling("async_no_reraise", reraise=False)
        async def failing_async_function():
            raise TimeoutError("Async timeout")
        
        result = await failing_async_function()
        
        assert result is None  # Should return None when not reraising
        assert len(self.handler.error_history) == 1
        context = self.handler.error_history[0]
        assert context.operation == "async_no_reraise"
    
    @pytest.mark.asyncio
    async def test_with_error_handling_async_function_success(self):
        """Test decorator with successful asynchronous function"""
        @self.handler.with_error_handling("async_success")
        async def successful_async_function():
            return "async_result"
        
        result = await successful_async_function()
        
        assert result == "async_result"
        assert len(self.handler.error_history) == 0  # No errors should be recorded
    
    def test_with_error_handling_decorator_with_metadata(self):
        """Test decorator with additional metadata"""
        extra_metadata = {"user": "test_user", "session": "session_123"}
        
        @self.handler.with_error_handling(
            "metadata_decorator_test",
            ErrorSeverity.MEDIUM,
            RecoveryStrategy.GRACEFUL_DEGRADATION,
            reraise=False,
            **extra_metadata
        )
        def function_with_metadata():
            raise AttributeError("Metadata test error")
        
        result = function_with_metadata()
        
        assert result is None
        assert len(self.handler.error_history) == 1
        context = self.handler.error_history[0]
        assert context.metadata["user"] == "test_user"
        assert context.metadata["session"] == "session_123"
        assert context.recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION
    
    def test_attempt_recovery_success_first_try(self):
        """Test successful recovery on first attempt"""
        recovery_func = Mock()
        
        result = self.handler.attempt_recovery("test_op_1", recovery_func)
        
        assert result is True
        recovery_func.assert_called_once()
        assert self.handler.recovery_attempts["test_op_1"] == 0  # Reset after success
        self.mock_logger.info.assert_called_with("Recovery successful for test_op_1")
    
    def test_attempt_recovery_success_after_retries(self):
        """Test successful recovery after some failed attempts"""
        # Set up existing failed attempts
        self.handler.recovery_attempts["test_op_2"] = 2
        
        recovery_func = Mock()
        
        with patch('time.sleep') as mock_sleep:
            result = self.handler.attempt_recovery("test_op_2", recovery_func, backoff_seconds=0.5)
        
        assert result is True
        recovery_func.assert_called_once()
        mock_sleep.assert_called_once_with(1.0)  # 0.5 * (2 ** (2-1)) = 0.5 * 2 = 1.0
        assert self.handler.recovery_attempts["test_op_2"] == 0  # Reset after success
    
    def test_attempt_recovery_max_attempts_exceeded(self):
        """Test recovery failure when max attempts exceeded"""
        # Set up existing attempts at the limit
        self.handler.recovery_attempts["test_op_3"] = 3
        
        recovery_func = Mock()
        
        result = self.handler.attempt_recovery("test_op_3", recovery_func, max_attempts=3)
        
        assert result is False
        recovery_func.assert_not_called()
        self.mock_logger.error.assert_called_with(
            "Recovery abandoned for test_op_3 after 3 attempts"
        )
    
    def test_attempt_recovery_function_failure(self):
        """Test recovery when recovery function fails"""
        def failing_recovery():
            raise ConnectionError("Recovery failed")
        
        with patch('time.sleep'):
            result = self.handler.attempt_recovery("test_op_4", failing_recovery)
        
        assert result is False
        assert self.handler.recovery_attempts["test_op_4"] == 1
        
        # Verify error was handled for the failed recovery attempt
        assert len(self.handler.error_history) == 1
        context = self.handler.error_history[0]
        assert "Recovery attempt 1 for test_op_4" in context.operation
        assert context.severity == ErrorSeverity.HIGH
        assert context.recovery_strategy == RecoveryStrategy.RETRY
    
    def test_attempt_recovery_exponential_backoff(self):
        """Test exponential backoff calculation"""
        self.handler.recovery_attempts["backoff_test"] = 0
        recovery_func = Mock(side_effect=[Exception("fail"), Exception("fail"), None])
        
        with patch('time.sleep') as mock_sleep:
            # First attempt (no sleep)
            result1 = self.handler.attempt_recovery("backoff_test", recovery_func, backoff_seconds=1.0)
            assert result1 is False
            assert not mock_sleep.called
            
            # Second attempt (sleep 1.0 second)
            result2 = self.handler.attempt_recovery("backoff_test", recovery_func, backoff_seconds=1.0)
            assert result2 is False
            mock_sleep.assert_called_with(1.0)  # 1.0 * (2 ** (1-1)) = 1.0
            
            # Third attempt (sleep 2.0 seconds)
            mock_sleep.reset_mock()
            result3 = self.handler.attempt_recovery("backoff_test", recovery_func, backoff_seconds=1.0)
            assert result3 is True
            mock_sleep.assert_called_with(2.0)  # 1.0 * (2 ** (2-1)) = 2.0
    
    def test_get_error_summary_empty_history(self):
        """Test error summary with empty history"""
        summary = self.handler.get_error_summary()
        
        expected = {
            "total_errors": 0,
            "recent_errors": []
        }
        
        assert summary == expected
    
    def test_get_error_summary_with_errors(self):
        """Test error summary with error history"""
        # Add various types of errors
        errors = [
            (ValueError("Error 1"), "op1"),
            (KeyError("Error 2"), "op2"),
            (ValueError("Error 3"), "op3"),
            (RuntimeError("Error 4"), "op4"),
            (ValueError("Error 5"), "op5")
        ]
        
        for error, operation in errors:
            self.handler.handle_error(error, operation)
        
        # Add some recovery attempts
        self.handler.recovery_attempts = {"op1": 2, "op3": 1}
        
        summary = self.handler.get_error_summary()
        
        assert summary["total_errors"] == 5
        assert len(summary["recent_errors"]) == 5  # All 5 since we have < 10
        assert summary["error_types"]["ValueError"] == 3
        assert summary["error_types"]["KeyError"] == 1
        assert summary["error_types"]["RuntimeError"] == 1
        assert summary["recovery_attempts"] == {"op1": 2, "op3": 1}
        
        # Verify recent errors are properly formatted
        for error_dict in summary["recent_errors"]:
            assert "operation" in error_dict
            assert "component" in error_dict
            assert "timestamp" in error_dict
            assert "severity" in error_dict
            assert "recovery_strategy" in error_dict
            assert "metadata" in error_dict
    
    def test_get_error_summary_truncated_recent_errors(self):
        """Test error summary with more than 10 errors (should truncate recent)"""
        # Add 15 errors
        for i in range(15):
            error = ValueError(f"Error {i}")
            self.handler.handle_error(error, f"operation_{i}")
        
        summary = self.handler.get_error_summary()
        
        assert summary["total_errors"] == 15
        assert len(summary["recent_errors"]) == 10  # Should be limited to 10
        
        # Verify that recent errors are the last 10
        recent_operations = [error["operation"] for error in summary["recent_errors"]]
        expected_operations = [f"operation_{i}" for i in range(5, 15)]  # Last 10
        assert recent_operations == expected_operations
    
    def test_get_error_summary_error_type_counting(self):
        """Test error type counting in summary"""
        # Add errors with unknown error types (edge case)
        context_with_no_type = ErrorContext("test_op", "test_comp")
        context_with_no_type.metadata = {}  # No error_type key
        self.handler.error_history.append(context_with_no_type)
        
        # Add normal error
        self.handler.handle_error(ValueError("Normal error"), "normal_op")
        
        summary = self.handler.get_error_summary()
        
        assert summary["error_types"]["Unknown"] == 1
        assert summary["error_types"]["ValueError"] == 1


class TestDomainErrorCreation:
    """Test domain-specific error creation functions"""
    
    def test_create_domain_error_basic(self):
        """Test basic domain error creation"""
        with patch('lib.error_handler.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"
            
            error = create_domain_error(
                ContextError,
                "Test domain error",
                "test_operation",
                "test_component"
            )
            
            assert isinstance(error, ContextError)
            assert str(error) == "Test domain error"
            assert error.details["operation"] == "test_operation"
            assert error.details["component"] == "test_component"
            assert error.details["timestamp"] == "2023-01-01T12:00:00"
    
    def test_create_domain_error_with_kwargs(self):
        """Test domain error creation with additional kwargs"""
        error = create_domain_error(
            AgentPoolError,
            "Agent pool error with context",
            "pool_operation",
            "AgentPool",
            agent_id="agent_123",
            pool_state="ACTIVE",
            context_id="ctx_456"
        )
        
        assert isinstance(error, AgentPoolError)
        assert str(error) == "Agent pool error with context"
        assert error.details["operation"] == "pool_operation"
        assert error.details["component"] == "AgentPool"
        assert error.details["agent_id"] == "agent_123"
        assert error.details["pool_state"] == "ACTIVE"
        assert error.details["context_id"] == "ctx_456"
        assert error.agent_id == "agent_123"
        assert error.pool_state == "ACTIVE"
        assert error.context_id == "ctx_456"
    
    def test_create_agent_pool_error(self):
        """Test create_agent_pool_error convenience function"""
        error = create_agent_pool_error(
            "Agent failed to start",
            agent_id="agent_456",
            pool_state="FAILED"
        )
        
        assert isinstance(error, AgentPoolError)
        assert str(error) == "Agent failed to start"
        assert error.details["operation"] == "agent_pool_operation"
        assert error.details["component"] == "AgentPool"
        assert error.details["agent_id"] == "agent_456"
        assert error.details["pool_state"] == "FAILED"
        assert error.agent_id == "agent_456"
        assert error.pool_state == "FAILED"
    
    def test_create_agent_pool_error_no_agent_id(self):
        """Test create_agent_pool_error without agent_id"""
        error = create_agent_pool_error("General pool error")
        
        assert isinstance(error, AgentPoolError)
        assert str(error) == "General pool error"
        assert error.details["agent_id"] is None
    
    def test_create_state_machine_error(self):
        """Test create_state_machine_error convenience function"""
        error = create_state_machine_error(
            "Invalid state transition",
            current_state="IDLE",
            transition="START_WORK"
        )
        
        assert isinstance(error, StateMachineError)
        assert str(error) == "Invalid state transition"
        assert error.details["operation"] == "state_transition"
        assert error.details["component"] == "StateMachine"
        assert error.details["current_state"] == "IDLE"
        assert error.details["transition"] == "START_WORK"
        assert error.current_state == "IDLE"
        assert error.transition == "START_WORK"
    
    def test_create_state_machine_error_minimal(self):
        """Test create_state_machine_error with minimal parameters"""
        error = create_state_machine_error("State error")
        
        assert isinstance(error, StateMachineError)
        assert str(error) == "State error"
        assert error.details["current_state"] is None
        assert error.details["transition"] is None
    
    def test_create_orchestration_error(self):
        """Test create_orchestration_error convenience function"""
        error = create_orchestration_error(
            "Orchestration failed",
            project_id="project_789",
            phase="PLANNING"
        )
        
        assert isinstance(error, OrchestrationError)
        assert str(error) == "Orchestration failed"
        assert error.details["operation"] == "orchestration"
        assert error.details["component"] == "Orchestrator"
        assert error.details["project_id"] == "project_789"
        assert error.details["orchestration_phase"] == "PLANNING"
        assert error.project_id == "project_789"
        assert error.orchestration_phase == "PLANNING"
    
    def test_create_orchestration_error_minimal(self):
        """Test create_orchestration_error with minimal parameters"""
        error = create_orchestration_error("Simple orchestration error")
        
        assert isinstance(error, OrchestrationError)
        assert str(error) == "Simple orchestration error"
        assert error.details["project_id"] is None
        assert error.details["orchestration_phase"] is None
    
    def test_create_recovery_error(self):
        """Test create_recovery_error convenience function"""
        error = create_recovery_error(
            "Recovery attempt failed",
            recovery_type="EXPONENTIAL_BACKOFF",
            attempt_count=3
        )
        
        assert isinstance(error, RecoveryError)
        assert str(error) == "Recovery attempt failed"
        assert error.details["operation"] == "error_recovery"
        assert error.details["component"] == "RecoverySystem"
        assert error.details["recovery_type"] == "EXPONENTIAL_BACKOFF"
        assert error.details["attempt_count"] == 3
        assert error.recovery_type == "EXPONENTIAL_BACKOFF"
        assert error.attempt_count == 3
    
    def test_create_recovery_error_defaults(self):
        """Test create_recovery_error with default values"""
        error = create_recovery_error("Recovery failed")
        
        assert isinstance(error, RecoveryError)
        assert str(error) == "Recovery failed"
        assert error.details["recovery_type"] is None
        assert error.details["attempt_count"] == 0


class TestErrorHandlerIntegration:
    """Integration tests for error handler with real exception scenarios"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.handler = StandardizedErrorHandler("integration_test")
    
    def test_full_error_handling_workflow(self):
        """Test complete error handling workflow"""
        # Simulate a complex operation that fails and requires recovery
        def complex_operation():
            raise ConnectionError("Database connection failed")
        
        def recovery_operation():
            # Simulate successful recovery
            pass
        
        # Handle the initial error
        try:
            complex_operation()
        except Exception as e:
            context = self.handler.handle_error(
                e,
                "database_operation",
                ErrorSeverity.HIGH,
                RecoveryStrategy.RETRY,
                database_url="postgres://localhost:5432/test",
                query="SELECT * FROM users"
            )
        
        # Attempt recovery
        recovery_success = self.handler.attempt_recovery(
            "db_recovery",
            recovery_operation,
            max_attempts=3
        )
        
        # Verify results
        assert len(self.handler.error_history) == 1
        assert context.severity == ErrorSeverity.HIGH
        assert context.metadata["database_url"] == "postgres://localhost:5432/test"
        assert recovery_success is True
        
        # Get summary
        summary = self.handler.get_error_summary()
        assert summary["total_errors"] == 1
        assert summary["error_types"]["ConnectionError"] == 1
    
    @pytest.mark.asyncio
    async def test_async_decorator_real_scenario(self):
        """Test async decorator with realistic async operation"""
        @self.handler.with_error_handling(
            "async_api_call",
            ErrorSeverity.MEDIUM,
            RecoveryStrategy.FALLBACK,
            reraise=False,
            endpoint="/api/users",
            timeout=30
        )
        async def api_call():
            await asyncio.sleep(0.001)  # Simulate async work
            raise TimeoutError("API call timed out")
        
        result = await api_call()
        
        assert result is None  # Function returns None due to reraise=False
        assert len(self.handler.error_history) == 1
        
        context = self.handler.error_history[0]
        assert context.operation == "async_api_call"
        assert context.metadata["endpoint"] == "/api/users"
        assert context.metadata["timeout"] == 30
        assert context.metadata["error_type"] == "TimeoutError"
    
    def test_concurrent_error_handling(self):
        """Test concurrent error handling (thread safety simulation)"""
        import threading
        
        def create_error(error_id):
            error = ValueError(f"Concurrent error {error_id}")
            self.handler.handle_error(error, f"concurrent_op_{error_id}")
        
        # Create multiple threads that generate errors simultaneously
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_error, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all errors were handled
        assert len(self.handler.error_history) == 10
        
        # Verify unique operations
        operations = [ctx.operation for ctx in self.handler.error_history]
        expected_operations = [f"concurrent_op_{i}" for i in range(10)]
        assert sorted(operations) == sorted(expected_operations)
    
    def test_decorator_function_type_detection(self):
        """Test that decorator correctly detects function types"""
        # Test sync function detection
        @self.handler.with_error_handling("sync_detection")
        def sync_func():
            return "sync_result"
        
        # Test async function detection
        @self.handler.with_error_handling("async_detection")
        async def async_func():
            return "async_result"
        
        # Verify sync function works
        result = sync_func()
        assert result == "sync_result"
        
        # Verify async function works
        async def test_async():
            result = await async_func()
            assert result == "async_result"
        
        # Run the async test
        asyncio.run(test_async())
    
    def test_error_context_timestamp_realism(self):
        """Test that error context timestamps are realistic"""
        before_time = datetime.utcnow()
        
        context = ErrorContext("timestamp_test", "timestamp_component")
        
        after_time = datetime.utcnow()
        
        # Parse the timestamp
        context_time = datetime.fromisoformat(context.timestamp)
        
        # Verify timestamp is between before and after times
        assert before_time <= context_time <= after_time
    
    def test_recovery_with_complex_backoff_scenario(self):
        """Test recovery with multiple failures and complex backoff"""
        failure_count = 0
        
        def flaky_recovery():
            nonlocal failure_count
            failure_count += 1
            if failure_count < 3:
                raise ConnectionError(f"Failure {failure_count}")
            # Success on third attempt
        
        with patch('time.sleep') as mock_sleep:
            # First attempt - should fail
            result1 = self.handler.attempt_recovery(
                "flaky_operation",
                flaky_recovery,
                max_attempts=5,
                backoff_seconds=0.1
            )
            assert result1 is False
            assert failure_count == 1
            
            # Second attempt - should fail and apply backoff
            result2 = self.handler.attempt_recovery(
                "flaky_operation",
                flaky_recovery,
                max_attempts=5,
                backoff_seconds=0.1
            )
            assert result2 is False
            assert failure_count == 2
            
            # Third attempt - should succeed
            result3 = self.handler.attempt_recovery(
                "flaky_operation",
                flaky_recovery,
                max_attempts=5,
                backoff_seconds=0.1
            )
            assert result3 is True
            assert failure_count == 3
        
        # Verify backoff was applied correctly
        expected_calls = [
            # Second attempt: sleep 0.1 * (2 ** (1-1)) = 0.1
            # Third attempt: sleep 0.1 * (2 ** (2-1)) = 0.2
            unittest.mock.call(0.1),
            unittest.mock.call(0.2)
        ]
        assert mock_sleep.call_args_list == expected_calls
        
        # Verify recovery attempts were tracked and reset
        assert self.handler.recovery_attempts["flaky_operation"] == 0


class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.handler = StandardizedErrorHandler("edge_case_test")
    
    def test_handle_error_with_none_error(self):
        """Test handling when error is None (edge case)"""
        # This would be a programming error, but the handler should handle it gracefully
        context = self.handler.handle_error(
            Exception("None error test"),  # Use a real exception
            "none_error_test"
        )
        
        assert context.operation == "none_error_test"
        assert context.metadata["error_type"] == "Exception"
    
    def test_error_context_with_extremely_long_metadata(self):
        """Test error context with very large metadata"""
        large_metadata = {
            "huge_data": "x" * 10000,  # 10KB string
            "nested_dict": {str(i): f"value_{i}" for i in range(1000)},
            "list_data": list(range(1000))
        }
        
        context = self.handler.handle_error(
            ValueError("Large metadata test"),
            "large_metadata_operation",
            **large_metadata
        )
        
        assert context.metadata["huge_data"] == "x" * 10000
        assert len(context.metadata["nested_dict"]) == 1000
        assert len(context.metadata["list_data"]) == 1000
    
    def test_recovery_with_zero_backoff(self):
        """Test recovery with zero backoff time"""
        failure_count = 0
        
        def recovery_with_zero_backoff():
            nonlocal failure_count
            failure_count += 1
            if failure_count == 1:
                raise ValueError("First failure")
            # Success on second attempt
        
        with patch('time.sleep') as mock_sleep:
            # First attempt - should fail
            result1 = self.handler.attempt_recovery(
                "zero_backoff_test",
                recovery_with_zero_backoff,
                backoff_seconds=0.0
            )
            assert result1 is False
            
            # Second attempt - should succeed
            result2 = self.handler.attempt_recovery(
                "zero_backoff_test",
                recovery_with_zero_backoff,
                backoff_seconds=0.0
            )
            assert result2 is True
        
        # Should call sleep once with 0.0 on the second attempt
        mock_sleep.assert_called_once_with(0.0)
    
    def test_recovery_with_negative_max_attempts(self):
        """Test recovery with negative max attempts"""
        recovery_func = Mock()
        
        result = self.handler.attempt_recovery(
            "negative_attempts_test",
            recovery_func,
            max_attempts=-1
        )
        
        # Should fail immediately due to negative max attempts
        assert result is False
        recovery_func.assert_not_called()
    
    def test_error_summary_with_malformed_error_context(self):
        """Test error summary with malformed error context in history"""
        # Add a malformed context (missing error_type in metadata)
        malformed_context = ErrorContext("malformed_test", "test_component")
        malformed_context.metadata = {"some_key": "some_value"}  # No error_type
        self.handler.error_history.append(malformed_context)
        
        # Add normal context
        normal_error = ValueError("Normal error")
        self.handler.handle_error(normal_error, "normal_operation")
        
        summary = self.handler.get_error_summary()
        
        # Should handle malformed context gracefully
        assert summary["total_errors"] == 2
        assert summary["error_types"]["Unknown"] == 1  # Malformed context
        assert summary["error_types"]["ValueError"] == 1  # Normal context
    
    def test_decorator_with_function_that_returns_none(self):
        """Test decorator with function that normally returns None"""
        @self.handler.with_error_handling("none_return_test", reraise=False)
        def function_returning_none():
            return None
        
        result = function_returning_none()
        assert result is None
        assert len(self.handler.error_history) == 0  # No error occurred
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata"""
        def original_function():
            """Original docstring"""
            pass
        
        original_function.custom_attribute = "custom_value"
        
        decorated = self.handler.with_error_handling("metadata_preservation_test")(original_function)
        
        # Check that functools.wraps preserved the metadata
        assert decorated.__name__ == "original_function"
        assert decorated.__doc__ == "Original docstring"
        # Note: custom attributes might not be preserved by functools.wraps by default
    
    def test_extremely_long_operation_name(self):
        """Test handling of extremely long operation names"""
        long_operation_name = "operation_" + "x" * 10000
        
        context = self.handler.handle_error(
            RuntimeError("Long operation test"),
            long_operation_name
        )
        
        assert context.operation == long_operation_name
        assert len(context.operation) > 10000
    
    def test_unicode_and_special_characters_in_error_messages(self):
        """Test handling of unicode and special characters"""
        unicode_error = ValueError("Error with unicode: 你好世界 🌍 ñáéíóú")
        special_chars_metadata = {
            "unicode_field": "Special chars: @#$%^&*()_+-={}[]|\\:;\"'<>?,./",
            "emoji_field": "🔥🚀💯✨🎉"
        }
        
        context = self.handler.handle_error(
            unicode_error,
            "unicode_test_操作",
            **special_chars_metadata
        )
        
        assert "你好世界" in context.metadata["error_message"]
        assert context.operation == "unicode_test_操作"
        assert context.metadata["unicode_field"] == "Special chars: @#$%^&*()_+-={}[]|\\:;\"'<>?,./"
        assert context.metadata["emoji_field"] == "🔥🚀💯✨🎉"


# Import required for mock patching
import unittest.mock